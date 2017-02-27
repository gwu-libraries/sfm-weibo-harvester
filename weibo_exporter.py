#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sfmutils.exporter import ExportResult, BaseExporter, BaseTable
from weibo_warc_iter import WeiboWarcIter
import logging
import re
from dateutil.parser import parse as date_parse

log = logging.getLogger(__name__)

QUEUE = "weibo_exporter"
SEARCH_ROUTING_KEY = "export.start.weibo.weibo_search"
TIME_LINE_ROUTING_KEY = "export.start.weibo.weibo_timeline"
RE_LINKS = re.compile(r'(http://t.cn/[a-zA-z0-9]+)')
RE_TOPIC = re.compile(ur'#[\w\\\s\u4e00-\u9fff]+#')


class WeiboStatusTable(BaseTable):
    """
    Assume rows status for weibo
    """

    def __init__(self, warc_paths, dedupe, item_date_start, item_date_end, seed_uids, segment_row_size=None):
        BaseTable.__init__(self, warc_paths, dedupe, item_date_start, item_date_end, seed_uids, WeiboWarcIter,
                           segment_row_size)

    def _header_row(self):
        return ('created_at', 'weibo_id', 'screen_name',
                'followers_count', 'friends_count', 'reposts_count',
                'topics',
                'in_reply_to_screen_name',
                'weibo_url',
                'text',
                'url1',
                'url2',
                'retweeted_text',
                'retweeted_url1',
                'retweeted_url2')

    def _row(self, item):
        row = [date_parse(item["created_at"]),
               item["mid"],
               item['user']['screen_name'],
               item['user']['followers_count'],
               item['user']['friends_count'],
               item['reposts_count'],
               ', '.join(topic[1:-1] for topic in self._regex_topic(item['text'])),
               item['in_reply_to_screen_name'] or '',
               'http://m.weibo.cn/{}/{}'.format(item["user"]["idstr"], item["mid"]),
               item['text'],
               ]
        text_url = self._regex_links(item['text'])[:2]
        row.extend(text_url + [''] * (2 - len(text_url)))

        # adding two sample urls in retweeted_status text
        if 'retweeted_status' in item:
            row.extend([item['retweeted_status']['text']])
            row.extend(self._regex_links(item['retweeted_status']['text'])[:2])
        return row

    def id_field(self):
        return "weibo_id"

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


class WeiboExporter(BaseExporter):
    def __init__(self, api_base_url, working_path, mq_config=None, warc_base_path=None):
        BaseExporter.__init__(self, api_base_url, WeiboWarcIter, WeiboStatusTable, working_path,
                              mq_config=mq_config, warc_base_path=warc_base_path)


if __name__ == "__main__":
    WeiboExporter.main(WeiboExporter, QUEUE, [SEARCH_ROUTING_KEY, TIME_LINE_ROUTING_KEY])
