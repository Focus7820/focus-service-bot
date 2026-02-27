import discord
from discord.ext import commands
from utils.database import Database
from utils.views import TicketDropdown, ConfirmView, CloseView
import chat_exporter

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.command(name="exchange-panel")
    @commands.has_permissions(administrator=True)
    async def exchange_panel(self, ctx):
        """Create the exchange dropdown panel"""
        embed = discord.Embed(
            title="Focus Service | MM & EXCH",
            description="💱 Start Exchange",
            color=discord.Color.from_rgb(0, 150, 0)
        )
        embed.set_footer(text="Select an option below to create a ticket")
        embed.timestamp = discord.utils.utcnow()

        view = TicketDropdown(self.bot, self.db, ctx.guild)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="claim")
    @commands.has_permissions(manage_messages=True)
    async def claim_ticket(self, ctx):
        """Claim a ticket"""
        channel_name = ctx.channel.name
        if not channel_name.startswith("exchange-"):
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used in ticket channels",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        ticket_id = int(channel_name.split("-")[1])
        ticket_data = self.db.get_ticket(ticket_id)

        if not ticket_data:
            embed = discord.Embed(
                title="❌ Ticket Not Found",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        guild_id = ctx.guild.id
        staff_role_id = self.db.get_config(guild_id, "staff_role")

        if not staff_role_id:
            embed = discord.Embed(
                title="❌ Error",
                description="Staff role not configured",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        staff_role = ctx.guild.get_role(staff_role_id)
        if not staff_role or staff_role not in ctx.author.roles:
            embed = discord.Embed(
                title="❌ No Permission",
                description="You don't have the exchanger role",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if ctx.author.id == ticket_data["owner_id"]:
            embed = discord.Embed(
                title="❌ Error",
                description="You cannot claim your own ticket",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if ticket_data.get("claimed_by"):
            embed = discord.Embed(
                title="❌ Already Claimed",
                description="This ticket has already been claimed",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        category = ticket_data["category"]
        inr_amount = ticket_data.get("inr_amount", 0)
        rate = self.db.get_rate(guild_id, category)

        if not rate:
            embed = discord.Embed(
                title="❌ Rate Not Set",
                description=f"Rate for {category} not configured",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        usd_amount = inr_amount / rate
        limit = self.db.get_exchanger_limit(ctx.author.id, guild_id)

        embed = discord.Embed(
            title="✅ Ticket Claimed",
            color=discord.Color.green()
        )
        embed.add_field(name="Claimed by", value=f"<@{ctx.author.id}>", inline=False)
        embed.add_field(name="USD Calculated", value=f"${usd_amount:.2f}", inline=True)
        embed.add_field(name="Your Limit", value=f"${limit:.2f}", inline=True)

        if usd_amount > limit:
            embed.color = discord.Color.red()
            embed.title = "❌ Limit Exceeded"
            embed.description = f"This exchange exceeds your limit. Required: ${usd_amount:.2f}, Your limit: ${limit:.2f}"
            await ctx.send(embed=embed)
            return

        self.db.claim_ticket(ticket_id, ctx.author.id, usd_amount)
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="done")
    async def done_ticket(self, ctx, user: discord.User):
        """Mark ticket as done"""
        channel_name = ctx.channel.name
        if not channel_name.startswith("exchange-"):
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used in ticket channels",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        ticket_id = int(channel_name.split("-")[1])
        ticket_data = self.db.get_ticket(ticket_id)

        if not ticket_data:
            embed = discord.Embed(
                title="❌ Ticket Not Found",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if ticket_data.get("claimed_by") != ctx.author.id:
            embed = discord.Embed(
                title="❌ Not Claimed by You",
                description="Only the claimer can mark ticket as done",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if ticket_data.get("completed"):
            embed = discord.Embed(
                title="❌ Already Completed",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            owner = await self.bot.fetch_user(user.id)
            embed = discord.Embed(
                title="💸 Funds Sent",
                description="Exchanger Has Sent You The Funds.\nIf You Received Them Then Press The Button Below And Vouch.",
                color=discord.Color.from_rgb(0, 150, 0)
            )
            embed.timestamp = discord.utils.utcnow()

            view = ConfirmView(self.bot, self.db, ctx.guild, ticket_id, ctx.author.id, ticket_data)
            await owner.send(embed=embed, view=view)

            confirm_embed = discord.Embed(
                title="✅ Confirmation Sent",
                description=f"Confirmation message sent to {user.mention}",
                color=discord.Color.green()
            )
            confirm_embed.timestamp = discord.utils.utcnow()
            await ctx.send(embed=confirm_embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Could not send confirmation: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="transcript")
    async def transcript(self, ctx):
        """Export transcript without closing"""
        channel_name = ctx.channel.name
        if not channel_name.startswith("exchange-"):
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used in ticket channels",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        try:
            transcript = await chat_exporter.export(ctx.channel)
            if transcript is None:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Could not export transcript",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            transcript_file = discord.File(
                transcript,
                filename=f"transcript-{channel_name}.html"
            )

            embed = discord.Embed(
                title="✅ Transcript Exported",
                color=discord.Color.green()
            )
            embed.timestamp = discord.utils.utcnow()
            await ctx.send(embed=embed, file=transcript_file)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Export failed: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="close")
    async def close_ticket(self, ctx):
        """Close ticket with 2-step confirmation"""
        channel_name = ctx.channel.name
        if not channel_name.startswith("exchange-"):
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used in ticket channels",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="❓ Close Ticket",
            description="Are you sure you want to close this ticket?",
            color=discord.Color.orange()
        )
        embed.timestamp = discord.utils.utcnow()

        view = CloseView(self.bot, self.db, ctx.guild, ctx.channel, ctx.author)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Tickets(bot))