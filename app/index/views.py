import copy
import hashlib
import json
import time
import traceback
from datetime import datetime, timedelta
from operator import itemgetter
from urllib.parse import quote

from config import *

from aiohttp import web
from sqlalchemy import select, update, and_, text, or_
from sqlalchemy.dialects.mysql import insert

from libs.snowflake import IdWorker
from models.alchemy_models import MUserInfo, t_tp_pcdd_callback, PDictionary, t_tp_xw_callback, TpTaskInfo, \
    t_tp_ibx_callback, TpJxwCallback, TpYwCallback, TpDyCallback, TpZbCallback, LCoinChange, MChannelInfo, MChannel, \
    TpVideoCallback, MUserLeader, RealPhoneNumber, TpTjCallback
from task.callback_task import fission_schema, cash_exchange, select_user_id, get_channel_user_ids, get_callback_infos, \
    today_user_sign, select_admin_user_id
from task.check_sign import check_xw_sign, check_ibx_sign, check_jxw_sign, check_yw_sign, check_dy_sign, check_zb_sign, \
    check_ibx_task_sign, check_tj_sign
from util.log import logger
from util.static_methods import serialize, get_pdictionary_key, get_video_reward_count
from util.task_protocol import pub_to_nsq

routes = web.RouteTableDef()


# 获取高额赚任务
@routes.post('/get/hightasks')
async def add_hightasks(request):
    r_json = await request.json()
    connection = request['db_connection']
    parsed_results = r_json['data']['records']
    db_results = []
    for parsed_result in parsed_results:
        db_result = {
            "id": parsed_result['taskId'],
            "name": parsed_result['name'],
            "logo": parsed_result['icon'],
            "type_id": 1,
            # 1-高额收益2-注册任务3-实名认证4-超简单5-其他
            "label": parsed_result['tags'],
            "reward": parsed_result['price'],
            "is_upper": 1,
            "is_signin": 1,
            "task_channel": "Aibianxian",
            "create_time": int(round(time.time() * 1000)),
            "update_time": int(round(time.time() * 1000)),
            "orders": 1,
            "task_info_url": parsed_result['detailUrl'],

            "fulfil_time": None,
            "time_unit": None,
            "channel_task_number": None,
            "surplus_channel_task_number": None,
            "is_order": None,
            "order_time": None,
            "drReward": None,
        }
        db_results.append(db_result)

    # save product history
    insert_stmt = insert(TpTaskInfo)
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
        id=insert_stmt.inserted.id,
        name=insert_stmt.inserted.name,
        logo=insert_stmt.inserted.logo,
        type_id=insert_stmt.inserted.type_id,
        label=insert_stmt.inserted.label,
        reward=insert_stmt.inserted.reward,
        is_upper=insert_stmt.inserted.is_upper,
        is_signin=insert_stmt.inserted.is_signin,
        task_channel=insert_stmt.inserted.task_channel,
        create_time=insert_stmt.inserted.create_time,
        update_time=insert_stmt.inserted.update_time,
        orders=insert_stmt.inserted.orders,
        task_info_url=insert_stmt.inserted.task_info_url
    )
    await connection.execute(on_duplicate_key_stmt, db_results)

    return web.json_response({
        "ok": "爱变现高额任务拉取成功",
        "count": len(db_results)
    })


@routes.get('/index_name')
async def index_name(request):
    conn = request['db_connection']
    userinfo = {
        "user_id": "e2c2c1cd1",
        "account_id": 10999
    }
    ins = insert(MUserInfo)
    insert_stmt = ins.values(userinfo)
    # on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
    #     user_id=insert_stmt.inserted.user_id,
    #     account_id=insert_stmt.inserted.account_id
    # )
    await conn.execute(insert_stmt)
    # select_user = select([MUserInfo]).where(
    #     MUserInfo.user_id == "e2c2c1cdc1d04c91a8ae00b83dfba7eb"
    # )
    # cursor = await conn.execute(select_user)
    # record = await cursor.fetchall()
    # r = serialize(cursor, record)
    return web.json_response({
        "ok": 1
    })


# 平台回调摘选参数
@routes.get('/platform_list')
async def get_platform_list(request):
    connection = request['db_connection']
    select_channel_info = select([
        MChannelInfo.channel_id,
        MChannelInfo.channel_code,
        MChannel.channel_name
    ]).where(
        MChannelInfo.channel_id == MChannel.id
    )
    cur_channel = await connection.execute(select_channel_info)
    rec_channel = await cur_channel.fetchall()
    print(serialize(cur_channel, rec_channel))
    channel_list = [{"name": channel['channel_name'], "id": channel['channel_code']} for channel in rec_channel]
    channel_list.append({"name": "全渠道", "id": "all"})
    channel_list.append({"name": "新渠道", "id": "sall"})
    json_result = {
        "platform": [
            {"name": "多游", "id": "duoyou"},
            {"name": "闲玩", "id": "xianwan"},
            {"name": "享玩", "id": "xiangwan"},
            {"name": "爱变现", "id": "aibianxian"},
            {"name": "职伴", "id": "zhiban"},
            {"name": "鱼玩", "id": "yuwan"},
            {"name": "聚享玩", "id": "juxiangwan"}
        ],
        "channel_list": channel_list
    }

    return web.json_response(json_result)


# 全平台回调
@routes.get('/allcallback/list')
async def all_callback_list(request):
    params = {**request.query}
    pa = copy.deepcopy(params)
    for item in pa:
        if not params[item]:
            params.pop(item)
    token = request.query.get('token')
    channel = request.query.get('channel')
    relation = request.query.get('relation')
    platform = request.query.get("platform")
    pageNum = request.query.get('pageNum')
    pageSize = request.query.get('pageSize')

    # 创建连接
    connection = request['db_connection']
    user_ids = await get_channel_user_ids(connection, channel)
    print(user_ids)
    list_info, agg_info = await get_callback_infos(connection, user_ids, platform, params)
    list_info.reverse()
    # 获取平台表数据

    json_result = {
        "data": {
            **agg_info,
            "list": list_info if list_info else [],
        },
        "message": "操作成功",
        "statusCode": "2000",
        "token": token
    }
    print(json_result)
    return web.json_response(json_result)


# 享玩回调
@routes.get('/pcddcallback')
async def get_pcddcallback(request):
    connection = request['db_connection']
    is_ordernum = select([t_tp_pcdd_callback]).where(
        t_tp_pcdd_callback.c.ordernum == request.query.get('ordernum')
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchone()
    logger.info(record)
    if record:
        return web.json_response({"success": 0, "message": "订单已存在"})
    try:
        pcdd_callback_params = {
            "adid": int(request.query.get('adid')),
            "adname": request.query.get('adname'),
            "pid": request.query.get('pid'),
            "ordernum": request.query.get('ordernum'),
            "dlevel": int(request.query.get('dlevel')),
            "pagename": request.query.get('pagename'),
            "deviceid": request.query.get('deviceid'),
            "simid": request.query.get('simid'),
            "userid": request.query.get('userid'),
            "merid": request.query.get('merid'),
            "event": request.query.get('event'),
            "price": float(request.query.get('price')),
            "money": float(request.query.get('money')),
            "itime": datetime.strptime(request.query.get('itime'), '%Y/%m/%d %H:%M:%S'),
            "keycode": request.query.get('keycode'),
            "status": 1,
            "createTime": str(datetime.now().replace(microsecond=0))
        }
        pcdd_callback_params['userid'] = await select_user_id(connection, pcdd_callback_params['userid'])
        ins = insert(t_tp_pcdd_callback)
        insert_stmt = ins.values(pcdd_callback_params)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            adid=insert_stmt.inserted.adid,
            adname=insert_stmt.inserted.adname,
            pid=insert_stmt.inserted.pid,
            ordernum=insert_stmt.inserted.ordernum,
            dlevel=insert_stmt.inserted.dlevel,
            pagename=insert_stmt.inserted.pagename,
            deviceid=insert_stmt.inserted.deviceid,
            simid=insert_stmt.inserted.simid,
            userid=insert_stmt.inserted.userid,
            merid=insert_stmt.inserted.merid,
            event=insert_stmt.inserted.event,
            price=insert_stmt.inserted.price,
            money=insert_stmt.inserted.money,
            itime=insert_stmt.inserted.itime,
            keycode=insert_stmt.inserted.keycode,
            status=insert_stmt.inserted.status,
            createTime=insert_stmt.inserted.createTime
        )
        await connection.execute(on_duplicate_key_stmt)
        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        task_coin = float(pcdd_callback_params['money']) * int(rec_ctm['dic_value'])

        cash_result = await cash_exchange(
            connection,
            user_id=pcdd_callback_params['userid'],
            amount=task_coin,
            changed_type=7,
            reason="享玩游戏任务奖励",
            remarks=request.query.get('event'),
            flow_type=1
        )
        # if "充值" not in pcdd_callback_params['adname']:
        #     fs_result = await fission_schema(
        #         connection,
        #         aimuser_id=pcdd_callback_params['userid'],
        #         task_coin=task_coin
        #     )
        # else:
        #     fs_result = True
        fs_result = True
        if cash_result and fs_result:
            update_callback_status = update(t_tp_pcdd_callback).values({
                "status": 2
            }).where(
                t_tp_pcdd_callback.c.ordernum == pcdd_callback_params['ordernum']
            )
            await connection.execute(update_callback_status)
        json_result = {"success": 1, "message": "接收成功"}
    except Exception as e:
        logger.info(e)
        json_result = {"success": 0, "message": "数据插入失败"}

    return web.json_response(json_result)


