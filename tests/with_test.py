import time

from pyqt5_concurrent.TaskExecutor import UniqueTaskExecutor

task_num = 10
with UniqueTaskExecutor(4) as executor:
    tasks = []
    for i in range(task_num):
        executor.run(lambda ident: [print(ident), time.sleep(1)], i)
