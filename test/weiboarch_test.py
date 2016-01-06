#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Weibowarc import Weibowarc
import logging
import time

api_key = '3252156855'
api_secret = '4c6f6c568ad9ef6b6a81c42b172707b1'
redirect_uri = 'https://www.google.com/'
token={u'access_token': u'2.00kQCxKGpYiFYDc41039481c0wvwei',
       u'remind_in': u'157679999', u'uid': u'5658630430',
       u'expires_at': 1609785214}

weibotest = Weibowarc(api_key, api_secret, redirect_uri, token)

logging.basicConfig(filename="test.log", level=logging.INFO)


def test_get_friendship():
    count=0
    for weibo in weibotest.search_friendships():
        assert weibo[u'mid']
        count += 1
        if count == 100:
            break

    assert count == 100


def test_since_id():
    count=0
    for weibo in weibotest.search_friendships():
        mid = weibo[u'mid']
        count += 1
        if count == 10:
            break

    assert mid
    time.sleep(5)

    count=0
    for weibo in weibotest.search_friendships(since_id=id):
        print 'new_id [%s], pre_id [%s]' % (weibo[u'mid'], mid)
        assert weibo[u'mid'] > mid
        count += 1
        if count == 9:
            break


def test_max_id():
    for weibo in weibotest.search_friendships():
        mid = weibo[u'mid']
        break
    assert mid
    time.sleep(5)

    count = 0
    for weibo in weibotest.search_friendships(max_id=mid):
        count += 1
        assert weibo[u'mid'] <= mid
        if count > 100:
            break


def test_max_and_since_ids():
    max_id = since_id = None
    count = 0
    for weibo in weibotest.search_friendships():
        count += 1
        if not max_id:
            max_id = weibo[u'mid']
        since_id = weibo[u'mid']
        if count == 50:
            break
    count = 0
    for weibo in weibotest.search_friendships(max_id=max_id, since_id=since_id):
        count += 1
        assert weibo[u'mid'] <= max_id
        assert weibo[u'mid'] > since_id


def test_page():
    # pages are 100 weibo post but total we can get 150
    count = 0
    for weibo in weibotest.search_friendships():
        #print ("[%s],[%s],%s,%s" % (weibo[u'created_at'], weibo[u'id'], weibo[u'user'][u'screen_name'], weibo[u'text']))
        count += 1
        if count == 150:
            break
    assert count == 150


def test_friends_list():
    users = [u'庆中V', u'阿倪家蛋糕店', u'石述思 ', u'阜阳太和公安在线', u'邓超', u'天狼50陈浩']
    found = False
    for weibo in weibotest.search_friends_list():
        assert weibo[u'screen_name']
        if weibo[u'screen_name'] in users:
            found = True
        break

    assert found


def test_friends_list_all():
    users = [u'庆中V', u'阿倪家蛋糕店', u'石述思 ', u'阜阳太和公安在线', u'邓超', u'天狼50陈浩']
    count = 0
    for weibo in weibotest.search_friends_list():
        if weibo[u'screen_name'] in users:
            count += 1

    assert count == len(users)

# test_get_friendship()
# test_since_id()
# test_max_and_since_ids()
# test_friends_list_all()