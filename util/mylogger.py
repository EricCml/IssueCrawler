#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author   : BianCheng
@IDE      : PyCharm
@Filename : mylogger.py
@Date     : 2021/12/20 16:17
"""

import logging
from logging import handlers

# 日志记录器
logger = logging.getLogger('test')
logger.setLevel(level=logging.DEBUG)

# 日志格式化器
formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

# 日志处理器：文件输出
file_handler = logging.FileHandler(filename='../log/error.log', mode='a', encoding='utf-8')
file_handler.setLevel(level=logging.ERROR)
file_handler.setFormatter(formatter)

# 日志处理器：控制台输出
stream_handler = logging.StreamHandler()
stream_handler.setLevel(level=logging.INFO)
stream_handler.setFormatter(formatter)

# 日志处理器：按照时间自动分割日志文件
time_rotating_file_handler = handlers.TimedRotatingFileHandler(filename='../log/get_issue_event.log', when='D',
                                                               encoding='utf-8')
time_rotating_file_handler.setLevel(level=logging.INFO)
time_rotating_file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.addHandler(time_rotating_file_handler)
