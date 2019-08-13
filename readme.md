Toy4Recon是一款用于渗透测试前期的网络侦察工具.
# 工具截图
![图片](https://uploader.shimo.im/f/m8Qlx48BVPsjNHz7.png!thumbnail)
![图片](https://uploader.shimo.im/f/8rqthK5o18kPWV1N.png!thumbnail)
![图片](https://uploader.shimo.im/f/ZBQzgaK5IHQREJVY.png!thumbnail)

![图片](https://uploader.shimo.im/f/zfOeiSPQBCIxZxuQ.png!thumbnail)
![图片](https://uploader.shimo.im/f/tgE7H89KdXEk5Joi.png!thumbnail)
![图片](https://uploader.shimo.im/f/jDKx2o6nIjAT7uS4.png!thumbnail)

# 技术架构
![图片](https://uploader.shimo.im/f/K195M8Bmb7QAGuIq.png!thumbnail)
# 使用
### 安装
* 准备一台ubuntu/debain系统的VPS,VPS中安装docker.
```
root@vultr:~#wget -qO- https://get.docker.com/ | sh
root@vultr:~#service docker start
```
(教程参考[https://www.runoob](https://www.runoob.com/docker/ubuntu-docker-install.html)[.c](https://www.runoob.com/docker/ubuntu-docker-install.html)[om/d](https://www.runoob.com/docker/ubuntu-docker-install.html)[ocker](https://www.runoob.com/docker/ubuntu-docker-install.html)[/ubun](https://www.runoob.com/docker/ubuntu-docker-install.html)[t](https://www.runoob.com/docker/ubuntu-docker-install.html)[u-d](https://www.runoob.com/docker/ubuntu-docker-install.html)[ocker-install.h](https://www.runoob.com/docker/ubuntu-docker-install.html)[tml](https://www.runoob.com/docker/ubuntu-docker-install.html))
* 登录VPS下载docker镜像
```
$ docker pull registry.cn-beijing.aliyuncs.com/funny-wolf/toy4recon
```
* 运行镜像
```
$ docker run -i -t -p 3000:80 -d --name your_recon_name registry.cn-beijing.aliyuncs.com/funny-wolf/toy4recon /bin/bash
```
* 进入docker容器
```
$ docker exec -i -t your_recon_name /bin/bash
```
* 修改admin用户密码(toy4recon@admin替换为你的密码)
```
root@f658ccb72375:/# toy4recon --changepassword toy4recon@admin
```
* 启动服务
```
root@f658ccb72375:/# toy4recon -s start
```
* 访问http://vpsip:3000登录服务器(用户名:admin 密码toy4recon@admin)

# 其他
因操作系统限制,工具再进行端口扫描过程中默认最大使用1000个tcp连接,如果需要提升性能(linux系统建议最大设置50000),可以在VPS主机中执行Toy4Recon/Other/max_tcp.sh脚本打开操作系统限制,并修改Toy4Recon/Worker/PortScan/portScan.py的423行

