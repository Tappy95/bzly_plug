# coding: utf-8
import json

from sqlalchemy import Column, DECIMAL, Date, DateTime, Float, Index, String, Table, Text, text, BigInteger, Integer
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.declarative import DeclarativeMeta


class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)  # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


Base = declarative_base()
metadata = Base.metadata


class AppNewsInform(Base):
    __tablename__ = 'app_news_inform'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), index=True, comment='用户id')
    mobile = Column(String(11), comment='用户手机号')
    inform_title = Column(String(64))
    inform_content = Column(Text)
    push_object = Column(INTEGER(1), comment='推送对象1个人2所有人')
    push_time = Column(BIGINT(20), comment='推送时间')
    creater_time = Column(BIGINT(20))
    inform_type = Column(INTEGER(1), comment='通知类型1普通通知2自定义通知')
    inform_url = Column(String(400), server_default=text("'1'"), comment='自定义消息跳转链接')
    is_release = Column(INTEGER(1), comment='是否发布1.发布2.撤回')
    is_push = Column(INTEGER(1), comment='是否推送1未推送2已推送')
    push_mode = Column(INTEGER(1), comment='通知方式1短信2推送')
    add_mode = Column(INTEGER(1), comment='添加方式1后台添加2自动添加')
    is_read = Column(INTEGER(1), server_default=text("'1'"), comment='是否已读1未读2已读')
    app_type = Column(INTEGER(1), comment='app类型：1宝猪2中青赚点')


class AppNewsNotice(Base):
    __tablename__ = 'app_news_notice'

    id = Column(INTEGER(10), primary_key=True, comment='app公告id')
    notice_type = Column(INTEGER(1), comment='公告类型1文字公告2首页活动3消息活动')
    notice_title = Column(String(64), comment='公告标题')
    notice_content = Column(String(4000), comment='公告内容')
    img_url = Column(String(64), comment='公告图片')
    link_address = Column(String(256), comment='链接地址')
    ranges = Column(INTEGER(3), server_default=text("'1'"), comment='通知范围1全部')
    releaser_time = Column(BIGINT(20), comment='发布时间')
    cancel_time = Column(BIGINT(20), comment='取消时间')
    creater_time = Column(BIGINT(20), comment='创建时间')
    creater_mobile = Column(String(11), comment='创建人电话')
    is_release = Column(INTEGER(1), comment='定时器状态发布1.发布2.未发布3.已失效')
    is_publish = Column(INTEGER(1), comment='手动处理是否发布，1是2否')
    app_type = Column(INTEGER(1), comment='app类型：1宝猪2中青赚点')


class AppNoticeUser(Base):
    __tablename__ = 'app_notice_user'

    id = Column(INTEGER(10), primary_key=True)
    notice_id = Column(INTEGER(10), comment='公告id')
    user_id = Column(String(64), comment='用户id')
    read_num = Column(INTEGER(10), comment='阅读次数')
    creater_time = Column(BIGINT(20), comment='阅读时间')


t_btest = Table(
    'btest', metadata,
    Column('id', INTEGER(10)),
    Column('name', INTEGER(10))
)


class CCheckinContinuity(Base):
    __tablename__ = 'c_checkin_continuity'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    continuity_days = Column(INTEGER(10), comment='连续天数')
    update_time = Column(BIGINT(20), comment='修改时间')


class CCheckinLog(Base):
    __tablename__ = 'c_checkin_log'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    pay_coin = Column(BIGINT(20), comment='支付金币')
    reward_coin = Column(BIGINT(20), comment='奖励金币')
    user_type = Column(INTEGER(1), comment='用户类型：1真实用户2机器人')
    state = Column(INTEGER(1), comment='状态：1待打卡，2打卡成功，3打卡失败')
    create_time = Column(BIGINT(20), comment='创建时间')
    checkin_time = Column(BIGINT(20), comment='打卡时间（系统规定打卡开始时间）')
    user_time = Column(BIGINT(20), comment='用户打卡时间')
    last_time = Column(BIGINT(20), comment='上次打卡时间')
    continuity_days = Column(INTEGER(10), comment='连续打卡次数')
    is_tips = Column(INTEGER(1), comment='是否已提示打卡失败弹框1未提示2提示')
    is_coupon = Column(INTEGER(1), comment='是否使用补签券1未使用2使用')


class CCheckinLucky(Base):
    __tablename__ = 'c_checkin_lucky'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    img = Column(String(128), comment='头像')
    mobile = Column(String(11), comment='手机号')
    reward_coin = Column(BIGINT(20), comment='奖励金币')
    create_time = Column(BIGINT(20), comment='创建时间')


class CCheckinResult(Base):
    __tablename__ = 'c_checkin_result'

    id = Column(INTEGER(10), primary_key=True)
    bonus_pool = Column(BIGINT(20), comment='总金额')
    success_number = Column(INTEGER(10), comment='成功人数')
    fail_number = Column(INTEGER(10), comment='失败人数')
    success_real_number = Column(INTEGER(10), comment='真实成功人数')
    fail_real_number = Column(INTEGER(10), comment='真实失败人数')
    create_Time = Column(BIGINT(20), comment='创建时间')
    actual_bonus = Column(BIGINT(20), comment='实际奖金')


class CCheckinRewardRule(Base):
    __tablename__ = 'c_checkin_reward_rule'

    id = Column(INTEGER(10), primary_key=True)
    min_number = Column(INTEGER(10), comment='参与打卡最小人数')
    max_number = Column(INTEGER(10), comment='参与打卡最大人数')
    reward_ratio = Column(INTEGER(3), comment='奖金比例（%）')
    extra_reward = Column(BIGINT(20), comment='额外奖励（单位：金币）')
    create_time = Column(BIGINT(20), comment='创建时间')
    min_reward = Column(BIGINT(20), comment='最小奖励')
    max_reward = Column(BIGINT(20), comment='最大奖励')


class EGoldEggType(Base):
    __tablename__ = 'e_gold_egg_type'

    id = Column(INTEGER(10), primary_key=True)
    name = Column(String(16), comment='名称')
    pig_coin = Column(BIGINT(20), comment='消耗金猪')
    creator_time = Column(BIGINT(20), comment='创建时间')
    orders = Column(INTEGER(10), comment='排序')
    service_pig_coin = Column(BIGINT(20), comment='手续费')
    card_sign = Column(String(16), comment='卡号标记')


class EGoleEggOrder(Base):
    __tablename__ = 'e_gole_egg_order'

    id = Column(BIGINT(20), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    pig_coin = Column(BIGINT(20), comment='消耗金猪')
    obtain_pig_coin = Column(BIGINT(20), comment='获得金猪')
    card_number = Column(String(32), comment='卡号')
    card_password = Column(String(32), comment='卡密')
    state = Column(INTEGER(1), comment='状态：1未使用2已使用')
    exchange_user_id = Column(String(64), comment='使用者用户id')
    creator_time = Column(BIGINT(20), comment='创建时间')
    exchange_time = Column(BIGINT(20), comment='使用时间')
    is_prohibit = Column(INTEGER(1), comment='是否禁用：1否2是')
    modify_password = Column(INTEGER(2), comment='修改密码次数')


class EUserGoldEgg(Base):
    __tablename__ = 'e_user_gold_egg'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    frequency = Column(INTEGER(3), comment='砸金蛋次数')
    creator_time = Column(BIGINT(20), comment='创建时间')
    update_time = Column(BIGINT(20), comment='修改时间')


class JmsNewsLog(Base):
    __tablename__ = 'jms_news_log'

    id = Column(INTEGER(10), primary_key=True)
    jms_wrapper = Column(Text)
    jms_destination = Column(String(64), comment='队列名称')
    jms_exception = Column(Text, comment='异常原因')
    state = Column(INTEGER(1), comment='1成功2失败')
    creater_time = Column(BIGINT(20), comment='创建时间')


class LActiveGoldLog(Base):
    __tablename__ = 'l_active_gold_log'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    vip_id = Column(INTEGER(10), comment='vipId')
    active_coin = Column(BIGINT(20), comment='活跃金币')
    active_pig = Column(BIGINT(20), comment='活跃金猪')
    days = Column(BIGINT(1), comment='领取天数')
    creator_time = Column(BIGINT(20), comment='创建时间')


class LBalanceChange(Base):
    __tablename__ = 'l_balance_change'
    __table_args__ = {'comment': 'Users Balance change log'}

    log_id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(50), comment='用户id')
    amount = Column(DECIMAL(10, 2), comment='changed amount')
    account = Column(String(255))
    account_type = Column(INTEGER(255), comment='账号类型（1-微信 2-支付宝）')
    flow_type = Column(INTEGER(11), nullable=False, comment='流水类型（1-收入 2-支出）')
    changed_type = Column(INTEGER(11), comment='变更类型：（1-充值 2-提现 3-推荐好友 4-参与打卡 5-打卡奖励 6-购买会员 7-团队长赠送）')
    changed_time = Column(BIGINT(20), comment='变更时间')
    is_auditing = Column(INTEGER(11), comment='是需要审核的吗？如果不，则设置为0，如果设置大于零，则表示审查的进度。1:待审核 2审核中 3拒绝 4成功')
    reason = Column(String(255), comment='拒绝原因')
    review_time = Column(BIGINT(20))


class LCashGameTask(Base):
    __tablename__ = 'l_cash_game_task'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    game_id = Column(INTEGER(10), comment='游戏id')
    create_time = Column(BIGINT(20), comment='创建时间')
    cash_id = Column(INTEGER(10), index=True, comment='需要完成任务提现记录id')


class LCoinChange(Base):
    __tablename__ = 'l_coin_change'

    id = Column(INTEGER(10), primary_key=True, comment='金币收入支出')
    user_id = Column(String(64), index=True)
    amount = Column(BIGINT(20), comment='变更金额')
    flow_type = Column(INTEGER(1), comment='变更类型1收入-2支出')
    changed_type = Column(INTEGER(1), index=True,
                          comment='变更原因1答题2来访礼3提现4推荐用户获得5徒弟贡献6vip 7.游戏试玩奖励 8.徒弟到达4L奖励 9-新人注册奖励10任务11出题12兑换金猪 '
                                  '13-阅读资讯14-提现退回15直属用户返利 16-团队长赠送17间接用户返利18居间返利 19-阅读广告奖励 20-分享资讯 21-签到赚 22-大众团队长分佣 '
                                  '23-快速赚任务 24-达人首次奖励 25-达人后续奖励 26-阅读小说 27 达人邀请周榜奖励 28-高额赚提成 29 每日红包任务 30观看视频 31 '
                                  '小游戏奖励 32打卡消耗33打卡奖励 34 金币排行日榜奖励')
    changed_time = Column(BIGINT(20), index=True, comment='变更时间')
    status = Column(INTEGER(2), server_default=text("'1'"), comment="'状态（1-正常 2-冻结 3-拒绝）',")
    account_type = Column(INTEGER(2), server_default=text("'0'"), comment='提现账户类型（0-非提现 1-微信 2-支付宝）')
    audit_time = Column(BIGINT(20), comment='审核时间')
    reason = Column(String(255))
    remarks = Column(String(512))
    coin_balance = Column(BIGINT(20), comment='金币余额')


class LDarenActivity(Base):
    __tablename__ = 'l_daren_activity'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(64), nullable=False, index=True, comment='达人id')
    activity_score = Column(DECIMAL(10, 2), nullable=False, comment='活跃度')
    quality_score = Column(INTEGER(11), nullable=False, comment='质量分')
    create_date = Column(String(32), nullable=False, comment='创建日期（格式：yyyy-MM-dd）')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间（格式：时间戳）')


