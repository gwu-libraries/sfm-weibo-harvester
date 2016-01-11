# sfm-weibo-harvester
A basic harvester for Sina Weibo public post data as part of Social Feed Manager. 

Provides harvesters for [Sina Weibo API](http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI) and [Html Parser](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

Harvesting is performed by Weibowarc.

##Harvesting through [friends_timeline](http://open.weibo.com/wiki/2/statuses/friends_timeline)
Since the limited of API calling, the basic harvester uses the friendship to collecting the data.


##Getting a full list of followers
Usually, It can call the [friends API](http://open.weibo.com/wiki/2/friendships/friends) to get the full list of following friends.However, the API calling only results 30% of them.
Currently, a full list of followers can get through the html parser analyzing the simple [mobile website](http://weibo.cn/) contents, since it hasn't decorated with css or javascript. 


##Search key words
Since the same reason of limitation of API calling, searing key word also rely on parsing the search result pages, but we can't get the exact time of the post. 
It can return the user name and text of the weibo post.

##Follow or Unfollow users
When you try to follow someone using the [friends create API](http://open.weibo.com/wiki/2/friendships/create), it won't work. What we do is parsing the request for adding a friend. 
The raw data for following user is as follows:

    GET /attention/add?uid=12345678&rl=0&st=d56522 HTTP/1.1
    Host: weibo.cn
    Connection: keep-alive
    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
    Upgrade-Insecure-Requests: 1
    User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36
    Referer: http://weibo.cn/u/12345678
    Accept-Encoding: gzip, deflate, sdch
    Accept-Language: en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4
    Cookie: XXX-XXXX

Simulating the request data in the http session is a solution for following the special uids, it's very similar for unfollowing users.However, it's not as efficient as calling API.

The html parser is just a possible solution for any exist limitation problem. If possible, the weibo harvester will rely most on the API calling.