# 麒麟分佣任务
import asyncio
import time

from sqlalchemy import select, update, insert, and_, text, or_

from models.alchemy_models import MUserInfo, MFissionScheme, LCoinChange, TpDyCallback, t_tp_pcdd_callback, \
    t_tp_xw_callback, t_tp_ibx_callback, TpZbCallback, TpYwCallback, TpJxwCallback, MChannelInfo, MPartnerInfo, \
    MUserLeader, LUserSign
from util.log import logger

# 金币变更任务
from util.static_methods import serialize, get_pdictionary_key


# 流水变更及发放金币
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
    35 合伙人一级直属用户贡献 36 合伙人二级直属用户贡献 37 闯关助力
    :param remarks: 标识信息
    :param reason: 理由
    :return:
    """

    # 查询当前用户金币
    select_user_current_coin = select([MUserInfo]).where(
        MUserInfo.user_id == user_id
    )
    cursor_cur_coin = await connection.execute(select_user_current_coin)
    record_cur_coin = await cursor_cur_coin.fetchone()
    select_user_leader = select([MUserLeader]).where(
        MUserLeader.user_id == user_id
    )
    cursor_leader = await connection.execute(select_user_leader)
    record_leader = await cursor_leader.fetchone()
    if record_leader:
        select_user_partner = select([MPartnerInfo]).where(
            MPartnerInfo.user_id == record_leader['leader_id']
        )
        cursor_partner = await connection.execute(select_user_partner)
        record_partner = await cursor_partner.fetchone()
        if record_partner:
            current_activity = record_partner['activity_points'] + 1
    if record_cur_coin:

        # 计算金币余额
        if flow_type == 1:
            coin_balance = record_cur_coin['coin'] + amount
        else:
            coin_balance = record_cur_coin['coin'] - amount
            if coin_balance <= 0:
                logger.info("变更金币失败,余额不足")
        retry = 3
        while retry:
            try:
                # 插入金币变更信息
                insert_exchange = {
                    "user_id": user_id,
                    "amount": amount,
                    "flow_type": flow_type,
                    "changed_type": changed_type,
                    "changed_time": int(round(time.time() * 1000)),
                    "status": 1,
                    "account_type": 0,
                    "reason": reason,
                    "remarks": remarks,
                    "coin_balance": coin_balance
                }
                ins_exange = insert(LCoinChange).values(insert_exchange)
                await connection.execute(ins_exange)
                # 更改用户金币
                update_user_coin = update(MUserInfo).values({
                    "coin": coin_balance
                }).where(
                    and_(
                        MUserInfo.user_id == user_id,
                        MUserInfo.coin == record_cur_coin['coin']
                    )
                )
                await connection.execute(update_user_coin)
                if record_leader:
                    update_leader_activity = update(MPartnerInfo).values({
                        "activity_points": current_activity
                    }).where(
                        MPartnerInfo.user_id == record_leader['leader_id']
                    )
                    await connection.execute(update_leader_activity)
                return True
            except Exception as e:
                logger.info(e)
                logger.info("修改金币失败,请联系管理员")
                retry -= 1
        return False
    else:
        return False


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
    select_user_referrer = select([MUserInfo]).where(
        MUserInfo.user_id == aimuser_id
    )
    cursor_aimuser = await connection.execute(select_user_referrer)
    record_aimuser = await cursor_aimuser.fetchone()

    amount = one_commission / 100 * task_coin if is_one else two_commission / 100 * task_coin

    if record_aimuser:
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
            # 上级是合伙人,金币加入合伙人表
            if is_one:
                await cash_exchange_panrtner(connection, record_partner, amount, 1, is_one)
            else:
                await cash_exchange_panrtner(connection, record_partner, amount, 1, False)
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


# 合伙人发放未入账金币
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
        activity = record_cur_coin['activity_points'] + 1
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
                    "remarks": "合伙人未入账金币",
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

async def today_user_sign(connection, user_id):
    # 查询已有签到
    select_user_sign = select([LUserSign]).where(
        LUserSign.user_id == user_id
    )
    cur_sign = await connection.execute(select_user_sign)
    rec_sign = await cur_sign.fetchone()
    sign_coin_from_dic = await get_pdictionary_key(connection, "sign_coin")
    sign_coin = eval(sign_coin_from_dic)
    if rec_sign and rec_sign['sigh_time'] - int(time.time()*1000) < 86400000:
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
