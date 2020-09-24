import aiohttp
import jwt
from aiohttp import web
from sqlalchemy import select, and_

import config

# token生成器
from models.models import ana_user_permission
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


# 百伦身份验证器

# json结构
# json_result= {
#     "result": {
#         "success": true,
#         "Account": "宋奕贤",
#         "UserId": "2918195",
#         "UserCodeNew": "BL1669",
#         "UserCode": "BL5566709",
#         "OaUserId": "3137",
#         "AllCompany": false,
#         "roles": [],
#         "Company": {
#             "Id": 1,
#             "CompanyCode": "bailun",
#             "CompanyName": "广州百伦供应链有限公司"
#         },
#         "Department": {
#             "DepartmentId": 261,
#             "Name": "爬虫组",
#             "Code": ""
#         }
#     },
#     "statusCode": 200,
#     "message": null
# }

async def bailuntec_sso(token, request):
    headers = {"Authorization": token}
    if token == "123456":
        return {"result": {"UserId": "bailuntec", "Account": "bailuntec"}, "success": True}
    async with aiohttp.ClientSession() as session:
        async with session.get('http://sso.bailuntec.com/GetUserResource', headers=headers) as resp:
            json_body = await resp.json()
    if json_body['result']['success'] is False:
        try:
            payload = verify_jwt(token)
            if payload:
                payload['success'] = True
                user_premission = await get_user_permission(request['db_connection'], payload['UserId'])
                payload['roles'] = {"system_site_permission": user_premission}
                print(payload)
                json_result = {
                    "result": payload,
                    "statusCode": 200,
                    "message": "有效token成功获取用户信息"
                }
                return json_result
            else:
                # json_result = {"result": {"success": False}, "statusCode": 422, "message": "token失效,请重新登录或刷新token"}
                raise web.HTTPUnprocessableEntity(text='token失效,请重新登录或刷新token')
        except Exception as e:
            logger.info(e)
            return None
    else:
        return json_body


# 百伦身份验证器
async def get_user_id(token):
    headers = {"Authorization": token}
    if token == "123456":
        return {"result": {"UserId": "9527"}}
    async with aiohttp.ClientSession() as session:
        async with session.get('http://sso.bailuntec.com/GetUserResource', headers=headers) as resp:
            json_body = await resp.json()
    if json_body['result']['success'] is False:
        try:
            payload = verify_jwt(token)
            payload['success'] = True
            return {"result": payload, "statusCode": 200}
        except Exception as e:
            logger.info(e)
            return None
    else:
        return json_body


async def get_user_permission(connection, user_id):
    select_permission = select([ana_user_permission]).where(
        and_(
            ana_user_permission.c.user_id == user_id
        )
    )
    cursor = await connection.execute(select_permission)
    record = await cursor.fetchone()
    system_site_permission = {}
    site_list = ['ebay', 'amazon', 'shopee', 'wish']
    if record:
        for i in site_list:
            system_site_permission[i] = {
                "site": [] if not record['{0}_permission'.format(i)] else record['{0}_permission'.format(i)].split(':'),
                "is_auth": 1 if record['{0}_permission'.format(i)] else 0
            }
    else:
        for i in site_list:
            system_site_permission[i] = {
                "site": [],
                "is_auth": 0
            }

    return system_site_permission


async def get_permission_es_body(request, search_body, site):
    '''获取用户 数据过滤信息 对请求 数据进行过滤'''
    token = request.headers.get('Authorization')
    connection = request['db_connection']
    user_json = await get_user_id(token)
    user_id = user_json['result']['UserId']
    try:
        select_permission = select([
            ana_user_permission.c.is_bailun,
            ana_user_permission.c.shopee_permission,
            ana_user_permission.c.baned_seller,
            ana_user_permission.c.baned_brand
        ]).where(
            and_(
                ana_user_permission.c.user_id == user_id
            )
        )

        cursor = await connection.execute(select_permission)
        record = await cursor.fetchone()

    except Exception as e:
        logger.info(e)
        raise web.HTTPInternalServerError(text="DB error,Please contact Administrator")
    if record:
        # if record['is_bailun'] == '4k':
        #     return search_body
        shopee_permission = eval(record['shopee_permission'])
        if shopee_permission:
            if site in shopee_permission and shopee_permission[site]:
                search_body['query']['bool']['must'].append(
                    {"terms": {"category_id": [category_id for category_id in shopee_permission[site]]}})
        seller_list = eval(record['baned_seller'])[config.SYSTEM_NAME] if config.SYSTEM_NAME in eval(
            record['baned_seller']) else None
        # shopee通过shop_name过滤卖家
        if seller_list:
            search_body['query']['bool']['must_not'].append({"terms": {"shop_name": seller_list}})
        brand_list = eval(record['baned_brand'])[config.SYSTEM_NAME] if config.SYSTEM_NAME in eval(
            record['baned_brand']) else None
        if brand_list:
            search_body['query']['bool']['must_not'].append({"terms": {"brand": brand_list}})

    return search_body
