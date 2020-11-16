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
    MCheckpointRecord, MCheckpoint, MCheckpointIncome, MCheckpointIncomeChange, MUserLeader, LLeaderChange, \
    LPartnerChange, MPartnerInfo, MWageRecord, MWageLevel
from services.partner import leader_detail, check_current_invite, check_current_coin
from task.callback_task import fission_schema, cash_exchange, select_user_id, get_channel_user_ids, get_callback_infos, \
    insert_exchange_cash
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
            "current_videos": 0,
            "current_games": 0,
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

    # 查询下属闯关大于指标数个数
    if rec and rec_point:
        current_invite = await check_current_invite(connection, user_id, rec['current_invite'],
                                                    rec_point['friends_checkpoint_number'], rec['create_time'])
        current_coin = await check_current_coin(connection, user_id, rec['current_coin'], rec['create_time'])
        result = {
            "checkpoint_number": rec_point['checkpoint_number'],
            "current_coin": current_coin if rec else 0,
            "gold_number": rec_point['gold_number'],
            "current_videos": rec['current_videos'] if rec and rec['current_videos'] else 0,
            "video_number": rec_point['video_number'],
            "current_games": rec['current_games'] if rec and rec['current_games'] else 0,
            "game_number": rec_point['game_number'],
            "current_invite": current_invite if rec and rec_point else 0,
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
    select_income_change = select([MCheckpointIncomeChange]).where(
        MCheckpointIncomeChange.user_id == user_id
    )
    cur_income_change = await connection.execute(select_income_change)
    rec_income_change = await cur_income_change.fetchall()
    if rec_income and rec_income_change:
        current_amount = sum([int(income['amount']) for income in rec_income]) - sum(
            [int(income['change_amount']) for income in rec_income_change])
    else:
        current_amount = sum([int(income['amount']) for income in rec_income])
    if current_amount < 0:
        current_amount = 0
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
    # select_current_point = select([MCheckpointRecord]).where(
    #     MCheckpointRecord.user_id == user_id
    # ).order_by(MCheckpointRecord.checkpoint_number.desc())
    # cur_current = await connection.execute(select_current_point)
    # rec_current = await cur_current.fetchall()
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
    # select_checkpoint = select([MCheckpoint]).where(
    #     MCheckpoint.checkpoint_number == int(r_json['checkpoint_number'])
    # )
    # cur_checkpoint = await connection.execute(select_checkpoint)
    # rec_checkpoint = await cur_checkpoint.fetchone()
    record_info = {
        "user_id": user_id,
        "checkpoint_number": r_json['checkpoint_number'],
        "create_time": int(time.time() * 1000),
        "end_time": 0,
        "current_coin": 0,
        "current_invite": 0,
        "current_points": 0,
        "current_videos": 0,
        "current_games": 0,
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
        current_videos=insert_stmt.inserted.current_videos,
        current_games=insert_stmt.inserted.current_games,
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
            rec['current_points'] < rec_check['friends_checkpoint_number'] or \
            rec['current_videos'] < rec_check['video_number'] or \
            rec['current_games'] < rec_check['game_number']:
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
    if cash != 10:
        return web.json_response({
            "code": 400,
            "message": "导入金额不合法，满10元提现"
        })
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


# 获取每日工资状态
@routes.get('/user/wage')
async def get_user_wage(request):
    token = request.query.get('token')
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)
    now = datetime.now()
    today_time = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                 microseconds=now.microsecond)
    select_user_wage = select([MWageRecord]).where(
        and_(
            MWageRecord.user_id == user_id,
            MWageRecord.create_time == today_time
        )
    )
    cur_user_wage = await connection.execute(select_user_wage)
    rec_user_wage = await cur_user_wage.fetchone()
    if rec_user_wage:
        select_wage_level = select([MWageLevel]).where(
            MWageLevel.wage_level == rec_user_wage['wage_level']
        )
        cur_wage_level = await connection.execute(select_wage_level)
        rec_wage_level = await cur_wage_level.fetchone()
        result = {
            "wage_level": rec_user_wage['wage_level'],
            "wage_info": rec_wage_level['wage_info'],
            "status": rec_user_wage['status'],
            "current_video": rec_user_wage['current_video'],
            "current_game": rec_user_wage['current_game'],
            "game_number": rec_wage_level['game_number'],
            "video_number": rec_wage_level['video_number'],
            "reward": rec_wage_level['reward'],
        }
    else:
        result = {
            "wage_level": 0,
            "wage_info": "",
            "status": 0,
            "current_video": 0,
            "current_game": 0,
            "game_number": 0,
            "video_number": 0,
            "reward": 0
        }
    json_result = {
        "code": 200,
        "message": "success",
        "data": result,
        "current_reward": rec_user_wage['reward'] if rec_user_wage else 0
    }
    return web.json_response(json_result)