class LDarenReward(Base):
    __tablename__ = 'l_daren_reward'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True, comment='达人id')
    reward_date = Column(String(255), nullable=False, comment='奖励时间')
    apprentice_count = Column(INTEGER(255), nullable=False, comment='有效徒弟数')
    first_reward = Column(BIGINT(20), nullable=False, server_default=text("'0'"), comment='首次奖励')
    second_reward = Column(BIGINT(20), nullable=False, server_default=text("'0'"), comment='后续奖励')
    task_count = Column(INTEGER(2), nullable=False, server_default=text("'0'"), comment='任务个数')
    update_time = Column(BIGINT(20), nullable=False, comment='更新时间')


class LDarenRewardDetail(Base):
    __tablename__ = 'l_daren_reward_detail'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(255), nullable=False, comment='达人id')
    reward = Column(BIGINT(20), nullable=False, comment='达人奖励')
    apprentice_id = Column(String(255), nullable=False, comment='徒弟id')
    apprentice_reward = Column(BIGINT(20), nullable=False, comment='徒弟奖励金额')
    task_type = Column(INTEGER(2), nullable=False, comment='任务类型（1-首个任务 2-后续任务）')
    task_name = Column(String(255), nullable=False, comment='任务名称')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')


class LFightingInfo(Base):
    __tablename__ = 'l_fighting_info'
    __table_args__ = {'comment': 'User fighting log'}

    log_id = Column(INTEGER(11), primary_key=True)
    fight_id = Column(INTEGER(11), nullable=False)
    user_id = Column(String(50), nullable=False)
    question_id = Column(INTEGER(11), nullable=False)
    answer_id = Column(INTEGER(11))
    is_correct = Column(INTEGER(11))
    score = Column(BIGINT(20))
    answer_time = Column(BIGINT(20))


class LNoticeReady(Base):
    __tablename__ = 'l_notice_ready'
    __table_args__ = {'comment': '用户提醒表'}

    id = Column(INTEGER(11), primary_key=True)
    notice_type = Column(INTEGER(2), nullable=False, comment='提醒类型（1-每日红包提醒）')
    user_id = Column(String(255), nullable=False, comment='用户id')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')


class LPigChanage(Base):
    __tablename__ = 'l_pig_chanage'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    amount = Column(BIGINT(20), comment='变更金额')
    flow_type = Column(INTEGER(10), comment='变更类型1收入-2支出')
    changed_type = Column(INTEGER(10),
                          comment='变更原因1vip2提现3任务4试玩5金币兑换获得6竞猜7vip救济金猪 8-金猪抽奖 9抽奖退回 10竞猜退回 11-团队长赠送 12-救济金猪 13砸金蛋 14使用金蛋 15-金猪日榜排行奖励')
    changed_time = Column(BIGINT(20), comment='变更时间')
    remarks = Column(VARCHAR(64), comment='备注')
    pig_balance = Column(BIGINT(20), comment='金猪余额')


class LRankCoin(Base):
    __tablename__ = 'l_rank_coin'
    __table_args__ = {'comment': '金币排行榜'}

    id = Column(INTEGER(11), primary_key=True)
    rank_type = Column(INTEGER(11), nullable=False, comment='排行榜类型（1-天榜 2-周榜 3-月榜 4-年榜 5-总榜）')
    rank_order = Column(INTEGER(11), nullable=False, comment='排名')
    image_url = Column(String(255), comment='头像')
    alias_name = Column(String(255), comment='用户别名')
    mobile = Column(String(255), comment='电话号码')
    user_id = Column(String(64), comment='用户id')
    coin_balance = Column(BIGINT(40), comment='累计金币数')
    rank_date = Column(String(255), comment='排名时间')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    real_data = Column(INTEGER(2), comment='是否真实用户（1-是 2-不是）')
    reward_amount = Column(BIGINT(20), server_default=text("'0'"), comment='奖励金额')


class LRankDarenWeak(Base):
    __tablename__ = 'l_rank_daren_weak'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(255), nullable=False, comment='达人id')
    apprentice_count = Column(INTEGER(11), nullable=False, server_default=text("'0'"), comment='徒弟数量')
    rank = Column(INTEGER(11), nullable=False, comment='排名')
    reward = Column(BIGINT(20), comment='奖励金币数')
    rank_cycle = Column(String(255), nullable=False, comment='排行周期（如8.12-8.19）')
    create_date = Column(String(255), nullable=False, comment='排名时间')
    status = Column(INTEGER(2), nullable=False, comment='是否结算（1-未结算 2-已结算）')


class LRankMachine(Base):
    __tablename__ = 'l_rank_machine'

    id = Column(INTEGER(10), primary_key=True)
    img = Column(String(64), comment='用户头像')
    mobile = Column(String(11), comment='电话号码')
    create_time = Column(BIGINT(20), comment='创建时间')


class LRankPig(Base):
    __tablename__ = 'l_rank_pig'
    __table_args__ = {'comment': '金猪排行榜'}

    id = Column(INTEGER(11), primary_key=True)
    rank_type = Column(INTEGER(11), nullable=False)
    rank_order = Column(INTEGER(11), nullable=False)
    image_url = Column(String(255))
    alias_name = Column(String(255))
    mobile = Column(String(255))
    user_id = Column(String(64))
    pig_balance = Column(BIGINT(40))
    rank_date = Column(String(255))
    create_time = Column(BIGINT(20), nullable=False)
    real_data = Column(INTEGER(2))
    reward_amount = Column(BIGINT(20), server_default=text("'0'"), comment='奖励金猪数')


class LUserActive(Base):
    __tablename__ = 'l_user_active'
    __table_args__ = (
        Index('unique_id_time', 'user_id', 'active_time', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(255), nullable=False)
    active_time = Column(String(255), nullable=False)
    active_ip = Column(String(255), nullable=False)


class LUserAdsReward(Base):
    __tablename__ = 'l_user_ads_reward'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(64), nullable=False, comment='用户id')
    content = Column(String(512), nullable=False, comment='内容正文')
    reward_date = Column(String(20), nullable=False, comment='阅读时间')
    status = Column(INTEGER(2), nullable=False)


class LUserBq(Base):
    __tablename__ = 'l_user_bq'
    __table_args__ = {'comment': '用户补签卡'}

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(32), nullable=False, comment='用户id')
    card_count = Column(INTEGER(11), nullable=False, comment='补签卡数量')
    update_time = Column(BIGINT(20), nullable=False, comment='创建时间戳')
    bq_type = Column(INTEGER(1), comment='1签到赚2打卡')


class LUserCash(Base):
    __tablename__ = 'l_user_cash'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    out_trade_no = Column(String(64), comment='提现订单号')
    mode = Column(INTEGER(1), comment='提现方式1-微信 2-支付宝')
    money = Column(INTEGER(5), comment='提现金额')
    state = Column(INTEGER(1), comment='状态：1未完成2已完成3审核中4提现成功5提现异常')
    creator_time = Column(BIGINT(20), comment='创建时间')


class LUserCashLog(Base):
    __tablename__ = 'l_user_cash_log'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    out_trade_no = Column(String(64), comment='提现订单号')
    cash_coin = Column(BIGINT(20), comment='提现金额 单位：金币')
    cash_time = Column(BIGINT(20), comment='提现时间')
    cash_num = Column(INTEGER(5), comment='提现次数')
    days = Column(INTEGER(5), comment='距离注册时间的天数')


class LUserCashtoutiao(Base):
    __tablename__ = 'l_user_cashtoutiao'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(255), nullable=False, comment='用户id')
    channel = Column(String(255), nullable=False, comment='新闻类目')
    create_time = Column(BIGINT(20), nullable=False)
    status = Column(INTEGER(2), nullable=False, comment='状态（1-成功 2-失败）')


class LUserCheckin(Base):
    __tablename__ = 'l_user_checkin'
    __table_args__ = {'comment': 'Users check-in information'}

    user_id = Column(String(50), primary_key=True)
    total_investment = Column(DECIMAL(10, 2), comment='Cumulative investment')
    total_success = Column(INTEGER(11), server_default=text("'0'"), comment='Cumulative success days')
    total_failure = Column(INTEGER(11), server_default=text("'0'"), comment='Cumulative failure days')
    total_reward = Column(DECIMAL(10, 2), server_default=text("'0.00'"), comment='Cumulative reward')


class LUserExchangeCash(Base):
    __tablename__ = 'l_user_exchange_cash'

    id = Column(INTEGER(10), primary_key=True)
    coin_change_id = Column(INTEGER(10), comment='金币变动表id')
    user_id = Column(String(64), index=True, comment='用户id')
    out_trade_no = Column(String(32), comment='订单号')
    bank_account = Column(String(64), comment='银行卡号')
    real_name = Column(String(32), comment='真实姓名')
    coin = Column(BIGINT(20), comment='提现金币')
    actual_amount = Column(DECIMAL(10, 2), comment='实际提现金额（元）')
    service_charge = Column(DECIMAL(10, 2), comment='提现服务费（元）')
    coin_balance = Column(BIGINT(20), comment='金币余额')
    coin_to_money = Column(INTEGER(10), comment='兑换比例')
    creator_time = Column(BIGINT(20), comment='创建时间')
    operator_mobile = Column(String(11), comment='操作人电话')
    examine_time = Column(BIGINT(20), comment='审核时间')
    remarks = Column(String(200), comment='备注')
    state = Column(INTEGER(1), comment='1审核中2提现成功3提现失败4提现异常5提现通过')
    locking_mobile = Column(String(11), comment='锁定人账号')
    is_locking = Column(INTEGER(1), comment='是否锁定1是2否')
    user_ip = Column(String(32), comment='用户ip地址')
    cash_type = Column(INTEGER(1), server_default=text("'1'"), comment='提现类型1不用完成任务2完成任务')


class LUserFirstLog(Base):
    __tablename__ = 'l_user_first_log'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    is_one = Column(INTEGER(1), comment='是否第一次进入app1是2不是')


class LUserGame(Base):
    __tablename__ = 'l_user_game'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True, comment='用户id')
    game_id = Column(INTEGER(11), comment='游戏id')
    modify_time = Column(BIGINT(20), comment='试玩时间')


class LUserGameTask(Base):
    __tablename__ = 'l_user_game_task'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), index=True, comment='用户id')
    game_id = Column(INTEGER(10), comment='游戏id')
    vip_id = Column(INTEGER(10), comment='vipId')
    state = Column(INTEGER(1), comment='状态1未完成2完成')
    task_type = Column(INTEGER(1), comment='任务类型1领取活跃金2提现3每日红包')
    create_time = Column(BIGINT(20), comment='创建时间')
    is_hide = Column(INTEGER(1), comment='是否隐藏1不隐藏2隐藏')
    money = Column(Float(10, True), comment='用户获得的奖励')
    cash_id = Column(INTEGER(10), comment='需要完成任务的提现记录id')


class LUserHippo(Base):
    __tablename__ = 'l_user_hippo'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(255), comment='用户id')
    category = Column(String(255), nullable=False, comment='新闻类目')
    create_time = Column(BIGINT(20), nullable=False)
    status = Column(INTEGER(2), nullable=False, comment='状态（1-成功 2-失败）')


class LUserReward(Base):
    __tablename__ = 'l_user_reward'
    __table_args__ = {'comment': 'Users reward log'}

    reward_id = Column(INTEGER(11), primary_key=True, nullable=False)
    user_id = Column(String(50), primary_key=True, nullable=False)
    reward_type = Column(INTEGER(11), nullable=False, server_default=text("'0'"),
                         comment='only support two kinds. one:user got a apprentice two:apprentice finished one task. three:finished one task')
    money = Column(DECIMAL(10, 2), comment='reward')
    reward_time = Column(BIGINT(20), comment='reward time')
    provide = Column(String(50), comment='reward source. who provided?(user id)')


