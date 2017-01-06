#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester
from weiboarc import Weiboarc
from weibo_warc_iter import WeiboWarcIter
import re

log = logging.getLogger(__name__)

QUEUE = "weibo_harvester"
SEARCH_ROUTING_KEY = "harvest.start.twitter.weibo_search"
TIMELINE_ROUTING_KEY = "harvest.start.twitter.weibo_timeline"
RE_LINKS = re.compile(r'(http://t.cn/[a-zA-z0-9]+)')


class WeiboHarvester(BaseHarvester):
    def __init__(self, working_path, mq_config=None, debug=False, debug_warcprox=False, tries=3):
        BaseHarvester.__init__(self, working_path, mq_config=mq_config, debug=debug, debug_warcprox=debug_warcprox,
                               tries=tries)
        self.weiboarc = None
        # Initial the harvest options.
        self.extract_web_resources = False
        self.extract_images_sizes = []
        self.incremental = False

    def harvest_seeds(self):
        self._create_weiboarc()

        # Get harvest extract options.
        self.extract_web_resources = self.message.get("options", {}).get("web_resources", False)
        self.extract_images_sizes = self.message.get("options", {}).get("image_sizes", [])
        self.incremental = self.message.get("options", {}).get("incremental", False)

        harvest_type = self.message.get("type")
        log.debug("Harvest type is %s", harvest_type)
        if harvest_type == "weibo_timeline":
            self.friends_timeline()
        elif harvest_type == "weibo_search":
            self.search_topic()
        else:
            raise KeyError

    def friends_timeline(self):
        """
        Weibo harvester is considered as a seedless harvester, the harvester message has no seeds info.
        In order to supporting incremental searching, it will use the collection set id to record the
        corresponding since_id.
        """
        # Get since_id flag from collection set id
        collection_set_id = self.message["collection_set"]["id"]
        if len(collection_set_id):
            since_id = self.state_store.get_state(__name__, u"{}.since_id".format(
                self.message["collection_set"]["id"])) if self.incremental else None
            self._harvest_weibos(self.weiboarc.search_friendships(since_id=since_id))

    def search_topic(self):
        assert len(self.message.get("seeds", [])) == 1
        incremental = self.message.get("options", {}).get("incremental", False)
        query = self.message["seeds"][0]["token"]

        since_id = self.state_store.get_state(__name__, u"{}.since_id".format(query)) if incremental else None

        self._harvest_weibos(self.weiboarc.search_topic(query, since_id=since_id))

    def _create_weiboarc(self):
        self.weiboarc = Weiboarc(self.message["credentials"]["access_token"])

    def _harvest_weibos(self, weibos):
        for count, weibo in enumerate(weibos):
            if not count % 100:
                log.debug("Harvested %s weibos", count)
            if "text" in weibo:
                self.result.harvest_counter["weibos"] += 1

    def process_warc(self, warc_filepath):
        harvest_type = self.message.get("type")
        log.debug("Harvest type is %s", harvest_type)
        if harvest_type == "weibo_search":
            self.process_search_warc(warc_filepath)
        elif harvest_type == "weibo_timeline":
            self.process_timeline_warc(warc_filepath)
        else:
            raise KeyError

    def process_search_warc(self, warc_filepath):
        since_weibo_ids = {}
        query = self.message["seeds"][0]["token"]
        key = u"{}.since_id".format(query)
        for count, status in enumerate(WeiboWarcIter(warc_filepath)):
            weibo = status.item
            if not count % 25:
                log.debug("Processing %s weibos", count)
            if "id" in weibo:
                weibo_id = weibo.get("id")
                if not self.incremental:
                    self.result.increment_stats("weibos")
                    self._process_search_options(weibo['retweeted_status'] if 'retweeted_status' in weibo else weibo)
                else:
                    since_id = self.state_store.get_state(__name__, key) or 0
                    if key not in since_weibo_ids:
                        since_weibo_ids[key] = since_id
                    if weibo_id > since_id:
                        # Update state
                        self.state_store.set_state(__name__, key, weibo_id)
                    if weibo_id > since_weibo_ids[key]:
                        self.result.increment_stats("weibos")
                        self._process_search_options(
                            weibo['retweeted_status'] if 'retweeted_status' in weibo else weibo)

    def process_timeline_warc(self, warc_filepath):
        for count, status in enumerate(WeiboWarcIter(warc_filepath)):
            weibo = status.item
            if not count % 100:
                log.debug("Processing %s weibos", count)
            if "text" in weibo:
                self.result.increment_stats("weibos")
                if self.incremental:
                    # Update state
                    key = u"{}.since_id".format(self.message["collection_set"]["id"])
                    self.state_store.set_state(__name__, key,
                                               max(self.state_store.get_state(__name__, key), weibo.get("id")))
                self._process_timeline_options(weibo['retweeted_status'] if 'retweeted_status' in weibo else weibo)

    def _process_search_options(self, weibo):
        # the search statues has a filed named `url_objects`, it contains the urls related to the weibo topic page
        # since weibo has anti-crawler, will not collect the pages in weibo topic pages

        if self.extract_web_resources:
            # URL-1 analyzing the url in text field and adding the short url in lists
            self.result.urls.extend(self._regex_links(weibo['text'].encode('utf-8')))
            # URL-2 adding the long text url
            if 'isLongText' in weibo and weibo['isLongText']:
                self.result.urls.append(
                    'http://m.weibo.cn/' + weibo['user']['idstr'] + '/' + weibo['mid'])

        # a field name `pic_ids` marked all picture id in the posts, need to combine the urls
        # a filed 'thumbnail_pic' has the total url of the pictures like
        # "http://ww3.sinaimg.cn/thumbnail/006pGttogw1fbglhniavcj30m80fc42e.jpg",
        # we need to get the prefix of the url "http://ww3.sinaimg.cn/" first, the piture urls is
        # http://ww3.sinaimg.cn/+picture_size_identify+id+".jpg"
        if len(self.extract_images_sizes) != 0 and 'pic_ids' in weibo and len(weibo['pic_ids']) != 0:
            # get the prefix of the url
            url_str = weibo['thumbnail_pic']
            prefix = url_str[0:url_str.find("thumbnail")]
            # URL-3 adding the photo url with the large size

            if "Large" in self.extract_images_sizes:
                self.result.urls.extend(
                    map(lambda x: "{}large/{}.jpg".format(prefix, x), weibo['pic_ids']))
            if "Medium" in self.extract_images_sizes:
                self.result.urls.extend(
                    map(lambda x: "{}bmiddle/{}.jpg".format(prefix, x), weibo['pic_ids']))
            if "Thumbnail" in self.extract_images_sizes:
                self.result.urls.extend(
                    map(lambda x: "{}thumbnail/{}.jpg".format(prefix, x), weibo['pic_ids']))

    def _process_timeline_options(self, weibo):
        if self.extract_web_resources:
            # URL-1 analyzing the url in text field and adding the short url in lists
            self.result.urls.extend(self._regex_links(weibo['text'].encode('utf-8')))
            # URL-2 adding the long text url
            if 'isLongText' in weibo and weibo['isLongText']:
                self.result.urls.append(
                    'http://m.weibo.cn/' + weibo['user']['idstr'] + '/' + weibo['mid'])
        if len(self.extract_images_sizes) != 0 and 'pic_urls' in weibo:
            # URL-3 adding the photo url with the large size
            if "Large" in self.extract_images_sizes:
                self.result.urls.extend(
                    map(lambda x: x['thumbnail_pic'].replace('thumbnail', 'large'), weibo['pic_urls']))
            if "Medium" in self.extract_images_sizes:
                self.result.urls.extend(
                    map(lambda x: x['thumbnail_pic'].replace('thumbnail', 'bmiddle'), weibo['pic_urls']))
            if "Thumbnail" in self.extract_images_sizes:
                self.result.urls.extend(
                    map(lambda x: x['thumbnail_pic'], weibo['pic_urls']))

    @staticmethod
    def _regex_links(text):
        """
        A list of bare urls from weibo text
        """
        return RE_LINKS.findall(text)


if __name__ == "__main__":
    WeiboHarvester.main(WeiboHarvester, QUEUE, [SEARCH_ROUTING_KEY, TIMELINE_ROUTING_KEY])
