# sfm-weibo-harvester
A basic harvester for Sina Weibo public post data as part of Social Feed Manager. 

[![Build Status](https://travis-ci.org/gwu-libraries/sfm-weibo-harvester.svg?branch=master)](https://travis-ci.org/gwu-libraries/sfm-weibo-harvester)

Provides harvesters for [Sina Weibo API](http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI) and [Html Parser](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

Harvesting is performed by [weibowarc](https://github.com/gwu-libraries/weibowarc).

The weibowarchtml is just a possible solution for any exist limitation problem. If possible, the weibo harvester will rely mostly on the API calling.
# Install
```bash
git clone https://github.com/gwu-libraries/sfm-weibo-harvester
cd sfm-weibo-harvester
pip install -r requirements.txt
```

# Testing
* Install [Docker](https://docs.docker.com/installation/) and [Docker-Compose](https://docs.docker.com/compose/install/)
* Geting the `API_KEY`, `API_SECRET`, `REDIRECT_URI`, `ACCESS_TOKEN`, refer to  [weibowarc](https://github.com/gwu-libraries/weibowarc)
* Start up the containers
```bash
docker-compose -f docker/dev.docker-compose.yml up -d
```
* Running the tests
```bash
docker exec sfmdocker_sfmweiboharvester_1 python -m unittest discover
```
* Check the logs
```bash
docker-compose -f docker/dev.docker-compose.yml logs
```
* Shutdown all the containers and clear what you have done
```bash
docker-compose -f docker/dev.docker-compose.yml kill
docker-compose -f docker/dev.docker-compose.yml rm -v --force
docker rmi $(docker images -q)
```

# Harvest start messages
The necessary information to construct a harvest start message for the weibo harvester.

### Search friend timeline harvest type
**Type**

* weibo_timeline

**API called**

* statuses/friends_timeline

**Optional parameters**

* incremental: True (default) or False

**Summary**

* count for weibos