class LUserSign(Base):
    __tablename__ = 'l_user_sign'
    __table_args__ = {'comment': 'Check-in information '}

    sign_id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(50), nullable=False)
    sign_time = Column(BIGINT(20), comment='Check-in time')
    score = Column(BIGINT(20), comment='Check-in get score')
    stick_times = Column(INTEGER(11), comment='Continuous check-in times')
    last_day = Column(BIGINT(20), comment='the last check-in time')
    sign_ip = Column(String(50), comment="market user's check-in used ip address")
    rule_id = Column(INTEGER(11))
    is_task = Column(INTEGER(1), comment='是否领取任务奖励1未领取2领取')
    task_coin = Column(BIGINT(20), comment='任务奖励金币数')


class LUserSignGame(Base):
    __tablename__ = 'l_user_sign_game'
    __table_args__ = {'comment': '用户签到游戏'}

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(32), nullable=False, index=True)
    signin_id = Column(INTEGER(11), nullable=False, comment='签到记录id')
    game_id = Column(INTEGER(11), nullable=False, comment='游戏id')
    reward = Column(INTEGER(20), comment='游戏中获得的金币数')
    create_time = Column(BIGINT(20), nullable=False)
    finish_time = Column(BIGINT(20))
    status = Column(INTEGER(2), nullable=False, comment='状态（1-待完成 2-已完成）')
    is_hide = Column(INTEGER(2), nullable=False, server_default=text("'1'"), comment='是否隐藏（1-不隐藏 2-隐藏）')


class LUserSignin(Base):
    __tablename__ = 'l_user_signin'
    __table_args__ = (
        Index('unique_user_id_sign_day', 'user_id', 'sign_day', unique=True),
        {'comment': '用户签到赚记录表'}
    )

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(32), nullable=False, index=True)
    sign_day = Column(INTEGER(2), nullable=False, comment='签到天数')
    game_count = Column(INTEGER(2), nullable=False, comment='游戏任务数')
    reward = Column(INTEGER(2), nullable=False, comment='奖励金额')
    update_time = Column(BIGINT(20), comment='修改时间')
    create_time = Column(BIGINT(20), nullable=False, index=True, comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（-1 未到时间 1-待补签 2-进行中 3-待领取 4-已领取）')


class LUserStatistic(Base):
    __tablename__ = 'l_user_statistic'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), index=True)
    one_game = Column(INTEGER(10), comment='注册当天完成游戏任务次数')
    two_game = Column(INTEGER(10), comment='注册前两天完成游戏任务次数')
    total_game = Column(INTEGER(10), comment='累计完成游戏任务次数')


class LUserTask(Base):
    __tablename__ = 'l_user_task'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(64), nullable=False, index=True, comment='用户id')
    task_id = Column(INTEGER(11), nullable=False, comment='任务id')
    create_time = Column(BIGINT(20), comment='完成时间')
    is_receive = Column(INTEGER(1), server_default=text("'1'"), comment='是否领取1未领取2领取 //只适用于新手任务')


class LUserTpTask(Base):
    __tablename__ = 'l_user_tp_task'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(64), nullable=False, comment='用户id')
    tp_task_id = Column(INTEGER(11), nullable=False, comment='任务id')
    update_time = Column(BIGINT(20), comment='修改时间')
    create_time = Column(BIGINT(20), nullable=False, comment='领取时间')
    expire_time = Column(BIGINT(20), comment='过期时间')
    remark = Column(String(255), comment='描述')
    status = Column(INTEGER(2), nullable=False, server_default=text("'1'"),
                    comment='状态（-2-已放弃 -1-已过期 1-待提交 2-已提交，待审核 3-审核通过 4-审核失败 5-已预约）')
    account_id = Column(INTEGER(11), nullable=False)
    flew_num = Column(String(64))


class LUserTpTaskSubmit(Base):
    __tablename__ = 'l_user_tp_task_submit'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(64), nullable=False, comment='用户id')
    l_tp_task_id = Column(INTEGER(11), nullable=False, comment='领取记录id')
    tp_task_id = Column(INTEGER(11), nullable=False, comment='任务id')
    submit_id = Column(INTEGER(11), nullable=False, comment='提交材料id')
    submit_name = Column(String(32), nullable=False, comment='提交材料名称')
    submit_value = Column(Text, nullable=False, comment='提交材料值')
    create_time = Column(BIGINT(20), nullable=False, comment='提交时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-正常 2-失效）')


class LUserVip(Base):
    __tablename__ = 'l_user_vip'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(32), nullable=False, index=True, comment='用户id')
    vip_id = Column(INTEGER(11), nullable=False)
    surplus_day = Column(INTEGER(11), nullable=False, comment='剩余天数')
    expire_time = Column(String(32), nullable=False, comment='过期时间')
    create_time = Column(BIGINT(20), nullable=False)
    status = Column(INTEGER(2), nullable=False, comment='状态（1-正常 2-过期）')


class LUserWelfare(Base):
    __tablename__ = 'l_user_welfare'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    types = Column(INTEGER(1), comment='类型：1新手福利')
    create_time = Column(BIGINT(20), comment='创建时间')


class MActivityInfo(Base):
    __tablename__ = 'm_activity_info'
    __table_args__ = {'comment': 'Activity information'}

    act_id = Column(INTEGER(11), primary_key=True)
    activity_name = Column(String(50), nullable=False, comment='Activity name')
    activity_type = Column(INTEGER(11), comment='type:0 weak up to check-in')
    start_time = Column(String(20), comment='start time in cycle')
    stop_time = Column(String(20), comment='end time in cycle')
    is_cycle = Column(INTEGER(11), comment='The Activity is a cycle?')
    periodic = Column(BIGINT(20), comment='Activity cycle')
    periodic_unit = Column(INTEGER(11),
                           comment='Periodic unit: 0:second 1:minumte 2:hour 3:day 4:month 5:season 6:year')
    is_disable = Column(INTEGER(11), comment='0:enable 1:disable')
    memo = Column(Text)
    begain_time = Column(BIGINT(20), comment='Activity start date')
    end_time = Column(BIGINT(20), comment='Activity end date')
    settlement_time = Column(String(20), comment="Settlement time(if it's in cycle, then settlement in every cycle)")
    base_allocation_amount = Column(DECIMAL(10, 2), server_default=text("'0.00'"), comment='瓜分金额初始值')


class MActivityLog(Base):
    __tablename__ = 'm_activity_log'
    __table_args__ = {'comment': 'Activity information log'}

    l_id = Column(INTEGER(11), primary_key=True)
    activity_id = Column(INTEGER(11), nullable=False)
    cycle_num = Column(String(50), comment='activity code(cycly number)')
    participants_num = Column(INTEGER(11), comment='The number of participants')
    participants_amount = Column(DECIMAL(10, 2), comment='The amount of participants')
    allocation_amount = Column(DECIMAL(10, 2), comment='Allocation amount')
    success_num = Column(INTEGER(11), comment='success people number')
    failure_num = Column(INTEGER(11), comment='failure people number')


class MChannel(Base):
    __tablename__ = 'm_channel'

    id = Column(INTEGER(11), primary_key=True)
    channel_name = Column(String(255), nullable=False)


class MChannelConfig(Base):
    __tablename__ = 'm_channel_config'

    id = Column(INTEGER(10), primary_key=True)
    channel_code = Column(String(32), comment='渠道标识')
    fission_id = Column(INTEGER(10), comment='渠道方案id')
    charge_mode = Column(INTEGER(1), comment='收费方式1平台收费2渠道收费')
    effective_object = Column(INTEGER(1), comment='生效对象1仅对渠道生效2对渠道用户和渠道次级用户生效')
    open_game = Column(String(64), comment='第三方游戏id,逗号分隔')
    create_time = Column(BIGINT(20), comment='创建时间')
    apply_task = Column(INTEGER(1), comment='是否需要完成高额赚任务1需要2不需要')
    game_28 = Column(INTEGER(1), comment='是否打开游戏28,1关闭2打开')
    pcdd_28 = Column(INTEGER(1), comment='是否打开蛋蛋28,1关闭2打开')
    jnd_28 = Column(INTEGER(1), comment='是否打开加拿大28,1关闭2打开')


class MChannelConfigUser(Base):
    __tablename__ = 'm_channel_config_user'

    id = Column(INTEGER(11), primary_key=True)
    config_id = Column(INTEGER(11), nullable=False, comment='渠道配置id')
    user_type = Column(INTEGER(2), nullable=False, comment='用户类型（1-普通用户 2-团队长）')
    sign_7 = Column(BIGINT(20), nullable=False)
    sign_15 = Column(BIGINT(20), nullable=False)
    vip_18 = Column(INTEGER(11), nullable=False)
    vip_48 = Column(INTEGER(11), nullable=False)
    vip_228 = Column(INTEGER(11), nullable=False)
    vip_1188 = Column(INTEGER(11), nullable=False)
    vip_1688 = Column(INTEGER(11), nullable=False)
    vip_1888 = Column(INTEGER(11), nullable=False)
    vip_3188 = Column(INTEGER(11), nullable=False)
    level_4 = Column(BIGINT(11), nullable=False)
    level_6 = Column(BIGINT(11), nullable=False)
    level_8 = Column(BIGINT(11), nullable=False)
    level_12 = Column(BIGINT(11), nullable=False)
    referrer_addition = Column(INTEGER(11), nullable=False)
    recommend_coin = Column(BIGINT(20), nullable=False, comment='推荐有效好友奖励金币数')
    create_time = Column(BIGINT(20), nullable=False)
    status = Column(INTEGER(2), nullable=False, comment='1-启用 2-停用')
    daren_coin = Column(INTEGER(11), comment='达人推荐好友奖励金币数')


class MChannelInfo(Base):
    __tablename__ = 'm_channel_info'

    id = Column(INTEGER(11), primary_key=True)
    channel_code = Column(String(32), nullable=False, unique=True, comment='渠道标识')
    channel_id = Column(INTEGER(11), nullable=False, comment='渠道名称')
    channel_position = Column(String(255), comment='渠道推广位置')
    channel_push_type = Column(INTEGER(2), comment='推广方式（1-banner+链接 2-文字+链接）')
    content = Column(String(255), comment='banner url/投放文字')
    download_url = Column(String(255))
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-停用）')
    open_ali = Column(INTEGER(1), comment='是否开启支付宝支付1开启2关闭')
    open_wx = Column(INTEGER(1), comment='是否开启微信支付1开启2关闭')
    wx_app_id = Column(String(32), comment='微信支付appId')
    mch_id = Column(String(32), comment='微信支付mchId')
    api_key = Column(Text, comment='微信支付apiKey')
    ali_app_id = Column(String(32), comment='支付宝appId')
    ali_private_key = Column(Text, comment='支付宝私钥')
    ali_public_key = Column(Text, comment='支付宝公钥')
    web_type = Column(INTEGER(11))


class MDarenReward(Base):
    __tablename__ = 'm_daren_reward'

    id = Column(INTEGER(10), primary_key=True)
    reward_type = Column(INTEGER(1), comment='奖励类型1首个任务2后续任务')
    reward_name = Column(String(64), comment='奖励名称')
    coin = Column(BIGINT(20), comment='奖励金币数')
    orders = Column(INTEGER(3), comment='排序')
    day_limit = Column(INTEGER(10), comment='天数限制')
    people_limit = Column(INTEGER(10), comment='人数限制')
    create_time = Column(BIGINT(20), comment='创建时间')
    state = Column(INTEGER(1), comment='状态1启用2禁用3已删除')


class MFightingAnswer(Base):
    __tablename__ = 'm_fighting_answer'
    __table_args__ = {'comment': 'Questions answer'}

    ans_id = Column(INTEGER(11), primary_key=True)
    question_id = Column(INTEGER(11), nullable=False)
    answer = Column(String(50))
    is_correct = Column(INTEGER(11))


