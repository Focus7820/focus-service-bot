import discord
from discord.ext import commands
from utils.database import Database

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.command(name="setlogchannel")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the log channel for transcripts"""
        self.db.set_config(ctx.guild.id, "log_channel", channel.id)
        embed = discord.Embed(
            title="✅ Log Channel Set",
            description=f"Log channel set to {channel.mention}",
            color=discord.Color.green()
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="setstaffrole")
    @commands.has_permissions(administrator=True)
    async def set_staff_role(self, ctx, role: discord.Role):
        """Set the staff/exchanger role"""
        self.db.set_config(ctx.guild.id, "staff_role", role.id)
        embed = discord.Embed(
            title="✅ Staff Role Set",
            description=f"Staff role set to {role.mention}",
            color=discord.Color.green()
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="setexchangerrole")
    @commands.has_permissions(administrator=True)
    async def set_exchanger_role(self, ctx, role: discord.Role):
        """Set the exchanger role"""
        self.db.set_config(ctx.guild.id, "exchanger_role", role.id)
        embed = discord.Embed(
            title="✅ Exchanger Role Set",
            description=f"Exchanger role set to {role.mention}",
            color=discord.Color.green()
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="setrates")
    @commands.has_permissions(administrator=True)
    async def set_rates(self, ctx, category: str, rate: float):
        """Set exchange rates"""
        categories = ["I2C", "C2I", "P2C", "C2P"]
        if category.upper() not in categories:
            embed = discord.Embed(
                title="❌ Invalid Category",
                description=f"Valid categories: {', '.join(categories)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.db.set_rate(ctx.guild.id, category.upper(), rate)
        embed = discord.Embed(
            title="✅ Rate Updated",
            description=f"**{category.upper()}**: {rate}",
            color=discord.Color.green()
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="setlimit")
    @commands.has_permissions(administrator=True)
    async def set_limit(self, ctx, user_id: int, usd_amount: float):
        """Set exchanger limit"""
        self.db.set_exchanger_limit(user_id, ctx.guild.id, usd_amount)
        embed = discord.Embed(
            title="✅ Limit Set",
            description=f"User <@{user_id}> limit set to ${usd_amount}",
            color=discord.Color.green()
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Show all available commands"""
        embed = discord.Embed(
            title="📖 Focus Service Bot Commands",
            color=discord.Color.from_rgb(0, 150, 0)
        )

        admin_commands = """
``.setlogchannel`` - Set log channel
``.setstaffrole`` - Set staff role
``.setexchangerrole`` - Set exchanger role
``.setrates`` - Set exchange rates
``.setlimit`` - Set exchanger limit
"""

        exchange_commands = """
``.exchange-panel`` - Create exchange panel
``.claim`` - Claim a ticket
``.done @user`` - Mark ticket complete
``.transcript`` - Export transcript
``.close`` - Close ticket with export
"""

        staff_commands = """
``.volume`` - View volume stats
``.leaderboard`` - Staff leaderboard
``.sp @user`` - Staff profile
``.p @user`` - User profile
"""

        utility_commands = """
``.ltcbal <address>`` - Check LTC balance
``.setupi <slot> <upi_id>`` - Setup UPI ID
``.mqr <slot> <amount>`` - Generate UPI QR
"""

        embed.add_field(name="👑 Admin Commands", value=admin_commands, inline=False)
        embed.add_field(name="💼 Exchange Commands", value=exchange_commands, inline=False)
        embed.add_field(name="📊 Staff Systems", value=staff_commands, inline=False)
        embed.add_field(name="🛠 Utility Commands", value=utility_commands, inline=False)

        embed.set_footer(text="Focus Service | MM & EXCH")
        embed.timestamp = discord.utils.utcnow()
        embed.color = discord.Color.from_rgb(0, 0, 0)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
