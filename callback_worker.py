import json
import time

from datetime import datetime, timedelta

import emoji as emoji
from sqlalchemy import create_engine, select, and_, update, delete
from sqlalchemy.dialects.mysql import insert

import pipeflow
from config import *
from models.alchemy_models import MUserInfo, LUserCashLogPY, MUserLeader, MPartnerInfo, LCoinChange, LUserSign, \
    TpVideoCallback
from pipeflow.endpoints.nsq_endpoints import NsqInputEndpoint
from util.log import logger
from util.task_protocol import QLTask

from aioelasticsearch import Elasticsearch

WORKER_NUMBER = 1
TOPIC_NAME = "callback_queue"

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)


def worker_cash_change(connection, task_info):
    trans = connection.begin()
    user_id = task_info['user_id']
    amount = task_info['amount']
    changed_type = task_info['changed_type']
    reason = task_info['reason']
    remarks = task_info['remarks']
    flow_type = task_info['flow_type']
    try:
        # 查询当前用户金币
        select_user_current_coin = select([MUserInfo]).where(
            MUserInfo.user_id == user_id
        )
        cursor_cur_coin = connection.execute(select_user_current_coin)
        record_cur_coin = cursor_cur_coin.fetchone()
        select_user_leader = select([MUserLeader]).where(
            MUserLeader.user_id == user_id
        )
        cursor_leader = connection.execute(select_user_leader)
        record_leader = cursor_leader.fetchone()
        if record_leader:
            select_user_partner = select([MPartnerInfo]).where(
                MPartnerInfo.user_id == record_leader['leader_id']
            )
            cursor_partner = connection.execute(select_user_partner)
            record_partner = cursor_partner.fetchone()
            if record_partner:
                current_activity = record_partner['activity_points'] + 1
                if record_leader:
                    update_leader_activity = update(MPartnerInfo).values({
                        "activity_points": current_activity
                    }).where(
                        MPartnerInfo.user_id == record_leader['leader_id']
                    )
                    connection.execute(update_leader_activity)
        if record_cur_coin:

            # 计算金币余额
            if flow_type == 1:
                coin_balance = record_cur_coin['coin'] + amount
            else:
                coin_balance = record_cur_coin['coin'] - amount
                if coin_balance <= 0:
                    logger.info("变更金币失败,余额不足")
            # 插入金币变更信息
            insert_exchange = {
                "user_id": user_id,
                "amount": amount,
                "flow_type": flow_type,
                "changed_type": changed_type,
                "changed_time": int(round(time.time() * 1000)),
                "status": 1,
                "account_type": 0,
                "reason": reason,
                "remarks": remarks,
                "coin_balance": coin_balance
            }
            ins_exange = insert(LCoinChange).values(insert_exchange)
            connection.execute(ins_exange)
            # 更改用户金币
            update_user_coin = update(MUserInfo).values({
                "coin": coin_balance
            }).where(
                and_(
                    MUserInfo.user_id == user_id,
                    MUserInfo.coin == record_cur_coin['coin']
                )
            )
            connection.execute(update_user_coin)

        trans.commit()
        return True
    except Exception as e:
        logger.info(e)
        trans.rollback()
        return False


# 查找上级,并返回上级ID
def search_top(connection, aimuser_id):
    select_top = connection.execute(select([MUserLeader]).where(
        MUserLeader.user_id == aimuser_id
    )).fetchone()
    if select_top and select_top['referrer']:
        return select_top['referrer']
    else:
        return None

# 确认用户是否为合伙人,及其合伙人等级
def is_partner(connection, user_id):
    select_partner = connection.execute(select([MPartnerInfo]).where(
        MPartnerInfo.user_id == user_id
    )).fetchone()
    if select_partner and select_partner['status'] == 1:
        return True, select_partner['partner_level']
    else:
        return False, 2


def worker_fission_schema(connection, task_info):
    # 查上级A
    top_a = search_top(connection, task_info['user_id'])
    is_top_a, a_level = is_partner(connection, top_a)
    if top_a:
        # 查上级B
        top_b = search_top(connection, top_a)
        is_top_b, b_level = is_partner(connection, top_a)
        if top_b:
            # 查上级C
            top_c = search_top(connection, top_b)
            is_top_c, c_level = is_partner(connection, top_a)
    return True


async def callback_handle(group, task):
    ql_task = QLTask(task)
    task_type = ql_task.task_type
    task_info = ql_task.task_data
    task_log = [task_type, task_info]
    logger.info(task_log)
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with engine.connect() as conn:
        worker_cash_change(conn, task_info)
        # 游戏试玩, 高额任务, 视频奖励->裂变
        if task_info['changed_type'] == 7 \
                or task_info['changed_type'] == 10 \
                or task_info['changed_type'] == 30:
            worker_fission_schema(conn, task_info)


def run():
    input_end = NsqInputEndpoint(TOPIC_NAME, 'callback_worker', WORKER_NUMBER, **INPUT_NSQ_CONF)
    logger.info('连接nsq成功,topic_name = {}, nsq_address={}'.format(TOPIC_NAME, INPUT_NSQ_CONF))
    server = pipeflow.Server()
    logger.info("pipeflow开始工作")
    group = server.add_group('main', WORKER_NUMBER)
    logger.info("抓取任务")
    group.set_handle(callback_handle)
    logger.info("处理任务")
    group.add_input_endpoint('input', input_end)

    # server.add_routine_worker(ebay_maintain_task, interval=5, immediately=True)
    server.run()


if __name__ == '__main__':
    run()