class MFightingInfo(Base):
    __tablename__ = 'm_fighting_info'
    __table_args__ = {'comment': 'User fighting Information'}

    fight_id = Column(INTEGER(11), primary_key=True)
    fighting_type = Column(INTEGER(11))
    initiator = Column(String(64), comment='fighting initiator')
    defense = Column(String(64))
    initiator_coin = Column(INTEGER(10), comment='发起人支付金币数')
    defense_coin = Column(INTEGER(10), comment='参与人支付金币数')
    fighting_time = Column(BIGINT(20))
    winner = Column(String(50), comment='who won?')
    victory_score = Column(INTEGER(11))
    failure_score = Column(INTEGER(11))
    use_time = Column(INTEGER(11))
    entry_code = Column(String(20), comment='like password')
    state = Column(INTEGER(1), comment='1发起2好友已加入3进行中4结束5答题异常')
    is_receive = Column(INTEGER(1), server_default=text("'2'"), comment='是否领取1是2否')


class MFightingQuestion(Base):
    __tablename__ = 'm_fighting_question'
    __table_args__ = {'comment': 'Fighting questions'}

    q_id = Column(INTEGER(11), primary_key=True)
    question_type = Column(INTEGER(11), comment='use dictionary')
    question = Column(String(200))
    creator = Column(String(50), comment='who created')
    create_time = Column(BIGINT(20))
    score = Column(INTEGER(11), comment='if answer is correct, then you can get the score')
    question_state = Column(INTEGER(11), server_default=text("'0'"), comment='0:normal 1:submit 2:passed 3:reject')
    reject_reason = Column(String(255))
    count_time = Column(INTEGER(11), comment='count down time(s)')
    coin = Column(INTEGER(10), comment='出题者获得金币数')


class MFightingType(Base):
    __tablename__ = 'm_fighting_type'
    __table_args__ = {'comment': 'Fighting Type'}

    type_id = Column(INTEGER(11), primary_key=True)
    type_name = Column(String(50), nullable=False)
    create_time = Column(BIGINT(20))
    update_time = Column(BIGINT(20))
    is_disable = Column(INTEGER(11))
    reward_type = Column(INTEGER(11), comment='0:money 1:coin')
    reward_from = Column(INTEGER(11))
    reward_to = Column(INTEGER(11))
    fighting_rule = Column(String(200))
    question_num = Column(INTEGER(11), comment='The number of questions that need to be answered')


class MFissionScheme(Base):
    __tablename__ = 'm_fission_scheme'

    id = Column(INTEGER(10), primary_key=True)
    name = Column(String(32), comment='方案名称')
    team_price = Column(DECIMAL(5, 2), comment='团队长价格')
    renew_price = Column(DECIMAL(5, 2), comment='续费价格')
    one_commission = Column(Float(5, True), comment='一级分佣')
    two_commission = Column(Float(5, True), comment='二级分佣')
    partner_commission = Column(Float(5, True), comment='合伙人分佣')
    effective_day = Column(INTEGER(10), comment='团队长有效天数')
    ordinary_exchange = Column(Float(5, True), comment='普通用户起提金额')
    group_exchange = Column(Float(5, True), comment='团队长起提金额')
    give_money = Column(Float(5, True), comment='每日赠送人民币数')
    give_coin = Column(BIGINT(20), comment='每天赠送金币数')
    give_pig = Column(BIGINT(20), comment='每天赠送金猪数')
    give_day = Column(INTEGER(3), comment='赠送天数')
    scheme_img = Column(String(1024), comment='方案图')
    ordinary_reward_img = Column(String(1024), comment='普通用户奖励图')
    team_reward_img = Column(String(1024), comment='团队长奖励图')
    daren_reward_img = Column(String(1024), comment='达人奖励图')
    invite_img = Column(String(1024), comment='邀请流程图')
    remarks = Column(String(200), comment='备注')
    creater_time = Column(BIGINT(20), comment='创建时间')


class MLotteryGood(Base):
    __tablename__ = 'm_lottery_goods'
    __table_args__ = {'comment': '奖品表'}

    id = Column(INTEGER(11), primary_key=True)
    type_id = Column(INTEGER(11), nullable=False, comment='抽奖类型id')
    abbreviation = Column(String(64), comment='奖品简称')
    goods_name = Column(String(255), nullable=False, comment='奖品名称')
    rate = Column(INTEGER(11), nullable=False, comment='中奖概率')
    image_url = Column(String(255), nullable=False, comment='奖品图片地址')
    remark = Column(String(255), comment='奖品描述')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-停用 3已删除）')
    price = Column(DECIMAL(10, 2), comment='奖品价格')
    pig_coin = Column(BIGINT(20), server_default=text("'0'"), comment='兑换奖品所需金猪')
    goods_number = Column(INTEGER(10), comment='奖品数量')
    goods_consume_number = Column(INTEGER(10), comment='奖品使用数量')
    orders = Column(INTEGER(5), comment='排序')
    goods_type = Column(INTEGER(1), server_default=text("'1'"), comment='奖品类型1虚拟2实物')
    carousel_img = Column(String(512), comment='奖品轮播图,多张使用逗号分隔')
    info_img = Column(String(512), comment='奖品详情图,多张使用逗号分隔')


class MLotteryOrder(Base):
    __tablename__ = 'm_lottery_order'
    __table_args__ = {'comment': '中奖记录表'}

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(32), nullable=False, index=True, comment='中奖用户id')
    type_id = Column(INTEGER(11), nullable=False, comment='中奖类型id')
    goods_id = Column(INTEGER(11), nullable=False, comment='中奖奖品id')
    address_id = Column(INTEGER(11), comment='寄送地址id')
    account_id = Column(INTEGER(10), comment='账户id')
    expend_pig_coin = Column(BIGINT(20), comment='抽奖消耗金额')
    price = Column(DECIMAL(10, 2), comment='奖品价格')
    express_company = Column(String(64), comment='快递公司/卡号')
    express_numbers = Column(String(64), comment='快递单号/卡密')
    remarks = Column(String(400), comment='备注')
    create_time = Column(BIGINT(20), comment='中奖时间')
    update_time = Column(BIGINT(20), comment='修改时间')
    status = Column(INTEGER(2), comment='中奖状态1.待审核2.拒绝3.待发货4.已发货')
    operator_mobile = Column(String(11), comment='操作人电话')
    locking_mobile = Column(String(11), comment='锁定人电话')
    is_locking = Column(INTEGER(1), server_default=text("'2'"), comment='是否锁定1是2否')


class MLotteryType(Base):
    __tablename__ = 'm_lottery_type'
    __table_args__ = {'comment': '抽奖类型表'}

    id = Column(INTEGER(11), primary_key=True)
    type_name = Column(String(255), nullable=False, comment='类型名称')
    day_num = Column(INTEGER(10), comment='每天发放数量')
    times_oneday = Column(INTEGER(11), comment='用户每天次数限制')
    expend_pig_coin = Column(BIGINT(20), comment='每次所需金猪')
    remark = Column(Text, comment='类型描述')
    apply_crowd = Column(INTEGER(1), comment='1全部')
    lottery_sort = Column(INTEGER(1), comment='抽奖分类 1兑换2抽奖')
    create_time = Column(BIGINT(20), nullable=False)
    status = Column(INTEGER(2), comment='类型状态（1-启用 2-停用）')


class MPassbook(Base):
    __tablename__ = 'm_passbook'

    id = Column(INTEGER(11), primary_key=True)
    passbook_name = Column(String(32), nullable=False, comment='优惠券名称')
    passbook_type = Column(INTEGER(2), nullable=False, comment='卡券类型（1-翻倍券 2-折扣券 3-加成券)')
    use_day = Column(INTEGER(2), nullable=False, comment='有效天数')
    passbook_value = Column(INTEGER(11), nullable=False, comment='折扣或者奖励倍数')
    reg_send = Column(INTEGER(11), nullable=False, comment='是否注册发放（1-否 2-是）')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    remark = Column(String(255), comment='描述')


class MRankConfig(Base):
    __tablename__ = 'm_rank_config'
    __table_args__ = {'comment': '排行榜配置'}

    id = Column(INTEGER(11), primary_key=True)
    rank_name = Column(String(255), nullable=False, comment='排行名称')
    rank_type = Column(INTEGER(2), nullable=False, comment='排行榜类型（1-金猪排行榜 2-金币排行榜 3-好友排行榜）')
    data_logic = Column(INTEGER(2), nullable=False, comment='数据筛选逻辑（1-月榜 2-总榜）')
    range_min = Column(DECIMAL(10, 2), nullable=False, comment='随机范围-最小值')
    rang_max = Column(DECIMAL(10, 2), nullable=False, comment='随机范围-最大值')
    up_num = Column(INTEGER(11), nullable=False, server_default=text("'0'"), comment='上榜人数')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    update_time = Column(BIGINT(20), nullable=False, comment='修改时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-停用）')


class MRankConfigReward(Base):
    __tablename__ = 'm_rank_config_reward'
    __table_args__ = {'comment': '排行奖励表'}

    id = Column(INTEGER(11), primary_key=True)
    config_id = Column(INTEGER(11), nullable=False, comment='排行配置id')
    reward_type = Column(INTEGER(2), nullable=False, comment='奖励类型（1-金币 2-金猪）')
    reward_amount = Column(BIGINT(20), nullable=False, comment='奖励金额')
    reward_order = Column(INTEGER(2), nullable=False, comment='奖励排行')
    reward_remark = Column(String(255), nullable=False, comment='奖励排行描述')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-停用）')


class MRankDarenConfig(Base):
    __tablename__ = 'm_rank_daren_config'

    id = Column(INTEGER(11), primary_key=True)
    daren_level = Column(INTEGER(2), nullable=False, comment='奖励等级')
    need_num = Column(INTEGER(11), nullable=False, comment='人数要求')
    reward = Column(BIGINT(20), nullable=False, comment='奖池金额')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')


class MSignRule(Base):
    __tablename__ = 'm_sign_rule'
    __table_args__ = {'comment': 'Check-in rule'}

    rule_id = Column(INTEGER(11), primary_key=True)
    rule_name = Column(String(50), nullable=False)
    stick_time = Column(INTEGER(11), comment='Continuous check-in time.Do not allow broken')
    score = Column(BIGINT(20))
    has_other_reward = Column(INTEGER(11), comment="has other kinds of reward? if setting Zero, it's none.")
    reward_type = Column(INTEGER(11), comment='which kinds of reward')
    other_reward = Column(String(50), comment="extend field. can use to store other kinds of reward's identity")


class MTaskInfo(Base):
    __tablename__ = 'm_task_info'

    id = Column(INTEGER(11), primary_key=True)
    task_name = Column(String(255), nullable=False, comment='任务名称')
    task_type = Column(INTEGER(255), nullable=False, comment='任务类型（对应m_task_type）')
    reward = Column(BIGINT(20), nullable=False, comment='奖励数量')
    reward_unit = Column(INTEGER(2), nullable=False, comment='奖励数量单位（1-金币 2-金猪 3-金币百分比 4-金猪百分比）')
    remark = Column(String(255), nullable=False, comment='描述')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-禁用）')
    task_img = Column(String(64), comment='未完成任务图片')
    icon_type = Column(INTEGER(1), comment='小图标类型1无2金猪3金币')
    remarks = Column(String(128), comment='备注')
    sort = Column(INTEGER(5), comment='排序')
    fulfil_task_img = Column(String(64), comment='已完成任务显示图标')


