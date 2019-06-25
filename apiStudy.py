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
        while not self.city_queue.empty():
            ci = self.city_queue.get()
            result = get_month_average_info_by_city(city=ci)
            print(result)
            insert_month_db(result)
            # insert_db(result)
            # write_excel(result, ci)

    def pause(self):
        self.log_ctrl.AppendText("pause\n")
        self.singal.clear()

    def restart(self):
        self.log_ctrl.AppendText("continue\n")
        self.singal.set()


if __name__ == '__main__':
    city_queue = Queue()
    citys = get_city()

    for i in citys:
        city_queue.put(i)

    threads = [AQIThread(i, city_queue) for i in range(num_of_threads)]
    for i in range(num_of_threads):
        threads[i].start()
