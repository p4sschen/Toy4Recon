from CONFIG import *

broker_url = 'redis://:{}@{}:{}/0'.format(REDIS_PASSWORD, REDIS_HOST, REDIS_PORT)
result_backend = 'redis://:{}@{}:{}/0'.format(REDIS_PASSWORD, REDIS_HOST, REDIS_PORT)
# broker_url = 'amqp://zhaochengyu:chengyuzhaorabbitmq@192.168.31.101:5672/zhaochengyuhost'
# result_backend = 'amqp://zhaochengyu:chengyuzhaorabbitmq@192.168.31.101:5672/zhaochengyuhost'

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Shanghai'
enable_utc = True
task_soft_time_limit = 3600
