from datetime import datetime

import jwt
from aiohttp import web
# from sqlalchemy.orm import sessionmaker

import config
from aiohttp.web import middleware


# 数据库链接中间件
from util.log import logger


# @middleware
# async def es_middleware(request, handler):
#     es = request.app['es_engine']
#     request['es_connection'] = es
#     return await handler(request)


@middleware
async def db_middleware(request, handler):
    engine = request.app['db_engine']
    async with engine.acquire() as conn:
        request['db_connection'] = conn
        return await handler(request)


@middleware
async def redis_middleware(request, handler):
    redis = request.app['redis_engine']
    request['redis_connection'] = redis

    return await handler(request)


# JWT验证中间件
@middleware
async def jwt_verify(request, handler):
    request.user = None
    jwt_token = ((request.headers.get('Authorization')).split(' '))[1]
    print(jwt_token)
    if jwt_token:
        try:
            payload = jwt.decode(jwt_token, config.JWT_SECRET,
                                 algorithms=['HS256'])
            exp = payload.get('exp')
            print(exp)
        except (jwt.DecodeError, jwt.ExpiredSignatureError):
            return web.json_response({'message': 'Token is invalid'}, status=400)

        # request.user = ebay_user.objects.get(id=payload['user_id'])

    return await handler(request)
