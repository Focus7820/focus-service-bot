import discord
from discord.ext import commands
import os
from utils.database import Database

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)
db = Database()

@bot.event
async def on_ready():
    print("\n" + "="*50)
    print("Focus Service | MM & EXCH Enterprise Online")
    print("="*50 + "\n")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Focus Service | MM & EXCH"
        )
    )

@bot.event
async def on_member_update(before, after):
    guild_id = after.guild.id
    staff_role_id = db.get_config(guild_id, "staff_role")
    
    if staff_role_id:
        staff_role = after.guild.get_role(staff_role_id)
        if staff_role:
            if staff_role not in before.roles and staff_role in after.roles:
                db.set_staff_join_date(after.id, guild_id)

async def load_cogs():
    cog_files = [
        "cogs.admin",
        "cogs.tickets",
        "cogs.exchange",
        "cogs.stats"
    ]
    
    for cog in cog_files:
        try:
            await bot.load_extension(cog)
            print(f"✓ Loaded {cog}")
        except Exception as e:
            print(f"✗ Failed to load {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
