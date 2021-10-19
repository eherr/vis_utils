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
import sys
import time
import math
import numpy as np
from .scene.scene import Scene
from . import constants
if constants.activate_simulation:
    from physics_utils.sim import SimWorld

DEFAULT_SIM_DT = 1/200
DEFAULT_FPS = 60


class ConsoleApp(object):
    def __init__(self,  fps=DEFAULT_FPS, sim_settings=None, sync_sim=True, sim_dt=DEFAULT_SIM_DT):
        self.maxfps = fps
        self.sim_dt = sim_dt
        self.interval = 1.0/self.maxfps
        if sim_settings is None:
            sim_settings = dict()
        self.sim_settings = sim_settings
        sim = None
        if constants.activate_simulation:
            self.sim_settings["auto_disable"] = False
            if "engine" not in self.sim_settings:
                self.sim_settings["engine"] = "ode"
            self.sim_settings["add_ground"] = True
            sim = SimWorld(**self.sim_settings)
        self.scene = Scene(False, sim=sim)
        self.keyboard_handler = dict()

        self.last_time = time.perf_counter()
        self.next_time = self.last_time+self.interval
        self.scene.global_vars["step"] = 0
        self.scene.global_vars["fps"] = self.maxfps
        self.synchronize_updates = True
        self.synchronize_simulation = sync_sim and self.scene.sim is not None
        self.is_running = False
        self.visualize = False
        self.fixed_dt = False

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

    def update_scene(self, dt):
        self.scene.before_update(dt)
        if self.synchronize_simulation:
            # from locotest
            sim_seconds = dt
            n_steps = int(math.ceil(sim_seconds / self.sim_dt))
            for i in range(0, n_steps):
                self.scene.sim_update(self.sim_dt)
                self.scene.global_vars["step"] += 1
        self.scene.update(dt)
        self.scene.after_update(dt)

    def run(self):
        print("run")
        self.is_running = True
        while self.is_running:
            self.update()

    def step_sim(self, n_steps=1):
        step_idx = 0
        while step_idx < n_steps:
            self.scene.sim_update(self.sim_dt)
            step_idx += 1
            self.scene.global_vars["step"] += 1

    def get_sim_steps_per_update(self):
        if self.interval > self.sim_dt:
            return np.floor(self.interval/self.sim_dt)
        else:
            return 1

