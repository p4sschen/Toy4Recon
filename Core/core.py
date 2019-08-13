# -*- coding: utf-8 -*-


import datetime
import json
import time

from django.db import transaction
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from Core.celeryTask import CeleryTask
from Core.configs import *
from Core.lib import *
from Core.serializers import *
from Data.data import IPaddress, Website


class BaseAuth(TokenAuthentication):
    def authenticate_credentials(self, key):
        # Search token in cache
        cache_user = cache.get(key)
        if cache_user:
            return cache_user, key

        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed()

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed()

        time_now = datetime.datetime.now()

        if token.created < time_now - datetime.timedelta(minutes=EXPIRE_MINUTES):
            token.delete()
            raise exceptions.AuthenticationFailed()

        if token:
            # Cache token
            cache.set(key, token.user, EXPIRE_MINUTES * 60)

        return token.user, token


class CurrentUser(object):
    def __init__(self):
        pass

    @staticmethod
    def list(user):
        current_info = {
            'name': user.username,
            'avatar': 'user',
            'userid': user.id,
            'email': 'Toy4Recon',
            'signature': '海纳百川，有容乃大',
            'title': '安全专家',
            'group': '某某某事业群－某某平台部－某某技术部－UED',
            'tags': [
                {
                    'key': '0',
                    'label': '很有想法的',
                },
                {
                    'key': '5',
                    'label': '海纳百川',
                },
            ],
            'notifyCount': 12,
            'unreadCount': 0,
            'country': 'China',
            'geographic': {
                'province': {
                    'label': '辽宁省',
                    'key': '330000',
                },
                'city': {
                    'label': '沈阳市',
                    'key': '330100',
                },
            },
            'address': 'Nowhere',
            'phone': '000-888888888'
        }

        return current_info


class Settings(object):
    def __init__(self):
        pass

    @staticmethod
    def list(kind, activated):
        if activated is True or activated == 'true':
            # 获取激活的配置
            try:
                model = SettingModel.objects.get(kind=kind, activating=True)
                result = SettingSerializer(model, many=False).data
                result = Settings._deal_pasword_field(result, 'RPC_TOKEN')
                CODE = 200
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
                return context
            except Exception as E:
                CODE = 404
                logger.warning(E)
                logger.warning("存在多个激活配置")
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
                return context

        models = SettingModel.objects.filter(kind=kind)
        result = SettingSerializer(models, many=True).data
        result = Settings._deal_pasword_field(result, 'RPC_TOKEN')
        CODE = 200
        context = list_data_return(CODE, CODE_MESSAGE.get(CODE), result)
        return context

    @staticmethod
    def list_activated_setting(kind):
        try:
            model = SettingModel.objects.get(kind=kind, activating=True)
            result = SettingSerializer(model, many=False).data
            return result
        except Exception as E:
            return None

    @staticmethod
    def create(kind, tag, setting):
        if isinstance(setting, str):
            setting = json.loads(setting)

        defaultDict = {'kind': kind, 'tag': tag, 'setting': setting, }  # 没有该主机数据时新建
        model, created = SettingModel.objects.get_or_create(kind=kind, setting=setting, defaults=defaultDict)
        if created is True:
            result = SettingSerializer(model, many=False).data
            CODE = 201
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
            return context
        # 有历史数据
        with transaction.atomic():
            try:
                model = SettingModel.objects.select_for_update().get(id=model.id)
                model.tag = tag
                model.save()
                result = SettingSerializer(model, many=False).data
                CODE = 201
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
                return context
            except Exception as E:
                logger.error(E)
                result = SettingSerializer(model, many=False).data
                CODE = 405
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
                return context

    @staticmethod
    def update(id, activating, tag, setting):
        if activating is True:
            # 配置激活流程
            try:
                model = SettingModel.objects.get(id=id)
                models = SettingModel.objects.filter(kind=model.kind).update(activating=False)
                model.activating = True
                model.save()
                result = SettingSerializer(model, many=False).data
                CODE = 201
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
                return context
            except Exception as E:
                logger.warning(E)
                logger.warning("尝试激活不存在的配置")
                CODE = 405
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
                return context
        else:
            # 更新配置流程
            defaultDict = {'id': id, 'tag': tag, 'setting': setting}  # 没有该主机数据时新建
            model, created = SettingModel.objects.get_or_create(id=id, defaults=defaultDict)
            if created is True:
                result = SettingSerializer(model, many=False).data
                CODE = 201
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
                return context
            # 有历史数据
            with transaction.atomic():
                try:
                    model = SettingModel.objects.select_for_update().get(id=id)
                    model.tag = tag
                    model.setting = setting
                    model.save()
                    result = SettingSerializer(model, many=False).data
                    CODE = 201
                    context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
                    return context
                except Exception as E:
                    logger.error(E)
                    result = SettingSerializer(model, many=False).data
                    CODE = 405
                    context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
                    return context

    @staticmethod
    def destory(id):
        try:
            row_cont, row_cont_dict = SettingModel.objects.filter(id=id).delete()
            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return context

    @staticmethod
    def _deal_pasword_field(data, field):
        if isinstance(data, dict):
            setting = data.get('setting')
            oldstr = data.get('setting').get(field)
            if len(oldstr) <= 3:
                pass
            else:
                data['setting'][field] = oldstr[0:3] + "*************"
            return data
        elif isinstance(data, list):
            for one in data:
                setting = one.get('setting')
                oldstr = one.get('setting').get(field)
                if len(oldstr) <= 3:
                    pass
                else:
                    one['setting'][field] = oldstr[0:3] + "*************"
            return data
        else:
            return data


