#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import re
import math
import time
import random
import urllib.request
from urllib.error import HTTPError

from configure import config
from http.client import RemoteDisconnected
from retrying import retry
from configure import config
from loguru import logger


# smooth and fast html extractor
# 1. remove newline characters
# 2. remove tags, replace with newlines
# 3. get blocks
# 4. stat each block's text/stopword/link/punctuation densities
# 5. get the best block
# 6. merge it's neighbours

class SFExtractor(object):
    # mininum size of a valid block
    min_block_len = 10

    # meta data
    _title = re.compile(r'<title>(.*?)</title>', re.I | re.S)
    _title2 = re.compile(r'<h1>(.*?)</h1>', re.I | re.S)
    _description = re.compile(r'<\s*meta\s*name=\"?Description\"?\s+content=\"?(.*?)\"?\s*>', re.I | re.S)
    _keywords = re.compile(r'<\s*meta\s*name=\"?Keywords\"?\s+content=\"?(.*?)\"?\s*>', re.I | re.S)
    # special cases
    _annotation_cases = [re.compile(r'<!-- 正文开始 -->(.*?)<!-- 正文结束 -->'), ]
    # special chars
    _special_list = [(re.compile(r'&quot;', re.I | re.S), '\"'),
                     (re.compile(r'&amp;', re.I | re.S), '&'),
                     (re.compile(r'&lt;', re.I | re.S), '<'),
                     (re.compile(r'&gt;', re.I | re.S), '>'),
                     (re.compile(r'&nbsp;', re.I | re.S), ' '),
                     (re.compile(r'&#34;', re.I | re.S), '\"'),
                     (re.compile(r'&#38;', re.I | re.S), '&'),
                     (re.compile(r'&#60;', re.I | re.S), '<'),
                     (re.compile(r'&#62;', re.I | re.S), '>'),
                     (re.compile(r'&#160;', re.I | re.S), ' '),
                     ]
    _special_char = re.compile(r'&\w{2,6};|&#\w{2,5};', re.I | re.S)
    # html
    _html = re.compile(r'<\w*html', re.I | re.S)
    # DTD
    _doc_type = re.compile(r'<!DOCTYPE[^>]*?>', re.I | re.S)
    # html annotation
    _annotation = re.compile(r'<!--.*?-->', re.I | re.S)
    # js
    _javascript = re.compile(r'<script[^>]*?>.*?</script>', re.I | re.S)
    # css
    _css = re.compile(r'<style[^>]*?>.*?</style>', re.I | re.S)
    _ad_links = re.compile(
        r'(<a\s+[^>\"\']+href=[\"\']?[^>\"\']+[\"\']?\s+[^>]*>[^<>]{0,50}</a>\s*([^<>]{0,40}?)){2,100}', re.I | re.S)
    _comment_links = re.compile(r'(<span[^>]*>[^<>]{0,50}</span>\s*([^<>]{0,40}?)){2,100}', re.I | re.S)
    _link = re.compile(r'<a.*?>|</a>', re.I | re.S)
    _link_mark = '|linktag|'
    _paragraph = re.compile(r'<p(\s+[^>]+)??>|</p>|<br>', re.I | re.S)
    _special_tag = re.compile(r'<[^>\'\"]*[\'\"][^\'\"]{1,500}[\'\"][^>]*?>', re.I | re.S)
    # tag
    _other_tag = re.compile(r'<[^>]*?>', re.I | re.S)
    _new_line = re.compile(r'\r\n|\n\r|\r')
    _start_spaces = re.compile(r'^[ \t]+', re.M)
    _spaces = re.compile(r'[ \t]+')
    # _multi = re.compile(r'\n+')
    _multi = re.compile(r'\n|\r|\t')
    # punction
    _punc = re.compile(r',|\?|!|:|;|。|，|？|！|：|；|《|》|%|、|“|”', re.I | re.S)
    # stop words, specific for chinese pages
    _stopword = re.compile(
        r'备\d+号|Copyright\s*©|版权所有|all rights reserved|广告|推广|回复|评论|关于我们|链接|About|广告|下载|href=|本网|言论|内容合作|法律法规|原创|许可证|营业执照|合作伙伴|备案',
        re.I | re.S)

    def preprocess(self, text):
        text = self._new_line.sub(' ', text)
        # text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '\"').replace('&amp;', '&').replace('&nbsp;', ' ')
        for r, c in self._special_list:
            text = r.sub(c, text)
        text = self._special_char.sub(' ', text)
        text = self._doc_type.sub('', text)
        text = self._annotation.sub('', text)
        s = self._html.search(text)
        if not s: return ''
        if text.strip().startswith('document.write'): return ''
        return text

    def remove_tags(self, text):
        text = self._javascript.sub('\n', text)
        text = self._css.sub('\n', text)
        # text = self._ad_links.sub('\n', text)
        # text = self._comment_links.sub('\n', text)
        text = self._link.sub(self._link_mark, text)
        # text = self._paragraph.sub('\n', text)
        # text = self._special_tag.sub('\n', text)
        text = self._other_tag.sub('\n', text)
        # text = self._multi.sub('\n', text)

        text = self._start_spaces.sub('', text)
        text = self._spaces.sub(' ', text)

        # print 'after all'.center(100, '*')
        # print text
        return text

    def get_blocks(self, lines, thres):
        if not lines: return []
        # for lin in lines:
        #    print len(lin), lin
        line_lens = [len(line) for line in lines]
        tot_line = len(lines)

        # get property block interval
        empty_blocks = []
        istart = 0
        for iend in range(0, tot_line):
            if line_lens[iend] != 0 and iend > istart:
                empty_blocks.append(iend - istart - 1)
                istart = iend
            if iend == tot_line - 1 and iend > istart:
                empty_blocks.append(iend - istart - 1)
        if not empty_blocks: return []
        sort_list = sorted(empty_blocks)
        sort_list2 = []
        for v in sort_list:
            if v > 1:
                sort_list2.extend([v] * v)
            else:
                sort_list2.append(v)
        prop_interval = max(3, sort_list2[len(sort_list2) // 5] + 1)
        # print 'interval:', prop_interval

        # get blocks
        blocks = []
        istart = 0
        for iend in range(0, tot_line):
            if sum(line_lens[iend:iend + prop_interval]) <= 3 and iend > istart:
                if sum(line_lens[istart:iend]) >= thres:
                    blocks.append((istart, iend))
                istart = iend + prop_interval
                while istart < tot_line - 1 and line_lens[istart] <= 2:
                    istart += 1
            if iend == tot_line - 1:
                if sum(line_lens[istart:iend]) >= thres:
                    blocks.append((istart, iend))
        return blocks

    def stat_blocks(self, lines, blocks):
        title_set = set(self.title)
        title_len = len(title_set) + 1.0
        tot_line = len(lines)

        block_scores = []
        for istart, iend in blocks:
            block = '\n'.join(lines[istart:iend])
            line_num = iend - istart + 1.0
            clean_block = block.replace(self._link_mark, '')

            position_rate = (tot_line - istart + 1.0) / (tot_line + 1.0)
            text_density = (len(clean_block) + 1.0) / line_num
            punc_density = (len(self._punc.findall(clean_block)) + 1.0) / line_num
            link_density = (block.count(self._link_mark) + 1.0) / line_num
            stopword_density = (len(self._stopword.findall(clean_block)) + 1.0) / line_num
            matched_set = set(clean_block) & title_set
            title_match_rate = len(''.join(matched_set)) / title_len

            score = position_rate * text_density
            score *= math.pow(punc_density, 0.5)
            score *= 1.0 + title_match_rate
            score /= link_density
            score /= math.pow(stopword_density, 0.5)

            block_scores.append(score)
        return block_scores

    def extract_title(self, text):
        match = self._title.search(text)
        if not match:
            match = self._title2.search(text)
        if match:
            title = match.groups()[0]
            # title = self._special_char.sub(' ', title)
            title = self._multi.sub(' ', title)
        else:
            return ''
        # remove noisy parts
        title_arr = re.split('\-|\||_', title)
        title_scores = []
        for i, part in enumerate(title_arr):
            score = len(part.strip())
            score *= (len(title_arr) - i) / len(title_arr)
            title_scores.append((i, score))
        sort_list = sorted(title_scores, key=lambda d: -d[1])
        new_title = ''
        for i in range((len(title_scores) + 1) // 2):
            new_title += ' ' + title_arr[sort_list[i][0]]
        return new_title

    def extract_keywords(self, text):
        match = self._keywords.search(text)
        if match:
            title = match.groups()[0]
            # title = self._special_char.sub(' ', title)
            return self._multi.sub(' ', title)
        return ''

    def extract_description(self, text):
        match = self._description.search(text)
        if match:
            title = match.groups()[0]
            # title = self._special_char.sub(' ', title)
            return self._multi.sub(' ', title)
        return ''

    def extract_content(self, text, thres):
        # 2. remove tags, replace with newlines
        text = self.remove_tags(text)

        # 3. get blocks
        lines = text.split('\n')
        # for line in lines: print line
        blocks = self.get_blocks(lines, thres)
        if not blocks:
            return ''

        # 4. stat each block's text/stopword/link/punctuation densities
        block_scores = self.stat_blocks(lines, blocks)

        # 5. get the best block, and it's neighbours
        best_idx, best_block, best_score = -1, None, max(block_scores) - 1
        for i, score in enumerate(block_scores):
            if score > best_score:
                best_idx = i
                best_block = blocks[i]
                best_score = score

        # 6. merge it's neighbours
        i = best_idx - 1
        while i >= 0:
            new_block = (blocks[i][0], best_block[1])
            new_score = self.stat_blocks(lines, [new_block])[0]
            if new_score > best_score:
                best_score = new_score
                best_block = new_block
                i -= 1
            else:
                break
        i = best_idx + 1
        while i < len(blocks):
            new_block = (best_block[0], blocks[i][1])
            new_score = self.stat_blocks(lines, [new_block])[0]
            if new_score > best_score:
                best_score = new_score
                best_block = new_block
                i += 1
            else:
                break

        content = '\n'.join(lines[best_block[0]:best_block[1]])
        content = self._multi.sub(' ', content)
        content = content.replace(self._link_mark, '')
        return content

    def check_from_annotation(self, text):
        candi_list = []
        for r in self._annotation_cases:
            s = r.search(text)
            if s:
                candi_list.extend(list(s.groups()))
        if not candi_list: return ''
        return '  '.join(candi_list)

    def extract(self, raw_text, _thres=0):
        if not raw_text: return '', '', '', ''

        # 1. remove newline characters
        text = self.preprocess(raw_text)

        self.title = self.extract_title(text)
        self.keywords = self.extract_keywords(text)
        self.desc = self.extract_description(text)

        # special process
        content = ''  # self.check_from_annotation(raw_text)
        if content:
            self.content = content
        else:
            self.content = self.extract_content(text, _thres or self.min_block_len)
        return [self.title, self.content, self.keywords, self.desc]


def retry_on_exception(exception):
    return isinstance(exception, RemoteDisconnected) or isinstance(exception, ConnectionResetError) or isinstance(exception,HTTPError)


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
    headers = config.HEADERS
    proxy_handler = urllib.request.ProxyHandler(config.VNP_PROXIES)
    opener = urllib.request.build_opener(proxy_handler)
    if url['need_vpn']:
        req = urllib.request.Request(url['_id'], headers=headers)
        raw_html = opener.open(req).read()
    else:
        req = urllib.request.Request(url['_id'],headers=headers)
        raw_html = urllib.request.urlopen(req).read()
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
    raw_html = raw_html.decode(best_match[0], 'ignore')
    return raw_html


def test():
    ext = SFExtractor()

    urls = [
        'https://baike.baidu.com/item/%E8%89%BE%E8%96%87%E5%84%BF%C2%B7%E6%8B%89%E7%BB%B4%E5%B0%BC/8566850?fromtitle=%E8%89%BE%E8%96%87%E5%84%BF&fromid=478366',
        'http://hi.baidu.com/handylee/blog/item/6523c4fc35a235fffc037fc5.html',
        'http://www.ifanr.com/15876',
        'http://news.cnhubei.com/xw/yl/201404/t2894467_5.shtml',
    ]

    for url in urls:
        raw_html = download_and_normalize(url)
        if raw_html:
            print('url:', url)
            start_time = time.time()
            for i in range(0, 10):
                title, content, keywords, desc = ext.extract(raw_html)
            end_time = time.time()
            print('QPS:', 10 / (end_time - start_time))
            print('title:', title)
            print('content:', content)
        else:
            print('url:', url)


if __name__ == '__main__':
    ext = SFExtractor()
    url = json.loads(config.redis_client.get('http://www.filipinoexpress.com/'))
    try:
        raw_html = download_and_normalize(url)
    except Exception as e:
        print(e)
    title, content, keywords, desc = ext.extract(raw_html)
    print('title:', title)
    print('content:', content)
