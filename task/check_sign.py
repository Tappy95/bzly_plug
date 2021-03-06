import base64

import copy
import hashlib
from urllib.parse import quote

from config import *
from util.log import logger


def check_xw_sign(keysign, adid, appid, ordernum, dlevel, deviceid, appsign, price, money):
    check_key = (hashlib.md5((str(adid) + appid + ordernum + dlevel + deviceid + appsign + price + money + XW_KEY).encode(
        'utf-8')).hexdigest()).upper()
    logger.info("XW:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False


def check_pcdd_sign(keysign, adid, pid, ordernum, deviceid):
    check_key = hashlib.md5(
        (str(adid) + pid + ordernum + deviceid + PCDD_KEY).encode('utf-8')).hexdigest()
    logger.info("PCDD:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False


def check_ibx_sign(keysign, app_key, device, device_info, target_id, notify_url):
    check_key = (hashlib.md5(
        (app_key + device + device_info + target_id + notify_url + IBX_SECRET).encode('utf-8')).hexdigest()).upper()
    logger.info("IBX:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False



def check_ibx_task_sign(keysign, app_key, device, device_info, target_id):
    check_key = (hashlib.md5(
        (app_key + device + device_info + target_id + IBX_SECRET).encode('utf-8')).hexdigest()).upper()
    logger.info("IBX:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False


def check_jxw_sign(keysign, prize_info, mid, time, resource_id):
    logger.info(prize_info)
    # 转码prize_info
    # prize_info_copy = copy.deepcopy(prize_info)
    # for idx, item in enumerate(prize_info):
    #     for key in item:
    #         if
    #         prize_info_copy[idx][key] = item[key].encode("raw_unicode_escape", "utf-8").decode()
    # logger.info(prize_info_copy)
    check_key = (hashlib.md5(
        (prize_info + mid + time + resource_id + JXW_TOKEN).encode('utf-8')).hexdigest()).lower()
    logger.info("JXW:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False


def check_yw_sign(keysign, rewardDataJson, time):
    check_key = (hashlib.md5(
        (rewardDataJson + time + YW_SECRET).encode('utf-8')).hexdigest()).lower()
    logger.info("YW:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False


def check_dy_sign(keysign, advert_id, advert_name, content, created, device_id, media_id, media_income, member_income,
                  order_id, user_id):
    keystr = "advert_id=" + advert_id + "&" + "advert_name=" + quote(advert_name) + "&" + "content=" + quote(content) \
             + "&" + "created=" + created + "&" + "device_id=" + device_id + "&" + "media_id=" + media_id + "&" + \
             "media_income=" + media_income + "&" + "member_income=" + member_income + "&" + "order_id=" + order_id \
             + "&" + "user_id=" + user_id + "&" + "key=" + DY_SECRET

    logger.info(keystr)

    check_key = (hashlib.md5(keystr.encode('utf-8')).hexdigest()).lower()
    logger.info("DY:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False


def check_zb_sign(r_post):
    r_dict = {**r_post}
    before_md5 = ""
    keysign = r_dict.pop("sign")
    for idx, key in enumerate(sorted(r_dict)):
        str_ele = key + "=" + r_dict[key]
        if idx < len(r_dict) - 1:
            str_ele += "&"
        before_md5 += str_ele
    before_md5 += "&key=" + ZB_KEY
    print(before_md5)
    check_key = (hashlib.md5(before_md5.encode('utf-8')).hexdigest()).upper()
    logger.info("ZB:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False


def check_tj_sign(r_post):
    r_dict = {**r_post}
    before_md5 = ""
    keysign = r_dict.pop("sign")
    for idx, key in enumerate(sorted(r_dict)):
        str_ele = r_dict[key]
        before_md5 += str_ele+"#"
    before_md5 += TJ_APPKEY
    base64_before_md5 = base64.b64encode(before_md5.encode())
    print(before_md5)
    check_key = (hashlib.md5(base64_before_md5).hexdigest()).lower()
    logger.info("TJ:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False
