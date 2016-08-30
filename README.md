# sfm-weibo-harvester
A basic harvester for Sina Weibo public post data as part of [Social Feed Manager](https://gwu-libraries.github.io/sfm-ui). 

[![Build Status](https://travis-ci.org/gwu-libraries/sfm-weibo-harvester.svg?branch=master)](https://travis-ci.org/gwu-libraries/sfm-weibo-harvester)

Provides harvesters for [Sina Weibo API](http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI) and harvesting is performed by weiboarc.

## Development

For information on development and running tests, see the [development documentation](http://sfm.readthedocs.io/en/latest/development.html).

When running tests, provide Weibo credentials either as a `test_config.py` file or environment variables (`WEIBO_ACCESS_TOKEN`).
An example `test_config.py` looks like:

   WEIBO_ACCESS_TOKEN = "2.kQCxKsdpYiFYDc41039481c0fi"


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

### Authentication

Required parameters:

* access_token
