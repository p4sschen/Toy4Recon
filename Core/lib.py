# -*- coding: utf-8 -*-


import logging

from django.core.cache import cache

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('django')


# 返回数据拼装函数,数据拼装应全部放在view模块中进行
def list_data_return(code, message, data):
    # if code == 200 or code == 400 or code == 500 :
    #     pass
    # else:
    #     logger.warning("code不符合规范,参考configs.py状态码")
    if not isinstance(message, str):
        logger.warning("message不符合规范,应为str类型")
    if not isinstance(data, list):
        logger.warning("data不符合规范,应为list类型")
    return {'code': code, 'message': message, 'data': data}


def dict_data_return(code, message, data):
    # if code == 200 or code == 400 or code == 500 :
    #     pass
    # else:
    #     logger.warning("code不符合规范,参考config.py状态码")
    if not isinstance(message, str):
        logger.warning("message不符合规范,应为str类型")
    if not isinstance(data, dict):
        logger.warning("data不符合规范,应为dict类型")
    return {'code': code, 'message': message, 'data': data}


class Xcache(object):
    """因为cache是无法使用线程的,所以类的所有函数都是线程不安全的,这个要注意"""
    XCACHE_SESSION_LOCK = "XCACHE_SESSION_LOCK"
    XCACHE_MODULES_CONFIG = "XCACHE_MODULES_CONFIG"
    XCACHE_SESSION_INFO = "XCACHE_SESSION_INFO"
    XCACHE_SESSION_INFO_ALIVE_TIME = 600  # session 信息默认存活600秒
    XCACHE_SESSION_LIST = "XCACHE_SESSION_LIST"
    XCACHE_SESSION_LIST_ALIVE_TIME = 1  # session_list 信息默认存活3秒
    XCACHE_VIRTUAL_HADLER_LIST = "XCACHE_VIRTUAL_HADLER_LIST"
    XCACHE_SERVICES_STATUS = "XCACHE_SERVICES_STATUS"

    def __init__(self):
        pass

    @staticmethod
    def lock_sessionIO(sessionid):
        sessionid_dict = cache.get(Xcache.XCACHE_SESSION_LOCK)
        if sessionid_dict is None:
            cache.set(Xcache.XCACHE_SESSION_LOCK, {}, None)

        sessionid_dict = cache.get(Xcache.XCACHE_SESSION_LOCK)
        sessionid_dict[sessionid] = True
        return True

    @staticmethod
    def islock_sessionIO(sessionid):

        sessionid_dict = cache.get(Xcache.XCACHE_SESSION_LOCK)
        if sessionid_dict is None:
            cache.set(Xcache.XCACHE_SESSION_LOCK, {}, None)
            return False
        if sessionid_dict.get(sessionid):
            return True
        else:
            return False

    @staticmethod
    def unload_sessionIO(sessionid):
        sessionid_dict = cache.get(Xcache.XCACHE_SESSION_LOCK)
        if sessionid_dict is None:
            cache.set(Xcache.XCACHE_SESSION_LOCK, {}, None)
        sessionid_dict = cache.get(Xcache.XCACHE_SESSION_LOCK)
        if sessionid_dict.get(sessionid):
            del sessionid_dict[sessionid]
        cache.set(Xcache.XCACHE_SESSION_LOCK, sessionid_dict, None)
        return True

    @staticmethod
    def get_modules_config():

        modules_config = cache.get(Xcache.XCACHE_MODULES_CONFIG)
        if modules_config is None:
            return None
        else:
            return modules_config

    @staticmethod
    def set_modules_config(all_modules_config):
        cache.set(Xcache.XCACHE_MODULES_CONFIG, all_modules_config, None)
        return True

    @staticmethod
    def get_one_module_config(loadpath):
        modules_config = cache.get(Xcache.XCACHE_MODULES_CONFIG)
        try:

            for config in modules_config:
                if config.get("loadpath") == loadpath:
                    return config
            return None
        except Exception as E:
            logger.error(E)
            return None

    @staticmethod
    def set_session_info(sessionid, session_info):
        key = "{}_{}".format(Xcache.XCACHE_SESSION_INFO, sessionid)
        cache.set(key, session_info, Xcache.XCACHE_SESSION_INFO_ALIVE_TIME)
        return True

    @staticmethod
    def get_session_info(sessionid):
        key = "{}_{}".format(Xcache.XCACHE_SESSION_INFO, sessionid)
        session_info = cache.get(key)
        return session_info

    @staticmethod
    def set_session_list(session_list):
        cache.set(Xcache.XCACHE_SESSION_LIST, session_list, Xcache.XCACHE_SESSION_LIST_ALIVE_TIME)
        return True

    @staticmethod
    def get_session_list():
        session_list = cache.get(Xcache.XCACHE_SESSION_LIST)
        return session_list

    @staticmethod
    def get_virtual_handlers():
        handler_list = cache.get(Xcache.XCACHE_VIRTUAL_HADLER_LIST)
        if handler_list is None:
            handler_list = []
        return handler_list

    @staticmethod
    def add_virtual_handler(onehandler):
        handler_list = cache.get(Xcache.XCACHE_VIRTUAL_HADLER_LIST)
        if handler_list is None:
            handler_list = []
        handler_id = -(len(handler_list) + 1)
        onehandler['ID'] = handler_id
        handler_list.append(onehandler)
        cache.set(Xcache.XCACHE_VIRTUAL_HADLER_LIST, handler_list, None)
        return handler_id

    @staticmethod
    def del_virtual_handler(virtual_id):
        handler_list = cache.get(Xcache.XCACHE_VIRTUAL_HADLER_LIST)
        if handler_list is None:
            handler_list = []
            cache.set(Xcache.XCACHE_VIRTUAL_HADLER_LIST, handler_list, None)
            return False
        for onehandler in handler_list:
            if onehandler.get('ID') == virtual_id:
                handler_list.remove(onehandler)
        cache.set(Xcache.XCACHE_VIRTUAL_HADLER_LIST, handler_list, None)
        return True

    @staticmethod
    def get_services_status():
        services_status = cache.get(Xcache.XCACHE_SERVICES_STATUS)
        return services_status

    @staticmethod
    def set_services_status(services_status):
        cache.set(Xcache.XCACHE_SERVICES_STATUS, services_status, None)
        return True
