FROM python@sha256:ad39551743b356efda7c61f46019b97d49d1aab01b97f0e6d87c9b34326f3bfe
MAINTAINER Victor Tan <ychtan@email.gwu.edu>

RUN apt-get update && apt-get install -y \
    git=1:2.1.4-2.1+deb8u1

#pip set in 7.1.2
RUN pip install pip==7.1.2
#Avoid the warning of https
RUN pip install --upgrade ndg-httpsclient

#copy the requirement
ADD https://raw.githubusercontent.com/gwu-libraries/sfm-weibo-harvester/master/requirements/common.txt /tmp/
ADD https://raw.githubusercontent.com/gwu-libraries/sfm-weibo-harvester/master/requirements/requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt
RUN pip install appdeps
#It should mounted as your development dir
WORKDIR /opt/sfm-weibo-harvester

CMD pip install -r requirements/dev.txt --upgrade \
    && appdeps.py --port-wait mq:5672 \
    && python weibo_harvester.py --debug=$DEBUG service mq $MQ_ENV_RABBITMQ_DEFAULT_USER $MQ_ENV_RABBITMQ_DEFAULT_PASS
