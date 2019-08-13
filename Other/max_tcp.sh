#!/bin/sh
echo "ulimit -HSn 65536" >> /etc/rc.local
echo "ulimit -HSn 65536" >> /root/.bash_profile
ulimit -HSn 65536
echo "speng soft nofile 10240" >> /etc/security/limits.conf
echo "speng hard nofile 1024" >> /etc/security/limits.conf
echo "session required /lib/security/pam_limits.so" >> /etc/pam.d/login
cat>/etc/sysctl.conf<<EOF
net.ipv4.ip_local_port_range = 1024 65535
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_timestamps = 0
net.ipv4.tcp_window_scaling = 0
net.ipv4.tcp_sack = 0
net.core.netdev_max_backlog = 30000
net.ipv4.tcp_no_metrics_save = 1
net.core.somaxconn = 10240
net.ipv4.tcp_syncookies = 0
net.ipv4.tcp_max_orphans = 262144
net.ipv4.tcp_max_syn_backlog = 262144
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 2
EOF
sysctl -p /etc/sysctl.conf >/dev/null
sysctl -w net.ipv4.route.flush=1
echo "Run success,Do not run repeatedly"