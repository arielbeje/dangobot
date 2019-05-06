from itertools import groupby
from operator import itemgetter
from utils import sql

import discord
from discord.ext import commands

from typing import Union


class DangoCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        type(self).__name__ = "Dango Commands"

    @commands.command(name="setemoji")
    @commands.has_permissions(administrator=True)
    async def set_emoji(self, ctx: commands.Context,
                        emoji: Union[discord.Emoji, str]):
        """Set a different emoji for the bot"""
        if isinstance(emoji, discord.Emoji):
            await sql.execute(
                "UPDATE servers SET emoji_id=?, emoji_char=? WHERE serverid=?",
                emoji.id, None, str(ctx.message.guild.id))
        else:
            await sql.execute(
                "UPDATE servers SET emoji_id=?, emoji_char=? WHERE serverid=?",
                None, emoji, str(ctx.message.guild.id))
        em = discord.Embed(title="Set emoji",
                           description=str(emoji),
                           colour=discord.Colour.dark_green())
        await ctx.send(embed=em)

    @commands.command(name="setinterval")
    @commands.has_permissions(administrator=True)
    async def set_interval(self, ctx: commands.Context, interval: int):
        """Set a different interval for the bot"""
        await sql.execute("UPDATE servers SET interval=? WHERE serverid=?",
                          interval, str(ctx.message.guild.id))
        em = discord.Embed(title="Updated interval",
                           description=f"Updated interval is {interval}",
                           colour=discord.Colour.dark_green())
        await ctx.send(embed=em)

    @commands.command(name="setprefix")
    @commands.has_permissions(administrator=True)
    async def set_perfix(self, ctx: commands.Context, *, prefix: str):
        """Set a different prefix for the bot"""
        await sql.execute("UPDATE servers SET prefix=? WHERE serverid=?",
                          prefix, str(ctx.message.guild.id))
        em = discord.Embed(title="Updated prefix",
                           description=f"Updated prefix is `{prefix}`",
                           colour=discord.Colour.dark_green())
        await ctx.send(embed=em)

    @commands.command(aliases=["stats", "scoreboard"])
    async def leaderboard(self, ctx: commands.context):
        """Show the leaderboard"""
        people = await sql.fetch(
            "SELECT memberid, score FROM scoreboard WHERE serverid=? ORDER BY score DESC",
            str(ctx.message.guild.id))
        interval = (await
                    sql.fetch("SELECT interval FROM servers WHERE serverid=?",
                              str(ctx.message.guild.id)))[0][0]
        emoji_info = (await sql.fetch(
            "SELECT emoji_id, emoji_char FROM servers WHERE serverid=?",
            str(ctx.message.guild.id)))[0]
        if emoji_info[1] is not None:
            emoji = emoji_info[1]
        else:
            emoji = await ctx.message.guild.fetch_emoji(int(emoji_info[0]))
        total_dangos = sum([int(person[1])
                            for person in people]) if people is not None else 0
        message = f"{emoji} **Scoreboard** {emoji}"
        message += f"\n\nTotal dangos: **{total_dangos}**"
        message += f"\nEvery **{interval}** messages\n"
        if people is not None:
            members = [(ctx.guild.get_member(int(person[0])), person[1])
                       for person in people[:20]]
            scores = [item[0] for item in groupby(people[:20], itemgetter(1))]
            scoreboard = {score: [] for score in scores}
            for member in members:
                scoreboard[member[1]].append(member[0])
            for index, score in enumerate(scores):
                people_with_score = [
                    person.display_name for person in scoreboard[score]
                ]
                people_with_score.sort()
                message += f"{index + 1}. **{score}** ({', '.join(people_with_score)})\n"
        await ctx.send(message)


def setup(bot):
    bot.add_cog(DangoCog(bot))