class MTaskJob(Base):
    __tablename__ = 'm_task_job'
    __table_args__ = (
        Index('pk_index', 'jobName', 'jobGroup', unique=True),
    )

    id = Column(BIGINT(20), primary_key=True)
    jobName = Column(String(100))
    jobGroup = Column(String(100))
    triggerName = Column(String(100))
    triggerGroupName = Column(String(100))
    processClass = Column(String(100))
    cronExpression = Column(String(100))
    status = Column(BIGINT(20))
    createDate = Column(BIGINT(20), nullable=False)
    modifiedDate = Column(BIGINT(20), nullable=False)
    remark = Column(String(255))


class MTaskType(Base):
    __tablename__ = 'm_task_type'

    id = Column(INTEGER(11), primary_key=True)
    type_name = Column(String(32), nullable=False, comment='任务类型名称')
    short_name = Column(String(32), nullable=False, comment='简称')


class MUserAddres(Base):
    __tablename__ = 'm_user_address'
    __table_args__ = {'comment': 'Users Address'}

    address_id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(50), nullable=False)
    receiver = Column(String(50), comment='receiver name')
    mobile = Column(String(11), comment='receivers phone number')
    area_id = Column(BIGINT(20), comment='delivery targert')
    detail_address = Column(String(255), comment='详细地址')
    is_default = Column(INTEGER(11), comment='1默认地址2非默认地址')
    create_time = Column(BIGINT(20))
    update_time = Column(BIGINT(20))
    is_disabled = Column(INTEGER(11), comment='1有效2失效')


class MUserApprentice(Base):
    __tablename__ = 'm_user_apprentice'
    __table_args__ = {'comment': 'Apprentice Information'}

    apprentice_id = Column(INTEGER(11), primary_key=True)
    referrer_id = Column(String(50), nullable=False, comment='referrer user')
    user_id = Column(String(50), comment='apprentice')
    contribution = Column(BIGINT(20), comment='total of his contribution')
    reward_status = Column(INTEGER(2), server_default=text("'1'"), comment='是否获得奖励（1-待完成 2-已完成）')
    update_time = Column(BIGINT(20), comment='the last of contribution time')
    create_time = Column(BIGINT(20))
    apprentice_type = Column(INTEGER(2), server_default=text("'1'"), comment='徒弟类型（1-正常徒弟 2-达人徒弟）')


class MUserGyro(Base):
    __tablename__ = 'm_user_gyro'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64))
    gyro_x = Column(Float(10, True), comment='陀螺仪x轴')
    gyro_y = Column(Float(10, True), comment='陀螺仪y轴')
    gyro_z = Column(Float(10, True), comment='陀螺仪z轴')
    page_type = Column(INTEGER(1), comment='页面类型：1主页，2游戏列表，3游戏详情')
    update_time = Column(BIGINT(20), comment='修改时间')
    number = Column(INTEGER(1), comment='存储次数')


class MUserInfo(Base):
    __tablename__ = 'm_user_info'
    __table_args__ = {'comment': 'User Information'}

    user_id = Column(String(50), nullable=False, unique=True)
    user_name = Column(String(50), comment='users real name')
    sex = Column(INTEGER(11), comment='sex/sexual')
    birthday = Column(String(32), comment='my birthday(use long)')
    mobile = Column(String(50), unique=True, comment='users phone number,maximum length is 11')
    alias_name = Column(String(50), comment='users alias name')
    identity = Column(String(50), comment='when necessary, user can use identity to loging')
    social_digital_num = Column(String(50), comment='users social security digital number')
    digital_num_type = Column(INTEGER(11), server_default=text("'1'"),
                              comment='which kinds of users social security number')
    profile = Column(String(200), comment='uses profile setting(store the url)')
    balance = Column(DECIMAL(10, 2), comment='users balance')
    jade_cabbage = Column(DECIMAL(10, 2), comment='other kinds of balance')
    coin = Column(BIGINT(20), comment='users coin(none forbidden)')
    reward = Column(DECIMAL(10, 2), comment='total of my reward(unit:￥)')
    apprentice = Column(INTEGER(11), comment='total of my apprentice')
    qr_code = Column(String(200), comment='my special code')
    level = Column(String(50), comment='my level name')
    level_value = Column(BIGINT(20), comment='my levels number')
    password = Column(String(100), comment='security words(MD5)')
    create_time = Column(BIGINT(20), comment='register time')
    update_time = Column(BIGINT(20), comment='the last update time')
    referrer = Column(String(50), comment='who recommended?')
    recommended_time = Column(BIGINT(20), comment='Recommended time')
    imei = Column(String(255), comment='设备唯一标识')
    equipment_type = Column(INTEGER(2), comment='登陆设备类型（1-安卓 2-ios）')
    pig_coin = Column(BIGINT(255), server_default=text("'0'"), comment='金猪币')
    registration_id = Column(String(32), comment='用户极光唯一标识')
    token = Column(String(64), comment='用户当前token')
    ali_num = Column(String(32), comment='支付宝账号')
    open_id = Column(String(64), comment='微信openId')
    account_id = Column(INTEGER(64), primary_key=True, comment='账户id')
    status = Column(INTEGER(2), server_default=text("'1'"), comment='用户状态（1-正常 2-拉黑）')
    reg_imei = Column(String(255))
    pay_password = Column(String(64), comment='支付密码')
    channel_code = Column(String(32), index=True)
    role_type = Column(INTEGER(11), server_default=text("'1'"), comment='角色类型（1-小猪猪 2-团队长 3-超级合伙人 4-邀请达人）')
    surplus_time = Column(INTEGER(11))
    parent_channel_code = Column(String(255), comment='师傅的渠道标识')
    remark = Column(String(255), comment='备注')
    xq_end_time = Column(BIGINT(20))
    wx_num = Column(String(64), comment='用户在微信的真实姓名')
    daren_time = Column(BIGINT(20), comment='设置达人时间')
    qq_num = Column(String(15), comment='用户qq号')
    open_activity = Column(INTEGER(2), server_default=text("'1'"), comment='是否展示活跃度')
    high_role = Column(INTEGER(4))


class MUserOpinion(Base):
    __tablename__ = 'm_user_opinion'

    id = Column(INTEGER(10), primary_key=True)
    account_id = Column(INTEGER(10), comment='用户id')
    vip_name = Column(String(32), comment='会员等级')
    experience = Column(BIGINT(20), comment='用户成长值')
    opinion_type = Column(INTEGER(1), comment='意见类型1会员相关2积分提现3信息错误4 友好意见5其他')
    opinion_content = Column(String(200), comment='意见内容')
    content_img = Column(String(300), comment='图片 逗号分隔')
    email = Column(String(32), comment='邮箱')
    state = Column(INTEGER(1), comment='1待处理2已处理3不予处理')
    remarks = Column(String(200), comment='备注')
    creater_time = Column(BIGINT(20), comment='创建时间')


class MUserVipReferrerLog(Base):
    __tablename__ = 'm_user_vip_referrer_log'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    referrer_id = Column(String(64), comment='师傅id')
    rank = Column(INTEGER(2), comment='领取累充奖励级别')
    creator_time = Column(BIGINT(20), comment='创建时间')


class MVipInfo(Base):
    __tablename__ = 'm_vip_info'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(32), nullable=False, comment='VIP卡名称')
    logo = Column(String(255))
    first_reward = Column(BIGINT(20), nullable=False, comment='首充奖励')
    first_reward_unit = Column(INTEGER(255), nullable=False, comment='首充奖励单位（1-金币 2-金猪）')
    continue_reward = Column(BIGINT(20), nullable=False, server_default=text("'0'"), comment='续充奖励')
    continue_reward_unit = Column(INTEGER(255), nullable=False, comment='续充奖励单位（1-金币 2-金猪）')
    game_addition = Column(INTEGER(255), nullable=False, comment='游戏加成（%）')
    use_day = Column(INTEGER(255), nullable=False, comment='有效期（单位：天）')
    coin_to_pig_addition = Column(DECIMAL(10, 2), nullable=False, comment='金币兑换金猪加成')
    everyday_active_pig = Column(BIGINT(20), nullable=False, comment='每日活跃奖励金猪')
    everyday_active_coin = Column(BIGINT(20), nullable=False, comment='每日活跃奖励金币')
    onetime_limit = Column(BIGINT(20), nullable=False, comment='单笔限额（金猪）')
    audit_first = Column(INTEGER(2), nullable=False, comment='兑换是否优先审核（1-是 2-否）')
    send_sms = Column(INTEGER(2), nullable=False, comment='兑换是否短信提醒（1-是 2-否）')
    everyday_relief_pig = Column(BIGINT(20), nullable=False, comment='每日救济金猪')
    everyday_relief_pig_times = Column(INTEGER(11), nullable=False, server_default=text("'1'"), comment='救济金猪每日领取次数')
    one_withdrawals = Column(INTEGER(2), nullable=False, comment='是否一元提现（1-是 2-否）')
    price = Column(DECIMAL(10, 2), nullable=False, comment='价格')
    create_time = Column(BIGINT(20), nullable=False)
    status = Column(INTEGER(2), nullable=False, server_default=text("'1'"), comment='是否可用（1-是 2-否）')
    order_id = Column(INTEGER(11), nullable=False, comment='等级排序')
    is_task = Column(INTEGER(1), comment='是否需要完成任务1是2否')
    task_num = Column(INTEGER(1), server_default=text("'1'"), comment='任务个数')
    is_renew = Column(INTEGER(1), comment='是否可以续费1是2否')
    background_img = Column(String(64), comment='背景图')
    overdue_img = Column(String(64), comment='过期背景图')
    vip_type = Column(INTEGER(2), comment='1.普通vip 2.中青赚点')
    cash_money = Column(INTEGER(10), comment='可提现金额 单位元，-1无限制')
    reward_day = Column(INTEGER(10), comment='奖励天数 -1无限制')
    return_vip = Column(INTEGER(10), comment='退款vipId,-1无退款')
    high_vip = Column(INTEGER(10), comment='未知字段')


class MWeakupCheckin(Base):
    __tablename__ = 'm_weakup_checkin'
    __table_args__ = {'comment': 'Morning check-in logger'}

    chk_id = Column(INTEGER(11), primary_key=True)
    log_id = Column(INTEGER(11), nullable=False)
    checkin_user = Column(String(50), nullable=False)
    checkin_time = Column(BIGINT(20))
    investment = Column(DECIMAL(10, 2), nullable=False, comment='investment amount')
    checkin_state = Column(INTEGER(11), server_default=text("'0'"),
                           comment='check-in state 0:sign up 1:success 2:failure')
    reward_amount = Column(DECIMAL(10, 2), server_default=text("'0.00'"))


class PAdmin(Base):
    __tablename__ = 'p_admin'

    admin_id = Column(String(255), primary_key=True)
    realname = Column(String(255), nullable=False)
    mobile = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    image_url = Column(String(255))
    role_id = Column(INTEGER(11), nullable=False, comment='角色id')
    create_time = Column(BIGINT(20), nullable=False)
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-禁用）')
    channel_code = Column(String(32), comment='渠道标识')
    user_relation = Column(INTEGER(1), server_default=text("'1'"), comment='用户关系1全部2直属用户3非直属用户')


class PApplicationMarket(Base):
    __tablename__ = 'p_application_market'

    id = Column(INTEGER(10), primary_key=True)
    market_name = Column(String(32), comment='市场名')
    package_name = Column(String(64), comment='包名')
    edition_num = Column(String(64), comment='版本号')
    state = Column(INTEGER(1), comment='1下架2审核中3正常')


