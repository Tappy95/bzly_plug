import asyncio

from aiomysql import create_pool

from config import *

class InitDb:
    _pool = None

    @classmethod
    async def create_pool(cls):
        cls._pool = await create_pool(
            # pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
            echo=SQLALCHEMY_ECHO,
            # pool_size=SQLALCHEMY_POOL_SIZE,
            # max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
            # pool_recycle=SQLALCHEMY_POOL_RECYCLE,
            autocommit=True,
            user=DB_USER_NAME, db=DB_DATABASE_NAME,
            host=DB_SEVER_ADDR, port=DB_SEVER_PORT, password=DB_USER_PW,
            maxsize=300,
            loop=asyncio.get_event_loop()
        )

    @classmethod
    async def execute(cls, sql):
        conn = await cls._pool.acquire()
        cur = await conn.cursor()
        await cur.execute(str(sql))
        return cur
