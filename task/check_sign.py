import hashlib
from config import *
from util.log import logger


def check_xw_sign(keysign, adid, appid, ordernum, deviceid, appsign, price, money):
    check_key = hashlib.md5(
        (str(adid) + appid + ordernum + "1" + deviceid + appsign + price + money + XW_KEY).encode('utf-8')).hexdigest()
    logger.info("server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False


def check_pcdd_sign(keysign, adid, pid, ordernum, deviceid):
    check_key = hashlib.md5(
        (str(adid) + pid + ordernum + deviceid + PCDD_KEY).encode('utf-8')).hexdigest()
    logger.info("server keycode:{},request keycode:{}".format(check_key, keysign))
    if keysign == check_key:
        return True
    else:
        return False
