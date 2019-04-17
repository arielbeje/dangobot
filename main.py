import asyncio
import os
import pickle
from utils import sql

import logging
from logging.handlers import TimedRotatingFileHandler

import discord
from discord.ext import commands

workDir = os.getcwd()
logDir = os.path.join(workDir, "logs")
if not os.path.exists(logDir):
    os.makedirs(logDir)

fh = TimedRotatingFileHandler("logs/log", "midnight", encoding="utf-8", backupCount=7)
fh.setFormatter(logging.Formatter(fmt="[%(asctime)s] [%(name)-19s] %(levelname)-8s: %(message)s",
                                  datefmt="%Y-%m-%dT%H:%M:%S%z"))
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(fmt="[%(asctime)s] %(levelname)-8s: %(message)s",
                                  datefmt="%Y-%m-%dT%H:%M:%S%z"))
logging.basicConfig(handlers=[fh, ch],
                    level=logging.INFO)
logger = logging.getLogger('root')


async def initdb():
    tables = [table[0] for table in await sql.fetch("SELECT name FROM sqlite_master WHERE type='table'")]
    if any(table not in tables for table in ["servers", "messages", "scoreboard"]):
        if "servers" not in tables:
            await sql.execute("CREATE TABLE servers (serverid varchar(20) PRIMARY KEY, prefix text, interval integer, emoji blob)")
        if "messages" not in tables:
            await sql.execute("CREATE TABLE messages (serverid varchar(20), messageid varchar(20))")
        if "scoreboard" not in tables:
            await sql.execute("CREATE TABLE scoreboard (serverid varchar(20), memberid varchar(20), score integer)")


async def get_prefix(bot: commands.AutoShardedBot, message: discord.Message):
    prefix = (await sql.fetch("SELECT prefix FROM servers WHERE serverid=?", str(message.guild.id)))[0][0]
    return commands.when_mentioned_or(prefix)(bot, message) if prefix else commands.when_mentioned(bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix)


@bot.event
async def on_ready():
    # In case the bot was off when leaving/joining a guild
    logger.info("Verifying guilds match DB")
    guilds = bot.guilds
    guildIds = [guild.id for guild in guilds]
    missingGuildIds = [guildId for guildId in guildIds if len(await sql.fetch("SELECT 1 FROM servers WHERE serverid=?", str(guildId))) == 0]
    for guildId in missingGuildIds:
        logger.debug(f"Added guild with id {guildId} to DB")
        await sql.initserver(guildId)
    undeletedGuildIds = [guildId[0] for guildId in await sql.fetch("SELECT serverid FROM servers") if int(guildId[0]) not in guildIds]
    for guildId in undeletedGuildIds:
        logger.debug(f"Removed guild with id {guildId} from DB")
        await sql.deleteserver(guildId)

    logger.info(f"Logged in as: {bot.user.name} - {bot.user.id}")
    logger.info(f"Serving {len(bot.users)} users in {len(guilds)} server{('s' if len(guilds) > 1 else '')}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    logger.info(f"Joined server \'{guild.name}\' - {guild.id}")
    await sql.initserver(guild.id)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    logger.info(f"Left server \'{guild.name}\' - {guild.id}")
    await sql.deleteserver(guild.id)


@bot.event
async def on_message(message: discord.Message):
    if not isinstance(message.channel, discord.abc.GuildChannel):
        return
    await sql.execute("INSERT INTO messages VALUES (?, ?)", str(message.guild.id), str(message.id))
    messages = len(await sql.fetch("SELECT 1 FROM messages WHERE serverid=?", str(message.guild.id)))
    interval = (await sql.fetch("SELECT interval FROM servers WHERE serverid=?", str(message.guild.id)))[0][0]
    if messages >= interval:
        if not await sql.fetch("SELECT 1 FROM scoreboard WHERE serverid=? AND memberid=?",
                               str(message.server.id), str(message.author.id)):
            await sql.execute("INSERT INTO scoreboard VALUES (?, ?, ?)",
                              str(message.guild.id), str(message.author.id), 1)
        else:
            await sql.execute("UPDATE scoreboard SET score=score+1 WHERE serverid=? AND memberid=?",
                              str(message.server.id), str(message.author.id))
        await sql.execute("DELETE FROM messages WHERE serverid=?", str(message.guild.id))
        emoji = pickle.loads("SELECT emoji FROM servers WHERE serverid=?", str(message.server.id))
        await message.channel.send(str(emoji))
    await bot.processcommands(message)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(initdb())
    bot.load_extension("cogs.dango")
    bot.load_extension("cogs.info")
    bot.run(os.environ["DANGOBOT"], bot=True, reconnect=True)
