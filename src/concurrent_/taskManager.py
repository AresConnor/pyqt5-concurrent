import functools
import warnings
from typing import Dict, List, Callable, Iterable

from PyQt5 import QtCore
from PyQt5.QtCore import QThreadPool, QObject

from .future import Future, FutureCancelled
from .task import BaseTask, Task


# substitute for psutil.cpu_count()
def cpu_count():
    return 8


class BaseTaskExecutor(QObject):
    def __init__(self, useGlobalThreadPool=True):
        super().__init__()
        self.useGlobalThreadPool = useGlobalThreadPool
        if useGlobalThreadPool:
            self.threadPool = QThreadPool.globalInstance()
        else:
            self.threadPool = QThreadPool()
            self.threadPool.setMaxThreadCount(2 * cpu_count())  # IO-Bound = 2*N, CPU-Bound = N + 1
        self.taskMap = {}
        self.tasks: Dict[int, BaseTask] = {}
        self.taskCounter = 0

    def deleteLater(self) -> None:
        if not self.useGlobalThreadPool:
            self.threadPool.clear()
            self.threadPool.waitForDone()
            self.threadPool.deleteLater()
        super().deleteLater()

    def _taskRun(self, task: BaseTask, future: Future, **kwargs):
        self.tasks[self.taskCounter] = task
        future.setTaskID(self.taskCounter)
        # task.signal.finished:pyqtBoundSignal
        task.signal.finished.connect(self._taskDone, type=QtCore.Qt.ConnectionType.QueuedConnection)
        self.threadPool.start(task)
        self.taskCounter += 1

    def _taskDone(self, fut: Future):
        """
        need manually set Future.setFailed() or Future.setResult() to be called!!!
        """
        self.tasks.pop(fut.getTaskID())
        if isinstance(e := fut.getExtra("exception"), Exception):
            fut.setFailed(e)
        else:
            fut.setResult(fut.getExtra("result"))

    def _taskCancel(self, fut: Future):
        stack: List[Future] = [fut]
        while stack:
            f = stack.pop()
            if not f.hasChildren() and not f.isDone():
                self._taskSingleCancel(f)
                f.setFailed(FutureCancelled())
            stack.extend(f.getChildren())

    def _taskSingleCancel(self, fut: Future):
        _id = fut.getTaskID()
        taskRef: BaseTask = self.tasks[_id]
        if taskRef is not None:
            try:
                taskRef.setAutoDelete(False)
                self.threadPool.cancel(taskRef)
                taskRef.setAutoDelete(True)
            except RuntimeError:
                print("wrapped C/C++ object of type BaseTask has been deleted")
        del taskRef

    def cancelTask(self, fut: Future):
        warnings.warn("BaseTaskExecutor.cancelTask: 目前好像不能正常工作...", DeprecationWarning)
        self._taskCancel(fut)


class TaskExecutor(BaseTaskExecutor):
    globalInstance = None

    def _asyncRun(self, target: Callable, *args, **kwargs) -> Future:
        future = Future()
        task = Task(
            _id=self.taskCounter,
            future=future,
            target=target if target is functools.partial else functools.partial(target),
            args=args,
            kwargs=kwargs
        )
        self._taskRun(task, future)
        return future

    def _asyncMap(self, target: Callable, iterable: List[Iterable]):
        futures = []
        for args in iterable:
            futures.append(self._asyncRun(target, *args))
        return Future.gather(futures)

    @staticmethod
    def getGlobalInstance():
        if TaskExecutor.globalInstance is None:
            TaskExecutor.globalInstance = TaskExecutor()
        return TaskExecutor.globalInstance

    @classmethod
    def runTask(cls, target: Callable, *args, **kwargs) -> Future:
        """
        使用统一的TaskExecutor实例,防止task id冲突
        :param target:
        :param args:
        :param kwargs:
        :return:
        """
        return cls.getGlobalInstance()._asyncRun(target, *args, **kwargs)
