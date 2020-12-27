import random
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta

from sqlalchemy import create_engine, select, and_, update, or_
from sqlalchemy.dialects.mysql import insert

from config import *
from models.alchemy_models import LRankMachine, LRankCoin, MPartnerInfo, MUserLeader, LCoinChange, LLeaderChange, \
    MCheckpointRecord, MUserInfo, MCheckpoint
from util.static_methods import serialize, get_pidic_key, update_leader_id

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
    range_coin_after = 6 + cur_hour*4
    with engine.connect() as conn:
        select_rank_machine = conn.execute(select([LRankMachine])).fetchall()
        # rank_machine = random.sample(select_rank_machine, 10)
        fakers = []
        key = random.randint(5,20)
        for idx, user in enumerate(select_rank_machine):
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
            if idx == key or idx == key + 5 or idx == key + 10:
                faker['coin_balance'] += random.randint(50000, 100000)
            fakers.append(faker)

        # 插入真实用户
        select_users = conn.execute(select([MUserInfo])).fetchall()
        now = datetime.now()
        zeroToday = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
        # 获取23:59:59
        lastToday = zeroToday + timedelta(hours=23, minutes=59, seconds=59)
        zeroTodaytime = time.mktime(zeroToday.timetuple()) * 1000
        lastTodaytime = time.mktime(lastToday.timetuple()) * 1000
        for user in select_users:
            select_user_coin = conn.execute(select([LCoinChange]).where(
                and_(
                    LCoinChange.user_id == user['user_id'],
                    LCoinChange.changed_time > zeroTodaytime,
                    LCoinChange.changed_time < lastTodaytime
                )
            )).fetchall()
            sum_user_coin = sum([coin_change['amount'] for coin_change in select_user_coin])
            real_user = {
                "rank_type": 1,
                "rank_order": 1,
                "image_url": user['profile'],
                "alias_name": "",
                "mobile": user['mobile'],
                "user_id": user['mobile'],
                "coin_balance": sum_user_coin,
                "rank_date": cur_date,
                "create_time": int(time.time() * 1000),
                "real_data": 1,
                "reward_amount": 0,
            }
            fakers.append(real_user)

        fakers = sorted(fakers, key=lambda k: k['coin_balance'], reverse=True)
        for idx, fake in enumerate(fakers[:30]):
            select_exist_rank = conn.execute(select([LRankCoin]).where(
                and_(
                    LRankCoin.mobile == fake['mobile'],
                    LRankCoin.rank_date == cur_date
                )
            )).fetchone()
            fake['rank_order'] = idx + 1
            if idx+1 == 1:
                fake['reward_amount'] = 1280000
            elif idx+1 == 2:
                fake['reward_amount'] = 780000
            elif idx+1 == 3:
                fake['reward_amount'] = 380000
            elif idx+1 == 4:
                fake['reward_amount'] = 280000
            elif idx+1 == 5:
                fake['reward_amount'] = 160000
            else:
                fake['reward_amount'] = 80000
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
    print("wake up update enddate invite")
    # 遍历合伙人
    with engine.connect() as conn:
        select_user = conn.execute(select([MUserInfo])).fetchall()
        for user in select_user:
            select_invite = conn.execute(select([MUserInfo]).where(
                MUserInfo.referrer == user['user_id']
            )).fetchall()
            conn.execute(update(MUserInfo).values({
                "apprentice": len(select_invite)
            }).where(
                MUserInfo.user_id == user['user_id']
            ))
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


# 更新周期内活跃度,流水
def update_activity():
    # 遍历合伙人
    with engine.connect() as conn:
        now = datetime.now()
        select_partner = conn.execute(
            select([MPartnerInfo])).fetchall()
        for partner in select_partner:
            today_time = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                         microseconds=now.microsecond)
            # 计算当前合伙人周期
            enddate = partner['enddate']
            startdate = enddate - timedelta(days=7)
            print(partner['user_id'], enddate, startdate)
            # 查询leader表,下级用户IDS
            for days in range(17):
                today_time_start = today_time - timedelta(days=days)
                today_time_end = today_time_start + timedelta(hours=23, minutes=59, seconds=59)
                select_salve = conn.execute(
                    select([MUserLeader]).where(MUserLeader.leader_id == partner['user_id'])).fetchall()
                salave_ids = [salave['user_id'] for salave in select_salve]
                enddatetime = int(time.mktime(today_time_end.timetuple()) * 1000)
                startdatetime = int(time.mktime(today_time_start.timetuple()) * 1000)
                select_leader_coin = conn.execute(select([LCoinChange]).where(
                    and_(
                        LCoinChange.changed_time > startdatetime,
                        LCoinChange.changed_time < enddatetime,
                        LCoinChange.user_id == partner['user_id'],
                        or_(
                            LCoinChange.changed_type == 5,
                            LCoinChange.changed_type == 35,
                            LCoinChange.changed_type == 36,
                        )
                    )
                )).fetchall()
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
                total_reward = sum([change['amount'] for change in select_leader_coin])
                active_user = len(set([active_user['user_id'] for active_user in select_activity]))
                change_info = {
                    "leader_id": partner['user_id'],
                    "create_time": today_time_start,
                    "total_reward": total_reward,
                    "active_user": active_user,
                    "update_time": now
                }
                # 更新当日汇总表
                ins = insert(LLeaderChange)
                insert_stmt = ins.values(change_info)
                on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                    leader_id=insert_stmt.inserted.leader_id,
                    create_time=insert_stmt.inserted.create_time,
                    total_reward=insert_stmt.inserted.total_reward,
                    active_user=insert_stmt.inserted.active_user,
                    update_time=insert_stmt.inserted.update_time
                )
                conn.execute(on_duplicate_key_stmt)
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


