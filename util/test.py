import csv
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
            with open('./bb.txt', 'w') as file_obj2:
                file_obj2.writelines([user['user_id'] + ', ' + str(user['account_id']) + '\n' for user in select_all])


def get_phone_number():
    with engine.connect() as conn:
        with open('./zhuhai.txt') as file:
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


def create_fake_coinchange():
    with engine.connect() as conn:
        select_coinchange = conn.execute(select([LCoinChange]).where(
            and_(
                LCoinChange.changed_time <= 1609486855000,
                LCoinChange.changed_type == 7
            )
        ).limit(5000)).fetchall()
        exist_money = 0
        for result in select_coinchange:
            if result['amount'] > 100000:
                continue
            the_chang = {
                'user_id': 'dce96420b0b740b0b63beae4f200e09c',
                "amount": result['amount'],
                "flow_type": result['flow_type'],
                "changed_type": result['changed_type'],
                "changed_time": result['changed_time'] + 39000000,
                "status": result['status'],
                "account_type": result['account_type'],
                "audit_time": result['audit_time'],
                "reason": result['reason'],
                "remarks": result['remarks'],
                "coin_balance": result['coin_balance'],
            }
            exist_money += result['amount']
            print(exist_money)
            # if exist_money >= 20000000:
            #     break
            conn.execute(insert(LCoinChange).values(the_chang))


def select_daili_qian():
    with open(f'./csvfile.csv', 'r', encoding='UTF-8') as csv_obj:
        reader = csv.reader(csv_obj)
        c_dict = {}
        i_dict = {}
        for row in reader:
            if row[0] == '':
                row[0] = 0

            c_dict[int(float(row[0]))] = row[2]
            i_dict[int(float(row[1]))] = row[3:]
        data = []
        with open('./results.csv', 'w', newline='', encoding='UTF-8') as recharge_obj:
            write_recharge = csv.writer(recharge_obj)
            for category_id, info in i_dict.items():
                a_data = []
                a_data.append(category_id)
                if category_id in c_dict:
                    if not c_dict[category_id]:
                        a_data.append(0)
                    else:
                        a_data.append(c_dict[category_id])
                else:
                    a_data.append(0)
                a_data.extend(info)
                data.append(a_data)
            write_recharge.writerows(data)


def convert_csv():
    import pandas as pd
    data_xls = pd.read_excel('12.xlsx', 'Sheet1', index_col=None)
    data_xls.to_csv('csvfile.csv', encoding='utf-8', index=False)


def update_user_money():
    with open('./bb.txt', 'r') as file_obj:
        a = file_obj.readlines()
        for i in a:
            b = i.split(',')
            id = b[0],
            money = int(float(b[1]) * 10000)
            with engine.connect() as conn:
                select_user = conn.execute(select([MUserInfo]).where(
                    MUserInfo.account_id == id
                )).fetchone()
                print(id, select_user['coin'], money, select_user['coin'] + money)
                conn.execute(update(MUserInfo).values({
                    "coin": select_user['coin'] + money
                }).where(
                    MUserInfo.account_id == id
                ))


if __name__ == '__main__':
    create_fake_coinchange()
