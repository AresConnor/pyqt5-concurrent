# PyQt5-Concurrent

### 现已支持Pyside2 PySide6 PyQt5 PyQt6

## 简介:

​	pyqt5-concurrent是一个基于QThreadPool实现的并发库，主要是对QRunnable的封装，提供了一些易于使用的面向任务的API。简单实现了Future和Task，并支持链式操作，让代码逻辑更流畅。

## 为什么需要PyQt5-Concurrent:

​	如果你需要一些可以双向交互，粗粒度的并发，你可以使用QThread，它具有优先级，可运行的事件循环。但是有时候你实现并发可能是细粒度，多次轻量的，再使用QThread会显得有点重（当然你可以使用QOjbect.movetothread()来重复利用一个thread，但这就和size=1的QThreadPool没啥大区别)。

​	这个时候你可能会说，为什么试试QThreadPool+QRunnable呢？这确实是一个好的解决方法。但是QRunnable是一个虚类，你需要重写他的run方法并实例化。比方说你有多个任务，你会不耐烦的发现：你不得不写很多的QRunnable的子类。于是我想到将任务和run解耦，写一个Task模板。QRunnable的构造方法中传入一个目标函数及参数，在run中统一运行，并try catch错误，来实现QtConcurrent那样的面向任务的细粒度并发(pyqt5中并没有封装QtConcurrent库，这是一个高级的面向任务的API库。)。于是这个库就诞生了

​	(起初是因为我在给MCSL2写模组广场插件的时候，一页需要异步获取50个图像，任务的重复性很强，不是很适合用QThread，但是子类化QRunnable又太累了（lazy =_=），于是突发奇想，构造了一个初步的Future和TaskExecutor来实现基于任务的并发，之后在群主的建议下分出了并发逻辑构建成库)

## 一些例子:
- [示例1]
```python
import sys
import time
from PyQt5.QtCore import QCoreApplication
from pyqt5_concurrent.TaskExecutor import TaskExecutor


app = QCoreApplication(sys.argv)
future = TaskExecutor.run(time.sleep, 3)
future.finished.connect(app.quit)

print("3s 后退出")
app.exec_()
```

上图例子中简单介绍了TaskExecutor最基本的用法：TaskExecutor.run(self, target: Callable, *args, **kwargs) -> QFuture。args和kwargs将传入target中，并在线程池中运行。他返回一个future，你可以用他来实现任务成功，任务失败（发生异常），任务结束的回调。



- [示例2]
```python
import sys
import time
from PyQt5.QtCore import QCoreApplication
from pyqt5_concurrent.TaskExecutor import TaskExecutor

def work(who, t):
    while t > 0:
        print(f"{who} - hint")
        time.sleep(1)
        t -= 1

app = QCoreApplication(sys.argv)

TaskExecutor.map(work, [("worker1",3), ("worker2",5)]).then(
    onSuccess=app.quit
)

app.exec_()
```

上文中，你将使用一个类似multiprocess.map的方法来简单执行多个任务。这里同时使用了Future的then方法。这是一个可以链式调用的方法，可以设定一些回调。等同于Future.result.connect(cb),

Future.failed.connect(cb),Future.finished.connect(cb)。但是then返回的是Future本身，因此可以实现链式调用。



- [示例3]
```python
import sys
import time
from urllib.request import Request,urlopen
from PyQt5.QtCore import QCoreApplication
from pyqt5_concurrent.TaskExecutor import TaskExecutor

headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0"
}

def work1(url,filename):
    req = Request(
    	method='GET',
        url=url,
        headers=headers
    )
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(urlopen(req).read().decode("utf-8"))
    
def work2(url):
    req = Request(
    	method='HEAD',
        url=url,
        headers=headers
    )
    return urlopen(req).status

app = QCoreApplication(sys.argv)

task1 = TaskExecutor.createTask(
    work1, 
    "https://github.com",
    "github.html"
).then(lambda _:print("success saved page"), lambda e:print("failed",e))

task2 = TaskExecutor.createTask(
	work2,
    "https://www.baidu.com"
).then(lambda r:print("status",r), lambda e:print("failed",e))

TaskExecutor.runTasks([task1, task2]).finished.connect(app.quit)
print("2个任务开始")

# 你也可以只启动一个:
# task2.runTask().then(app.quit)
# 等于
# TaskExecutor.runTask(task1).then(app.quit)

# 你也可以等待任务1完成 在执行任务2
# task1.runTask().wait()  或者.synchronize()
# task2.runTask.then(app.quit)
app.exec_()
```



- [Task的用法]

```python
import sys
import time

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from pyqt5_concurrent.TaskExecutor import TaskExecutor
from pyqt5_concurrent.Future import QFuture

WORK_TIME = 10

# 创建必要的对象
app = QApplication(sys.argv)
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
```



- [QFuture.gather以及QFuture.wait()]


```python
# 创建一个带有优先级的任务
TaskExecutor.runWithPriority(print,1,"hello world")
TaskExecutor.createTask(print,"hello world").withPriority(1).runTask()
```

为任务添加优先级的两种方法（只有在任务等待被调度时，优先级才有意义）



- [UniqueTaskExecutor]

0.1.6添加UniqueTaskExecutor

它包装了一个非全局的线程池，如其名Unique，不同实例的线程池相互独立，意味着它是独立的执行单元，支持with语句。

UniqueTaskExecutor的api与TaskExecutor一致，用法请参考后者。

UniqueTaskExecutor支持设定并行的任务数量。

UniqueTaskExecutor退出with语句前会自动执行self.threadpool.waitForDone()，并会销毁自己

```python
class UniqueTaskExecutor(BaseTaskExecutor):
    def __init__(self, workers: int = CPU_COUNTS):
        super().__init__(useGlobalThreadPool=False)
        self.workers = workers

	...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.threadPool.waitForDone()
        self.deleteLater()
```



## 鸣谢：

1.PyQt5

2.[zhiyiYo (之一) (github.com)](https://github.com/zhiyiYo) (提出了一些很好的点子,例如链式调用then)

3.[rainzee (rainzee wang) (github.com)](https://github.com/rainzee)(提出了一些很好的点子,例如使用装饰器注册future回调)

(按照时间先后的顺序)