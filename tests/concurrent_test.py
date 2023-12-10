import os
import sys
import time
from urllib.request import Request,urlopen

from pyqt5_concurrent.future import QFuture

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from PyQt5.QtWidgets import QApplication
from src.pyqt5_concurrent.taskManager import TaskExecutor
app = QApplication(sys.argv)


def savePage(html, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"saved page to path: {path}")


def getPage(url):
    time.sleep(1)
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0"
    req = Request(
        method='GET',
        url=url,
        headers={'User-Agent': ua}
    )
    return urlopen(req).read().decode("utf-8")


print("测试异步爬虫\n" + "=" * 50)
task1 = TaskExecutor.createTask(getPage, "https://www.baidu.com").then(lambda r: savePage(r,"baidu1.html"))
task2= TaskExecutor.createTask(getPage, "https://www.baidu.com").then(lambda r: savePage(r,"baidu2.html"))

TaskExecutor.runAll([task1,task2]).finished.connect(app.quit)

print("任务开始")
sys.exit(app.exec_())
