import json
import time

from datetime import datetime, timedelta

import emoji as emoji
from sqlalchemy import create_engine, select, and_, update, delete
from sqlalchemy.dialects.mysql import insert

import pipeflow
from config import *
from models.alchemy_models import MUserInfo, LUserCashLogPY
from pipeflow.endpoints.nsq_endpoints import NsqInputEndpoint
from util.log import logger
from util.task_protocol import QLTask

from aioelasticsearch import Elasticsearch

WORKER_NUMBER = 1
TOPIC_NAME = "callback_queue"

engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=SQLALCHEMY_POOL_PRE_PING,
    echo=SQLALCHEMY_ECHO,
    pool_size=SQLALCHEMY_POOL_SIZE,
    max_overflow=SQLALCHEMY_POOL_MAX_OVERFLOW,
    pool_recycle=SQLALCHEMY_POOL_RECYCLE,
)


class CallbackTask:

    @staticmethod
    def cash_change(connection):
        trans = connection.begin()
        try:
            connection.execute(insert(LUserCashLogPY).values(
                {
                    "user_id": "111"
                }
            ))
            trans.commit()
        except Exception as e:
            logger.info(e)
            trans.rollback()
            raise


class CallbackCase(CallbackTask):
    def __init__(self, connection):
        self.connection = connection

    def video_callback(self):
        trans = self.connection.begin()
        try:
            self.connection.execute(insert(LUserCashLogPY).values(
                {
                    "user_id": "222"
                }
            ))
            self.cash_change(self.connection)
            trans.commit()
        except Exception as e:
            logger.info(e)
            trans.rollback()
            raise


async def callback_handle(group, task):
    hy_task = QLTask(task)
    task_log = [hy_task.task_type, hy_task.task_data]
    logger.info(task_log)
    task = hy_task.task_data
    time_now = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    with engine.connect() as conn:
        callback = CallbackCase(conn)
        callback.video_callback()


def run():
    input_end = NsqInputEndpoint(TOPIC_NAME, 'callback_worker', WORKER_NUMBER, **INPUT_NSQ_CONF)
    logger.info('连接nsq成功,topic_name = {}, nsq_address={}'.format(TOPIC_NAME, INPUT_NSQ_CONF))
    server = pipeflow.Server()
    logger.info("pipeflow开始工作")
    group = server.add_group('main', WORKER_NUMBER)
    logger.info("抓取任务")
    group.set_handle(callback_handle)
    logger.info("处理任务")
    group.add_input_endpoint('input', input_end)

    # server.add_routine_worker(ebay_maintain_task, interval=5, immediately=True)
    server.run()


if __name__ == '__main__':
    run()