# # 遍历合伙人,更新leader表->断开合伙人分支
def update_leader():
    print("wake up update_leader")
    with engine.connect() as conn:
        select_partner = conn.execute(select([MPartnerInfo]).where(
            MPartnerInfo.status == 1
            # 有效合伙人
        )).fetchall()
        for partner in select_partner:
            update_leader_id(conn, partner['user_id'], partner['user_id'])
    print("done update leaders")


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
                if enddate < datetime.now():
                    if len(select_activity) >= int(activity_limit) \
                            and all_invite_user >= int(invite_limit):
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
                        and all_invite_user >= int(invite_limit):
                    # 任务完成
                    status = 1
                else:
                    # 任务未完成
                    status = 0
            if enddate >= datetime.now():
                nextdate = enddate
            else:
                nextdate = enddate + timedelta(days=7)
            conn.execute(update(MPartnerInfo).values(
                {
                    # 活跃度
                    "activity_points": len(select_activity),
                    # 状态
                    "status": status,
                    "enddate": nextdate,
                    "update_time": datetime.now()
                }
            ).where(
                MPartnerInfo.user_id == partner['user_id']
            ))

    print("Done update partner status")


# 闯关实时统计
def update_checkpoint_record():
    print("wake up update checkpoint record")
    # 遍历闯关表.去除所有状态为1的正在进行闯关行数据:
    with engine.connect() as conn:
        select_record = conn.execute(select([MCheckpointRecord]).where(
            MCheckpointRecord.state == 1
        )).fetchall()
        # 查询用户当前闯关邀请人闯关数限制
        select_invite_limit = conn.execute(select([MCheckpoint])).fetchall()
        limit_dict = {limits['checkpoint_number']: int(limits['friends_checkpoint_number']) for limits in
                      select_invite_limit}

        for user in select_record:
            # 查询用户时间段内的金币收益
            select_change = conn.execute(select([LCoinChange]).where(
                and_(
                    LCoinChange.user_id == user['user_id'],
                    LCoinChange.flow_type == 1,
                    LCoinChange.changed_time > user['create_time'],
                    LCoinChange.changed_time < int(time.time() * 1000),
                    LCoinChange.remarks != "徒弟提现贡献",
                    LCoinChange.changed_type != 12
                )
            )).fetchall()
            current_coin = sum([change['amount'] for change in select_change])

            # 查询用户时间段内的邀请人数
            select_invite = conn.execute(select([MUserInfo]).where(
                and_(
                    MUserInfo.referrer == user['user_id'],
                    MUserInfo.recommended_time > user['create_time'],
                    MUserInfo.recommended_time < int(time.time() * 1000)
                )
            )).fetchall()
            invite_ids = [user['user_id'] for user in select_invite]
            # 如果当前关没有关数限制,跳过
            if limit_dict[user['checkpoint_number']]:
                effect_user = 0
                for u_id in invite_ids:
                    select_current_checkpoint = conn.execute(select([MCheckpointRecord]).where(
                        and_(
                            MCheckpointRecord.user_id == u_id,
                            MCheckpointRecord.state == 2
                        )
                    )).fetchall()
                    if len(select_current_checkpoint) >= limit_dict[user['checkpoint_number']]:
                        effect_user += 1
                current_invite = effect_user
            else:
                current_invite = len(select_invite)
            students_ids = [student['user_id'] for student in select_invite]
            # current_invite = len(select_invite)

            # 查询用户时间段内的徒弟闯关数
            select_student_record = conn.execute(select([MCheckpointRecord]).where(
                and_(
                    MCheckpointRecord.user_id.in_(students_ids),
                    MCheckpointRecord.state == 2,
                    MCheckpointRecord.create_time > user['create_time'],
                    MCheckpointRecord.create_time < int(time.time() * 1000)
                )
            )).fetchall()
            currnet_friends_points = len(select_student_record)

            # 查询用户时间段内的视频数
            select_videos = conn.execute(select([LCoinChange]).where(
                and_(
                    LCoinChange.user_id == user['user_id'],
                    LCoinChange.flow_type == 1,
                    LCoinChange.changed_time > user['create_time'],
                    LCoinChange.changed_time < int(time.time() * 1000),
                    LCoinChange.changed_type == 30
                )
            )).fetchall()
            current_videos = len(select_videos)
            # 查询用户时间段内的游戏任务数
            select_games = conn.execute(select([LCoinChange]).where(
                and_(
                    LCoinChange.user_id == user['user_id'],
                    LCoinChange.flow_type == 1,
                    LCoinChange.changed_time > user['create_time'],
                    LCoinChange.changed_time < int(time.time() * 1000),
                    LCoinChange.changed_type == 7
                )
            )).fetchall()
            current_games = len(select_games)

            conn.execute(update(MCheckpointRecord).values(
                {
                    "current_coin": current_coin,
                    "current_invite": current_invite,
                    "current_points": currnet_friends_points,
                    "current_games": current_games,
                    "current_videos": current_videos,
                }
            ).where(
                and_(
                    MCheckpointRecord.user_id == user['user_id'],
                    MCheckpointRecord.checkpoint_number == user['checkpoint_number']
                )
            ))
    print("Done update checkpoint record")


