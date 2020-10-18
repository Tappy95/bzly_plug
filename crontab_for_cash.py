# import sys
# # sys.path.append("/root/bzly_plug")
# print(sys.path)

import time
from datetime import datetime
import random

from sqlalchemy import select, create_engine, insert, update, delete, and_

from config import *
from models.alchemy_models import LUserExchangeCash, LUserCashLogPY, MUserInfo, LCoinChange, CCheckinLog, CCheckinResult
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


# 提现奖励师傅,3分钟一次
async def cash_reward():
    print(0.0)
    # 创建连接对象
    with engine.connect() as conn:
        # 遍历提现信息表,state = 5---提现通过
        select_ex_cash = select([LUserExchangeCash]).where(
            LUserExchangeCash.state == 5
        )
        c_cash = conn.execute(select_ex_cash)
        r_cash = c_cash.fetchall()
        cash_infos = serialize(c_cash, r_cash)
        # logger.info(cash_infos)
        for cash_info in cash_infos:
            logger.info(cash_info["id"])
            # 利用信息id和log表做关联,查是否存在此log记录
            select_cash_log = conn.execute(select([LUserCashLogPY]).where(
                LUserCashLogPY.id == cash_info["id"]
            )).fetchone()
            if select_cash_log:
                logger.info("已存在记录:{}".format(select_cash_log))
                continue
            else:
                # 查询此用户已提现次数
                select_cash_count = conn.execute(select([LUserCashLogPY]).where(
                    LUserCashLogPY.user_id == cash_info['user_id']
                )).fetchall()
                count = len(select_cash_count)
                # 查出再信息表缺不在log表的信息
                count += 1
                logger.info("新增提现记录:{}".format(cash_info['id']))
                # 插入新增信息进入log表
                cash_log = {
                    "id": cash_info['id'],
                    "user_id": cash_info['user_id'],
                    "out_trade_no": cash_info['out_trade_no'],
                    "cash_coin": cash_info['coin'],
                    "cash_time": cash_info['examine_time'],
                    "cash_num": count
                }
                conn.execute(insert(LUserCashLogPY).values(cash_log))
                reward = [1, 2, 5]
                if count <= 3:
                    amount = reward[count - 1] * cash_info['coin_to_money']
                    # 查询用户是否有师傅
                    select_user_teacher = conn.execute(select([MUserInfo]).where(
                        MUserInfo.user_id == cash_log['user_id']
                    )).fetchone()

                    if select_user_teacher:
                        # 根据徒弟提现次数给师傅发奖励(单位RMB)

                        # 查询师傅金币信息
                        select_teacher = conn.execute(select([MUserInfo]).where(
                            MUserInfo.user_id == select_user_teacher['referrer']
                        )).fetchone()
                        if select_teacher:
                            # 添加流水记录
                            insert_exchange = {
                                "user_id": select_user_teacher['referrer'],
                                "amount": amount,
                                "flow_type": 1,
                                "changed_type": 5,
                                "changed_time": int(round(time.time() * 1000)),
                                "status": 1,
                                "account_type": 0,
                                "reason": "徒弟第{}提现奖励".format(count),
                                "remarks": "徒弟贡献",
                                "coin_balance": select_teacher['coin'] + amount
                            }
                            conn.execute(insert(LCoinChange).values(insert_exchange))
                            # 修改账户金币余额
                            # 更改用户金币
                            update_teacher_coin = update(MUserInfo).values({
                                "coin": insert_exchange['coin_balance']
                            }).where(
                                MUserInfo.user_id == select_user_teacher['referrer']
                            )
                            conn.execute(update_teacher_coin)


