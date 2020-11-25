import os

# ENV_TYPE = os.environ.get('ENV_TYPE', '')
# print(ENV_TYPE)
# 线上
# PRODUCTION_ENV = True
# 本地
PRODUCTION_ENV = False

DB_USER_NAME = "online_db_accout" if PRODUCTION_ENV else "root"
DB_USER_PW = "JdNH9QN52Nd7Pox58J7WmaD5nLiQ" if PRODUCTION_ENV else "!Syy950507"
DB_SEVER_ADDR = "rm-m5epui2mr0l38qot98o.mysql.rds.aliyuncs.com" if PRODUCTION_ENV else "cdb-nfyowpkz.gz.tencentcdb.com"
DB_SEVER_PORT = 3306 if PRODUCTION_ENV else 10166
DB_DATABASE_NAME = "bzly"

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{name:s}:{pw:s}@{addr:s}:{port}/{db:s}".format(
    name=DB_USER_NAME,
    pw=DB_USER_PW,
    addr=DB_SEVER_ADDR,
    db=DB_DATABASE_NAME,
    port=DB_SEVER_PORT
)

SQLALCHEMY_POOL_PRE_PING = True
SQLALCHEMY_ECHO = False if PRODUCTION_ENV else False
SQLALCHEMY_POOL_SIZE = 0
SQLALCHEMY_POOL_MAX_OVERFLOW = -1
SQLALCHEMY_POOL_RECYCLE = 120

# ELASTIC_HOST = "10.0.1.3" if PRODUCTION_ENV else "es-fx731b5q.public.tencentelasticsearch.com"
# ELASTIC_PORT = 9200 if PRODUCTION_ENV else 9200
# ELASTIC_INDEX = "" if PRODUCTION_ENV else ""
# ELASTIC_DOC_TYPE = "" if PRODUCTION_ENV else ""
# ELASTIC_VALUES = "" if PRODUCTION_ENV else ""
# ELASTIC_USE_SSL = True
# ELASTIC_TIMEOUT = 60
# ELASTIC_USERNAME = "elastic" if PRODUCTION_ENV else "elastic"
# ELASTIC_PASSWORD = "$EStest.813" if PRODUCTION_ENV else "$EStest.813"
# ELASTICSEARCH_URL = \
#     f'http://{ELASTIC_USERNAME}:{ELASTIC_PASSWORD}@{ELASTIC_HOST}:{ELASTIC_PORT}' \
#         if PRODUCTION_ENV else "http://47.102.220.1:9200"
# ELASTICSEARCH_URL = f'https://{ELASTIC_USERNAME}:{ELASTIC_PASSWORD}@{ELASTIC_HOST}:{ELASTIC_PORT}' \
#         if PRODUCTION_ENV else "https://elastic:$EStest.813@es-fx731b5q.public.tencentelasticsearch.com:9200/"
# ELASTICSEARCH_URL = f"https://elastic:$EStest.813@es-fx731b5q.public.tencentelasticsearch.com:9200/"
# ELASTIC_VALUES = {'index': "ebay", 'doc_type': "ebay_product"}
# ELASTICSEARCH_URL = [{'host': ELASTIC_HOST, 'port': ELASTIC_PORT, 'user_ssl': ELASTIC_USE_SSL,
#                       'http_auth': (ELASTIC_USERNAME, ELASTIC_PASSWORD)}] \
#     if PRODUCTION_ENV else "https://elastic:$EStest.813@es-fx731b5q.public.tencentelasticsearch.com:9200/"
#
# JWT_SECRET = "secret"

REDIS_HOST = "47.105.131.58" if PRODUCTION_ENV else "47.105.131.58"
REDIS_PORT = 6379 if PRODUCTION_ENV else 6379
REDIS_DB_NUMBER = 0
# REDIS_PASSWORD = "$redis.813" if PRODUCTION_ENV else "c18d1ba0f01f15b2168297663a85abf5"
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_NUMBER}'

# NSQ_LOOKUPD_HTTP_ADDR = 'bd-nsqlookupd:4161' if PRODUCTION_ENV else '134.73.133.2:25761'
# NSQ_NSQD_TCP_ADDR = 'bd-nsqd:4150' if PRODUCTION_ENV else '134.73.133.2:25750'
# NSQ_NSQD_HTTP_ADDR = 'bd-nsqd:4151' if PRODUCTION_ENV else '134.73.133.2:25751'

NSQ_LOOKUPD_HTTP_ADDR = '47.105.131.58:4161' if PRODUCTION_ENV else '47.112.96.218:4161'
NSQ_NSQD_TCP_ADDR = '47.105.131.58:4150' if PRODUCTION_ENV else '47.112.96.218:4150'
NSQ_NSQD_HTTP_ADDR = '47.105.131.58:4151' if PRODUCTION_ENV else '47.112.96.218:4151'

INPUT_NSQ_CONF = {
    'lookupd_http_addresses': [NSQ_LOOKUPD_HTTP_ADDR]
}
OUTPUT_NSQ_CONF = {
    'nsqd_tcp_addresses': NSQ_NSQD_TCP_ADDR
}

# REPORT_TASK_TOPIC = "shopee_analysis_report"
#
# SYSTEM_NAME = "shopee"

AIOHTTP_PORT = 8090 if PRODUCTION_ENV else 7999

XW_KEY = "ba9g60295zs208pk"

PCDD_KEY = "PCDDXW5_QLQW_11474"

IBX_SECRET = "06bff8a6f9963466"
IBX_NOTIFY_URL = "http://lottery.shouzhuan518.com/py/ibxcallback"

JXW_TOKEN = "0d17f372103a8433947afc2a289239d5"
JXW_MID = "1245"

YW_SECRET = "yzkp444d9syun0cmdjodqv8av9ibqxaz"

DY_SECRET = "8438a57e060153af209f6480d475630e"
DY_ID = "dy_59634181"

ZB_MEDIA_ID = "65"
ZB_APP_ID_SEED = "54"
ZB_KEY = "20d89382ff5c0e04cc265506a14e8892"
