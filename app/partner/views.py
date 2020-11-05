import copy
import json
import time
import traceback
from datetime import datetime, timedelta
from operator import itemgetter
from random import random, uniform, randint
from urllib.parse import quote

from config import *

from aiohttp import web
from sqlalchemy import select, update, and_, text, or_
from sqlalchemy.dialects.mysql import insert

from models.alchemy_models import MUserInfo, t_tp_pcdd_callback, PDictionary, t_tp_xw_callback, TpTaskInfo, \
    t_tp_ibx_callback, TpJxwCallback, TpYwCallback, TpDyCallback, TpZbCallback, LCoinChange, MChannelInfo, MChannel, \
    MCheckpointRecord, MCheckpoint, MCheckpointIncome, MCheckpointIncomeChange, MUserLeader, LLeaderChange
from task.callback_task import fission_schema, cash_exchange, select_user_id, get_channel_user_ids, get_callback_infos
from task.check_sign import check_xw_sign, check_ibx_sign, check_jxw_sign, check_yw_sign, check_dy_sign, check_zb_sign
from util.log import logger
from util.static_methods import serialize

routes = web.RouteTableDef()


# 查看当前用户闯关状态->当前关卡状态
@routes.get('/checkpoint')
async def get_checkpoint(request):
    logger.info({**request.query})
    connection = request['db_connection']
    # 获取user_id
    user_id = await select_user_id(connection, request.query.get('token'))
    # 查询用户闯关数据
    select_user_point = select([MCheckpointRecord]).where(
        MCheckpointRecord.user_id == user_id
    ).order_by(MCheckpointRecord.checkpoint_number.desc()).limit(1)
    cur = await connection.execute(select_user_point)
    rec = await cur.fetchone()
    if not rec:
        # 插入第一关
        await connection.execute(insert(MCheckpointRecord).values({
            "user_id": user_id,
            "checkpoint_number": 1 if not rec else rec['checkpoint_number'] + 1,
            "create_time": int(time.time() * 1000),
            "end_time": 0,
            "current_coin": 0,
            "current_invite": 0,
            "current_points": 0,
            "reward_amount": 0,
            "state": 0
        }))
    else:
        # 上一关已完成
        if rec['state'] == 2:
            # 上一关大于等于第七关
            if rec['checkpoint_number'] >= 7:
                return web.json_response({
                    "code": 200,
                    "message": "已达终点"
                })

            # 小于第七关
            else:
                # 插入下一关数据
                await connection.execute(insert(MCheckpointRecord).values({
                    "user_id": user_id,
                    "checkpoint_number": rec['checkpoint_number'] + 1,
                    "create_time": int(time.time() * 1000),
                    "end_time": 0,
                    "current_coin": 0,
                    "current_invite": 0,
                    "current_points": 0,
                    "reward_amount": 0,
                    "state": 0
                }))
    # 查询关卡具体指标
    select_user_point = select([MCheckpointRecord]).where(
        MCheckpointRecord.user_id == user_id
    ).order_by(MCheckpointRecord.checkpoint_number.desc()).limit(1)
    cur = await connection.execute(select_user_point)
    rec = await cur.fetchone()
    checkpoint = rec['checkpoint_number'] if rec else 1
    select_checkpoint = select([MCheckpoint]).where(
        MCheckpoint.checkpoint_number == checkpoint
    )
    cur_point = await connection.execute(select_checkpoint)
    rec_point = await cur_point.fetchone()
    if rec_point:
        result = {
            "checkpoint_number": rec_point['checkpoint_number'],
            "current_coin": rec['current_coin'] if rec else 0,
            "gold_number": rec_point['gold_number'],
            "current_invite": rec['current_invite'] if rec else 0,
            "friends_number": rec_point['friends_number'],
            "current_points": rec['current_points'] if rec else 0,
            "friends_checkpoint_number": rec_point['friends_checkpoint_number'],
            "create_time": rec['create_time'] if rec else int(time.time() * 1000),
            "end_time": rec['end_time'] if rec else 0,
            "task_info": rec_point['task_info'] if rec_point else "任务要求",
            "reward_amount": int(rec_point['reward_amount']) if rec_point else 0,
            "state": rec['state'] if rec else 0
        }
    select_income = select([MCheckpointIncome]).where(
        MCheckpointIncome.user_id == user_id
    )
    cur_income = await connection.execute(select_income)
    rec_income = await cur_income.fetchall()
    current_amount = sum([int(income['amount']) for income in rec_income]) if rec_income else 0
    json_result = {
        "code": 200,
        "message": "success",
        "data": result,
        "amount": current_amount
    }
    logger.info(json_result)
    return web.json_response(json_result)


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
@routes.post('/checkpoint')
async def post_checkpoint_point(request):
    connection = request['db_connection']
    r_json = await request.post()
    logger.info(r_json)
    # r_json['checkpoint_number'] = int(r_json['checkpoint_number'])
    user_id = await select_user_id(connection, r_json['token'])
    print(user_id)
    # 查询当前关数
    select_current_point = select([MCheckpointRecord]).where(
        MCheckpointRecord.user_id == user_id
    ).order_by(MCheckpointRecord.checkpoint_number.desc())
    cur_current = await connection.execute(select_current_point)
    rec_current = await cur_current.fetchall()
    # 如果申请开启关数为正确关数,则通过
    # print(rec_current)
    # state = False
    # if rec_current:
    #     if len(rec_current) == int(r_json['checkpoint_number']) - 1:
    #         state = True
    # else:
    #     state = True
    # if state == True:
    # 查询关卡条件
    select_checkpoint = select([MCheckpoint]).where(
        MCheckpoint.checkpoint_number == int(r_json['checkpoint_number'])
    )
    cur_checkpoint = await connection.execute(select_checkpoint)
    rec_checkpoint = cur_checkpoint.fetchone()
    record_info = {
        "user_id": user_id,
        "checkpoint_number": r_json['checkpoint_number'],
        "create_time": int(time.time() * 1000),
        "end_time": 0,
        "current_coin": 0,
        "current_invite": 0,
        "current_points": 0,
        "reward_amount": 0,
        "state": 1
    }
    ins = insert(MCheckpointRecord)
    insert_stmt = ins.values(record_info)
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
        user_id=insert_stmt.inserted.user_id,
        checkpoint_number=insert_stmt.inserted.checkpoint_number,
        create_time=insert_stmt.inserted.create_time,
        end_time=insert_stmt.inserted.end_time,
        current_coin=insert_stmt.inserted.current_coin,
        current_invite=insert_stmt.inserted.current_invite,
        current_points=insert_stmt.inserted.current_points,
        reward_amount=insert_stmt.inserted.reward_amount,
        state=insert_stmt.inserted.state
    )
    await connection.execute(on_duplicate_key_stmt)
    return web.json_response({
        "code": 200,
        "message": "开启闯关成功"
    })


