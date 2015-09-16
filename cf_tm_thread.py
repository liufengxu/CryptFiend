#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (c) 2015 .com, Inc. All Rights Reserved
#
################################################################################
"""
description: 多线程版抓取网页
author: liufengxu
date: 2015-09-15 12:09:58
last modified: 2015-09-16 14:39:01
version: 1.0.0
"""

import logging
import threading
import Queue
import urllib2
import cookielib
import re
import random
import time
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

Q_MAX_SIZE = 1024
TASK_MAX = 16


class CryptFiend(object):
    """ 蜘蛛类 """
    def __init__(self):
        self.timeout = 20
        self.proxy_handler = urllib2.ProxyHandler({})

    def connect(self, url, http_proxy='null'):
        """ 抓取网页 """
        resp_html = None
        try:
            if http_proxy != 'null':
                logging.debug('use http proxy')
                self.set_proxy_handler(http_proxy)
            # opener = urllib2.build_opener(self.proxy_handler)
            self.set_cookie()
            self.opener = urllib2.build_opener(self.proxy_handler,
                                               self.cookie_handler)
            logging.debug('opener installed ok')
            # 使用 Request 会处理重定向
            self.set_headers()
            req = urllib2.Request(url=url, headers=self.headers)
            logging.debug('set request url ok')
            resp = self.opener.open(req, timeout=self.timeout)
            logging.debug('urlopen success')
            logging.debug('%s', resp.info())
            resp_html = resp.read()
            resp.close()
        except urllib2.URLError as e:
            logging.error('%s', e.reason)
            # logging.error('%s: %s', e.code, e.reason)
            # return str(e.code)
        return resp_html

    def set_proxy_handler(self, http_proxy):
        """ 设置代理 """
        self.proxy_handler = urllib2.ProxyHandler({'http':
                                                   'http://%s/' % http_proxy})

    def set_cookie(self):
        cookie = cookielib.CookieJar()
        self.cookie_handler = urllib2.HTTPCookieProcessor(cookie)

    def set_headers(self):
        ua = 'Mozilla/5.0 (X11; U; Linux i686)Gecko/20071127 Firefox/2.0.0.11'
        headers = {'User-Agent': ua}
        self.headers = headers


class HtmlParser(object):
    """ 解析页面类 """
    def __init__(self, resp_html):
        self.page = resp_html
        self.bs = BeautifulSoup(self.page)

    def parse_category(self):
        li_list = self.bs.findAll('li')
        for li in li_list:
            a_list = li.findAll('a', href=re.compile('\/category\/[0-9]*\/'))
            for a in a_list:
                print a['href'], a.contents[0]

    def parse_middle(self, tag):
        p_list = self.bs.findAll('p', {'class': 'name'})
        for p in p_list:
            a_list = p.findAll('a', href=re.compile('\/recipe\/[0-9]*\/'))
            for a in a_list:
                print a['href'] + '\t' + tag


class Worker(threading.Thread):
    """ 线程工作类 """
    def __init__(self, task_queue, resource_queue):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.resource_queue = resource_queue

    def run(self):
        logging.debug('start to run')
        while True:
            if not self.do_work():
                logging.error('%s', self.getName())
            else:
                logging.info('%s', self.getName())

    def do_work(self):
        logging.debug('get page start to work')
        # 读队列信息
        task_info = self.task_queue.get()
        logging.debug(self.resource_queue.qsize())
        proxy = self.resource_queue.get()
        logging.debug('proxy is %s', proxy)
        # 业务逻辑
        logging.debug('get page start to crawl')
        flag = True
        segs = task_info.split(' ')
        if len(segs) != 2:
            logging.error('input format not right')
            return False
        url_part, tag = segs
        head = 'http://www.xiachufang.com'
        tail = '?page='
        cf = CryptFiend()
        for i in xrange(1, 51):
            logging.debug('get page %d', i)
            time.sleep(random.uniform(0.5, 1.5))
            url = head + url_part + tail + str(i)
            xcf_middle = cf.connect(url, proxy)
            if xcf_middle:
                if xcf_middle == '404':
                    break
                logging.debug('start parsing')
                hp = HtmlParser(xcf_middle)
                hp.parse_middle(tag)
            else:
                logging.debug('maybe something wrong')
                flag = False
        # 向队列反馈信息
        self.task_queue.task_done()
        if flag:
            self.resource_queue.put(proxy)
            self.resource_queue.put(proxy)  # copy self as bonus
        return flag


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: "
                        "%(asctime)s: %(filename)s: %(lineno)d * "
                        "%(thread)d %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    task_queue = Queue.Queue(Q_MAX_SIZE)
    resource_queue = Queue.Queue(0)  # infinite queue
    # init the input queue
    task_file = sys.argv[1]
    with open(task_file) as fp:
        for line in fp:
            task_id = line[:-1]
            task_queue.put(task_id)
    # init proxy(resource) queue
    proxy_file = sys.argv[2]
    for i in xrange(8):  # 每个代理初始化8份
        with open(proxy_file) as fp:
            for line in fp:
                proxy = line[:-1]
                resource_queue.put(proxy)
    # init worker queue
    for i in xrange(TASK_MAX):
        worker = Worker(task_queue, resource_queue)
        # set main thread not blocked
        worker.setDaemon(True)
        worker.start()
    # wait until the queue is empty
    task_queue.join()


if __name__ == '__main__':
    main()
