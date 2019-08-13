# -*- coding: utf-8 -*-
# @File  : data.py
# @Date  : 2019/4/17
# @Desc  :
# @license : Copyright(C), MIT
# @Author: zhaochengyu
# @Contact : yu5890681@gmail.com
import re
import time

from django.db import transaction

from Core.configs import *
from Core.lib import logger, list_data_return, dict_data_return
from Data.serializers import *


class IPaddress(object):
    def __init__(self):
        pass

    @staticmethod
    def list(pid):
        models = IPaddressModel.objects.filter(pid=pid)
        ipaddresses = IPaddressSerializer(models, many=True).data
        # 添加ports信息
        for ipaddress in ipaddresses:
            ports = Port.list_port(ipaddress.get('id'))
            ipaddress['ports'] = ports

        CODE = 200
        context = list_data_return(CODE, CODE_MESSAGE.get(CODE), ipaddresses)
        return context

    @staticmethod
    def update_ipaddress(pid, ipaddress, domain=None):
        defaultDict = {'pid': pid, 'ipaddress': ipaddress, 'domain': domain,
                       'update_time': int(time.time())}  # 没有该主机数据时新建
        model, created = IPaddressModel.objects.get_or_create(pid=pid, ipaddress=ipaddress, defaults=defaultDict)
        if created is True:
            result = IPaddressSerializer(model, many=False).data
            return result
        else:
            result = IPaddressSerializer(model, many=False).data
            return result

    @staticmethod
    def update_ipaddress_os(id, os):
        defaultDict = {'id': id, 'os': os, }  # 没有该主机数据时新建
        model, created = IPaddressModel.objects.get_or_create(id=id, defaults=defaultDict)
        if created is True:
            result = IPaddressSerializer(model, many=False).data
            return result
        else:
            model.os = os
            model.save()
            result = IPaddressSerializer(model, many=False).data
            return result

    @staticmethod
    def update_ipaddress_hostname(id, hostname):
        defaultDict = {'id': id, 'hostname': hostname, }  # 没有该主机数据时新建
        model, created = IPaddressModel.objects.get_or_create(id=id, defaults=defaultDict)
        if created is True:
            result = IPaddressSerializer(model, many=False).data
            return result
        else:
            model.hostname = hostname
            model.save()
            result = IPaddressSerializer(model, many=False).data
            return result

    @staticmethod
    def destory_by_pid(pid):
        try:
            models = IPaddressModel.objects.filter(pid=pid)
            for model in models:
                Port.destory_by_ipid(model.id)
            models.delete()

            return True
        except Exception as E:
            logger.error(E)
            return False

    @staticmethod
    def destory(id):
        try:
            model = IPaddressModel.objects.get(id=id)
            model.delete()
            Port.destory_by_ipid(id)
            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return context


class Port(object):
    def __init__(self):
        pass

    @staticmethod
    def list(ipid):
        result = Port.list_port(ipid)
        CODE = 200
        context = list_data_return(CODE, CODE_MESSAGE.get(CODE), result)
        return context

    @staticmethod
    def list_port(ipid):
        models = PortModel.objects.filter(ipid=ipid).order_by("port")
        result = PortSerializer(models, many=True).data
        result = Port.remove_x00(result)
        return result

    @staticmethod
    def remove_x00(result):
        for one in result:
            try:
                if one.get('info').get('hostname') is not None and len(one.get('info').get('hostname')) > 0:
                    one['info']['hostname'] = [one['info']['hostname'][0].replace('\x00', '')]
                if one.get('info').get('info') is not None and len(one.get('info').get('info')) > 0:
                    one['info']['info'] = [one['info']['info'][0].replace('\x00', '')]
            except Exception as E:
                logger.error(E)
                continue
        return result

    @staticmethod
    def update_port(ipid, port, service, info):
        defaultDict = {'ipid': ipid,
                       'port': port,
                       'service': service,
                       'info': info,
                       'update_time': int(time.time()), }  # 没有该主机数据时新建
        model, created = PortModel.objects.get_or_create(ipid=ipid, port=port, defaults=defaultDict)
        if created is True:
            result = PortSerializer(model, many=False).data
        with transaction.atomic():
            try:
                model = PortModel.objects.select_for_update().get(id=model.id)
                model.service = service
                model.info = info
                model.update_time = int(time.time())
                model.save()
                result = PortSerializer(model, many=False).data
            except Exception as E:
                logger.error(E)
                result = PortSerializer(model, many=False).data

        # 解析OS信息及hostname

        try:
            if result.get('info').get('operatingsystem') is not None and \
                    len(result.get('info').get('operatingsystem')) > 0:
                IPaddress.update_ipaddress_os(ipid, result.get('info').get('operatingsystem')[0])
            if result.get('info').get('hostname') is not None and \
                    len(result.get('info').get('hostname')) > 0:
                hostname = result.get('info').get('hostname')[0].replace('\x00', '')
                IPaddress.update_ipaddress_hostname(ipid, hostname)
        except Exception as E:
            logger.error(E)
        return result

    @staticmethod
    def destory_by_ipid(ipid):
        row_cont, row_cont_dict = PortModel.objects.filter(ipid=ipid).delete()
        return row_cont

    @staticmethod
    def destory(id):
        try:
            model = PortModel.objects.get(id=id)
            model.delete()
            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return context


