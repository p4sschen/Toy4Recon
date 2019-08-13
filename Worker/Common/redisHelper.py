# -*- coding: utf-8 -*-
# @File  : RedisHelper.py
# @Date  : 2019/4/16
# @Desc  :
# @license : Copyright(C), MIT
# @Author: zhaochengyu
# @Contact : yu5890681@gmail.com

import redis

from CONFIG import *


class RedisHelper:

    def __init__(self):
        pool = redis.ConnectionPool(host=REDIS_HOST,
                                    port=REDIS_PORT,
                                    password=REDIS_PASSWORD,
                                    db=1,
                                    )
        self.__conn = redis.StrictRedis(connection_pool=pool)

    def public(self, channel, msg):
        result = self.__conn.publish(channel, msg)
        return result

    def subscribe(self, channel):
        pub = self.__conn.pubsub()
        pub.subscribe(channel)
        pub.parse_response()  # 去除初始化消息
        return pub
