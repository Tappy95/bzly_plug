import random
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta

from sqlalchemy import create_engine, select, and_, update
from sqlalchemy.dialects.mysql import insert

from config import *
from models.alchemy_models import LRankMachine, LRankCoin, MPartnerInfo, MUserLeader, LCoinChange, LLeaderChange, \
    MCheckpointRecord, MUserInfo, MCheckpoint, LPartnerChange
from util.static_methods import serialize, get_pidic_key, update_leader_id

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)


# 合伙人间收益统计结算
def update_partner_reward():
    # 遍历合伙人
    with engine.connect() as conn:
        select_partner = conn.execute(select([MPartnerInfo]).where(
            MPartnerInfo.status == 1
        )).fetchall()
        partner_ids = [partner['user_id'] for partner in select_partner]
        one_ids = []
        two_ids = []
        now = datetime.now()
        today_time = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                     microseconds=now.microsecond),
        for king_partner in select_partner:

            # 查找合伙人的一级合伙人下级
            select_one = conn.execute(select([MUserLeader]).where(
                MUserLeader.referrer == king_partner['user_id']
            )).fetchall()
            for one in select_one:
                if one['user_id'] in partner_ids:
                    one_ids.append(one['user_id'])

            # 查找合伙人的二级合伙人下级
            select_two = conn.execute(select([MUserLeader]).where(
                MUserLeader.referrer.in_([one['user_id'] for one in select_one])
            )).fetchall()
            for two in select_two:
                if two['user_id'] in partner_ids:
                    two_ids.append(two['user_id'])

            # 查找一级合伙人下级流水
            now = datetime.now()
            one_reward = 0
            two_reward = 0
            active_user = 0
            one_count = len(one_ids)
            two_count = len(two_ids)
            if one_ids:
                select_one_leader_change = conn.execute(select([LLeaderChange]).where(
                    and_(
                        LLeaderChange.create_time == today_time,
                        LLeaderChange.leader_id.in_(one_ids),
                        LLeaderChange.total_reward > 0
                    )
                )).fetchall()
                active_user += len(select_one_leader_change)
                one_reward = sum([one_change['total_reward'] for one_change in select_one_leader_change])

                # 查找二级合伙人的下级流水
                if two_ids:
                    select_two_leader_change = conn.execute(select([LLeaderChange]).where(
                        and_(
                            LLeaderChange.create_time == today_time,
                            LLeaderChange.leader_id.in_(two_ids),
                            LLeaderChange.total_reward > 0
                        )
                    )).fetchall()
                    active_user += len(select_two_leader_change)
                    two_reward = sum([two_change['total_reward'] for two_change in select_two_leader_change])
            # 发放顶级合伙人流水收益
            change_info = {
                "partner_id": king_partner['user_id'],
                "create_time": today_time,
                "one_reward": int(one_reward * 0.15),
                "two_reward": int(two_reward * 0.4),
                "active_partner": active_user,
                "one_count": one_count,
                "two_count": two_count,
                "is_reward": 0,
                "update_time": now
            }
            # 更新当日汇总表
            ins = insert(LPartnerChange)
            insert_stmt = ins.values(change_info)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                partner_id=insert_stmt.inserted.partner_id,
                create_time=insert_stmt.inserted.create_time,
                one_reward=insert_stmt.inserted.one_reward,
                two_reward=insert_stmt.inserted.two_reward,
                active_partner=insert_stmt.inserted.active_partner,
                one_count=insert_stmt.inserted.one_count,
                two_count=insert_stmt.inserted.two_count,
                is_reward=insert_stmt.inserted.is_reward,
                update_time=insert_stmt.inserted.update_time
            )
            conn.execute(on_duplicate_key_stmt)
    print("Done update partner status")


if __name__ == '__main__':
    scheduler = BlockingScheduler()

    scheduler.add_job(update_partner_reward, "interval", minutes=4, next_run_time=datetime.now())

    # scheduler.add_job(update_enddate_invite, "interval", seconds=2)
    # scheduler.add_job(my_clock, "cron", hour='21', minute='48')
    scheduler.start()