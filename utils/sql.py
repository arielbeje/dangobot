import aiosqlite
import pickle
import logging
from typing import List, Tuple, Union

DB_FILE = "db.db"

logger = logging.getLogger('root')


class InvalidQueryError(Exception):
    pass


class NoDBError(Exception):
    pass


async def execute(query: str, *args: Union[str, int]):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(query, args)
        await db.commit()


async def fetch(query: str, *args: Union[str, int]) -> Union[List[Tuple[str]], List[Tuple[int]], None]:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(query, args)
        rows = await cursor.fetchall()
    return rows


async def executemany_queries(*queries: str):
    async with aiosqlite.connect(DB_FILE) as db:
        for query in queries:
            if type(query) == tuple:
                await db.execute(query[0], query[1:])
                await db.commit()
            elif type(query) == str:
                await db.execute(query)
                await db.commit()
            else:
                raise InvalidQueryError()


async def initserver(serverid: Union[int, str]):
    await executemany_queries(
        ("INSERT INTO servers VALUES (?, ?, ?, ?)", str(serverid), "dango ", 100, pickle.dumps(u"🍡"))
    )


async def deleteserver(serverid: Union[int, str]):
    queries = ["DELETE FROM servers WHERE serverid=?",
               "DELETE FROM messages WHERE serverid=?",
               "DELETE FROM scoreboard WHERE serverid=?"]
    await executemany_queries(*[(query, str(serverid)) for query in queries])
