#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name:mongodb_to_redis
   Author:Johnhay
   date:20.10.11
-------------------------------------------------
   Change Activity:20.10.11:
-------------------------------------------------
"""
from configure import config
from extractor import SFExtractor
from tqdm import tqdm
import json

'''
将mongodb中没有采集到的url再输入redis
'''

if __name__ == '__main__':
    mongo_client = config.mongo_client
    redis_client = config.redis_client
    extractor = SFExtractor()

    for url in tqdm(list(mongo_client.find({'log': {'$ne': ''}}))):
        redis_client.set(url['_id'],json.dumps(url))
