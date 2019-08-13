# -*- coding: utf-8 -*-
# @File  : test.py
# @Date  : 2019/5/17
# @Desc  :
# @license : Copyright(C), 360 
# @Author: zhaochengyu
# @Contact : zhaochengyu@360.net

import logging
import platform
import queue
import threading

import dns.resolver
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from Worker.WebCheck.wafw00f.wafw00f import check_waf
from Worker.WebCheck.wappalyzer.wappalyzer import WebPage, Wappalyzer

logger = logging.getLogger('webcheck')
dns_list = [
    '8.8.4.4',
    '114.114.114.114',
    '223.5.5.5',
    '223.6.6.6',
    '119.29.29.29',
    '182.254.116.116'
]
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    "Connection": "keep-alive",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    "Accept-Language": "zh-CN,zh;q=0.8",
    # 'Accept-Language': 'en-US,en;q=0.8',
    'Accept-Encoding': 'gzip',
}


def get_website_ipaddress(website=None):
    if website is None:
        return []
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = dns_list

    try:
        answers = resolver.query(website)
    except Exception as e:
        return []
    ipaddress = []
    for answer in answers:
        ipaddress.append(answer.address)
    ipaddress = list(set(ipaddress))
    return ipaddress


def check_website_alive(website=None):
    if website.startswith('https://') or website.startswith('http://'):
        entireUrl = website
    else:
        entireUrl = "http://{}".format(website)
    try:
        logging.captureWarnings(True)
        response = requests.get(entireUrl,
                                verify=False,
                                headers=headers,
                                timeout=5
                                )
        response.encoding = response.apparent_encoding
    except Exception as E:
        return False, None
    return True, response


class ScanThread(threading.Thread):
    def __init__(self, websitesQueue=queue.Queue(), resultQueue=queue.Queue()):
        threading.Thread.__init__(self)
        self.websitesQueue = websitesQueue
        self.resultQueue = resultQueue
        self.wappalyzer = Wappalyzer.latest()
        options = Options()
        options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        options.add_argument('window-size=1280x960')  # 指定浏览器分辨率

        options.add_argument('--hide-scrollbars')  # 隐藏滚动条, 应对一些特殊页面
        options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        sysstr = platform.system()
        if sysstr == "Windows":
            self.browser = webdriver.Chrome(executable_path="Worker/WebCheck/chromedriver.exe", chrome_options=options)
        elif sysstr == "Linux":
            self.browser = webdriver.Chrome(executable_path="Worker/WebCheck/chromedriver", chrome_options=options)
        else:
            self.browser = webdriver.Chrome(executable_path="Worker/WebCheck/chromedriver", chrome_options=options)

    def __del__(self):
        self.browser.close()

    def scan_website(self, website=None):
        logger.info("Start to scan {}".format(website))
        one_empty_result = {
            'website': website,
            'alive': False,  # 可访问
            'title': None,  # 可访问
            'ipaddress': [],  # ip地址
            'hascdn': False,  # cdn加速
            'techs': [],
            'waf': {'haswaf': False, 'waf': None, 'detectTech': None}
        }
        if website.startswith('https://') or website.startswith('http://'):
            entireUrl = website
        else:
            entireUrl = "http://{}".format(website)

        # 检查是否可达
        alive, response = check_website_alive(entireUrl)
        if alive is not True:
            one_empty_result['alive'] = False
            return one_empty_result
        else:
            one_empty_result['alive'] = True

        # 运行selenium
        self.browser.get(entireUrl)
        entireUrl = self.browser.current_url
        page_source = self.browser.page_source

        # 检测网站技术
        try:
            webpage = WebPage(response)
            one_empty_result['techs'] = self.wappalyzer.analyze_with_categories(webpage)
        except Exception as E:
            logger.warning(E)
            one_empty_result['techs'] = []

        # 解析title
        try:

            parsed_html = BeautifulSoup(page_source, 'html.parser')
            # parsed_html = BeautifulSoup(response.text, 'html.parser')
            rew_title = parsed_html.find_all('title')
            one_empty_result['title'] = rew_title[0].text
        except Exception as E:
            logger.warning(E)
            rew_title = None
            one_empty_result['title'] = entireUrl

        # 查找真实IP
        ipaddress_list = get_website_ipaddress(website)
        for ipaddress in ipaddress_list:
            url = entireUrl.replace(website, ipaddress)
            # url = "http://{}".format(ipaddress)
            try:
                logging.captureWarnings(True)
                response = requests.get(url,
                                        verify=False,
                                        headers=headers,
                                        timeout=3)
                response.encoding = response.apparent_encoding
            except Exception as E:
                one_empty_result['hascdn'] = True
                continue
            try:
                parsed_html = BeautifulSoup(response.text, 'html.parser')
                ip_title = parsed_html.find_all('title')
            except Exception as E:
                logging.warning(E)
                ip_title = None

            if rew_title == ip_title:
                one_empty_result['ipaddress'].append(ipaddress)
            else:
                one_empty_result['hascdn'] = True

        # 检测waf
        if len(one_empty_result['ipaddress']) > 0:
            one_empty_result['waf'] = check_waf(one_empty_result['ipaddress'][0])
        else:
            one_empty_result['waf'] = check_waf(website)

        logger.info(one_empty_result)
        return one_empty_result

    def run(self):
        while self.websitesQueue.empty() is not True:
            try:
                website = self.websitesQueue.get_nowait()
            except Exception as E:
                logger.warning(E)
                continue
            oneResult = self.scan_website(website)
            self.resultQueue.put(oneResult)


def worker_entry(websites=[]):
    resultQueue = queue.Queue()
    websitesQueue = queue.Queue()
    for website in websites:
        websitesQueue.put(website)
    threads = []
    for i in range(10):
        threads.append(ScanThread(websitesQueue=websitesQueue, resultQueue=resultQueue))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    result = []
    while resultQueue.empty() is not True:
        result.append(resultQueue.get())
    return result
