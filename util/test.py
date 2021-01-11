from datetime import datetime

from sqlalchemy import create_engine, select, update, and_, insert
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


def get_real_id():
    with engine.connect() as conn:
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


def get_phone_number():
    with engine.connect() as conn:
        with open('./guangzhou.txt') as file:
            f_list = file.readlines()
            results = []
            for i in f_list:
                if i:
                    a = i.replace('，', '')
                    b = a.replace('\n', '')
                    result = {
                        "phonenumber": b,
                        "status": 0
                    }
                    results.append(result)
            print(results)
        conn.execute(insert(RealPhoneNumber).values(results))


if __name__ == '__main__':
    get_real_id()
