from datetime import datetime

import aioredis
from aiohttp import web

from app.index import views
from config import *
# from sqlalchemy import create_engine
from aiomysql.sa import create_engine

from util.log import logger
from .middleware import db_middleware, jwt_verify, redis_middleware
from aioelasticsearch import Elasticsearch

sharable_secret = 'secret'

# 中间件加载
# app = web.Application(middlewares=[db_middleware, jwt_verify])
app = web.Application(middlewares=[db_middleware, redis_middleware])


# async def init_elasticsearch(app):
#     # app['elastic'] = Elasticsearch(ELASTICSEARCH_URL)
#     app['elastic'] = Elasticsearch("http://47.102.220.1:9200")
#
#
# async def close_elasticsearch(app):
#     await app['elastic'].close()

# async def init_es(app):
#     app['es_engine'] = Elasticsearch(hosts=ELASTICSEARCH_URL, timeout=ELASTIC_TIMEOUT)
#     logger.info("连接ES成功")


async def init_db(app):
    app['db_engine'] = await create_engine(
        # pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
        echo=SQLALCHEMY_ECHO,
        # pool_size=SQLALCHEMY_POOL_SIZE,
        # max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
        pool_recycle=SQLALCHEMY_POOL_RECYCLE,
        autocommit=True,
        user=DB_USER_NAME, db=DB_DATABASE_NAME,
        host=DB_SEVER_ADDR, port=DB_SEVER_PORT, password=DB_USER_PW,
        maxsize=10
    )
    logger.info("连接DB成功")



async def close_db(app):
    app['db_engine'].close()
    await app['db_engine'].wait_closed()
    logger.info("断开数据库连接")


async def init_redis(app):
    app['redis_engine'] = await aioredis.create_redis_pool(
        address=REDIS_URL
        # password=REDIS_PASSWORD
    )
    logger.info("连接Redis成功")


async def close_redis(app):
    app['redis_engine'].close()
    await app['db_engine'].wait_closed()
    logger.info("断开Redis连接")


app.on_startup.append(init_db)
# app.on_startup.append(init_es)
app.on_cleanup.append(close_db)
app.on_startup.append(init_redis)
app.on_cleanup.append(close_redis)
# app.on_startup.append(init_elasticsearch)
# app.on_cleanup.append(close_elasticsearch)

'''
app['db_engine'] = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)
'''

app.add_routes(index.views.routes)
