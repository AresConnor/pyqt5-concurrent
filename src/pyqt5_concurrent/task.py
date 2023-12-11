import functools
from typing import Callable, Optional

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable

from .Future import QFuture


class Signal(QObject):
    finished = pyqtSignal(object)


class QBaseTask(QRunnable):
    def __init__(self, _id: int, future: QFuture):
        super().__init__()
        self._signal: Signal = Signal()  # pyqtSignal(object)
        self._future: QFuture = future
        self._id: int = _id
        self._exception: Optional[BaseException] = None
        self._semaphore = future.semaphore

    @property
    def finished(self):
        return self._signal.finished

    @property
    def signal(self):
        return self._signal
    
    @property
    def taskID(self):
        return self._id

    @property
    def future(self):
        return self._future

    def _taskDone(self, **data):
        for d in data.items():
            self._future.setExtra(*d)
        self._signal.finished.emit(self._future)
        self._semaphore.release(1)


def func(*args) -> int:
    return sum(args)


class QTask(QBaseTask):
    def __init__(self, _id: int, future: QFuture, target: functools.partial, executor ,args, kwargs):
        super().__init__(_id=_id, future=future)
        self._executor = executor
        self._target = target
        self._kwargs = kwargs
        self._args = args

    def run(self) -> None:
        try:
            self._taskDone(result=self._target(*self._args, **self._kwargs))
        except Exception as exception:
            self._taskDone(exception=exception)

    def then(self, onSuccess: Callable, onFailed: Callable = None, onFinished: Callable = None) -> 'QTask':
        self._future.then(onSuccess, onFailed, onFinished)
        return self

    def runTask(self) -> QFuture:
        return self._executor.runTask(self)