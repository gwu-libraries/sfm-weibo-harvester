# sfm-weibo-exporter master docker container

A docker container for running sfm-weibo-exporter as a service.

This container requires a link to a container running the queue. This must be linked with the alias `mq`.  
For example:

```python
links:
    - sfmrabbit:mq
```
