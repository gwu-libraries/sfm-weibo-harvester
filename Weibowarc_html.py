#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


class WeibowarcHtml(object):
    """
    WeibowarcHtml allows you to login weibo to mobile page using
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
        self.uid = soup.find("div", "tip2").a["href"].split('/')[1]

        logging.info("Login successful...")

    def follow_users(self, uids):
        """
        Try to follow the special uid in the html ways.But it won't work!!, it needs the access code verification
        --Testing function--
        :return:
        """
        for uid in uids:
            follow_url = 'http://weibo.cn/attention/add'
            data = {"uid": uid,
                      'rl': 0,
                      }
            headers = {
                'Referer': 'http://weibo.cn/' + uid+'follow',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            res = self.session.post(url=follow_url, data=data, headers=headers)
            page_text = res.text
            print page_text
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
                yield tag.td.next_sibling.a.string

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
                    yield tag.parent.a.string + ',' + soup_tmp.get_text()[1:]

    def _assert_error(self, d):
        """Assert if  response is error.
        """
        if 'error_code' in d and 'error' in d:
            raise RuntimeError("{0} {1}".format(
                d.get("error_code", ""), d.get("error", "")))
