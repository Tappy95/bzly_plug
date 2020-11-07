import decimal
import json
import time
from datetime import datetime, timedelta
from operator import itemgetter

from aiohttp import web
from sqlalchemy import select, and_, update

from models.alchemy_models import PDictionary, TpVideoCallback, MUserLeader
from util.log import logger


def time_info(utc_time_iso):
    # local_time = datetime.strptime(utc_time_iso, '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta(hours=8)
    if utc_time_iso:
        local_time = datetime.strptime(utc_time_iso, '%Y-%m-%dT%H:%M:%S') + timedelta(hours=8)
    else:
        return utc_time_iso
    # print("转化时间",local_time)
    return local_time.strftime('%Y-%m-%d')


def date_range(start_time, end_time, effect_time):
    dates = []
    dt = datetime.strptime(start_time, "%Y-%m-%d")
    date = start_time[:]
    while date <= end_time:
        dates.append(date)
        dt = dt + timedelta(1)
        date = dt.strftime("%Y-%m-%d")
    for e_time in effect_time:
        if e_time in dates:
            dates.remove(e_time)

    return dates


# 数据库序列化器
def serialize(cursor, records):
    row_info, list_info = {}, []
    for row in records:
        for key in cursor.keys():
            if key == 'is_leaf':
                if row[key] == 0:
                    row_info[key] = 'False'
                    continue
                else:
                    row_info[key] = 'True'
                    continue
                # row_info[key] = isinstance(row[key], bool)
                # continue
            if isinstance(row[key], datetime):
                row_info[key] = row[key].strftime("%Y-%m-%d")
            elif isinstance(row[key], decimal.Decimal):
                row_info[key] = round(float(row[key]), 2)
            else:
                row_info[key] = row[key]
        list_info.append(row_info)
        row_info = {}
    return list_info


# 生成七天日期列表
def date_front(end_time):
    dates = []
    dt = datetime.strptime(end_time, "%Y-%m-%d")
    front_time = (dt - timedelta(6)).strftime("%Y-%m-%d")
    date = end_time[:]
    while date >= front_time:
        dates.append(date)
        dt = dt - timedelta(1)
        date = dt.strftime("%Y-%m-%d")
    return dates


# 分页器
def get_page_list(current_page, countent, max_page):
    """
        定义一个分页的方法
        current_page:表示当前页面
        countent:查询出来全部的数据
        MAX_PAGE:表示一页显示多少,一般定义在一个常量的文件中
    """
    start = (current_page - 1) * max_page
    end = start + max_page
    # 进行切片操作
    split_countent = countent[start:end]
    # 计算总共多少页
    count = int((len(countent) + max_page - 1) / max_page)
    # logger.info(count)
    # 上一页
    pre_page = current_page - 1
    # 下一页
    next_page = current_page + 1
    # 边界点的判断
    if pre_page == 0:
        pre_page = 1
    if next_page > count:
        next_page = current_page

    # 进行分页处理，把当前显示的全部页码返回到前端，前端直接遍历就可以
    if count < 5:
        pages = [p for p in range(1, count + 1)]
    elif current_page <= 3:
        pages = [p for p in range(1, 6)]
    elif current_page >= count - 2:
        pages = [p for p in range(count - 4, count + 1)]
    else:
        pages = [p for p in range(current_page - 2, current_page + 3)]
    # logger.info(count)
    return {
        'split_countent': split_countent,  # 当前显示的
        'count': count,  # 总共可以分多少页
        'pre_page': pre_page,  # 上一页
        'next_page': next_page,  # 下一页
        'current_page': current_page,  # 当前页
        'pages': pages  # 全部的页面吗
    }


# 获取字典值
async def get_pdictionary_key(connection, pd_name):
    select_pd = select([PDictionary]).where(
        PDictionary.dic_name == pd_name
    )
    cursor = await connection.execute(select_pd)
    record = await cursor.fetchone()
    return record['dic_value']


# 获取字典纸,同步版
def get_pidic_key(conn, pd_name):
    select_pd = conn.execute(select([PDictionary]).where(
        PDictionary.dic_name == pd_name
    )).fetchone()
    return select_pd['dic_value']


# 获取今日视频奖励次数
async def get_video_reward_count(connection, user_id):
    # 获取当前时间
    now = datetime.now()
    # 获取今天零点
    zeroToday = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
    # 获取23:59:59
    lastToday = zeroToday + timedelta(hours=23, minutes=59, seconds=59)
    zeroTodaytime = time.mktime(zeroToday.timetuple()) * 1000
    lastTodaytime = time.mktime(lastToday.timetuple()) * 1000
    select_count_reward = select([TpVideoCallback]).where(
        and_(
            TpVideoCallback.creator_time > zeroTodaytime,
            TpVideoCallback.creator_time < lastTodaytime,
            TpVideoCallback.user_id == user_id
        )
    )
    cursor = await connection.execute(select_count_reward)
    record = await cursor.fetchall()
    return len(record)


def update_leader_id(connection, referrer_id, leader_id):
    print("update leader->referrer:{}, leader:{}".format(referrer_id, leader_id))
    # 递归更新leader_id->断开分支
    select_low_user = connection.execute(select([MUserLeader]).where(
        and_(
            MUserLeader.referrer == referrer_id,
            MUserLeader.user_id != referrer_id,
            MUserLeader.leader_id != leader_id
        )
    )).fetchall()
    if select_low_user:
        # low_user 的目前leader是即将更新得leader的下级.则不更新
        select_leader_students = connection.execute(select([MUserLeader]).where(
            and_(
                MUserLeader.leader_id == leader_id
            )
        )).fetchall()
        students_ids = [student['user_id'] for student in select_leader_students]
        for low_user in select_low_user:
            if low_user['leader_id'] in students_ids:
                continue
            connection.execute(update(MUserLeader).values({
                "leader_id": leader_id
            }).where(
                MUserLeader.user_id == low_user['user_id']
            ))
        return update_leader_id(connection, low_user['user_id'], leader_id)
    else:
        return True
