#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

import argparse
import os
import socket
import subprocess
import time


def check_services():
    """服务检查函数"""
    LOCALHOST = "127.0.0.1"
    redis_port = 6379
    nginx_port = 80

    toybox_port = 18000
    print("-------------- 检查服务状态 ----------------")
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1)
        client.connect((LOCALHOST, redis_port))
        print("[+] redis运行中")
        client.close()
    except Exception as err:
        print("[x] redis未启动")
    finally:
        client.close()
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1)
        client.connect((LOCALHOST, nginx_port))
        print("[+] nginx运行中")
        client.close()
    except Exception as err:
        print("[x] nginx未启动")
    finally:
        client.close()
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1)
        client.connect((LOCALHOST, toybox_port))
        print("[+] Toy4Recon主服务运行中")
        client.close()
    except Exception as err:
        print("[x] Toy4Recon主服务未启动")
    finally:
        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        add_help=True,
        description="脚本用于 启动/停止 Toy4Recon服务,修改admin用户密码,设置反向Shell回连IP等功能.")
    parser.add_argument('-s', metavar='start/stop/check', help="启动/停止/检测 Toy4Recon服务")
    parser.add_argument('--changepassword', metavar='newpassword', help="修改admin密码")
    args = parser.parse_args()

    action = args.s
    newpassword = args.changepassword

    if action is None and newpassword is None:
        parser.print_help()
        exit(0)

    if action is not None:
        if action.lower() == "start":
            # 启动服务

            devNull = open(os.devnull, 'w')
            try:
                print("[*] 启动redis服务")
                result = subprocess.run(["service", "redis-server", "start"], stdout=devNull)
            except Exception as E:
                pass
            try:
                print("[*] 检查权限")
                result = subprocess.run(["chmod", "755", "/root/Toy4Recon/Worker/WebCheck/chromedriver"],
                                        stdout=devNull)
            except Exception as E:
                pass
            try:
                print("[*] 启动nginx服务")
                result = subprocess.run(["service", "nginx", "start"], stdout=devNull)
            except Exception as E:
                pass
            try:
                print("[*] 启动celery服务")
                result = subprocess.run(["service", "celeryd", "start"], stdout=devNull)
            except Exception as E:
                pass
            try:
                print("[*] 启动Toy4Recon主服务")
                result = subprocess.run(["uwsgi", "--ini", "/root/Toy4Recon/uwsgi.ini", ], stdout=devNull)
            except Exception as E:
                pass
            time.sleep(3)
            check_services()

        elif action.lower() == "stop":
            devNull = open(os.devnull, 'w')
            try:
                print("[*] 关闭nginx服务")
                result = subprocess.run(["service", "nginx", "stop"], stdout=devNull)
            except Exception as E:
                pass
            try:
                print("[*] 关闭celery服务")
                result = subprocess.run(["service", "celeryd", "stop"], stdout=devNull)
            except Exception as E:
                pass
            try:
                print("[*] 关闭Toy4Recon主服务")
                result = subprocess.run(["uwsgi", "--stop", "/root/Toy4Recon/uwsgi.pid"], stdout=devNull)
            except Exception as E:
                pass
            time.sleep(5)
            check_services()
        else:
            check_services()

    if newpassword is not None:
        if len(newpassword) < 8:
            print("[x] 新密码必须大于等于8位")
            exit(0)
        else:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Toy4Recon.settings")
            import django

            django.setup()  # 启动django项目
            from django.contrib.auth.models import User

            user = User.objects.get(username='admin')
            user.set_password(newpassword)
            user.save()
            print("[+] 修改密码完成,新密码为: {}".format(newpassword))
