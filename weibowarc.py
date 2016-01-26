#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import sys
import logging
import time
import json
import requests
from weibo import Client
import argparse
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

try:
    import configparser  # Python 3
except ImportError:
    import ConfigParser as configparser  # Python 2

if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
else:
    # Python 3
    get_input = input


# Error code for weibo api
# 10022   IP requests out of rate limit
# 10023   User requests out of rate limit
# 10024   User requests for (%s) out of rate limit

def main():
    """
    The testing command line for the weibo warc
    refer https://github.com/edsu/twarc/blob/master/twarc.py
    :return:
    """

    parser = argparse.ArgumentParser("weibowarc")
    parser.add_argument('-s', '--stimeline', action='store_true', required=True,
                        help="archive weibos in friendship timeline")
    parser.add_argument("--max_id", dest="max_id",
                        help="maximum weibo id to search for")
    parser.add_argument("--since_id", dest="since_id",
                        help="smallest id to search for")
    parser.add_argument("--log", dest="log",
                        default="weibowarc.log", help="log file")
    parser.add_argument("--api_key",
                        default=None, help="Weibo API key")
    parser.add_argument("--api_secret",
                        default=None, help="Weibo API secret")
    parser.add_argument("--redirect_uri",
                        default=None, help="Weibo API redirect uri")
    parser.add_argument("--access_token",
                        default=None, help="Weibo API access_token")
    parser.add_argument('-c', '--config',
                        default=default_config_filename(),
                        help="Config file containing Weibo keys and secrets")
    parser.add_argument('-p', '--profile', default='main',
                        help="Name of a profile in your configuration file")
    parser.add_argument('-w', '--warnings', action='store_true',
                        help="Include warning messages in output")

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # get the api key
    api_key = args.api_key or os.environ.get('API_KEY')
    api_secret = args.api_secret or os.environ.get('API_SECRET')
    redirect_uri = args.redirect_uri or os.environ.get('REDIRECT_URI')
    access_token = args.access_token or os.environ.get("ACCESS_TOKEN")

    if not (api_key and api_secret and
            redirect_uri and access_token):
        credentials = load_config(args.config, args.profile)
        if credentials:
            api_key = credentials['api_key']
            api_secret = credentials['api_secret']
            redirect_uri = credentials['redirect_uri']
            access_token = credentials['access_token']
        else:
            print("Please enter weibo authentication credentials")
            api_key = get_input('api key: ')
            api_secret = get_input('api secret: ')
            redirect_uri = get_input('redirect_uri: ')
            access_token = get_input('access_token: ')
            save_keys(args.profile, api_key, api_secret,
                      redirect_uri, access_token)

    weibowarc = Weibowarc(api_key=api_key,
                          api_secret=api_secret,
                          redirect_uri=redirect_uri,
                          access_token=access_token)

    if args.stimeline:
        weibos = weibowarc.search_friendships(since_id=args.since_id, max_id=args.max_id)
    else:
        raise argparse.ArgumentTypeError("-s  is required for the command.")

    for weibo in weibos:
        if u'mid' in weibo or args.warnings:
            print(json.dumps(weibo))
        # adding log infor
        if u'mid' in weibo:
            log.info("archived weibo [%s]:[%s]", weibo[u'user'][u'screen_name'], weibo[u"mid"])
        else:
            log.warn(json.dumps(weibo))


def save_config(filename, profile,
                api_key, api_secret,
                redirect_uri, access_token):
    config = configparser.ConfigParser()
    config.add_section(profile)
    config.set(profile, 'api_key', api_key)
    config.set(profile, 'api_secret', api_secret)
    config.set(profile, 'redirect_uri', redirect_uri)
    config.set(profile, 'access_token', access_token)
    with open(filename, 'w') as config_file:
        config.write(config_file)


def save_keys(profile, api_key, api_secret,
              redirect_uri, access_token):
    """
    Save keys to ~/.weibowarc
    """
    filename = default_config_filename()
    save_config(filename, profile,
                api_key, api_secret,
                redirect_uri, access_token)
    print("Keys saved to", filename)


