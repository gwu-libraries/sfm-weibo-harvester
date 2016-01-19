# sfm-weibo-harvester
A basic harvester for Sina Weibo public post data as part of Social Feed Manager. 

Provides harvesters for [Sina Weibo API](http://open.weibo.com/wiki/%E5%BE%AE%E5%8D%9AAPI) and [Html Parser](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

Harvesting is performed by [weibowarc](https://github.com/gwu-libraries/weibowarc).

The weibowarchtml is just a possible solution for any exist limitation problem. If possible, the weibo harvester will rely mostly on the API calling.
# Install
```bash
git clone https://github.com/gwu-libraries/sfm-weibo-harvester
cd sfm-weibo-harvester
pip install -r requirements.txt
```

#Testing
* Install [Docker](https://docs.docker.com/installation/) and [Docker-Compose](https://docs.docker.com/compose/install/)
* Geting the `API_KEY`, `API_SECRET`, `REDIRECT_URI`, `ACCESS_TOKEN`, refer to  [weibowarc](https://github.com/gwu-libraries/weibowarc)
* Start up the containers
```bash
docker-compose -f docker/dev.docker-compose.yml up -d
```
* Running the tests
* Check the logs
* Shutdown all the containers and clear what you have done