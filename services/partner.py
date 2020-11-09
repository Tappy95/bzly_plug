from datetime import datetime, timedelta

from sqlalchemy import select, and_

from models.alchemy_models import MPartnerInfo, MUserLeader, LLeaderChange, MUserInfo


async def leader_detail(connection, user_id):
    list_info = []
    sum_1 = 0
    sum_2 = 0
    # 查一级合伙人下级
    select_partner = select([MPartnerInfo]).where(
        MPartnerInfo.status == 1
    )
    cur_partner = await connection.execute(select_partner)
    rec_partner = await cur_partner.fetchall()
    partner_ids = [partner['user_id'] for partner in rec_partner]
    one_ids = []
    two_ids = []
    now = datetime.now()
    today_time = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                 microseconds=now.microsecond)
    # 查找合伙人的一级合伙人下级
    select_one = select([MUserLeader]).where(
        MUserLeader.referrer == user_id
    )
    cur_one = await connection.execute(select_one)
    rec_one = await cur_one.fetchall()
    for one in rec_one:
        if one['user_id'] in partner_ids:
            one_ids.append(one['user_id'])

    # 查找合伙人的二级合伙人下级
    select_two = select([MUserLeader]).where(
        MUserLeader.referrer.in_([one['user_id'] for one in rec_one])
    )
    cur_two = await connection.execute(select_two)
    rec_two = await cur_two.fetchall()
    for two in rec_two:
        if two['user_id'] in partner_ids:
            two_ids.append(two['user_id'])

    if one_ids:
        select_one_leader_change = select([LLeaderChange]).where(
            and_(
                LLeaderChange.create_time > datetime(2020,11,7),
                LLeaderChange.leader_id.in_(one_ids),
                LLeaderChange.total_reward > 0
            )
        )
        cur_o_change = await connection.execute(select_one_leader_change)
        rec_o_change = await cur_o_change.fetchall()
        for o_change in rec_o_change:
            sum_1 += int(o_change['total_reward'] * 0.15)
            result = {
                "id": o_change['leader_id'],
                "friend_floor": "一级合伙人",
                "reward_time": o_change['create_time'].strftime('%Y-%m-%d'),
                "reward": int(o_change['total_reward'] * 0.15)
            }
            list_info.append(result)

        if two_ids:
            select_two_leader_change = select([LLeaderChange]).where(
                and_(
                    LLeaderChange.create_time > datetime(2020, 11, 7),
                    LLeaderChange.leader_id.in_(two_ids),
                    LLeaderChange.total_reward > 0
                )
            )
            cur_t_change = await connection.execute(select_two_leader_change)
            rec_t_change = await cur_t_change.fetchall()
            for t_change in rec_t_change:
                sum_2 += int(t_change['total_reward'] * 0.4)
                result = {
                    "id": t_change['leader_id'],
                    "friend_floor": "一级合伙人",
                    "reward_time": t_change['create_time'].strftime('%Y-%m-%d'),
                    "reward": int(t_change['total_reward'] * 0.4)
                }
                list_info.append(result)


    user_ids = [user['id'] for user in list_info]
    select_user = select([MUserInfo]).where(
        MUserInfo.user_id.in_(user_ids)
    )
    cur_users = await connection.execute(select_user)
    rec_users = await cur_users.fetchall()
    for info in list_info:
        for user in rec_users:
            if info['id'] == user['user_id']:
                info['account_id'] = user['account_id']

    return list_info, sum_1, sum_2