import copy
import hashlib
from config import *
from util.log import logger


def check_xw_sign(keysign, adid, appid, ordernum, deviceid, appsign, price, money):
    check_key = hashlib.md5(
        (str(adid) + appid + ordernum + "1" + deviceid + appsign + price + money + XW_KEY).encode('utf-8')).hexdigest()
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
    check_key = (hashlib.md5(
        (
                "advert_id=" + advert_id + "&" + "advert_name=" + advert_name + "&" + "content=" + content + "&" +
                "created=" + created + "&" + "device_id=" + device_id + "&" + "media_id=" + media_id + "&" +
                "media_income=" + media_income + "&" + "member_income=" + member_income + "&" + "order_id=" + order_id
                + "&" + "user_id=" + user_id + "&" + "key=" + DY_SECRET).encode(
            'utf-8')).hexdigest()).lower()
    logger.info("DY:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False
