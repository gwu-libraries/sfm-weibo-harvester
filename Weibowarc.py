#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import requests
from weibo import Client
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

# Error code for weibo api
# 10022   IP requests out of rate limit
# 10023   User requests out of rate limit
# 10024   User requests for (%s) out of rate limit


def catch_conn_reset(fun):
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
            return fun(self, *args, **kwargs)
        except ConnError:
            self._connect()
            return fun(self, *args, **kwargs)

    return new_f


class Weibowarc(object):
    """
    Weibowarc allows you to connect the API with the four parameters,
    get data from the friendships API.
    """

    def __init__(self, api_key, api_secret, redirect_uri, token):
        """
        Instantiate a Weibowarc instance. Make sure your  variables
        are set.
        """

        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri
        self.access_token = token
        self._connect()

    def search_friends_list(self):
        """
        Try to get the all the users followed by the current user, but it only returns
        30% of users haven't give right to the application
        :return:
        """
        logging.info("starting search for friend.")
        friends_url = "friendships/friends"

        params = {'count': 100}

        params['uid'] = self.user_id()[u'uid']

        resp = self.get(friends_url, **params)
        statuses = resp[u'users']

        if len(statuses) == 0:
            logging.info("no new weibo friendlist matching %s", params)
            return

        for status in statuses:
            yield status

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
            'count': 100,
            'page': 1
        }
        # count the number of post in first page
        page_count = 0
        while True:
            if since_id:
                params['since_id'] = since_id
            if max_id:
                params['max_id'] = max_id
            if page_count > 100:
                params['page'] = 2
                #time.sleep(2)

            resp = self.get(friendships_url, **params)
            statuses = resp[u'statuses']

            if len(statuses) == 0:
                logging.info("no new weibo post matching %s", params)
                break

            for status in statuses:
                page_count += 1
                yield status

            max_id = str(int(status[u'mid']) - 1)


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
        return not self.access_token or not self.client.alive()

    def user_id(self):
        """
        To get the current user id
        http://open.weibo.com/wiki/2/account/get_uid
        """
        res = self.get('account/get_uid')
        return res

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
        refer https://github.com/ghostrong/weibo-crawler/blob/master/example.py
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
        self.client = Client(api_key=self.api_key,
                         api_secret=self.api_secret,
                         redirect_uri=self.redirect_uri,
                         token=self.access_token)


