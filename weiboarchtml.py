#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
import time
import sys
from bs4 import BeautifulSoup
import argparse
import getpass


if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
else:
    # Python 3
    get_input = input


def main():
    """
    The testing command line for the weibo archive html
    :return:
    """

    parser = argparse.ArgumentParser("weiboarchtml")
    parser.add_argument("--search", dest="search",
                        help="search for weibos matching a keywords")
    parser.add_argument("--max_page",
                        default=10, type=int,help="Show the Weibo search results less than max page")
    parser.add_argument("--follow", nargs='*', dest="follow",
                        help="follow the given user")
    parser.add_argument("--unfollow", nargs='*', dest="unfollow",
                        help="unfollow the given user")
    parser.add_argument("--followlist", action='store_true',dest="followlist",
                        help="get the followlist of current user")
    parser.add_argument("--log", dest="log",
                        default="weiboarchtml.log", help="log file")
    parser.add_argument("--username",
                        default=None, help="Weibo username")
    parser.add_argument("--password",
                        default=None, help="Weibo password")
    parser.add_argument('-w', '--warnings', action='store_true',
                        help="Include warning messages in output")

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    username = args.username
    password = args.password

    if not (username and password):
        print("Please enter your weibo username and password")
        username = get_input('username: ')
        password = getpass.getpass('password: ')

    weibohtml = WeiboarcHtml(username=username, password=password)

    if args.search:
        weibos = weibohtml.search_word(key_word=args.search, max_page_num=args.max_page)
        for weibo in weibos:
            print weibo
    elif args.follow:
        users_id = []
        for user in args.follow:
            users_id.append(user)
        weibohtml.follow_users(uids=users_id)
    elif args.unfollow:
        users_id = []
        for user in args.unfollow:
            users_id.append(user)
        weibohtml.unfollow_users(uids=users_id)
    elif args.followlist:
        for followers in weibohtml.get_follower_list():
            print followers
    else:
        raise argparse.ArgumentTypeError("search, follow, unfollow or followlist is required for the command.")


class WeiboarcHtml(object):
    """
    WeiboarcHtml allows you to login weibo to mobile page using
    the username, password. Getting the whole friendship of the login user.
    refer from  https://github.com/wangdashuaihenshuai/weibo/blob/master/weibo.py
    """

    def __init__(self, username, password):
        self.session = requests.session()
        self.rand_url = 'http://login.weibo.cn/login/'
        self.login_url = 'http://login.weibo.cn/login/'

        res = self.session.post(self.login_url, data={})
        page_text = res.text
        soup = BeautifulSoup(page_text, "html.parser")
        rand = soup.form["action"]
        self.url = self.rand_url + rand
        for v in soup.select('input[name="vk"]'):
            vk = v["value"]
        for p in soup.select('input[type="password"]'):
            password_rand = p["name"]

        self.data = {'mobile': username,
                     password_rand: password,
                     'remember': 'on',
                     'backURL': 'http://weibo.cn/',
                     'backTitle': '新浪微博',
                     'vk': vk,
                     'submit': '登录',
                     'encoding': 'utf-8'}
        page = self.session.post(self.url, self.data)
        self._assert_error(res)

        soup = BeautifulSoup(page.text, "html.parser")
        print soup
        try:
            self.uid = soup.find("div", "tip2").a["href"].split('/')[1]
            self.st_num = soup.find("div", "pms").form["action"].split('st=')[1]
        except AttributeError, e:
            logging.error("Login failed,bad username or password.")
            raise AttributeError("Login failed,bad username or password.")

        logging.info("Login successful...")

    def follow_users(self, uids):
        """
        Try to follow the special uid in the html ways.
        --Testing function--
        :return:
        """
        for uid in uids:
            follow_url = 'http://weibo.cn/attention/add?uid='+uid+'&rl=0&st='+self.st_num
            headers = {
                'Referer': 'http://weibo.cn/u/' + uid,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            res = self.session.get(url=follow_url, headers=headers)
            # slow down the follow speed
            time.sleep(0.2)
            self._assert_error(res)

    def unfollow_users(self, uids):
        """
        Try to destroy follow the special uid in the html ways.
        --Testing function--
        :return:
        """
        for uid in uids:
            follow_url = 'http://weibo.cn/attention/del?rl=1&act=delc&uid='+uid+'&st='+self.st_num
            headers = {

                'Referer': ' http://weibo.cn/attention/del?uid='+uid+'&rl=1&st='+self.st_num,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            res = self.session.get(url=follow_url, headers=headers)
            # slow down the follow speed
            time.sleep(0.2)
            self._assert_error(res)

    def get_max_list_num(self, page_text):
        """
        To get the max number of the follower list with these user
        :param page_text:
        :return: page_num
        """
        soup_list = BeautifulSoup(page_text, "html.parser")
        try:
            max_num = 1
            for value in soup_list.select('input[name="mp"]'):
                max_num = value["value"]
        except AttributeError, e:
            logging.error("caught attribute error %s", e)

        return int(max_num)

    def get_follower_list(self):
        """
        To get the full list of followers
        :return:
        """
        logging.info("Starting get the follower list!")
        follow_url = "http://weibo.cn/" + self.uid + "/follow?vt=4"
        follow_page = self.session.get(follow_url)
        page_num = self.get_max_list_num(follow_page.text)
        url_len = range(1, page_num + 1)
        for n in url_len:
            follow_url = "http://weibo.cn/" + self.uid + "/follow?page=" + str(n)
            if n != 1:
                follow_page = self.session.get(follow_url)
            soup_list = BeautifulSoup(follow_page.text, "html.parser")
            for tag in soup_list.find_all("tr"):
                yield 'screen_name: '+tag.td.next_sibling.a.string

    def search_word(self, key_word, max_page_num=None):
        """
        To get the full pages of the keyword, it has a problem that the first one or two results
        can't analyze since the keyword page not get the original text
        :return:
        """
        logging.info("Starting get the results of %s", key_word)
        keyword_url = "http://weibo.cn/search/mblog?hideSearchFrame=&keyword=" + key_word
        keyword_page = self.session.get(keyword_url)
        page_num = self.get_max_list_num(keyword_page.text)
        if max_page_num and (page_num > max_page_num):
            page_num = max_page_num
        url_len = range(1, page_num + 1)
        for n in url_len:
            keyword_url = "http://weibo.cn/search/mblog?hideSearchFrame=&keyword=" + key_word + "&page=" + str(n)
            if n != 1:
                keyword_page = self.session.get(keyword_url)
            soup_list = BeautifulSoup(keyword_page.text, "html.parser")
            for tag in soup_list.find_all("span"):
                soup_tmp = BeautifulSoup(str(tag).decode('utf-8'), 'html.parser')
                if tag['class'] == [u'ctt']:
                    yield 'screen_name:'+tag.parent.a.string + ',  text:' + soup_tmp.get_text()[1:]

    def _assert_error(self, d):
        """Assert if  response is error.
        """
        if 'error_code' in d and 'error' in d:
            raise RuntimeError("{0} {1}".format(
                d.get("error_code", ""), d.get("error", "")))


if __name__ == "__main__":
    main()