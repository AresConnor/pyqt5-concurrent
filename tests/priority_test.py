import sys
import time

from qt import QCoreApplication

from pyqt5_concurrent.TaskExecutor import TaskExecutor

app = QCoreApplication(sys.argv)


def task(priority):
    print(f"task with {priority} started")
    time.sleep(3)
    print(f"task with {priority} finished")


TaskExecutor.globalInstance().threadPool.setMaxThreadCount(1)
task1 = TaskExecutor.createTask(task, 1).withPriority(1)
task2 = TaskExecutor.createTask(task, 0).withPriority(0)
task3 = TaskExecutor.createTask(task, 2).withPriority(2)
task4 = TaskExecutor.createTask(task, 3).withPriority(3)
gather = TaskExecutor.runTasks([task1, task2, task3, task4])
gather.finished.connect(app.quit)

app.exec()
