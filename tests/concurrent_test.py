import os
import sys
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from PyQt5.QtWidgets import QApplication
from src.pyqt5_concurrent.taskManager import TaskExecutor
app = QApplication(sys.argv)


def savePage(html, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"saved page to path: {path}")


def getPage(url):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0"
    response = requests.request(
        method='GET',
        url=url,
        headers={'User-Agent': ua}
    )
    return response.text


print("测试异步爬虫\n" + "=" * 50)
executor = TaskExecutor(useGlobalThreadPool=False)
run = executor._asyncRun(getPage, "https://www.baidu.com")
run.result.connect(lambda r: savePage(r, "baidu.html"))
run.finished.connect(lambda x: app.quit())
print("任务开始")
sys.exit(app.exec_())
