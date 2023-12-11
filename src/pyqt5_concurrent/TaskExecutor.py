import os
import functools
import warnings
from typing import Dict, List, Callable, Iterable,Tuple

from PyQt5 import QtCore
from PyQt5.QtCore import QThreadPool, QObject

from .Future import QFuture, FutureCancelled
from .Task import QBaseTask, QTask


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
        use the global TaskExecutor instance to avoid task ID conflicts
        :param target:
        :param args:
        :param kwargs:
        :return:
        """
        return cls.globalInstance()._asyncRun(target, *args, **kwargs)
    
    @classmethod
    def map(cls, target:Callable, iter_:Iterable) -> QFuture:
        """
        a simple wrapper for createTask and runTasks.

        iter_ must be like : [1, 2, 3] for [(1, 2), (3, 4)],
        if you need **kwargs in iter_, use createTask instead.
        """
        taskList = []
        for args in iter_:
            if isinstance(args,Tuple):
                taskList.append(cls.createTask(target,*args))
            else:
                taskList.append(cls.createTask(target,args))
        return cls.runTasks(taskList)        

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
