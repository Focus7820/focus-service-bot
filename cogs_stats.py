import discord
from discord.ext import commands
from utils.database import Database
from datetime import datetime, timedelta

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.command(name="volume")
    async def volume_stats(self, ctx):
        """Show volume statistics"""
        guild_id = ctx.guild.id
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        stats = self.db.get_volume_stats(guild_id)

        embed = discord.Embed(
            title="📊 Volume Statistics",
            color=discord.Color.from_rgb(0, 150, 0)
        )

        for category in ["I2C", "C2I", "P2C", "C2P"]:
            daily = stats.get(f"{category}_daily", 0)
            weekly = stats.get(f"{category}_weekly", 0)
            monthly = stats.get(f"{category}_monthly", 0)
            alltime = stats.get(f"{category}_alltime", 0)

            embed.add_field(
                name=f"🔄 {category}",
                value=f"Daily: ${daily:.2f}\nWeekly: ${weekly:.2f}\nMonthly: ${monthly:.2f}\nAll-Time: ${alltime:.2f}",
                inline=False
            )

        embed.set_footer(text="Focus Service | MM & EXCH")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx):
        """Show staff leaderboard"""
        guild_id = ctx.guild.id
        leaderboard_data = self.db.get_leaderboard(guild_id)

        embed = discord.Embed(
            title="🏆 Staff Leaderboard",
            color=discord.Color.from_rgb(0, 0, 0)
        )

        medals = ["🥇", "🥈", "🥉"]
        for idx, (user_id, volume, profit, completed) in enumerate(leaderboard_data[:10]):
            try:
                user = await self.bot.fetch_user(user_id)
                medal = medals[idx] if idx < 3 else f"{idx + 1}."
                value = f"Volume: ${volume:.2f}\nProfit: ${profit:.2f}\nDeals: {completed}"
                embed.add_field(name=f"{medal} {user.name}", value=value, inline=False)
            except:
                pass

        embed.set_footer(text="Focus Service | MM & EXCH")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="sp")
    async def staff_profile(self, ctx, user: discord.User):
        """Show staff profile"""
        guild_id = ctx.guild.id
        profile = self.db.get_staff_profile(user.id, guild_id)

        embed = discord.Embed(
            title=f"👤 {user.name} Profile",
            color=discord.Color.from_rgb(0, 150, 0)
        )

        embed.add_field(name="Limit", value=f"${profile.get('limit', 0):.2f}", inline=True)
        embed.add_field(name="All-Time Volume", value=f"${profile.get('alltime_volume', 0):.2f}", inline=True)
        embed.add_field(name="Daily Volume", value=f"${profile.get('daily_volume', 0):.2f}", inline=True)
        embed.add_field(name="Weekly Volume", value=f"${profile.get('weekly_volume', 0):.2f}", inline=True)
        embed.add_field(name="Monthly Volume", value=f"${profile.get('monthly_volume', 0):.2f}", inline=True)
        embed.add_field(name="Completed Deals", value=str(profile.get('completed', 0)), inline=True)
        embed.add_field(name="Total Profit", value=f"${profile.get('profit', 0):.2f}", inline=True)

        join_date = profile.get('join_date', 'Unknown')
        embed.add_field(name="Staff Joined", value=str(join_date), inline=False)

        embed.set_footer(text="Focus Service | MM & EXCH")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="p")
    async def user_profile(self, ctx, user: discord.User):
        """Show user profile"""
        guild_id = ctx.guild.id
        profile = self.db.get_user_profile(user.id, guild_id)

        embed = discord.Embed(
            title=f"👤 {user.name} Profile",
            color=discord.Color.from_rgb(0, 150, 0)
        )

        embed.add_field(name="Total Exchanges", value=str(profile.get('total_exchanges', 0)), inline=True)
        embed.add_field(name="Total Volume", value=f"${profile.get('total_volume', 0):.2f}", inline=True)
        embed.add_field(name="Last Exchange", value=str(profile.get('last_exchange', 'Never')), inline=True)

        embed.set_footer(text="Focus Service | MM & EXCH")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))