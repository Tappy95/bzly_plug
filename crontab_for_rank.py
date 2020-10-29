import random
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta

from sqlalchemy import create_engine, select, and_, update, insert
from config import *
from models.alchemy_models import LRankMachine, LRankCoin, MPartnerInfo, MUserLeader, LCoinChange
from util.static_methods import serialize, get_pidic_key

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)


# 更新假的排名用户
def update_rank_user():
    print("start update rank user! the time is:%s" % datetime.now())
    cur_hour = int(datetime.fromtimestamp(time.time()).strftime('%H'))
    cur_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    range_coin = 1
    range_coin_after = 2 + cur_hour
    with engine.connect() as conn:
        select_rank_machine = conn.execute(select([LRankMachine])).fetchall()
        # rank_machine = random.sample(select_rank_machine, 10)
        fakers = []
        for user in select_rank_machine:
            select_exist_rank = conn.execute(select([LRankCoin]).where(
                and_(
                    LRankCoin.mobile == user['mobile'],
                    LRankCoin.rank_date == cur_date
                )
            )).fetchone()
            coin_balance = (select_exist_rank['coin_balance']) / 10000 + random.randint(range_coin, range_coin_after) \
                if select_exist_rank else random.randint(range_coin, range_coin_after)
            faker = {
                "rank_type": 1,
                "rank_order": 1,
                "image_url": user['img'],
                "alias_name": "",
                "mobile": user['mobile'],
                "user_id": user['mobile'],
                "coin_balance": coin_balance * 10000,
                "rank_date": cur_date,
                "create_time": int(time.time() * 1000),
                "real_data": 2,
                "reward_amount": 0,
            }
            fakers.append(faker)
        fakers = sorted(fakers, key=lambda k: k['coin_balance'], reverse=True)
        for idx, fake in enumerate(fakers):
            select_exist_rank = conn.execute(select([LRankCoin]).where(
                and_(
                    LRankCoin.mobile == fake['mobile'],
                    LRankCoin.rank_date == cur_date
                )
            )).fetchone()
            fake['rank_order'] = idx + 1
            if select_exist_rank:
                update_rank = update(LRankCoin).where(
                    LRankCoin.id == select_exist_rank['id']
                ).values(
                    fake
                )
                conn.execute(update_rank)
            else:
                inset_rank = insert(LRankCoin).values(fake)
                conn.execute(inset_rank)


# 更新周期内邀请人数
def update_enddate_invite():
    # 遍历合伙人
    with engine.connect() as conn:
        select_partner = conn.execute(select([MPartnerInfo])).fetchall()
        for partner in select_partner:
            # 计算当前合伙人周期
            enddate = partner['enddate']
            startdate = enddate - timedelta(days=7)
            print(partner['user_id'], enddate, startdate)
            # 查询周期内的leader表
            select_leader = conn.execute(select([MUserLeader]).where(
                and_(
                    MUserLeader.leader_id == partner['user_id'],
                    MUserLeader.update_time > startdate,
                    MUserLeader.update_time < enddate
                )
            )).fetchall()
            select_all_leader = conn.execute(select([MUserLeader]).where(
                MUserLeader.leader_id == partner['user_id']
            )).fetchall()
            invite_user = len(select_leader)
            all_invite_user = len(select_all_leader)

            # 更新合伙人表->周期内邀请人数
            conn.execute(update(MPartnerInfo).values(
                {
                    "enddate_invite": invite_user,
                    "history_invite": all_invite_user
                }
            ).where(
                MPartnerInfo.user_id == partner['user_id']
            ))
    print("Done the update invite users info task")


# TODO: 更新周期内活跃度
def update_activity():
    # 遍历合伙人
    with engine.connect() as conn:
        select_partner = conn.execute(select([MPartnerInfo])).fetchall()
        for partner in select_partner:
            # 计算当前合伙人周期
            enddate = partner['enddate']
            startdate = enddate - timedelta(days=7)
            print(partner['user_id'], enddate, startdate)
            # 查询leader表,下级用户IDS
            select_salve = conn.execute(
                select([MUserLeader]).where(MUserLeader.leader_id == partner['user_id'])).fetchall()
            salave_ids = [salave['user_id'] for salave in select_salve]
            enddatetime = int(time.mktime(partner['enddate'].timetuple()) * 1000)
            startdatetime = int(time.mktime((enddate - timedelta(days=7)).timetuple()) * 1000)
            select_activity = conn.execute(select([LCoinChange]).where(
                and_(
                    LCoinChange.changed_time > startdatetime,
                    LCoinChange.changed_time < enddatetime,
                    LCoinChange.user_id.in_(salave_ids)
                )
            )).fetchall()
            conn.execute(update(MPartnerInfo).values(
                {
                    # 活跃度
                    "activity_points": len(select_activity)
                }
            ).where(
                MPartnerInfo.user_id == partner['user_id']
            ))
    print("Done update activity")


