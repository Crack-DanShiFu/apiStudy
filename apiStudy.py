import json
from lxml import etree
import execjs
import requests


# 获取一个城市所有的历史数据  by lczCrack  qq1124241615

# 加密参数
def encryption_params(city, date_time, ctx):
    method = 'GETDAYDATA'
    js = 'getEncryptedData("{0}", "{1}", "{2}")'.format(method, city, date_time)
    return ctx.eval(js)


# 解码response对象
def decode_info(info, ctx):
    js = 'decodeData("{0}")'.format(info)
    data = ctx.eval(js)
    data = json.loads(data)
    return data


def get_response(params):
    url = 'https://www.aqistudy.cn/historydata/api/historyapi.php'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.80 Safari/537.36'
    }
    data = {
        'hd': params
    }
    html_info = requests.post(url, data=data)
    return html_info.text


def get_city():
    url = 'https://www.aqistudy.cn/historydata/'
    html_info = requests.get(url)
    html = etree.HTML(html_info.text)  # 初始化生成一个XPath解析对象
    items = html.xpath('//div[@class="all"]//a/text()')
    return items


def get_all_info_by_city(city):
    years = [str(i + 2013) for i in range(7)]
    month = [str(i if i > 9 else '0' + str(i)) for i in range(1, 13)]
    node = execjs.get()
    ctx = node.compile(open('decrypt.js', encoding='utf-8').read())
    for y in years:
        for m in month:
            date_time = y + m  # 201805
            html_info = get_response(encryption_params(city, date_time, ctx))
            item = decode_info(html_info, ctx)
            for i in item['result']['data']['items']:
                print(i)


if __name__ == '__main__':
    get_all_info_by_city('北京')
