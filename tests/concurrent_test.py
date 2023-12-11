import sys
import time
from urllib.request import Request,urlopen

from PyQt5.QtCore import QCoreApplication
from pyqt5_concurrent.TaskExecutor import TaskExecutor
app = QCoreApplication(sys.argv)

def func(i,t):
    while t > 0:
        print(f"Task_{i} - hint")
        time.sleep(1)
        t -= 1

def savePage(html, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"saved page to path: {path}")

def getPage(url):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0"
    req = Request(
        method='GET',
        url=url,
        headers={'User-Agent': ua}
    )
    return urlopen(req).read().decode("utf-8")

print("测试简单的run\n" + "=" * 50)
TaskExecutor.run(func,114514,t=2).wait()

print("测试单个Task的链式启动\n" + "=" * 50)
TaskExecutor.createTask(getPage, "https://github.com").then(onSuccess=lambda r: savePage(r,"github.html"),onFailed=lambda _:print("failed:",_)).runTask().wait()

print("测试map\n" + "=" * 50)
args = [(0, 3),(1, 5)]
fut = TaskExecutor.map(func,args).wait()

print("测试异步爬虫\n" + "=" * 50)
task1 = TaskExecutor.createTask(getPage, "https://www.baidu.com").then(onSuccess=lambda r: savePage(r,"baidu1.html"),onFailed=lambda _:print("failed:",_))
task2= TaskExecutor.createTask(getPage, "https://www.baidu.com").then(onSuccess=lambda r: savePage(r,"baidu2.html"),onFailed=lambda _:print("failed:",_))

TaskExecutor.runTasks([task1,task2]).finished.connect(app.quit)

print("任务开始")
sys.exit(app.exec_())
