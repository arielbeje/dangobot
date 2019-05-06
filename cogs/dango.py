from itertools import groupby
from operator import itemgetter
from utils import sql

import discord
from discord.ext import commands

from typing import Union


async def get_dangos(ctx: commands.Context, member: discord.Member) -> int:
    person = await sql.fetch(
        "SELECT score FROM scoreboard WHERE serverid=? AND memberid=?",
        str(ctx.message.guild.id), str(member.id))
    if len(person) == 0:
        return 0
    return person[0][0]


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
    async def set_prefix(self, ctx: commands.Context, *, prefix: str):
        """Set a different prefix for the bot"""
        await sql.execute("UPDATE servers SET prefix=? WHERE serverid=?",
                          prefix, str(ctx.message.guild.id))
        em = discord.Embed(title="Updated prefix",
                           description=f"Updated prefix is `{prefix}`",
                           colour=discord.Colour.dark_green())
        await ctx.send(embed=em)

    @commands.command(aliases=["stats", "scoreboard"])
    async def leaderboard(self,
                          ctx: commands.Context,
                          member: Union[discord.Member, str] = None):
        """Show the leaderboard. Can also be used for a specific person."""
        if member is not None and (isinstance(member, discord.Member)
                                   or type(member) is str
                                   and member.lower() == "me"):
            if isinstance(member, discord.Member):
                name = member.display_name
                score = await get_dangos(ctx, member)
            elif type(member) is str:
                author = ctx.message.author
                name = author.display_name
                score = await get_dangos(ctx, author)
            await ctx.send(f"{name} has {score} dangos.")
        else:
            people = await sql.fetch(
                "SELECT memberid, score FROM scoreboard WHERE serverid=? ORDER BY score DESC",
                str(ctx.message.guild.id))
            interval = (await sql.fetch(
                "SELECT interval FROM servers WHERE serverid=?",
                str(ctx.message.guild.id)))[0][0]
            emoji_info = (await sql.fetch(
                "SELECT emoji_id, emoji_char FROM servers WHERE serverid=?",
                str(ctx.message.guild.id)))[0]
            if emoji_info[1] is not None:
                emoji = emoji_info[1]
            else:
                emoji = await ctx.message.guild.fetch_emoji(int(emoji_info[0]))
            total_dangos = sum([int(person[1]) for person in people
                                ]) if people is not None else 0
            message = f"{emoji} **Scoreboard** {emoji}"
            message += f"\n\nTotal dangos: **{total_dangos}**"
            message += f"\nEvery **{interval}** messages\n"
            if people is not None:
                members = [(ctx.guild.get_member(int(person[0])), person[1])
                           for person in people[:20]]
                scores = [
                    item[0] for item in groupby(people[:20], itemgetter(1))
                ]
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

    @commands.command()
    async def me(self, ctx: commands.Context):
        author = ctx.message.author
        score = await get_dangos(ctx, author)
        await ctx.send(f"{author.display_name} has {score} dangos.")


def setup(bot):
    bot.add_cog(DangoCog(bot))
