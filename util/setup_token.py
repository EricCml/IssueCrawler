#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author   : BianCheng
@IDE      : PyCharm
@Filename : setup_token.py
@Date     : 2021/12/22 21:48
"""

from queue import Queue
import json


class Token(object):
    def __init__(self, config_path="../config/tokens.json"):
        self.config_path = config_path

        with open(config_path) as fp:
            config = json.load(fp)
        tokens = config["tokens"]

        # token的队列
        token_pool = Queue(len(tokens))

        for token in tokens:
            token_pool.put(token)
        self.token_pool = token_pool

    def get_token(self):
        if self.token_pool.empty():
            print('token池为空！')
            return None
        token = self.token_pool.get()
        # TODO:应该判断该token是否还有访问机会，否则再放回池子里
        return token

    def push_token(self, token):
        if self.token_pool.full():
            print('token池已满！')
            return False
        self.token_pool.put(token)
        return True
