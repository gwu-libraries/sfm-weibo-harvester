import logging
import unittest
import os
import socket

try:
    from test_config import *
except ImportError:
    WEIBO_API_KEY = os.environ.get("WEIBO_API_KEY")
    WEIBO_API_SECRET = os.environ.get("WEIBO_API_SECRET")
    WEIBO_REDIRECT_URI = os.environ.get("WEIBO_REDIRECT_URI")
    WEIBO_ACCESS_TOKEN = os.environ.get("WEIBO_ACCESS_TOKEN")

test_config_available = True if WEIBO_API_KEY and WEIBO_API_SECRET \
                                and WEIBO_REDIRECT_URI and WEIBO_ACCESS_TOKEN else False

mq_port_available = True
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(("mq", 5672))
except socket.error:
    mq_port_available = False

mq_username = os.environ.get("MQ_ENV_RABBITMQ_DEFAULT_USER")
mq_password = os.environ.get("MQ_ENV_RABBITMQ_DEFAULT_PASS")
integration_env_available = mq_port_available and mq_username and mq_password


class TestCase(unittest.TestCase):
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("weibo_harvester").setLevel(logging.DEBUG)
    logging.getLogger("weibowarc").setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("vcr").setLevel(logging.INFO)