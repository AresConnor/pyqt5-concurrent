_qt_found = False

while True:
    try:
        from PySide6.QtCore import (
            QThreadPool,
            QRunnable,
            QSemaphore,
            QMutex,
            QCoreApplication,
            QObject,
            Signal,
        QTimer,
        QThread
        )
        _qt_found = True
        break
    except ModuleNotFoundError:
        pass

    try:
        from PyQt6.QtCore import (
            QThreadPool,
            QRunnable,
            QSemaphore,
            QMutex,
            QCoreApplication,
            QObject,
            pyqtSignal as Signal,
            QTimer,
            QThread
        )
        _qt_found = True
        break
    except ModuleNotFoundError:
        pass

    try:
        from PySide2.QtCore import (
            QThreadPool,
            QRunnable,
            QSemaphore,
            QMutex,
            QCoreApplication,
            QObject,
            Signal,
            QTimer,
            QThread
        )
        _qt_found = True
        break
    except ModuleNotFoundError:
        pass

    try:
        from PyQt5.QtCore import (
            QThreadPool,
            QRunnable,
            QSemaphore,
            QMutex,
            QCoreApplication,
            QObject,
            pyqtSignal as Signal,
            QTimer,
            QThread
        )
        _qt_found = True
        break
    except ModuleNotFoundError:
        pass
    break

if not _qt_found:
    raise ModuleNotFoundError("No Qt bindings found")
