#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name:url_to_redis
   Author:Johnhay
   date:20.10.10
-------------------------------------------------
   Change Activity:20.10.10:
-------------------------------------------------
"""
from tqdm import tqdm
from configure import config
import pandas as pd
import json
import redis
from loguru import logger

if __name__ == '__main__':
    input_file = config.INPUT_URL_FILE
    columns = config.INPUT_COLUMNS
    df = pd.read_csv(input_file, index_col=False)  # 第一列是数据列
    # 预处理数据：增加URL属性、默认值填充、类型转换
    df.dropna(axis=0, how='all', inplace=True)  # 删除全空的行
    # 增加URL属性
    last_columns = [x for x in config.URL.keys() if x not in columns]
    for column in last_columns:
        if '_id' == column:
            df[column] = df['url']
        if 'log' == column or 'text' == column:
            df[column] = ""
        if 'related_keyword' == column:
            df[column] = ""
        if 'url_time' == column or 'crawl_time' == column:
            df[column] = ""
    # 空数据填充默认值
    df['category'] = df['category'].fillna(config.DEFAULT_FLAGS['default_category'])
    df['country'] = df['country'].fillna(config.DEFAULT_FLAGS['default_country'])
    df['depth'] = df['depth'].fillna(config.DEFAULT_FLAGS['default_depth'])
    df['keyword'] = df['keyword'].fillna(','.join(config.DEFAULT_FLAGS['default_keyword']))
    df['threshold'] = df['threshold'].fillna(config.DEFAULT_FLAGS['default_threshold'])
    df['need_vpn'] = df['need_vpn'].fillna(config.DEFAULT_FLAGS['default_need_vpn'])
    # 关键字列表处理
    keywords = []
    for index, row in df.iteritems():
        if 'keyword' == index:
            for x in row:
                keywords.append(','.join(x.split('#') + config.DEFAULT_FLAGS['default_keyword']))
    df['keyword'] = keywords
    # 类型转换
    df['_id'].astype(str)
    df['url'].astype(str)
    df['website'].astype(str)
    df['category'].astype(str)
    df['threshold'].astype(float)
    df['country'].astype(str)
    df['name'].astype(str)
    df['depth'].astype(int)
    df['need_vpn'].astype(int)
    df['text'].astype(str)
    df['log'].astype(str)
    df['related_keyword'].astype(str)
    df['url_time'].astype(str)
    df['crawl_time'].astype(str)
    # 保存到redids
    # pool = redis.ConnectionPool(host='localhost', port=6379,
    #                             decode_responses=True)  # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
    # rds = redis.Redis(connection_pool=pool)
    rds = config.redis_client

    k = rds.randomkey()
    if k is None:
        rds.set(config.URL_HISTORY_KEY,'')

    for row in tqdm(list(df.itertuples())):
        try:
            url = getattr(row, 'url')
            _id = url
            website = getattr(row, 'website')
            category = getattr(row, 'category')
            threshold = getattr(row, 'threshold')
            country = getattr(row, 'country')
            name = getattr(row, 'name')
            keyword = getattr(row, 'keyword')
            depth = getattr(row, 'depth')
            need_vpn = getattr(row, 'need_vpn')
            text = getattr(row, 'text')
            log = getattr(row, 'log')
            related_keyword = getattr(row, 'related_keyword')
            url_time = getattr(row, 'url_time')
            crawl_time = getattr(row, 'crawl_time')
            item = {
                '_id': _id,
                'url': url,
                'website': website,
                'category': category,
                'need_vpn': need_vpn,
                'threshold': threshold,
                'country': country,
                'name': name,
                'keyword': keyword,
                'depth': depth,
                'text': text,
                'log': log,
                'related_keyword': related_keyword,
                'url_time': url_time,
                'crawl_time': crawl_time
            }
            rds.set(_id, json.dumps(item))
            logger.success("{} insert successful.".format(_id))
        except Exception as e:
            logger.error(" has error = {}".format(_id, e))
            continue
