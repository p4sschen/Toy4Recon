# -*- coding: utf-8 -*-
# @File  : Monitor.py
# @Date  : 2019/4/16
# @Desc  :
# @license : Copyright(C), MIT
# @Author: zhaochengyu
# @Contact : yu5890681@gmail.com
import json
import logging
import socket

from apscheduler.schedulers.background import BackgroundScheduler

from Core.core import Task
from Core.lib import logger
from Worker.Common.configs import *
from Worker.Common.redisHelper import RedisHelper


class Monitor(object):
    def __init__(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("127.0.0.1", 47200))
        except socket.error:
            logger.warning("Monitor 已经启动")
            return
        # 初始化redis实例
        self.redisHelper = RedisHelper()
        self.redis_celery_result_sub = self.redisHelper.subscribe(REDIS_CELERY_RESULT_CHANNEL)

        log = logging.getLogger('apscheduler.scheduler')
        log.setLevel(logging.ERROR)  # 关闭apscheduler的警告
        self.Scheduler = BackgroundScheduler()

        self.Scheduler.add_job(func=self.get_celery_result_scheduler,
                               max_instances=1,
                               trigger='interval',
                               seconds=5,
                               id='get_celery_result_scheduler')
        self.Scheduler.start()
        logger.warning("Monitor 启动完成")

    def get_celery_result_scheduler(self):
        """循环调用函数,用于处理celery结果"""
        try:
            msg = self.redis_celery_result_sub.parse_response()
        except Exception as E:
            logger.warning("redis连接错误")
            return False
        try:
            result = json.loads(msg[2])
            task_id = result.get('task_id')
            status = result.get('status')
            retval = result.get('retval')
            einfo = result.get('einfo')
            logger.info("开始存储任务结果,task_id: {}".format(task_id))
            flag = Task.update_task(task_id=task_id, status=status, retval=retval, einfo=einfo)
            logger.info("存储任务完成,task_id: {}".format(task_id))
            return True
        except Exception as E:
            logger.warning("json解析task结果失败,详细信息: {} 异常:{}".format(msg, E))
