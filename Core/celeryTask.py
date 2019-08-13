# -*- coding: utf-8 -*-

from django.core.cache import cache

from Core.configs import CELERY_TASK_INSTANCE
from Core.lib import logger
from Data.data import IPaddress, Port, Website, WebsiteTech, WebsiteWaf, WebsiteCDN

# 注册Task关键字
PORTSCAN = 'PortScan'
SUBDOMAIN = 'SubDomain'
WEBCHECK = 'WebCheck'


class CeleryTask(object):
    @staticmethod
    def call_task(kind, kwargs, expires=3600):
        """用于建立task任务"""
        logger.info("建立任务,kind: {} kwargs:{}".format(kind, kwargs))
        try:
            task_instance = CeleryTask._get_celery_task_instance(kind)
            result = task_instance.apply_async(kwargs=kwargs, expires=expires)
            return result.task_id
        except Exception as E:
            logger.error("未找到对应的任务实例,kind: {} Except:{}".format(kind, E))
            return None

    @staticmethod
    def _get_celery_task_instance(kind):
        task_instance = cache.get("{}{}".format(kind, CELERY_TASK_INSTANCE))
        # 初始化task实例
        if task_instance is None:
            if kind == PORTSCAN:
                from Worker.Common.tasks import portScan_task
                cache.set("{}{}".format(PORTSCAN, CELERY_TASK_INSTANCE), portScan_task, None)
                return portScan_task
            elif kind == SUBDOMAIN:
                from Worker.Common.tasks import sublist3r_task
                cache.set("{}{}".format(SUBDOMAIN, CELERY_TASK_INSTANCE), sublist3r_task, None)
                return sublist3r_task
            elif kind == WEBCHECK:
                from Worker.Common.tasks import webcheck_task
                cache.set("{}{}".format(WEBCHECK, CELERY_TASK_INSTANCE), webcheck_task, None)
                return webcheck_task
            else:
                return None
        else:
            return task_instance

    @staticmethod
    def result_callback(pid, kind, retval):
        """调用定义好的回调函数"""
        try:
            if kind == PORTSCAN:
                flag = CeleryTask._port_scan_store(pid, retval)
                return flag
            elif kind == SUBDOMAIN:
                flag = CeleryTask._sub_domain_store(pid, retval)
                return flag
            elif kind == WEBCHECK:
                flag = CeleryTask._webcheck_store(pid, retval)
                return flag
            else:
                logger.error("未找到对应的回调函数,kind: {}".format(kind))
                return False
        except Exception as E:
            logger.error("存储结果失败,异常信息为:{}".format(E))

            return False

    @staticmethod
    def _port_scan_store(pid, retval):
        logger.info("portscan 存储结果: {} {}".format(pid, retval))
        format_result = {}
        scanResult = retval.get('result')
        domain = retval.get('domain')
        try:
            for one in scanResult:
                if one.get('data').get('error') is None:
                    if one.get('data').get('versioninfo') is None:
                        info = {}
                    else:
                        info = one.get('data').get('versioninfo')
                    if format_result.get(one.get('ipaddress')) is None:

                        format_result[one.get('ipaddress')] = [{'port': one.get('port'),
                                                                'service': one.get('data').get('service'),
                                                                'info': info
                                                                }]
                    else:
                        format_result[one.get('ipaddress')].append({'port': one.get('port'),
                                                                    'service': one.get('data').get('service'),
                                                                    'info': info
                                                                    })
                else:  # 扫描中包含错误
                    pass
            for ipaddress in format_result:
                ipaddress_update_result = IPaddress.update_ipaddress(pid=pid, ipaddress=ipaddress, domain=domain)
                ipid = ipaddress_update_result.get('id')
                ports = format_result.get(ipaddress)
                for port in ports:
                    port_update_result = Port.update_port(ipid=ipid,
                                                          port=port.get('port'),
                                                          service=port.get('service'),
                                                          info=port.get('info'))
                    # 更新
                    webServiceList = ['http', 'https']
                    if port.get('service') in webServiceList:
                        # 更新web服务到website
                        websiteWithIPaddress = "{}:{}".format(ipaddress, port.get('port'))
                        Website.update_website(pid=pid, domain=domain, website=websiteWithIPaddress)



        except Exception as E:
            logger.error("存储结果失败,异常: {}".format(E))
            return False
        return True

    @staticmethod
    def _sub_domain_store(pid, retval):
        logger.info("subdomain 存储结果: {} {}".format(pid, retval))
        domain = retval.get('domain')
        subdomains = retval.get('subdomain')
        try:
            for website in subdomains:
                Website.update_website(pid=pid, domain=domain, website=website)
        except Exception as E:
            logger.error("存储结果失败,异常: {}".format(E))
            return False
        return True

    @staticmethod
    def _webcheck_store(pid, retval):
        logger.info("wafw00f 存储结果: {} {}".format(pid, retval))
        for one in retval:
            website = one.get('website')
            wid = Website.get_wid_by_website(pid, website)
            if wid is None:
                logger.warning("数据库中无法找到网站:{}".format(website))
                continue
            else:
                # 更新网站存活信息
                Website.update_website_alive(wid, one.get('alive'))
                # 更新cdn信息
                WebsiteCDN.update_website_cdn(wid=wid, hascdn=one.get('hascdn'), ipaddress=one.get('ipaddress'),
                                              title=one.get('title'))
                # 更新techs信息
                techs = one.get('techs')
                for tech in techs:
                    WebsiteTech.update_website_tech(wid=wid, name=tech.get('name'), version=tech.get('version'),
                                                    icon=tech.get('icon'))
                # 更新waf信息
                waf = one.get('waf')
                WebsiteWaf.update_website_waf(wid=wid, hasWaf=waf.get('haswaf'), waf=waf.get('waf'),
                                              detect_tech=waf.get('detectTech'))
        return True
