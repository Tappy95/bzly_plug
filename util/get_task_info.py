from datetime import datetime
from urllib.parse import quote

import aiohttp
import asyncio
import hashlib
import time

import requests
from sqlalchemy import select, create_engine, update, and_
from sqlalchemy.dialects.mysql import insert

from config import *
from models.alchemy_models import LUserExchangeCash, LUserCashLogPY, MUserInfo, LCoinChange, TpGame, MUserLeader, \
    MPartnerInfo
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
        "size": "500",
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


def get_leader_id(low_user_id, conn):
    select_low_user = conn.execute(select([MUserInfo]).where(
        MUserInfo.user_id == low_user_id
    )).fetchone()
    if select_low_user and select_low_user['referrer']:
        return get_leader_id(select_low_user['referrer'], conn)
    return low_user_id


def insert_leader_id():
    with engine.connect() as conn:
        select_users = conn.execute(select([MUserInfo])).fetchall()
        for user in select_users:
            leader_id = get_leader_id(user['user_id'], conn)
            leader_info = {
                "user_id": user['user_id'],
                "referrer": user['referrer'],
                "leader_id": leader_id,
                "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            ins = insert(MUserLeader)
            insert_stmt = ins.values(leader_info)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                user_id=insert_stmt.inserted.user_id,
                referrer=insert_stmt.inserted.referrer,
                leader_id=insert_stmt.inserted.leader_id,
                update_time=insert_stmt.inserted.update_time
            )
            conn.execute(on_duplicate_key_stmt)


def sync_channel_admin():
    dict = {
        "sld": "18746458381",
        "hcl": "18746286622",
        "fyd": "15945238667",
        "dx": "15545020905",
        "lxq": "18645218625",
        "cjl": "19845286972",
        "xmn": "16606671234",
        "wf": "15046200651",
        "wj": "13634528880",
        "yy": "18646619228",
        "sl": "13514685861",
        "xq": "13104527681"
    }
    # 查询并修改用户表渠道为xx的,且没有上级用户的,修改上级用户为手机号所绑定的用户
    with engine.connect() as conn:
        for admin in dict.keys():
            # 查询渠道管理员信息
            select_channel_admin = conn.execute(select([MUserInfo]).where(
                MUserInfo.mobile == dict[admin]
            )).fetchone()
            admin_id = select_channel_admin['user_id']

            conn.execute(update(MUserInfo).values(
                {
                    # "referrer": admin_id,
                    # "recommended_time": int(time.time() * 1000),
                    "role_type": 2,
                    "high_role": 2
                }
            ).where(
                and_(
                    # MUserInfo.channel_code == admin,
                    # MUserInfo.referrer == None,
                    # MUserInfo.mobile != dict[admin]
                    MUserInfo.user_id == admin_id
                )
            ))
        # select_user = conn.execute(select([MUserInfo])).fetchall()
        # for user in select_user:
        #     conn.execute(update(MUserLeader).values({
        #         "referrer": user['referrer']
        #     }).where(
        #         MUserLeader.user_id == user['user_id']
        #     ))
    print("done work")


def sync_channel_partner():
    dict = {
        "sld": "18746458381",
        "hcl": "18746286622",
        "fyd": "15945238667",
        "dx": "15545020905",
        "lxq": "18645218625",
        "cjl": "19845286972",
        "xmn": "16606671234",
        "wf": "15046200651",
        "wj": "13634528880",
        "yy": "18646619228",
        "sl": "13514685861",
        "xq": "13104527681"
    }
    # 查询并修改用户表渠道为xx的,且没有上级用户的,修改上级用户为手机号所绑定的用户
    with engine.connect() as conn:
        for admin in dict.keys():
            # 查询渠道管理员信息
            select_channel_admin = conn.execute(select([MUserInfo]).where(
                MUserInfo.mobile == dict[admin]
            )).fetchone()
            admin_id = select_channel_admin['user_id']
            logger.info(admin_id)
            # 更新合伙人状态
            conn.execute(update(MPartnerInfo).values({
                "status": 1
            }).where(
                MPartnerInfo.user_id == admin_id
            ))
    print("done work")


def fix_coin_change():
    with engine.connect() as conn:
        select_conin = conn.execute(select([LCoinChange]).where(
            and_(
                LCoinChange.amount > 100000,
                LCoinChange.changed_time > 1604466648344
            )
        )).fetchall()
        for user in select_conin:
            select_user_coin = conn.execute(select([MUserInfo]).where(
                MUserInfo.user_id == user['user_id']
            )).fetchone()
            conn.execute(update(MUserInfo).values({
                "coin": select_user_coin['coin'] - user['amount']
            }).where(
                MUserInfo.user_id == user['user_id']
            ))


def fix_low_coin_change():
    with engine.connect() as conn:
        select_user = conn.execute(select([MUserInfo])).fetchall()
        for user in select_user:
            select_coin = conn.execute(select([LCoinChange]).where(
                LCoinChange.user_id == user['user_id']
            ).order_by(LCoinChange.changed_time.desc()).limit(1)).fetchone()

            # select_user_coin = conn.execute(select([MUserInfo]).where(
            #     MUserInfo.user_id == user['user_id']
            # )).fetchone()
            if not select_coin:
                continue
            conn.execute(update(MUserInfo).values({
                "coin": select_coin['coin_balance']
            }).where(
                MUserInfo.user_id == user['user_id']
            ))


def update_leader_info():
    with engine.connect() as conn:
        conn.execute(update(MUserLeader).values(
            {
                "referrer": "d64bb408629c4f7e9f5c92b503672dcb"
            }
        ).where(
            MUserLeader.referrer == None
        ))


def find_partner_one_or_two():
    with engine.connect() as conn:
        select_partner = conn.execute(select([MPartnerInfo]).where(
            MPartnerInfo.status == 1
        )).fetchall()
        one_ids = []
        two_ids = []
        partner_ids = [partner['user_id'] for partner in select_partner]
        select_one = conn.execute(select([MUserLeader]).where(
            MUserLeader.referrer == "d64bb408629c4f7e9f5c92b503672dcb"
        )).fetchall()
        for one in select_one:
            if one['user_id'] in partner_ids:
                one_ids.append(one['user_id'])
        print(one_ids)
        select_two = conn.execute(select([MUserLeader]).where(
            MUserLeader.referrer.in_([one['user_id'] for one in select_one])
        )).fetchall()
        for two in select_two:
            if two['user_id'] in partner_ids:
                two_ids.append(two['user_id'])
        print(two_ids)


def test_inset():
    with engine.connect() as conn:
        a = conn.execute(insert(LUserCashLogPY).values({
            "user_id": "123"
        }))
        print(a.lastrowid)


if __name__ == '__main__':
    # 爱变现
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(get_ibx_tasks())

    # 多游游戏获取
    test_inset()