# 维护faker状态,每天3点更新用户状态
async def checkin_faker():
    logger.info("Begain create checkin faker,and update exist faker checkin time")
    # 获取整点时间
    cur_hour = int(datetime.fromtimestamp(time.time()).strftime('%H'))
    if cur_hour == 2:
        # 创建或补齐选定数faker
        # 选定标准数
        today_faker_number = [522, 534, 224, 328, 213, 211, 633, 466]
        faker_number = random.sample(today_faker_number, 1)[0]
        # 查询已存在的faker数量
        with engine.connect() as conn:
            select_exist_faker = conn.execute(
                select([CCheckinLog]).where(CCheckinLog.user_type == 2).order_by(CCheckinLog.id.asc())).fetchall()
            # 已存在faker数量
            now_count = len(select_exist_faker)
            new_faker_number = faker_number - now_count
            if new_faker_number > 0:
                # 循环创建用户
                # 差额正数,补齐创建faker
                fakers = []
                for user in range(new_faker_number - 1):
                    faker = {
                        "user_id": "faker",
                        "pay_coin": 10000,
                        "user_type": 2,
                        "state": 2,
                        "create_time": int(time.time() * 1000),
                        "checkin_time": int(time.time() * 1000),
                        "is_tips": 1,
                        "is_coupon": 1
                    }
                    fakers.append(faker)
                conn.execute(insert(CCheckinLog).values(fakers))
            elif new_faker_number < 0:
                select_fakers = conn.execute(
                    select([CCheckinLog.id]).where(CCheckinLog.user_type == 2).limit(abs(new_faker_number))).fetchall()
                faker_ids = [faker['id'] for faker in select_fakers]
                delete_fakers = delete(CCheckinLog).where(
                    CCheckinLog.id.in_(faker_ids)
                )
                conn.execute(delete_fakers)
            # 获取时间戳,更新所有faker用户的今日签到时间
            update_fakers = update(CCheckinLog).where(
                CCheckinLog.user_type == 2
            ).values(
                {
                    "create_time": int(time.time() * 1000),
                    "checkin_time": int(time.time() * 1000)
                }
            )
            conn.execute(update_fakers)


# 更新每日签到奖池,5分钟一次
async def update_checkin_result():
    logger.info("Begain update_checkin_result")
    # 查询签到log表
    cur = time.time()
    today0 = (cur - cur % 86400 + 86400 - 8 * 3600) * 1000
    today24 = (cur - cur % 86400 + 86400 - 8 * 3600 + 86400) * 1000

    with engine.connect() as conn:
        select_if_result = conn.execute(select([CCheckinResult]).where(CCheckinResult.create_Time == today0)).fetchone()

        select_log = conn.execute(select([CCheckinLog]).where(
            and_(
                # CCheckinLog.user_type == 1,
                CCheckinLog.create_time > today0,
                CCheckinLog.create_time < today24,
            )
        )).fetchall()
        sum_all_coin = sum([user['pay_coin'] for user in select_log])
        sum_real_coin = sum([user['pay_coin'] for user in select_log if user['user_type'] == 1])
        success_number = len([user['id'] for user in select_log if user['state'] == 2])
        fail_number = len([user['id'] for user in select_log if user['state'] == 1])
        success_real_number = len([user['id'] for user in select_log if user['state'] == 2 and user['user_type'] == 1])
        fail_real_number = len([user['id'] for user in select_log if user['state'] == 1 and user['user_type'] == 1])
        checkin_result = {
            "bonus_pool": sum_all_coin,
            "success_number": success_number,
            "fail_number": fail_number,
            "success_real_number": success_real_number,
            "fail_real_number": fail_real_number,
            "create_Time": today0,
            "actual_bonus": sum_real_coin,
        }
        if select_if_result:
            conn.execute(update(CCheckinResult).where(
                CCheckinResult.id == select_if_result['id']
            ).values(checkin_result))
        else:
            ins = insert(CCheckinResult).values(checkin_result)
            conn.execute(ins)


