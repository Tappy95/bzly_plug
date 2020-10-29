import copy
import json
import time
import traceback
from datetime import datetime
from operator import itemgetter
from urllib.parse import quote

from config import *

from aiohttp import web
from sqlalchemy import select, update, and_, text, or_
from sqlalchemy.dialects.mysql import insert

from models.alchemy_models import MUserInfo, t_tp_pcdd_callback, PDictionary, t_tp_xw_callback, TpTaskInfo, \
    t_tp_ibx_callback, TpJxwCallback, TpYwCallback, TpDyCallback, TpZbCallback, LCoinChange, MChannelInfo, MChannel
from task.callback_task import fission_schema, cash_exchange, select_user_id, get_channel_user_ids, get_callback_infos
from task.check_sign import check_xw_sign, check_ibx_sign, check_jxw_sign, check_yw_sign, check_dy_sign, check_zb_sign
from util.log import logger
from util.static_methods import serialize

routes = web.RouteTableDef()


# 查看当前用户闯关状态->七个关卡状态

# 单任务状态->已赚金币/任务要求赚取总额,已邀请人/任务要求邀请人总数.

# 开启新关卡

# 提交结算任务, 获取三张随机牌

# 提交抽牌结果,完成结算