class Website(object):
    def __init__(self):
        pass

    @staticmethod
    def list(pid):
        models = WebsiteModel.objects.filter(pid=pid)
        websites = WebsiteSerializer(models, many=True).data

        for website in websites:
            # 添加WebsiteTech信息
            website['tech'] = WebsiteTech.list_by_wid(website.get('id'))
            # 添加waf信息
            wafinfo = WebsiteWaf.get_by_wid(website.get('id'))
            website['hasWaf'] = wafinfo.get('hasWaf')
            website['waf'] = wafinfo.get('waf')
            website['detect_tech'] = wafinfo.get('detect_tech')

            cdninfo = WebsiteCDN.get_by_wid(website.get('id'))
            website['hascdn'] = cdninfo.get('hascdn')
            website['ipaddress'] = cdninfo.get('ipaddress')
            website['title'] = cdninfo.get('title')
        CODE = 200
        context = list_data_return(CODE, CODE_MESSAGE.get(CODE), websites)
        return context

    @staticmethod
    def create(pid, domain, websites):
        def websites_str_to_list(websitesStr):
            websites = []
            templist = re.split('[,\n]', websitesStr)
            for one in templist:
                if re.search("(?:[-\w.]|(?:%[\da-fA-F]{2}))+", one):
                    websites.append(one)
            return websites

        websites = websites_str_to_list(websites)
        count = Website.import_websites(pid, domain, websites)
        CODE = 201
        context = list_data_return(CODE, CODE_MESSAGE.get(CODE), {'count': count})
        return context

    @staticmethod
    def import_websites(pid, domain, websites):
        """导入的域名"""
        count = 0
        for website in websites:
            defaultDict = {'pid': pid, 'domain': domain, 'website': website,
                           'update_time': int(time.time())}  # 没有该主机数据时新建
            model, created = WebsiteModel.objects.update_or_create(pid=pid, domain=domain, website=website,
                                                                   defaults=defaultDict)
            if created is True:
                count = count + 1
        return count

    @staticmethod
    def update_website(pid, domain, website):
        defaultDict = {'pid': pid, 'domain': domain, 'website': website, 'update_time': int(time.time())}  # 没有该主机数据时新建
        model, created = WebsiteModel.objects.update_or_create(pid=pid, domain=domain, website=website,
                                                               defaults=defaultDict)
        result = WebsiteSerializer(model, many=False).data
        return result

    @staticmethod
    def update_website_alive(id, alive):
        try:
            model = WebsiteModel.objects.filter(id=id).update(alive=alive, update_time=int(time.time()))
            return True
        except Exception as E:
            return None

    @staticmethod
    def get_wid_by_website(pid, website):
        try:
            model = WebsiteModel.objects.get(pid=pid, website=website)
            return model.id
        except Exception as E:
            return None

    @staticmethod
    def destory_by_pid(pid):
        try:
            models = WebsiteModel.objects.filter(pid=pid)
            # 删除关联表
            for model in models:
                id = model.id
                WebsiteTech.destory_by_wid(id)
                WebsiteTech.destory_by_wid(id)
                WebsiteWaf.destory_by_wid(id)
                WebsiteCDN.destory_by_wid(id)
            models.delete()
            return True
        except Exception as E:
            logger.error(E)
            return False

    @staticmethod
    def destory(id):
        try:
            model = WebsiteModel.objects.get(id=id)
            model.delete()
            # 删除关联表
            WebsiteTech.destory_by_wid(id)
            WebsiteWaf.destory_by_wid(id)
            WebsiteCDN.destory_by_wid(id)
            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return context


