import aiohttp
import asyncio
import hashlib


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
        # async with client.get('http://lottery.shouzhuan518.com/api/tpGame/pcddCallback', params=params) as resp:
        async with client.get('http://localhost:7999/pcddcallback', params=params) as resp:
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
        # async with client.get('http://lottery.shouzhuan518.com/api/tpGame/pcddCallback', params=params) as resp:
        async with client.get('http://localhost:7999/xwcallback', params=params) as resp:
            assert resp.status == 200
            r = await resp.json()
            print(r)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(xw_call_back_test())