def load_config(filename, profile):
    if not os.path.isfile(filename):
        return None
    config = configparser.ConfigParser()
    config.read(filename)
    data = {}
    for key in ['access_token', 'redirect_uri', 'api_key', 'api_secret']:
        try:
            data[key] = config.get(profile, key)
        except configparser.NoSectionError:
            sys.exit("no such profile %s in %s" % (profile, filename))
        except configparser.NoOptionError:
            sys.exit("missing %s from profile %s in %s" % (key, profile, filename))
    return data


def default_config_filename():
    """
    Return the default filename for storing Weibo keys.
    """
    home = os.path.expanduser("~")
    return os.path.join(home, ".weibowarc")


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

    def __init__(self, api_key, api_secret, redirect_uri, access_token):
        """
        Instantiate a Weibowarc instance. Make sure your  variables
        are set.
        """

        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self._connect()

    def search_friends_list(self):
        """
        Try to get the all the users followed by the current user, but it only returns
        30% of users haven't give right to the application
        :return:
        """
        log.info("starting search for friend.")
        friends_url = "friendships/friends"

        params = {'count': 100}

        params['uid'] = self.user_id()[u'uid']

        resp = self.get(friends_url, **params)
        statuses = resp[u'users']

        if len(statuses) == 0:
            log.info("no new weibo friendlist matching %s", params)
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
        log.info("starting search for max_id:%s, since_id:%s.", max_id, since_id)
        friendships_url = "statuses/friends_timeline"
        params = {
            'count': 100,
            'page': 1
        }

        while True:
            if since_id:
                params['since_id'] = since_id
            if max_id:
                params['max_id'] = max_id

            resp = self.get(friendships_url, **params)
            statuses = resp[u'statuses']

            if len(statuses) == 0:
                log.info("no new weibo post matching %s", params)
                break

            for status in statuses:
                """
                the application level need deal the retweeted text.
                if u'retweeted_status' in status and status[u'retweeted_status'] is not None:
                    yield status[u'retweeted_status']
                """
                yield status

            max_id = str(int(status[u'mid']) - 1)

    def get_long_urls(self, urls_short):
        log.info("starting get long urls for short url:%s.", urls_short)
        longurls_url = "short_url/expand"
        params = {
            'url_short': urls_short
        }

        resp = self.get(longurls_url, **params)
        # print resp
        urls = resp[u'urls']

        for url in urls:
            yield url

    @catch_conn_reset
    def get(self, *args, **kwargs):
        try:
            return self.client.get(*args, **kwargs)
        except RuntimeError, e:
            log.error("caught runtime error %s", e)
            error_code = ''.join(e)[0:5]
            if error_code in ['10022', '10023', '10024']:
                time.sleep(self.wait_time())
            else:
                raise e
        except requests.exceptions.ConnectionError as e:
            log.error("caught connection error %s", e)
            self._connect()
            return self.get(*args, **kwargs)

    @catch_conn_reset
    def post(self, *args, **kwargs):
        try:
            return self.client.post(*args, **kwargs)
        except RuntimeError, e:
            log.error("caught runtime error %s", e)
            error_code = ''.join(e)[0:5]
            if error_code in ['10022', '10023', '10024']:
                time.sleep(self.wait_time())
            else:
                raise e
        except requests.exceptions.ConnectionError as e:
            log.error("caught connection error %s", e)
            self._connect()
            return self.post(*args, **kwargs)

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

    def wait_time(self):
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
        log.info("creating client session with api_key=%s", self.api_key)
        # create the token
        # The uid and expires_at actually not used in the following
        token = {'access_token': self.access_token, 'uid': '', 'expires_at': 1609785214}
        try:
            self.client = Client(api_key=self.api_key,
                                api_secret=self.api_secret,
                                redirect_uri=self.redirect_uri,
                                token=token)
        except Exception, e:
            log.error("creating client session error,%s", e)
            raise e

if __name__ == "__main__":
    main()
