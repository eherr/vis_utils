#!/usr/bin/env python
#
# Copyright 2019 DFKI GmbH.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the
# following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
import collections
import time
from threading import Lock


class Task(object):
    """ task to be executed repeatedly """
    def __init__(self, name, func, data):
        self.name = name
        self.func = func
        self.data = data
        self.active = False
        self.interval = None
        self.call_once = False
        self.last_tick = time.time()

    def start(self):
        self.active = True

    def update(self, dt):
        self.func(dt, self.data)

    def stop(self):
        self.active = False


class FuncCallTask(object):
    """ task to be executed once """
    def __init__(self, name, func, params, scene, task_manager):
        self.name = name
        self.func = func
        self.params = params
        self.active = False
        self.interval = None
        self.call_once = True
        self.last_tick = time.time()
        self.scene = scene
        self.task_manager = task_manager

    def start(self):
        self.active = True

    def update(self, dt):
        print("call method", self.name, *self.params)
        self.func(*self.params)
        #self.task_manager.remove(self.name)
        if self.name in self.task_manager.tasks:
            del self.task_manager.tasks[self.name]

    def stop(self):
        self.active = False



class TaskManager(object):
    def __init__(self):
        self.tasks = collections.OrderedDict()
        self.last_tick = time.time()
        self.mutex = Lock()

    def update(self, dt):
        self.mutex.acquire()
        tick = time.time()
        func_keys = list(self.tasks.keys())
        for key in func_keys:
            delta = tick - self.tasks[key].last_tick
            if self.tasks[key].call_once:
                self.tasks[key].update(dt)
            elif self.tasks[key].interval is None or delta > self.tasks[key].interval:
                self.tasks[key].update(dt)
                self.tasks[key].last_tick = tick
        self.mutex.release()

    def add(self, key, task):
        self.mutex.acquire()
        self.tasks[key] = task
        self.mutex.release()

    def stop(self, key):
        self.mutex.acquire()
        if key in self.tasks:
            self.tasks[key].stop()
        self.mutex.release()

    def start(self, key):
        self.mutex.acquire()
        if key in self.tasks:
            self.tasks[key].start()
        self.mutex.release()

    def remove(self, key):
        self.mutex.acquire()
        if key in self.tasks:
            del self.tasks[key]
        self.mutex.release()
