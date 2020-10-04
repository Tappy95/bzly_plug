# 麒麟分佣任务
import time

from sqlalchemy import select, update, insert

from models.alchemy_models import MUserInfo, MFissionScheme, LCoinChange
from util.log import logger


# 金币变更任务
async def cash_exchange(connection, user_id, amount, changed_type, reason, remarks, flow_type=1):
    """
    :param connection:
    :param user_id:
    :param amount: 变更金额
    :param flow_type: 变更类型1收入-2支出
    :param changed_type: 变更原因1答题2来访礼3提现4推荐用户获得5徒弟贡献6vip 7.游戏试玩奖励 8.徒弟到达4L奖励
    9-新人注册奖励10任务11出题12兑换金猪 13-阅读资讯14-提现退回15直属用户返利 16-团队长赠送17间接用户返利18居间返利
    19-阅读广告奖励 20-分享资讯 21-签到赚 22-大众团队长分佣 23-快速赚任务 24-达人首次奖励 25-达人后续奖励 26-阅读小说
    27 达人邀请周榜奖励 28-高额赚提成 29 每日红包任务 30观看视频 31 小游戏奖励 32打卡消耗33打卡奖励 34 金币排行日榜奖励
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
    if record_cur_coin:

        # 计算金币余额
        if flow_type == 1:
            coin_balance = record_cur_coin['coin'] + amount
        else:
            coin_balance = record_cur_coin['coin'] - amount
            if coin_balance <= 0:
                logger.info("变更金币失败,余额不足")
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
                MUserInfo.user_id == user_id
            )
            await connection.execute(update_user_coin)
        except Exception as e:
            logger.info(e)
            logger.info("修改金币失败,请联系管理员")
            return False

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
    select_user_referrer = select([MUserInfo]).where(
        MUserInfo.user_id == aimuser_id
    )
    cursor_aimuser = await connection.execute(select_user_referrer)
    record_aimuser = await cursor_aimuser.fetchone()
    amount = one_commission / 100 * task_coin if is_one else two_commission / 100 * task_coin
    if record_aimuser:
        # 根据上级ID下发徒弟贡献金币变更任务
        await cash_exchange(
            connection,
            user_id=record_aimuser['referrer'],
            amount=amount,
            changed_type=5,
            reason="裂变方案贡献",
            remarks="徒弟贡献",
            flow_type=1
        )
        if is_one:
            await fission_schema(
                connection,
                aimuser_id=record_aimuser['referrer'],
                task_coin=task_coin,
                is_one=False
            )

    return True
