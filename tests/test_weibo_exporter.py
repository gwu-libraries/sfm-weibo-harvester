#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import tests
import vcr as base_vcr
from tests.weibos import weibo2
from weibo_exporter import WeiboExporter, WeiboStatusTable
from datetime import datetime
import os
import tempfile
import shutil

vcr = base_vcr.VCR(
    cassette_library_dir='tests/fixtures',
    record_mode='once',
)


class TestWeiboStatusTable(tests.TestCase):
    def test_exporter_row(self):
        table = WeiboStatusTable(None, None, None, None, None, None)
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
        self.assertEqual("retweeted text http://t.cn/URL1Test  http://t.cn/URL2Test", row[12])
        self.assertEqual("http://t.cn/URL1Test", row[13])
        self.assertEqual("http://t.cn/URL2Test", row[14])


class TestWeiboExporterVcr(tests.TestCase):
    def setUp(self):
        self.warc_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warcs")
        self.working_path = tempfile.mkdtemp()
        self.exporter = WeiboExporter("http://127.0.0.1:8080", self.working_path, warc_base_path=self.warc_base_path)
        self.exporter.routing_key = "export.request.weibo.weibo_timeline"
        self.export_path = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.export_path):
            shutil.rmtree(self.export_path)
        if os.path.exists(self.working_path):
            shutil.rmtree((self.working_path))

    @vcr.use_cassette()
    def test_export_collection(self):
        export_message = {
            "id": "test1",
            "type": "weibo_timeline",
            "collection": {
                "id": "afe49fc673ab4380909e06f43b46a990"
            },
            "format": "csv",
            "segment_size": None,
            "path": self.export_path
        }

        self.exporter.message = export_message
        self.exporter.on_message()

        self.assertTrue(self.exporter.result.success)
        csv_filepath = os.path.join(self.export_path, "test1_001.csv")
        self.assertTrue(os.path.exists(csv_filepath))
        with open(csv_filepath, "r") as f:
            lines = f.readlines()
        self.assertEqual(182, len(lines))


class TestWeiboStatusTableVcr(tests.TestCase):
    def setUp(self):
        warc_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warcs/2/2016/04/24")
        self.warc_paths = (os.path.join(warc_base_path,
                                        "17/3a3f522447d1482f8f8dd0018b00bd35-20160424170028814-00000-6389-bf4e6baa25b2"
                                        "-8000.warc.gz"),
                           os.path.join(warc_base_path,
                                        "17/5d8ea69b354444c699df6e984eb83825-20160424174045758-00000-6407-bf4e6baa25b2"
                                        "-8000.warc.gz"),
                           os.path.join(warc_base_path,
                                        "17/3a3f522447d1482f8f8dd0018b00bd35-20160424170028814-00000-6389-bf4e6baa25b2"
                                        "-8000.warc.gz"))

    def test_table(self):
        tables = WeiboStatusTable(self.warc_paths, False, None, None, None, segment_row_size=3)
        chunk_count = total_count = 0
        for idx, table in enumerate(tables):
            chunk_count += 1
            for count, row in enumerate(table):
                total_count += 1
                if count == 0:
                    # check the fields on the right way
                    self.assertEqual("created_at", row[0])
                    self.assertEqual("topics", row[6])
                if idx == 0 and count == 2:
                    # testing the second row
                    self.assertEqual("3967949742420016", row[1])
                    self.assertEqual("http://m.weibo.cn/1635386337/3967949742420016", row[8])
                    self.assertEqual(u"看到这个视频，是我联想到我们上学时学到的课文《卖炭翁》！[伤心][话筒]", row[9])
                if idx == 2 and count == 1:
                    # testing the second row
                    self.assertEqual("3967949008693275", row[1])
        self.assertEqual(3, chunk_count)
        # 1+3,1+3,1+1
        self.assertEqual(10, total_count)
