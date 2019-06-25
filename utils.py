import datetime
import json
import logging
import random
import execjs
import filelock
import xlrd
import xlwt
from lxml import etree
import requests
from xlutils3 import copy
from config import *
from proxy import get_proxy
from usually_data import target_type, USER_AGENTS, years, month
import pymysql as mdb

logging.basicConfig(filename='apiStudy.log', level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)


def day_params(city, date_time, ctx):
    method = 'GETDAYDATA'
    js = 'getEncryptedData("{0}", "{1}", "{2}")'.format(method, city, date_time)
    return ctx.eval(js)


def month_params(city, date_time, ctx):
    method = 'GETMONTHDATA'
    js = 'getEncryptedData("{0}", "{1}", "{2}")'.format(method, city, date_time)
    return ctx.eval(js)


# 解码response对象
def decode_info(info, ctx):
    js = 'decodeData("{0}")'.format(info)
    data = ctx.eval(js)
    data = json.loads(data)
    return data


def get_response(params):
    url = data_url
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': random.choice(USER_AGENTS)
    }
    data = {
        'hd': params
    }
    proxies = {}
    # 动态代理
    # headers, proxies = get_proxy()
    html_info = requests.post(url, data=data, headers=headers, proxies=proxies)
    if html_info.status_code is 200:
        return html_info.text
    else:
        return None


def get_city():
    url = city_url
    html_info = requests.get(url)
    html = etree.HTML(html_info.text)  # 初始化生成一个XPath解析对象
    items = html.xpath('//div[@class="all"]//a/text()')
    return items


def get_city_data():
    url = city_url
    html_info = requests.get(url)
    result = []
    html = etree.HTML(html_info.text)  # 初始化生成一个XPath解析对象
    items = html.xpath('//div[@class="all"]//ul[@class="unstyled"]')
    for i in items:
        cityName = i.xpath('div/li/a/text()')
        first_letter = i.xpath('div/b/text()')
        for c in cityName:
            result.append([c, first_letter[0][:-1]])
    for k, v in enumerate(result):
        result[k].append(k)
    return result


# 得到一个城市所有的历史数据
def get_all_info_by_city(city):
    now_y, now_m, _ = datetime.datetime.now().strftime('%Y-%m-%d').split('-')
    node = execjs.get()
    ctx = node.compile(open('decrypt.js', encoding='utf-8').read())
    result = []
    for y in years:
        for m in month:
            if now_y == y and (int(now_m) < int(m)):
                break
            date_time = y + m  # 201805
            html_info = get_response(day_params(city, date_time, ctx))
            print('爬取' + date_time + city)
            if html_info is not None:
                item = decode_info(html_info, ctx)
                for i in item['result']['data']['items']:
                    result.append(en_day_sdict_to_list(city, i))
    return result


# 得到一个城市最近一天的数据
def get_least_info_by_city(city):
    now_y, now_m, _ = datetime.datetime.now().strftime('%Y-%m-%d').split('-')
    node = execjs.get()
    ctx = node.compile(open('decrypt.js', encoding='utf-8').read())
    result = []
    date_time = now_y + now_m  # 201805
    html_info = get_response(day_params(city, date_time, ctx))
    if html_info is not None:
        item = decode_info(html_info, ctx)
        last_num = len(item['result']['data']['items'])

        if last_num is 0:
            logging.info(city + '无最近数据或未更新')
            return []
        logging.info('获取' + city + str(item['result']['data']['items'][-1]['time_point']) + '数据')
        return [en_day_sdict_to_list(city, item['result']['data']['items'][-1])]


# 爬取某城市一年的日数据
def get_year_info_by_city(year, city):
    now_y, now_m, _ = datetime.datetime.now().strftime('%Y-%m-%d').split('-')
    node = execjs.get()
    ctx = node.compile(open('decrypt.js', encoding='utf-8').read())
    result = []
    for m in month:
        if now_y == year and (int(now_m) < int(m)):
            break
        date_time = year + m  # 201805
        html_info = get_response(day_params(city, date_time, ctx))
        print('爬取' + date_time + city)
        if html_info is not None:
            item = decode_info(html_info, ctx)
            for i in item['result']['data']['items']:
                result.append(i)
    return result


# 爬取某城市的月平均数据
def get_month_average_info_by_city(city):
    now_y, now_m, _ = datetime.datetime.now().strftime('%Y-%m-%d').split('-')
    node = execjs.get()
    ctx = node.compile(open('decrypt.js', encoding='utf-8').read())
    result = []
    date_time = ''  # 201805
    html_info = get_response(month_params(city, date_time, ctx))
    if html_info is not None:
        item = decode_info(html_info, ctx)
        for i in item['result']['data']['items']:
            result.append(en_month_dict_to_list(city, i))
            logging.info('获取' + city + str(i['time_point']) + '的月平均数据')
    return result


def insert_db(result):
    conn = mdb.connect(host='47.107.173.225', port=3306, user='root', passwd='root', db='openApiStudy')
    cursor = conn.cursor()
    cursor.executemany(
        'INSERT INTO day_data(cityName,time_point,aqi,pm2_5,pm10,so2,no2,co,o3,rank,quality) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        result)
    conn.commit()
    conn.close()


def insert_month_db(result):
    conn = mdb.connect(host='47.107.173.225', port=3306, user='root', passwd='root', db='openApiStudy')
    cursor = conn.cursor()
    cursor.executemany(
        'INSERT INTO month_data(cityName,time_point,aqi,max_aqi,min_aqi,pm2_5,pm10,so2,no2,co,o3,rank,quality) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        result)

    conn.commit()
    conn.close()


def write_excel(result, ci, data_type):
    # rb = xlrd.open_workbook('1.xls', formatting_info=True)
    # wbk = xl_copy(rb)
    wbk = xlwt.Workbook()
    sheet = wbk.add_sheet(ci)
    for k, v in enumerate(data_type):
        sheet.write(0, k, v)
    for k, v in enumerate(result):
        for k1, v1 in enumerate(data_type):
            sheet.write(k + 1, k1, v[v1])
    wbk.save('./day/' + ci + '.xls')


def en_day_sdict_to_list(cityName, result):
    return [cityName, result['time_point'], result['aqi'], result['pm2_5'], result['pm10'], result['so2'],
            result['no2'], result['co'], result['o3'],
            result['rank'], result['quality']]


def en_month_dict_to_list(cityName, result):
    return [cityName, result['time_point'], result['aqi'], result['max_aqi'], result['min_aqi'], result['pm2_5'],
            result['pm10'], result['so2'],
            result['no2'], result['co'], result['o3'],
            result['rank'], result['quality']]
