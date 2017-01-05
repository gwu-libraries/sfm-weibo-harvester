#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import sys
import logging
import time
import json
import requests
import argparse
from datetime import datetime, timedelta
from twarc import get_input, catch_conn_reset

log = logging.getLogger(__name__)

try:
    import configparser  # Python 3
except ImportError:
    import ConfigParser as configparser  # Python 2

# Max weibos in per page
MAX_WEIBO_PER_PAGE = 50


# Error code for weibo api
# 10022   IP requests out of rate limit
# 10023   User requests out of rate limit
# 10024   User requests for (%s) out of rate limit

def main():
    """
    The testing command line for the weibo archive
    refer https://github.com/edsu/twarc/blob/master/twarc.py
    :return:
    """

    parser = argparse.ArgumentParser("weiboarc")
    parser.add_argument("--search", dest="search",
                        help="search for weibo posts matching a query topic")
    parser.add_argument("--max_id", dest="max_id",
                        help="maximum weibo id to search for")
    parser.add_argument("--since_id", dest="since_id",
                        help="smallest id to search for")
    parser.add_argument("--log", dest="log",
                        default="weiboarc.log", help="log file")
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
    access_token = args.access_token or os.environ.get("ACCESS_TOKEN")
    if not access_token:
        credentials = load_config(args.config, args.profile)
        if credentials:
            access_token = credentials['access_token']
        else:
            print("Please enter weibo authentication credentials")
            access_token = get_input('access_token: ')

            save_keys(args.profile, access_token)

    weiboarc = Weiboarc(access_token=access_token)
    weibos = []
    if args.search:
        weibos = weiboarc.search_topic(
            args.search.decode('utf-8'),
            since_id=None if not args.since_id else int(args.since_id),
            max_id=None if not args.max_id else int(args.max_id),
        )
    else:
        weibos = weiboarc.search_friendships(since_id=args.since_id, max_id=args.max_id)

    for weibo in weibos:
        if u'mid' in weibo or args.warnings:
            print(json.dumps(weibo))
        # adding log info
        if u'mid' in weibo:
            log.info("archived weibo [%s]:[%s]", weibo[u'user'][u'screen_name'], weibo[u"mid"])
        else:
            log.warn(json.dumps(weibo))


def save_config(filename, profile, access_token):
    config = configparser.ConfigParser()
    config.add_section(profile)
    config.set(profile, 'access_token', access_token)
    with open(filename, 'w') as config_file:
        config.write(config_file)


def save_keys(profile, access_token):
    """
    Save keys to ~/.weibowarc
    """
    filename = default_config_filename()
    save_config(filename, profile, access_token)
    print("Keys saved to", filename)


def load_config(filename, profile):
    if not os.path.isfile(filename):
        return None
    config = configparser.ConfigParser()
    config.read(filename)
    data = {}
    for key in ['access_token']:
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
    return os.path.join(home, ".weiboarc")


def status_error(f):
    """
    A decorator to handle http response error from the Weibo API.
    refer: https://github.com/edsu/twarc/blob/master/twarc.py
    """

    def new_f(*args, **kwargs):
        errors = 0
        while True:
            resp = f(*args, **kwargs)
            if resp.status_code == 200:
                errors = 0
                return resp
            elif resp.status_code == 404:
                errors += 1
                logging.warn("404:Not found url! Sleep 1s to try again...")
                if errors > 10:
                    logging.warn("Too many errors 404, stop!")
                    resp.raise_for_status()
                logging.warn("%s from request URL, sleeping 1s", resp.status_code)
                time.sleep(1)

            # deal with the response error
            elif resp.status_code >= 500:
                errors += 1
                if errors > 30:
                    logging.warn("Too many errors from Weibo REST API Server, stop!")
                    resp.raise_for_status()
                seconds = 60 * errors
                logging.warn("%s from Weibo REST API Server, sleeping %d", resp.status_code, seconds)
                time.sleep(seconds)
            else:
                resp.raise_for_status()

    return new_f


