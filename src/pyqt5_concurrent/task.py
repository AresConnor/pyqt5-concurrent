import functools
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable

from .future import Future


class Signal(QObject):
    finished = pyqtSignal(object)


class BaseTask(QRunnable):
    def __init__(self, _id: int, future: Future):
        super().__init__()
        self._signal: Signal = Signal()  # pyqtSignal(object)
        self._future: Future = future
        self._id: int = _id
        self._exception: Optional[BaseException] = None
        self._semaphore = future.semaphore

    @property
    def finished(self):
        return self._signal.finished

    @property
    def signal(self):
        return self._signal

    def _taskDone(self, **data):
        for d in data.items():
            self._future.setExtra(*d)
        self._signal.finished.emit(self._future)
        self._semaphore.release(1)


def func(*args) -> int:
    return sum(args)


class Task(BaseTask):
    def __init__(self, _id: int, future: Future, target: functools.partial, args, kwargs):
        super().__init__(_id=_id, future=future)
        self._target = target
        self._kwargs = kwargs
        self._args = args

    def run(self) -> None:
        try:
            self._taskDone(result=self._target(*self._args, **self._kwargs))
        except Exception as exception:
            self._taskDone(exception=exception)
