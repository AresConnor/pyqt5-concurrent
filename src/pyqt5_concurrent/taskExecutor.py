import os
import functools
import warnings
from typing import Dict, List, Callable, Iterable

from PyQt5 import QtCore
from PyQt5.QtCore import QThreadPool, QObject

from .future import QFuture, FutureCancelled
from .task import QBaseTask, QTask


# substitute for psutil.cpu_count()
def cpu_count():
    return os.cpu_count()  # logical cores


class BaseTaskExecutor(QObject):
    def __init__(self, useGlobalThreadPool=True):
        super().__init__()
        self.useGlobalThreadPool = useGlobalThreadPool
        if useGlobalThreadPool:
            self.threadPool = QThreadPool.globalInstance()
        else:
            self.threadPool = QThreadPool()
            self.threadPool.setMaxThreadCount(cpu_count())
        self.taskMap = {}
        self.tasks: Dict[int, QBaseTask] = {}
        self.taskCounter = 0

    def deleteLater(self) -> None:
        if not self.useGlobalThreadPool:
            self.threadPool.clear()
            self.threadPool.waitForDone()
            self.threadPool.deleteLater()
        super().deleteLater()

    def _runTask(self, task: QBaseTask) -> QFuture:
        future = task._future
        future.setTaskID(task.taskID)
        task.signal.finished.connect(self._taskDone, type=QtCore.Qt.ConnectionType.QueuedConnection)
        self.threadPool.start(task)
        return future

    def _createTask(self, target, args, kwargs) -> QTask:
        future = QFuture()
        task = QTask(
            _id=self.taskCounter,
            future=future,
            target=target if target is functools.partial else functools.partial(target),
            executor=self,
            args=args,
            kwargs=kwargs
        )
        self.tasks[self.taskCounter] = task
        self.taskCounter += 1
        return task

    def _taskDone(self, fut: QFuture):
        """
        need manually set Future.setFailed() or Future.setResult() to be called!!!
        """
        self.tasks.pop(fut.getTaskID())
        e = fut.getExtra("exception")
        if isinstance(e, Exception):
            fut.setFailed(e)
        else:
            fut.setResult(fut.getExtra("result"))

    def _taskCancel(self, fut: QFuture) -> None:
        stack: List[QFuture] = [fut]
        while stack:
            f = stack.pop()
            if not f.hasChildren() and not f.isDone():
                self._taskSingleCancel(f)
                f.setFailed(FutureCancelled())
            stack.extend(f.getChildren())

    def _taskSingleCancel(self, fut: QFuture) -> None:
        _id = fut.getTaskID()
        taskRef: QBaseTask = self.tasks[_id]
        if taskRef is not None:
            try:
                taskRef.setAutoDelete(False)
                self.threadPool.cancel(taskRef)
                taskRef.setAutoDelete(True)
            except RuntimeError:
                print("wrapped C/C++ object of type BaseTask has been deleted")
        del taskRef

    def cancelTask(self, fut: QFuture) -> None:
        """
        currently, this method can not work properly...
        """
        warnings.warn("BaseTaskExecutor.cancelTask: currently, this method can not work properly...",
                      DeprecationWarning)
        self._taskCancel(fut)


class TaskExecutor(BaseTaskExecutor):
    _globalInstance = None

    def _asyncRun(self, target: Callable, *args, **kwargs) -> QFuture:
        task = self._createTask(target, args, kwargs)
        return self._runTask(task)

    def _asyncMap(self, target: Callable, iterable: List[Iterable]) -> QFuture:
        futures = []
        for args in iterable:
            futures.append(self._asyncRun(target, *args))
        return QFuture.gather(futures)

    @staticmethod
    def globalInstance() -> 'TaskExecutor':
        if TaskExecutor._globalInstance is None:
            TaskExecutor._globalInstance = TaskExecutor()
        return TaskExecutor._globalInstance

    @classmethod
    def run(cls, target: Callable, *args, **kwargs) -> QFuture:
        """
        使用统一的TaskExecutor实例,防止task id冲突
        :param target:
        :param args:
        :param kwargs:
        :return:
        """
        return cls.globalInstance()._asyncRun(target, *args, **kwargs)

    @classmethod
    def createTask(cls, target: Callable, *args, **kwargs) -> QTask:
        return cls.globalInstance()._createTask(target, args, kwargs)

    @classmethod
    def runTask(cls, task: QTask) -> QFuture:
        return cls.globalInstance()._runTask(task)

    @classmethod
    def runTasks(cls, tasks: List[QTask]) -> QFuture:
        futs = []
        for task in tasks:
            futs.append(cls.runTask(task))
        return QFuture.gather(futs)
