#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sfmutils.exporter import ExportResult, BaseExporter, BaseTable
from weibo_warc_iter import WeiboWarcIter
import logging
from dateutil.parser import parse as date_parse


log = logging.getLogger(__name__)

QUEUE = "weibo_exporter"
TIMELINE_ROUTING_KEY = "export.start.weibo.weibo_timeline"


class WeiboStatusTable(BaseTable):
    """
    Assume rows status for weibo
    """
    def __init__(self, warc_paths, dedupe, item_date_start, item_date_end, seed_uids):
        BaseTable.__init__(self, warc_paths, dedupe, item_date_start, item_date_end, seed_uids, WeiboWarcIter)

    def _header_row(self):
        return ('created_at', 'weibo_id',
                'screen_name', 'followers_count', 'friends_count',
                'retweet_count',
                'weibo_url', 'text',
                'url1', 'url2')

    def _row(self, item):
        row = [date_parse(item["created_at"]),
               item["mid"],
               item['user']['screen_name'],
               item['user']['followers_count'],
               item['user']['friends_count'],
               item['reposts_count'],
               'http://m.weibo.cn/{}/{}'.format(item["user"]["id_str"], item["mid"]),
               item['text'].replace('\n', ' ')
               ]
        for url in item['pic_urls']['urls'][:2]:
            row.extend([url['url']])
        return row


class WeiboExporter(BaseExporter):
    def __init__(self, api_base_url, mq_config=None, warc_base_path=None):
        BaseExporter.__init__(self, api_base_url, WeiboWarcIter, WeiboStatusTable, mq_config=mq_config,
                              warc_base_path=warc_base_path)

if __name__ == "__main__":
    WeiboExporter.main(WeiboExporter, QUEUE, [TIMELINE_ROUTING_KEY])