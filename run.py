# encoding=utf-8

import sys
from config import AIOHTTP_PORT
import logging
import argparse
from app import app
from aiohttp import web, log

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i', '--ip', dest='ip', nargs='?', default='0.0.0.0',
                        help='indicate the ip listening on')
    parser.add_argument('-p', '--port', dest='port', nargs='?', default=AIOHTTP_PORT, type=int,
                        help='indicate the port listening on')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, host=args.ip, port=args.port)