# 闲玩回调
@routes.get('/xwcallback')
async def get_xwcallback(request):
    connection = request['db_connection']
    is_ordernum = select([t_tp_xw_callback]).where(
        t_tp_xw_callback.c.ordernum == request.query.get('ordernum')
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchone()
    logger.info(record)
    if record:
        return web.json_response({"success": 1, "message": "订单已接收"})
    try:
        callback_params = {
            "adid": int(request.query.get('adid')),
            "adname": request.query.get('adname'),
            "appid": request.query.get('appid'),
            "ordernum": request.query.get('ordernum'),
            "dlevel": int(request.query.get('dlevel')),
            "pagename": request.query.get('pagename'),
            "deviceid": request.query.get('deviceid'),
            "simid": request.query.get('simid'),
            "appsign": request.query.get('appsign'),
            "merid": request.query.get('merid'),
            "event": request.query.get('event'),
            "price": float(request.query.get('price')),
            "money": float(request.query.get('money')),
            "itime": datetime.strptime(request.query.get('itime'), '%Y/%m/%d %H:%M:%S'),
            "keycode": request.query.get('keycode'),
            "status": 2,
            "createTime": str(datetime.now().replace(microsecond=0))
        }
        logger.info(callback_params)
        check_key = check_xw_sign(
            keysign=request.query.get('keycode'),
            adid=request.query.get('adid'),
            appid=request.query.get('appid'),
            ordernum=request.query.get('ordernum'),
            dlevel=request.query.get('dlevel'),
            deviceid=request.query.get('deviceid'),
            appsign=request.query.get('appsign'),
            price=request.query.get('price'),
            money=request.query.get('money')
        )
        if not check_key:
            return web.json_response({"success": 0, "message": "验签失败"})
        callback_params['appsign'] = await select_user_id(connection, callback_params['appsign'])
        ins = insert(t_tp_xw_callback)
        insert_stmt = ins.values(callback_params)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            adid=insert_stmt.inserted.adid,
            adname=insert_stmt.inserted.adname,
            appid=insert_stmt.inserted.appid,
            ordernum=insert_stmt.inserted.ordernum,
            dlevel=insert_stmt.inserted.dlevel,
            pagename=insert_stmt.inserted.pagename,
            deviceid=insert_stmt.inserted.deviceid,
            simid=insert_stmt.inserted.simid,
            appsign=insert_stmt.inserted.appsign,
            merid=insert_stmt.inserted.merid,
            event=insert_stmt.inserted.event,
            price=insert_stmt.inserted.price,
            money=insert_stmt.inserted.money,
            itime=insert_stmt.inserted.itime,
            keycode=insert_stmt.inserted.keycode,
            status=insert_stmt.inserted.status,
            createTime=insert_stmt.inserted.createTime
        )
        await connection.execute(on_duplicate_key_stmt)

        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        task_coin = float(callback_params['money']) * int(rec_ctm['dic_value'])

        c_result = await cash_exchange(
            connection,
            user_id=callback_params['appsign'],
            amount=task_coin,
            changed_type=7,
            reason="闲玩游戏任务奖励",
            remarks=callback_params['adname'],
            flow_type=1
        )
        # if "充值" not in callback_params['adname']:
        #     fs_result = await fission_schema(
        #         connection,
        #         aimuser_id=callback_params['appsign'],
        #         task_coin=task_coin
        #     )
        # else:
        #     fs_result = True
        fs_result = True
        if c_result and fs_result:
            update_callback_status = update(t_tp_xw_callback).values({
                "status": 1
            }).where(
                t_tp_xw_callback.c.ordernum == callback_params['ordernum']
            )
            await connection.execute(update_callback_status)
        json_result = {"success": 1, "message": "接收成功"}
    except Exception as e:
        logger.info(e)
        json_result = {"success": 0, "message": "数据插入失败"}

    return web.json_response(json_result)


