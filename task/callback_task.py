# 麒麟分佣任务
import asyncio
from config import *
import time
from datetime import datetime, timedelta

from sqlalchemy import select, update, insert, and_, text, or_

from models.alchemy_models import MUserInfo, MFissionScheme, LCoinChange, TpDyCallback, t_tp_pcdd_callback, \
    t_tp_xw_callback, t_tp_ibx_callback, TpZbCallback, TpYwCallback, TpJxwCallback, MChannelInfo, MPartnerInfo, \
    MUserLeader, LUserSign, LUserExchangeCash, MWageRecord, PAdmin
from util.log import logger

# 金币变更任务
from util.static_methods import serialize, get_pdictionary_key

# 流水变更及发放金币
from util.task_protocol import pub_to_nsq


async def cash_exchange(connection, user_id, amount, changed_type, reason, remarks, flow_type=1):
    """
    :param connection:
    :param user_id:用户token
    :param amount: 变更金额
    :param flow_type: 变更类型1收入-2支出
    :param changed_type: 变更原因1答题2来访礼3提现4推荐用户获得5徒弟贡献6vip 7.游戏试玩奖励 8.徒弟到达4L奖励
    9-新人注册奖励10任务11出题12兑换闯关奖励 13-阅读资讯14-提现退回15直属用户返利 16-团队长赠送17间接用户返利18居间返利
    19-阅读广告奖励 20-分享资讯 21-签到赚 22-大众团队长分佣 23-快速赚任务 24-达人首次奖励 25-达人后续奖励 26-阅读小说
    27 达人邀请周榜奖励 28-高额赚提成 29 每日红包任务 30观看视频 31 小游戏奖励 32打卡消耗33打卡奖励 34 金币排行日榜奖励
    35 合伙人一级直属用户贡献 36 合伙人二级直属用户贡献 37 闯关助力 38 合伙人二级以下直属用户贡献 39 代理推广收益分成
    :param remarks: 标识信息
    :param reason: 理由
    :return:
    """
    nsq_topic = "ql_callback_queue"
    nsq_msg = {
        "task": "reward_task",
        "data": {
            "user_id": user_id,
            "amount": amount,
            "changed_type": changed_type,
            "reason": reason,
            "remarks": remarks,
            "flow_type": flow_type
        }
    }
    task_status = await pub_to_nsq(NSQ_NSQD_HTTP_ADDR, nsq_topic, nsq_msg)
    if task_status != 200:
        return False
    else:
        return True


# 裂变任务
async def fission_schema(connection, aimuser_id, task_coin, is_one=True):
    # 查询麒麟裂变方案
    select_fission_schema = select([MFissionScheme]).where(
        MFissionScheme.name == "麒麟裂变方案"
    )
    cur_f_c = await connection.execute(select_fission_schema)
    rec_f_c = await cur_f_c.fetchone()
    # 获取一级二级裂变百分百
    one_commission = float(rec_f_c['one_commission'])
    two_commission = float(rec_f_c['two_commission'])

    # 查询上级ID
    select_user_referrer = select([MUserLeader]).where(
        MUserLeader.user_id == aimuser_id
    )
    cursor_aimuser = await connection.execute(select_user_referrer)
    record_aimuser = await cursor_aimuser.fetchone()

    amount = one_commission / 100 * task_coin if is_one else two_commission / 100 * task_coin

    if record_aimuser:
        # 领导人奖励
        if record_aimuser['leader_id'] != record_aimuser['referrer'] and is_one:
            await cash_exchange_leader(connection, aimuser_id, record_aimuser['leader_id'],
                                       two_commission / 100 * task_coin)

        # 根据上级ID下发徒弟贡献金币变更任务
        # 查询上级是否是合伙人,是合伙人.金币不入账,且享受二级收益
        select_is_partner = select([MPartnerInfo]).where(
            and_(
                MPartnerInfo.status == 1,
                MPartnerInfo.user_id == record_aimuser['referrer']
            )
        )
        cursor_partner = await connection.execute(select_is_partner)
        record_partner = await cursor_partner.fetchone()
        if record_partner:
            # 上级是合伙人
            await cash_exchange_panrtner(connection, record_partner, amount, 1, is_one)
        elif record_aimuser['referrer']:
            # 上级不是合伙人
            await cash_exchange(
                connection,
                user_id=record_aimuser['referrer'],
                amount=amount,
                changed_type=5,
                reason="裂变方案贡献",
                remarks="徒弟贡献",
                flow_type=1
            )
            await fission_schema(
                connection,
                aimuser_id=record_aimuser['referrer'],
                task_coin=task_coin,
                is_one=False
            )
        else:
            return True
        if is_one and record_partner:
            await fission_schema(
                connection,
                aimuser_id=record_aimuser['referrer'],
                task_coin=task_coin,
                is_one=False
            )

    return True


