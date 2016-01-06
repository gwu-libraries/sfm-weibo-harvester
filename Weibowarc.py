#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import requests
from weibo import Client
import urllib, httplib
from datetime import datetime, timedelta

log = logging.getLogger(__name__)


# Error code for weibo api
# 10022   IP requests out of rate limit
# 10023   User requests out of rate limit
# 10024   User requests for (%s) out of rate limit

def catch_conn_reset(f):
    """
    A decorator to handle connection reset errors even ones from pyOpenSSL
    until https://github.com/edsu/twarc/issues/72 is resolved
    """
    try:
        import OpenSSL
        ConnError = OpenSSL.SSL.SysCallError
    except:
        ConnError = requests.exceptions.ConnectionError

    def new_f(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except ConnError:
            self._connect()
            return f(self, *args, **kwargs)

    return new_f


class Weibowarc(object):
    """
    Weibowarc allows you to connect the API with the four parameters,
    get data from the friendships API.
    """

    def __init__(self, api_key, api_secret, redirect_uri, authorization_code):
        """
        Instantiate a Weibowarc instance. Make sure your environment variables
        are set.
        """

        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri
        self.authorization_code = authorization_code
        self._connect()

    def search_friendships(self, max_id=None, since_id=None):
        """
        Return all the results with optional max_id, since_id and get
        back an iterator for decoded weibo post.
        :param since_id:
        :param max_id:
        """
        logging.info("starting search for max_id:%s, since_id:%s.", max_id, since_id)
        friendships_url = "statuses/friends_timeline"
        params = {
            "count": 100
        }

        while True:
            if since_id:
                params['since_id'] = since_id
            if max_id:
                params['max_id'] = max_id

            statuses = self.get(friendships_url, params=params)

            if len(statuses) == 0:
                logging.info("no new weibo post matching %s", params)
                break

            for status in statuses:
                yield status

            max_id = str(int(status["mid"]) - 1)

    @catch_conn_reset
    def get(self, *args, **kwargs):
        try:
            return self.client.get(*args, **kwargs)
        except RuntimeError, e:
            logging.error("caught runtime error %s", e)
            error_code = ''.join(e)[0:5]
            if error_code in [10022, 10023, 10024]:
                time.sleep(self._wait_time())
            else:
                time.sleep(seconds=1)
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self._connect()
            return self.get(*args, **kwargs)

    @catch_conn_reset
    def post(self, *args, **kwargs):
        try:
            return self.client.post(*args, **kwargs)
        except RuntimeError, e:
            logging.error("caught runtime error %s", e)
            error_code = ''.join(e)[0:5]
            if error_code in [10022, 10023, 10024]:
                time.sleep(self._wait_time())
            else:
                time.sleep(seconds=1)
        except requests.exceptions.ConnectionError as e:
            logging.error("caught connection error %s", e)
            self._connect()
            return self.post(*args, **kwargs)

    def isTokenExpired(self):
        """
        check if the access_token is expired now
        :return:
        """
        return not self.access_token or self.client.alive()

    def rate_limit(self):
        """
        To get the rate_limit of the APIs calling.
        http://open.weibo.com/wiki/2/account/rate_limit_status
        since the rate_limit_status is without the rate limit, we can
        use it to count the sleep time.
        """
        res = self.get('account/rate_limit_status')
        return res

    def _wait_time(self):
        """
        If a rate limit error is encountered we will sleep until we can
        issue the API call again.
        """
        try:
            rl = self.rate_limit()
        except Exception, e:
            rl = None

        if rl:
            if rl['remaining_ip_hits'] > 1 and rl['remaining_user_hits'] > 1:
                return 1
            return rl['reset_time_in_seconds'] + 1
        now = datetime.now()
        reset = now + timedelta(seconds=3600 - now.minute * 60 - now.second)
        reset_ts = time.mktime(datetime.timetuple(reset))
        return reset_ts - time.time() + 10

    def _connect(self):
        logging.info("creating client session")
        if self.isTokenExpired():
            self.client = Client(app_key=self.api_key,
                                 app_secret=self.api_secret,
                                 redirect_uri=self.redirect_uri,
                                 token=self.access_token)
        else:
            self.client = Client(app_key=self.api_key,
                                 app_secret=self.api_secret,
                                 redirect_uri=self.redirect_uri)
            self.client.set_code(authorization_code=self.authorization_code)
            self.access_token = self.client.token
