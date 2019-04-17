import discord
from discord.ext import commands


class InfoCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Info Command"

    @commands.command()
    async def info(self, ctx: commands.Context):
        """Shows info about the bot"""
        em = discord.Embed(title="DangoBot",
                           colour=discord.Colour.gold())
        em.add_field(name="Creator", value="arielbeje - <@114814850621898755>")
        em.add_field(name="Source", value="[GitHub](https://github.com/arielbeje/dangobot)")
        await ctx.send(embed=em)