# 接取每日工资任务
@routes.post('/user/wage')
async def post_user_wage(request):
    params = await request.post()
    token = params['token']
    wage_level = int(params['wage_level'])
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)
    now = datetime.now()
    today_time = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                 microseconds=now.microsecond)
    select_user_wage = select([MWageRecord]).where(
        and_(
            MWageRecord.user_id == user_id,
            MWageRecord.create_time == today_time
        )
    )
    cur_user_wage = await connection.execute(select_user_wage)
    rec_user_wage = await cur_user_wage.fetchone()
    # 今日任务已接取
    if rec_user_wage:
        return web.json_response({
            "code": 400,
            "message": "今日任务已接取"
        })
    else:
        select_wage_level = select([MWageLevel]).where(
            MWageLevel.wage_level == wage_level
        )
        cur_wage_level = await connection.execute(select_wage_level)
        rec_wage_level = await cur_wage_level.fetchone()
        try:
            await connection.execute(
                insert(MWageRecord).values(
                    {
                        "user_id": user_id,
                        "create_time": today_time,
                        "reward": 0,
                        "wage_level": rec_wage_level['wage_level'],
                        "current_game": 0,
                        "current_video": 0,
                        "status": 1,
                        "update_time": today_time,
                    }
                )
            )
            json_result = {
                "code": 200,
                "message": "接取成功",
                "data": {
                    "wage_level": rec_wage_level['wage_level'],
                    "wage_info": rec_wage_level['wage_level'],
                    "status": 1,
                    "current_video": 0,
                    "current_game": 0,
                    "game_number": rec_wage_level['wage_level'],
                    "video_number": rec_wage_level['wage_level'],
                    "reward": rec_wage_level['wage_level']
                }
            }
        except Exception as e:
            logger.info(e)
            json_result = {
                "code": 400,
                "message": "接取失败",
                "data": {}
            }
    return web.json_response(json_result)


# 提交并结算每日工资
@routes.get('/user/wage/cash')
async def get_wage_cash(request):
    token = request.query.get('token')
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)
    now = datetime.now()
    today_time = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                 microseconds=now.microsecond)
    select_user_wage = select([MWageRecord]).where(
        and_(
            MWageRecord.user_id == user_id,
            MWageRecord.create_time == today_time
        )
    )
    cur_user_wage = await connection.execute(select_user_wage)
    rec_user_wage = await cur_user_wage.fetchone()
    select_wage_level = select([MWageLevel]).where(
        MWageLevel.wage_level == rec_user_wage['wage_level']
    )
    cur_wage_level = await connection.execute(select_wage_level)
    rec_wage_level = await cur_wage_level.fetchone()
    if rec_user_wage and rec_wage_level:
        if rec_user_wage['status'] == 2:
            return web.json_response({
                "code": 400,
                "message": "任务已结算"
            })
        if rec_user_wage['current_game'] >= rec_wage_level['game_number'] and \
                rec_user_wage['current_video'] >= rec_wage_level['video_number']:
            await connection.execute(
                update(MWageRecord).values({
                    "status": 2,
                    "reward": rec_wage_level['reward'],
                    "update_time": datetime.now()
                }).where(
                    and_(
                        MWageRecord.user_id == user_id,
                        MWageRecord.create_time == today_time
                    )
                )
            )
            json_result = {
                "code": 200,
                "message": "提交并结算成功"
            }
        else:
            json_result = {
                "code": 400,
                "message": "任务指标未达标"
            }
    else:
        json_result = {
            "code": 400,
            "message": "缺少任务信息"
        }

    return web.json_response(json_result)


