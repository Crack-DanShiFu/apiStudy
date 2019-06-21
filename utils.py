import datetime
import json
import random
import execjs
import xlrd
from lxml import etree
import requests
from xlutils3 import copy
from config import *
from usually_data import target_type, USER_AGENTS, years, month


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
    # 动态代理
    # headers, proxies = get_proxy()
    html_info = requests.post(url, data=data, headers=headers)
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
                    result.append(i)
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
            return city, None
        return city, item['result']['data']['items'][-1]


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
    print('爬取' + date_time + city)
    if html_info is not None:
        item = decode_info(html_info, ctx)
        for i in item['result']['data']['items']:
            result.append(i)
    return result


def write_excel(result, ci):
    rb = xlrd.open_workbook('1.xls', formatting_info=True)
    wbk = copy.copy(rb)
    sheet = wbk.add_sheet(ci)
    for k, v in enumerate(target_type):
        sheet.write(0, k, v)
    for k, v in enumerate(result):
        sheet.write(k + 1, 0, v['time_point'])
        sheet.write(k + 1, 1, v['aqi'])
        sheet.write(k + 1, 2, v['pm2_5'])
        sheet.write(k + 1, 3, v['pm10'])
        sheet.write(k + 1, 4, v['so2'])
        sheet.write(k + 1, 5, v['no2'])
        sheet.write(k + 1, 6, v['co'])
        sheet.write(k + 1, 7, v['o3'])
        sheet.write(k + 1, 8, v['rank'])
        sheet.write(k + 1, 9, v['quality'])
    wbk.save('1.xls')
