from django.db import models

# Create your models here.
from Core.models import DiyDictField, DiyListField


class IPaddressModel(models.Model):
    pid = models.IntegerField(default=0)
    ipaddress = models.CharField(blank=True, null=True, max_length=20, default=None)
    os = models.CharField(blank=True, null=True, max_length=100, default=None)
    hostname = models.CharField(blank=True, null=True, max_length=255, default=None)
    domain = models.CharField(blank=True, null=True, max_length=255, default=None)
    update_time = models.IntegerField(default=0)


class PortModel(models.Model):
    ipid = models.IntegerField(default=0)
    port = models.IntegerField(default=0)
    service = models.CharField(blank=True, null=True, max_length=100, default=None)
    info = DiyDictField(default={})
    update_time = models.IntegerField(default=0)


class WebsiteModel(models.Model):
    """实际域名(子域名),例如cc.faw.com.cn,"""
    pid = models.IntegerField(default=0)
    # 主域,例如faw.com.cn
    domain = models.CharField(blank=True, null=True, max_length=255, default=None)
    # 网址,例如cc.faw.com.cn
    website = models.CharField(blank=True, null=True, max_length=1024, default=None)
    alive = models.BooleanField(blank=True, null=True, default=None)
    update_time = models.IntegerField(default=0)


class WebsiteTechModel(models.Model):
    wid = models.IntegerField(default=0)
    name = models.CharField(blank=True, null=True, max_length=200)
    version = models.CharField(blank=True, null=True, max_length=200)
    icon = models.CharField(blank=True, null=True, max_length=200)
    update_time = models.IntegerField(default=0)


class WebsiteWafModel(models.Model):
    wid = models.IntegerField(default=0)
    hasWaf = models.BooleanField(blank=True, null=True, default=None)
    waf = models.CharField(blank=True, null=True, max_length=200)
    detect_tech = models.CharField(blank=True, null=True, max_length=200)
    update_time = models.IntegerField(default=0)


class WebsiteCDNModel(models.Model):
    wid = models.IntegerField(default=0)
    hascdn = models.BooleanField(blank=True, null=True, default=None)
    ipaddress = DiyListField(default=[])
    title = models.TextField(blank=True, null=True)
    update_time = models.IntegerField(default=0)
