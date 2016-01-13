# sfm-weibo-harvester
A basic harvester for Sina Weibo public post data as part of Social Feed Manager. 

Provides harvesters for [Sina Weibo API](http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI) and [Html Parser](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

Harvesting is performed by [weibowarc](https://github.com/gwu-libraries/weibowarc).

The html parser is just a possible solution for any exist limitation problem. If possible, the weibo harvester will rely most on the API calling.