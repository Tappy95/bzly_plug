import json
import re
import time
from datetime import datetime

import operator
from aiohttp import web
from sqlalchemy import text, select, and_

from models.alchemy_models import MUserInfo, AlchemyEncoder
from util.log import logger
from util.static_methods import category_tree, date_range, get_category_names, check_effect_category

routes = web.RouteTableDef()


@routes.get('/index_name')
async def index_name(request):
    conn = request['db_connection']
    result = conn.query(MUserInfo).all()
    print(json.dumps(result, cls=AlchemyEncoder, ensure_ascii=False))
