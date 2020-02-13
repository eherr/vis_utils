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
"""based on
https://pypede.wordpress.com/2009/08/30/opengl-in-pygame-tutorial-part-1/
https://www.reddit.com/r/pygame/comments/5lhp28/how_do_i_get_mouse_wheel_events/
 """
import pygame
import math
from sys import exit
import time
from OpenGL.GL import *
from .scene.editor_scene import EditorScene
from .graphics.camera3d import OrbitingCamera
from .graphics.graphics_context import GraphicsContext
from .graphics.console import Console
from .graphics.plot_manager import PlotManager
from . import constants
if constants.activate_simulation:
    from physics_utils.sim import SimWorld
SIM_DELTA_TIME = 0.01
DEFAULT_FPS = 60


class CameraController(object):
    def __init__(self, camera, pose=None):
        self.camera = camera
        self.rotation_scale = 0.1
        self.translation_scale = 0.2
        self.zoom_step = 15.0
        if pose is None:
            self.camera.position = [0, -10, 0]
            self.camera.zoom = -150
            self.camera.updateRotationMatrix(45, -20)
        else:
            self.camera.position = pose["position"]
            self.camera.zoom = pose["zoom"]
            self.camera.updateRotationMatrix(*pose["angles"])


    def zoom(self, button):
        if button == 4:
            self.camera.zoom += self.zoom_step
        elif button == 5:
            self.camera.zoom -= self.zoom_step

    def mouse_move(self, state):
        delta = self.last_pos = pygame.mouse.get_rel()
        if state[2]:  # right
            pitch = self.camera.pitch + delta[1] * self.rotation_scale
            yaw = self.camera.yaw + delta[0] * self.rotation_scale
            self.camera.updateRotationMatrix(pitch, yaw)
        elif state[1]:  # middle
            self.camera.moveHorizontally(-delta[0] * self.translation_scale * 2)
            self.camera.position[1] -= delta[1] * self.translation_scale

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.zoom(event.button)
            elif event.type == pygame.MOUSEMOTION:
                state = pygame.mouse.get_pressed()
                self.mouse_move(state)
            else:
                pygame.event.post(event)


def step_control(key, scene):
    if key == pygame.K_RIGHT:
        scene.update(scene.sim_delta_time)
        scene.global_vars["step"] += 1

    elif key == pygame.K_LEFT:
        scene.update(scene.sim_delta_time)
        scene.global_vars["step"] += 1
    elif key == pygame.K_p:
        scene.sim.toggle_simulation()


class PyGameApp(object):
    def __init__(self, width, height, setup_scene=None, title="PyGameApp",
                 console_scale=0.5, camera_pose=None, draw_plot=False,
                 sim_settings=None, sim_delta_time=SIM_DELTA_TIME,
                 fps=DEFAULT_FPS):
        self.maxfps = fps
        self.interval = 1000.0 / self.maxfps

        #self.interval = 1 / self.maxfps
        self.width = width
        self.height = height
        self.aspect = float(width) / float(height)
        pygame.init()
        pygame.display.set_caption(title)
        self.surface = pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF, 16)

        
        self.graphics_context = GraphicsContext(width, height)
        self.console = Console([0, 0], scale=console_scale)
        self.plot_manager = PlotManager(self.width, self.height)
        sim = None
        if constants.activate_simulation:
            if sim_settings is None:
                sim_settings = dict()
            sim_settings["auto_disable"] = False
            sim_settings["engine"] = "ode"
            #self.sim_settings["engine"] = "bullet"
            sim_settings["add_ground"] = True
            sim = SimWorld(**sim_settings)
        self.scene = EditorScene(True, sim)
        self.scene._create_visual_reference_frame()
        self.scene.sim_delta_time = sim_delta_time
        if sim_settings is not None and "delta_time" in sim_settings:
            self.scene.sim_delta_time = sim_settings["delta_time"]

        #self.camera = OrbitingCamera()

        self.camera_controller = CameraController(self.graphics_context.camera, camera_pose)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        self.reshape()
        self.keyboard_handler = dict()
        self.mouse_move_handler = dict()
        self.mouse_click_handler = dict()
        self.mouse_move_handler["camera_mouse"] = (self.camera_controller.mouse_move, None)
        self.mouse_click_handler["camera_zoom"] = (self.camera_controller.zoom, None)
        self.draw_plot = draw_plot
        self.scene.global_vars["step"] = 0

        if setup_scene is not None:
            setup_scene(app=self)
        self.last_time = pygame.time.get_ticks()
        self.next_time = self.last_time+self.interval


    def reshape(self):
        glViewport(0, 0, self.width, self.height)
        self.graphics_context.resize(self.width, self.height)

    def update(self, dt):
        self.handle_events()
        #self.camera.update(dt)

        sim_dt = self.scene.sim_delta_time
        #from simbicon
        simulation_seconds = 1/self.maxfps
        n_steps = int(math.ceil(simulation_seconds / sim_dt))
        #print(n_steps, n_steps*sim_dt, dt)
        #n_steps = 1
        for i in range(n_steps):
            #self.scene.update(sim_dt)
            self.scene.task_manager.update(sim_dt)
            #self.scene.sim.update(sim_dt)
            #
            #self.camera_controller.update()
            self.scene.global_vars["step"] += 1
            #for scene_object in self.scene.get_visible_objects(self.camera):
            #    scene_object.update(sim_dt)
        self.graphics_context.update(dt)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                for t in self.keyboard_handler.values():
                    handler, params = t
                    handler(event.key, params)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for t in self.mouse_click_handler.values():
                    handler, params = t
                    handler(event.button)
            elif event.type == pygame.MOUSEMOTION:
                for t in self.mouse_move_handler.values():
                    handler, params = t
                    state = pygame.mouse.get_pressed()
                    handler(state)
            elif event.type == pygame.QUIT:
                exit()

    def update_steps(self, dt):
        self.handle_events()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        self.graphics_context.render(self.scene)
        pygame.display.flip()

    def run(self):
        while True:
            t = pygame.time.get_ticks()
            dt = t- self.last_time
            while t < self.next_time:
                st = self.next_time - t
                time.sleep(st/1000)
                t = pygame.time.get_ticks()
            dt = t - self.last_time
            self.last_time = t
            fps= 1000/dt
            dt /= 1000
            self.scene.global_vars["fps"] = fps
            self.update(dt)
            self.draw()
            self.next_time = self.last_time + self.interval
            print(fps)

    def run_steps(self):
        self.keyboard_handler["step_control"] = (step_control, self.scene)
        clock = pygame.time.Clock()
        while True:
            clock.tick(self.maxfps)
            self.update_steps(self.scene.sim_delta_time)
            self.draw()

    def set_camera_target(self, scene_object):
        self.graphics_context.camera.setTarget(scene_object)
