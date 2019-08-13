# -*- coding: utf-8 -*-
import base64
import codecs
import contextlib
import json
import re
import socket
import zlib
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM

import gevent
import gevent.monkey
from gevent.pool import Pool

from Worker.PortScan.RE_DATA import ALLPROBES, ALL_GUESS_SERVICE, TOP_1000_PORTS

global TIME_OUT
global RESULT_LIST

SOCKET_READ_BUFFERSIZE = 1024  # SOCKET DEFAULT READ BUFFER
NMAP_ENABLE_PROBE_INCLUED = True  # Scan probes inclued target port
NMAP_ENABLE_PROBE_EXCLUED = True  # Scan probes exclued target port


def add_port_banner(result_queue, host, port, proto, banner):
    """添加一个结果"""
    result_queue.put({'host': host, 'port': port, 'proto': proto, 'banner': banner})


def dqtoi(dq):
    """ip地址转数字."""
    octets = dq.split(".")
    if len(octets) != 4:
        raise ValueError
    for octet in octets:
        if int(octet) > 255:
            raise ValueError
    return (int(octets[0]) << 24) + \
           (int(octets[1]) << 16) + \
           (int(octets[2]) << 8) + \
           (int(octets[3]))


def itodq(intval):
    """数字转ip地址."""
    return "%u.%u.%u.%u" % ((intval >> 24) & 0x000000ff,
                            ((intval & 0x00ff0000) >> 16),
                            ((intval & 0x0000ff00) >> 8),
                            (intval & 0x000000ff))


def compile_pattern(allprobes):
    """编译re的正则表达式"""
    for probe in allprobes:
        matches = probe.get('matches')
        if isinstance(matches, list):
            for match in matches:
                try:
                    # pattern, _ = codecs.escape_decode(match.get('pattern'))
                    pattern = match.get('pattern').encode('utf-8')
                except Exception as err:
                    continue
                try:
                    match['pattern_compiled'] = re.compile(pattern, re.IGNORECASE | re.DOTALL)
                except Exception as err:
                    continue
        softmatches = probe.get('softmatches')
        if isinstance(softmatches, list):
            for match in softmatches:
                try:
                    # pattern, _ = codecs.escape_decode(match.get('pattern'))
                    pattern = match.get('pattern').encode('utf-8')
                except Exception as err:
                    continue
                try:
                    match['pattern_compiled'] = re.compile(pattern, re.IGNORECASE | re.DOTALL)
                except Exception as err:
                    continue
    return allprobes


