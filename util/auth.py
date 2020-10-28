import aiohttp
import jwt
from aiohttp import web
from sqlalchemy import select, and_

import config

# token生成器
from util.log import logger


def generate_jwt(payload, expiry, secret=None):
    """
    生成jwt
    :param payload: dict 载荷
    :param expiry: datetime 有效期
    :param secret: 密钥
    :return: jwt
    """
    _payload = {'exp': expiry}
    _payload.update(payload)

    if not secret:
        secret = config.JWT_SECRET

    token = jwt.encode(_payload, secret, algorithm='HS256')
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1ODYzMTI5OTAsInVzZXJfbmFtZSI6ImJhaWx1bnRlYyIsInVzZXJfaWQiOiIxMTEifQ.jkNrTI_69jEOLbtEQLEqs0t9Pndu0iXOLgQelkSAAYs"
    return token


# token解析器, 暂时废弃
def verify_jwt(token, secret=None):
    """
    检验jwt
    :param token: jwt
    :param secret: 密钥
    :return: dict: payload
    """
    if not secret:
        secret = config.JWT_SECRET

    # payload = jwt.decode(token, secret, algorithm=['HS256'])
    try:
        payload = jwt.decode(token, secret, algorithm=['HS256'])
    except jwt.PyJWTError:
        payload = None

    return payload

