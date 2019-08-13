#!/usr/bin/env python
# wafw00f - Web Application Firewall Detection Tool
# by Sandro Gauci - enablesecurity.com (c) 2016
#  and Wendel G. Henrique - Trustwave 2009

__license__ = """
Copyright (c) 2016, {Sandro Gauci|Wendel G. Henrique}
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of EnableSecurity or Trustwave nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import os

try:
    import httplib
except ImportError:
    import http.client as httplib
try:
    from urllib import quote, unquote
except ImportError:
    from urllib.parse import quote, unquote
import logging
# import sys
# currentDir = os.getcwd()
# scriptDir = os.path.dirname(sys.argv[0]) or '.'
# os.chdir(scriptDir)
import random

from Worker.WebCheck.wafw00f.lib.evillib import oururlparse, scrambledheader, waftoolsengine
from Worker.WebCheck.wafw00f.manager import load_plugins
from Worker.WebCheck.wafw00f.wafprio import wafdetectionsprio


class WafW00F(waftoolsengine):
    AdminFolder = '/Admin_Files/'
    xssstring = '<script>alert(1)</script>'
    dirtravstring = '../../../../etc/passwd'
    cleanhtmlstring = '<invalid>hello'

    def __init__(self, target='www.microsoft.com', port=80, ssl=False,
                 debuglevel=0, path='/', followredirect=True, extraheaders={}, proxy=False):
        """
        target: the hostname or ip of the target server
        port: defaults to 80
        ssl: defaults to false
        """
        self.log = logging.getLogger('wafw00f')
        waftoolsengine.__init__(self, target, port, ssl, debuglevel, path, followredirect, extraheaders, proxy)
        self.knowledge = dict(generic=dict(found=False, reason=''), wafname=list())

    def normalrequest(self, usecache=True, cacheresponse=True, headers=None):
        return self.request(usecache=usecache, cacheresponse=cacheresponse, headers=headers)

    def normalnonexistentfile(self, usecache=True, cacheresponse=True):
        path = self.path + str(random.randrange(1000, 9999)) + '.html'
        return self.request(path=path, usecache=usecache, cacheresponse=cacheresponse)

    def unknownmethod(self, usecache=True, cacheresponse=True):
        return self.request(method='OHYEA', usecache=usecache, cacheresponse=cacheresponse)

    def directorytraversal(self, usecache=True, cacheresponse=True):
        return self.request(path=self.path + self.dirtravstring, usecache=usecache, cacheresponse=cacheresponse)

    def invalidhost(self, usecache=True, cacheresponse=True):
        randomnumber = random.randrange(100000, 999999)
        return self.request(headers={'Host': str(randomnumber)})

    def cleanhtmlencoded(self, usecache=True, cacheresponse=True):
        string = self.path + quote(self.cleanhtmlstring) + '.html'
        return self.request(path=string, usecache=usecache, cacheresponse=cacheresponse)

    def cleanhtml(self, usecache=True, cacheresponse=True):
        string = self.path + '?htmli=' + self.cleanhtmlstring
        return self.request(path=string, usecache=usecache, cacheresponse=cacheresponse)

    def xssstandard(self, usecache=True, cacheresponse=True):
        xssstringa = self.path + '?xss=' + self.xssstring
        return self.request(path=xssstringa, usecache=usecache, cacheresponse=cacheresponse)

    def protectedfolder(self, usecache=True, cacheresponse=True):
        pfstring = self.path + self.AdminFolder
        return self.request(path=pfstring, usecache=usecache, cacheresponse=cacheresponse)

    def xssstandardencoded(self, usecache=True, cacheresponse=True):
        xssstringb = self.path + quote(self.xssstring) + '.html'
        return self.request(path=xssstringb, usecache=usecache, cacheresponse=cacheresponse)

    attacks = [xssstandard, directorytraversal, protectedfolder, xssstandardencoded]

    def genericdetect(self, usecache=True, cacheresponse=True):
        knownflops = [
            ('Microsoft-IIS/7.0', 'Microsoft-HTTPAPI/2.0'),
        ]
        reason = ''
        reasons = ['Blocking is being done at connection/packet level.',
                   'The server header is different when an attack is detected.',
                   'The server returned a different response code when a string trigged the blacklist.',
                   'It closed the connection for a normal request.',
                   'The connection header was scrambled.'
                   ]
        # test if response for a path containing html tags with known evil strings
        # gives a different response from another containing invalid html tags
        try:
            cleanresponse, _tmp = self._perform_and_check(self.cleanhtml)
            xssresponse, _tmp = self._perform_and_check(self.xssstandard)
            if xssresponse.status != cleanresponse.status:
                self.log.info('Server returned a different response when a script tag was tried')
                reason = reasons[2]
                reason += '\r\n'
                reason += 'Normal response code is "%s",' % cleanresponse.status
                reason += ' while the response code to an attack is "%s"' % xssresponse.status
                self.knowledge['generic']['reason'] = reason
                self.knowledge['generic']['found'] = True
                return True
            cleanresponse, _tmp = self._perform_and_check(self.cleanhtmlencoded)
            xssresponse, _tmp = self._perform_and_check(self.xssstandardencoded)
            if xssresponse.status != cleanresponse.status:
                self.log.info('Server returned a different response when a script tag was tried')
                reason = reasons[2]
                reason += '\r\n'
                reason += 'Normal response code is "%s",' % cleanresponse.status
                reason += ' while the response code to an attack is "%s"' % xssresponse.status
                self.knowledge['generic']['reason'] = reason
                self.knowledge['generic']['found'] = True
                return True
            response, _ = self._perform_and_check(self.normalrequest)
            normalserver = response.getheader('Server')
            for attack in self.attacks:
                response, _ = self._perform_and_check(lambda: attack(self))
                attackresponse_server = response.getheader('Server')
                if attackresponse_server:
                    if attackresponse_server != normalserver:
                        if (normalserver, attackresponse_server) in knownflops:
                            return False
                        self.log.info('Server header changed, WAF possibly detected')
                        self.log.debug('attack response: %s' % attackresponse_server)
                        self.log.debug('normal response: %s' % normalserver)
                        reason = reasons[1]
                        reason += '\r\nThe server header for a normal response is "%s",' % normalserver
                        reason += ' while the server header a response to an attack is "%s",' % attackresponse_server
                        self.knowledge['generic']['reason'] = reason
                        self.knowledge['generic']['found'] = True
                        return True
            for attack in wafdetectionsprio:
                if self.wafdetections[attack](self) is None:
                    self.knowledge['generic']['reason'] = reasons[0]
                    self.knowledge['generic']['found'] = True
                    return True
            for attack in self.attacks:
                response, _ = self._perform_and_check(lambda: attack(self))
                for h, _ in response.getheaders():
                    if scrambledheader(h):
                        self.knowledge['generic']['reason'] = reasons[4]
                        self.knowledge['generic']['found'] = True
                        return True
        except RequestBlocked:
            self.knowledge['generic']['reason'] = reasons[0]
            self.knowledge['generic']['found'] = True
            return True

        return False

    def _perform_and_check(self, request_method):
        r = request_method()
        if r is None:
            raise RequestBlocked()

        return r

    def matchheader(self, headermatch, attack=False, ignorecase=True):
        import re

        detected = False
        header, match = headermatch
        if attack:
            requests = self.attacks
        else:
            requests = [self.normalrequest]
        for request in requests:
            r = request(self)
            if r is None:
                return
            response, _ = r
            headerval = response.getheader(header)
            if headerval:
                # set-cookie can have multiple headers, python gives it to us
                # concatinated with a comma
                if header == 'set-cookie':
                    headervals = headerval.split(', ')
                else:
                    headervals = [headerval]
                for headerval in headervals:
                    if ignorecase:
                        if re.search(match, headerval, re.IGNORECASE):
                            detected = True
                            break
                    else:
                        if re.search(match, headerval):
                            detected = True
                            break
                if detected:
                    break
        return detected

    def matchcookie(self, match):
        """
        a convenience function which calls matchheader
        """
        return self.matchheader(('set-cookie', match))

    wafdetections = dict()

    plugin_dict = load_plugins()
    result_dict = {}
    for plugin_module in plugin_dict.values():
        wafdetections[plugin_module.NAME] = plugin_module.is_waf

    def identwaf(self, findall=False):
        detected = list()

        # Check for prioritized ones first, then check those added externally
        checklist = wafdetectionsprio
        checklist += list(set(self.wafdetections.keys()) - set(checklist))

        for wafvendor in checklist:
            self.log.info('Checking for %s' % wafvendor)
            if self.wafdetections[wafvendor](self):
                detected.append(wafvendor)
                if not findall:
                    break
        self.knowledge['wafname'] = detected
        return detected


def calclogginglevel(verbosity):
    default = 40  # errors are printed out
    level = default - (verbosity * 10)
    if level < 0:
        level = 0
    return level


def getheaders(fn):
    headers = {}
    fullfn = os.path.abspath(os.path.join(os.getcwd(), fn))
    if not os.path.exists(fullfn):
        logging.getLogger('wafw00f').critical('Headers file "%s" does not exist!' % fullfn)
        return
    with open(fn, 'r') as f:
        for line in f.readlines():
            _t = line.split(':', 2)
            if len(_t) == 2:
                h, v = map(lambda x: x.strip(), _t)
                headers[h] = v
    return headers


class RequestBlocked(Exception):
    pass


def check_waf(website):
    log = logging.getLogger()
    log.setLevel(logging.ERROR)
    empty_result = {'haswaf': False, 'waf': None, 'detectTech': None}
    if not (website.startswith('http://') or website.startswith('https://')):
        website = 'http://' + website
    pret = oururlparse(website)
    if pret is None:
        log.critical('The url %s is not well formed' % website)
        return empty_result

    (hostname, port, path, _, ssl) = pret

    attacker = WafW00F(hostname, port=port, ssl=ssl,
                       debuglevel=0, path=path,
                       followredirect=True,
                       extraheaders={},
                       proxy=False)
    if attacker.normalrequest() is None:
        log.error('Site %s appears to be down' % website)
        return empty_result

    waf = attacker.identwaf(findall=False)  # 只检测第一个匹配的waf

    if len(waf) > 0:
        return {'website': website, 'haswaf': True, 'waf': waf[0], 'detectTech': 'Plugin'}
    else:
        if attacker.genericdetect():
            return {'haswaf': True, 'waf': 'Unknow',
                    'detectTech': attacker.knowledge['generic']['reason']}
        else:
            return {'haswaf': False, 'waf': None, 'detectTech': None}


def worker_entry(websites):
    """每一个worker的入口函数"""
    result = []

    log = logging.getLogger()
    log.setLevel(logging.ERROR)
    for target in websites:
        website = target
        if not (target.startswith('http://') or target.startswith('https://')):
            target = 'http://' + target
        pret = oururlparse(target)
        if pret is None:
            log.critical('The url %s is not well formed' % target)
            continue
        (hostname, port, path, _, ssl) = pret
        log.info('starting wafw00f on %s' % target)
        attacker = WafW00F(hostname, port=port, ssl=ssl,
                           debuglevel=0, path=path,
                           followredirect=True,
                           extraheaders={},
                           proxy=False)
        if attacker.normalrequest() is None:
            log.error('Site %s appears to be down' % target)
            continue

        waf = attacker.identwaf(findall=False)  # 只检测第一个匹配的waf
        log.info('Ident WAF: %s' % waf)
        if len(waf) > 0:
            result.append({'website': website, 'haswaf': True, 'waf': waf[0], 'detectTech': 'Plugin'})
            continue
        else:
            if attacker.genericdetect():

                result.append({'website': website, 'haswaf': True, 'waf': 'Unknow',
                               'detectTech': attacker.knowledge['generic']['reason']})

            else:
                result.append({'website': website, 'haswaf': False, 'waf': None, 'detectTech': None})
    return result

# if __name__ == '__main__':
#     worker_entry(["ant.design", "zt.faw.com.cn", "mail.jf.faw.com.cn", ])