# else:
#     return web.json_response({
#         "code": 402,
#         "message": "闯关开启异常"
#     })


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
            MCheckpointRecord.checkpoint_number == params['checkpoint_number'],
            MCheckpointRecord.state == 0
        )
    )
    cur_record = await connection.execute(select_record)
    rec_record = await cur_record.fetchone()
    if rec_record and rec_record['current_coin'] >= rec_checkpoint['gold_number'] \
            and rec_record['current_invite'] >= rec_checkpoint['friends_number'] \
            and rec_record['current_points'] >= rec_checkpoint['friends_checkpoint_number']:

        one_reward = float(rec_checkpoint['reward_amount']) / 3
        start = 0
        end = one_reward
        result = []
        for i in range(3):
            reward = uniform(start, end)
            start += one_reward
            end += one_reward
            result.append(round(reward, 2))
        # await connection.execute(update(MCheckpointRecord).values({
        #     "state": 1
        # }).where(
        #     and_(
        #         MCheckpointRecord.user_id == user_id,
        #         MCheckpointRecord.checkpoint_number == params['checkpoint_number'],
        #         MCheckpointRecord.state == 0
        #     )
        # ))
        json_result = {
            "code": 200,
            "message": "success",
            "data": result
        }
    else:
        json_result = {
            "code": 402,
            "message": "闯关要求未达标或该关已通过",
            "data": []
        }
    return web.json_response(json_result)


# 提交抽牌结果,完成结算
@routes.post('/checkpoint/card')
async def post_checkpoint_card(request):
    r_json = await request.post()
    connection = request['db_connection']
    user_id = await select_user_id(connection, r_json['token'])
    select_exist_record = select([MCheckpointRecord]).where(
        and_(
            MCheckpointRecord.user_id == user_id,
            MCheckpointRecord.checkpoint_number == r_json['checkpoint_number']
        )
    )
    cur = await connection.execute(select_exist_record)
    rec = await cur.fetchone()
    if rec and rec['state'] == 2:
        return web.json_response({
            "code": 402,
            "message": "奖励已发"
        })

    # 查询闯关指标,判断指标
    select_check = select([MCheckpoint]).where(
        MCheckpoint.checkpoint_number == r_json['checkpoint_number']
    )
    cur_check = await connection.execute(select_check)
    rec_check = await cur_check.fetchone()
    if rec['current_coin'] < rec_check['gold_number'] or \
            rec['current_invite'] < rec_check['friends_number'] or \
            rec['current_points'] < rec_check['friends_checkpoint_number']:
        return web.json_response({
            "code": 402,
            "message": "任务条件未达成"
        })

    result_value = {
        "end_time": int(time.time() * 1000),
        "reward_amount": rec_check['reward_amount'],
        "state": 2
    }
    await connection.execute(update(MCheckpointRecord).values(result_value).where(
        and_(
            MCheckpointRecord.user_id == user_id,
            MCheckpointRecord.checkpoint_number == r_json['checkpoint_number'],
            MCheckpointRecord.state == 1
        )
    ))
    # 插入闯关解锁金额表
    await connection.execute(insert(MCheckpointIncome).values({
        "user_id": user_id,
        "amount": rec_check['reward_amount'],
        "create_time": int(time.time() * 1000),
        "update_time": int(time.time() * 1000),
    }))
    # # 新建下一关数据
    # if r_json['checkpoint_number']+1 <= 7:
    #     await connection.execute(update(MCheckpointRecord).values({
    #         "user_id": user_id,
    #         "checkpoint_number": r_json['checkpoint_number']+1,
    #         "create_time": int(time.time() * 1000),
    #         "end_time": 0,
    #         "current_coin": 0,
    #         "current_invite": 0,
    #         "current_points": 0,
    #         "reward_amount": 0,
    #         "state": 0
    #     }))
    json_result = {
        "code": 200,
        "message": "本关奖励顺利发放"
    }
    return web.json_response(json_result)


