#!/usr/bin/env python3

from __future__ import absolute_import
from sfmutils.warc_iter import BaseWarcIter
from dateutil.parser import parse as date_parse


class WeiboWarcIter(BaseWarcIter):
    def __init__(self, file_paths, limit_user_ids=None):
        BaseWarcIter.__init__(self, file_paths)
        self.limit_user_ids = limit_user_ids

    def _select_record(self, url):
        return url.startswith("https://api.weibo.com/2")

    def _item_iter(self, url, json_obj):
        if isinstance(json_obj, dict) and ('error' in json_obj):
            return
        for status in json_obj["statuses"]:
            yield "weibo_status", status["mid"], date_parse(status["created_at"]), status

    @staticmethod
    def item_types():
        return ["weibo_status"]

    def _select_item(self, item):
        if not self.limit_user_ids or item.get("user", {}).get("idstr") in self.limit_user_ids:
            return True
        return False


if __name__ == "__main__":
    WeiboWarcIter.main(WeiboWarcIter)