class Project(object):

    def __init__(self):
        pass

    @staticmethod
    def list():
        Project._check_defalut_project_exist()
        models = ProjectModel.objects.all()
        result = ProjectSerializer(models, many=True).data
        CODE = 200
        context = list_data_return(CODE, CODE_MESSAGE.get(CODE), result)
        return context

    @staticmethod
    def create(tag, name, desc):
        defaultDict = {'tag': tag, 'name': name, 'desc': desc, }  # 没有该主机数据时新建
        model, created = ProjectModel.objects.get_or_create(tag=tag, name=name, desc=desc, defaults=defaultDict)
        if created is True:
            result = ProjectSerializer(model, many=False).data
            CODE = 201
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
            return context
        else:
            result = ProjectSerializer(model, many=False).data
            CODE = 201
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
            return context

    @staticmethod
    def update(id, tag, name, desc):
        try:
            model = ProjectModel.objects.get(id=id)
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context
        if id == 0:
            model.tag = 'default'
        else:
            if model.tag == 'default':
                model.tag = 'other'
            else:
                model.tag = tag

        model.name = name
        model.desc = desc
        model.save()
        result = ProjectSerializer(model, many=False).data
        CODE = 201
        context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
        return context

    @staticmethod
    def destory(id):
        # 删除本表信息

        try:
            model = ProjectModel.objects.get(id=id)
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context
        try:
            row_cont, row_cont_dict = ProjectModel.objects.filter(id=id).delete()
            # 删除关联表信息
            IPaddress.destory_by_pid(id)
            Task.destory_by_pid(id)
            Website.destory_by_pid(id)

            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context

        except Exception as E:
            logger.error(E)
            CODE = 406
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context

    @staticmethod
    def _check_defalut_project_exist():
        """检查默认项目是否存在"""
        if ProjectModel.objects.filter(id=0).count() < 1:
            model = ProjectModel()
            model.id = 0
            model.tag = 'default'
            model.name = '默认项目'
            model.desc = '该项目为系统默认项目'
            model.save()


class Task(object):

    def __init__(self):
        pass

    @staticmethod
    def list(pid):
        models = TaskModel.objects.filter(pid=pid).order_by('start_time').reverse()
        result = TaskSerializer(models, many=True).data
        CODE = 200
        for one in result:
            start_time = one.get('start_time')
            end_time = one.get('end_time')

            if end_time is None or end_time <= 0:
                used_time = int(time.time()) - start_time
            else:
                used_time = end_time - start_time
            one['used_time'] = used_time
        context = list_data_return(CODE, CODE_MESSAGE.get(CODE), result)
        return context

    @staticmethod
    def create(pid, kind, kwargs):
        defaultDict = {'pid': pid, 'kind': kind, 'kwargs': kwargs, }  # 没有该主机数据时新建
        model, created = TaskModel.objects.get_or_create(pid=pid, kind=kind, kwargs=kwargs, defaults=defaultDict)
        if created is True:
            task_id = CeleryTask.call_task(kind=kind, kwargs=kwargs)
            if task_id is not None:
                model.task_id = task_id
                model.status = 'PENDING'
                model.start_time = int(time.time())
                model.save()
                result = TaskSerializer(model, many=False).data
                CODE = 201
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
            else:
                CODE = 405
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context
        else:
            if model.status in ['PENDING', 'STARTED', 'PROGRESS']:
                result = TaskSerializer(model, many=False).data
                CODE = 201
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
            else:
                task_id = CeleryTask.call_task(kind=kind, kwargs=kwargs)
                if task_id is not None:
                    model.task_id = task_id
                    model.status = 'PENDING'
                    model.start_time = int(time.time())
                    model.end_time = 0
                    model.save()
                    result = TaskSerializer(model, many=False).data
                    CODE = 201
                    context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), result)
                else:
                    CODE = 405
                    context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context

    @staticmethod
    def update_task(task_id, status, retval, einfo):
        try:
            model = TaskModel.objects.get(task_id=task_id)
        except Exception as E:
            logger.warning("未找到对应的task信息,task: {} exception: {}".format(task_id, E))
            return False
        # 调用task回调函数
        if status == "SUCCESS" or status == b"SUCCESS":
            flag = CeleryTask.result_callback(model.pid, model.kind, retval)
            if flag is True:
                model.status = 'STORED'
                model.end_time = int(time.time())
                model.save()
                return True
            else:
                logger.warning("存储任务结果失败,task_id: {},kind: {},retval: {}".format(task_id, model.kind, retval))
                model.status = 'STOREFAIL'
                model.end_time = int(time.time())
                model.save()
                return False
        else:
            logger.warning("任务执行失败,task_id: {},status: {},einfo: {}".format(task_id, status, einfo))
            model.status = status
            model.end_time = int(time.time())
            model.save()
            return False

    @staticmethod
    def destory(id):
        try:
            model = TaskModel.objects.get(id=id)
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context
        if model.status in ['STARTED', 'PROGRESS']:
            CODE = 400
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context

        try:
            row_cont, row_cont_dict = TaskModel.objects.filter(id=id).delete()
            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context

        except Exception as E:
            logger.error(E)
            CODE = 406
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
            return context

    @staticmethod
    def destory_by_pid(pid):
        try:
            row_cont, row_cont_dict = TaskModel.objects.filter(pid=pid).delete()
            return row_cont
        except Exception as E:
            logger.error(E)
            return None
