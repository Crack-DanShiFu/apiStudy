import threading
from queue import Queue
from proxy import get_proxy
# 获取一个城市所有的历史数据  by lczCrack  qq1124241615
# 加密参数
from utils import *


# 爬虫的线程对象
class AQIThread(threading.Thread):
    def __init__(self, threadID, city_queue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.city_queue = city_queue
        self.singal = threading.Event()
        self.singal.set()

    def run(self):
        while True:
            if self.city_queue.empty():
                break
            else:
                ci = self.city_queue.get()
                result = get_year_info_by_city(year='2018', city=ci)
                print(result)
                # write_excel(result, ci)

    def pause(self):
        self.log_ctrl.AppendText("pause\n")
        self.singal.clear()

    def restart(self):
        self.log_ctrl.AppendText("continue\n")
        self.singal.set()


if __name__ == '__main__':
    city_queue = Queue()
    for i in get_city():
        city_queue.put(i)

    threads = [AQIThread(i, city_queue) for i in range(num_of_threads)]
    for i in range(num_of_threads):
        threads[i].start()
