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
last modified: 2015-09-19 23:32:54
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

Q_MAX_SIZE = 1000000
TASK_MAX = 8


class CryptFiend(object):
    """ 蜘蛛类 """
    def __init__(self):
        self.timeout = 10
        self.proxy_handler = urllib2.ProxyHandler({})

    def connect(self, url, http_proxy='null'):
        """ 抓取网页 """
        resp_html = None
        ret_code = '0'
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
            logging.debug('%s', resp.getcode())
            ret_code = str(resp.getcode())
            logging.debug('urlopen success')
            logging.debug('%s', resp.info())
            resp_html = resp.read()
            resp.close()
        except urllib2.URLError as e:
            logging.error('%s', e)
            reobj = re.compile('[0-9]{3}')
            errno = re.findall(reobj, str(e))
            if errno:
                return resp_html, str(errno[0])
            # it's strange if I use e.code, the ERROR is :
            # 'URLError' object has no attribute 'code'
            # logging.error('%s: %s', e.code, e.reason)
            # return str(e.code)
        return resp_html, ret_code

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

    def parse_middle(self, tag, page_num):
        p_list = self.bs.findAll('p', {'class': 'name'})
        for p in p_list:
            a_list = p.findAll('a', href=re.compile('\/recipe\/[0-9]*\/'))
            for a in a_list:
                print a['href'] + '\t' + tag + '\t' + page_num

    def parse_recipe(self, url_part):
        output = []
        output.append(url_part)
        h1_list = self.bs.findAll('h1', {'class': 'page-title'})
        # 菜谱标题
        title = 'NULL'
        if h1_list:
            logging.debug('%s', h1_list[0].contents)
            title = h1_list[0].contents[0].strip()
            logging.debug('%s', title)
        else:
            logging.debug('no title')
        output.append(title)
        # 菜谱评分
        score_list = self.bs.findAll('span', {'itemprop': 'ratingValue'})
        score = 'NULL'
        if score_list:
            score = score_list[0].contents[0].strip()
            logging.debug('%s', score)
        output.append(score)
        # 多少人做过
        have_done_list = self.bs.findAll('span', {'class': 'number'})
        have_done = 'NULL'
        if have_done_list:
            have_done = have_done_list[-1].contents[0].strip()
            logging.debug('%s', have_done)
        output.append(have_done)
        # 图片url
        pic_url = 'NULL'
        pic_list = self.bs.findAll('img', {'width': '620'})
        logging.debug('%s', pic_list)
        if pic_list:
            pic_url = pic_list[0]['src']
            logging.debug('%s', pic_url)
        output.append(pic_url)
        # 配料 用量 list
        food_list = []
        bs_table = self.bs.findAll('tr', {'itemprop': 'ingredients'})
        for bs_tag in bs_table:
            food_name = ''
            food_unit = ''
            food_name_list = bs_tag.findAll('td', {'class': 'name has-border'})
            if food_name_list:
                logging.debug('%s', food_name_list[0])
                logging.debug('%s', food_name_list[0].a)
                if food_name_list[0].contents[0].strip():
                    food_name = food_name_list[0].contents[0].strip()
                else:
                    if food_name_list[0].a:
                        logging.debug('%s', food_name_list[0].a.contents)
                        food_name = food_name_list[0].a.contents[0]
            food_unit_list = bs_tag.findAll('td', {'class': 'unit has-border'})
            if food_unit_list:
                food_unit = food_unit_list[0].contents[0].strip()
            food_item = food_name + ':' + food_unit
            food_list.append(food_item)
        output.append(','.join(food_list))
        # 标签list
        cate_list = []
        div_list = self.bs.findAll('div', {'class': 'recipe-cats'})
        if div_list:
            div_tag = div_list[0]
            a_list = div_tag.findAll('a',
                                     href=re.compile('\/category\/[0-9]*\/'))
            if a_list:
                for a in a_list:
                    if a.contents:
                        cate_list.append(str(a.contents[0]))
        output.append(','.join(cate_list))
        print '\t'.join(output)


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
        logging.debug('task queue length: %s', self.task_queue.qsize())
        try:
            task_info = self.task_queue.get()
        except Exception as e:
            logging.error('%s', e)
            return False
        if not task_info:
            logging.debug('task queue is empty')
            return False
        logging.debug('proxy queue length: %s', self.resource_queue.qsize())
        try:
            proxy = self.resource_queue.get()
        except Exception as e:
            logging.error('%s', e)
            return False
        if not proxy:
            logging.debug('resource queue is empty')
            return False
        logging.debug('proxy is %s', proxy)
        # 业务逻辑
        # self.crawl(task_info, proxy)
        self.crawl_recipe(task_info, proxy)

    def crawl(self, task_info, proxy):
        flag = False
        try:
            logging.debug('get page start to crawl')
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
                time.sleep(random.uniform(2, 2.8))
                url = head + url_part + tail + str(i)
                xcf_middle, ret_code = cf.connect(url, proxy)
                logging.debug('%s', ret_code)
                if ret_code == '404':
                    flag = True
                    break
                elif ret_code == '200':
                    if xcf_middle:
                        logging.debug('start parsing')
                        hp = HtmlParser(xcf_middle)
                        hp.parse_middle(tag, str(i))
                        logging.debug('html parsing success')
                        flag = True
                    else:
                        logging.debug('html parsing problems')
                elif ret_code == '503':
                    flag = False
                    break
        except Exception as e:
            logging.error('%s', e)
        finally:
            # 向队列反馈信息
            self.task_queue.task_done()
        if flag:
            logging.info('Bonus the good proxy: %s', proxy)
            self.resource_queue.put(proxy)  # copy self as bonus
        else:
            logging.info('Record the bad proxy: %s', proxy)
            self.task_queue.put(task_info)
        return flag

    def crawl_recipe(self, task_info, proxy):
        flag = False
        try:
            logging.debug('get page start to crawl')
            url_part = task_info
            head = 'http://www.xiachufang.com'
            cf = CryptFiend()
            time.sleep(random.uniform(2, 2.8))
            url = head + url_part
            xcf_middle, ret_code = cf.connect(url, proxy)
            logging.debug('%s', ret_code)
            if ret_code == '404':
                flag = True
            elif ret_code == '200':
                if xcf_middle:
                    logging.debug('start parsing')
                    hp = HtmlParser(xcf_middle)
                    hp.parse_recipe(url_part)
                    logging.debug('html parsing success')
                    flag = True
                else:
                    logging.debug('html parsing problems')
        except Exception as e:
            logging.error('%s', e)
        finally:
            # 向队列反馈信息
            self.task_queue.task_done()
        if flag:
            logging.info('Bonus the good proxy: %s', proxy)
            self.resource_queue.put(proxy)  # copy self as bonus
        else:
            logging.info('Record the bad proxy: %s', proxy)
            self.task_queue.put(task_info)
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
    for i in xrange(1):  # 每个代理初始化1份
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
