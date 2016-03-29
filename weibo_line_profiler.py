from weibo_harvester import WeiboHarvester
from sfmutils.state_store import DictHarvestStateStore
from sfmutils.harvester import HarvestResult
import threading
import tests


class TestWeiboHarvesterProfiler(object):
    def __init__(self):
        self.harvester = WeiboHarvester()
        self.harvester.state_store = DictHarvestStateStore()
        self.harvester.harvest_result = HarvestResult()
        self.harvester.stop_event = threading.Event()
        self.harvester.harvest_result_lock = threading.Lock()
        self.harvester.message = {
            "id": "test:2",
            "type": "weibo_timeline",
            "credentials": {
                "api_key":  tests.WEIBO_API_KEY,
                "api_secret": tests.WEIBO_API_SECRET,
                "redirect_uri": tests.WEIBO_REDIRECT_URI,
                "access_token": tests.WEIBO_ACCESS_TOKEN
            },
            "collection": {
                "id": "test_collection",
                "path": "/collections/test_collection"
            },
            "options": {}
        }

    def test_search(self):
        self.harvester.harvest_seeds()


if __name__ == "__main__":
    test = TestWeiboHarvesterProfiler()
    test.test_search()