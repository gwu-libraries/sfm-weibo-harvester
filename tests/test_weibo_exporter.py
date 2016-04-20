#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import tests
from tests.weibos import weibo2
from weibo_exporter import WeiboStatusTable
from datetime import datetime


class TestWeiboStatusTable(tests.TestCase):
    def test_exporter_row(self):
        table = WeiboStatusTable(None, None, None, None, None)
        row = table._row(weibo2)
        self.assertIsInstance(row[0], datetime)
        self.assertEqual("3928235789939265", row[1])
        self.assertEqual("\u5929\u72fc50\u9648\u6d69", row[2])
        self.assertEqual(679396, row[3])
        self.assertEqual(837, row[4])
        self.assertEqual(72, row[5])
        self.assertEqual("Victor Tan, \u4eba\u6c11\u65e5\u62a5", row[6])
        self.assertEqual("http://m.weibo.cn/2244733937/3928235789939265", row[8])
        self.assertEqual("#Victor Tan##\u4eba\u6c11\u65e5\u62a5# "
                         "\u7591\u4f3c\u90a3\u5565\u4e86\u4e00\u6b21\u3002 http://t.cn/RGzPJYq",
                         row[9])
        self.assertEqual("http://t.cn/RGzPJYq", row[10])