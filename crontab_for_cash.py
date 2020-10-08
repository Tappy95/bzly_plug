# import sys
# # sys.path.append("/root/bzly_plug")
# print(sys.path)

import time

from sqlalchemy import select, create_engine, insert, update

from config import *
from models.alchemy_models import LUserExchangeCash, LUserCashLogPY, MUserInfo, LCoinChange
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


def run():
    server = pipeflow.Server()
    server.add_routine_worker(cash_reward, interval=3, immediately=True)
    server.run()


if __name__ == '__main__':
    run()
