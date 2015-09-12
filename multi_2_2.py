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
date: 2015-09-12 23:35:07
last modified: 2015-09-12 23:51:18
version:
"""

import logging
import sys
import subprocess


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: "
                        "%(asctime)s: %(filename)s: %(lineno)d * "
                        "%(thread)d %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    proxy_file = sys.argv[1]
    input_files = sys.argv[2]
    proxy_list = []
    with open(proxy_file) as fp:
        for line in fp:
            proxy_list.append(line[:-1])
    for input_file in input_files.split(','):
        subprocess.Popen('python 2_2.py ' + input_file + ' ' + proxy_list.pop()\
                         + ' > ' + input_file + '.out' + ' 2> ' + input_file + \
                         '.log', shell=True)


if __name__ == '__main__':
    main()
