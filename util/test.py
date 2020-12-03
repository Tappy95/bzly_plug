from datetime import datetime

from sqlalchemy import create_engine, select, update
from config import *

from models.alchemy_models import *

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)

with engine.connect() as conn:
    # select_c = conn.execute(select([MPartnerInfo])).fetchone()
    # print(select_c['enddate'])
    # print(type(select_c['enddate']))
    # conn.execute(update(MPartnerInfo).values({
    #     "enddate": datetime.now()
    # }))
    select_user_ids = conn.execute(select([
        MUserInfo.user_id,
        MUserInfo.account_id,
        MUserInfo.channel_code,
        MUserInfo.parent_channel_code,
    ]).where(
        MUserInfo.referrer == None
    )).fetchall()
    for i in select_user_ids:
        print(i)
