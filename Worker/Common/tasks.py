# -*- coding: utf-8 -*-
# @File  : tasks.py
# @Date  : 2019/4/16
# @Desc  :
# @license : Copyright(C), MIT
# @Author: zhaochengyu
# @Contact : yu5890681@gmail.com

import json
import logging

from celery import Task
from celery.worker.request import Request

from Worker.Common.celeryApps import templateApp, redisHelper
from Worker.Common.configs import *
from Worker.PortScan import portScan
from Worker.Sublist3r import sublist3r

logger = logging.getLogger('celery.worker')


class TemplateRequest(Request):
    'A minimal custom request to log failures and hard time limits.'

    def on_timeout(self, soft, timeout):
        super(TemplateRequest, self).on_timeout(soft, timeout)
        if not soft:
            logger.warning(
                'A hard timeout was enforced for task %s',
                self.task.name
            )

    def on_failure(self, exc_info, send_failed_event=True, return_ok=False):
        super(TemplateRequest, self).on_failure(
            exc_info,
            send_failed_event=send_failed_event,
            return_ok=return_ok
        )
        logger.warning(
            'Failure detected for task %s',
            self.task.name
        )


class TemplateTask(Task):
    Request = TemplateRequest

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logging.info('on_retry,task_id: {} exc:{}'.format(task_id, exc))

    def on_success(self, retval, task_id, args, kwargs):
        logging.debug('on_success,task_id: {} retval:{}'.format(task_id, retval))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error('on_failure,task_id: {} exc:{} einfo:{}'.format(task_id, exc, einfo))

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        logging.info('after_return,task_id: {} status:{}'.format(task_id, status))
        try:
            message = json.dumps({
                'task_id': task_id,
                'status': status,
                'retval': retval,
                'einfo': einfo, })
            result = redisHelper.public(REDIS_CELERY_RESULT_CHANNEL, message)
        except Exception as E:
            logging.error(E)


@templateApp.task(base=TemplateTask)
def portScan_task(startip, stopip, domain, port_list=[], timeout=3):
    return portScan.worker_entry(startip, stopip, port_list, timeout, domain)


@templateApp.task(base=TemplateTask)
def sublist3r_task(domain, bruteforce=False):
    return sublist3r.worker_entry(domain=domain, bruteforce=bruteforce)


@templateApp.task(base=TemplateTask)
def webcheck_task(websites):
    from Worker.WebCheck import webcheck
    return webcheck.worker_entry(websites=websites)
