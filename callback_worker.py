import json
import time
import traceback
from models.alchemy_models import *
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
TOPIC_NAME = "ql_callback_queue"

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)


def worker_cash_change(connection, cash_info):
    trans = connection.begin()
    user_id = cash_info['user_id']
    amount = cash_info['amount']
    changed_type = cash_info['changed_type']
    reason = cash_info['reason']
    remarks = cash_info['remarks']
    flow_type = cash_info['flow_type']
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


# 上级用户奖励
def top_reward(connection, top_user_id, amount, if_partner, low_if_partner, partner_level, floor):
    """

    :param connection:
    :param top_user_id: 上级用户ID
    :param amount: 基础奖励金额
    :param if_partner: 是否为合伙人
    :param low_if_partner: 下级是否为合伙人
    :param partner_level: 合伙人等级
    :param floor: 第几层上级
    :return:
    """
    reward = amount
    reason = "下级用户奖励"
    remarks = "合伙人一级"
    changed_type = 0
    # 第一层上级
    if floor == 'A':
        # 是合伙人
        if if_partner:
            # 玉麒麟
            if partner_level == 1:
                reward = int(amount * 0.2)
                remarks = "合伙人一级直属用户贡献"
                changed_type = 35
            elif partner_level == 2:
                reward = int(amount * 0.2)
                remarks = "合伙人一级直属用户贡献"
                changed_type = 35
        # 不是合伙人
        else:
            reward = int(amount * 0.125)
            remarks = "徒弟贡献"
            changed_type = 5
    # 第二层上级
    elif floor == "B":
        logger.info("{}{}{}".format(if_partner, partner_level, low_if_partner))
        # 是合伙人
        if if_partner:
            # 玉麒麟
            if partner_level == 1:
                if low_if_partner:
                    reward = int(amount * 0.2 * 0.15)
                    remarks = "代理推广收益分成"
                    changed_type = 39
                else:
                    reward = int(amount * 0.075)
                    remarks = "合伙人二级直属用户贡献"
                    changed_type = 36
            # 金麒麟
            elif partner_level == 2:
                if low_if_partner:
                    reward = int(amount * 0.2 * 0.15)
                    remarks = "代理推广收益分成"
                    changed_type = 39
                else:
                    reward = int(amount * 0.075)
                    remarks = "合伙人二级直属用户贡献"
                    changed_type = 36
    # 第三层上级
    elif floor == "C":
        logger.info("{}{}{}{}".format(floor, if_partner, partner_level, low_if_partner))
        # 是合伙人
        if if_partner:
            # 玉麒麟
            if partner_level == 1:
                if low_if_partner:
                    reward = int(amount * 0.075 * 0.40)
                    remarks = "代理推广收益分成"
                    changed_type = 39
            elif partner_level == 2:
                if low_if_partner:
                    reward = int(amount * 0.075 * 0.40)
                    remarks = "代理推广收益分成"
                    changed_type = 39

    cash_info = {
        "user_id": top_user_id,
        "amount": reward,
        "changed_type": changed_type,
        "reason": reason,
        "remarks": remarks,
        "flow_type": 1,
    }
    if changed_type != 0:
        worker_cash_change(connection, cash_info)
    else:
        return


# 裂变主入口
def worker_fission_schema(connection, task_info):
    trans = connection.begin()
    # 查上级A
    try:
        top_a = search_top(connection, task_info['user_id'])
        top_b = None
        if top_a:
            is_top_a, a_level = is_partner(connection, top_a)
            # 上级分成
            top_reward(connection, top_a, task_info['amount'], is_top_a, False, a_level, 'A')

            # 查上级B
            top_b = search_top(connection, top_a)

            if top_b:
                is_top_b, b_level = is_partner(connection, top_b)
                logger.info("{},{}".format(is_top_b, b_level))
                # 上级分成
                top_reward(connection, top_b, task_info['amount'], is_top_b, is_top_a, b_level, 'B')

                # 查上级C
                top_c = search_top(connection, top_b)
                if top_c:
                    is_top_c, c_level = is_partner(connection, top_c)
                    # 上级分成
                    if not (is_top_a and is_top_b):
                        logger.info("{}{}".format(is_top_b, is_top_a))

                        top_reward(connection, top_c, task_info['amount'], is_top_c, is_top_b, c_level, 'C')

        # 发放领导人奖励
        select_leader = connection.execute(select([MUserLeader]).where(
            MUserLeader.user_id == task_info['user_id']
        )).fetchone()
        if select_leader['leader_id'] != task_info['user_id'] and select_leader['leader_id'] != top_a:
            if top_b and select_leader['leader_id'] != top_b:
                # 查询当前用户金币
                select_user_current_coin = select([MPartnerInfo]).where(
                    MPartnerInfo.user_id == select_leader['leader_id']
                )
                cursor_cur_coin = connection.execute(select_user_current_coin)
                record_cur_coin = cursor_cur_coin.fetchone()
                if record_cur_coin:
                    amount = int(task_info['amount'] * 0.075)
                    # 计算金币余额
                    coin_balance = record_cur_coin['future_coin'] + amount
                    # activity = record_cur_coin['activity_points'] + 1
                    # 插入金币变更信息
                    insert_exchange = {
                        "user_id": select_leader['leader_id'],
                        "amount": amount,
                        "flow_type": 1,
                        "changed_type": 38,
                        "changed_time": int(round(time.time() * 1000)),
                        "status": 1,
                        "account_type": 0,
                        "reason": "下级用户贡献",
                        "remarks": "合伙人未入账金币(二级以下用户贡献)",
                        "coin_balance": coin_balance
                    }
                    ins_exange = insert(LCoinChange).values(insert_exchange)
                    connection.execute(ins_exange)
                    # 更改用户金币
                    update_user_coin = update(MPartnerInfo).values({
                        "future_coin": coin_balance
                    }).where(
                        and_(
                            MPartnerInfo.user_id == select_leader['leader_id'],
                            MPartnerInfo.future_coin == record_cur_coin['future_coin']
                        )
                    )
                    connection.execute(update_user_coin)
        trans.commit()
    except Exception as e:
        logger.info(traceback.print_exc())
        logger.info(traceback.format_exc())
        logger.info(e)
        trans.rollback()
        raise


