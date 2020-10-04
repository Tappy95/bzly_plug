import json
from datetime import datetime

from aiohttp import web
from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert

from models.alchemy_models import MUserInfo, t_tp_pcdd_callback, PDictionary, t_tp_xw_callback
from task.callback_task import fission_schema, cash_exchange
from task.check_sign import check_xw_sign
from util.log import logger
from util.static_methods import serialize

routes = web.RouteTableDef()


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

        await cash_exchange(
            connection,
            user_id=callback_params['appsign'],
            amount=task_coin,
            changed_type=7,
            reason="享玩游戏任务奖励",
            remarks=callback_params['adname'],
            flow_type=1
        )
        await fission_schema(
            connection,
            aimuser_id=callback_params['appsign'],
            task_coin=task_coin
        )
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