# 提交导入到钱包的金额
@routes.post('/checkpoint/cash')
async def get_reward(request):
    params = await request.post()
    cash = int(params['cash'])
    connection = request['db_connection']
    user_id = await select_user_id(connection, params['token'])
    # 查询金额表,确定余额可用
    select_income = select([MCheckpointIncome]).where(
        MCheckpointIncome.user_id == user_id
    )
    cur = await connection.execute(select_income)
    rec = await cur.fetchall()
    sum_cash = sum([i['amount'] for i in rec])
    if sum_cash < cash:
        return web.json_response({
            "code": 400,
            "message": "解锁金额不足"
        })
    # 插入金额转换表
    await connection.execute(insert(MCheckpointIncomeChange).values(
        {
            "user_id": user_id,
            "change_amount": int(cash),
            "create_time": int(time.time() * 1000),
            "update_time": int(time.time() * 1000),
        }
    ))
    # 调用发币方法
    await cash_exchange(connection, user_id, int(cash) * 10000, 12, "闯关奖励导入", "闯关获取解锁金额")

    return web.json_response({
        "code": 200,
        "message": "success"
    })


# 团队奖励统计
@routes.get('/partner/reward_detail')
async def get_partner_reward_detail(request):
    token = request.query.get('token')
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)
    # 查团队ids
    select_team_ids = select([MUserLeader]).where(
        and_(
            MUserLeader.leader_id == user_id,
            MUserLeader.user_id != user_id
        )
    )
    cur = await connection.execute(select_team_ids)
    rec = await cur.fetchall()
    team_ids = [user['user_id'] for user in rec]

    # 查流水
    select_change = select([LCoinChange]).where(
        and_(
            LCoinChange.user_id == user_id,
            LCoinChange.flow_type == 1,
            or_(
                LCoinChange.changed_type == 35,  # 一级直属用户
                LCoinChange.changed_type == 36  # 二级直属用户
            )
        )
    )
    cur_change = await connection.execute(select_change)
    rec_change = await cur_change.fetchall()
    teamBenefit = sum([change['amount'] for change in rec_change])
    json_result = {
        "data": {
            "reward": 1,
            "teamBenefit": teamBenefit if rec_change else 0,  # 我的团队总收益->金币
            "directProfit": 3,
            "drReward": teamBenefit if rec_change else 0,  # 团队详情->收益->金币
            "ordinaryProfit": 5,
            "directPeopleNum": 6,
            "highVipAmount": 7,
            "indirectPeopleNum": 8,
            "additionalProfit": 9,
            "ordinaryPeopleNum": 10,
            "isiIndirectProfit": 12,
            "highVipCount": 13,
            "indirectProfit": 14,
            "drPeopleNum": len(team_ids) if rec else 0  # 团队详情->人数
        },
        "message": "操作成功",
        "statusCode": "2000",
        "token": token
    }
    return web.json_response(json_result)