class PArea(Base):
    __tablename__ = 'p_area'
    __table_args__ = {'comment': '地区信息表'}

    id = Column(INTEGER(6), primary_key=True, comment='ID，即行政区划代码')
    name = Column(String(32), nullable=False, comment='名称，如：浙江省、杭州市、西湖区')
    short_name = Column(String(32), comment='简称，如：浙江、杭州、西湖')
    full_name = Column(String(64), comment='全称，即全路径名称，如：中国/浙江省/杭州市')
    short_spell = Column(String(32), comment='简拼，如：杭州（hz）')
    spell = Column(String(64), comment='全拼，如：杭州（hangzhou）')
    area_code = Column(String(12), comment='电话区号，如：0571')
    post_code = Column(String(12), comment='邮政编码，如：320000')
    parent_id = Column(INTEGER(6), index=True, comment='父级ID，即省级ID')
    level = Column(INTEGER(11), nullable=False, comment='行政区划级别：0.国家 1.省份 2.城市 3.区县')
    is_direct = Column(TINYINT(1), nullable=False, comment='是否直辖：0.非直辖 1.直辖')


class PBanner(Base):
    __tablename__ = 'p_banner'

    banner_id = Column(INTEGER(11), primary_key=True)
    title = Column(String(32))
    position = Column(INTEGER(2), comment='1-宝猪抽奖2首页底部3-游戏列表头部 4金猪乐园轮播')
    image_url = Column(String(128))
    link_url = Column(String(512))
    start_time = Column(BIGINT(20))
    end_time = Column(BIGINT(20))
    create_time = Column(BIGINT(20))
    status = Column(INTEGER(11), comment='1启用2停用')


class PCashPriceConfig(Base):
    __tablename__ = 'p_cash_price_config'

    id = Column(INTEGER(10), primary_key=True)
    price = Column(INTEGER(10), comment='提现价格')
    orders = Column(INTEGER(10), comment='排序')
    is_task = Column(INTEGER(1), server_default=text("'2'"), comment='是否需要完成任务1是2否')
    web_type = Column(INTEGER(11), comment='未知字段,支付宝报错添加')
    priceDouble = Column(Float(11, True), comment='未知字段')


class PDataStatistic(Base):
    __tablename__ = 'p_data_statistics'

    id = Column(INTEGER(10), primary_key=True)
    channel_code = Column(String(32), comment='渠道标识')
    total = Column(INTEGER(10), comment='总用户数')
    seven_day_add = Column(INTEGER(10), comment='7天内新增用户')
    same_day_add = Column(INTEGER(10), comment='当天新增用户数')
    sign = Column(INTEGER(10), comment='签到用户数')
    bind_ali = Column(INTEGER(10), comment='绑定支付宝用户数')
    cash = Column(INTEGER(10), comment='提现用户数')
    game_28 = Column(INTEGER(10), comment='参与28游戏用户数')
    creator_time = Column(String(32), comment='创建时间')


class PDictionary(Base):
    __tablename__ = 'p_dictionary'

    id = Column(INTEGER(11), primary_key=True)
    dic_name = Column(String(255), nullable=False, comment='字典名称')
    dic_remark = Column(String(255), nullable=False, comment='字典描述')
    dic_value = Column(String(255), nullable=False, comment='字典值')
    modify_user = Column(String(255), nullable=False, comment='最后一次修改人')
    modify_time = Column(BIGINT(20), nullable=False, comment='最后一次修改时间')
    value_type = Column(INTEGER(1), comment='1文本2图片')
    status = Column(INTEGER(2), nullable=False, server_default=text("'1'"), comment='状态（1-启用 2-停用 3-删除）')


class PIpBlacklist(Base):
    __tablename__ = 'p_ip_blacklist'
    __table_args__ = {'comment': 'ip黑名单'}

    id = Column(INTEGER(11), primary_key=True, nullable=False)
    ip = Column(String(255), primary_key=True, nullable=False)
    create_time = Column(BIGINT(20), nullable=False)


class PLevel(Base):
    __tablename__ = 'p_level'

    id = Column(INTEGER(11), primary_key=True)
    level = Column(String(255))
    experience = Column(BIGINT(20))
    img_url = Column(String(255))
    addition = Column(INTEGER(2), comment='金猪加成比例')
    order_id = Column(INTEGER(2))


class PMenu(Base):
    __tablename__ = 'p_menu'

    id = Column(INTEGER(11), primary_key=True)
    icon = Column(String(255), comment='小图标')
    menu_name = Column(String(32), nullable=False, comment='菜单名称')
    menu_url = Column(String(32), nullable=False, comment='菜单访问地址')
    file_name = Column(String(32), nullable=False, comment='文件名')
    parent_id = Column(INTEGER(11), nullable=False, server_default=text("'0'"), comment='父级id（默认0）')
    order_id = Column(INTEGER(11), nullable=False, comment='排序')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    status = Column(INTEGER(11), nullable=False, comment='状态（1-启用 2-停用）')


class PMenuBtn(Base):
    __tablename__ = 'p_menu_btn'

    id = Column(INTEGER(11), primary_key=True)
    menu_id = Column(INTEGER(11))
    btn_name = Column(String(32))
    btn_code = Column(String(32), comment='按钮代码')


class PPayLog(Base):
    __tablename__ = 'p_pay_log'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(32), index=True, comment='用户id')
    out_trade_no = Column(String(64), comment='订单号')
    price = Column(DECIMAL(10, 2), comment='支付金额')
    balance = Column(DECIMAL(10, 2), comment='余额抵扣')
    actual_price = Column(DECIMAL(10, 2), comment='实际支付价格')
    descripte = Column(String(32), comment='订单描述')
    pay_mode = Column(String(1), comment='支付方式1支付宝2微信3余额支付')
    pay_type = Column(String(1), comment='支付类型1app 2小程序')
    pay_ip = Column(String(32), comment='ip地址')
    coupon_id = Column(INTEGER(10), comment='优惠券id 未使用优惠券填0')
    open_id = Column(String(64), comment='微信支付的openId')
    state = Column(INTEGER(1), comment='支付状态1待支付2已支付3已取消')
    creator_time = Column(BIGINT(20), comment='创建时间')
    pay_time = Column(BIGINT(20), comment='支付时间')
    cancel_time = Column(BIGINT(20), comment='取消时间')
    is_delete = Column(INTEGER(1), server_default=text("'1'"), comment='是否删除1存在2删除')
    pay_purpose = Column(INTEGER(2), comment='支付用途1购买会员2购买团队长3团队长续期')
    vip_id = Column(INTEGER(10), comment='vipId')
    is_balance = Column(INTEGER(1), comment='是否使用余额1不使用2使用')
    web_state = Column(INTEGER(1), server_default=text("'0'"), comment='前端支付结果1为已支付')
    channel_code = Column(String(32), comment='渠道标识')


class PRole(Base):
    __tablename__ = 'p_role'

    id = Column(INTEGER(11), primary_key=True)
    role_name = Column(String(32), nullable=False, comment='角色名称')
    remark = Column(String(32), comment='描述')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-禁用）')


class PRoleMenuBtn(Base):
    __tablename__ = 'p_role_menu_btn'

    id = Column(INTEGER(11), primary_key=True)
    role_id = Column(INTEGER(11), nullable=False)
    type = Column(INTEGER(255), comment='类型（1-menu 2-button）')
    ref_id = Column(INTEGER(11), comment='关联id（1-menuid 2-btnid）')


class PVersion(Base):
    __tablename__ = 'p_version'

    id = Column(INTEGER(11), primary_key=True)
    channel_code = Column(String(32), nullable=False, comment='渠道名称')
    version_no = Column(String(32), comment='安卓版本号')
    ios_version_no = Column(String(32), comment='ios版本号')
    open_28 = Column(INTEGER(2), nullable=False, comment='是否开起28')
    need_update = Column(INTEGER(11), comment='是否需要更新')
    update_url = Column(String(300), comment='安卓下载地址')
    ios_update_url = Column(String(300), comment='ios下载地址')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-停用）')
    open_novice_task = Column(INTEGER(1), comment='是否开启新手引导1开启2不开启')
    update_remark = Column(Text, comment='更新描述')
    channel_update = Column(INTEGER(1), comment='是否独立更新 1是2否')


class PWhitelist(Base):
    __tablename__ = 'p_whitelist'
    __table_args__ = {'comment': '白名单'}

    id = Column(INTEGER(11), primary_key=True)
    content_type = Column(INTEGER(2), nullable=False, comment='白名单内容类型（1-电话 2-IP）')
    content = Column(String(255), nullable=False, comment='白名单内容')
    create_time = Column(BIGINT(20), nullable=False)


class RsPassbookTask(Base):
    __tablename__ = 'rs_passbook_task'

    id = Column(INTEGER(11), primary_key=True)
    passbook_id = Column(INTEGER(11), nullable=False)
    task_type_id = Column(INTEGER(11), nullable=False)


class RsUserPassbook(Base):
    __tablename__ = 'rs_user_passbook'

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(String(32), nullable=False, comment='用户id')
    passbook_id = Column(INTEGER(11), nullable=False, comment='优惠券id')
    expiration_day = Column(INTEGER(11), nullable=False, comment='剩余天数')
    expiration_time = Column(String(32), nullable=False, comment='过期时间')
    status = Column(INTEGER(2), nullable=False, server_default=text("'1'"), comment='是否使用（1-未使用 2-已使用 3-已过期）')


class SContentInfo(Base):
    __tablename__ = 's_content_info'
    __table_args__ = {'comment': '定时任务的配置信息'}

    id = Column(INTEGER(11), primary_key=True, comment='任务id 取值范围(1-1000)')
    message_title = Column(String(20), nullable=False, comment='消息标题')
    message_model = Column(String(255), nullable=False, comment='消息模板')
    param_caption = Column(String(255), comment='参数说明')
    send_mode = Column(INTEGER(1), nullable=False, comment='1,手机号 2邮箱 3.公众号')
    is_timing = Column(INTEGER(1), nullable=False, comment='是否定时发送 1否2是')
    timing_time = Column(DateTime, comment='定时发送发送时间')
    is_active = Column(INTEGER(1), nullable=False, comment='是否启用(0:未启用 1:启用 默认1)')
    create_time = Column(DateTime, nullable=False, comment='创建时间')
    update_time = Column(DateTime, comment='更新时间')


class SLogAppAuthor(Base):
    __tablename__ = 's_log_app_author'
    __table_args__ = {'comment': '应用授权记录'}

    id = Column(String(50), primary_key=True)
    api_name = Column(String(50), comment='API名称')
    app_key = Column(String(50), nullable=False)
    session = Column(String(50), nullable=False, comment='授权令处于')
    timestamp = Column(BIGINT(20), comment='授权时效')
    format = Column(String(50), server_default=text("'json'"), comment='响应格式。默认为xml格式，可选值：xml，json。')
    v = Column(String(50), nullable=False, comment='API协议版本')
    signature = Column(String(50), comment='签名的摘要算法，可选值为：hmac，md5。')
    sign = Column(String(100), nullable=False, comment='API输入参数签名结果')
    open_account_id = Column(String(50), comment='用户开放ID')


class SPlatApp(Base):
    __tablename__ = 's_plat_app'
    __table_args__ = {'comment': '第三方应用'}

    app_key = Column(String(50), primary_key=True, comment='应用程序ID')
    app_name = Column(String(50), nullable=False, comment='应用程序名称')
    app_security = Column(String(50), nullable=False, comment='应用程序加密字符串')
    redirect_url = Column(String(255), comment='重定向网址')
    insert_time = Column(BIGINT(20), comment='创建时间')
    owner_user = Column(String(50), comment='应用所有者')
    app_version = Column(String(50), nullable=False, comment='应用版本')
    is_enable = Column(INTEGER(11), server_default=text("'1'"), comment='是否有效')
    certificate_pub = Column(String(255), comment='公钥路径')
    certificate_pri = Column(String(50), comment='私钥路径')
    is_mobile = Column(INTEGER(11), server_default=text("'0'"), comment='是否为手机0：否，1是')