# 更新闯关状态
def worker_checkpoint_task(connection, task_info):
    # 查询是否处于闯关状态
    select_user_checkpoint = connection.execute(select([MCheckpointRecord]).where(
        and_(
            MCheckpointRecord.user_id == task_info['user_id'],
            MCheckpointRecord.state == 1
        )
    )).fetchone()
    if select_user_checkpoint:
        # 初始化值
        # current_invite = select_user_checkpoint['current_invite'] if select_user_checkpoint['current_invite'] else 0
        # current_points = select_user_checkpoint['current_points'] if select_user_checkpoint['current_points'] else 0
        current_videos = select_user_checkpoint['current_videos'] if select_user_checkpoint['current_videos'] else 0
        current_games = select_user_checkpoint['current_games'] if select_user_checkpoint['current_games'] else 0

        if task_info['changed_type'] == 7:
            current_games += 1
        elif task_info['changed_type'] == 30:
            current_videos += 1

        # 更新闯关字段值
        connection.execute(update(MCheckpointRecord).values({
            "current_videos": current_videos,
            "current_games": current_games,
        }).where(
            and_(
                MCheckpointRecord.user_id == task_info['user_id'],
                MCheckpointRecord.state == 1
            )
        ))


# 更新每日工资状态
def worker_wage_task(conn, task_info):
    now = datetime.now()
    today_time = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                 microseconds=now.microsecond)
    select_wage_record = conn.execute(select([MWageRecord]).where(
        and_(
            MWageRecord.status == 1,
            MWageRecord.create_time == today_time,
            MWageRecord.user_id == task_info['user_id']
        )
    )).fetchone()
    current_game = select_wage_record['current_game'] if select_wage_record else 0
    current_video = select_wage_record['current_video'] if select_wage_record else 0
    # 更新每日任务数据
    if task_info['changed_type'] == 7:
        current_game += 1
    elif task_info['changed_type'] == 30:
        current_video += 1
    if select_wage_record:
        conn.execute(update(MWageRecord).values({
            "current_game": current_game,
            "current_video": current_video,
        }).where(
            and_(
                MWageRecord.user_id == select_wage_record['user_id'],
                MWageRecord.create_time == select_wage_record['create_time']
            )
        ))
    logger.info("{}:game->{},video->{}".format(task_info['user_id'], current_game, current_video))


async def callback_handle(group, task):
    ql_task = QLTask(task)
    task_type = ql_task.task_type
    task_info = ql_task.task_data
    task_log = [task_type, task_info]
    logger.info(task_log)
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            worker_cash_change(conn, task_info)
            # 游戏试玩, 高额任务, 视频奖励->裂变
            if task_info['changed_type'] == 7 \
                    or task_info['changed_type'] == 10 \
                    or task_info['changed_type'] == 30:
                # 裂变分润
                if "充值" not in task_info['remarks']:
                    worker_fission_schema(conn, task_info)
                # 更新闯关
                worker_checkpoint_task(conn, task_info)
                # 更新每日工资
                worker_wage_task(conn, task_info)
            # 更新
            trans.commit()

        except Exception as e:
            logger.info(e)
            logger.info(traceback.print_exc())
            logger.info(traceback.format_exc())
            trans.rollback()


def run():
    input_end = NsqInputEndpoint(TOPIC_NAME, 'ql_callback_worker', WORKER_NUMBER, **INPUT_NSQ_CONF)
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
