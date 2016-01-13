#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester
from weibowarc import Weibowarc

log = logging.getLogger(__name__)

QUEUE = "weibo_harvester"
ROUTING_KEY = "harvest.start.weibo.timeline_search"


class WeiboHarvester(BaseHarvester):
    def __init__(self, process_interval_secs=1200, mq_config=None, debug=False):
        BaseHarvester.__init__(self, mq_config=mq_config, process_interval_secs=process_interval_secs, debug=debug)
        self.weibowarc = None

    def harvest_seeds(self):
        self._create_weibowarc()

        harvest_type = self.message.get("type")
        log.debug("Harvest type is %s", harvest_type)
        if harvest_type == "weibo_timeline":
            self.search_timeline()
        else:
            raise KeyError

    def search_timeline(self):
        incremental = self.message.get("options", {}).get("incremental", False)

        # Get since_id from state_store
        since_id = self.state_store.get_state(__name__, "{}.since_id".format('weibo')) if incremental else None
        max_weibo_id = self._process_tweets(self.weibowarc.search_friendships(since_id=since_id))
        log.debug("Searching since %s returned %s weibo.",
                    since_id, self.harvest_result.summary.get("weibo"))

        # Update state store
        if incremental and max_weibo_id:
                self.state_store.set_state(__name__, "{}.since_id".format('weibo'), max_weibo_id)

    def _create_weibowarc(self):
        self.weibowarc = Weibowarc(self.message["credentials"]["api_key"],
                                   self.message["credentials"]["api_secret"],
                                   self.message["credentials"]["redirect_uri"],
                                   self.message["credentials"]["access_token"])

    def _process_tweets(self, weibos):
        max_weibo_id = None
        for count, weibo in enumerate(weibos):
            if not count % 150:
                log.debug("Processed %s weibo", count)
            if self.stop_event.is_set():
                log.debug("Stopping since stop event set.")
                break
            if "text" in weibo:
                with self.harvest_result_lock:
                    max_weibo_id = max(max_weibo_id, weibo[u"mid"])
                    self.harvest_result.increment_summary("weibo")

        return max_weibo_id


if __name__ == "__main__":
    WeiboHarvester.main(WeiboHarvester, QUEUE, [ROUTING_KEY])