class SSmsBlack(Base):
    __tablename__ = 's_sms_black'
    __table_args__ = {'comment': '用户黑名单表'}

    id = Column(INTEGER(11), primary_key=True, comment='id')
    account_num = Column(String(32), nullable=False, comment='手机号,ip地址,邮箱')
    create_time = Column(DateTime, nullable=False, comment='创建时间')
    limit_time = Column(INTEGER(1), nullable=False, comment='限制时长：0-永久')
    black_count = Column(INTEGER(8), nullable=False, server_default=text("'1'"), comment='拉黑次数')
    type = Column(String(1), nullable=False, server_default=text("'0'"), comment='锁定状态：0-拉黑，1-解除')


class SSmsLog(Base):
    __tablename__ = 's_sms_log'

    id = Column(INTEGER(10), primary_key=True, comment='验证码日志id')
    account_num = Column(String(64), comment='账号')
    code = Column(String(16), comment='验证码')
    ip = Column(String(32), comment='请求id')
    rule_num = Column(String(10), comment='发送规则')
    send_mode = Column(INTEGER(1), comment='1.手机号2.邮箱')
    create_time = Column(DateTime, comment='发送时间')
    remark = Column(String(255), server_default=text("'1'"))
    status = Column(INTEGER(2), nullable=False, server_default=text("'3'"),
                    comment='发送状态（1-待确认 2-已确认，发送失败 已切换创蓝 3-已确认，发送成功）')
    sms_message_id = Column(String(64))
    is_valid = Column(INTEGER(1), comment='是否有效1有2没有')


class SSmsParamConf(Base):
    __tablename__ = 's_sms_param_conf'

    id = Column(INTEGER(5), primary_key=True, comment='主键')
    name = Column(String(20), comment='配置项名称')
    max_value = Column(INTEGER(5), comment='限制范围最大值')
    memo = Column(String(100), comment='备注')


class SSmsSendRule(Base):
    __tablename__ = 's_sms_send_rule'
    __table_args__ = {'comment': '短信发送规则表'}

    id = Column(INTEGER(11), primary_key=True, comment='规则ID')
    scene = Column(String(3), nullable=False, comment='来源：1-pc,2-app')
    send_mode = Column(String(3), comment='发送方式：1-手机号,2邮箱')
    rule_num = Column(String(8), nullable=False, comment='短型类型编号(取值范围10000-20000)')
    type = Column(String(32), nullable=False, comment='短信类型')
    limit_send_number = Column(INTEGER(2), nullable=False, comment='限制条数')


t_subject = Table(
    'subject', metadata,
    Column('sn', String(255)),
    Column('title', String(255)),
    Column('type', String(255)),
    Column('right', String(255)),
    Column('e1', String(255)),
    Column('e2', String(255)),
    Column('e3', String(255)),
    Column('times', String(255)),
    Column('score', INTEGER(255)),
    Column('remark', String(255))
)

t_tp_bz_callback = Table(
    'tp_bz_callback', metadata,
    Column('adid', INTEGER(11), comment='广告ID'),
    Column('adname', String(255), comment='广告名称'),
    Column('appid', String(255), comment='开发者ID'),
    Column('ordernum', String(255), comment='订单编号'),
    Column('dlevel', String(255), comment='奖励级别'),
    Column('pagename', String(255), comment='用户体验游戏的包名'),
    Column('deviceid', String(255), comment='手机设备号 imei 或 idfa'),
    Column('simid', String(255), comment='手机sim卡id'),
    Column('appsign', String(255), comment='开发者用户编号（用户id）'),
    Column('merid', String(255), comment='用户体验游戏注册的账号id'),
    Column('event', String(255), comment='奖励说明—在开发者自己的APP中需显示给用户看，以便用户了解自己获得的奖励'),
    Column('price', String(255), comment='于开发者结算单价、保留2位小数 【人民币单位】'),
    Column('money', String(255), comment='开发者需奖励给用户金额 【人民币单位】'),
    Column('itime', String(255), comment='用户获得奖励时间 时间字符串 如：2018/01/24 12:13:24'),
    Column('keycode', String(255), comment='订单校验参数 '),
    Column('status', INTEGER(255), comment='处理结果 1-成功 2-失败'),
    Column('createTime', String(32), comment='回调时间')
)


class TpCallback(Base):
    __tablename__ = 'tp_callback'

    id = Column(INTEGER(11), primary_key=True)
    tp_name = Column(String(255), comment='游戏方名称')
    game_id = Column(String(255), comment='游戏id')
    game_name = Column(String(255), comment='游戏名称')
    order_num = Column(String(255), comment='流水号（订单号）')
    game_reward = Column(String(255), comment='游戏方奖励金币数')
    reward = Column(String(255), comment='总奖励金币数')
    tp_game_id = Column(String(255), comment='用户在游戏方的id')
    user_id = Column(String(255), index=True, comment='奖励用户id')
    channel_code = Column(String(255), comment='渠道标识')
    channel_name = Column(String(255), comment='渠道名称')
    create_time = Column(BIGINT(20), comment='创建时间')
    status = Column(INTEGER(2), comment='状态（1-成功 2-失败）')


class TpCompany(Base):
    __tablename__ = 'tp_company'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(255), nullable=False, comment='公司名称')
    short_name = Column(String(255))
    image_url = Column(String(255))
    remark = Column(String(255), comment='描述')
    h5_type = Column(INTEGER(2), nullable=False, server_default=text("'1'"), comment='游戏列表类型（1-我方列表 2-他方列表）')
    create_time = Column(BIGINT(20), comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-启用 2-停用）')


class TpGame(Base):
    __tablename__ = 'tp_game'
    __table_args__ = (
        Index('index_ptype', 'game_tag', 'status', 'ptype'),
    )

    id = Column(INTEGER(11), primary_key=True)
    interface_id = Column(INTEGER(11), nullable=False, comment='所属接口')
    game_id = Column(INTEGER(11), nullable=False, comment='游戏id')
    game_title = Column(String(255), nullable=False, comment='游戏标题（名称）')
    icon = Column(String(255), nullable=False, comment='游戏图标')
    url = Column(String(255), comment='游戏地址')
    enddate = Column(String(255), comment='活动截止日期')
    game_gold = Column(DECIMAL(10, 2), comment='奖励金币数')
    introduce = Column(Text, comment='游戏介绍')
    package_name = Column(String(225), comment='包名')
    status = Column(INTEGER(2), server_default=text("'1'"), comment='状态（1-正常 2-下架）')
    game_tag = Column(INTEGER(2), comment='游戏标签 （1-正常有游戏 2-快速任务）')
    order_id = Column(INTEGER(11), server_default=text("'1'"))
    ptype = Column(INTEGER(2), comment='适用设备类型 1-iOS 2-安卓')
    label_str = Column(String(255), comment='小标签，多个用逗号分隔')
    short_intro = Column(String(255), comment='充值返利')


class TpGameRelationType(Base):
    __tablename__ = 'tp_game_relation_type'

    id = Column(INTEGER(10), primary_key=True)
    game_id = Column(INTEGER(10), comment='游戏id')
    type_id = Column(INTEGER(10), comment='类型id')


class TpGameType(Base):
    __tablename__ = 'tp_game_type'

    id = Column(INTEGER(11), primary_key=True)
    type_name = Column(String(255))
    create_time = Column(BIGINT(20))
    orders = Column(INTEGER(5), comment='排序')
    status = Column(INTEGER(255))


class TpHippoClkTracking(Base):
    __tablename__ = 'tp_hippo_clk_tracking'
    __table_args__ = {'comment': '广告曝光上报记录'}

    id = Column(INTEGER(11), primary_key=True)
    clk_tracking = Column(Text, nullable=False)
    create_time = Column(BIGINT(20), nullable=False)


class TpHippoImpTracking(Base):
    __tablename__ = 'tp_hippo_imp_tracking'
    __table_args__ = {'comment': '资讯曝光上报记录'}

    id = Column(INTEGER(11), primary_key=True)
    imp_tracking = Column(Text, nullable=False)
    create_time = Column(BIGINT(20), nullable=False)


class TpInterface(Base):
    __tablename__ = 'tp_interface'

    id = Column(INTEGER(11), primary_key=True)
    company_id = Column(INTEGER(11), nullable=False, comment='所属公司')
    interface_name = Column(String(255), nullable=False, comment='接口名称')
    interface_code = Column(String(255), nullable=False, comment='接口代码')
    base_url = Column(String(255), nullable=False, comment='基础地址')
    req_type = Column(INTEGER(2), nullable=False, comment='请求类型（1-get 2-post）')
    is_cycle = Column(INTEGER(2), nullable=False, comment='是否循环')
    create_time = Column(BIGINT(20))
    weight = Column(INTEGER(11), comment='定时顺序')
    coins = Column(BIGINT(255), comment='预计获取金币')
    game_type = Column(INTEGER(2), comment='游戏类型id')


class TpKsCallback(Base):
    __tablename__ = 'tp_ks_callback'

    id = Column(INTEGER(11), primary_key=True)
    equipment_type = Column(INTEGER(2), nullable=False, comment='设备类型（1-iOS 2-安卓）')
    imeiMD5 = Column(String(255), nullable=False, index=True, comment='设备号MD5加密字段')
    ip = Column(String(255), comment='IP地址')
    callback = Column(Text, comment='回调地址')
    create_time = Column(BIGINT(20), nullable=False, comment='创建时间')
    status = Column(INTEGER(2), nullable=False, comment='状态（1-待回调 2-已回调）')


class TpParam(Base):
    __tablename__ = 'tp_params'

    id = Column(INTEGER(11), primary_key=True)
    interface_id = Column(INTEGER(11), nullable=False)
    name = Column(String(255), nullable=False, comment='参数名称')
    code = Column(String(255), nullable=False, comment='参数代码')
    type = Column(String(255), nullable=False, comment='参数类型（1-固定值 2-请求参数 3-加密）')
    value = Column(String(255))
    is_encrypt = Column(INTEGER(255), nullable=False, comment='是否加密（1-是 2-否）')
    encrypt_type = Column(INTEGER(255), comment='加密类型（1-MD5 2-其他）')
    encrypt_separator = Column(String(2), comment='加密分隔符')
    is_need = Column(INTEGER(255), nullable=False, comment='是否是请求列表参数（1-是 2-否）')
    encrypt_need = Column(INTEGER(2), nullable=False, comment='是否加密列表所需字段')
    info_encrypt_need = Column(INTEGER(2), nullable=False, comment='是否详情加密所需字段(1-是 2-否)')
    order_id = Column(INTEGER(2), nullable=False, comment='排序')
    is_replace = Column(INTEGER(2), comment='是否被替换 （1-是 2-否）')
    replace_code = Column(String(255), comment='被替换成用户参数代码')
    create_time = Column(BIGINT(20), nullable=False)


t_tp_pcdd_callback = Table(
    'tp_pcdd_callback', metadata,
    Column('adid', INTEGER(32), comment='广告ID'),
    Column('adname', String(32), comment='广告名称'),
    Column('pid', String(32), comment='开发者渠道ID'),
    Column('ordernum', String(32), comment='订单编号'),
    Column('dlevel', INTEGER(32), comment='奖励级别'),
    Column('pagename', String(255)),
    Column('deviceid', String(255)),
    Column('simid', String(32), comment='sim卡id'),
    Column('userid', String(32), comment='开发者渠道自身统计编号'),
    Column('merid', String(32), comment='用户体验广告注册的账号id'),
    Column('event', Text, comment='奖励说明'),
    Column('price', Float(10, True), comment='结算单价、保留2位小数'),
    Column('money', Float(10, True), comment='给用户奖励金额、保留2位小数'),
    Column('itime', Date, comment='用户领取奖励时间'),
    Column('keycode', String(64), comment='MD5(adid+pid+ordernum+deviceid+key)  小写'),
    Column('status', INTEGER(2), comment='状态（1-失败 2-成功）'),
    Column('createTime', String(32), comment=' 回调时间')
)


class TpResp(Base):
    __tablename__ = 'tp_resp'

    id = Column(INTEGER(11), primary_key=True)
    interface_id = Column(INTEGER(11), nullable=False)
    gfield = Column(String(255))
    respkey = Column(String(255))


class TpTaskCallback(Base):
    __tablename__ = 'tp_task_callback'

    id = Column(INTEGER(11), primary_key=True)
    orderNum = Column(String(64), comment='唯一订单号')
    taskId = Column(INTEGER(11), comment='任务id')
    name = Column(String(255), comment='任务名称')
    userId = Column(String(64), comment='用户id')
    chReward = Column(DECIMAL(10, 2), comment='渠道奖励(单位：元）')
    userReward = Column(DECIMAL(10, 2), comment='用户奖励（单位：元）')
    totalCoin = Column(INTEGER(11), server_default=text("'0'"), comment='实际用户获得金币数')
    resultCode = Column(INTEGER(11), comment='审核结果(2-拒绝 1-通过)')
    remark = Column(String(255), comment='审核结果描述')
    date = Column(BIGINT(20), comment='发送时间')
    sign = Column(String(255), comment='密钥')
    createTime = Column(BIGINT(20), comment='创建时间')
    status = Column(INTEGER(255), comment='处理结果（1-成功 2-失败 3-重复发送）')


class TpTaskInfo(Base):
    __tablename__ = 'tp_task_info'

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(64), comment='任务名称')
    logo = Column(String(255), comment='任务logo')
    type_id = Column(INTEGER(10), comment='任务类型')
    label = Column(String(128), comment='任务标签逗号分隔')
    reward = Column(DECIMAL(10, 2), comment='奖励单位元')
    fulfil_time = Column(INTEGER(11))
    time_unit = Column(INTEGER(11))
    channel_task_number = Column(INTEGER(11), comment='渠道分配数量')
    surplus_channel_task_number = Column(INTEGER(11))
    is_order = Column(INTEGER(2), comment='是否可预约1-是 2-否')
    order_time = Column(BIGINT(20), comment='预上架时间')
    is_upper = Column(INTEGER(2), comment='是否上架1上架2下架 3-待上架')
    is_signin = Column(INTEGER(2), comment='是否是签到赚任务1是2否')
    task_channel = Column(String(32), comment='任务渠道')
    create_time = Column(BIGINT(20), comment='创建时间')
    update_time = Column(BIGINT(20))
    drReward = Column(DECIMAL(10, 2), server_default=text("'0.00'"), comment='达人奖励')
    task_info_url = Column(String(255))
    orders = Column(INTEGER(10), comment='排序')