# 合伙人发放入账金币
async def cash_exchange_panrtner(connection, partner_info, amount, flow_type=1, is_one=True):
    # 查询当前用户金币
    select_user_current_coin = select([MUserInfo]).where(
        MUserInfo.user_id == partner_info['user_id']
    )
    cursor_cur_coin = await connection.execute(select_user_current_coin)
    record_cur_coin = await cursor_cur_coin.fetchone()
    if record_cur_coin:

        # 计算金币余额
        if flow_type == 1:
            coin_balance = record_cur_coin['coin'] + amount
        else:
            coin_balance = record_cur_coin['coin'] - amount
            if coin_balance <= 0:
                logger.info("变更金币失败,余额不足")
        retry = 3
        # activity = record_cur_coin['activity_points'] + 1
        while retry:
            try:
                # 插入金币变更信息
                insert_exchange = {
                    "user_id": partner_info['user_id'],
                    "amount": amount,
                    "flow_type": flow_type,
                    "changed_type": 35 if is_one else 36,
                    "changed_time": int(round(time.time() * 1000)),
                    "status": 1,
                    "account_type": 0,
                    "reason": "下级用户贡献",
                    "remarks": "合伙人金币",
                    "coin_balance": coin_balance
                }
                ins_exange = insert(LCoinChange).values(insert_exchange)
                await connection.execute(ins_exange)
                # 更改用户金币
                update_user_coin = update(MUserInfo).values({
                    "coin": coin_balance
                }).where(
                    and_(
                        MUserInfo.user_id == partner_info['user_id'],
                        MUserInfo.coin == record_cur_coin['coin']
                    )
                )
                await connection.execute(update_user_coin)
                return True
            except Exception as e:
                logger.info(e)
                logger.info("修改金币失败,请联系管理员")
                retry -= 1
        return False
    else:
        return False


