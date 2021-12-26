#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author   : BianCheng
@IDE      : PyCharm
@Filename : get_issue_event.py
@Date     : 2021/12/19 14:22
"""
import pymongo
from pymongo import MongoClient
import requests
import json
import time
import concurrent.futures
from util.setup_token import Token
from util.setup_logging import setup_logging
import logging

setup_logging(colored=True)
log = logging.getLogger('mainModule')

# 初始化token池
token_pool = Token()

# 定义全局变量用于记录处理成功数
success_count = 0


def get_issue_timeline_one(url):
    issue_number = int(url.split('/')[-2])
    # page_url = url + '?{page}&per_page=100'

    page_number = 1  # 页码编号
    payload = {'page': page_number, 'per_page': 100}  # URL 参数

    # 请求头
    headers = {'User-Agent': 'Mozilla/5.0',
               'Authorization': None,
               'Content-Type': 'application/json',
               'Accept': 'application/vnd.github.v3+json'
               }

    # 存放所有页的结果
    all_pages_results = []

    try:
        while True:
            # 及时关闭会话
            session = requests.Session()
            session.keep_alive = False

            # 从token队列中取token，构造请求头
            token = token_pool.get_token()
            if token is not None:
                headers.update({'Authorization': 'token ' + token})

            response = requests.get(url, params=payload, headers=headers, timeout=20)
            token_pool.push_token(token)

            # 判断请求是否成功
            if response.status_code == 200:
                response_result = response.json()

                # 加入issue编号
                for r in response_result:
                    # dict.update()方法，为字典添加元素
                    r.update({"issue_number": issue_number})
                    all_pages_results.append(r)

                if len(response_result) < 100:
                    # 直接存入数据库并退出循环
                    # 批量插入数据到MongoDB
                    if len(all_pages_results) > 0:
                        if write_to_mongodb(all_pages_results):
                            global success_count
                            success_count += 1
                            log.info(f'{issue_number}号issue处理成功：{len(all_pages_results)}条')
                        else:
                            log.error(f'{issue_number}号issue请求成功，但写入数据库失败！')
                    else:
                        log.info(f'{issue_number}号issue请求成功，但没有数据！')
                        break
                else:
                    # 暂存并继续循环
                    page_number += 1
                    payload.update({'page': page_number})

            elif response.status_code == 404:
                log.error(f'{issue_number}号issue请求错误，错误码：404 Not Found')
                break

            elif response.status_code == 410:
                log.error(f'{issue_number}号issue请求错误，错误码：410 Gone')
                break

            # 发送未知错误请求码则抛出异常
            else:
                response.raise_for_status()

    except requests.exceptions.ConnectionError:
        log.critical(f'ConnectionError: {issue_number}号issue连接失败')

    except requests.exceptions.Timeout:
        log.error(f'超时: {issue_number}号issue请求超时')

    except requests.exceptions.HTTPError:
        log.error(f'{issue_number}号issue请求错误，错误码：{response.status_code}')
        log.critical(f'{issue_number}号issue请求错误，错误码：{response.status_code}', exc_info=True)

    except:
        log.critical(f'Unfortunitely -- An Unknow Error Happened! {issue_number}号issue请求失败', exc_info=True)


def write_to_mongodb(result):
    """
    将爬取结果写入数据库
    :param result: 爬取结果
    :return: 写入是否成功
    """
    try:
        # 批量插入数据到MongoDB
        event_col.insert_many(result)
        return True
    except pymongo.errors.InvalidOperation:
        log.critical("InvalidOperation: ", exc_info=True)
        return False


def write_to_jsonfile(issue_no, page_no, result):
    # 文件名
    base_filename = '../dataset/issue_event_{issue_no}_p{page_no}.json'
    # 存成json格式文件
    filename = base_filename.format(issue_no=issue_no, page_no=page_no)
    with open(filename, 'a', encoding='utf-8') as file:
        # indent控制缩进，ensure_ascii的值设为False以正常显示中文
        file.write(json.dumps(result, indent=2, ensure_ascii=False))


def get_issue_timeline_all(sites):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(get_issue_timeline_one, sites)


def get_downloaded_issue_list():
    """
    获取数据库已有的issue编号
    :return: 返回数据库已有的issue编号列表
    """
    # distinct(key, filter=None, session=None, **kwargs)
    # 获取此集合中所有文档中key的不同值的列表。
    already_issue_number = event_col.distinct('issue_number')
    return already_issue_number


def get_all_needs_issue_list():
    """
    获取数据库总共的issue编号
    :return: 返回数据库总共需要爬取的issue编号列表
    """
    # distinct(key, filter=None, session=None, **kwargs)
    # 获取此集合中所有文档中key的不同值的列表。
    issue_col = db['test_issue']
    issue_number_list = issue_col.distinct('number')
    return issue_number_list


def main():
    base_url = 'https://api.github.com/repos/rails/rails/issues/{issue_number}/timeline'

    already_issue_number = get_downloaded_issue_list()
    issue_number_list = get_all_needs_issue_list()

    # 求剩余待爬取的issue列表（求集合差集）
    need_issue_number = list(set(issue_number_list) - set(already_issue_number))
    # need_issue_number = list(set(issue_number_list).difference(set(already_issue_number)))
    need_issue_number.sort()
    print(need_issue_number)

    sites = [base_url.format(issue_number=i) for i in need_issue_number]

    start_time = time.perf_counter()
    get_issue_timeline_all(sites)
    end_time = time.perf_counter()
    log.info('Download {} issues timeline in {} seconds'.format(success_count, end_time - start_time))


if __name__ == '__main__':
    # 创建MongoClient连接
    with MongoClient('localhost', 27017) as client:
        # 创建数据库
        db = client['test_database']
        # 创建集合
        event_col = db['test_issue_event']
        main()
