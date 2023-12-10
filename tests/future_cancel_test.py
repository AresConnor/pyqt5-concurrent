import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QApplication

from src.concurrent_.taskManager import TaskExecutor

app = QApplication(sys.argv)
taskExecutor = TaskExecutor.getGlobalInstance()

TIME_TO_SLEEP = 3
TIME_TO_CANCEL = 1


# ===============================================================================
def func(t):
    print(f"task will work 10s, current Thread:{QThread.currentThread()}")
    while t > 0:
        print(f"task work time remains {t}s")
        time.sleep(0.5)
        t -= 0.5


def cancelFunc(taskManager_, fut_, beginTime_):
    taskManager_.cancelTask(fut_)
    print(f"task canceled, {time.time() - beginTime_}s elapsed")


fut = taskExecutor.asyncRun(func, TIME_TO_SLEEP)
beginTime = time.time()
print("task started")
QTimer.singleShot(TIME_TO_CANCEL * 1000, lambda: cancelFunc(taskExecutor, fut, beginTime))  # cancel task after 5s
QTimer.singleShot((TIME_TO_SLEEP + 1) * 1000, app.quit)  # close app
print("显然,这个测试是失败的,还没研究为什么,TaskExecutor中调用了QThreadPool::cancel()函数,但是任务还是继续执行了")
app.exec_()