# 提现今日工资
@routes.post('/user/wage/cash')
async def post_wage_cash(request):
    params = await request.post()
    token = params['token']
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)
    now = datetime.now()
    today_time = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                 microseconds=now.microsecond)
    select_user_wage = select([MWageRecord]).where(
        and_(
            MWageRecord.create_time == today_time,
            MWageRecord.user_id == user_id
        )
    )
    cur_user_wage = await connection.execute(select_user_wage)
    rec_user_wage = await cur_user_wage.fetchone()
    if rec_user_wage:
        if rec_user_wage['status'] == 2:
            # 任务验证成功发起提现
            cash_result, toast = await insert_exchange_cash(connection, user_id, rec_user_wage['reward'],
                                                            rec_user_wage['create_time'])
            json_result = {
                "code": 200 if cash_result else 400,
                "message": toast
            }
        elif rec_user_wage['status'] == 3:
            json_result = {
                "code": 400,
                "message": "今日工资已提现"
            }
        else:
            json_result = {
                "code": 400,
                "message": "每日工资未获取"
            }
    else:
        json_result = {
            "code": 400,
            "message": "清先接取每日工资任务"
        }
    return web.json_response(json_result)


# 主页统计表
@routes.get('/partner/index')
async def get_partner_index(request):
    token = request.query.get('token')
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)
    # 查询leader收益
    select_leader_change = select([LCoinChange]).where(
        and_(
            LCoinChange.user_id == user_id,
            LCoinChange.changed_type == 5
        )
    )
    cur_l_change = await connection.execute(select_leader_change)
    rec_l_change = await cur_l_change.fetchall()
    teamBenefit = 0
    if rec_l_change:
        teamBenefit = sum([change['amount'] for change in rec_l_change])
    # 查询partner收益
    select_partner_change = select([LPartnerChange]).where(
        LPartnerChange.partner_id == user_id
    )
    cur_p_change = await connection.execute(select_partner_change)
    rec_p_change = await cur_p_change.fetchall()
    sum_partner_reward = 0
    for partner_change in rec_p_change:
        sum_partner_reward += partner_change['one_reward']
        sum_partner_reward += partner_change['two_reward']
    teamBenefit += sum_partner_reward
    # 查询leader下级人数
    select_leader = select([MUserLeader]).where(
        MUserLeader.leader_id == user_id
    )
    cur_leader = await connection.execute(select_leader)
    rec_leader = await cur_leader.fetchall()

    # 查询当前Muserinfo
    select_muser = select([MUserInfo]).where(
        MUserInfo.user_id == user_id
    )
    cur = await connection.execute(select_muser)
    rec = await cur.fetchone()
    json_result = {
        "data": {
            "isRenewal": 2,
            "teamBenefit": teamBenefit if rec_l_change else 0,
            "ordinaryRewardImg": "http://qiniu.shouzhuan518.com/小麒麟规则.png",
            "photo": rec['profile'] if rec and rec['profile'] else "https://image.bzlyplay.com/default_img.png",
            "inviteImg": "http://qiniu.shouzhuan518.com/pro_20201009163222476.png",
            "roleType": rec['role_type'],
            "accountId": rec['account_id'],
            "teamRewardImg": "http://qiniu.shouzhuan518.com/金麒麟规则.png",
            "qrCode": rec['qr_code'],
            "highRole": rec['high_role'],
            "price": 999,
            "darenRewardImg": "http://qiniu.shouzhuan518.com/玉麒麟规则.png",
            "surplusTime": 0,
            "schemeImg": "http://qiniu.shouzhuan518.com/pro_202010091631585262.png",
            "apprentice": rec['apprentice']
        },
        "message": "操作成功",
        "statusCode": "2000",
        "token": token
    }
    return web.json_response(json_result)


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

    # 查询合伙人情况
    select_partner_change = select([LPartnerChange]).where(
        LPartnerChange.partner_id == user_id
    ).order_by(LPartnerChange.create_time.desc())
    cur_p_change = await connection.execute(select_partner_change)
    rec_p_chenge = await cur_p_change.fetchall()
    sum_total_reward = 0
    for row in rec_p_chenge:
        sum_total_reward += row['one_reward']
        sum_total_reward += row['two_reward']
    json_result = {
        "data": {
            "reward": 1,
            "teamBenefit": teamBenefit if rec_change else 0,  # 我的团队总收益->金币
            "directProfit": 3,
            "drReward": teamBenefit if rec_change else 0,  # 团队详情->收益->金币
            "ordinaryProfit": sum_total_reward,  # 合伙人累计收益
            "directPeopleNum": 6,
            "highVipAmount": 7,
            "indirectPeopleNum": 8,
            "additionalProfit": 9,
            "ordinaryPeopleNum": rec_p_chenge[0]['one_count'] + rec_p_chenge[0]['two_count'] if rec_p_chenge else 0,
            # 合伙人数
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
        '3': "38"
    }
    name_dict = {
        35: "直属一级奖励",
        36: "直属二级奖励",
        38: "直属二级以下奖励",
    }
    # 查询一二级下级流水表
    coditions = []
    coditions.append(
        or_(LCoinChange.changed_type == 35, LCoinChange.changed_type == 36, LCoinChange.changed_type == 38))
    if user_id:
        coditions.append(LCoinChange.user_id == user_id)
    # if 'friend_floor' in params and floor_dict[params['friend_floor']]:
    #     coditions.append(LCoinChange.changed_type == int(floor_dict[params['friend_floor']]))
    print(coditions)
    select_coin_change = select([LCoinChange]).where(and_(*coditions)).order_by(LCoinChange.changed_time.desc())
    cur = await connection.execute(select_coin_change)
    rec = await cur.fetchall()

    list_info = []
    sum_1 = 0
    sum_2 = 0
    sum_3 = 0
    for row in rec:
        result = {
            "id": row['id'],
            "friend_floor": name_dict[row['changed_type']],
            "reward_time": row['changed_time'],
            "reward": row['amount']
        }
        if row['changed_type'] == 35:
            sum_1 += row['amount']
            if 'friend_floor' in params and params['friend_floor'] == '1':
                list_info.append(result)
        elif row['changed_type'] == 36:
            sum_2 += row['amount']
            if 'friend_floor' in params and params['friend_floor'] == '2':
                list_info.append(result)
        elif row['changed_type'] == 38:
            sum_3 += row['amount']
            if 'friend_floor' in params and params['friend_floor'] == '3':
                list_info.append(result)
        if 'friend_floor' not in params:
            list_info.append(result)
    json_result = {
        "data": {
            "total": len(list_info),
            "list": list_info,
            "sum_1": sum_1,
            "sum_2": sum_2,
            "sum_3": sum_3
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


# 下级代理收益
@routes.get('/partner/agent_detail')
async def get_agent_detail(request):
    token = request.query.get('token')
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)
    select_partner_change = select([LPartnerChange]).where(
        LPartnerChange.partner_id == user_id
    ).order_by(LPartnerChange.create_time.desc())
    cur = await connection.execute(select_partner_change)
    rec = await cur.fetchall()
    list_info = []
    sum_total_reward = 0

    for row in rec:
        result = {
            "apprenticeCount": row['active_partner'],
            "drPeopleNum": "20000",
            "drReward": "10000",
            "firstReward": row['one_reward'],
            "per": "0",
            "secondReward": row['two_reward'],
            "total": 0,
            "updateTime": row['create_time'].strftime('%Y-%m-%d')
        }
        sum_total_reward += row['one_reward']
        sum_total_reward += row['two_reward']
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
            "pageSize": 10,
            "list": list_info,
            "total_reward": sum_total_reward,  # 累计收益
            "partner_count": rec[0]['one_count'] + rec[0]['two_count'] if rec else 0,  # 合伙人数
            "pageNum": 1,
            "navigatePages": 8,
            "navigateFirstPage": 0,
            "total": 0,
            "pages": 0,
            "firstPage": 0,
            "size": 0,
            "isLastPage": True,
            "hasPreviousPage": False,
            "navigateLastPage": 0,
            "isFirstPage": True
        },
        "message": "操作成功",
        "statusCode": "2000",
        "token": token
    }
    return web.json_response(json_result)


# 下级代理详情
@routes.get('/partner/leader_detail')
async def get_leader_detail(request):
    token = request.query.get('token')
    connection = request['db_connection']
    user_id = await select_user_id(connection, token)

    list_info, sum_1, sum_2 = await leader_detail(connection, user_id)

    json_result = {
        "data": {
            "total": len(list_info),
            "list": list_info,
            "sum_1": sum_1,
            "sum_2": sum_2
        },
        "message": "操作成功",
        "statusCode": "2000",
        "token": token
    }
    return web.json_response(json_result)