class Weiboarc(object):
    """
    Weiboarc allows you to connect the API with the four parameters,
    get data from the friendships API.
    """

    def __init__(self, access_token):
        """
        Instantiate a Weiboarc instance. Make sure your  variables
        are set.
        """

        self.access_token = access_token
        self._connect()

    def search_topic(self, q, since_id=None, max_id=None):
        """
        Return the latest 200 weibos related to a query topic
        :param q: keyword for topic to search
        :param since_id: it will return the weibo with id larger than the id
        :param max_id: it will return the weibo with id smaller than the id
        """
        log.info(u"starting search for topic:%s.", q)
        search_url = "search/topics"
        params = {
            'count': MAX_WEIBO_PER_PAGE,
            'q': q
        }
        start_page = 1
        while True:
            params['page'] = start_page

            # if access more than 200, avoid ["error_code": "21411", error": "only provide 200 results"]
            if start_page * MAX_WEIBO_PER_PAGE > 200:
                break

            resp = self.get(search_url, **params)
            statuses = resp.json()['statuses']

            if len(statuses) == 0:
                logging.info("reach the end of calling for weibos statues.")
                break

            start_pos, end_pos = 0, len(statuses)
            if max_id:
                start_pos = self._lower_bound(statuses, max_id)
            if since_id:
                end_pos = self._upper_bound(statuses, since_id)

            # checks the result after filtering
            if len(statuses[start_pos:end_pos]) == 0:
                logging.info("no new weibos matching since_id %s and max_id %s", since_id, max_id)
                break

            for status in statuses[start_pos:end_pos]:
                yield status

            max_id = status[u'id'] - 1

            # if the page has apply filter and found the post id, it should be the last page
            if 0 < (end_pos - start_pos) < MAX_WEIBO_PER_PAGE:
                logging.info("reach the last page for since_id %s and max_id %s", since_id, max_id)
                break

            # go to the next page
            start_page += 1

    def search_friendships(self, max_id=None, since_id=None):
        """
        Return all the results with optional max_id, since_id and get
        back an iterator for decoded weibo post.
        :param since_id: it will return the weibo with id larger than the id
        :param max_id: it will return the weibo with id smaller than the id
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
            statuses = resp.json()['statuses']

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

    @status_error
    @catch_conn_reset
    def get(self, *args, **kwargs):
        try:
            r = self.client.get(*args, **kwargs)
            # if rate limit reach
            if r.status_code == 429:
                seconds = self.wait_time()
                logging.warn("Rate limit 429 from Weibo API, Sleep %d to try...", seconds)
                time.sleep(seconds)
                r = self.get(*args, **kwargs)
            return r
        except APIError, e:
            # if rate limit reach
            log.error("caught APIError error %s", e)
            if e.error_code in [10022, 10023, 10024]:
                seconds = self.wait_time()
                logging.warn("Rate limit %d from Weibo API, Sleep %d to try...", e.error_code, seconds)
                time.sleep(seconds)
                return self.get(*args, **kwargs)
            else:
                raise e
        except requests.exceptions.ConnectionError as e:
            log.error("caught connection error %s", e)
            self._connect()
            return self.get(*args, **kwargs)

    def rate_limit(self):
        """
        To get the rate_limit of the APIs calling.
        http://open.weibo.com/wiki/2/account/rate_limit_status
        since the rate_limit_status is without the rate limit, we can
        use it to count the sleep time.
        """
        res = self.get('account/rate_limit_status')
        return res.json()

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
                return 60
            return rl['reset_time_in_seconds'] + 10

        now = datetime.now()
        reset = now + timedelta(seconds=3600 - now.minute * 60 - now.second)
        reset_ts = time.mktime(datetime.timetuple(reset))
        return reset_ts - time.time() + 60

    def _connect(self):
        log.info("creating client session...")
        try:
            self.client = Client(access_token=self.access_token)
        except Exception, e:
            log.error("creating client session error,%s", e)
            raise e

    def _lower_bound(self, weibos, max_id):
        """
        Finding the lower bound of the position to insert the max weibo id
        for i<left weibos[low]['id']>max_id
        :param weibos: the weibos need to deal with
        :param max_id: the target weibo id
        :return: the position for insert the max_id
        """
        left, right = 0, len(weibos) - 1
        while left <= right:
            mid = (left + right) / 2
            if weibos[mid][u'id'] >= max_id:
                left = mid + 1
            else:
                right = mid - 1
        return left

    def _upper_bound(self, weibos, since_id):
        """
        Finding the upper bound of the position to insert the since weibo id
        for i>right weibos[high]['id']<since_post_id
        :param weibos: the weibos need to deal with
        :param since_id: the target since weibo id
        :return: the position for insert the since_id
        """
        left, right = 0, len(weibos) - 1
        while left <= right:
            mid = (left + right) / 2
            if weibos[mid][u'id'] > since_id:
                left = mid + 1
            else:
                right = mid - 1
        return left


class APIError(StandardError):
    """
    raise APIError if got failed message from the API not the http error.
    """

    def __init__(self, error_code, error, request):
        self.error_code = error_code
        self.error = error
        self.request = request
        StandardError.__init__(self, error)

    def __str__(self):
        return 'APIError: %s, %s, Request: %s' % (self.error_code, self.error, self.request)


class Client(object):
    """
    Refer from https://github.com/lxyu/weibo/blob/master/weibo.py
    Since we need deal withe the http response error code
    """

    def __init__(self, access_token, api_key=None, api_secret=None, redirect_uri=None):
        # const define
        self.site = 'https://api.weibo.com/'
        self.authorization_url = self.site + 'oauth2/authorize'
        self.token_url = self.site + 'oauth2/access_token'
        self.api_url = self.site + '2/'

        # init basic info, for future api use
        self.client_id = api_key
        self.client_secret = api_secret
        self.redirect_uri = redirect_uri

        self.session = requests.session()
        # activate client directly with given access_token
        self.session.params = {'access_token': access_token}

    def _assert_error(self, d):
        """
        Assert if json response is error.
        """
        if 'error_code' in d and 'error' in d:
            raise APIError(d.get('error_code'), d.get('error', ''), d.get('request', ''))

    def get(self, uri, **kwargs):
        """
        Request resource by get method.
        """
        # 500 test url
        # self.api_url='https://httpbin.org/status/500'

        url = "{0}{1}.json".format(self.api_url, uri)

        res = self.session.get(url, params=kwargs)
        # other error code with server will be deal in low level app
        # 403 for invalid access token and rate limit
        # 400 for information of expire token
        if res.status_code in [200, 400, 403]:
            self._assert_error(res.json())
        return res


if __name__ == "__main__":
    main()
