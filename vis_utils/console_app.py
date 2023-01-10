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
import time
from .scene.scene import Scene
from .app_base import AppBase, DEFAULT_SIM_DT, DEFAULT_FPS


class ConsoleApp(AppBase):
    def __init__(self, fps=DEFAULT_FPS, sim_settings=None, sync_sim=True, sim_dt=DEFAULT_SIM_DT):
        AppBase.__init__(self, maxfps=fps, sim_dt=sim_dt,sim_settings=sim_settings)
        sim = None
        if self.activate_simulation:
            sim = self.init_simulation()
        self.scene = Scene(False, sim=sim)
        self.keyboard_handler = dict()

        self.last_time = time.perf_counter()
        self.next_time = self.last_time+self.interval
        self.scene.global_vars["step"] = 0
        self.scene.global_vars["fps"] = self.maxfps
        self.synchronize_simulation = sync_sim and self.scene.sim is not None
        self.is_running = False
        self.visualize = False

    def update(self):
        t = time.perf_counter()
        if self.fixed_dt:
            dt = self.interval
        else:
            while t < self.next_time:
                st = self.next_time - t
                time.sleep(st)
                t = time.perf_counter()
            dt = t - self.last_time
        self.last_time = t
        fps= 1.0/dt
        if self.synchronize_updates:
            self.update_scene(dt)
        self.next_time = self.last_time + self.interval
        self.scene.global_vars["fps"] = fps

    def run(self):
        print("run")
        self.is_running = True
        while self.is_running:
            self.update()



