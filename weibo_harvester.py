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
SEARCH_ROUTING_KEY = "harvest.start.weibo.weibo_search"
TIMELINE_ROUTING_KEY = "harvest.start.weibo.weibo_timeline"


class WeiboHarvester(BaseHarvester):
    def __init__(self, working_path, mq_config=None, debug=False, debug_warcprox=False, tries=3):
        BaseHarvester.__init__(self, working_path, mq_config=mq_config, debug=debug, debug_warcprox=debug_warcprox,
                               tries=tries)
        self.weiboarc = None
        self.incremental = False

    def harvest_seeds(self):
        self._create_weiboarc()

        # Get harvest extract options.
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
                else:
                    since_id = self.state_store.get_state(__name__, key) or 0
                    if key not in since_weibo_ids:
                        since_weibo_ids[key] = since_id
                    if weibo_id > since_id:
                        # Update state
                        self.state_store.set_state(__name__, key, weibo_id)
                    if weibo_id > since_weibo_ids[key]:
                        self.result.increment_stats("weibos")

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


if __name__ == "__main__":
    WeiboHarvester.main(WeiboHarvester, QUEUE, [SEARCH_ROUTING_KEY, TIMELINE_ROUTING_KEY])
