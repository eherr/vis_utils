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
import numpy as np
import time
import math
import queue
import threading
from . import constants
try:
    import physics_utils
except:
    physics_utils = None
if constants.activate_simulation and physics_utils is not None:
    from physics_utils.sim import SimWorld

from .scene.editor_scene import EditorScene
DEFAULT_CLEAR_COLOR = [0,0,0]

DEFAULT_SIM_DT = 1/200
DEFAULT_FPS = 60


class AppBase:
    def __init__(self, **kwargs):
        self.maxfps=kwargs.get("maxfps",None)
        if self.maxfps is None:
            self.maxfps=kwargs.get("max_fps",None)
        if self.maxfps is None:
            self.maxfps=kwargs.get("fps",DEFAULT_FPS)
        self.sim_dt=kwargs.get("sim_dt",DEFAULT_SIM_DT)
        self.sim_settings=kwargs.get("sim_settings",None)
        sync_sim=kwargs.get("sync_sim",True)
        self.activate_simulation=kwargs.get("activate_simulation",constants.activate_simulation)
        self.visualize = kwargs.get("visualize",True)
        self.interval = 1.0/self.maxfps
        self.fixed_dt = False
        self.event_queue = queue.Queue()
        self.mutex = threading.Lock()
        self.synchronize_updates = kwargs.get("synchronize_updates",True)
        up_axis=kwargs.get("up_axis",1)
        self.scene = EditorScene(self.visualize, up_axis=up_axis)
        if self.activate_simulation and physics_utils is not None:
            self.init_simulation()
        self.keyboard_handler = dict()
        self.last_time = time.perf_counter()
        self.next_time = self.last_time+self.interval
        self.scene.global_vars["fps"] = self.maxfps
        self.is_running = False
        self.synchronize_simulation = sync_sim and self.activate_simulation

    def init_simulation(self):
        if self.sim_settings is None:
            self.sim_settings = dict()
        self.sim_settings["auto_disable"] = False
        if "engine" not in self.sim_settings:
            self.sim_settings["engine"] = "ode"
        self.sim_settings["add_ground"] = True
        #erp = 0.8#1.0#0.5#0.8# 0.1- 0.8
        #cfm = 1e-5 #1e-10##1e-2 # 1e-9 - 1  # 0 means enfore, 1 means ignore
        #self.sim_settings["error_correction"] = 0.2
        #self.sim_settings["constraint_force_mixing"] = 1e-5
        #self.sim_settings["surface_layer_depth"] = 0.0# 0.01
        #self.sim_settings["ground_penalty"] = 0.0 # 0.8
        #self.sim_settings["gravity"] = 0.0 # 0.8
        self.scene.sim = SimWorld(**self.sim_settings)
        self.activate_simulation = True
        
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
            #if self.fixed_dt:
            #    dt = self.interval
        self.last_time = t
        fps= 1.0/dt
        if self.synchronize_updates:
            self.update_scene(dt)
        if self.visualize:
            self.render(dt)
        self.next_time = self.last_time + self.interval
        self.scene.global_vars["fps"] = fps

    def update_scene(self, dt):
        self.mutex.acquire()
        self.scene.before_update(dt)
        if self.synchronize_simulation:
            # from locotest
            sim_seconds = dt
            n_steps = int(math.ceil(sim_seconds / self.sim_dt))
            for i in range(0, n_steps):
                self.scene.sim_update(self.sim_dt)
                #self.scene.global_vars["step"] += 1
        self.scene.update(dt)
        self.scene.after_update(dt)
        self.mutex.release()

    def step_sim(self, n_steps=1):
        step_idx = 0
        while step_idx < n_steps:
            self.scene.sim_update(self.sim_dt)
            step_idx += 1
            #self.scene.global_vars["step"] += 1

    def get_sim_steps_per_update(self):
        if self.interval > self.sim_dt:
            return np.floor(self.interval/self.sim_dt)
        else:
            return 1

    def render(self, dt):
        return
