#!/usr/bin/env python

from __future__ import absolute_import
import sys
import json
import re
from sfmutils.warc_iter import BaseWarcIter
from dateutil.parser import parse as date_parse

RE_MENTIONS = re.compile(ur'@[\w\\\s\u4e00-\u9fff]+')
RE_LINKS = re.compile(r'(http://t.cn/[a-zA-z0-9]+)')
RE_TOPIC = re.compile(ur'#[\w\\\s\u4e00-\u9fff]+#')


class WeiboWarcIter(BaseWarcIter):
    def __init__(self, file_paths, limit_user_ids=None):
        BaseWarcIter.__init__(self, file_paths)
        self.limit_user_ids = limit_user_ids

    def _select_record(self, url):
        return url.startswith("https://api.weibo.com/2")

    def _item_iter(self, url, json_obj):
        for status in json_obj["statuses"]:
            yield "weibo_status", status["mid"], date_parse(status["created_at"]), status

    @staticmethod
    def item_types():
        return ["weibo_status"]

    def _select_item(self, item):
        if not self.limit_user_ids or item.get("user", {}).get("idstr") in self.limit_user_ids:
            return True
        return False

    def print_elk_warc_iter(self, pretty=False, fp=sys.stdout, limit_item_types=None, print_item_type=False,
                            dedupe=True):
        for item_type, _, _, _, item in self.iter(limit_item_types=limit_item_types, dedupe=dedupe):
            if print_item_type:
                fp.write("{}:".format(item_type))
            json.dump(self._row(item), fp, indent=4 if pretty else None)
            fp.write("\n")

    def print_elk_json_iter(self, pretty=False, fp=sys.stdout):
        for filepath in self.filepaths:
            with open(filepath, 'r') as f:
                for line in f:
                    json.dump(self._row(json.loads(line)), fp, indent=4 if pretty else None)
                    fp.write("\n")

    def _row(self, item):
        # rows sm_type: \"weibo\", id: .mid, user_id: .user.idstr,
        # screen_name: .user.screen_name, created_at: .created_at, text: .text
        row = {"sm_type": "weibo", 'id': item["mid"], 'user_id': item["user"]["idstr"],
               'screen_name': (item['user']['screen_name'],), 'created_at': item['created_at'], 'text': item['text'],
               'followers_count': item['user']['followers_count'], 'friends_count': item['user']['friends_count'],
               'topics': [topic[1:-1] for topic in self._regex_topic(item['text'])],
               'urls': self._regex_links(item['text']), 'location': item['user']['location'],
               'user_mentions': [mention[1:] for mention in self._regex_mentions(item['text'])]}
        return row

    def _regex_links(self, text):
        """
        A list of bare urls from weibo text
        """
        return RE_LINKS.findall(text)

    def _regex_topic(self, text):
        """
        A list of topic from weibo text
        """
        return RE_TOPIC.findall(text)

    def _regex_mentions(self, text):
        """
        A list of user mentions from weibo text
        """
        return RE_MENTIONS.findall(text)

if __name__ == "__main__":
    WeiboWarcIter.main(WeiboWarcIter)