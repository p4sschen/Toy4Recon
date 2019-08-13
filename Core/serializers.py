# -*- coding: utf-8 -*-

from rest_framework.serializers import *

from Core.models import *


class ProjectSerializer(ModelSerializer):
    class Meta(object):
        model = ProjectModel
        fields = '__all__'


class SettingSerializer(Serializer):
    id = IntegerField()
    activating = BooleanField()
    tag = CharField(max_length=100)
    kind = CharField(max_length=100)
    setting = DictField()


class TaskSerializer(Serializer):
    id = IntegerField()
    pid = models.IntegerField()
    task_id = CharField(max_length=150)
    kind = CharField(max_length=100)
    kwargs = DictField()
    status = CharField(max_length=50)
    start_time = IntegerField()
    end_time = IntegerField()
