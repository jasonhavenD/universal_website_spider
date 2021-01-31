#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name:config.py
   Author:Johnhay
   date:20.9.22
-------------------------------------------------
   Change Activity:20.9.22:
-------------------------------------------------
"""
import logging
import datetime
import redis
import pymongo
import random
import os

now = datetime.datetime.now()

###################################################################################
# 人工配置
###################################################################################

# 保存文件位置
SAVE_FOLDER = os.path.join(os.getcwd(),'output')


# 程序启动和终止时间配置
# 注意格式："%Y-%m-%d %H:%M:%S"
TIME_CFG = {
    'start_date': '2020-10-11 15:30:00',
    'end_date': '2020-11-30 22:00:00'
}

# MongoDB 数据库配置
MONGO_CFG = {
    'host': '10.108.17.184',
    'port': 27017,
    'db': 'pspider',
    'table': 'urls'
}

# Redis 数据库配置
REDIS_CFG = {
    'host': '10.108.17.184',
    'port': 6379
}

# URL输入文件
INPUT_COLUMNS = ['url', 'website', 'name', 'category', 'country', 'keyword', 'depth', 'threshold', 'need_vpn']  # 文件格式
INPUT_URL_FILE = './input/11.23_input.csv'


# Keywords字典
KEYWORDS_DICT = {
    -1: {
        'zh': [],
        'en': []
    },
    0: {
        'zh': ["杜特尔特,"
               "国务卿特奥多罗·洛辛,"
               "唐纳德·特朗普,"
               "南中国海,"
               "西菲律宾海,"
               "联合演习,"
               "中国/中国,"
               "索赔,"
               "美国/美国/美国,"
               "外交部长王毅,"
               "越南,"
               "大陆架,"
               "德尔芬·洛伦扎纳,"
               "马克·埃斯珀,"
               "群岛海道,"
               "航空母舰,"
               "解放军,"
               "环境和自然资源部,"
               "渔业局还有水资源,"
               "地貌,"
               "斯卡伯勒浅滩,"
               "石油,"
               "芦苇滩,"
               "外交部长,"
               "赫摩根尼"],
        'en': [
            "Duterte",
            "Secretary Teodoro L. Locsin Jr.",
            "Donald Trump",
            "South China Sea",
            "West Philippine Sea",
            "joint exercise",
            "China/Chines",
            "claim",
            "U.S./the United States/America",
            "Foreign Minister Wang Yi ",
            "vietnam",
            "continental shelf",
            "Delfin Lorenzana",
            "Mark Esper",
            "archipelagic sea lanes",
            "aircraft carrier",
            "PLA",
            "Department of Environment and Natural Resources",
            "The Bureau of Fisheries and Aquatic Resources",
            "features",
            "Scarborough Shoal",
            "oil",
            "reed bank",
            "Secretary of Foreign Affairs",
            "Hermogenes"
        ]
    },
    1: {
        'zh': ["杜特尔特,"
               "国务卿特奥多罗·洛辛,"
               "唐纳德·特朗普,"
               "南中国海,"
               "西菲律宾海,"
               "联合演习,"
               "中国/中国,"
               "索赔,"
               "美国/美国/美国,"
               "外交部长王毅,"
               "越南,"
               "大陆架,"
               "德尔芬·洛伦扎纳,"
               "马克·埃斯珀,"
               "群岛海道,"
               "航空母舰,"
               "解放军,"
               "环境和自然资源部,"
               "渔业局还有水资源,"
               "地貌,"
               "斯卡伯勒浅滩,"
               "石油,"
               "芦苇滩,"
               "外交部长,"
               "赫摩根尼"],
        'en': [
            "Duterte",
            "Secretary Teodoro L. Locsin Jr.",
            "Donald Trump",
            "South China Sea",
            "West Philippine Sea",
            "joint exercise",
            "China/Chines",
            "claim",
            "U.S./the United States/America",
            "Foreign Minister Wang Yi ",
            "vietnam",
            "continental shelf",
            "Delfin Lorenzana",
            "Mark Esper",
            "archipelagic sea lanes",
            "aircraft carrier",
            "PLA",
            "Department of Environment and Natural Resources",
            "The Bureau of Fisheries and Aquatic Resources",
            "features",
            "Scarborough Shoal",
            "oil",
            "reed bank",
            "Secretary of Foreign Affairs",
            "Hermogenes"
        ]
    },
    2: {
        'zh': ["杜特尔特,"
               "国务卿特奥多罗·洛辛,"
               "唐纳德·特朗普,"
               "南中国海,"
               "西菲律宾海,"
               "联合演习,"
               "中国/中国,"
               "索赔,"
               "美国/美国/美国,"
               "外交部长王毅,"
               "越南,"
               "大陆架,"
               "德尔芬·洛伦扎纳,"
               "马克·埃斯珀,"
               "群岛海道,"
               "航空母舰,"
               "解放军,"
               "环境和自然资源部,"
               "渔业局还有水资源,"
               "地貌,"
               "斯卡伯勒浅滩,"
               "石油,"
               "芦苇滩,"
               "外交部长,"
               "赫摩根尼"],
        'en': [
            "Duterte",
            "Secretary Teodoro L. Locsin Jr.",
            "Donald Trump",
            "South China Sea",
            "West Philippine Sea",
            "joint exercise",
            "China/Chines",
            "claim",
            "U.S./the United States/America",
            "Foreign Minister Wang Yi ",
            "vietnam",
            "continental shelf",
            "Delfin Lorenzana",
            "Mark Esper",
            "archipelagic sea lanes",
            "aircraft carrier",
            "PLA",
            "Department of Environment and Natural Resources",
            "The Bureau of Fisheries and Aquatic Resources",
            "features",
            "Scarborough Shoal",
            "oil",
            "reed bank",
            "Secretary of Foreign Affairs",
            "Hermogenes"
        ]
    }
}

# URL默认参数:category,country,keyword,depth,threshold
DEFAULT_FLAGS = {
    'default_category': 0,  # url类别
    'default_country': 'en',  # url国家
    'default_depth': 5,  # url层次
    'default_threshold': 0.5,  # 阈值
    'default_thread': 6,  # 线程数
    'default_need_vpn': 1,  # vpn是否需要
    'default_topk': 3,  # 保留的topk关键词
    'default_keyword': KEYWORDS_DICT[0]['en']
}

# URL下载策略
RETRY_CFG = {
    'stop_max_delay': 1000 * 10,  # 毫秒,推荐10-20s
    'stop_max_attempt_number': 6,  # 最大尝试次数，推荐6
    'wait_random_min': 1000 * 6,  # 连续重试随机时间下线毫秒，推荐3
    'wait_random_max': 1000 * 15  # 连续重试随机时间上线毫秒，推荐10
}

###################################################################################
# 基本无需修改
###################################################################################
# 数据库实例
pool = redis.ConnectionPool(host=REDIS_CFG['host'], port=REDIS_CFG['port'], decode_responses=True)
client = pymongo.MongoClient(host=MONGO_CFG['host'], port=MONGO_CFG['port'])
db = client[MONGO_CFG['db']]
mongo_client = db[MONGO_CFG['table']]
redis_client = redis.Redis(connection_pool=pool)

# URL定义
URL = {
    '_id': 'http://www.gov.ph',  # 唯一id
    'url': 'http://www.gov.ph',  # url地址
    'website': 'http://www.gov.ph',  # 所属根网站
    'need_vpn': 0,  # 是否需要翻墙访问
    'category': 0,  # 网站类别
    'threshold': 0.5,  # 相似度阈值
    'country': 'zh',  # 'en', 配合keyword进行相似度计算
    'name': '菲律宾政府',  # url名字
    'keyword': "",  # 关键字列表k,k,k,k
    'depth': 0,  # url相对website所处深度，0表示网站
    'text': "文本内容",  # 默认为空，如果成功则不为空
    'log': '失败日志',  # 默认为空，如果失败则不为空
    'related_keyword': "",  # topk的相关关键词词表字符串，逗号分隔,k,k,k
    'url_time': "",  # 网页最后修改时间
    'crawl_time': ""  # 网页抓取时间
}

# URL类别字典
CATEGORY_DICT = {
    '无': -1,
    '政府': 0,
    '新闻': 1,
    '百科': 2
}

# 日志文件
LOG_FILE = "./log/{}_log.txt".format(now.strftime('%Y%m%d%H'))

# 日志级别
LOG_LEVELS = {
    5: logging.CRITICAL,
    4: logging.ERROR,
    3: logging.WARNING,
    2: logging.INFO,
    1: logging.DEBUG
}

# 外网访问代理
VNP_PROXIES = {
    'https': 'https://127.0.0.1:1080',
    'http': 'http://127.0.0.1:1080'
}

# 用户代理池
USER_AGENT = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
    'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; Tablet PC 2.0; .NET4.0E)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; InfoPath.3)',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; ) AppleWebKit/534.12 (KHTML, like Gecko) Maxthon/3.0 Safari/534.12',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.33 Safari/534.3 SE 2.X MetaSr 1.0',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E)',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.41 Safari/535.1 QQBrowser/6.9.11079.201',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E) QQBrowser/6.9.11079.201',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)',
    'Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Tri dent/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)',
    'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64;Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)',
    'Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)',
]

HEADERS = {
    'User-Agent': random.choice(USER_AGENT),
}

URL_HISTORY_KEY = 'redids-url-history-do-not-delete'