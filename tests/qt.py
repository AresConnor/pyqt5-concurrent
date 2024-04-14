import importlib.util

QT_BINDINGS = None

qt_bindings = ["PySide6.QtCore", "PyQt6.QtCore", "PySide2.QtCore", "PyQt5.QtCore"]


def find_qt_bindings():
    for binding in qt_bindings:
        if importlib.util.find_spec(binding) is not None:
            return binding
    raise ModuleNotFoundError("No python Qt bindings found.")


qt_binding = find_qt_bindings()
QT_BINDINGS = qt_binding.split(".")[0]


# import
QThreadPool = importlib.import_module(qt_binding).QThreadPool
QRunnable = importlib.import_module(qt_binding).QRunnable
QSemaphore = importlib.import_module(qt_binding).QSemaphore
QMutex = importlib.import_module(qt_binding).QMutex
QCoreApplication = importlib.import_module(qt_binding).QCoreApplication
QObject = importlib.import_module(qt_binding).QObject
QTimer = importlib.import_module(qt_binding).QTimer
QThread = importlib.import_module(qt_binding).QThread
if "PyQt" in qt_binding:
    Signal = importlib.import_module(qt_binding).pyqtSignal
else:
    Signal = importlib.import_module(qt_binding).Signal
