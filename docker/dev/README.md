# sfm-weibo-harvester master docker container

A docker container for running sfm-weibo-harvester as a service.
The harvester code must be mounted as `/opt/sfm-weibo-harvester`, and the sfm-utils code must be mounted as `/opt/sfm-utils`.
For example:

```python
volumes:
    - "/my_directory/sfm-weibo-harvester:/opt/sfm-weibo-harvester"
    - "/my_directory/sfm-utils:/opt/sfm-utils"
```

This container requires a link to a container running the queue. This must be linked with the alias `mq`.  
For example:

```python
links:
    - sfmrabbit:mq
```
