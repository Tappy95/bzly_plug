from datetime import datetime

from sqlalchemy import create_engine, select, update, and_
from sqlalchemy.orm import aliased, sessionmaker

from config import *

from models.alchemy_models import *
# from util.static_methods import serialize

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

    # user_alias = ana_user.alias()
    #     select_leader_count = select([ana_user_permission,
    #                                   user_alias.c.user_name
    #                                   ]).where(
    #         and_(
    #             user_alias.c.leader_id == False,
    #             ana_user_permission.c.user_id == user_alias.c.user_id
    #         )
    #     )
    # Session = sessionmaker()
    # Session.configure(bind=engine)
    # session = Session()
    # our_user = session.query(MUserInfo, LCoinChange)\
    #     .filter(MUserInfo.user_id==LCoinChange.user_id)\
    #     .filter(MUserInfo.user_id=='d64bb408629c4f7e9f5c92b503672dcb')\
    #     .all()
    # for u,l in our_user:
    #     print(u.to_dict())
    #     print(l.to_dict())
    # select_user = select([MUserInfo.mobile, LCoinChange]).where(
    #     and_(
    #        MUserInfo.user_id == LCoinChange.user_id,
    #        MUserInfo.user_id == 'd64bb408629c4f7e9f5c92b503672dcb'
    #     )
    # )
    # cur = conn.execute(select_user)
    # rec = cur.fetchone()
    # print(rec['user_id'])
    # print(serialize(cur, rec))
    with open('./aa.txt') as file_obj:
        f_list = file_obj.readlines()
        a = []
        for i in f_list:
            a.append(i.replace('\n', ''))
        print(a)
        select_all = conn.execute(select([MUserInfo]).where(
            MUserInfo.token.in_(a)
        )).fetchall()
        print([user['account_id'] for user in select_all])