# 每日12点根据当日真实奖池给用户发奖励,一小时一次,检测当前时间是否为午间12点
async def checkin_user_reward():
    logger.info("Begain checkin_user_reward")
    # 判断时间
    cur_hour = int(datetime.fromtimestamp(time.time()).strftime('%H'))
    cur = time.time()
    today12 = (cur - cur % 86400 + 4 * 3600) * 1000
    yesterday12 = (cur - cur % 86400 - 20 * 3600) * 1000
    if cur_hour == 12:
        # 获取当前真实用户奖池
        with engine.connect() as conn:
            # 更新当日奖池
            # 统计午间12点之间的24小时内数据
            select_if_result = conn.execute(
                select([CCheckinResult]).where(CCheckinResult.create_Time == today12)).fetchone()

            select_log = conn.execute(select([CCheckinLog]).where(
                and_(
                    # CCheckinLog.user_type == 1,
                    CCheckinLog.create_time > yesterday12,
                    CCheckinLog.create_time < today12,
                )
            )).fetchall()
            sum_all_coin = sum([user['pay_coin'] for user in select_log])
            sum_real_coin = sum([user['pay_coin'] for user in select_log if user['user_type'] == 1])
            success_number = len([user['id'] for user in select_log if user['state'] == 2])
            fail_number = len([user['id'] for user in select_log if user['state'] == 1])
            success_real_number = len(
                [user['id'] for user in select_log if user['state'] == 2 and user['user_type'] == 1])
            fail_real_number = len([user['id'] for user in select_log if user['state'] == 1 and user['user_type'] == 1])
            checkin_result = {
                "bonus_pool": sum_all_coin,
                "success_number": success_number,
                "fail_number": fail_number,
                "success_real_number": success_real_number,
                "fail_real_number": fail_real_number,
                "create_Time": today12,
                "actual_bonus": sum_real_coin,
            }
            if select_if_result:
                conn.execute(update(CCheckinResult).where(
                    CCheckinResult.id == select_if_result['id']
                ).values(checkin_result))
            else:
                ins = insert(CCheckinResult).values(checkin_result)
                conn.execute(ins)

            # 查询奖池
            select_real_pool = conn.execute(select([CCheckinResult]).where(
                CCheckinResult.create_Time == today12
            )).fetchone()
            if select_real_pool:

                # 查询所有当日成功签到用户
                select_all_reall_success_user = conn.execute(select([CCheckinLog]).where(
                    and_(
                        CCheckinLog.user_type == 1,
                        CCheckinLog.state == 2
                    )
                )).fetchall()

                # 如果签到成功用户==真实奖池,每人发1w金币
                if len(select_all_reall_success_user) == select_real_pool['actual_bonus'] / 10000:
                    reward_coin = 10000
                # 如果成功用户数<真实奖池,开启随机,循环递减
                else:
                    reward_coin = select_real_pool['actual_bonus'] / len(select_all_reall_success_user)

                for user in select_all_reall_success_user:
                    # 查询用户余额
                    select_success_user = conn.execute(select([MUserInfo]).where(
                        MUserInfo.user_id == user['user_id']
                    )).fetchone()
                    if select_success_user:
                        # 奖励用户
                        insert_exchange = {
                            "user_id": user['user_id'],
                            "amount": reward_coin,
                            "flow_type": 1,
                            "changed_type": 33,
                            "changed_time": int(round(time.time() * 1000)),
                            "status": 1,
                            "account_type": 0,
                            "reason": "打卡奖励奖励",
                            "remarks": "打卡奖励",
                            "coin_balance": select_success_user['coin'] + reward_coin
                        }
                        conn.execute(insert(LCoinChange).values(insert_exchange))
                        # 修改账户金币余额
                        # 更改用户金币
                        update_user_coin = update(MUserInfo).values({
                            "coin": insert_exchange['coin_balance']
                        }).where(
                            MUserInfo.user_id == user['user_id']
                        )
                        conn.execute(update_user_coin)


def run():
    server = pipeflow.Server()
    server.add_routine_worker(cash_reward, interval=3, immediately=True)
    server.add_routine_worker(checkin_faker, interval=3, immediately=True)
    # server.add_routine_worker(update_checkin_result, interval=5, immediately=True)
    server.add_routine_worker(checkin_user_reward, interval=59, immediately=True)
    server.run()


if __name__ == '__main__':
    run()