# 爱变现回调
@routes.post('/ibxcallback')
async def get_ibxcallback(request):
    connection = request['db_connection']
    r_json = await request.post()
    print(r_json)
    is_ordernum = select([t_tp_ibx_callback]).where(
        t_tp_ibx_callback.c.order_id == r_json.get('order_id')
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchone()
    logger.info(record)
    content_cz = '充值返利' if int(r_json.get('type')) == 2 else ""
    if record:
        return web.json_response({"code": 200, "message": "订单已接收"})
    try:
        callback_params = {
            "app_key": r_json.get('app_key'),
            "device": r_json.get('device'),
            "device_info": r_json.get('device_info'),
            "target_id": r_json.get('target_id'),
            "unit": r_json.get('unit'),
            "time_end": int(r_json.get('time_end')),
            "user_reward": float(r_json.get('user_reward')),
            "app_reward": float(r_json.get('app_reward')),
            "game_name": r_json.get('game_name'),
            "game_id": int(r_json.get('game_id')),
            "sign": r_json.get('sign'),
            "content": r_json.get('content'),
            "order_id": int(r_json.get('order_id')),
            "type": int(r_json.get('type')),
            "status": 0,
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        check_key = check_ibx_sign(
            keysign=r_json.get('sign'),
            app_key=r_json.get('app_key'),
            device=r_json.get('device'),
            device_info=r_json.get('device_info'),
            target_id=r_json.get('target_id'),
            notify_url=IBX_NOTIFY_URL
        )
        if not check_key:
            return web.json_response({"code": 0, "message": "验签失败"})
        callback_params['target_id'] = await select_user_id(connection, callback_params['target_id'])
        ins = insert(t_tp_ibx_callback)
        insert_stmt = ins.values(callback_params)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            app_key=insert_stmt.inserted.app_key,
            device=insert_stmt.inserted.device,
            device_info=insert_stmt.inserted.device_info,
            target_id=insert_stmt.inserted.target_id,
            unit=insert_stmt.inserted.unit,
            time_end=insert_stmt.inserted.time_end,
            user_reward=insert_stmt.inserted.user_reward,
            app_reward=insert_stmt.inserted.app_reward,
            game_name=insert_stmt.inserted.game_name,
            game_id=insert_stmt.inserted.game_id,
            sign=insert_stmt.inserted.sign,
            content=insert_stmt.inserted.content,
            order_id=insert_stmt.inserted.order_id,
            type=insert_stmt.inserted.type,
            status=insert_stmt.inserted.status,
            update_time=insert_stmt.inserted.update_time
        )
        await connection.execute(on_duplicate_key_stmt)

        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        # task_coin = callback_params['user_reward'] * int(rec_ctm['dic_value'])
        task_coin = float(callback_params['user_reward'])

        c_result = await cash_exchange(
            connection,
            user_id=callback_params['target_id'],
            amount=task_coin,
            changed_type=7,
            reason="爱变现游戏任务奖励",
            remarks=callback_params['game_name'] + callback_params['content'] + content_cz,
            flow_type=1
        )
        # if "充值" not in callback_params['game_name']:
        #     fs_result = await fission_schema(
        #         connection,
        #         aimuser_id=callback_params['target_id'],
        #         task_coin=task_coin
        #     )
        # else:
        #     fs_result = True
        fs_result = True
        if c_result and fs_result:
            update_callback_status = update(t_tp_ibx_callback).values({
                "status": 1
            }).where(
                t_tp_ibx_callback.c.order_id == callback_params['order_id']
            )
            await connection.execute(update_callback_status)
        json_result = {"code": 200, "message": "接收成功"}
    except Exception as e:
        logger.info(traceback.print_exc())
        logger.info(traceback.format_exc())
        logger.info(e)
        json_result = {"code": 0, "message": "数据插入失败"}

    return web.json_response(json_result)


# 爱变现高额赚回调
@routes.post('/ibxtaskcallback')
async def post_ibxtaskcallback(request):
    connection = request['db_connection']
    r_json = await request.post()
    is_ordernum = select([t_tp_ibx_callback]).where(
        t_tp_ibx_callback.c.order_id == r_json.get('order_id')
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchone()
    logger.info(record)
    if record:
        return web.json_response({"code": 200, "message": "订单已接收"})
    try:
        callback_params = {
            "app_key": r_json.get('app_key'),
            "device": r_json.get('device'),
            "device_info": str(r_json.get('device_info')),
            "target_id": r_json.get('target_id'),
            "unit": r_json.get('unit'),
            "time_end": int(r_json.get('time_end')),
            "user_reward": float(r_json.get('user_reward')),
            "app_reward": float(r_json.get('app_reward')),
            # "game_name": r_json.get('game_name'),
            # "game_id": int(r_json.get('game_id')),
            "sign": r_json.get('sign'),
            "content": r_json.get('content'),
            "order_id": int(r_json.get('order_id')),
            # "type": int(r_json.get('type')),
            "status": 0,
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        check_key = check_ibx_task_sign(
            keysign=r_json.get('sign'),
            app_key=r_json.get('app_key'),
            device=r_json.get('device'),
            device_info=r_json.get('device_info'),
            target_id=r_json.get('target_id')
        )
        if not check_key:
            return web.json_response({"code": 0, "message": "验签失败"})
        callback_params['target_id'] = await select_user_id(connection, callback_params['target_id'])
        ins = insert(t_tp_ibx_callback)
        insert_stmt = ins.values(callback_params)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            app_key=insert_stmt.inserted.app_key,
            device=insert_stmt.inserted.device,
            device_info=insert_stmt.inserted.device_info,
            target_id=insert_stmt.inserted.target_id,
            unit=insert_stmt.inserted.unit,
            time_end=insert_stmt.inserted.time_end,
            user_reward=insert_stmt.inserted.user_reward,
            app_reward=insert_stmt.inserted.app_reward,
            # game_name=insert_stmt.inserted.game_name,
            # game_id=insert_stmt.inserted.game_id,
            sign=insert_stmt.inserted.sign,
            content=insert_stmt.inserted.content,
            order_id=insert_stmt.inserted.order_id,
            # type=insert_stmt.inserted.type,
            status=insert_stmt.inserted.status,
            update_time=insert_stmt.inserted.update_time
        )
        await connection.execute(on_duplicate_key_stmt)

        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        # task_coin = callback_params['user_reward'] * int(rec_ctm['dic_value'])
        task_coin = float(callback_params['user_reward'])

        c_result = await cash_exchange(
            connection,
            user_id=callback_params['target_id'],
            amount=task_coin,
            changed_type=7,
            reason="爱变现高额任务奖励",
            remarks=callback_params['content'],
            flow_type=1
        )
        # if "充值" not in callback_params['content']:
        #     fs_result = await fission_schema(
        #         connection,
        #         aimuser_id=callback_params['target_id'],
        #         task_coin=task_coin
        #     )
        # else:
        #     fs_result = True
        fs_result = True
        if c_result and fs_result:
            update_callback_status = update(t_tp_ibx_callback).values({
                "status": 1
            }).where(
                t_tp_ibx_callback.c.order_id == callback_params['order_id']
            )
            await connection.execute(update_callback_status)
        json_result = {"code": 200, "message": "接收成功"}
    except Exception as e:
        logger.info(traceback.print_exc())
        logger.info(traceback.format_exc())
        logger.info(e)
        json_result = {"code": 0, "message": "数据插入失败"}

    return web.json_response(json_result)


# 聚享玩回调
@routes.get('/jxwcallback')
async def get_jxwcallback(request):
    connection = request['db_connection']
    # 获取参数
    mid = request.query.get("mid")
    resource_id = request.query.get("resource_id")
    get_time = request.query.get("time")
    prize_info = json.loads(request.query.get("prize_info"))
    sign = request.query.get("sign")
    adid = request.query.get("adid")
    device_code = request.query.get("device_code")
    field = request.query.get("field")
    icon = request.query.get("icon")
    logger.info([mid, resource_id, time, sign, adid, device_code, field, icon, prize_info])
    prize_infos = []
    for deal_info in prize_info:
        deal = {
            "prize_id": int(deal_info['prize_id']),
            "name": deal_info['name'],
            "title": deal_info['title'],
            "type": int(deal_info['type']),
            "task_prize": float(deal_info['task_prize']),
            "deal_prize": float(deal_info['deal_prize']),
            "task_prize_coin": float(deal_info['task_prize_coin']),
            "ad_id": int(deal_info['task_prize_coin']),
            "prize_time": int(deal_info['prize_time']),
            "task_id": int(deal_info['task_id']),
            "game_id": int(deal_info['game_id']) if "game_id" in deal_info else None,
            "mid": int(mid),
            "resource_id": resource_id,
            "sign": sign,
            "time": int(get_time),
            "device_code": device_code,
            "field": int(field),
            "icon": icon,
            "status": 0,
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        prize_infos.append(deal)

    is_ordernum = select([TpJxwCallback]).where(
        TpJxwCallback.prize_id.in_([prize_id['prize_id'] for prize_id in prize_infos])
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchall()
    if len(record) == len(prize_info):
        logger.info("订单已存在")
        return web.Response(text="success")
    else:
        exist_ids = [ex_id['prize_id'] for ex_id in record]
        copy_prize = copy.deepcopy(prize_infos)
        for item in copy_prize:
            if item['prize_id'] in exist_ids:
                prize_infos.remove(item)
    logger.info("-------------------------------------------------{}".format(prize_infos))

    try:
        check_key = check_jxw_sign(
            keysign=sign,
            prize_info=request.query.get("prize_info"),
            mid=str(mid),
            time=str(get_time),
            resource_id=resource_id
        )
        if not check_key:
            return web.Response(text="验签失败")

        for deal in prize_infos:
            deal['resource_id'] = await select_user_id(connection, deal['resource_id'])
            ins = insert(TpJxwCallback)
            insert_stmt = ins.values(deal)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                prize_id=insert_stmt.inserted.prize_id,
                name=insert_stmt.inserted.name,
                title=insert_stmt.inserted.title,
                type=insert_stmt.inserted.type,
                task_prize=insert_stmt.inserted.task_prize,
                deal_prize=insert_stmt.inserted.deal_prize,
                task_prize_coin=insert_stmt.inserted.task_prize_coin,
                ad_id=insert_stmt.inserted.ad_id,
                prize_time=insert_stmt.inserted.prize_time,
                task_id=insert_stmt.inserted.task_id,
                game_id=insert_stmt.inserted.game_id,
                mid=insert_stmt.inserted.mid,
                resource_id=insert_stmt.inserted.resource_id,
                time=insert_stmt.inserted.time,
                sign=insert_stmt.inserted.sign,
                device_code=insert_stmt.inserted.device_code,
                field=insert_stmt.inserted.field,
                icon=insert_stmt.inserted.icon,
                status=insert_stmt.inserted.status,
                update_time=insert_stmt.inserted.update_time
            )
            await connection.execute(on_duplicate_key_stmt)

            # 查询金币比列
            select_coin_to_money = select([PDictionary]).where(
                PDictionary.dic_name == "coin_to_money"
            )
            cur_ctm = await connection.execute(select_coin_to_money)
            rec_ctm = await cur_ctm.fetchone()
            task_coin = deal['task_prize'] * int(rec_ctm['dic_value'])

            c_result = await cash_exchange(
                connection,
                user_id=deal['resource_id'],
                amount=task_coin,
                changed_type=7,
                reason="聚享玩游戏任务奖励",
                remarks=deal['name'] + deal['title'],
                flow_type=1
            )
            # if "充值" not in deal['title']:
            #     fs_result = await fission_schema(
            #         connection,
            #         aimuser_id=deal['resource_id'],
            #         task_coin=task_coin
            #     )
            # else:
            #     fs_result = True
            fs_result = True
            if c_result and fs_result:
                update_callback_status = update(TpJxwCallback).values({
                    "status": 1
                }).where(
                    TpJxwCallback.prize_id == deal['prize_id']
                )
                await connection.execute(update_callback_status)
        json_result = "success"
    except Exception as e:
        logger.info(e)
        logger.info(traceback.print_exc())
        json_result = "数据接收失败"
    return web.Response(text=json_result)


# 鱼丸回调
@routes.post('/ywcallback')
async def post_ywcallback(request):
    connection = request['db_connection']
    r_post = await request.post()
    # 获取参数
    orderNo = r_post.get("orderNo")
    sign = r_post.get("sign")
    get_time = r_post.get("time")
    rewardDataJson = json.loads(r_post.get("rewardDataJson"))
    deal = {
        "orderNo": orderNo,
        "sign": sign,
        "time": int(get_time),
        "advertName": rewardDataJson['advertName'],
        "rewardRule": rewardDataJson['rewardRule'],
        "stageId": int(rewardDataJson['stageId']),
        "stageNum": rewardDataJson['stageNum'],
        "advertIcon": rewardDataJson['advertIcon'],
        "rewardType": rewardDataJson['rewardType'],
        "isSubsidy": int(rewardDataJson['isSubsidy']),
        "mediaMoney": float(rewardDataJson['mediaMoney']),
        "rewardUserRate": float(rewardDataJson['rewardUserRate']),
        "currencyRate": float(rewardDataJson['currencyRate']),
        "userMoney": float(rewardDataJson['userMoney']),
        "userCurrency": float(rewardDataJson['userCurrency']),
        "mediaUserId": rewardDataJson['mediaUserId'],
        "receivedTime": int(rewardDataJson['receivedTime']),
        "status": 0,
        "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    is_ordernum = select([TpYwCallback]).where(
        TpYwCallback.orderNo == deal['orderNo']
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchone()
    if record:
        logger.info("订单已存在")
        return web.json_response({"code": 1, "msg": "已接收过了"})

    try:
        check_key = check_yw_sign(
            keysign=sign,
            rewardDataJson=r_post.get("rewardDataJson"),
            time=str(deal['time'])
        )
        if not check_key:
            return web.json_response({"code": 2, "msg": "签名错误"})
        deal['mediaUserId'] = await select_user_id(connection, deal['mediaUserId'])
        ins = insert(TpYwCallback)
        insert_stmt = ins.values(deal)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            orderNo=insert_stmt.inserted.orderNo,
            sign=insert_stmt.inserted.sign,
            time=insert_stmt.inserted.time,
            advertName=insert_stmt.inserted.advertName,
            rewardRule=insert_stmt.inserted.rewardRule,
            stageId=insert_stmt.inserted.stageId,
            stageNum=insert_stmt.inserted.stageNum,
            advertIcon=insert_stmt.inserted.advertIcon,
            rewardType=insert_stmt.inserted.rewardType,
            isSubsidy=insert_stmt.inserted.isSubsidy,
            mediaMoney=insert_stmt.inserted.mediaMoney,
            rewardUserRate=insert_stmt.inserted.rewardUserRate,
            currencyRate=insert_stmt.inserted.currencyRate,
            userMoney=insert_stmt.inserted.userMoney,
            userCurrency=insert_stmt.inserted.userCurrency,
            mediaUserId=insert_stmt.inserted.mediaUserId,
            receivedTime=insert_stmt.inserted.receivedTime,
            status=insert_stmt.inserted.status,
            update_time=insert_stmt.inserted.update_time
        )
        await connection.execute(on_duplicate_key_stmt)

        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        task_coin = deal['userMoney'] * int(rec_ctm['dic_value'])

        c_result = await cash_exchange(
            connection,
            user_id=deal['mediaUserId'],
            amount=task_coin,
            changed_type=7,
            reason="鱼玩游戏任务奖励",
            remarks=deal['advertName'] + deal['rewardRule'],
            flow_type=1
        )
        # if "充值" not in deal['rewardRule']:
        #     fs_result = await fission_schema(
        #         connection,
        #         aimuser_id=deal['mediaUserId'],
        #         task_coin=task_coin
        #     )
        # else:
        #     fs_result = True
        fs_result = True
        if c_result and fs_result:
            update_callback_status = update(TpYwCallback).values({
                "status": 1
            }).where(
                TpYwCallback.orderNo == deal['orderNo']
            )
            await connection.execute(update_callback_status)
        json_result = {"code": 0, "msg": ""}
    except Exception as e:
        logger.info(e)
        logger.info(traceback.print_exc())
        json_result = {"code": 2, "msg": "未知错误"}
    return web.json_response(json_result)


# 多游回调
@routes.get('/dycallback')
async def get_dycallback(request):
    connection = request['db_connection']
    # 获取参数
    order_id = request.query.get("order_id")
    advert_id = int(request.query.get("advert_id"))
    advert_name = request.query.get("advert_name")
    created = int(request.query.get("created"))
    media_income = float(request.query.get("media_income"))
    member_income = float(request.query.get("member_income"))
    media_id = request.query.get("media_id")
    user_id = request.query.get("user_id")
    device_id = request.query.get("device_id")
    content = request.query.get("content")
    sign = request.query.get("sign")
    deal = {
        "order_id": order_id,
        "advert_id": advert_id,
        "advert_name": advert_name,
        "created": created,
        "media_income": media_income,
        "member_income": member_income,
        "media_id": media_id,
        "user_id": user_id,
        "device_id": device_id,
        "content": content,
        "status": 0,
        "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    is_ordernum = select([TpDyCallback]).where(
        TpDyCallback.order_id == order_id
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchone()
    if record:
        logger.info("订单已存在")
        return web.json_response({"status_code": 200, "message": "订单已存在"})
    try:
        check_key = check_dy_sign(
            keysign=sign,
            advert_id=request.query.get("advert_id"),
            advert_name=request.query.get("advert_name"),
            content=request.query.get("content"),
            created=request.query.get("created"),
            device_id=request.query.get("device_id"),
            media_id=request.query.get("media_id"),
            media_income=request.query.get("media_income"),
            member_income=request.query.get("member_income"),
            order_id=request.query.get("order_id"),
            user_id=request.query.get("user_id")
        )
        if not check_key:
            return web.json_response({"status_code": 403, "message": "签名sign错误"})
        deal['user_id'] = await select_user_id(connection, deal['user_id'])
        ins = insert(TpDyCallback)
        insert_stmt = ins.values(deal)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            order_id=insert_stmt.inserted.order_id,
            advert_id=insert_stmt.inserted.advert_id,
            advert_name=insert_stmt.inserted.advert_name,
            created=insert_stmt.inserted.created,
            media_income=insert_stmt.inserted.media_income,
            member_income=insert_stmt.inserted.member_income,
            media_id=insert_stmt.inserted.media_id,
            user_id=insert_stmt.inserted.user_id,
            device_id=insert_stmt.inserted.device_id,
            content=insert_stmt.inserted.content,
            sign=insert_stmt.inserted.sign,
            status=insert_stmt.inserted.status,
            update_time=insert_stmt.inserted.update_time
        )
        await connection.execute(on_duplicate_key_stmt)

        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        # task_coin = deal['member_income'] * int(rec_ctm['dic_value'])
        task_coin = deal['member_income']

        c_result = await cash_exchange(
            connection,
            user_id=deal['user_id'],
            amount=task_coin,
            changed_type=7,
            reason="多游游戏任务奖励",
            remarks=deal['advert_name'] + deal['content'],
            flow_type=1
        )
        # if "充值" not in deal['content']:
        #     fs_result = await fission_schema(
        #         connection,
        #         aimuser_id=deal['user_id'],
        #         task_coin=task_coin
        #     )
        # else:
        #     fs_result = True
        fs_result = True
        if c_result and fs_result:
            update_callback_status = update(TpDyCallback).values({
                "status": 1
            }).where(
                TpDyCallback.order_id == deal['order_id']
            )
            await connection.execute(update_callback_status)
        json_result = {"status_code": 200, "message": "回调成功"}
    except Exception as e:
        logger.info(e)
        logger.info(traceback.print_exc())
        json_result = {"status_code": 400, "message": "未知错误发生"}
    return web.json_response(json_result)


# 淘金回调
@routes.post('/tjcallback')
async def post_tjcallback(request):
    connection = request['db_connection']
    r_post = await request.post()
    print(r_post)
    # 获取参数
    ID = r_post.get("ID")
    MtIDUser = r_post.get("MtIDUser")
    IMEI = r_post.get("IMEI")
    MtId = r_post.get("MtId")
    IDUser = r_post.get("IDUser")
    UserFee = r_post.get("UserFee")
    MtFee = r_post.get("MtFee")
    DoneTime = r_post.get("DoneTime")
    IDTask = r_post.get("IDTask")
    Note = r_post.get("Note")
    ExtParams = eval(r_post.get("ExtParams").replace('null', '""'))
    AppName = ExtParams['AppName']
    AppIcon = ExtParams['AppIcon']
    SubtaskName = ExtParams['SubtaskName']
    OAID = ExtParams['OAID']
    TaskGroup = ExtParams['TaskGroup']
    MtGetFee = ExtParams['MtGetFee']
    TaskIndex = ExtParams['TaskIndex']
    TaskSubIndex = ExtParams['TaskSubIndex']
    sign = r_post.get("sign")
    deal = {
        "ID": ID,
        "MtIDUser": MtIDUser,
        "IMEI": IMEI,
        "MtId": MtId,
        "IDUser": IDUser,
        "UserFee": float(UserFee),
        "MtFee": float(MtFee),
        "DoneTime": int(DoneTime),
        "IDTask": IDTask,
        "Note": Note,
        "sign": sign,
        "TaskGroup": int(TaskGroup),
        "MtGetFee": float(MtGetFee),
        "TaskIndex": int(TaskIndex),
        "TaskSubIndex": int(TaskSubIndex),
        "AppName": AppName,
        "AppIcon": AppIcon,
        "SubtaskName": SubtaskName,
        "OAID": OAID,
        "status": 0,
        "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    is_ordernum = select([TpTjCallback]).where(
            TpTjCallback.ID == ID
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchone()
    if record:
        logger.info("订单已存在")
        return web.Response(text='ok')

    try:
        check_key = check_tj_sign(
            r_post=r_post
        )
        if not check_key:
            return web.json_response({"code": 403, "success": "false"})
        deal['MtIDUser'] = await select_user_id(connection, deal['MtIDUser'])
        ins = insert(TpTjCallback)
        insert_stmt = ins.values(deal)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            ID=insert_stmt.inserted.ID,
            MtIDUser=insert_stmt.inserted.MtIDUser,
            IMEI=insert_stmt.inserted.IMEI,
            MtId=insert_stmt.inserted.MtId,
            IDUser=insert_stmt.inserted.IDUser,
            UserFee=insert_stmt.inserted.UserFee,
            MtFee=insert_stmt.inserted.MtFee,
            DoneTime=insert_stmt.inserted.DoneTime,
            IDTask=insert_stmt.inserted.IDTask,
            Note=insert_stmt.inserted.Note,
            sign=insert_stmt.inserted.sign,
            TaskGroup=insert_stmt.inserted.TaskGroup,
            MtGetFee=insert_stmt.inserted.MtGetFee,
            TaskIndex=insert_stmt.inserted.TaskIndex,
            TaskSubIndex=insert_stmt.inserted.TaskSubIndex,
            AppName=insert_stmt.inserted.AppName,
            AppIcon=insert_stmt.inserted.AppIcon,
            SubtaskName=insert_stmt.inserted.SubtaskName,
            OAID=insert_stmt.inserted.OAID,
            status=insert_stmt.inserted.status,
            update_time=insert_stmt.inserted.update_time
        )
        await connection.execute(on_duplicate_key_stmt)

        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        task_coin = deal['UserFee'] * int(rec_ctm['dic_value'])
        # task_coin = deal['price']

        c_result = await cash_exchange(
            connection,
            user_id=deal['MtIDUser'],
            amount=task_coin,
            changed_type=7,
            reason="91淘金任务奖励",
            remarks=deal['AppName'] + deal['Note'],
            flow_type=1
        )
        # if "充值" not in deal['Note']:
        #         #     fs_result = await fission_schema(
        #         #         connection,
        #         #         aimuser_id=deal['uid'],
        #         #         task_coin=task_coin
        #         #     )
        #         # else:
        #         #     fs_result = True
        fs_result = True
        if c_result and fs_result:
            update_callback_status = update(TpTjCallback).values({
                "status": 1
            }).where(
                    TpTjCallback.ID == deal['ID']
            )
            await connection.execute(update_callback_status)
        result_text = 'ok'
    except Exception as e:
        logger.info(e)
        logger.info(traceback.print_exc())
        result_text = 'error'
    return web.Response(text=result_text)

# 职伴回调
@routes.post('/zbcallback')
async def post_zbcallback(request):
    connection = request['db_connection']
    r_post = await request.post()
    # 获取参数
    uid = r_post.get("uid")
    media_id = r_post.get("media_id")
    app_id = r_post.get("app_id")
    dev_code = r_post.get("dev_code")
    task_id = r_post.get("task_id")
    code = r_post.get("code")
    msg = r_post.get("msg")

    price = float(r_post.get("price")) if r_post.get("price") else 0
    media_price = float(r_post.get("media_price")) if r_post.get("media_price") else 0
    get_time = int(r_post.get("time"))
    title = r_post.get("title")
    logo = r_post.get("logo")
    sign = r_post.get("sign")
    deal = {
        "uid": uid,
        "task_id": task_id,
        "media_id": media_id,
        "app_id": app_id,
        "dev_code": dev_code,
        "code": code,
        "msg": msg,
        "price": price,
        "media_price": media_price,
        "time": get_time,
        "title": title,
        "logo": logo,
        "sign": sign,
        "status": 0,
        "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    is_ordernum = select([TpZbCallback]).where(
        and_(
            TpZbCallback.uid == uid,
            TpZbCallback.task_id == task_id
        )
    )
    cursor = await connection.execute(is_ordernum)
    record = await cursor.fetchone()
    if record:
        logger.info("订单已存在")
        return web.json_response({"code": 200, "success": "true"})

    try:
        check_key = check_zb_sign(
            r_post=r_post
        )
        if not check_key:
            return web.json_response({"code": 403, "success": "false"})
        deal['uid'] = await select_user_id(connection, deal['uid'])
        ins = insert(TpZbCallback)
        insert_stmt = ins.values(deal)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            uid=insert_stmt.inserted.uid,
            task_id=insert_stmt.inserted.task_id,
            media_id=insert_stmt.inserted.media_id,
            app_id=insert_stmt.inserted.app_id,
            dev_code=insert_stmt.inserted.dev_code,
            code=insert_stmt.inserted.code,
            msg=insert_stmt.inserted.msg,
            price=insert_stmt.inserted.price,
            media_price=insert_stmt.inserted.media_price,
            time=insert_stmt.inserted.time,
            title=insert_stmt.inserted.title,
            logo=insert_stmt.inserted.logo,
            sign=insert_stmt.inserted.sign,
            status=insert_stmt.inserted.status,
            update_time=insert_stmt.inserted.update_time
        )
        await connection.execute(on_duplicate_key_stmt)

        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        task_coin = deal['price'] * int(rec_ctm['dic_value'])
        # task_coin = deal['price']

        c_result = await cash_exchange(
            connection,
            user_id=deal['uid'],
            amount=task_coin,
            changed_type=10,
            reason="职伴任务奖励",
            remarks=deal['title'] + deal['msg'],
            flow_type=1
        )
        # if "充值" not in deal['msg']:
        #     fs_result = await fission_schema(
        #         connection,
        #         aimuser_id=deal['uid'],
        #         task_coin=task_coin
        #     )
        # else:
        #     fs_result = True
        fs_result = True
        if c_result and fs_result:
            update_callback_status = update(TpZbCallback).values({
                "status": 1
            }).where(
                and_(
                    TpZbCallback.uid == deal['uid'],
                    TpZbCallback.task_id == deal['task_id']
                )
            )
            await connection.execute(update_callback_status)
        json_result = {"code": 200, "success": "true"}
    except Exception as e:
        logger.info(e)
        logger.info(traceback.print_exc())
        json_result = {"code": 400, "success": "false"}
    return web.json_response(json_result)


# 视频广告回调
@routes.get('/tpvideocallback')
async def get_current_day_video_reward(request):
    params = {**request.query}
    connection = request['db_connection']
    # 查询用户ID
    user_id = await select_user_id(connection, params['token'])
    # 查询视频奖励次数
    limit_count = await get_pdictionary_key(connection, "video_number")
    reward_count = await get_video_reward_count(connection, user_id)
    if reward_count >= int(limit_count):
        return web.json_response({
            "code": 403,
            "message": "今日奖励超限"
        })
    # 获取随机订单号
    worker = IdWorker(1, 2, 0)
    trans_id = worker.get_id()
    # 获取单挑视频奖励
    reward_amount = await get_pdictionary_key(connection, "video_reward")
    callback_info = {
        "user_id": user_id,
        "operate_type": int(params['operate_type']),
        "trans_id": str(trans_id),
        "reward_amount": int(reward_amount),
        "reward_name": "趣变视频奖励",
        "creator_time": int(time.time() * 1000),
        "sign": "无需签名",
        "state": "3",
        "remarks": "视频奖励回调"
    }
    try:
        await connection.execute(insert(TpVideoCallback).values(callback_info))
        # 每日红包签到,签到不发放视频奖励,只发放签到奖励
        if params['operate_type'] == '1':
            c_result = await today_user_sign(connection, user_id)
            if c_result:
                toast = "签到成功"
            else:
                return web.json_response({
                    "code": 400,
                    "message": "签到失败,请联系管理员"
                })
        else:
            # 发放视频奖励
            toast = "视频奖励"
            c_result = await cash_exchange(
                connection,
                user_id=user_id,
                amount=int(reward_amount),
                changed_type=30,
                reason="视频奖励",
                remarks="趣变视频奖励",
                flow_type=1
            )
            # fs_result = await fission_schema(
            #     connection,
            #     aimuser_id=user_id,
            #     task_coin=int(reward_amount)
            # )
            if c_result:
                update_callback_status = update(TpVideoCallback).values({
                    "state": 1
                }).where(
                    and_(
                        TpVideoCallback.user_id == user_id,
                        TpVideoCallback.trans_id == trans_id
                    )
                )
                await connection.execute(update_callback_status)

        return web.json_response({
            "code": 200,
            "message": "{}+{}金币!".format(toast, int(reward_amount))
        })
    except Exception as e:
        logger.info(e)
        logger.info(traceback.print_exc())
        update_callback_status = update(TpVideoCallback).values({
            "state": 3
        }).where(
            and_(
                TpVideoCallback.user_id == user_id,
                TpVideoCallback.trans_id == trans_id
            )
        )
        await connection.execute(update_callback_status)
        return web.json_response({
            "code": 405,
            "message": "发放奖励异常,请联系管理员"
        })


# 回调重发,全平台
# TODO: 备注信息->充值
@routes.get('/recallback')
async def restart_callback(request):
    platform = request.query.get("platform")
    connection = request['db_connection']
    p_dict = {
        "duoyou": {
            "table": TpDyCallback,
            "order_column": "order_id",
            "user_column": "user_id",
            "user_money_column": "member_income",
            "defeat_status": 0,
            "success_status": 1,
            "title_column": "advert_name"
        },
        "xiangwan": {
            "table": t_tp_pcdd_callback,
            "order_column": "ordernum",
            "user_column": "userid",
            "user_money_column": "money",
            "defeat_status": 1,
            "success_status": 2,
            "title_column": "adname"
        },
        "xianwan": {
            "table": t_tp_xw_callback,
            "order_column": "ordernum",
            "user_column": "appsign",
            "user_money_column": "money",
            "defeat_status": 2,
            "success_status": 1,
            "title_column": "adname"
        },
        "aibianxian": {
            "table": t_tp_ibx_callback,
            "order_column": "order_id",
            "user_column": "target_id",
            "user_money_column": "user_reward",
            "defeat_status": 0,
            "success_status": 1,
            "title_column": "game_name"
        },
        "zhiban": {
            "table": TpZbCallback,
            "order_column": ["uid", "task_id"],
            "user_column": "uid",
            "user_money_column": "price",
            "defeat_status": 0,
            "success_status": 1,
            "title_column": "title"
        },
        "yuwan": {
            "table": TpYwCallback,
            "order_column": "orderNo",
            "user_column": "mediaUserId",
            "user_money_column": "userCurrency",
            "defeat_status": 0,
            "success_status": 1,
            "title_column": "advertName"
        },
        "juxiangwan": {
            "table": TpJxwCallback,
            "order_column": "prize_id",
            "user_column": "resource_id",
            "user_money_column": "task_prize",
            "defeat_status": 0,
            "success_status": 1,
            "title_column": "name"
        },
        "taojin":{
            "table": TpTjCallback,
            "order_column": "ID",
            "user_column": "MtIDUser",
            "user_money_column": "UserFee",
            "defeat_status": 0,
            "success_status": 1,
            "title_column": "Note"
        }
    }
    # 判断表model类型
    is_c_model = type(t_tp_xw_callback) == type(p_dict[platform]['table'])
    # 初始化对象
    s_table = p_dict[platform]["table"]
    order_column = p_dict[platform]["order_column"]
    title_column = p_dict[platform]["title_column"]
    user_column = p_dict[platform]["user_column"]
    user_money_column = p_dict[platform]["user_money_column"]
    defeat_status = p_dict[platform]["defeat_status"]
    success_status = p_dict[platform]["success_status"]
    # 查询平台内所有失败任务

    select_defeat_tasks = select([p_dict[platform]["table"]]).where(
        and_(
            text(
                "status = {}".format(defeat_status)
            )
        )
    )
    cursor = await connection.execute(select_defeat_tasks)
    record = await cursor.fetchall()
    tasks = serialize(cursor, record)
    # 遍历失败任务信息
    i = 0
    for task in tasks:
        # 查询用户ID,并覆盖
        task[user_column] = await select_user_id(connection, task[user_column])
        if not task[user_column]:
            continue
        logger.info("user_id:{}".format(task[user_column]))
        # 重新发放奖励及列表
        # 查询金币比列
        select_coin_to_money = select([PDictionary]).where(
            PDictionary.dic_name == "coin_to_money"
        )
        cur_ctm = await connection.execute(select_coin_to_money)
        rec_ctm = await cur_ctm.fetchone()
        if float(task[user_money_column]) < 20:
            task_coin = float(task[user_money_column]) * int(rec_ctm['dic_value'])
        else:
            task_coin = int(task[user_money_column])

        c_result = await cash_exchange(
            connection,
            user_id=task[user_column],
            amount=task_coin,
            changed_type=7,
            reason="{}游戏任务奖励".format(platform),
            remarks=task[title_column],
            flow_type=1
        )
        # fs_result = await fission_schema(
        #     connection,
        #     aimuser_id=task[user_column],
        #     task_coin=task_coin
        # )
        fs_result = True
        logger.info("流水记录及变更用户金币:{},列表任务:{}".format(c_result, fs_result))
        if c_result and fs_result:
            if platform != "zhiban":
                str1 = order_column + '="' + str(task[order_column]) + '"'
                logger.info(str1)
                sql_text = [text(order_column + '="' + str(task[order_column]) + '"')]
            else:
                sql_text = [text(order_column[0] + '="' + str(task[order_column[0]]) + '"'),
                            text(order_column[1] + '="' + str(task[order_column[1]]) + '"')]
                # logger.info(str(order_column[0] + '="' + str(task[order_column[0]])))
                # logger.info(str(order_column[1] + '="' + str(task[order_column[1]])))
            update_callback_status = update(s_table).values({
                "status": success_status
            }).where(and_(*sql_text))
            logger.info(update_callback_status)
            await connection.execute(update_callback_status)
            i += 1

        if platform != "zhiban":
            logger.info("处理{}任务:{}".format(platform, task[order_column]))
        else:
            logger.info("处理{}任务:{},{}".format(platform, str(task[order_column[0]]), str(task[order_column[1]])))
    return web.json_response({
        "成功处理任务": i
    })


# 财务流水渠道明细
@routes.get('/coinchange')
async def get_coinchange(request):
    start_time = time.time()
    cast_time = time.time() - start_time
    print(cast_time)
    params = {**request.query}
    token = params['token']
    pa = copy.deepcopy(params)
    for item in pa:
        if not params[item]:
            params.pop(item)
    connection = request['db_connection']
    conditions = []
    if "isJQL" in params:
        redis_connection = request['redis_connection']
        leader_id = await select_admin_user_id(connection, token, redis_connection)
        select_under_leader_ids = select([MUserLeader]).where(
            MUserLeader.leader_id == leader_id
        )
        cur_u_leaders = await connection.execute(select_under_leader_ids)
        rec_u_leaders = await cur_u_leaders.fetchall()
        u_l_ids = [under_user['user_id'] for under_user in rec_u_leaders]
        conditions.append(MUserInfo.user_id.in_(u_l_ids))
    else:

        if "channelType" in params:
            params['channel'] = params['channelType']

        if params['channel'] != "all":
            if "searchType" not in params:
                if params['channel'] == 'sall':
                    conditions.append(
                        or_(
                            MUserInfo.channel_code == 'scjn',
                            MUserInfo.channel_code == 'slxq',
                            MUserInfo.channel_code == 'shq',
                            MUserInfo.channel_code == 'scq',
                            MUserInfo.channel_code == 'sxmn',
                            MUserInfo.channel_code == 'ssld',
                            MUserInfo.channel_code == 'scjl',
                            MUserInfo.channel_code == 'szy',
                            MUserInfo.channel_code == 'sll',
                            MUserInfo.channel_code == 'slxs',
                            MUserInfo.channel_code == 'slyz',
                            MUserInfo.channel_code == 'szj',
                            MUserInfo.channel_code == 'sqy',
                            MUserInfo.parent_channel_code == 'scjn',
                            MUserInfo.parent_channel_code == 'slxq',
                            MUserInfo.parent_channel_code == 'shq',
                            MUserInfo.parent_channel_code == 'scq',
                            MUserInfo.parent_channel_code == 'sxmn',
                            MUserInfo.parent_channel_code == 'ssld',
                            MUserInfo.parent_channel_code == 'scjl',
                            MUserInfo.parent_channel_code == 'szy',
                            MUserInfo.parent_channel_code == 'sll',
                            MUserInfo.parent_channel_code == 'slxs',
                            MUserInfo.parent_channel_code == 'slyz',
                            MUserInfo.parent_channel_code == 'szj',
                            MUserInfo.parent_channel_code == 'sqy'
                        )
                    )
                else:
                    conditions.append(
                        or_(MUserInfo.channel_code == params['channel'],
                            MUserInfo.parent_channel_code == params['channel']))
            else:
                if params['searchType'] == "1":
                    conditions.append(MUserInfo.channel_code == params['channel'])
                elif params['searchType'] == "2":
                    # 先查一级,再查一级的徒弟
                    select_1_user = select([MUserInfo]).where(MUserInfo.channel_code == params['channel'])
                    cur_1 = await connection.execute(select_1_user)
                    rec_1 = await cur_1.fetchall()
                    first_user_ids = [user_info['user_id'] for user_info in rec_1]
                    # 查一级ID的徒弟
                    select_2_user = select([MUserInfo]).where(MUserInfo.referrer.in_(first_user_ids))
                    cur_2 = await connection.execute(select_2_user)
                    rec_2 = await cur_2.fetchall()
                    second_user_ids = [user_info['user_id'] for user_info in rec_2]
                    # 加入主查询
                    conditions.append(MUserInfo.user_id.in_(second_user_ids))
                elif params['searchType'] == "3":
                    select_1_user = select([MUserInfo]).where(MUserInfo.channel_code == params['channel'])
                    cur_1 = await connection.execute(select_1_user)
                    rec_1 = await cur_1.fetchall()
                    first_user_ids = [user_info['user_id'] for user_info in rec_1]
                    select_all_user = select([MUserInfo]).where(
                        or_(MUserInfo.channel_code == params['channel'],
                            MUserInfo.parent_channel_code == params['channel'])
                    )
                    cur_all = await connection.execute(select_all_user)
                    rec_all = await cur_all.fetchall()
                    all_user_ids = [user_info['user_id'] for user_info in rec_all]
                    not_first_ids = []
                    for not_first in all_user_ids:
                        if not_first not in first_user_ids:
                            not_first_ids.append(not_first)
                    # 加入主查询
                    conditions.append(MUserInfo.user_id.in_(not_first_ids))

    if "mobile" in params:
        conditions.append(MUserInfo.mobile == params['mobile'])
    if "accountId" in params:
        conditions.append(MUserInfo.account_id == params['accountId'])
    # 根据查询维度获取用户ids
    cast_time = time.time() - start_time
    logger.info("构建前消耗{}".format(cast_time))
    select_user_ids = select([MUserInfo.user_id]).where(and_(*conditions))
    select_user_ids_2 = select([MUserInfo]).where(and_(*conditions))
    # logger.info(select_user_ids)
    cur_user = await connection.execute(select_user_ids_2)
    rec_user = await cur_user.fetchall()
    cast_time = time.time() - start_time
    logger.info("查询用户消耗{}".format(cast_time))
    # search_user_ids = [user_info['user_id'] for user_info in rec_user]

    # 领导人下级
    if 'leader_accountId' in params:
        select_leader_accountId = select([MUserInfo]).where(MUserInfo.account_id == params['leader_accountId'])
        cur_acc = await connection.execute(select_leader_accountId)
        rec_acc = await cur_acc.fetchone()
        select_leader_students = select([MUserLeader.user_id]).where(MUserLeader.referrer == rec_acc['user_id'])
        cur_one_students = await connection.execute(select_leader_students)
        rec_one_students = await cur_one_students.fetchall()
        select_two_students = select([MUserLeader.user_id]).where(
            MUserLeader.referrer.in_([user['user_id'] for user in rec_one_students]))
        cur_two_students = await connection.execute(select_two_students)
        rec_two_students = await cur_two_students.fetchall()
        search_user_ids = [*[user['user_id'] for user in rec_one_students],
                           *[user['user_id'] for user in rec_two_students]]
        select_user_ids = select([MUserInfo.user_id]).where(MUserInfo.user_id.in_(search_user_ids))
        select_user_ids_2 = select([MUserInfo.user_id]).where(MUserInfo.user_id.in_(search_user_ids))
        # logger.info(select_user_ids)
        cur_user = await connection.execute(select_user_ids_2)
        rec_user = await cur_user.fetchall()
    # 流水查询条件
    # 判断是否查询全部渠道收益
    change_conditions = [LCoinChange.user_id.in_(select_user_ids)]

    cast_time = time.time() - start_time
    logger.info("查询全部用户消耗{}".format(cast_time))

    if "changedType" in params:
        change_conditions.append(LCoinChange.changed_type == int(params['changedType']))
    if "startTime" in params:
        change_conditions.append(LCoinChange.changed_time >= int(params['startTime']))
    if "endTime" in params:
        change_conditions.append(LCoinChange.changed_time <= int(params['endTime']))
    if "coinMin" in params:
        change_conditions.append(LCoinChange.amount >= int(params['coinMin']))
    if "coinMax" in params:
        change_conditions.append(LCoinChange.amount <= int(params['coinMax']))
    if "rewardType" in params and params['rewardType'] == "1":
        change_conditions.append(LCoinChange.changed_type != 9)
        change_conditions.append(LCoinChange.changed_type != 5)
    # 流水查询分页
    page_size = int(params['pageSize'])
    pageoffset = (int(params['pageNum']) - 1) * page_size

    select_coin_change = select([
        LCoinChange,
        MUserInfo.account_id,
        MUserInfo.equipment_type,
        MUserInfo.user_name,
        MUserInfo.mobile,
        MUserInfo.referrer,
        MUserInfo.role_type,
        MUserInfo.level,
        MUserInfo.create_time,
        MUserLeader.leader_id
    ]).where(and_(
        *change_conditions,
        LCoinChange.user_id == MUserInfo.user_id,
        MUserLeader.user_id == MUserInfo.user_id
    )).order_by(
        LCoinChange.changed_time.desc()).limit(page_size).offset(pageoffset)

    # logger.info(select_coin_change)
    select_all_change = select([LCoinChange]).where(and_(*change_conditions))
    cur_coin = await connection.execute(select_coin_change)
    rec_coin = await cur_coin.fetchall()
    # logger.info(rec_coin[0]['mobile'])
    cast_time = time.time() - start_time
    logger.info("查询流水消耗{}(分页)".format(cast_time))
    # logger.info(serialize(cur_coin, rec_coin))
    cur_total = await connection.execute(select_all_change)
    rec_total = await cur_total.fetchall()
    cast_time = time.time() - start_time
    logger.info("查询流水消耗{}(不分页)".format(cast_time))
    total = len(rec_total)
    pageCount = (total + page_size - 1) / page_size

    totalRevenuePrice = 0
    subExpendPrice = 0
    totalExpendPrice = 0
    subRevenuePrice = 0
    list_info = []

    # 总结果
    for row in rec_total:
        if row['flow_type'] == 1:
            totalRevenuePrice += row['amount']
        else:
            totalExpendPrice += row['amount']

    # 分页结果
    for change_and_user in rec_coin:
        result = {
            "user_id": change_and_user['user_id'],
            "accountId": change_and_user['account_id'],
            "equipmentType": change_and_user['equipment_type'],
            "userName": change_and_user['user_name'],
            "phoneNum": change_and_user['mobile'],
            "referrerId": change_and_user['referrer'] if change_and_user['referrer'] else "",
            "leaderId": change_and_user['leader_id'] if change_and_user['leader_id'] else "",
            "roleType": change_and_user['role_type'],
            "level": change_and_user['level'],
            "changedType": change_and_user['changed_type'],
            "revenue": change_and_user['amount'] if change_and_user['flow_type'] == 1 else 0,
            "expend": change_and_user['amount'] if change_and_user['flow_type'] == 2 else 0,
            "coinBalance": change_and_user['coin_balance'],
            "changedTime": change_and_user['changed_time'],
            "registerTime": change_and_user['create_time'],
            "flowType": change_and_user['flow_type'],
            "status": change_and_user['status'],
            "reason": change_and_user['reason'] if change_and_user['reason'] else "",
            "remarks": change_and_user['remarks'] if change_and_user['remarks'] else ""
        }
        list_info.append(result)
        subExpendPrice += result['expend']
        subRevenuePrice += result['revenue']
    cast_time = time.time() - start_time
    logger.info("流水第一次处理消耗{}()".format(cast_time))
    # 补全信息->上级ID,最高领导人id
    partner_leader_ids = []
    select_all_leader = select([MUserLeader]).where(
        MUserLeader.user_id.in_(select_user_ids)
    )
    cur_all_leader = await connection.execute(select_all_leader)
    rec_all_leader = await cur_all_leader.fetchall()
    for row in rec_all_leader:
        partner_leader_ids.append(row['referrer'])
        partner_leader_ids.append(row['leader_id'])
    cast_time = time.time() - start_time
    logger.info("查询上级及领导人消耗{}()".format(cast_time))
    select_account_id = select([MUserInfo]).where(
        MUserInfo.user_id.in_(partner_leader_ids)
    )
    cur_account = await connection.execute(select_account_id)
    rec_account = await cur_account.fetchall()
    cast_time = time.time() - start_time
    logger.info("补全上级及领导人消耗{}()".format(cast_time))
    for r_row in list_info:
        for account in rec_account:
            if r_row['referrerId'] == account['user_id']:
                r_row['referrerId'] = account['account_id']
            if r_row['leaderId'] == account['user_id']:
                r_row['leaderId'] = account['account_id']
    cast_time = time.time() - start_time
    logger.info("循环补全消耗{}".format(cast_time))
    newlist = sorted(list_info, key=itemgetter('changedTime'))
    cast_time = time.time() - start_time
    logger.info("补全信息及排序{}".format(cast_time))
    # logger.info(list_info)
    json_result = {
        "data": {
            "res": "1",
            "totalRevenuePrice": totalRevenuePrice,
            "pageCount": pageCount,
            "total": total,
            "subExpendPrice": subExpendPrice,
            "list": newlist,
            "totalExpendPrice": totalExpendPrice,
            "subRevenuePrice": subRevenuePrice
        },
        "message": "操作成功",
        "statusCode": "2000",
        "token": "70f0ffd18fb3c3c52f4f83b2cb56ae7c"
    }
    return web.json_response(json_result)


# 安卓获取服务器时间
@routes.get('/time')
async def get_time(request):
    timenow = int(time.time())
    return web.Response(text=str(timenow))


# 测试NSQ
@routes.get('/nsq')
async def get_nsq(request):
    nsq_topic = "callback_queue"
    nsq_msg = {
        "task": "callback_task",
        "data": {}
    }
    task_status = await pub_to_nsq(NSQ_NSQD_HTTP_ADDR, nsq_topic, nsq_msg)
    if task_status != 200:
        return web.HTTPServiceUnavailable(text="Task publishing failed")
    return web.json_response({
        "ok": "success"
    })


@routes.get('/test_sql')
async def test_sql(request):
    connection = request['db_connection']
    select_user = select([MUserInfo])
    print(select_user)
    print(dir(select_user))
    cur = await connection.execute(select_user)
    print(dir(select_user))
    r = await cur.fetchall()
    print(r)


@routes.get('/phonenumber')
async def get_phonenumber(request):
    key = request.query.get('key')
    secret = 'secret'
    cur_hour = datetime.fromtimestamp(time.time()).strftime('%H')
    gen_key = hashlib.md5(
        (secret + cur_hour).encode('utf-8')).hexdigest()

    if not key == gen_key:
        return web.HTTPBadRequest(text='验证错误')

    connection = request['db_connection']
    select_phone = select([RealPhoneNumber]).where(
        RealPhoneNumber.status == 0
    )
    cur = await connection.execute(select_phone)
    rec = await cur.fetchone()

    json_result = {
        "id": rec['id'],
        "phonenumber": rec['phonenumber'],
        "status": rec['status']
    }

    await connection.execute(update(RealPhoneNumber).values({
        "status": 1
    }).where(
        RealPhoneNumber.id == rec['id']
    ))

    return web.json_response(json_result)
