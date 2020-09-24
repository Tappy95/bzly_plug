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


# 类目对应一级类目dict
async def category_dict_firstlevel(connection, site, es_result, start_time=None, end_time=None, data_type=None):
    category_ids = [category['key'] for category in es_result]
    try:
        select_firstlevel = select([
            shopee_category.c.category_id_path,
            shopee_category.c.category_name,
            shopee_category.c.category_id
        ]).where(
            and_(
                shopee_category.c.category_id.in_(category_ids),
                shopee_category.c.site == site
            )
        )
        cursor = await connection.execute(select_firstlevel)
        records = await cursor.fetchall()

        if start_time:
            select_c_data = select([shopee_category_history]).where(
                and_(
                    shopee_category_history.c.category_id.in_(category_ids),
                    shopee_category_history.c.site == site,

                    shopee_category_history.c.date >= datetime.strptime(start_time, "%Y-%m-%d"),
                    shopee_category_history.c.date <= datetime.strptime(end_time, "%Y-%m-%d")
                )
            )
            cursor_c_data = await connection.execute(select_c_data)
            record_c_data = await cursor_c_data.fetchall()
    except Exception as e:
        logger.error(e)
        raise web.HTTPInternalServerError(text="DB error,Please contact Administrator")

    category_line = []

    for category_add in records:
        for category_cur in es_result:
            if category_cur['key'] == category_add['category_id']:
                category_cur['site'] = site
                category_cur['category_id'] = category_add['category_id']
                category_cur['category_firstlevel_id'] = (category_add['category_id_path'].split(':'))[0]
                category_cur['category_name'] = category_add['category_name']
                c_data = {
                    "category_id": category_cur['category_id'],
                    "name": category_cur['category_name'],
                    "data_list": []
                }
                if start_time:
                    effect_dates = []
                    for category_data in record_c_data:
                        if c_data['category_id'] == category_data['category_id']:
                            c_data['data_list'].append(
                                {
                                    "date": category_data['date'].strftime('%Y-%m-%d'),
                                    "data": category_data[data_type + '_last_1'] if data_type == 'sold' else float(category_data[data_type + '_last_1'])
                                    # "gmv": float(category_data['gmv_last_1'])
                                }
                            )
                            effect_dates.append(category_data['date'].strftime('%Y-%m-%d'))
                    dates = date_range(start_time, end_time, effect_dates)
                    for date in dates:
                        c_data['data_list'].append({
                            'date': date,
                            "data": None
                            # "gmv": None
                        })
                    c_data['data_list'].sort(key=itemgetter('date'))
                    category_line.append(c_data)

    return es_result, category_line


async def get_category_names(connection, json_list, market, is_category_id=None):
    name_ids = list(set([k for i in json_list for k in i['leaf_category_id']]))
    # logger.info(name_ids)
    select_category_name = select([
        shopee_category.c.category_name,
        shopee_category.c.category_id,
        shopee_category.c.category_id_path,
        shopee_category.c.category_name_path
    ]).where(
        and_(
            shopee_category.c.category_id.in_(name_ids),
            shopee_category.c.site == market
        ))
    cursor_name = await connection.execute(select_category_name)
    records_name = await cursor_name.fetchall()
    # 补全品类名
    list_info = complete_all_category_name(records_name, json_list, is_category_id)
    return list_info


# 商品详情页全链品类名补全
def complete_all_category_name(records, es_info, is_category_id=None):
    for category in es_info:
        category['category_path'] = []
        for low_id in category['leaf_category_id']:
            for db_info in records:
                if low_id == db_info['category_id']:
                    name_list = db_info['category_name_path'].split(':')
                    id_list = db_info['category_id_path'].split(':')
                    complete_list = []
                    for i in range(len(name_list)):
                        complete_list.append({"name": name_list.pop(0), "id": id_list.pop(0)})
                    category['category_path'].append(complete_list)
                    category['category_name'] = category['category_path'][0][-1]['name']

        if is_category_id:
            for idx, path_check in enumerate(category['category_path']):
                for id_check in path_check:
                    if id_check['id'] == is_category_id:
                        category['category_path'] = [path_check]
                        category['category_name'] = category['category_path'][0][-1]['name']
    return es_info


# 确认category等级
async def select_category_level(connection, site, category_id):
    try:
        select_category = select([
            # ebay_category.c.category_name,
            # ebay_category.c.site,
            # ebay_category.c.category_id,
            # ebay_category.c.parent_id,
            shopee_category.c.level
        ]).where(
            and_(
                shopee_category.c.category_id == category_id,
                shopee_category.c.site == site
            )
        )
        cursor = await connection.execute(select_category)
        records = await cursor.fetchall()
    except Exception as e:
        logger.info(e)
        raise web.HTTPInternalServerError(text="DB error,Please contact Administrator")

    # 类目序列化
    # category_dict = serialize(cursor, records)
    category_id_level = [c_item['level'] for c_item in records]
    return category_id_level[0]


# 类目层级关系,返回类目ID列表
async def select_category_list(connection, market, category_id):
    try:
        select_category = select([
            # ebay_category.c.category_name,
            shopee_category.c.site,
            shopee_category.c.category_id,
            shopee_category.c.parent_id,
            # shopee_category.c.level
        ]).where(
            and_(
                shopee_category.c.parent_id == category_id,
                shopee_category.c.site == market
            )
        )
        cursor = await connection.execute(select_category)
        records = await cursor.fetchall()
    except Exception as e:
        logger.info(e)
        raise web.HTTPInternalServerError(text="DB error,Please contact Administrator")

    # 类目序列化
    # category_dict = serialize(cursor, records)
    category_id_list = [c_item['category_id'] for c_item in records]
    return category_id_list


# 查看有效类目ID
async def check_effect_category(redis_conn, es_conn, es_key_time, site):
    key_word = 'shopee-category-' + es_key_time + '-' + site
    effect_ids = await redis_conn.get(key_word, encoding='utf-8')
    if effect_ids:
        c_ids = eval(effect_ids)
        if c_ids:
            return c_ids
    else:
        es_body = [{"index": "shopee_product_" + es_key_time},
                   {"size": 0, "query": {"bool": {"filter": {"term": {"site": site}}}},
                    "aggs": {"category_ids": {"terms": {"field": "category_l1_id", "size": 3000}},
                             "count": {"cardinality": {"field": "category_l1_id"}}}},
                   {"index": "shopee_product_" + es_key_time},
                   {"size": 0, "query": {"bool": {"filter": {"term": {"site": site}}}},
                    "aggs": {"category_ids": {"terms": {"field": "category_l2_id", "size": 3000}},
                             "count": {"cardinality": {"field": "category_l2_id"}}}},
                   {"index": "shopee_product_" + es_key_time},
                   {"size": 0, "query": {"bool": {"filter": {"term": {"site": site}}}},
                    "aggs": {"category_ids": {"terms": {"field": "category_l3_id", "size": 3000}},
                             "count": {"cardinality": {"field": "category_l3_id"}}}}]
        logger.info(json.dumps(es_body))
        c_id_result = await es_conn.msearch(body=es_body)

        c_ids = [k['key'] for i in c_id_result['responses'] for k in i['aggregations']['category_ids']['buckets']]
        if c_ids:
            redis_conn.setex(key_word, 3600 * 24, str(c_ids))
        return c_ids
