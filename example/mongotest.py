#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author   : BianCheng
@IDE      : PyCharm
@Filename : mongotest.py
@Date     : 2021/12/19 14:31
"""

from pymongo import MongoClient
import requests
import pprint
import json


def get_issue_timeline():
    url = 'https://api.github.com/repos/octocat/hello-world/issues/42/timeline'
    response = requests.get(url)
    if response.status_code == 200:
        response_result = response.json()
        # 加入issue编号
        for r in response_result:
            # dict.update()方法，为字典添加元素
            r.update({"issue_number": 42})

        # 存成json格式文件
        with open('../dataset/mysample.json', 'w', encoding='utf-8') as file:
            # indent控制缩进，ensure_ascii的值设为False以正常显示中文
            file.write(json.dumps(response_result, indent=2, ensure_ascii=False))

        return True, response_result
    else:
        return False, None


if __name__ == '__main__':
    # 创建MongoClient连接
    with MongoClient('localhost', 27017) as client:
        # 创建数据库
        db = client['test_database']
        # 创建集合
        collection = db['test_collection']
        # 获取数据
        status, result = get_issue_timeline()
        # 如果成功爬到数据
        if status:
            # 批量插入数据到MongoDB
            insert_result = collection.insert_many(result)

            print(insert_result.inserted_ids)
            # pprint.pprint(result)
        else:
            print('GitHub API获取数据失败!')
