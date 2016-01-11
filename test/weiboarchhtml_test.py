#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Weibowarc_html import WeibowarcHtml

USERNAME = '17090888875'
PASSWORD = 'beijing'

WeiboHtmlTest = WeibowarcHtml(username=USERNAME, password=PASSWORD)


def get_list_test():
    count = 0
    for followers in WeiboHtmlTest.get_follower_list():
        print followers
        count += 1
    print count
    assert count == 6


def search_keyword():
    count = 0
    for followers in WeiboHtmlTest.search_word(key_word=u'郭德纲', max_page_num=10):
        print followers


def follow_test():
    users_id = ['5576276117', '5789331626', '5762461926', '5817859794', '5822897960', '5000726243',
                '1171284121', '5819333684', '5280878510', '2846143823', '2357356234', '3305085281',
                '5680985239', '1907166177', '5357651574', '2873365222', '1789715862', '2099437882',
                '5764871471', '3609443587']
    WeiboHtmlTest.follow_users(uids=users_id)


def unfollow_test():
    users_id = ['5576276117', '5789331626', '5762461926', '5817859794', '5822897960', '5000726243',
                '1171284121', '5819333684', '5280878510', '2846143823', '2357356234', '3305085281',
                '5680985239', '1907166177', '5357651574', '2873365222', '1789715862', '2099437882',
                '5764871471', '3609443587']
    WeiboHtmlTest.unfollow_users(uids=users_id)

#follow_test()
unfollow_test()