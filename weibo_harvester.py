#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
from sfmutils.harvester import BaseHarvester

log = logging.getLogger(__name__)


class WeiboHarvester(BaseHarvester):
    def __init__(self, process_interval_secs=1200, mq_config=None, debug=False):
        BaseHarvester.__init__(self, mq_config=mq_config, process_interval_secs=process_interval_secs, debug=debug)
        self.weibowarc = None

    def harvest_seeds(self):
        pass

    def search(self):
        pass

    def filter(self):
        pass