# 团队奖励详情
@routes.get('/partner/partner_detail')
async def get_partner_reward_detail(request):
    token = request.query.get('token')
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)
    # 查询团队流水
    select_team = select([LLeaderChange]).where(
        LLeaderChange.leader_id == user_id
    )
    cur = await connection.execute(select_team)
    rec = await cur.fetchall()
    list_info = []
    for info in rec:
        result = {
            "drReward": '10000',
            "drPeopleNum": '20000',
            "updateTime": info['create_time'].strftime('%Y-%m-%d') if info else '2000-01-01',
            "apprenticeCount": info['active_user'] if info else 0,
            "firstReward": 0,
            "secondReward": 0,
            "total": info['total_reward'] if info else 0,
            "per": '0'
        }
        list_info.append(result)
    json_result = {
        "data": {
            "lastPage": 0,
            "navigatepageNums": [],
            "startRow": 0,
            "hasNextPage": False,
            "prePage": 0,
            "nextPage": 0,
            "endRow": 0,
            "pageSize": 50,
            "list": list_info,
            "pageNum": 1,
            "navigatePages": 8,
            "navigateFirstPage": 0,
            "total": 2000,
            "pages": 0,
            "firstPage": 0,
            "size": 0,
            "isLastPage": True, "hasPreviousPage": False, "navigateLastPage": 0, "isFirstPage": True
        },
        "message": "操作成功",
        "statusCode": "2000",
        "token": token}
    return web.json_response(json_result)


# 团队奖励明细
@routes.get('/partner/team_detail')
async def get_partner_team_detail(request):
    params = {**request.query}
    connection = request['db_connection']
    user_id = await select_user_id(connection, params['token'])
    floor_dict = {
        '1': "35",
        '2': "36",
        '3': ""
    }
    name_dict = {
        35: "直属一级奖励",
        36: "直属二级奖励",
    }
    # 查询一二级下级流水表
    coditions = []
    coditions.append(or_(LCoinChange.changed_type == 35, LCoinChange.changed_type == 36))
    if user_id:
        coditions.append(LCoinChange.user_id == user_id)
    if 'friend_floor' in params and floor_dict[params['friend_floor']]:
        coditions.append(LCoinChange.changed_type == int(floor_dict[params['friend_floor']]))
    print(coditions)
    select_coin_change = select([LCoinChange]).where(and_(*coditions)).order_by(LCoinChange.changed_time.desc())
    cur = await connection.execute(select_coin_change)
    rec = await cur.fetchall()

    list_info = []
    for row in rec:
        result = {
            "id": row['id'],
            "friend_floor": name_dict[row['changed_type']],
            "reward_time": row['changed_time'],
            "reward": row['amount']
        }
        list_info.append(result)

    json_result = {
        "data": {
            "total": len(list_info),
            "list": list_info
        },
        "message": "操作成功",
        "statusCode": "2000",
        "token": params['token']
    }
    return web.json_response(json_result)


# 闯关助力
@routes.post('/partner/boost')
async def post_boost(request):
    # params = {**request.query}
    params = await request.post()
    connection = request['db_connection']
    user_id = await select_user_id(connection, params['token'])
    # 查询leader
    select_leader = select([MUserLeader]).where(
        and_(
            MUserLeader.user_id == user_id,
            MUserLeader.leader_id != user_id
        )
    )
    cur = await connection.execute(select_leader)
    rec = await cur.fetchone()
    # 查询今日是否助力
    # 获取今天零点
    now = datetime.now()
    zeroToday = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
    # 获取23:59:59
    lastToday = zeroToday + timedelta(hours=23, minutes=59, seconds=59)
    zeroTodaytime = time.mktime(zeroToday.timetuple()) * 1000
    lastTodaytime = time.mktime(lastToday.timetuple()) * 1000
    select_change = select([LCoinChange]).where(
        and_(
            LCoinChange.changed_time > zeroTodaytime,
            LCoinChange.changed_time < lastTodaytime,
            LCoinChange.remarks == user_id
        )
    )
    cur_today = await connection.execute(select_change)
    rec_today = await cur_today.fetchone()
    if rec_today:
        return web.json_response({
            "code": 400,
            "message": "您今天已经助力过啦!"
        })
        # 查询leader闯关状态 state = 1
    if rec:
        select_checkpoint = select([MCheckpointRecord]).where(
            and_(
                MCheckpointRecord.state == 1,
                MCheckpointRecord.user_id == rec['leader_id']
            )
        )
        cur_check = await connection.execute(select_checkpoint)
        rec_check = await cur_check.fetchone()
        select_is_boost = select([LCoinChange]).where(
            LCoinChange.remarks == user_id
        )
        cur_boost = await connection.execute(select_is_boost)
        rec_boost = await cur_boost.fetchone()
        amount = 200 if rec_boost else randint(200, 800)
        if rec_check:
            c_result = await cash_exchange(
                connection,
                user_id=rec_check['user_id'],
                amount=amount,
                changed_type=37,
                reason="闯关助力",
                remarks=user_id,
                flow_type=1
            )
            if c_result:
                return web.json_response({
                    "code": 200,
                    "message": "助力成功"
                })
            else:
                return web.json_response({
                    "code": 400,
                    "message": "助力失败,请联系管理员"
                })
        else:
            return web.json_response({
                "code": 400,
                "message": "上级合伙人不在闯关状态,无法助力"
            })
    else:
        return web.json_response({
            "code": 400,
            "message": "无上级合伙人可助力"
        })
