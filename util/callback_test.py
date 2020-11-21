import aiohttp
import asyncio
import hashlib

from config import *


async def pcdd_call_back_test():
    # 参数
    m = hashlib.md5()

    key = "PCDDXW5_QLQW_11474"
    adid = 43520
    pid = "11474"
    ordernum = "99869465959891053"
    deviceid = "863270643441130"
    params = {
        "adid": adid,
        "adname": "暴击联盟oi",
        "pid": pid,
        "ordernum": ordernum,
        "dlevel": 1,
        "pagename": "245603539208156800",
        "deviceid": deviceid,
        "userid": "2cfdd8e67aaf45deb3cb242a1621f2de",
        "merid": "13167325185",
        "event": "暴击联盟累计获得5000金币（仅限新用户）",
        "price": "0.85",
        "money": "0.55",
        "itime": "2020/9/29 10:00:38",
        "ptype": 2,
        "keycode": hashlib.md5((str(adid) + pid + ordernum + deviceid + key).encode('utf-8')).hexdigest(),
        "awardtype": 0,
        "stype": 1,
        "imgurl": "http://pcdd-app.oss-cn-hangzhou.aliyuncs.com/advimg/20200617/2020061709571795476049.jpg",
        "simid": "",
        "pagename": "com.tencent.tmgp.wbbuyu"
    }
    print(params['keycode'])
    async with aiohttp.ClientSession() as client:
        async with client.get('http://lottery.shouzhuan518.com/py/pcddcallback', params=params) as resp:
            # async with client.get('http://localhost:7999/pcddcallback', params=params) as resp:
            assert resp.status == 200
            r = await resp.json()
            print(r)


async def xw_call_back_test():
    # 参数
    m = hashlib.md5()

    key = "ba9g60295zs208pk"
    adid = 43520
    pid = "11474"
    price = "0.85"
    money = "0.55"
    user_id = "2cfdd8e67aaf45deb3cb242a1621f2de"
    ordernum = "99869465959661053"
    deviceid = "863270643441130"
    params = {
        "adid": adid,
        "adname": "暴击联盟oi",
        "appid": pid,
        "ordernum": ordernum,
        "dlevel": 1,
        "pagename": "245603539208156800",
        "deviceid": deviceid,
        "appsign": user_id,
        "merid": "13167325185",
        "simid": "866001031077416",
        "event": "暴击联盟累计获得5000金币（仅限新用户）",
        "price": price,
        "money": money,
        "itime": "2020/9/29 10:00:38",
        "ptype": 2,
        "keycode": hashlib.md5(
            (str(adid) + pid + ordernum + "1" + deviceid + user_id + price + money + key).encode('utf-8')).hexdigest(),
        "awardtype": 0,
        "stype": 1,
        "imgurl": "http://pcdd-app.oss-cn-hangzhou.aliyuncs.com/advimg/20200617/2020061709571795476049.jpg",
        "pagename": "com.tencent.tmgp.wbbuyu"
    }
    print(params['keycode'])
    async with aiohttp.ClientSession() as client:
        async with client.get('http://lottery.shouzhuan518.com/py/xwcallback', params=params) as resp:
            # async with client.get('http://localhost:7999/xwcallback', params=params) as resp:
            assert resp.status == 200
            r = await resp.json()
            print(r)


async def ibx_call_back_test():
    # 参数
    m = hashlib.md5()

    app_secret = IBX_SECRET
    notify_url = IBX_NOTIFY_URL
    app_key = "142792891"
    device = "安卓"
    device_info = "863270643441130"
    target_id = "735e262f38de420b9a545a884c89cba1"
    game_id = "11474"
    app_reward = "0.85"
    user_reward = "10000"

    order_id = "99869465955614"
    params = {
        "app_key": app_key,
        "device": device,
        "device_info": device_info,
        "target_id": target_id,
        "unit": "金币",
        "time_end": "20201003133525",
        "user_reward": user_reward,
        "app_reward": app_reward,
        "game_name": "奇奇乐捕鱼",
        "game_id": 324,
        "sign": (hashlib.md5(
            (app_key + device + device_info + target_id + notify_url + IBX_SECRET).encode(
                'utf-8')).hexdigest()).upper(),
        "content": "累计红包0.9元",
        "order_id": order_id,
        "type": 1
    }
    print(params['sign'])
    async with aiohttp.ClientSession() as client:
        async with client.post('http://lottery.shouzhuan518.com/py/ibxcallback', data=params) as resp:
        # async with client.post('http://localhost:8090/ibxcallback', data=params) as resp:
        #     assert resp.status == 200
            r = await resp.json()
            print(r)


async def yw_call_back_test():
    # 参数
    m = hashlib.md5()

    orderNo = "142792891"
    rewardDataJson = '{"advertName":"\u6251\u5ba2\u6355\u9c7c","advertIcon":"http:\/\/imgs1.zhuoyixia.com\/5d0ae875d7ffc.png","rewardRule":"\u5168\u573a\u4efb\u610f\u6e38\u620f\u7d2f\u8ba1\u8d62\u53d6\u91d1\u5e01 5\u5343","stageId":"1","stageNum":"6","rewardType":"1","isSubsidy":"0","mediaMoney":"0.60","rewardUserRate":"60.00","currencyRate":"1.00","userMoney":"0.36","userCurrency":"0.36","mediaUserId":"735e262f38de420b9a545a884c89cba1","receivedTime":"1576646036"}'
    time = "1601913600"
    params = {
        "orderNo": orderNo,
        "rewardDataJson": rewardDataJson,
        "time": time,
        "sign": (hashlib.md5(
            (rewardDataJson + time + YW_SECRET).encode(
                'utf-8')).hexdigest()).upper()
    }
    print(params['sign'])
    async with aiohttp.ClientSession() as client:
        async with client.get('http://lottery.shouzhuan518.com/py/ywcallback', params=params) as resp:
        # async with client.post('http://localhost:7999/ywcallback', data=params) as resp:
            assert resp.status == 200
            r = await resp.json()
            print(r)


async def zb_call_back_test():
    # 参数
    m = hashlib.md5()

    dev_code = "863270643441130"
    uid = "2cfdd8e67aaf45deb3cb242a1621f2de"
    task_id = "123"
    time_now = "1601913600"
    media_price = "0.85"
    price = "0.55"
    logo = "http://www.baidu.com"

    params = {
        "uid": uid,
        "media_id": ZB_MEDIA_ID,
        "app_id": ZB_APP_ID_SEED,
        "dev_code": dev_code,
        "task_id": task_id,
        "code": "0",
        "msg": "测试一号",
        "price": price,
        "media_price": media_price,
        "time": time_now,
        "title": "闲鱼任务",
        "logo": logo,
        "sign": "1"
    }
    sign = params.pop("sign")
    before_md5 = ""
    for idx, key in enumerate(sorted(params)):
        str_ele = key + "=" + params[key]
        if idx < len(params) - 1:
            str_ele += "&"
        before_md5 += str_ele
    before_md5 += "&key=" + ZB_KEY
    print(before_md5)
    params['sign'] = (hashlib.md5(before_md5.encode('utf-8')).hexdigest()).upper()
    print(params['sign'])
    async with aiohttp.ClientSession() as client:
        # async with client.get('http://lottery.shouzhuan518.com/py/xwcallback', params=params) as resp:
        async with client.post('http://localhost:7999/zbcallback', data=params) as resp:
            assert resp.status == 200
            r = await resp.json()
            print(r)



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ibx_call_back_test())
