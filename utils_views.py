import discord
from discord.ui import View, Select, Button
from discord.ext import commands
import chat_exporter
import asyncio

class TicketDropdown(View):
    def __init__(self, bot, db, guild):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = db
        self.guild = guild

    @discord.ui.select(
        placeholder="Select an exchange type...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="I2C (INR to Crypto)", value="I2C"),
            discord.SelectOption(label="C2I (Crypto to INR)", value="C2I"),
            discord.SelectOption(label="P2C (PayPal to Crypto)", value="P2C"),
            discord.SelectOption(label="C2P (Crypto to PayPal)", value="C2P"),
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: Select):
        await interaction.response.defer()
        category = select.values[0]

        ticket_num = self.db.get_next_ticket_id(self.guild.id)
        channel_name = f"exchange-{ticket_num:04d}"

        staff_role_id = self.db.get_config(self.guild.id, "staff_role")
        staff_role = self.guild.get_role(staff_role_id) if staff_role_id else None

        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await self.guild.create_text_channel(channel_name, overwrites=overwrites)

        ticket_id = self.db.create_ticket(self.guild.id, channel.id, interaction.user.id, category, "")

        embed = discord.Embed(
            title=f"🎫 Ticket #{ticket_num:04d}",
            description=f"Category: **{category}**\nOwner: {interaction.user.mention}",
            color=discord.Color.from_rgb(0, 150, 0)
        )
        embed.add_field(name="ℹ️ Instructions", value="Please specify the INR amount you want to exchange.", inline=False)
        embed.timestamp = discord.utils.utcnow()

        await channel.send(embed=embed)

        view = CoinSelectView(self.bot, self.db, ticket_id, interaction.user.id, category)
        select_embed = discord.Embed(
            title="💱 Select Coin",
            description="Choose which coin you want to exchange:",
            color=discord.Color.from_rgb(0, 150, 0)
        )
        select_embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=select_embed, view=view)

        confirm_embed = discord.Embed(
            title="✅ Ticket Created",
            description=f"Your ticket has been created: {channel.mention}",
            color=discord.Color.green()
        )
        confirm_embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

class CoinSelectView(View):
    def __init__(self, bot, db, ticket_id, owner_id, category):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = db
        self.ticket_id = ticket_id
        self.owner_id = owner_id
        self.category = category

    @discord.ui.button(label="LTC", style=discord.ButtonStyle.blurple)
    async def ltc_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_coin_select(interaction, "LTC")

    @discord.ui.button(label="USDT", style=discord.ButtonStyle.blurple)
    async def usdt_button(self, interaction: discord.Interaction, button: Button):
        await self.handle_coin_select(interaction, "USDT")

    async def handle_coin_select(self, interaction: discord.Interaction, coin: str):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("You don't have permission to use this!", ephemeral=True)
            return

        await interaction.response.defer()

        self.db.get_connection().execute(
            "UPDATE tickets SET coin = ? WHERE ticket_id = ?",
            (coin, self.ticket_id)
        )
        self.db.get_connection().commit()

        def check(msg):
            return msg.author.id == self.owner_id and msg.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=600.0)
            try:
                inr_amount = float(msg.content)
                self.db.set_ticket_inr(self.ticket_id, inr_amount)

                embed = discord.Embed(
                    title="✅ Amount Recorded",
                    description=f"INR Amount: ₹{inr_amount}",
                    color=discord.Color.green()
                )
                embed.timestamp = discord.utils.utcnow()
                await msg.reply(embed=embed)

            except ValueError:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description="Please enter a valid number.",
                    color=discord.Color.red()
                )
                embed.timestamp = discord.utils.utcnow()
                await msg.reply(embed=embed)

        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⏱️ Timeout",
                description="Took too long to respond.",
                color=discord.Color.red()
            )
            embed.timestamp = discord.utils.utcnow()
            await interaction.channel.send(embed=embed)

class ConfirmView(View):
    def __init__(self, bot, db, guild, ticket_id, claimer_id, ticket_data):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = db
        self.guild = guild
        self.ticket_id = ticket_id
        self.claimer_id = claimer_id
        self.ticket_data = ticket_data

    @discord.ui.button(label="✅ Confirm & Vouch", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ticket_data["owner_id"]:
            await interaction.response.send_message("Only the ticket owner can confirm!", ephemeral=True)
            return

        await interaction.response.defer()

        usd_amount = self.ticket_data.get("usd_amount", 0)
        category = self.ticket_data["category"]
        coin = self.ticket_data.get("coin", "USDT")

        self.db.complete_ticket(self.ticket_id, self.claimer_id, self.guild.id, usd_amount, category)

        claimer = await self.bot.fetch_user(self.claimer_id)

        if category == "I2C":
            rep_message = f"+rep {self.claimer_id}\nLegit Exchanged UPI TO {coin}\n[ {usd_amount:.2f}$ ]"
        elif category == "C2I":
            rep_message = f"+rep {self.claimer_id}\nLegit Exchanged {coin} TO UPI\n[ {usd_amount:.2f}$ ]"
        else:
            rep_message = f"+rep {self.claimer_id}\nLegit Exchange\n[ {usd_amount:.2f}$ ]"

        embed = discord.Embed(
            title="⭐ Professional Vouch",
            description=rep_message,
            color=discord.Color.from_rgb(0, 150, 0)
        )
        embed.timestamp = discord.utils.utcnow()
        await interaction.channel.send(embed=embed)

        success_embed = discord.Embed(
            title="✅ Exchange Confirmed",
            description="Thank you for vouching!",
            color=discord.Color.green()
        )
        success_embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=success_embed)

class CloseView(View):
    def __init__(self, bot, db, guild, channel, user):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = db
        self.guild = guild
        self.channel = channel
        self.user = user

    @discord.ui.button(label="✅ Close", style=discord.ButtonStyle.green)
    async def close_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()

        try:
            transcript = await chat_exporter.export(self.channel)

            if transcript:
                transcript_file = discord.File(
                    transcript,
                    filename=f"transcript-{self.channel.name}.html"
                )

                try:
                    await self.user.send(
                        content=f"Transcript from {self.channel.mention}",
                        file=transcript_file
                    )
                except:
                    pass

                log_channel_id = self.db.get_config(self.guild.id, "log_channel")
                if log_channel_id:
                    log_channel = self.guild.get_channel(log_channel_id)
                    if log_channel:
                        await log_channel.send(
                            content=f"Transcript from {self.channel.name}",
                            file=transcript_file
                        )

            await interaction.followup.send("Closing channel...", ephemeral=True)
            await asyncio.sleep(5)
            await self.channel.delete()

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error closing channel: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()