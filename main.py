#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name:main.py
   Author:Johnhay
   date:20.9.26
-------------------------------------------------
   Change Activity:20.9.26:
-------------------------------------------------
"""
import urllib
import urllib.request
from urllib.error import HTTPError
import datetime
from http.client import RemoteDisconnected
from retrying import retry
import threading
from bs4 import BeautifulSoup
from configure import config
import json
from loguru import logger
from first_extractor import SFExtractor
import rowblock_extractor
import Levenshtein
import re
import time
import random
import requests


###################################################################################
# 启动线程
###################################################################################
class MainThread(threading.Thread):

    def __init__(self, thread_num=1, timeout=10.0):
        super(MainThread, self).__init__()
        self.thread_num = thread_num
        self.timeout = timeout
        self.stopped = False

    def run(self):
        def target_func():
            logger.info('1.从Redis读URL')
            url: dict = get_url_from_redis()
            while url:
                logger.info('2.访问URL，url={}'.format(url['_id']))
                raw_html = get_html_from_url(url)
                if raw_html:
                    logger.info('3.解析URL，url={}'.format(url['_id']))
                    get_content_from_html(url, raw_html)
                    logger.info('4.尝试发现相关URL，url={}，depth={}'.format(url['_id'], url['depth']))
                    get_links_from_html(url, raw_html)
                    logger.info('5.保存URL，url={}'.format(url['_id']))
                    save_to_mongodb(url)
                url: dict = get_url_from_redis()

        for i in range(self.thread_num):
            subthread = threading.Thread(target=target_func, args=())
            subthread.setDaemon(True)  # 设置子线程为守护线程时，主线程一旦执行结束，则全部线程全部被终止执行
            subthread.start()
            if not self.stopped:
                subthread.join(self.timeout)  # 主线程等待子线程超时时间

    def stop(self):
        self.stopped = True

    def isStopped(self):
        return self.stopped


###################################################################################
# 核心方法
###################################################################################

def retry_on_exception(exception):
    return isinstance(exception, RemoteDisconnected) or isinstance(exception, ConnectionResetError) or isinstance(
        exception, HTTPError)


@retry(stop_max_delay=config.RETRY_CFG['stop_max_delay'],
       stop_max_attempt_number=config.RETRY_CFG['stop_max_attempt_number'],
       wait_random_min=config.RETRY_CFG['wait_random_min'], wait_random_max=config.RETRY_CFG['wait_random_max'],
       retry_on_exception=retry_on_exception)
def download_and_normalize(url: dict):
    '''
    :param url:{
                '_id': 'http://www.gov.ph',  # 唯一id
                'url': 'http://www.gov.ph',  # url地址
                'website': 'http://www.gov.ph',  # 所属根网站
                'need_vpn':0,# 是否需要翻墙访问
                'category': 0,  # 网站类别
                'threshold': 0.5,  # 相似度阈值
                'country': 'zh',  # 'en', 配合keyword进行相似度计算
                'name': '菲律宾政府',  # url名字
                'keyword': {'zh': [], 'en': []},  # 关键字列表
                'depth': 0,  # url相对website所处深度，0表示网站
                'text': "文本内容",  # 默认为空，如果成功则不为空
                'log': '失败日志',  # 默认为空，如果失败则不为空
                'related_keyword': "",  # topk的相关关键词词表字符串，逗号分隔
                'url_time': "",  # 网页最后修改时间
                'crawl_time': ""  # 网页抓取时间
            }
    :return:
    '''
    logger.info("url = {}, name = {}".format(url['_id'], url['name']))
    proxy_handler = urllib.request.ProxyHandler(config.VNP_PROXIES)
    opener = urllib.request.build_opener(proxy_handler)
    req = urllib.request.Request(url['_id'], headers=config.HEADERS)

    if url['need_vpn']:
        resp = opener.open(req)
    else:
        resp = urllib.request.urlopen(req)
    content_charset = resp.info().get_content_charset()
    raw_html = resp.read()
    if not raw_html:
        return ''
    best_match = ('', 0)
    for charset in ['utf-8', 'gbk', 'big5', 'gb18030']:
        try:
            unicode_html = raw_html.decode(charset, 'ignore')
            guess_html = unicode_html.encode(charset)
            if len(guess_html) == len(raw_html):
                best_match = (charset, len(guess_html))
                break
            elif len(guess_html) > best_match[1]:
                best_match = (charset, len(guess_html))
        except:
            pass
    if content_charset in ['utf-8', 'gbk', 'big5', 'gb18030']:
        raw_html = raw_html.decode(content_charset, 'ignore')
    else:
        raw_html = raw_html.decode(best_match[0], 'ignore')

    return raw_html


def get_url_from_redis():
    url_pool = redis_client.keys()
    url_pool.remove(config.URL_HISTORY_KEY)

    if len(url_pool) == 0:
        return None
    else:
        try:
            target_url = random.choice(url_pool)
            url = json.loads(redis_client.get(target_url))
            # 更新访问历史
            url_history = redis_client.get(config.URL_HISTORY_KEY)
            url_history = url_history + ',' + target_url if url_history != '' else target_url
            redis_client.set(config.URL_HISTORY_KEY, url_history)
            logger.info('读URL成功！URL = {}'.format(url['_id']))
        except Exception as e:
            logger.error('读URL失败！URL = {},e = {}'.format(url['_id'], e))
        else:
            redis_client.delete(target_url)
        return url


def get_html_from_url(url: dict):
    if url is None: return None
    try:
        url['crawl_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        url['url_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        raw_html = download_and_normalize(url)
        logger.info('下载URL成功！URL = {}'.format(url['_id']))
    except Exception as e:
        logger.error('下载URL失败！URL = {},e = {}'.format(url['_id'], e))
        url['log'] = e
        save_to_mongodb(url)  # 保存到MongoDB
        return None
    return raw_html


def get_content_from_html(url: dict, raw_html: str):
    '''
    解析时间和正文文本
    :param url:
    :param raw_html:
    :return:
    '''
    title, content1, keywords, desc = extractor.extract(raw_html)
    url['name'] = title
    content2 = rowblock_extractor.extract(raw_html)

    def choose_content(content1, content2):
        if (not content1) and (not content2):
            url['log'] = '文本为空！'
            return ''
        return content1 if len(content1) > len(content2) else content2

    url['text'] = choose_content(content1, content2)

    if url['need_vpn']:
        resp = requests.get(url['_id'], headers=config.HEADERS, proxies=config.VNP_PROXIES)
    else:
        resp = requests.get(url['_id'], headers=config.HEADERS)
    if resp.status_code == 200 and 'Last-Modified' in resp.headers:
        url['url_time'] = format_gmt_time(resp.headers['Last-Modified'])


def get_links_from_html(url: dict, raw_html: str):
    if url is None: return
    if raw_html is None: return
    if url['depth'] >= config.DEFAULT_FLAGS['default_depth']:
        return
    soup = BeautifulSoup(raw_html, 'lxml')
    # 全部links
    candidate_links = find_candidate_links(soup, url['website'])
    # logger.debug("candidate_links")
    # logger.debug('\n'.join([re.sub(r'\s{2,}', '', str(x)) for x in candidate_links]))
    # 相似度超过阈值的links
    target_links = find_similar_links(candidate_links, url['keyword'].split(','), url['threshold'])
    # logger.debug("similar_links")
    # logger.debug(target_links)
    for link, link_text, topk_keywords in target_links:
        if url['country'] == 'zh':
            link_text = re.sub(r'[^\u4e00-\u9fa5]', '', link_text)
        elif url['country'] == 'en':
            link_text = re.sub(r'[^a-zA-Z]', '', link_text)
        if len(link_text) < 2:
            continue

        sub_url = {
            '_id': link,  # 唯一id
            'url': 'link',  # url地址
            'website': url['website'],  # 所属根网站
            'need_vpn': url['need_vpn'],  # 是否需要翻墙访问
            'category': url['category'],  # 网站类别
            'threshold': url['threshold'],  # 相似度阈值
            'country': url['country'],  # 'en', 配合keyword进行相似度计算
            'name': link_text,  # url名字,在采集的时候会更新
            'keyword': url['keyword'],  # 关键字列表
            'depth': url['depth'] + 1,  # url相对website所处深度，0表示网站
            'text': "",  # 默认为空，如果成功则不为空
            'log': '',  # 默认为空，如果失败则不为空
            'related_keyword': topk_keywords,  # topk的相关关键词词表字符串，逗号分隔
            'url_time': "",  # 网页最后修改时间
            'crawl_time': ""  # 网页抓取时间
        }
        # 加入redis
        try:
            url_history = redis_client.get(config.URL_HISTORY_KEY)
            if sub_url['_id'] not in url_history:
                redis_client.set(sub_url['_id'], json.dumps(sub_url))
                logger.info('添加新URL成功！url = {}'.format(sub_url['_id']))
        except Exception as e:
            logger.error('添加新URL失败！ url = {},e = {}'.format(sub_url['_id'], e))


def find_candidate_links(soup, website):
    all_links = soup.find_all('a')

    # logger.debug("all_links")
    # logger.debug('\n'.join([re.sub(r'\s{2,}','',str(x)) for x in all_links]))

    def extract_domain(url: str):
        return urllib.parse.urlparse(url).netloc

    def filter_href(link):
        try:
            href = link['href']
            # url长度
            if len(href) > 128:
                return False
            # url格式
            if re.match(r'^https?:/{2}\w.+$', href):
                # url属于当前域下
                domain = extract_domain(website)
                cur_domain = extract_domain(href)
                if cur_domain != '' and (domain.endswith(cur_domain) or cur_domain.endswith(domain)):
                    return True
        except KeyError as e:
            return False
        return False

    def filter_text(link):
        # 文本长度过滤
        text = link.text.strip() if link.text != '' else ''
        if len(text) < 2:
            return False
        return True

    candidate_links = []
    for link in all_links:
        if filter_href(link) and filter_text(link):
            candidate_links.append(link)

    return candidate_links


def find_similar_links(candidate_links: list, keywords: list, threshold: float):
    '''
    计算query 与 每个keyword 的相似度score，总分和threshold比较，保留topk
    :param all_links:
    :return:[(link,link_text,topk_keywords),(link,link_text,topk_keywords)...]
    '''
    similar_links = []

    def filter(text):
        # 存在大于阈值的,即认为相似，并获取topk的关键词词表字符串
        key_scores = sorted(
            dict([(key.strip(), Levenshtein.jaro(text.lower(), key.strip().lower())) for key in keywords]).items(),
            key=lambda x: x[1],
            reverse=True)
        if key_scores[0][1] > config.DEFAULT_FLAGS['default_threshold']:
            return ','.join([key.strip() for key, _ in key_scores][:config.DEFAULT_FLAGS['default_topk']])
        return ''

    for link in candidate_links:
        url = link['href'].strip()
        text = link.text.strip()
        related_keywords = filter(text)
        if related_keywords != '':
            similar_links.append((url, text, related_keywords))

    return similar_links


def format_gmt_time(gmt_time):
    GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
    try:
        dt = datetime.datetime.strptime(gmt_time, GMT_FORMAT) + datetime.timedelta(hours=8)
    except Exception:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return "{}-{}-{} {}:{}:{}".format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def save_to_mongodb(url: dict):
    try:
        id = url['_id']
        mongo_client.replace_one({'_id': id}, url, upsert=True)  # 更新或插入
        logger.info("保存结果成功！url = {}".format(url['_id']))
    except Exception as e:
        logger.error('保存结果出错！url = {}, e = {}'.format(id, e))


if __name__ == '__main__':
    mongo_client = config.mongo_client
    redis_client = config.redis_client
    extractor = SFExtractor()
    logger.add(config.LOG_FILE, rotation="500 MB", encoding='utf-8')

    start_timestamp = time.mktime(time.strptime(config.TIME_CFG['start_date'], "%Y-%m-%d %H:%M:%S"))
    end_timestamp = time.mktime(time.strptime(config.TIME_CFG['end_date'], "%Y-%m-%d %H:%M:%S"))
    thread = MainThread(thread_num=config.DEFAULT_FLAGS['default_thread'])  # 线程数目
    thread.start()
    while True:
        time.sleep(1)
        if time.time() >= start_timestamp and time.time() <= end_timestamp:
            pass
        else:
            thread.stop()
            logger.info("运行时间到！，主程序结束!")
            break