# 合伙人发放未入账金币
async def cash_exchange_leader(connection, aimuser_id, leader_id, amount, flow_type=1):
    if aimuser_id == leader_id:
        return
    # 确认用户属于二级以下:
    select_ones = select([MUserLeader]).where(
        MUserLeader.referrer == leader_id
    )
    cur_one = await connection.execute(select_ones)
    rec_one = await cur_one.fetchall()
    one_ids = [one['user_id'] for one in rec_one]
    select_two = select([MUserLeader]).where(
        MUserLeader.referrer.in_(one_ids)
    )
    cur_two = await connection.execute(select_two)
    rec_two = await cur_two.fetchall()
    two_ids = [two['user_id'] for two in rec_two]
    if aimuser_id in one_ids or aimuser_id in two_ids:
        return

    # 查询当前用户金币
    select_user_current_coin = select([MPartnerInfo]).where(
        MPartnerInfo.user_id == leader_id
    )
    cursor_cur_coin = await connection.execute(select_user_current_coin)
    record_cur_coin = await cursor_cur_coin.fetchone()
    if record_cur_coin:

        # 计算金币余额
        if flow_type == 1:
            coin_balance = record_cur_coin['future_coin'] + amount
        else:
            coin_balance = record_cur_coin['future_coin'] - amount
            if coin_balance <= 0:
                logger.info("变更金币失败,余额不足")
        retry = 3
        # activity = record_cur_coin['activity_points'] + 1
        while retry:
            try:
                # 插入金币变更信息
                insert_exchange = {
                    "user_id": leader_id,
                    "amount": amount,
                    "flow_type": flow_type,
                    "changed_type": 38,
                    "changed_time": int(round(time.time() * 1000)),
                    "status": 1,
                    "account_type": 0,
                    "reason": "下级用户贡献",
                    "remarks": "合伙人未入账金币(二级以下用户贡献)",
                    "coin_balance": coin_balance
                }
                ins_exange = insert(LCoinChange).values(insert_exchange)
                await connection.execute(ins_exange)
                # 更改用户金币
                update_user_coin = update(MPartnerInfo).values({
                    "future_coin": coin_balance
                }).where(
                    and_(
                        MPartnerInfo.user_id == leader_id,
                        MPartnerInfo.future_coin == record_cur_coin['future_coin']
                    )
                )
                await connection.execute(update_user_coin)
                return True
            except Exception as e:
                logger.info(e)
                logger.info("修改金币失败,请联系管理员")
                retry -= 1
        return False
    else:
        return False


# 查询用户ID
async def select_user_id(connection, t_or_id):
    select_b_token = select([MUserInfo]).where(
        MUserInfo.token == t_or_id
    )
    cur = await connection.execute(select_b_token)
    rec = await cur.fetchone()
    select_b_id = select([MUserInfo]).where(
        MUserInfo.user_id == t_or_id
    )
    if rec:
        return rec['user_id']
    else:
        cur = await connection.execute(select_b_id)
        rec = await cur.fetchone()
        if rec:
            return rec['user_id']
        else:
            return None


# 查询管理员用户ID
async def select_admin_user_id(connection, redis_key, redis_conneciton):
    value = await redis_conneciton.get(redis_key, encoding="utf-8")
    values = value.split('_')
    admin_id = values[3]
    select_admin_id = select([PAdmin]).where(
        PAdmin.admin_id == admin_id
    )
    cur = await connection.execute(select_admin_id)
    rec = await cur.fetchone()
    select_b_id = select([MUserInfo]).where(
        MUserInfo.mobile == rec['mobile']
    )
    cur = await connection.execute(select_b_id)
    rec = await cur.fetchone()
    if rec:
        return rec['user_id']
    else:
        return None


# 查询渠道用户IDs
async def get_channel_user_ids(connection, channel):
    select_user_ids = select([MUserInfo]).where(
        or_(
            MUserInfo.channel_code == channel,
            MUserInfo.parent_channel_code == channel
        )
    )
    cursor = await connection.execute(select_user_ids)
    record = await cursor.fetchall()
    user_ids = [user_info['user_id'] for user_info in record if user_info["user_id"]]
    tokens = [user_info['token'] for user_info in record if user_info["token"]]
    return [*user_ids, *tokens]


