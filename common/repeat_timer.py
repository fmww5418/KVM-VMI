from threading import Timer
import time


class RepeatableTimer(object):
    def __init__(self, interval, fun, args=[], kwargs={}):
        self._interval = interval
        self._function = fun
        self._args = args
        self._kwargs = kwargs
        self._enable = False
        self.t = None

    def start(self):
        self._enable = True
        if self._enable:
            self.t = Timer(self._interval, self._function, *self._args, **self._kwargs)
            self.t.start()

    def cancel(self):
        if self.t:
            self.t.cancel()
        self._enable = False