# 实时统计邀请人数
def update_invite_users():
    print("wake up update intite users")
    with engine.connect() as conn:
        select_user = conn.execute(select([MUserInfo])).fetchall()
        for user in select_user:
            select_invite = conn.execute(select([MUserInfo]).where(
                MUserInfo.referrer == user['user_id']
            )).fetchall()
            conn.execute(update(MUserInfo).values({
                "apprentice": len(select_invite)
            }).where(
                MUserInfo.user_id == user['user_id']
            ))
    print("done update intite users")


# 更新用户表麒麟状态
def update_user_qilin():
    print("wake up update user qilin")
    with engine.connect() as conn:
        select_partner = conn.execute(select([MPartnerInfo])).fetchall()
        select_user = conn.execute(select([MUserInfo])).fetchall()
        for partner in select_partner:
            for user in select_user:
                if user['user_id'] == partner['user_id']:
                    if partner['status'] == 1:
                        if user['role_type'] != 1 and user['high_role'] != 1:
                            continue
                        else:
                            conn.execute(update(MUserInfo).values({
                                "role_type": partner['level'],
                                "high_role": partner['level']
                            }).where(
                                MUserInfo.user_id == user['user_id']
                            ))
    print("done update user qilin")


# 更新用户注册leader-biao
def update_user_leader():
    with engine.connect() as conn:
        select_user = conn.execute(select([MUserInfo])).fetchall()
        select_leader = conn.execute(select([MUserLeader])).fetchall()
        user_leader_ids = [leader_info['user_id'] for leader_info in select_leader]

        for user in select_user:
            if user['user_id'] not in user_leader_ids:
                select_refer_leader = conn.execute(select([MUserLeader]).where(
                    MUserLeader.user_id == user['referrer']
                )).fetchone()
                if select_refer_leader:
                    conn.execute(insert(MUserLeader).values({
                        "user_id": user['user_id'],
                        "referrer": user['referrer'],
                        "leader_id": select_refer_leader['leader_id'],
                        "update_time": datetime.now(),
                    }))
        print("done work")


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(update_rank_user, "interval", minutes=60, next_run_time=datetime.now())
    scheduler.add_job(update_enddate_invite, "interval", minutes=10)
    scheduler.add_job(insert_new_partner, "interval", minutes=5)
    scheduler.add_job(update_activity, "interval", hours=4)
    scheduler.add_job(update_partner_status, "interval", hours=4)
    scheduler.add_job(update_leader, "interval", minutes=2)
    scheduler.add_job(update_user_qilin, "interval", minutes=2)
    scheduler.add_job(update_user_leader, "interval", minutes=5)

    # scheduler.add_job(update_checkpoint_record, "interval", minutes=2)
    # scheduler.add_job(update_enddate_invite, "interval", seconds=2)
    # scheduler.add_job(my_clock, "cron", hour='21', minute='48')
    scheduler.start()