class ServiceScan(object):
    allprobes = compile_pattern(json.loads(zlib.decompress(base64.b64decode(ALLPROBES))))
    all_guess_services = json.loads(zlib.decompress(base64.b64decode(ALL_GUESS_SERVICE)))

    def __init__(self):
        self.sd = None

    def scan(self, host, port, protocol):
        nmap_fingerprint = {'error': 'unknowservice'}
        in_probes, ex_probes = self.filter_probes_by_port(port, self.allprobes)
        if NMAP_ENABLE_PROBE_INCLUED and in_probes:
            probes = self.sort_probes_by_rarity(in_probes)
            for probe in probes:
                response = self.send_probestring_request(host, port, protocol, probe, TIME_OUT)
                if response is None:  # 连接超时
                    if self.all_guess_services.get(str(port)) is not None:
                        return self.all_guess_services.get(str(port))
                    return {'error': 'timeout'}
                else:
                    nmap_service, nmap_fingerprint = self.match_probe_pattern(response, probe)
                    if bool(nmap_fingerprint):
                        record = {
                            "service": nmap_service,
                            "versioninfo": nmap_fingerprint,
                        }
                        return record

        if NMAP_ENABLE_PROBE_EXCLUED and ex_probes:
            for probe in ex_probes:
                response = self.send_probestring_request(host, port, protocol, probe, TIME_OUT)
                if response is None:  # 连接超时
                    if self.all_guess_services.get(str(port)) is not None:
                        return self.all_guess_services.get(str(port))
                    return {'error': 'timeout'}
                else:
                    nmap_service, nmap_fingerprint = self.match_probe_pattern(response, probe)
                    if bool(nmap_fingerprint):
                        record = {
                            "service": nmap_service,
                            "versioninfo": nmap_fingerprint,
                        }
                        return record
        return nmap_fingerprint

    def scan_with_probes(self, host, port, protocol, probes):
        """发送probes中的每个probe到端口."""
        for probe in probes:
            record = self.send_probestring_request(host, port, protocol, probe, TIME_OUT)
            if bool(record.get('versioninfo')):  # 如果返回了versioninfo信息,表示已匹配,直接返回
                return record
        return {}

    def send_probestring_request(self, host, port, protocol, probe, timeout):
        """根据nmap的probestring发送请求数据包"""
        proto = probe['probe']['protocol']
        payload = probe['probe']['probestring']
        payload, _ = codecs.escape_decode(payload)

        response = ""
        # protocol must be match nmap probe protocol
        if proto.upper() == protocol.upper():
            if protocol.upper() == "TCP":
                response = self.send_tcp_request(host, port, payload, timeout)
            elif protocol.upper() == "UDP":
                response = self.send_udp_request(host, port, payload, timeout)
        return response

        # record = {
        #     "probe": {
        #         "probename": probe["probe"]["probename"],
        #         "probestring": probe["probe"]["probestring"]
        #     },
        #     "match": {
        #         "service": nmap_service,
        #         "versioninfo": nmap_fingerprint,
        #     }
        # }

    def send_tcp_request(self, host, port, payload, timeout):
        """Send tcp payloads by port number."""
        data = ''
        client = socket.socket(AF_INET, SOCK_STREAM)
        # client.setblocking(1)
        # timeval = struct.pack('ll', 1, 0)
        try:
            # client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, timeval)
            # client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)
            client.settimeout(TIME_OUT)
            client.connect((host, int(port)))
            client.send(payload)
            data = client.recv(SOCKET_READ_BUFFERSIZE)
            client.close()
        except Exception as err:
            return None
        finally:
            client.close()
        return data

    def send_udp_request(self, host, port, payload, timeout):
        """Send udp payloads by port number.
        """
        data = ''
        try:
            with contextlib.closing(socket.socket(AF_INET, SOCK_DGRAM)) as client:
                client.settimeout(timeout)
                client.sendto(payload, (host, port))
                while True:
                    _, addr = client.recvfrom(SOCKET_READ_BUFFERSIZE)
                    if not _:
                        break
                    data += _
        except Exception as err:
            return None
        return data

    def match_probe_pattern(self, data, probe):
        """Match tcp/udp response based on nmap probe pattern.
        """
        nmap_service, nmap_fingerprint = "", {}

        if not data:
            return nmap_service, nmap_fingerprint
        try:
            matches = probe['matches']
            for match in matches:
                # pattern = match['pattern']
                pattern_compiled = match['pattern_compiled']

                # https://github.com/nmap/nmap/blob/master/service_scan.cc#L476
                # regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)

                rfind = pattern_compiled.findall(data)

                if rfind and ("versioninfo" in match):
                    nmap_service = match['service']
                    versioninfo = match['versioninfo']

                    rfind = rfind[0]
                    if isinstance(rfind, str) or isinstance(rfind, bytes):
                        rfind = [rfind]

                    # (['5.5.38-log'], <type 'list'>)
                    # ([('2.0', '5.3')], <type 'list'>)
                    # ([('2.4.7', 'www.nongnu.org')], <type 'list'>)

                    if re.search('\$P\(\d\)', versioninfo) is not None:
                        for index, value in enumerate(rfind):
                            dollar_name = "$P({})".format(index + 1)

                            versioninfo = versioninfo.replace(dollar_name, value.decode('utf-8', 'ignore'))
                    elif re.search('\$\d', versioninfo) is not None:
                        for index, value in enumerate(rfind):
                            dollar_name = "${}".format(index + 1)

                            versioninfo = versioninfo.replace(dollar_name, value.decode('utf-8', 'ignore'))

                    nmap_fingerprint = self.match_versioninfo(versioninfo)
                    if nmap_fingerprint is None:
                        continue
                    else:
                        return nmap_service, nmap_fingerprint
        except Exception as err:
            return nmap_service, nmap_fingerprint
        try:
            matches = probe['softmatches']
            for match in matches:
                # pattern = match['pattern']
                pattern_compiled = match['pattern_compiled']

                # https://github.com/nmap/nmap/blob/master/service_scan.cc#L476
                # regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)

                rfind = pattern_compiled.findall(data)

                if rfind and ("versioninfo" in match):
                    nmap_service = match['service']
                    return nmap_service, nmap_fingerprint
        except Exception as err:
            return nmap_service, nmap_fingerprint
        return nmap_service, nmap_fingerprint

    def match_versioninfo(self, versioninfo):
        """Match Nmap versioninfo
        """
        # p/vendorproductname/
        # v/version/
        # i/info/
        # h/hostname/
        # o/operatingsystem/
        # d/devicetype/
        # cpe:/cpename/[a]

        # p/SimpleHTTPServer/ v/0.6/ i/Python 3.6.0/ cpe:/a:python:python:3.6.0/ cpe:/a:python:simplehttpserver:0.6/
        # p/Postfix smtpd/ cpe:/a:postfix:postfix/a
        # s
        # s p/TLSv1/
        # p/Postfix smtpd/ cpe:/a:postfix:postfix/a

        record = {
            "vendorproductname": [],
            "version": [],
            "info": [],
            "hostname": [],
            "operatingsystem": [],
            "cpename": []
        }

        if "p/" in versioninfo:
            regex = re.compile(r"p/([^/]*)/")
            vendorproductname = regex.findall(versioninfo)
            record["vendorproductname"] = vendorproductname

        if "v/" in versioninfo:
            regex = re.compile(r"v/([^/]*)/")
            version = regex.findall(versioninfo)
            record["version"] = version

        if "i/" in versioninfo:
            regex = re.compile(r"i/([^/]*)/")
            info = regex.findall(versioninfo)
            record["info"] = info

        if "h/" in versioninfo:
            regex = re.compile(r"h/([^/]*)/")
            hostname = regex.findall(versioninfo)
            record["hostname"] = hostname

        if "o/" in versioninfo:
            regex = re.compile(r"o/([^/]*)/")
            operatingsystem = regex.findall(versioninfo)
            record["operatingsystem"] = operatingsystem

        if "d/" in versioninfo:
            regex = re.compile(r"d/([^/]*)/")
            devicetype = regex.findall(versioninfo)
            record["devicetype"] = devicetype

        if "cpe:/" in versioninfo:
            regex = re.compile(r"cpe:/a:([^/]*)/")
            cpename = regex.findall(versioninfo)
            record["cpename"] = cpename
        if record == {"vendorproductname": [], "version": [], "info": [], "hostname": [], "operatingsystem": [],
                      "cpename": []}:
            return None
        return record

    def sort_probes_by_rarity(self, probes):
        """Sorts by rarity
        """
        newlist = sorted(probes, key=lambda k: k['rarity']['rarity'])
        return newlist

    def filter_probes_by_port(self, port, probes):
        """通过端口号进行过滤,返回强符合的probes和弱符合的probes
        """
        # {'match': {'pattern': '^LO_SERVER_VALIDATING_PIN\\n$',
        #            'service': 'impress-remote',
        #            'versioninfo': ' p/LibreOffice Impress remote/ '
        #                           'cpe:/a:libreoffice:libreoffice/'},
        #  'ports': {'ports': '1599'},
        #  'probe': {'probename': 'LibreOfficeImpressSCPair',
        #            'probestring': 'LO_SERVER_CLIENT_PAIR\\nNmap\\n0000\\n\\n',
        #            'protocol': 'TCP'},
        #  'rarity': {'rarity': '9'}}

        included = []
        excluded = []

        for probe in probes:
            if "ports" in probe:
                ports = probe['ports']['ports']
                if self.is_port_in_range(port, ports):
                    included.append(probe)
                else:  # exclude ports
                    excluded.append(probe)

            elif "sslports" in probe:
                sslports = probe['sslports']['sslports']
                if self.is_port_in_range(port, sslports):
                    included.append(probe)
                else:  # exclude sslports
                    excluded.append(probe)

            else:  # no [ports, sslports] settings
                excluded.append(probe)

        return included, excluded

    def is_port_in_range(self, port, nmap_port_rule):
        """Check port if is in nmap port range
        """
        bret = False

        ports = nmap_port_rule.split(',')  # split into serval string parts
        if str(port) in ports:
            bret = True
        else:
            for nmap_port in ports:
                if "-" in nmap_port:
                    s, e = nmap_port.split('-')
                    if int(port) in range(int(s), int(e)):
                        bret = True

        return bret


