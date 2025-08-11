import threading


class ScheduleStack(object):
    _instance = None
    _lock = threading.Lock()


    def __new__(cls):
        if ScheduleStack._instance is None:
            with ScheduleStack._lock:
                if ScheduleStack._instance is None:
                    ScheduleStack._instance = super(ScheduleStack, cls).__new__(cls)
        return ScheduleStack._instance

    def __init__(self):
        self._max_scan_queue = 3
        self._scan_queue = []
        self._wait_queue = []

    @property
    def scan_queue(self):
        return self._scan_queue

    @scan_queue.setter
    def scan_queue(self, value):
        self._scan_queue = value

    @scan_queue.deleter
    def scan_queue(self):
        del self._scan_queue

    @property
    def wait_queue(self):
        return self._wait_queue

    @wait_queue.setter
    def wait_queue(self, value):
        self._wait_queue = value

    @wait_queue.deleter
    def wait_queue(self):
        del self._wait_queue

    @property
    def max_scan_queue(self):
        return self._max_scan_queue

    @max_scan_queue.setter
    def max_scan_queue(self, value):
        self._max_scan_queue = value

    @max_scan_queue.deleter
    def max_scan_queue(self):
        del self._max_scan_queue