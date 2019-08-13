# -*- coding: utf-8 -*-
# @File  : CeleryApps.py
# @Date  : 2019/4/16
# @Desc  :
# @license : Copyright(C), MIT
# @Author: zhaochengyu
# @Contact : yu5890681@gmail.com


# from celery import current_app
# current_app.conf.CELERY_ALWAYS_EAGER = True
# current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

from celery import Celery

from Worker.Common.redisHelper import RedisHelper

redisHelper = RedisHelper()

templateApp = Celery('template')
templateApp.config_from_object("Worker.Common.celeryConfig")
