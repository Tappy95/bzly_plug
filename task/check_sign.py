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
    check_key = (hashlib.md5(
        (prize_info + mid + time + resource_id + JXW_TOKEN).encode('utf-8')).hexdigest()).lower()
    logger.info("JXW:server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False