import aiohttp
import asyncio
import hashlib


async def get_ibx_tasks():
    # 参数
    m = hashlib.md5()

    app_key = "142792891"
    target_id = "2cfdd8e67aaf45deb3cb242a1621f2de"
    device_info = "863270643441130"
    device = "android"
    notify_url = "http://lottery.shouzhuan518.com/py/ibxcallback"
    app_secret = "06bff8a6f9963466"
    params = {
        "app_key": app_key,
        "target_id": target_id,
        "device_info": device_info,
        "device": device,
        "notify_url": notify_url,
        "sign": (hashlib.md5(
            (str(app_key) + device + device_info + target_id + notify_url + app_secret).encode(
                'utf-8')).hexdigest()).upper()
    }
    print(params['sign'])
    async with aiohttp.ClientSession() as client:
        async with client.post('https://api.aibianxian.net/igame/api/v1.0/cplApi/access', data=params) as resp:
            assert resp.status == 200
            r = await resp.json()
            print(r)
            token = r['data']['token']

            task_params = {
                "page_num": 1,
                "model": "",
                "osVersion": "",
                "token": token
            }
            # print(task_params)
            for page in range(1, 20):
                task_params['page_num'] = page
                # async with client.post('https://api.aibianxian.net/igame/h5/v1.51/outHightList', data=params) as task_info:
                async with client.get('https://api.aibianxian.net/igame/h5/v1.51/outHightList',
                                      data=task_params) as task_info:
                    task_result = await task_info.json()
                    # print(task_result)

                    async with client.post('http://127.0.0.1:8090/get/hightasks', json=task_result) as s_result:
                        d = await s_result.json()
                        print(task_result)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_ibx_tasks())
