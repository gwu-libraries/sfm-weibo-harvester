FROM python:2.7
MAINTAINER Vict Tan <ychtan@gwu.edu>

RUN apt-get update && apt-get install -y \
    wget \
    zip
#Upgrade pip
RUN pip install --upgrade pip
RUN wget --no-check-certificate https://github.com/gwu-libraries/sfm-weibo-harvester/archive/dev.zip
RUN unzip dev.zip
RUN mv sfm-weibo-harvester-dev /opt/sfm-weibo-harvester
WORKDIR /opt/sfm-weibo-harvester
RUN pip install -r requirements.txt
RUN pip install appdeps
# setting up the sfm-utils
CMD cd /opt/sfm-utils \
    && python setup.py develop \
    && cd /opt/sfm-weibo-harvester \
    && appdeps.py --port-wait mq:5672 \
    && python weibo_harvester.py --debug=$DEBUG service mq $MQ_ENV_RABBITMQ_DEFAULT_USER $MQ_ENV_RABBITMQ_DEFAULT_PASS
