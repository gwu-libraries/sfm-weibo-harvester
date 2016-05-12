FROM python@sha256:ad39551743b356efda7c61f46019b97d49d1aab01b97f0e6d87c9b34326f3bfe
MAINTAINER Vict Tan <ychtan@email.gwu.edu>

RUN apt-get update && apt-get install -y \
    zip=3.0-8 \
    git=1:2.1.4-2.1+deb8u1
#Upgrade pip
RUN pip install pip==7.1.2
#Avoid the warning of https
RUN pip install --upgrade ndg-httpsclient

WORKDIR /tmp
ADD  https://github.com/gwu-libraries/sfm-weibo-harvester/archive/master.zip /tmp/
RUN unzip master.zip
RUN mv sfm-weibo-harvester-master /opt/sfm-weibo-harvester
WORKDIR /opt/sfm-weibo-harvester
RUN pip install -r requirements/master.txt
RUN pip install appdeps
CMD appdeps.py --port-wait mq:5672 \
    && python weibo_exporter.py --debug=$DEBUG service mq $MQ_ENV_RABBITMQ_DEFAULT_USER $MQ_ENV_RABBITMQ_DEFAULT_PASS http://api

