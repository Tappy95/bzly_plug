import decimal
import json
from datetime import datetime, timedelta
from operator import itemgetter

from aiohttp import web
from sqlalchemy import select, and_

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


# 类目树生成
async def category_tree(connection, site, effect_ids):
    try:
        select_category = select([
            shopee_category.c.category_name,
            shopee_category.c.level,
            shopee_category.c.site,
            shopee_category.c.category_id,
            shopee_category.c.parent_id,
            shopee_category.c.category_id_path,
            shopee_category.c.category_name_path,
        ]).where(
            and_(
                shopee_category.c.level <= 3,
                shopee_category.c.site == site,
                shopee_category.c.category_id.in_(effect_ids)
            )
        )

        cursor = await connection.execute(select_category)
        records = await cursor.fetchall()
    except Exception as e:
        logger.info(e)
        raise web.HTTPInternalServerError(text="DB error,Please contact Administrator")
    # 类目树
    category_dict = category_list(records)

    return category_dict


# 类目树生成器
def category_list(records):
    category_dict = [{"firstName": row['category_name'], "show": False, "category_id": row['category_id']}
                     for row in records if row['level'] == 1]

    for row_1 in category_dict:
        for row_2 in records:
            if row_2['parent_id'] == row_1['category_id']:
                if 'secondTitle' not in row_1:
                    row_1['secondTitle'] = []
                list_2 = row_2['category_id_path'].split(':')
                key_index = list_2.index(row_2['parent_id'])
                list_name = row_2['category_name_path'].split(':')
                parentName = str(list_name[key_index])
                row_1['secondTitle'].append(
                    {"secondName": row_2['category_name'], "show": False,
                     "category_id": row_2['category_id'], "parentName": parentName, "parentId": row_2['parent_id']})

    for row_1 in category_dict:
        for row_2 in row_1['secondTitle']:
            for row_3 in records:
                if row_3['parent_id'] == row_2['category_id']:
                    if 'thirdTitle' not in row_2:
                        row_2['thirdTitle'] = []
                    list_3 = row_3['category_id_path'].split(':')
                    key_index = list_3.index(row_3['parent_id'])
                    list_name = row_3['category_name_path'].split(':')
                    parentName = str(list_name[key_index])
                    row_2['thirdTitle'].append(
                        {"thirdName": row_3['category_name'], "category_id": row_3['category_id'],
                         "parentName": parentName, "parentId": row_3['parent_id']
                         })

    return category_dict


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




