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
date: 2015-09-15 12:09:58
last modified: 2015-09-15 17:59:58
version:
"""

import logging
import threading
import Queue
import time
import random
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

MAX_SIZE = 1024


class Worker(threading.Thread):
    """ 工作类 """
    def __init__(self, id):
        threading.Thread.__init__(self)
        self.id = id

    def run(self):
        logging.debug('Threading %s start', self.id)
        self.real_work()
        logging.debug('Threading %s end', self.id)

    def real_work(self):
        time.sleep(random.randint(1, 5))


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: "
                        "%(asctime)s: %(filename)s: %(lineno)d * "
                        "%(thread)d %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    queue = Queue.Queue(MAX_SIZE)
    # if infinite queue is needed, use next line
    # queue = Queue.Queue(0)
    task_file = sys.argv[1]
    with open(task_file) as fp:
        for line in fp:
            task_id = line[:-1]
            queue.put(task_id)
    while not queue.empty():
        task = queue.get()
        logging.debug('get %s from queue', task)
        worker = Worker(task)
        worker.start()


if __name__ == '__main__':
    main()
