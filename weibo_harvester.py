#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester
from weiboarc import Weiboarc
import re

log = logging.getLogger(__name__)

QUEUE = "weibo_harvester"
ROUTING_KEY = "harvest.start.weibo.*"
RE_LINKS = re.compile(r'(http://t.cn/[a-zA-z0-9]+)')


class WeiboHarvester(BaseHarvester):
    def __init__(self, mq_config=None, debug=False):
        BaseHarvester.__init__(self, mq_config=mq_config, debug=debug)
        self.weiboarc = None
        # Initial the harvest options.
        self.extract_media = False
        self.extract_web_resources = False

    def harvest_seeds(self):
        self._create_weiboarc()

        # Get harvest extract options.
        self.extract_media = self.message.get("options", {}).get("media", False)
        self.extract_web_resources = self.message.get("options", {}).get("web_resources", False)

        harvest_type = self.message.get("type")
        log.debug("Harvest type is %s", harvest_type)
        if harvest_type == "weibo_timeline":
            self.search_timeline()
        else:
            raise KeyError

    def search_timeline(self):
        incremental = self.message.get("options", {}).get("incremental", False)

        """
        Weibo harvester is considered as a seedless harvester, the harvester message has no seeds info.
        In order to supporting incremental searching, it will use the collection id to record the
        corresponding since_id.
        """
        # Get since_id flag from collection id
        collections_id = self.message["collection"]["id"]
        if len(collections_id):
            query = collections_id
            since_id = self.state_store.get_state(__name__, u"{}.since_id".format(query)) if incremental else None
            max_weibo_id = self._process_weibos(self.weiboarc.search_friendships(since_id=since_id))
            log.debug("Searching since %s returned %s weibo.",
                      since_id, self.harvest_result.summary.get("weibo"))

            # Update state store
            if incremental and max_weibo_id:
                self.state_store.set_state(__name__, u"{}.since_id".format(query), max_weibo_id)

    def _create_weiboarc(self):
        self.weiboarc = Weiboarc(self.message["credentials"]["api_key"],
                                 self.message["credentials"]["api_secret"],
                                 self.message["credentials"]["redirect_uri"],
                                 self.message["credentials"]["access_token"])

    def _process_weibos(self, weibos):
        max_weibo_id = None
        for count, weibo in enumerate(weibos):
            if not count % 100:
                log.debug("Processed %s weibo", count)
            if "text" in weibo:
                max_weibo_id = max(max_weibo_id, weibo['id'])
                self.harvest_result.increment_summary("weibo")
                self._process_options(weibo['retweeted_status'] if 'retweeted_status' in weibo else weibo)

        return max_weibo_id

    def _process_options(self, weibo):
        if self.extract_web_resources:
            # URL-1 analyzing the url in text field and adding the short url in lists
            self.harvest_result.urls.extend(self._regex_links(weibo['text'].encode('utf-8')))
            # URL-2 adding the long text url
            if 'isLongText' in weibo and weibo['isLongText']:
                self.harvest_result.urls.append(
                     'http://m.weibo.cn/' + weibo['user']['idstr'] + '/' + weibo['mid'])
        if self.extract_media and 'pic_urls' in weibo:
            # URL-3 adding the photo url with the large size
            self.harvest_result.urls.extend(
                map(lambda x: x['thumbnail_pic'].replace('thumbnail', 'large'), weibo['pic_urls']))

    def _regex_links(self, text):
        """
        A list of bare urls from weibo text
        """
        return RE_LINKS.findall(text)


if __name__ == "__main__":
    WeiboHarvester.main(WeiboHarvester, QUEUE, [ROUTING_KEY])
