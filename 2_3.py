#!/usr/bin/env python
# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (c) 2015 .com, Inc. All Rights Reserved
#
################################################################################
"""
description:
author: liufengxu
date: 2015-07-05 12:39:35
last modified: 2015-09-13 23:54:24
version:
"""

import logging
import urllib2
import cookielib
import re
import time
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


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
            logging.error('%s: %s', e.code, e.reason)

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


def write_line(file_name, content):
    with open(file_name, 'a') as fw:
        fw.write(content + '\n')

def do_task(url, proxy, tag):
    cf = CryptFiend()
    xcf_middle = cf.connect(url, proxy)
    if xcf_middle:
        hp = HtmlParser(xcf_middle)
        hp.parse_middle(tag)


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: "
                        "%(asctime)s: %(filename)s: %(lineno)d * "
                        "%(thread)d %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    cf = CryptFiend()
    # 使用代理
    # print cf.connect('http://www.baidu.com', '101.71.27.120:80')
    # 不使用代理
    # 抓取一级目录
    input_file = sys.argv[1]
    proxy = sys.argv[2]
    head = 'http://www.xiachufang.com'
    tail = '?page='
    with open(input_file) as fp:
        for line in fp:
            segs = line[:-1].split(' ')
            if len(segs) != 2:
                continue
            url_part, tag = segs
            for i in xrange(1, 51):
                time.sleep(1)
                url = head + url_part + tail + str(i)
                do_task(url, proxy, tag)
                else:
                    logging.info('page %s is empty', url)
                    continue

if __name__ == '__main__':
    main()
