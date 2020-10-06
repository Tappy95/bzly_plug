import copy
import json
import time
import traceback
from datetime import datetime
from urllib.parse import quote

from config import *

from aiohttp import web
from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert

from models.alchemy_models import MUserInfo, t_tp_pcdd_callback, PDictionary, t_tp_xw_callback, TpTaskInfo, \
    t_tp_ibx_callback, TpJxwCallback, TpYwCallback, TpDyCallback
from task.callback_task import fission_schema, cash_exchange
from task.check_sign import check_xw_sign, check_ibx_sign, check_jxw_sign, check_yw_sign, check_dy_sign
from util.log import logger
from util.static_methods import serialize

routes = web.RouteTableDef()


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
        task_coin = pcdd_callback_params['money'] * int(rec_ctm['dic_value'])

        cash_result = await cash_exchange(
            connection,
            user_id=pcdd_callback_params['userid'],
            amount=task_coin,
            changed_type=7,
            reason="享玩游戏任务奖励",
            remarks=pcdd_callback_params['adname'],
            flow_type=1
        )
        fs_result = await fission_schema(
            connection,
            aimuser_id=pcdd_callback_params['userid'],
            task_coin=task_coin
        )
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
        check_key = check_xw_sign(
            keysign=request.query.get('keycode'),
            adid=request.query.get('adid'),
            appid=request.query.get('appid'),
            ordernum=request.query.get('ordernum'),
            deviceid=request.query.get('deviceid'),
            appsign=request.query.get('appsign'),
            price=request.query.get('price'),
            money=request.query.get('money')
        )
        if not check_key:
            return web.json_response({"success": 0, "message": "验签失败"})
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
        task_coin = callback_params['money'] * int(rec_ctm['dic_value'])

        c_result = await cash_exchange(
            connection,
            user_id=callback_params['appsign'],
            amount=task_coin,
            changed_type=7,
            reason="闲玩游戏任务奖励",
            remarks=callback_params['adname'],
            flow_type=1
        )
        fs_result = await fission_schema(
            connection,
            aimuser_id=callback_params['appsign'],
            task_coin=task_coin
        )
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
    if record:
        return web.json_response({"code": 200, "message": "订单已接收"})
    try:
        callback_params = {
            "app_key": r_json.get('app_key'),
            "device": r_json.get('device'),
            "device_info": int(r_json.get('device_info')),
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
        task_coin = callback_params['user_reward'] * int(rec_ctm['dic_value'])

        c_result = await cash_exchange(
            connection,
            user_id=callback_params['target_id'],
            amount=task_coin,
            changed_type=7,
            reason="爱变现游戏任务奖励",
            remarks=callback_params['game_name'],
            flow_type=1
        )
        fs_result = await fission_schema(
            connection,
            aimuser_id=callback_params['target_id'],
            task_coin=task_coin
        )
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


@routes.post('/ibxtaskcallback')
async def post_ibxtaskcallback(request):
    connection = request['db_connection']
    r_json = await request.json()
    print(r_json)
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
            "device_info": int(r_json.get('device_info')),
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
        task_coin = callback_params['user_reward'] * int(rec_ctm['dic_value'])

        c_result = await cash_exchange(
            connection,
            user_id=callback_params['target_id'],
            amount=task_coin,
            changed_type=7,
            reason="爱变现高额任务奖励",
            remarks=callback_params['content'],
            flow_type=1
        )
        fs_result = await fission_schema(
            connection,
            aimuser_id=callback_params['target_id'],
            task_coin=task_coin
        )
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
        idx_list = []
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
            fs_result = await fission_schema(
                connection,
                aimuser_id=deal['resource_id'],
                task_coin=task_coin
            )
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


@routes.post('/ywcallback')
async def post_ywcallback(request):
    connection = request['db_connection']
    r_post = await request.post()
    # 获取参数
    orderNo = r_post.get("orderNo")
    sign = r_post.get("sign")
    time = r_post.get("time")
    rewardDataJson = json.loads(r_post.get("rewardDataJson"))
    deal = {
        "orderNo": orderNo,
        "sign": sign,
        "time": int(time),
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
            return web.json_response({"code": 2, "msg": "未知错误"})
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
        fs_result = await fission_schema(
            connection,
            aimuser_id=deal['mediaUserId'],
            task_coin=task_coin
        )
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
        task_coin = deal['member_income'] * int(rec_ctm['dic_value'])

        c_result = await cash_exchange(
            connection,
            user_id=deal['user_id'],
            amount=task_coin,
            changed_type=7,
            reason="多游游戏任务奖励",
            remarks=deal['advert_name'] + deal['content'],
            flow_type=1
        )
        fs_result = await fission_schema(
            connection,
            aimuser_id=deal['user_id'],
            task_coin=task_coin
        )
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
