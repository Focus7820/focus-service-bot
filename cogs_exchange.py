import discord
from discord.ext import commands
from utils.database import Database
import qrcode
from io import BytesIO
import aiohttp

class Exchange(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.command(name="setupi")
    async def setup_upi(self, ctx, slot: int, upi_id: str):
        """Setup UPI ID"""
        if slot not in [1, 2, 3]:
            embed = discord.Embed(
                title="❌ Invalid Slot",
                description="Slots available: 1, 2, 3",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        self.db.set_upi_id(ctx.author.id, ctx.guild.id, slot, upi_id)
        embed = discord.Embed(
            title="✅ UPI Setup",
            description=f"Slot {slot} set to `{upi_id}`",
            color=discord.Color.green()
        )
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name="mqr")
    async def generate_qr(self, ctx, slot: int, amount: float):
        """Generate UPI QR code"""
        upi_id = self.db.get_upi_id(ctx.author.id, ctx.guild.id, slot)

        if not upi_id:
            embed = discord.Embed(
                title="❌ UPI Not Set",
                description=f"Slot {slot} not configured",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        upi_string = f"upi://pay?pa={upi_id}&am={amount}&cu=INR"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_string)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        file = discord.File(buffer, filename="upi_qr.png")
        embed = discord.Embed(
            title="💳 UPI QR Code",
            description=f"Amount: ₹{amount}",
            color=discord.Color.from_rgb(0, 150, 0)
        )
        embed.set_image(url="attachment://upi_qr.png")
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed, file=file)

    @commands.command(name="ltcbal")
    async def ltc_balance(self, ctx, ltc_address: str):
        """Check LTC balance"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{ltc_address}/balance"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        embed = discord.Embed(
                            title="❌ Error",
                            description="Address not found or invalid",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        return

                    data = await resp.json()
                    confirmed = data.get("balance", 0) / 100000000
                    unconfirmed = data.get("unconfirmed_balance", 0) / 100000000

                    embed = discord.Embed(
                        title="💰 LTC Balance",
                        color=discord.Color.from_rgb(0, 150, 0)
                    )
                    embed.add_field(name="Confirmed Balance", value=f"{confirmed:.8f} LTC", inline=False)
                    embed.add_field(name="Unconfirmed Balance", value=f"{unconfirmed:.8f} LTC", inline=False)
                    embed.add_field(name="Address", value=f"`{ltc_address}`", inline=False)
                    embed.timestamp = discord.utils.utcnow()
                    await ctx.send(embed=embed)

            except Exception as e:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Could not fetch balance: {str(e)}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Exchange(bot))