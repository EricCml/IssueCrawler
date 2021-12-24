#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author   : BianCheng
@IDE      : PyCharm
@Filename : setup_logging.py
@Date     : 2021/12/22 14:59
"""

import os
import yaml
import logging.config
import logging
import coloredlogs  # 彩色输出（可选）


class DebugFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.DEBUG


class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.INFO


class WarningFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.WARN


class ErrorFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.ERROR


class CriticalFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.CRITICAL


def setup_logging(default_path='../config/logging_setting.yaml', default_level=logging.INFO, env_key='LOG_CFG',
                  colored=False):
    fmt = "%(asctime)s,%(msecs)03d - %(name)s[%(process)d] - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)

                # 设置彩色输出（可选）
                if colored:
                    coloredlogs.install(level=default_level, fmt=fmt)
            except Exception as e:
                print(e)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
                if colored:
                    coloredlogs.install(level=default_level, fmt=fmt)
    else:
        logging.basicConfig(level=default_level)
        if colored:
            coloredlogs.install(level=default_level, fmt=fmt)
        print('Failed to load configuration file. Using default configs')
