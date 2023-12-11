import sys
import time

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QCoreApplication

from pyqt5_concurrent.TaskExecutor import TaskExecutor
from pyqt5_concurrent.Future import QFuture

WORK_TIME = 10

# 创建必要的对象
app = QCoreApplication(sys.argv)
futures = []

# 记录开始时间
t = time.time()

# 创建work_time个任务,每个任务sleep 1~work_time 秒
for _ in range(1, WORK_TIME + 1):
    futures.append(
        TaskExecutor.run(
            lambda i: {time.sleep(i), print(f"task_{i} done, waited: {i}s")}, _
        )
    )  # add coroutine tasks
print("task start")

gathered = QFuture.gather(futures)
gathered.synchronize()  # equivalent to: fut.wait()

print("all tasks done:", time.time() - t, ",expected:", WORK_TIME)

QTimer.singleShot(1000, app.quit)  # close app after 1s
app.exec_()
