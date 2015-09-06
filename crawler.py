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
last modified: 2015-07-25 18:20:40
version:
"""

import logging
import urllib2
import cookielib


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
            opener = self.set_cookie()
            logging.debug('opener ready')
            urllib2.install_opener(opener)
            logging.debug('global opener ready')
            req = urllib2.Request(url)  # 使用 Request 会处理重定向
            logging.debug('set request url ok')
            resp = urllib2.urlopen(req, timeout=self.timeout)
            logging.debug('urlopen success')
            logging.debug('%s', resp.info())
            resp_html = resp.read()
            resp.close()
        except Exception as e:
            logging.error('%s', e)
        return resp_html

    def set_proxy_handler(self, http_proxy):
        """ 设置代理 """
        self.proxy_handler = urllib2.ProxyHandler({'http':
                                                   'http://%s/' % http_proxy})

    def set_cookie(self):
        cookie = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
        return opener


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: "
                        "%(asctime)s: %(filename)s: %(lineno)d * "
                        "%(thread)d %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    cf = CryptFiend()
    # 使用代理
    # print cf.connect('http://www.baidu.com', '101.71.27.120:80')
    # 不使用代理
    print cf.connect('http://www.baidu.com')

if __name__ == '__main__':
    main()