# 查询回调信息
async def get_callback_infos(connection, user_ids, platform, params):
    p_dict = {
        "duoyou": {
            "table": TpDyCallback,
            "ordernum": "order_id",
            "userid": "user_id",
            "adid": "advert_id",
            "adname": "advert_name",
            "deviceid": "device_id",
            "price": "media_income",
            "money": "member_income",
            "createTime": "update_time",
            "event": "content",
            "dif_time": "created",
            "defeat_status": 0,
            "success_status": 1,
        },
        "xiangwan": {
            "table": t_tp_pcdd_callback,
            "ordernum": "ordernum",
            "userid": "userid",
            "adid": "adid",
            "adname": "adname",
            "deviceid": "deviceid",
            "price": "price",
            "money": "money",
            "createTime": "createTime",
            "event": "event",
            "dif_time": "price",
            "defeat_status": 1,
            "success_status": 2
        },
        "xianwan": {
            "table": t_tp_xw_callback,
            "ordernum": "ordernum",
            "userid": "appsign",
            "adid": "adid",
            "adname": "adname",
            "deviceid": "deviceid",
            "price": "price",
            "money": "money",
            "createTime": "createTime",
            "event": "event",
            "dif_time": "price",
            "defeat_status": 2,
            "success_status": 1
        },
        "aibianxian": {
            "table": t_tp_ibx_callback,
            "ordernum": "order_id",
            "userid": "target_id",
            "adid": "app_key",
            "adname": "game_name",
            "deviceid": "device_info",
            "price": "app_reward",
            "money": "user_reward",
            "createTime": "update_time",
            "event": "content",
            "dif_time": "time_end",
            "defeat_status": 0,
            "success_status": 1
        },
        "zhiban": {
            "table": TpZbCallback,
            "ordernum": ["uid", "task_id"],
            "userid": "uid",
            "adid": "task_id",
            "adname": "title",
            "deviceid": "dev_code",
            "price": "media_price",
            "money": "price",
            "createTime": "update_time",
            "event": "msg",
            "dif_time": "time",
            "defeat_status": 0,
            "success_status": 1
        },
        "yuwan": {
            "table": TpYwCallback,
            "ordernum": "orderNo",
            "userid": "mediaUserId",
            "adid": "stageId",
            "adname": "advertName",
            "deviceid": "mediaUserId",
            "price": "mediaMoney",
            "money": "userMoney",
            "createTime": "update_time",
            "event": "rewardRule",
            "dif_time": "time",
            "defeat_status": 0,
            "success_status": 1
        },
        "juxiangwan": {
            "table": TpJxwCallback,
            "ordernum": "prize_id",
            "userid": "resource_id",
            "adid": "ad_id",
            "adname": "name",
            "deviceid": "device_code",
            "price": "deal_prize",
            "money": "task_prize",
            "createTime": "update_time",
            "event": "title",
            "dif_time": "prize_time",
            "defeat_status": 0,
            "success_status": 1
        }
    }

    # 查对应回调表
    # 初始化对象
    s_table = p_dict[platform]["table"]
    ordernum = p_dict[platform]["ordernum"]
    userid = p_dict[platform]["userid"]
    adid = p_dict[platform]["adid"]
    adname = p_dict[platform]["adname"]
    deviceid = p_dict[platform]["deviceid"]
    price = p_dict[platform]["price"]
    money = p_dict[platform]["money"]
    event = p_dict[platform]["event"]
    dif_time = p_dict[platform]["dif_time"]
    createTime = p_dict[platform]["createTime"]
    defeat_status = p_dict[platform]["defeat_status"]
    success_status = p_dict[platform]["success_status"]

    # 构造条件
    conditions = []
    if "accountId" in params:
        # 先查询用户真实id
        select_real_id = select([MUserInfo]).where(
            MUserInfo.account_id == params['accountId']
        )
        c_id = await connection.execute(select_real_id)
        r_id = await c_id.fetchone()
        conditions.append(text(userid + '="' + r_id['user_id'] + '"'))
    if "adname" in params:
        conditions.append(text(adname + '="' + params['adname'] + '"'))
    if "status" in params:
        # params - status 1成功,2失败
        status_key = success_status if params['status'] == 1 else defeat_status
        conditions.append(text("status" + '=' + str(status_key)))
    if "startTime" in params:
        conditions.append(text(dif_time + '>' + int(params['startTime'])))
    if "endTime" in params:
        conditions.append(text(dif_time + '<' + int(params['endTime'])))
    if "yoleid" in params:
        if platform != "zhiban":
            conditions.append(text(ordernum + '="' + params['yoleid'] + '"'))

    # 过滤渠道用户
    if user_ids:
        conditions.append(text(userid + " IN " + str(tuple(user_ids))))

    select_allcallback = select([s_table]).where(and_(*conditions))
    print(select_allcallback)
    cursor = await connection.execute(select_allcallback)
    record = await cursor.fetchall()
    tasks = serialize(cursor, record)

    # 构造返回list_info
    list_info = []
    for task in tasks:
        # 先查询用户真实id
        select_real_id = select([MUserInfo]).where(
            MUserInfo.user_id == task[userid]
        )
        real_c = await connection.execute(select_real_id)
        real_r = await real_c.fetchone()
        real_record = ""
        if real_r:
            select_channel_info = select([MChannelInfo]).where(
                MChannelInfo.channel_code == real_r['channel_code']
            )
            real_channel_info = await connection.execute(select_channel_info)
            real_record = await real_channel_info.fetchone()
        result = {
            "accountId": real_r['account_id'] if real_r else "未知用户",
            "ordernum": task[ordernum] if platform != "zhiban" else "",
            "adid": task[adid],
            "pid": real_record['channel_id'] if real_r and real_record else "未知",
            "adname": task[adname],
            "channelCode": real_r['channel_code'] if real_r else "未知渠道",
            "createTime": task[createTime],
            "deviceid": task[deviceid],
            "event": task[event],
            "dlevel": 1,
            "price": task[price],
            "money": task[money],
            "status": 2 if task['status'] == success_status else 1

        }
        list_info.append(result)

    # 统计信息
    # 渠道内
    smallSuccessCount = len([task for task in tasks if task['status'] == success_status])
    smallPriceSum = sum([float(task[price]) for task in tasks if task['status'] == success_status])
    smallMoneySum = sum([float(task[money]) for task in tasks if task['status'] == success_status])
    # 总数
    select_totalcallback = select([s_table]).where(
        text("status" + '=' + str(success_status))
    )
    cursor_totalcallback = await connection.execute(select_totalcallback)
    record_totalcallback = await cursor_totalcallback.fetchall()
    SuccessCount = len([task for task in record_totalcallback])
    PriceSum = sum([float(task[price]) for task in record_totalcallback])
    MoneySum = sum([float(task[money]) for task in record_totalcallback])
    agg_info = {
        "smallSuccessCount": int(smallSuccessCount),
        "smallPriceSum": int(smallPriceSum),
        "smallMoneySum": int(smallMoneySum),
        "successCount": int(SuccessCount),
        "priceSum": int(PriceSum),
        "moneySum": int(MoneySum),
        "total": int(len(tasks))
    }

    return list_info, agg_info


# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(get_channel_user_ids())

# 用户签到视频
async def today_user_sign(connection, user_id):
    # 查询已有签到
    select_user_sign = select([LUserSign]).where(
        LUserSign.user_id == user_id
    )
    cur_sign = await connection.execute(select_user_sign)
    rec_sign = await cur_sign.fetchone()

    sign_coin_from_dic = await get_pdictionary_key(connection, "sign_coin")
    sign_coin = eval(sign_coin_from_dic)
    now = datetime.now()
    lastYesday = now - timedelta(hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
    # 获取23:59:59
    zeroYesday = lastYesday - timedelta(hours=23, minutes=59, seconds=59)
    zeroYesdaytime = time.mktime(zeroYesday.timetuple()) * 1000
    lastYesdaytime = time.mktime(lastYesday.timetuple()) * 1000
    if rec_sign and rec_sign['sign_time'] > lastYesdaytime:
        return False
    # if rec_sign and int(time.time()*1000) - rec_sign['sign_time'] < 86400000:
    if rec_sign and zeroYesdaytime < rec_sign['sign_time'] < lastYesdaytime:
        next_stick_times = rec_sign['stick_times'] + 1
    else:
        next_stick_times = 1
    reward_coin = sign_coin[next_stick_times - 1] if next_stick_times <= len(sign_coin) else 2000
    # 更新签到表
    sign_info = {
        "user_id": user_id,
        "sign_time": int(time.time() * 1000),
        "score": 200,
        "stick_times": next_stick_times,
        "is_task": 1,
        "task_coin": reward_coin
    }
    if rec_sign:
        await connection.execute(update(LUserSign).values(sign_info).where(LUserSign.user_id == user_id))
    else:
        await connection.execute(insert(LUserSign).values(sign_info))
    # 发放奖励
    c_result = await cash_exchange(
        connection=connection,
        user_id=user_id,
        amount=reward_coin,
        changed_type=29,
        reason="每日红包奖励",
        remarks="每日红包签到视频奖励"
    )
    if c_result:
        await connection.execute(update(LUserSign).values({
            "is_task": 2
        }).where(LUserSign.user_id == user_id))
    return True


# 插入提现待审核数据
async def insert_exchange_cash(connection, user_id, cash, create_time, update_time, game_number):
    select_user_wage = select([MWageRecord]).where(
        and_(
            MWageRecord.create_time == create_time,
            MWageRecord.user_id == user_id
        )
    )
    cur_user_wage = await connection.execute(select_user_wage)
    rec_user_wage = await cur_user_wage.fetchone()
    if rec_user_wage['status'] == 3:
        return False, "今日工资已提现"
    # 查询用户信息
    select_user = select([MUserInfo]).where(
        MUserInfo.user_id == user_id
    )
    cur_user = await connection.execute(select_user)
    rec_user = await cur_user.fetchone()
    if not rec_user or not rec_user['user_name'] or not rec_user['ali_num']:
        return False, "请在下方绑定支付宝"
    current_time = int(time.time() * 1000)

    # 获取当前任务数
    c_time = time.mktime(update_time.timetuple()) * 1000
    coinchange_games = select([LCoinChange]).where(
        and_(
            LCoinChange.user_id == user_id,
            LCoinChange.changed_type == 7,
            LCoinChange.changed_time > c_time
        )
    ).order_by(LCoinChange.changed_time.asc())
    cur_coinchange_games = await connection.execute(coinchange_games)
    rec_coinchange_games = await cur_coinchange_games.fetchall()
    real_tasks = []
    for task in rec_coinchange_games:
        if len(real_tasks) == game_number:
            break
        if '天天抢红包' not in task['remarks'] and '充值' not in task['remarks'] and 'sdk试玩' not in task['remarks']:
            real_tasks.append(task['amount'])
    amount = sum(real_tasks)
    if amount > (cash * 10000):
        amount = cash * 10000
    # 减去余额
    nsq_topic = "ql_callback_queue"
    nsq_msg = {
        "task": "reward_task",
        "data": {
            "user_id": user_id,
            "amount": amount,
            "changed_type": 3,
            "reason": "每日工资提现",
            "remarks": "每日工资提现",
            "flow_type": 2
        }
    }
    await pub_to_nsq(NSQ_NSQD_HTTP_ADDR, nsq_topic, nsq_msg)

    time.sleep(3)
    select_user_exchange_id = select([LCoinChange]).where(
        and_(
            LCoinChange.user_id == user_id,
            LCoinChange.flow_type == 2
        )
    ).order_by(LCoinChange.changed_time.desc()).limit(1)
    cur_id = await connection.execute(select_user_exchange_id)
    rec_id = await cur_id.fetchone()

    # 插入exchangecash表
    await connection.execute(insert(LUserExchangeCash).values({
        "coin_change_id": rec_id['id'],
        "user_id": user_id,
        "out_trade_no": str(current_time) + rec_user['qr_code'],
        "bank_account": rec_user['ali_num'],
        "real_name": rec_user['user_name'],
        "coin": cash * 10000,
        "actual_amount": cash,
        "service_charge": 0,
        "coin_balance": 0,
        "coin_to_money": 10000,
        "creator_time": current_time,
        "state": 1,
        "is_locking": 2,
        "user_ip": "127.0.0.1",
        "cash_type": 1,
    }))

    await connection.execute(update(MWageRecord).values({
        "status": 3,
        "reward": 0
    }).where(
        and_(
            MWageRecord.create_time == create_time,
            MWageRecord.user_id == user_id
        )
    ))

    return True, "申请提现成功"