# 插入新合伙人
def insert_new_partner():
    # 查询合伙人# 遍历合伙人
    with engine.connect() as conn:
        select_partner = conn.execute(select([MPartnerInfo])).fetchall()
        partner_ids = [partner['user_id'] for partner in select_partner]
        # 查询周期内的leader表
        select_leader = conn.execute(select([MUserLeader])).fetchall()
        # 遍历leader
        for user in select_leader:
            # 不在合伙人表的
            if user['user_id'] not in partner_ids:
                # 插入新合伙人,status = 0
                conn.execute(insert(MPartnerInfo).values({
                    "user_id": user['user_id'],
                    "partner_level": 2,
                    "future_coin": 0,
                    "enddate": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S'),
                    "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "status": 0,
                    "history_invite": 0,
                    "activity_points": 0,
                    "enddate_invite": 0,
                }))
    print("Done insert new partner")


# 合伙人周期结算
def update_partner_status():
    # 遍历合伙人
    with engine.connect() as conn:
        select_partner = conn.execute(select([MPartnerInfo])).fetchall()
        for partner in select_partner:
            # 更新邀请人数
            # 计算当前合伙人周期
            enddate = partner['enddate']
            startdate = enddate - timedelta(days=7)
            print(partner['user_id'], enddate, startdate)
            # 查询周期内的leader表
            select_leader = conn.execute(select([MUserLeader]).where(
                and_(
                    MUserLeader.leader_id == partner['user_id'],
                    MUserLeader.update_time > startdate,
                    MUserLeader.update_time < enddate
                )
            )).fetchall()
            select_all_leader = conn.execute(select([MUserLeader]).where(
                MUserLeader.leader_id == partner['user_id']
            )).fetchall()
            invite_user = len(select_leader)
            all_invite_user = len(select_all_leader)

            # 更新合伙人表->周期内邀请人数
            conn.execute(update(MPartnerInfo).values(
                {
                    "enddate_invite": invite_user,
                    "history_invite": all_invite_user
                }
            ).where(
                MPartnerInfo.user_id == partner['user_id']
            ))

            # 更新区间内活跃度
            # 查询leader表,下级用户IDS
            select_salve = conn.execute(
                select([MUserLeader]).where(MUserLeader.leader_id == partner['user_id'])).fetchall()
            salave_ids = [salave['user_id'] for salave in select_salve]
            enddatetime = int(time.mktime(partner['enddate'].timetuple()) * 1000)
            startdatetime = int(time.mktime((enddate - timedelta(days=7)).timetuple()) * 1000)
            select_activity = conn.execute(select([LCoinChange]).where(
                and_(
                    LCoinChange.changed_time > startdatetime,
                    LCoinChange.changed_time < enddatetime,
                    LCoinChange.user_id.in_(salave_ids)
                )
            )).fetchall()
            # 获取指标
            activity_limit = get_pidic_key(conn, "partner_activity_limit")
            invite_limit = get_pidic_key(conn, "partner_invite_limit")
            # 更细合伙人活跃度
            # 更新合伙人状态
            select_the_partner = conn.execute(
                select([MPartnerInfo]).where(MPartnerInfo.user_id == partner['user_id'])).fetchone()
            if select_the_partner['status'] == 1:
                # 已经成为合伙人.
                # 到期
                if enddate >= datetime.now():
                    if len(select_activity) >= int(activity_limit) \
                            and invite_user >= invite_limit:
                        # 任务完成
                        status = 1
                    else:
                        # 任务未完成
                        status = 0
                # 未到期
                else:
                    status = 1
            # 原本非合伙人
            else:
                if len(select_activity) >= int(activity_limit) \
                        and invite_user >= invite_limit:
                    # 任务完成
                    status = 1
                else:
                    # 任务未完成
                    status = 0
            if enddate >= datetime.now():
                nextdate = enddate + timedelta(days=7)
            else:
                nextdate = enddate
            conn.execute(update(MPartnerInfo).values(
                {
                    # 活跃度
                    "activity_points": len(select_activity),
                    # 状态
                    "status": status,
                    "enddate": enddate,
                    "update_time": datetime.now()
                }
            ).where(
                MPartnerInfo.user_id == partner['user_id']
            ))

    print("Done update partner status")


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    # scheduler.add_job(my_clock, "cron", hour='21', minute='48')
    scheduler.add_job(update_rank_user, "interval", minutes=60)
    scheduler.add_job(update_enddate_invite, "interval", minutes=10)
    scheduler.add_job(insert_new_partner, "interval", minutes=5)
    scheduler.add_job(update_activity, "interval", minutes=20)
    scheduler.add_job(update_partner_status, "interval", hours=4)
    # scheduler.add_job(update_enddate_invite, "interval", seconds=2)
    # scheduler.add_job(my_clock, "cron", hour='21', minute='48')
    scheduler.start()
