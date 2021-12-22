#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author   : BianCheng
@IDE      : PyCharm
@Filename : get_issue_event.py
@Date     : 2021/12/19 14:22
"""

from pymongo import MongoClient
import requests
import json
import time


def get_issue_timeline(issue_number):
    base_url = 'https://api.github.com/repos/rails/rails/issues/{issue_number}/timeline'.format(
        issue_number=issue_number)
    page_url = base_url + '?{page}&per_page=100'

    page_number = 1  # 页码编号

    token = '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'

    headers = {'User-Agent': 'Mozilla/5.0',
               'Authorization': 'token ' + token,
               'Content-Type': 'application/json',
               'Accept': 'application/json'
               }

    while True:
        try:
            session = requests.Session()
            session.keep_alive = False

            url = page_url.format(page=page_number)

            response = requests.get(url, headers=headers, timeout=(5, 5))
            if response.status_code == 200:
                response_result = response.json()
                # 判断有多少条，没有超过一百条说明已经爬完了，没有新的页需要爬了
                is_full = True if len(response_result) < 100 else False

                # 加入issue编号
                for r in response_result:
                    # dict.update()方法，为字典添加元素
                    r.update({"issue_number": issue_number})

                # 写入到json文件
                write_to_jsonfile(issue_number, page_number, response_result)

                # 批量插入数据到MongoDB
                collection.insert_many(response_result)

                print(f'{issue_number}号issue第{page_number}页处理成功：{len(response_result)}个')
                if is_full:
                    break
                else:
                    page_number = page_number + 1
            else:
                print('get_issue_timeline() error: fail to request')
        except Exception as e:
            print("ERR0R!get_issue_timeline() error:")
            print(e)


def write_to_jsonfile(issue_no, page_no, result):
    # 文件名
    base_filename = '../dataset/issue_event_{issue_no}_p{page_no}.json'
    # 存成json格式文件
    filename = base_filename.format(issue_no=issue_no, page_no=page_no)
    with open(filename, 'a', encoding='utf-8') as file:
        # indent控制缩进，ensure_ascii的值设为False以正常显示中文
        file.write(json.dumps(result, indent=2, ensure_ascii=False))


def get_issue_event_all(start_issue_no, end_issue_no):
    for issue_no in range(start_issue_no, end_issue_no + 1):
        get_issue_timeline(issue_no)


def main():
    start_time = time.perf_counter()
    get_issue_event_all(1, 4)
    end_time = time.perf_counter()
    print('Download {} issues in {} seconds'.format(10, end_time - start_time))


if __name__ == '__main__':
    # 创建MongoClient连接
    with MongoClient('localhost', 27017) as client:
        # 创建数据库
        db = client['test_database']
        # 创建集合
        collection = db['test_issue_event']
        main()
