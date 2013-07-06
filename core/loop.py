import time

from util import rsutil


class Loop(object):
    def __init__(self, fps=25):
        self.callbacks = []
        self.delta = 1.0 / fps
        self.running = False

    def update(self):
        td = time.time() - self.time
        if td > self.delta:
            [callback(td) for callback in self.callbacks]
            rsutil.rdnd()
            self.time = time.time()

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def run(self):
        self.running = True
        self.time = time.time()
        while True:
            if not self.running:
                return

            self.update()

    def stop(self):
        self.running = False