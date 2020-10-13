# universal_website_spider
一个能够自动的、与自定义相关关键词词表相关的通用网站爬虫。A universal spider which can crawl defined  and related urls from website.

## 代码结构说明
```python
BIT_PSPIDER
│  2020927爬虫汇报.pptx
│  first_extractor.py 网页内容抽取器
│  rowblock_extractor.py 网页内容抽取器
│  input_to_redis.py 输入文件导入redis
│  main.py 启动主程序
│  mongodb_to_redis.py mongodb中未成功采集的url导入redis
│
├─configure
│      config.py 配置文件
│
├─envs
│      pspider.zip Anaconda虚拟环境：使用方法简单：复制到本地机器的anaconda下的envs目录，解压即可正常激活和退出
│      python_Levenshtein-0.12.0-cp36-cp36m-win_amd64.whl 一个安装包
│
├─input
│      input_url.csv 输入URL文件
│      test.csv 测试URL文件
│
└─log 日志目录
```

## 程序使用说明
python main.py
