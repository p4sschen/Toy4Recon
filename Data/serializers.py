# -*- coding: utf-8 -*-

from rest_framework.serializers import *

from Data.models import *


class IPaddressSerializer(ModelSerializer):
    class Meta(object):
        model = IPaddressModel
        fields = '__all__'


class PortSerializer(Serializer):
    id = IntegerField()
    ipid = IntegerField()
    port = IntegerField()
    service = CharField(max_length=100)
    info = DictField()
    update_time = IntegerField()


class WebsiteSerializer(ModelSerializer):
    class Meta(object):
        model = WebsiteModel
        fields = '__all__'


class WebsiteTechSerializer(ModelSerializer):
    class Meta(object):
        model = WebsiteTechModel
        fields = '__all__'


class WebsiteWafSerializer(ModelSerializer):
    class Meta(object):
        model = WebsiteWafModel
        fields = '__all__'


class WebsiteCDNSerializer(Serializer):
    id = IntegerField()
    wid = IntegerField()
    hascdn = BooleanField()
    title = CharField(max_length=500)
    ipaddress = ListField(default=[])
    update_time = IntegerField()