class TpTaskStatusCallback(Base):
    __tablename__ = 'tp_task_status_callback'

    id = Column(BIGINT(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    task_id = Column(INTEGER(10), comment='任务id')
    flew_num = Column(String(255))
    status = Column(INTEGER(1), comment='状态1-待提交 2-已提交，待审核 3-审核通过 4-审核失败 5-预约')
    sign = Column(String(64), comment='加密信息')
    deal_status = Column(INTEGER(2), comment='处理结果 1-成功 2-失败')
    create_time = Column(BIGINT(20))
    expire_time = Column(BIGINT(20))


class TpVideoCallback(Base):
    __tablename__ = 'tp_video_callback'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    operate_type = Column(INTEGER(2), comment='操作类型：1.每日红包 2.首页视频 3.补签卡 4.首页弹窗')
    trans_id = Column(String(64), comment='唯一交易ID')
    reward_amount = Column(INTEGER(10), comment='奖励数量')
    reward_name = Column(String(32), comment='奖励名称')
    creator_time = Column(BIGINT(20), comment='创建时间')
    sign = Column(String(128), comment='加密结果')
    state = Column(INTEGER(1), comment='状态：1成功2验签失败3异常')
    remarks = Column(String(128), comment='备注')


t_tp_xw_callback = Table(
    'tp_xw_callback', metadata,
    Column('adid', INTEGER(11), comment='广告ID'),
    Column('adname', String(255), comment='广告名称'),
    Column('appid', String(255), comment='开发者ID'),
    Column('ordernum', String(255), comment='订单编号'),
    Column('dlevel', String(255), comment='奖励级别'),
    Column('pagename', String(255), comment='用户体验游戏的包名'),
    Column('deviceid', String(255), comment='手机设备号 imei 或 idfa'),
    Column('simid', String(255), comment='手机sim卡id'),
    Column('appsign', String(255), comment='开发者用户编号（用户id）'),
    Column('merid', String(255), comment='用户体验游戏注册的账号id'),
    Column('event', String(255), comment='奖励说明—在开发者自己的APP中需显示给用户看，以便用户了解自己获得的奖励'),
    Column('price', String(255), comment='于开发者结算单价、保留2位小数 【人民币单位】'),
    Column('money', String(255), comment='开发者需奖励给用户金额 【人民币单位】'),
    Column('itime', String(255), comment='用户获得奖励时间 时间字符串 如：2018/01/24 12:13:24'),
    Column('keycode', String(255), comment='订单校验参数 '),
    Column('status', INTEGER(255), comment='处理结果 1-成功 2-失败'),
    Column('createTime', String(32), comment='回调时间')
)


class TpYmCallback(Base):
    __tablename__ = 'tp_ym_callback'

    id = Column(INTEGER(10), primary_key=True)
    user_id = Column(String(64), comment='用户id')
    coin_callback_id = Column(String(64), comment='奖励记录Id')
    coin_count = Column(BIGINT(20), comment='奖励金币数')
    callback_time = Column(BIGINT(20), comment='回调时间')
    sign = Column(String(64), comment='加密值')
    state = Column(INTEGER(1), comment='状态1成功2失败')
    creator_time = Column(BIGINT(20), comment='创建时间')


t_tp_yole_callback = Table(
    'tp_yole_callback', metadata,
    Column('yoleid', String(255), comment='流水号'),
    Column('userid', String(255), comment='Box中用户编号'),
    Column('appid', String(255), comment='贵方用户ID'),
    Column('imei', String(255), comment='安卓手机的IMEI'),
    Column('chid', String(255), comment='渠道编号'),
    Column('gmid', String(255), comment='游戏编号'),
    Column('gmname', String(255), comment='游戏名称（经过urlencode编码）'),
    Column('rewardid', String(255), comment='奖励编号'),
    Column('rewarddesc', String(255), comment='奖励描述（经过urlencode编码）'),
    Column('gmgold', String(255), comment='用户奖励积分'),
    Column('chgold', String(255), comment='渠道奖励积分'),
    Column('rewardtype', String(255), comment='任务类型 1是普通任务，2是充值'),
    Column('menuorder', String(255), comment='序号'),
    Column('sign', String(255)),
    Column('status', INTEGER(255), comment='状态（1-成功 2-失败）'),
    Column('createTime', String(32), comment='回调时间')
)


class TpYuwanCallback(Base):
    __tablename__ = 'tp_yuwan_callback'

    id = Column(INTEGER(11), primary_key=True)
    orderNo = Column(String(255), nullable=False, comment='新量象平台唯一订单号')
    rewardDataJson = Column(String(1000), comment='领取奖励信息（json_encode）')
    sign = Column(String(255), comment='签名')
    time = Column(String(255), comment='发送时 时间戳 (单位秒)')
    createTime = Column(DateTime)
    ordertype = Column(String(255), comment='订单类型  cpl / apa')
    status = Column(INTEGER(11), comment='订单状态  1-失败 2-成功')
    rewardRule = Column(String(500))
    stageId = Column(INTEGER(11))
    stageNum = Column(String(255))
    advertIcon = Column(String(500))
    rewardTypeText = Column(String(255))
    rewardDescription = Column(String(255))
    advertName = Column(String(255))
    rewardType = Column(String(255))
    isSubsidy = Column(INTEGER(11))
    mediaMoney = Column(String(255))
    rewardUserRate = Column(String(255))
    currencyRate = Column(String(255))
    userMoney = Column(String(255))
    userCurrency = Column(String(255))
    mediaUserId = Column(String(255))
    receivedTime = Column(INTEGER(11))


class TpZrbCallback(Base):
    __tablename__ = 'tp_zrb_callback'

    id = Column(INTEGER(11), primary_key=True)
    uid = Column(String(255))
    points = Column(DECIMAL(12, 2))
    orderid = Column(String(255))
    ordername = Column(String(255))
    token = Column(String(255))
    createTime = Column(DateTime)
    status = Column(String(11))


t_tp_ibx_callback = Table(
    'tp_ibx_callback', metadata,
    Column('app_key', String(32), comment='平台的应用id'),
    Column('device', String(32), comment='ios，安卓'),
    Column('device_info', BigInteger, comment='安卓传imei,ios传参idfa值'),
    Column('target_id', String(128), comment='接入平台的用户唯一标示'),
    Column('unit', String(32), comment='接入平台的奖励单位'),
    Column('time_end', BigInteger, comment='领取完成时间，格式为yyyyMMddHHmmss，如2009年12月25日9点10分10秒表示为20091225091010'),
    Column('user_reward', Float(10), comment='应用方应当给予用户奖励(应用平台币计价)'),
    Column('app_reward', Float(10), comment='平台给予应用奖励'),
    Column('game_name', String(32), comment='领取奖励的游戏名'),
    Column('game_id', BigInteger, comment='领取奖励的游戏编号'),
    Column('sign', String(32),
           comment='通过签名算法计算得出的签名值，通过签名算法计算得出的签名值，'
                   '详见签名规则MD5(app_key+device+device_info+target_id+回调地址+app_secret) .toUpperCase'),
    Column('content', String(32), comment='奖励说明'),
    Column('order_id', BigInteger, comment='订单号'),
    Column('type', BigInteger, comment='1试玩赢金，2充值返利，3冲榜福利，4高额试玩'),
    Column('status', Integer, comment='任务状态1-成功0-失败'),
    Column('update_time', DateTime, comment='更新时间')
)


class TpJxwCallback(Base):
    __tablename__ = 'tp_jxw_callback'

    prize_id = Column(Integer, primary_key=True, comment='奖励流水标识，唯一')
    name = Column(String(150), comment='广告名称')
    title = Column(String(300), comment='奖励名称')
    type = Column(Integer, comment='任务类别，1 试玩，2 竞技，3 充值，4 榜单，7 悬赏 8 活动')
    task_prize = Column(Float(10), comment='用户领取金额（单位元）')
    deal_prize = Column(Float(10), comment='渠道利润（单位元）')
    task_prize_coin = Column(Float(10), comment='领取奖励（渠道方货币单位）')
    ad_id = Column(Integer, comment='广告 id')
    prize_time = Column(Integer, comment='领奖时间（unix 时间戳）')
    task_id = Column(Integer, comment='奖励任务任务 id')
    game_id = Column(Integer, comment='游戏 id')
    mid = Column(Integer, comment='渠道标识，聚享玩提供')
    resource_id = Column(String(64), comment='渠道用户标识')
    time = Column(Integer, comment='10 位时间戳')
    sign = Column(String(255), comment='验签，md5(prize_info+mid+time+resource_id+token)     (prize_info 里数据为 unicode 编码格式)')
    device_code = Column(String(255), comment='玩家设备码（安卓 imei,ios idfa）')
    field = Column(Integer, comment='广告类型（1 棋牌 2 金融 3 微任务 4H5 5 手游 6 棋牌 2 7 手游 2；奖励为活动时，此字段为固定值 0）')
    icon = Column(String(255), comment='游戏 icon（需用 url 解码）')
    status = Column('status', Integer, comment='任务状态1-成功0-失败')
    update_time = Column('update_time', DateTime, comment='更新时间')