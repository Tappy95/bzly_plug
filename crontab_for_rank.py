import random
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

from sqlalchemy import create_engine, select, and_, update, insert
from config import *
from models.alchemy_models import LRankMachine, LRankCoin
from util.static_methods import serialize

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)


def update_rank_user():
    print("start update rank user! the time is:%s" % datetime.now())
    cur_hour = int(datetime.fromtimestamp(time.time()).strftime('%H'))
    cur_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    range_coin = 1
    range_coin_after = 2+cur_hour
    with engine.connect() as conn:
        select_rank_machine = conn.execute(select([LRankMachine])).fetchall()
        # rank_machine = random.sample(select_rank_machine, 10)
        fakers = []
        for user in select_rank_machine:
            select_exist_rank = conn.execute(select([LRankCoin]).where(
                and_(
                    LRankCoin.mobile == user['mobile'],
                    LRankCoin.rank_date == cur_date
                )
            )).fetchone()
            coin_balance = (select_exist_rank['coin_balance'])/10000 + random.randint(range_coin, range_coin_after) \
                if select_exist_rank else random.randint(range_coin, range_coin_after)
            faker = {
                "rank_type": 1,
                "rank_order": 1,
                "image_url": user['img'],
                "alias_name": "",
                "mobile": user['mobile'],
                "user_id": user['mobile'],
                "coin_balance": coin_balance * 10000,
                "rank_date": cur_date,
                "create_time": int(time.time() * 1000),
                "real_data": 2,
                "reward_amount": 0,
            }
            fakers.append(faker)
        fakers = sorted(fakers, key=lambda k: k['coin_balance'], reverse=True)
        for idx, fake in enumerate(fakers):
            select_exist_rank = conn.execute(select([LRankCoin]).where(
                and_(
                    LRankCoin.mobile == fake['mobile'],
                    LRankCoin.rank_date == cur_date
                )
            )).fetchone()
            fake['rank_order'] = idx+1
            if select_exist_rank:
                update_rank = update(LRankCoin).where(
                    LRankCoin.id == select_exist_rank['id']
                ).values(
                    fake
                )
                conn.execute(update_rank)
            else:
                inset_rank = insert(LRankCoin).values(fake)
                conn.execute(inset_rank)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    # scheduler.add_job(my_clock, "cron", hour='21', minute='48')
    scheduler.add_job(update_rank_user, "interval", minutes=60)
    # scheduler.add_job(my_clock, "cron", hour='21', minute='48')
    scheduler.start()
