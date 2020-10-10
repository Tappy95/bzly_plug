from urllib.parse import quote

import aiohttp
import asyncio
import hashlib
import time

import requests
from sqlalchemy import select, create_engine, insert, update

from config import *
from models.alchemy_models import LUserExchangeCash, LUserCashLogPY, MUserInfo, LCoinChange, TpGame
from util.log import logger
from util.static_methods import serialize
import pipeflow

WORKER_NUMBER = 2

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)


async def get_ibx_tasks():
    # 参数
    m = hashlib.md5()

    app_key = "142792891"
    target_id = "2cfdd8e67aaf45deb3cb242a1621f2de"
    device_info = "863270643441130"
    device = "android"
    notify_url = "http://lottery.shouzhuan518.com/py/ibxcallback"
    app_secret = "06bff8a6f9963466"
    params = {
        "app_key": app_key,
        "target_id": target_id,
        "device_info": device_info,
        "device": device,
        "notify_url": notify_url,
        "sign": (hashlib.md5(
            (str(app_key) + device + device_info + target_id + notify_url + app_secret).encode(
                'utf-8')).hexdigest()).upper()
    }
    print(params['sign'])
    async with aiohttp.ClientSession() as client:
        async with client.post('https://api.aibianxian.net/igame/api/v1.0/cplApi/access', data=params) as resp:
            assert resp.status == 200
            r = await resp.json()
            print(r)
            token = r['data']['token']

            task_params = {
                "page_num": 1,
                "model": "",
                "osVersion": "",
                "token": token
            }
            # print(task_params)
            for page in range(1, 20):
                task_params['page_num'] = page
                # async with client.post('https://api.aibianxian.net/igame/h5/v1.51/outHightList', data=params) as task_info:
                async with client.get('https://api.aibianxian.net/igame/h5/v1.51/outHightList',
                                      data=task_params) as task_info:
                    task_result = await task_info.json()
                    # print(task_result)

                    async with client.post('http://127.0.0.1:8090/get/hightasks', json=task_result) as s_result:
                        d = await s_result.json()
                        print(task_result)


def get_dy_games():
    media_id = "dy_59610931"
    user_id = "888888"
    device_type = "2"
    device_ids = '{"1":"99001008920886","2":"99001008920887"}'
    app_secret = "A50000"
    sign = (hashlib.md5(
        (quote(device_ids) + device_type + media_id + user_id + app_secret).encode(
            'utf-8')).hexdigest()).lower()
    print(sign)
    params = {
        "media_id": media_id,
        "user_id": user_id,
        "device_ids": quote(device_ids),
        "device_type": device_type,
        "page": "1",
        "size": "100",
        "sign": "22b2a8e131a0b9042d40a7a7e21f02fa",
    }
    r = requests.get('https://api.ads66.com/api/list', params=params)
    json_r = r.json()
    game_list = json_r['data']
    # print(json_r["data"])

    results = []
    with engine.connect() as conn:
        for game in game_list:
            print(game)
            result = {
                "interface_id": 11,
                "game_id": str(game['advert_id']),
                "game_title": game['title'],
                "icon": game['product_icon'],
                "url": "https://h5.ads66.com/tasks/" + str(game['advert_id']),
                "enddate": str(game['serve_end']),
                "game_gold": float(game['max_price']),
                "introduce": game['product_introduction'],
                "package_name": game['package_name'],
                "status": 1,
                "game_tag": 1,
                "order_id": 1,
                "ptype": 2,
                "label_str": "",
                "short_intro": "",
            }
            results.append(result)
        conn.execute(insert(TpGame).values(results))



if __name__ == '__main__':
    # 爱变现
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(get_ibx_tasks())

    # 多游游戏获取
    get_dy_games()