def async_scan(ipaddress_port):
    ipaddress = ipaddress_port[0]
    port = ipaddress_port[1]
    serviceScan = ServiceScan()
    sd = socket.socket(AF_INET, SOCK_STREAM)
    try:
        global TIME_OUT

        sd.settimeout(TIME_OUT)
        sd.connect((ipaddress, port))

        data = serviceScan.scan(ipaddress, port, 'tcp')
        sd.close()
        global RESULT_LIST
        RESULT_LIST.append({'ipaddress': ipaddress, 'port': port, 'data': data})
    except Exception as E:
        pass
    finally:
        sd.close()


def worker_entry(startip, stopip, port_list=[], timeout=3, domain=None):
    """每一个worker的入口函数"""
    start = dqtoi(startip)
    stop = dqtoi(stopip)
    if port_list == []:
        port_list = TOP_1000_PORTS

    global TIME_OUT
    global RESULT_LIST
    RESULT_LIST = []
    TIME_OUT = timeout

    gevent.monkey.patch_socket()
    tasks = []
    pool = Pool(1000)
    for host in range(start, stop + 1):
        for port in port_list:
            ipaddress = itodq(host)
            task = pool.spawn(async_scan, (ipaddress, port))
            tasks.append(task)

    gevent.joinall(tasks)

    return {'domain': domain, 'result': RESULT_LIST}


if __name__ == '__main__':
    result = worker_entry(startip='192.168.3.10', stopip='192.168.3.20')
    print(result)
