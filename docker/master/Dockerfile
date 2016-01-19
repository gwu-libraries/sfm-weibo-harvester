FROM python:2.7
MAINTAINER Vict Tan <ychtan@gwu.edu>

RUN apt-get update && apt-get install -y \
    wget \
    zip
#Upgrade pip
RUN pip install --upgrade pip
RUN wget --no-check-certificate https://github.com/gwu-libraries/sfm-weibo-harvester/archive/master.zip
RUN unzip master.zip
RUN mv sfm-weibo-harvester-master /opt/sfm-weibo-harvester
WORKDIR /opt/sfm-weibo-harvester
RUN pip install -r requirements.txt
RUN pip install appdeps
CMD appdeps.py --port-wait mq:5672 \
    && python weibo_harvester.py --debug service mq $MQ_ENV_RABBITMQ_DEFAULT_USER $MQ_ENV_RABBITMQ_DEFAULT_PASS
