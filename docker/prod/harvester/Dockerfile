FROM python@sha256:ad39551743b356efda7c61f46019b97d49d1aab01b97f0e6d87c9b34326f3bfe
MAINTAINER Vict Tan <ychtan@email.gwu.edu>

ARG DEBIAN_FRONTEND=noninteractive
ENV sfm_harvester_version 1.0.0

RUN apt-get update && apt-get install -y \
    zip=3.0-8
#Upgrade pip
RUN pip install pip==7.1.2
#Avoid the warning of https
RUN pip install --upgrade ndg-httpsclient

WORKDIR /tmp
ADD https://github.com/gwu-libraries/sfm-weibo-harvester/archive/${sfm_harvester_version}.zip /tmp/
RUN unzip ${sfm_harvester_version}.zip
RUN mv sfm-weibo-harvester-${sfm_harvester_version} /opt/sfm-weibo-harvester

WORKDIR /opt/sfm-weibo-harvester
RUN pip install -r requirements/requirements.txt
RUN pip install appdeps
CMD appdeps.py --port-wait mq:5672 \
    && python weibo_harvester.py --debug=$DEBUG service mq $MQ_ENV_RABBITMQ_DEFAULT_USER $MQ_ENV_RABBITMQ_DEFAULT_PASS

