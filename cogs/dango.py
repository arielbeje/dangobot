from itertools import groupby
from operator import itemgetter
from utils import sql
import pickle


import discord
from discord.ext import commands


class DangoCog(commands.cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Dango Commands"

    @commands.command(name="setemoji")
    async def set_emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        await sql.execute("UPDATE servers SET emoji=? WHERE serverid=?", pickle.dumps(emoji), str(ctx.message.guild.id))
        em = discord.Embed(title="Set emoji",
                           description=str(emoji),
                           colour=discord.Colour.dark_green())
        await ctx.send(embed=em)

    @commands.command(name="setinterval")
    async def set_interval(self, ctx: commands.Context, interval: int):
        await sql.exceute("UPDATE servers SET interval=? WHERE serverid=?", interval, str(ctx.message.guild.id))
        em = discord.Embed(title="Updated interval",
                           description=f"Updated interval is {interval}",
                           colour=discord.Colour.dark_green())
        await ctx.send(embed=em)

    @commands.command()
    async def leaderboard(self, ctx: commands.context):
        people = await sql.fetch("SELECT memberid, score FROM scoreboard WHERE serverid=? ORDER BY score", str(ctx.message.guild.id))
        interval = await sql.fetch("SELECT interval FROM servers WHERE serverid=?", str(ctx.message.guild.id))
        emoji = pickle.loads(await sql.fetch("SELECT emoji FROM servers WHERE serverid=?", str(ctx.message.guild.id)))
        total_dangos = sum([int(person[1]) for person in people])
        members = [(ctx.guild.get_member(int(person[0])), person[1]) for person in people[:20]]
        message = f"{emoji} **Scoreboard** {emoji}"
        message += f"\n\nTotal dangos: **{total_dangos}**"
        message += f"\nEvery **{interval}** messages"
        scores = [item[0] for item in groupby(people, itemgetter(1))]
        scoreboard = {score: [] for score in scores}
        for member in members:
            scoreboard[member[1]].append(member[0])
        for score in scores:
            people_with_score = [person.display_name for person in scoreboard[score]]
            people_with_score.sort()
            message += f"**{score}** {', '.join(people_with_score)}\n"
        ctx.send(message)
