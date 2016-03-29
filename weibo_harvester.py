#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester
from weiboarc import Weiboarc
import re
import time

log = logging.getLogger(__name__)

QUEUE = "weibo_harvester"
ROUTING_KEY = "harvest.start.weibo.*"
RE_LINKS = re.compile(r'(http://t.cn/[a-zA-z0-9]+)')


class WeiboHarvester(BaseHarvester):
    def __init__(self, process_interval_secs=1200, mq_config=None, debug=False):
        BaseHarvester.__init__(self, mq_config=mq_config, process_interval_secs=process_interval_secs, debug=debug)
        self.weiboarc = None

    def harvest_seeds(self):
        self._create_weiboarc()

        harvest_type = self.message.get("type")
        log.debug("Harvest type is %s", harvest_type)
        if harvest_type == "weibo_timeline":
            self.search_timeline()
        else:
            raise KeyError

    def search_timeline(self):
        incremental = self.message.get("options", {}).get("incremental", False)

        # Get since_id from state_store
        since_id = self.state_store.get_state(__name__, "weibo.since_id") if incremental else None
        max_weibo_id = self._process_weibos(self.weiboarc.search_friendships(since_id=since_id))
        log.debug("Searching since %s returned %s weibo.",
                  since_id, self.harvest_result.summary.get("weibo"))

        # Update state store
        if incremental and max_weibo_id:
            self.state_store.set_state(__name__, "weibo.since_id", max_weibo_id)

    def _create_weiboarc(self):
        self.weiboarc = Weiboarc(self.message["credentials"]["api_key"],
                                 self.message["credentials"]["api_secret"],
                                 self.message["credentials"]["redirect_uri"],
                                 self.message["credentials"]["access_token"])

    def _process_weibos(self, weibos):
        max_weibo_id = None
        res_url_list = []
        for count, weibo in enumerate(weibos):
            if not count % 100:
                log.debug("Processed %s weibo", count)
            if "text" in weibo:
                with self.harvest_result_lock:
                    max_weibo_id = max(max_weibo_id, weibo['id'])
                    self.harvest_result.increment_summary("weibo")
                    # URL-1 analyzing the url in text field and adding the short url in lists
                    res_url_list.extend(self._regex_links(weibo['text'].encode('utf-8')))
                    # URL-2 adding the photo url, how to solve the corresponding relation to each posts?
                    if 'pic_urls' in weibo:
                        self.harvest_result.urls.extend(
                            map(lambda x: x['thumbnail_pic'].replace('thumbnail', 'large'), weibo['pic_urls']))
                    # URL-3 adding the long text url
                    if 'isLongText' in weibo and weibo['isLongText']:
                        self.harvest_result.urls.append(
                            'http://m.weibo.cn/' + weibo['user']['idstr'] + '/' + weibo['mid'])

                    # Retweeted_status Analysis
                    if 'retweeted_status' in weibo:
                        # URL-1 analyzing the url in text field and adding the short url in lists
                        res_url_list.extend(self._regex_links(weibo['retweeted_status']['text'].encode('utf-8')))
                        # URL-2 adding the photo url, how to solve the corresponding relation to each posts?
                        if 'pic_urls' in weibo['retweeted_status']:
                            self.harvest_result.urls.extend(
                                map(lambda x: x['thumbnail_pic'].replace('thumbnail', 'large'),
                                    weibo['retweeted_status']['pic_urls']))
                        # URL-3 adding the long text url
                        if 'isLongText' in weibo['retweeted_status'] and weibo['retweeted_status']['isLongText']:
                            self.harvest_result.urls.append(
                                'http://m.weibo.cn/' + weibo['retweeted_status']['user']['idstr'] + '/' +
                                weibo['retweeted_status']['mid'])

        # Expanding the short text links to the result
        # The weibo expanding url api supporting max 20 short urls in one call
        with self.harvest_result_lock:
            url_chunks_list = [res_url_list[i:i + 20] for i in xrange(0, len(res_url_list), 20)]
            for li in url_chunks_list:
                # Using map to reduce the list operations
                self.harvest_result.urls.extend(map(lambda x: x["url_long"], self.weiboarc.get_long_urls(li)))
                time.sleep(0.01)
        return max_weibo_id

    def _regex_links(self, text):
        """
        A list of bare urls from weibo text
        """
        return RE_LINKS.findall(text)


if __name__ == "__main__":
    WeiboHarvester.main(WeiboHarvester, QUEUE, [ROUTING_KEY])
