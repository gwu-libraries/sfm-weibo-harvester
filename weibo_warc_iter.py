#!/usr/bin/env python

from __future__ import absolute_import
from sfmutils.warc_iter import BaseWarcIter


class WeiboWarcIter(BaseWarcIter):
    def _select_record(self, url):
        return url.startswith("https://api.weibo.com/2")

    def _item_iter(self, url, json_obj):
        for status in json_obj["statuses"]:
            yield "weibo_status", status

    @staticmethod
    def item_types():
        return ["weibo_status"]

if __name__ == "__main__":
    WeiboWarcIter.main(WeiboWarcIter)