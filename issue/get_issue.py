#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Author   : BianCheng
@IDE      : PyCharm
@Filename : get_issue.py
@Date     : 2021/12/22 14:28
"""
import pymongo.errors
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


def get_issue_one(url, retry_times=3):
    """
    Get an issue: 按issue_number爬取issue
    :param url: 待爬取issue的url
    :param retry_times: 重试次数
    :return: 无返回
    """
    issue_number = int(url.split('/')[-1])

    # 及时关闭会话
    session = requests.Session()
    session.keep_alive = False
    # 请求头
    headers = {'User-Agent': 'Mozilla/5.0',
               'Authorization': None,
               'Content-Type': 'application/json',
               'Accept': 'application/vnd.github.v3+json'
               }

    # 从token队列中取token，构造请求头
    token = token_pool.get_token()
    if token is not None:
        headers.update({'Authorization': 'token ' + token})

    try:
        response = requests.get(url, headers=headers, timeout=10)
        token_pool.push_token(token)
        # 判断请求是否成功
        if response.status_code == 200:
            response_result = response.json()
            # 判断有多少条再插入数据
            if len(response_result) > 0:
                # 写入到json文件
                # write_to_jsonfile(issue_number, response_result)

                # 插入数据到MongoDB数据库
                if write_to_mongodb(response_result):
                    global success_count
                    success_count += 1
                    log.info(f'{issue_number}号issue处理成功')
                else:
                    log.error(f'{issue_number}号issue请求成功，但写入数据库失败！')

        else:
            # 如果还有重试机会，则休眠一会重新爬
            if retry_times > 0:
                time.sleep(3 * (4 - retry_times))
                get_issue_one(url, retry_times - 1)
            else:
                if response.status_code == 301:
                    log.error(f'{issue_number}号issue请求错误，错误码：301 Moved Permanently')

                elif response.status_code == 304:
                    log.error(f'{issue_number}号issue请求错误，错误码：304 Not Modified')

                elif response.status_code == 404:
                    log.error(f'{issue_number}号issue请求错误，错误码：404 Not Found')

                elif response.status_code == 410:
                    log.error(f'{issue_number}号issue请求错误，错误码：410 Gone')

                # 发送未知错误请求码则抛出异常
                else:
                    response.raise_for_status()

    except requests.exceptions.ConnectionError:
        log.critical(f'ConnectionError: {issue_number}号issue连接失败')

    except requests.exceptions.Timeout:
        log.error(f'超时: {issue_number}号issue请求超时')

    except requests.exceptions.HTTPError:
        log.error(f'HTTPError: {issue_number}号issue请求错误，错误码：{response.status_code}')

    except:
        log.critical(f'Unfortunitely -- An Unknow Error Happened! {issue_number}号issue处理失败', exc_info=True)


def write_to_mongodb(result):
    """
    将爬取结果写入数据库
    :param result: 爬取结果
    :return: 写入是否成功
    """
    try:
        # 插入数据到MongoDB
        collection.insert_one(result)
        return True
    except pymongo.errors.InvalidOperation:
        log.critical("InvalidOperation: ", exc_info=True)
        return False


def write_to_jsonfile(issue_no, result):
    """
    将爬取结果写入json文件
    :param issue_no: issue编号
    :param result: 爬取结果
    :return: 无返回
    """
    # 文件名
    base_filename = '../data/hello-world_issue_{issue_no}.json'
    # 存成json格式文件
    filename = base_filename.format(issue_no=issue_no)
    with open(filename, 'a', encoding='utf-8') as file:
        # indent控制缩进，ensure_ascii的值设为False以正常显示中文
        file.write(json.dumps(result, indent=2, ensure_ascii=False))


def get_issue_all(sites):
    """
    爬取所有issue
    :param sites: 待爬取的url列表
    :return: 无返回
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(get_issue_one, sites)


def get_downloaded_issue_list():
    """
    获取数据库已有的issue编号
    :return: 返回数据库已有的issue编号列表
    """
    # distinct(key, filter=None, session=None, **kwargs)
    # 获取此集合中所有文档中key的不同值的列表。
    already_issue_number = collection.distinct('number')
    return already_issue_number


def main():
    base_url = 'https://api.github.com/repos/rails/rails/issues/{issue_number}'

    already_issue_number = get_downloaded_issue_list()
    issue_number_list = [i for i in range(1, 43943)]

    # 求剩余待爬取的issue列表（求集合差集）
    need_issue_number = list(set(issue_number_list) - set(already_issue_number))
    # need_issue_number = list(set(issue_number_list).difference(set(already_issue_number)))
    need_issue_number.sort()

    sites = [base_url.format(issue_number=i) for i in need_issue_number]

    start_time = time.perf_counter()
    get_issue_all(sites)
    end_time = time.perf_counter()
    log.info('Download {} issues in {} seconds'.format(success_count, end_time - start_time))


if __name__ == '__main__':
    # 创建MongoClient连接
    with MongoClient('localhost', 27017) as client:
        # 创建数据库
        db = client['test_database']
        # 创建集合
        collection = db['test_issue']

        main()
