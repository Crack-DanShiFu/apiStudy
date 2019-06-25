import sys
import time
import hashlib

# 个人中心获取orderno与secret 如果不用代理则不用设置
orderno = "DT20190608165232Y5DenA70"
secret = "59a7a0df437f4caae30d8b6335b8a043"

ip = "dynamic.xiongmaodaili.com"
port = "8089"


def get_proxy():
    _version = sys.version_info
    is_python3 = (_version[0] == 3)
    ip_port = ip + ":" + port
    timestamp = str(int(time.time()))  # 计算时间戳
    txt = ""
    txt = "orderno=" + orderno + "," + "secret=" + secret + "," + "timestamp=" + timestamp
    if is_python3:
        txt = txt.encode()
    md5_string = hashlib.md5(txt).hexdigest()  # 计算sign
    sign = md5_string.upper()  # 转换成大写
    auth = "sign=" + sign + "&" + "orderno=" + orderno + "&" + "timestamp=" + timestamp
    proxy = {"http": "http://" + ip_port}
    headers = {"Proxy-Authorization": auth}
    return headers, proxy
