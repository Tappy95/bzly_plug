import copy
import json
import time
import traceback
from datetime import datetime
from operator import itemgetter
from random import random
from urllib.parse import quote

from config import *

from aiohttp import web
from sqlalchemy import select, update, and_, text, or_
from sqlalchemy.dialects.mysql import insert

from models.alchemy_models import MUserInfo, t_tp_pcdd_callback, PDictionary, t_tp_xw_callback, TpTaskInfo, \
    t_tp_ibx_callback, TpJxwCallback, TpYwCallback, TpDyCallback, TpZbCallback, LCoinChange, MChannelInfo, MChannel, \
    MCheckpointRecord, MCheckpoint
from task.callback_task import fission_schema, cash_exchange, select_user_id, get_channel_user_ids, get_callback_infos
from task.check_sign import check_xw_sign, check_ibx_sign, check_jxw_sign, check_yw_sign, check_dy_sign, check_zb_sign
from util.log import logger
from util.static_methods import serialize

routes = web.RouteTableDef()


# 查看当前用户闯关状态->七个关卡状态
@routes.get('/checkpoint')
async def get_checkpoint(request):
    connection = request['db_connection']
    # 获取user_id
    user_id = await select_user_id(connection, request.query.get('token'))
    # 查询用户闯关数据
    select_user_point = select([MCheckpointRecord]).where(
        MCheckpointRecord.user_id == user_id
    )
    cur = await connection.execute(select_user_point)
    rec = await cur.fetchall()
    list_info = []

    if rec:
        for record in rec:
            result = {
                "checkpoint_number": record['checkpoint_number'],
                "current_coin": record['current_coin'],
                "current_invite": record['current_invite'],
                "current_points": record['current_points'],
                "create_time": record['create_time'],
                "endtime": record['endtime'],
                "reward_amount": record['reward_amount'],
                "state": record['state']
            }
            list_info.append(result)
    json_result = {
        "code": 200,
        "message": "success",
        "data": list_info
    }


# 单任务状态->已赚金币/任务要求赚取总额,已邀请人/任务要求邀请人总数.
@routes.get('/checkpoint/point')
async def get_single_point(request):
    connection = request['db_connection']
    params = {**request.query}
    user_id = await select_user_id(connection, params['token'])
    # 查询关卡具体指标
    select_checkpoint = select([MCheckpoint]).where(
        MCheckpoint.checkpoint_number == params['checkpoint_number']
    )
    cur = await connection.execute(select_checkpoint)
    rec = await cur.fetchone()
    # 查询用户当前关数据
    select_current_point = select([MCheckpointRecord]).where(
        and_(
            MCheckpointRecord.user_id == user_id,
            MCheckpointRecord.checkpoint_number == params['checkpoint_number']
        )
    )
    cur_current = await connection.execute(select_current_point)
    rec_current = await cur_current.fetchone()
    result = {
        "create_time": rec_current['create_time'],
        "end_time": rec_current['end_time'],
        "current_coin": rec_current['current_coin'],
        "gold_number": rec['gold_number'],
        "current_invite": rec_current['current_invite'],
        "friends_number": rec['friends_number'],
        "current_points": rec_current['current_points'],
        "friends_checkpoint_number": rec['friends_checkpoint_number'],
        "state": rec_current['state'],
    }
    json_result = {
        "code": 200,
        "message": "success",
        "data": result
    }
    return web.json_response(json_result)


# 开启新关卡
@routes.post('/checkpoint/point')
async def post_checkpoint_point(request):
    connection = request['db_connection']
    r_json = await request.json()
    user_id = await select_user_id(connection, r_json['token'])
    # 查询当前关数
    select_current_point = select([MCheckpointRecord]).where(
        MCheckpointRecord.user_id == user_id
    )
    cur_current = await connection.execute(select_current_point)
    rec_current = await cur_current.fetchall()
    # 如果申请开启关数为正确关数,则通过
    if rec_current[-1]['state'] == 1 and len(rec_current) == r_json['checkpoint_number'] - 1:
        # 查询关卡条件
        select_checkpoint = select([MCheckpoint]).where(
            MCheckpoint.checkpoint_number == r_json['checkpoint_number']
        )
        cur_checkpoint = await connection.execute(select_checkpoint)
        rec_checkpoint = cur_checkpoint.fetchone()
        await connection.execute(insert(MCheckpointRecord).values({
            "user_id": user_id,
            "checkpoint_number": r_json['checkpoint_number'],
            "create_time": int(time.time() * 1000),
            "end_time": 0,
            "current_coin": 0,
            "current_invite": 0,
            "current_points": 0,
            "reward_amount": 0,
            "state": 0
        }))
        return web.json_response({
            "code": 200,
            "message": "开启闯关成功"
        })
    else:
        return web.json_response({
            "code": 402,
            "message": "闯关开启异常"
        })


# 提交结算任务, 获取三张随机牌
@routes.get('/checkpoint/card')
async def get_card(request):
    params = {**request.query}
    # 查询关卡奖励及指标
    connection = request['db_connection']
    user_id = await select_user_id(connection, params['token'])
    select_checkpoint = select([MCheckpoint]).where(
        MCheckpoint.checkpoint_number == params['checkpoint_number']
    )
    cur_checkpoint = await connection.execute(select_checkpoint)
    rec_checkpoint = await cur_checkpoint.fetchone()
    select_record = select([MCheckpointRecord]).where(
        and_(
            MCheckpointRecord.user_id == user_id,
            MCheckpointRecord.checkpoint_number == params['checkpoint_number']
        )
    )
    cur_record = await connection.execute(select_record)
    rec_record = await cur_record.fetchone()
    if rec_record['current_coin'] >= rec_checkpoint['gold_number'] \
            and rec_record['current_invite'] >= rec_checkpoint['friends_number'] \
            and rec_record['current_points'] >= rec_checkpoint['friends_checkpoint_number']:

        one_reward = float(rec_checkpoint['reward_amount']) / 3
        start = 0
        end = one_reward
        result = []
        for i in range(3):
            reward = random.uniform(start, end)
            start += one_reward
            end += one_reward
            result.append(reward)

        json_result = {
            "code": 200,
            "message": "success",
            "data": result
        }
    else:
        json_result = {
            "code": 402,
            "message": "闯关要求未达标",
            "data": []
        }
    return web.json_response(json_result)


# 提交抽牌结果,完成结算
@routes.post('/checkpoint/card')
async def post_checkpoint_card(request):
    r_json = await request.json()
    connection = request['db_connection']
    user_id = await select_user_id(connection, r_json['token'])
    result_value = {
        "end_time": int(time.time() * 1000),
        "reward_amount": r_json['card_reward'],
        "state": 1
    }
    await connection.execute(update(MCheckpointRecord).values(result_value).where(
        and_(
            MCheckpointRecord.user_id == user_id,
            MCheckpointRecord.checkpoint_number == r_json['checkpoint_number']
        )
    ))

