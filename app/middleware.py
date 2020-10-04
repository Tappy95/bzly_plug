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
    # if config.PRODUCTION_ENV:
    #     value = await redis.hgetall('shopee:product:batch_date', encoding='utf-8')
    #     if len(value) > 1:
    #         key_list = []
    #         for key, value in value.items():
    #             if value == '1':
    #                 key_list.append(datetime.strptime(key, '%Y-%m-%d'))
    #         key_time = sorted(key_list)[-1]
    #         key_time = datetime.strftime(key_time, '%Y-%m-%d')
    #     elif len(value) == 1:
    #         key_time = [x for x in value.keys()][0]
    #         key_time = datetime.strftime(key_time, '%Y-%m-%d')
    #     else:
    #         logger.info("Can't get the es_index name")
    #     request['es_key_time'] = key_time
    #     request['es_index_name'] = "shopee_product_" + key_time
    # else:
    #     request['es_key_time'] = '2020-05-11'
    #     request['es_index_name'] = "shopee_product_2020-05-11"

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