class WebsiteTech(object):
    def __init__(self):
        pass

    @staticmethod
    def list(wid):
        models = WebsiteTechModel.objects.filter(wid=wid)
        websiteTechs = WebsiteTechSerializer(models, many=True).data

        CODE = 200
        context = list_data_return(CODE, CODE_MESSAGE.get(CODE), websiteTechs)
        return context

    @staticmethod
    def list_by_wid(wid):
        models = WebsiteTechModel.objects.filter(wid=wid)
        websiteTechs = WebsiteTechSerializer(models, many=True).data
        return websiteTechs

    @staticmethod
    def update_website_tech(wid, name, version, icon):
        defaultDict = {'wid': wid, 'name': name, 'version': version, 'icon': icon,
                       'update_time': int(time.time())}  # 没有该主机数据时新建
        model, created = WebsiteTechModel.objects.update_or_create(wid=wid, name=name, defaults=defaultDict)
        result = WebsiteTechSerializer(model, many=False).data
        return result

    @staticmethod
    def destory_by_wid(wid):
        try:
            models = WebsiteTechModel.objects.filter(wid=wid)

            models.delete()
            return True
        except Exception as E:
            logger.error(E)
            return False

    @staticmethod
    def destory(id):
        try:
            model = WebsiteTechModel.objects.get(id=id)
            model.delete()

            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return context


class WebsiteWaf(object):
    def __init__(self):
        pass

    @staticmethod
    def get_by_wid(wid):
        defaultDict = {
            'wid': wid,
            'hasWaf': None,
            'waf': None,
            'detect_tech': None,
            'update_time': int(time.time())
        }
        model, created = WebsiteWafModel.objects.get_or_create(wid=wid, defaults=defaultDict)
        result = WebsiteWafSerializer(model, many=False).data
        return result

    @staticmethod
    def update_website_waf(wid, hasWaf, waf, detect_tech):
        defaultDict = {
            'wid': wid,
            'hasWaf': hasWaf,
            'waf': waf,
            'detect_tech': detect_tech,
            'update_time': int(time.time())
        }  # 没有该主机数据时新建
        model, created = WebsiteWafModel.objects.update_or_create(wid=wid, defaults=defaultDict)
        result = WebsiteWafSerializer(model, many=False).data
        return result

    @staticmethod
    def destory_by_wid(wid):
        try:
            models = WebsiteWafModel.objects.filter(wid=wid)

            models.delete()
            return True
        except Exception as E:
            logger.error(E)
            return False

    @staticmethod
    def destory(id):
        try:
            model = WebsiteWafModel.objects.get(id=id)
            model.delete()
            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return context


class WebsiteCDN(object):
    def __init__(self):
        pass

    @staticmethod
    def get_by_wid(wid):
        defaultDict = {
            'wid': wid,
            'hascdn': None,
            'ipaddress': [],
            'title': None,
            'update_time': int(time.time())
        }
        model, created = WebsiteCDNModel.objects.get_or_create(wid=wid, defaults=defaultDict)
        result = WebsiteCDNSerializer(model, many=False).data
        return result

    @staticmethod
    def update_website_cdn(wid, hascdn, ipaddress, title=None):
        defaultDict = {
            'wid': wid,
            'hascdn': hascdn,
            'ipaddress': ipaddress,
            'title': title,
            'update_time': int(time.time())
        }

        model, created = WebsiteCDNModel.objects.update_or_create(wid=wid, defaults=defaultDict)
        result = WebsiteCDNSerializer(model, many=False).data
        return result

    @staticmethod
    def destory_by_wid(wid):
        try:
            models = WebsiteCDNModel.objects.filter(wid=wid)

            models.delete()
            return True
        except Exception as E:
            logger.error(E)
            return False

    @staticmethod
    def destory(id):
        try:
            model = WebsiteCDNModel.objects.get(id=id)
            model.delete()
            CODE = 204
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            CODE = 404
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return context
