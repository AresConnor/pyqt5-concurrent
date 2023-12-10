import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtWidgets import QApplication

from src.pyqt5_concurrent.taskManager import TaskExecutor

app = QApplication(sys.argv)
executor = TaskExecutor.getGlobalInstance()

TIME_TO_RAISE = 3


def func(t):
    print(f"task will raise exception after {t}s")
    time.sleep(t)
    raise Exception("test exception")


fut = executor._asyncRun(func, TIME_TO_RAISE)
fut.result.connect(lambda x: print("result signal:", x))  # result 将不会被触发，因为任务抛出了异常
fut.failed.connect(lambda x: print("failed signal:", x))  # failed 信号将会被触发
fut.finished.connect(lambda x: {print("done signal:", x), app.quit()})  # done 信号将会被触发(不管任务是否抛出异常,只要是任务结束了,done信号就会被触发)
app.exec_()
