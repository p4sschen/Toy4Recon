import ast

from django.db import models

from Core.lib import logger


# Create your models here.


class DiyListField(models.TextField):
    """数据库中用来存储list类型字段"""
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(DiyListField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):  # 将python对象转为查询值
        if value is None:
            return value

        return str(value)  # use str(value) in Python 3

    def from_db_value(self, value, expression, connection):
        if not value:
            value = []
        if isinstance(value, list):
            return value
        # 直接将字符串转换成python内置的list
        try:
            return ast.literal_eval(value)
        except Exception as E:
            logger.error(value)
            return []

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


class DiyDictField(models.TextField):
    """数据库中用来存储dict类型字段"""
    description = "Stores a python dict"

    def __init__(self, *args, **kwargs):
        super(DiyDictField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):  # 将python对象转为查询值
        if value is None:
            return value

        return str(value)  # use str(value) in Python 3

    def from_db_value(self, value, expression, connection):
        if not value:
            value = []
        if isinstance(value, dict):
            return value
        # 直接将字符串转换成python内置的list
        try:
            return ast.literal_eval(value)
        except Exception as E:
            logger.error(value)
            return {}

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


class ProjectModel(models.Model):
    # 生成所需参数
    TAG = (
        ('default', 'default'),  # 调试
        ('home', "home"),  # 国内
        ('abroad', "abroad"),  # 国外
        ('other', "other"),  # 发布
    )
    tag = models.CharField(choices=TAG, max_length=50, default='other')
    name = models.CharField(blank=True, null=True, max_length=100)
    desc = models.TextField(blank=True, null=True, )


class SettingModel(models.Model):
    """系统配置表"""
    KIND = (
        ('redis', "redis"),  # rabbitmq配置
        ('nginx_file_server', "nginx_file_server"),  # nginx文件服务器配置
    )
    TAG = (
        ('debug', 'debug'),  # 调试
        ('home', "home"),  # 国内
        ('abroad', "abroad"),  # 国外
        ('other', "other"),  # 发布
    )
    activating = models.BooleanField(default=False)
    tag = models.CharField(choices=TAG, max_length=50, default='other')  # 配置类别
    kind = models.CharField(choices=KIND, max_length=50, default='other')  # 配置类别
    setting = DiyDictField(default={})


class TaskModel(models.Model):
    STATES = (
        ('PENDING', 'PENDING'),
        ('STARTED', "STARTED"),
        ('SUCCESS', "SUCCESS"),
        ('FAILURE', "FAILURE"),
        ('RETRY', "RETRY"),
        ('REVOKED', "REVOKED"),
        ('PROGRESS', "PROGRESS"),
        ('STORED', "STORED"),
        ('STOREFAIL', "STOREFAIL"),
    )
    # 输入参数
    pid = models.IntegerField(default=0)
    kind = models.CharField(blank=True, null=True, max_length=100, default=None)  # 配置类别
    kwargs = DiyDictField(default={})
    # 任务参数
    task_id = models.CharField(blank=True, null=True, max_length=150, default=None)
    status = models.CharField(blank=True, null=True, choices=STATES, max_length=50, default='PENDING')
    start_time = models.IntegerField(default=0)
    # 结果参数
    end_time = models.IntegerField(default=0)
