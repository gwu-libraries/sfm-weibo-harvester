# sfm-weibo-exporter master docker container

A docker container for running sfm-weibo-exporter as a service.
The harvester code must be mounted as `/opt/sfm-weibo-harvester`, the sfm-utils code as `/opt/sfm-utils` and the warcprox code as `/opt/warcprox`.
For example:

```python
volumes:
    - "/my_directory/sfm-weibo-harvester:/opt/sfm-weibo-harvester"
    - "/my_directory/sfm-utils:/opt/sfm-utils"
    - "/my_directory/warcprox:/opt/warcprox"
```

This container requires a link to a container running the queue. This must be linked with the alias `mq`.  
For example:

```python
links:
    - sfmrabbit:mq
```
