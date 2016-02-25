# sfm-weibo-harvester
A basic harvester for Sina Weibo public post data as part of Social Feed Manager. 

[![Build Status](https://travis-ci.org/gwu-libraries/sfm-weibo-harvester.svg?branch=master)](https://travis-ci.org/gwu-libraries/sfm-weibo-harvester)

Provides harvesters for [Sina Weibo API](http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI) and [Html Parser](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

Harvesting is performed by weiboarc.

The [weiboarchtml](#weiboarchtml) is just a possible solution for any exist limitation problem. If possible, the weibo harvester will rely mostly on the API calling.

# Install
```bash
git clone https://github.com/gwu-libraries/sfm-weibo-harvester
cd sfm-weibo-harvester
pip install -r requirements/requirements.txt
```

# Ready to work
* Sign up for a Sina developer account at [Sina Development Platform](http://open.weibo.com/apps) to create a new app.
* Get the information about `WEIBO_API_KEY`, `WEIBO_API_SECRET`, `WEIBO_REDIRECT_URI`,`WEIBO_ACCESS_TOKEN`.
* The corresponding information got from the guide is no prefix `WEIBO_`.
* How to get these information you can refer to the [Guide for Using Weibo API](http://tanych.github.io/weibo/apiguide/).

# Following the users manually  
*  Login sina weibo account at [here](http://weibo.com)
*  Search the users you want to follow
![Image of search](images/follow-step-1.jpg?raw=true)
*  Click the follow button
![Image of follow](images/follow-step-2.jpg?raw=true)

# Testing
## Unit testing
Running the unittest command in bash.
```bash
python -m unittest discover
```

## Integration tests in docker containers
* Install [Docker](https://docs.docker.com/installation/) and [Docker-Compose](https://docs.docker.com/compose/install/)

* Provide  the `WEIBO_API_KEY`, `WEIBO_API_SECRET`, `WEIBO_REDIRECT_URI`, `WEIBO_ACCESS_TOKEN` to the tests. This can be done either by putting them in a file named test_config.py or in environment variables (`WEIBO_API_KEY`, `WEIBO_API_SECRET`, `WEIBO_REDIRECT_URI`, `WEIBO_ACCESS_TOKEN`). An example test_config.py looks like:
```python
WEIBO_API_KEY = "123456789"
WEIBO_API_SECRET = "34567890123312"
WEIBO_REDIRECT_URI = "https://www.google.com"
WEIBO_ACCESS_TOKEN = "2.kQCxKsdpYiFYDc41039481c0fi"
```

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


#Weiboarchtml

**Marked as invalid since the login page adding the verify code, update 02/17/2016**

##How to use
To use the weiboarchtml, you need to give your `USERNAME`,`PASSWORD` with your sina account  

##Getting a full list of followers
Usually, It can call the [friends API](http://open.weibo.com/wiki/2/friendships/friends) to get the full list of following friends.However, the API calling only results 30% of them.
Currently, a full list of followers can get through the html parser analyzing the simple [mobile website](http://weibo.cn/) contents, since it hasn't decorated with css or javascript. 

```bash
weiboarchtml.py --followlist --username 'username' --password 'password'
```  

##Search key words
Since the same reason of limitation of API calling, searing key word also rely on parsing the search result pages, but we can't get the exact time of the post. 
It can return the user name and text of the weibo post.

```bash
weiboarchtml.py --search '郭德纲'  --username 'username' --password 'password'
```  

##Follow or Unfollow users
When you try to follow someone using the [friends create API](http://open.weibo.com/wiki/2/friendships/create), it won't work. What can do is parsing the html request for adding a friend. 

```bash
weiboarchtml.py --follow 12345 1234 123
```  
Simulating the request data in the http session is a solution for following the special uids, it's very similar for unfollowing users.However, it's not as efficient as calling API.
