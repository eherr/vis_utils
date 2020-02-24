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
import numpy as np
import time
import pygame
import math
import threading
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from .scene.editor_scene import EditorScene
from .graphics.graphics_context import GraphicsContext
from .graphics.console import Console
from . import constants
if constants.activate_simulation:
    from physics_utils.sim import SimWorld


class CameraController(object):
    def __init__(self, camera, pose=None):
        self.camera = camera
        self.rotation_scale = 0.1
        self.translation_scale = 1
        self.zoom_step = 5.0
        self.last_pos = np.array([0,0])
        self.mode = None
        if pose is None:
            self.camera.position = [0, -10, 0]
            self.camera.zoom = -150
            self.camera.updateRotationMatrix(45, -20)
        else:
            self.camera.position = pose["position"]
            self.camera.zoom = pose["zoom"]
            self.camera.updateRotationMatrix(*pose["angles"])

    def zoom(self, direction):
        self.camera.zoom += self.zoom_step * direction

    def rotate(self, delta):
        pitch = self.camera.pitch + delta[1] * self.rotation_scale
        yaw = self.camera.yaw + delta[0] * self.rotation_scale
        self.camera.updateRotationMatrix(pitch, yaw)

    def move(self, delta):
        self.camera.moveHorizontally(-delta[0] * self.translation_scale * 2)
        self.camera.position[1] -= delta[1] * self.translation_scale

    def mouse_motion(self, x, y):
        delta = [x, y] - self.last_pos
        self.last_pos = np.array([x, y])
        if self.mode == GLUT_RIGHT_BUTTON:
            self.rotate(delta)
        elif self.mode == GLUT_MIDDLE_BUTTON:
            self.move(delta)

    def mouse(self, button, state, x, y):
        self.last_pos = np.array([x, y])
        self.mode = button


    def mouse_wheel(self, wheel, direction, x, y):
        self.zoom(direction)


DEFAULT_CLEAR_COLOR = [0,0,0]
LEFT_MOUSE_BUTTON = 0
MOUSE_BUTTON_STATE_DOWN = 0
MOUSE_BUTTON_STATE_UP = 1


class GLUTApp(object):
    def __init__(self, width, height, title="GLUTApp", console_scale=0.5, camera_pose=None, maxfps=60, sim_settings=None,
                 sync_sim=True, use_shadows=True, use_frame_buffer=True, clear_color=DEFAULT_CLEAR_COLOR, sim_dt=1.0/200):
        self.maxfps = maxfps
        self.sim_dt = sim_dt
        self.interval = 1.0/self.maxfps
        self.width = width
        self.height = height
        self.aspect = float(width) / float(height)
        glutInit(sys.argv)

        # needed for the console which uses font functions of pygame
        pygame.init()
        # Create a double-buffer RGBA window. 
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

        glutInitWindowSize(width, height)
        glutCreateWindow(str.encode(title))

        #wglSwapIntervalEXT(0) disable vsync

        glutReshapeFunc(self.reshape)
        glutDisplayFunc(self.update)
        glutKeyboardFunc(self.keyboard)
        glutKeyboardFunc(self.keyboard)

        if sim_settings is None:
            sim_settings = dict()
        self.sim_settings = sim_settings
        self.graphics_context = GraphicsContext(width, height)
        self.console = Console([0, 0], scale=console_scale)

        sim = None
        if constants.activate_simulation:
            self.sim_settings["auto_disable"] = False
            self.sim_settings["engine"] = "ode"
            self.sim_settings["add_ground"] = True
            sim = SimWorld(**self.sim_settings)
        self.scene = EditorScene(True, sim=sim)

        self.camera_controller = CameraController(self.graphics_context.camera, camera_pose)

        glutMouseFunc(self.mouse_click)
        glutMotionFunc(self.mouse_motion)
        glutMouseWheelFunc(self.mouse_wheel)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        self.keyboard_handler = dict()
        self.last_time = time.perf_counter()
        self.next_time = self.last_time+self.interval
        self.scene.global_vars["step"] = 0
        self.scene.global_vars["fps"] = self.maxfps
        self.synchronize_simulation = sync_sim and self.scene.sim is not None
        self.last_click_position = np.zeros(3)
        self.mutex = threading.Lock()
        self.synchronize_updates = True
        self.enable_object_selection = False
        self.clear_color = clear_color
        self.use_shadows = use_shadows
        self.use_frame_buffer = use_frame_buffer
        self.reshape(width, height)

    def update(self):
        t = time.perf_counter()
        while t < self.next_time:
            st = self.next_time - t
            time.sleep(st)
            t = time.perf_counter()

        dt = t - self.last_time
        self.last_time = t
        fps= 1.0/dt
        if self.synchronize_updates:
            self.update_scene(dt)
        self.graphics_context.update(dt)
        self.render()
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
                self.scene.global_vars["step"] += 1
        self.scene.update(dt)
        self.scene.after_update(dt)
        self.mutex.release()

    def render(self):
        self.graphics_context.render(self.scene)
        self.console.draw_lines(self.graphics_context.camera.get_orthographic_matrix())
        glutSwapBuffers()
        glutPostRedisplay()

    def reshape(self, w, h):
        self.width = w
        self.height = max(h,1)
        glViewport(0, 0, self.width, self.height)
        self.graphics_context.resize(w, h)

    def run(self):
        # Run the GLUT main loop until the user closes the window.
        print("run")
        glutMainLoop()

    def keyboard(self, key, x, y):
        for t in self.keyboard_handler.values():
            handler, params = t
            handler(key, params)

    def get_position_from_click(self, x, y):
        return self.graphics_context.get_position_from_click(x,y)

    def get_camera(self):
        return self.graphics_context.camera

    def set_camera_target(self, scene_object):
        self.graphics_context.camera.setTarget(scene_object)

    def step_sim(self, n_steps=1):
        step_idx = 0
        while step_idx < n_steps:
            self.scene.sim_update(self.sim_dt)
            step_idx += 1
            self.scene.global_vars["step"] += 1

    def save_screenshot(self, filename="framebuffer.png"):
        self.graphics_context.frame_buffer.save_to_file(filename)

    def get_screenshot(self):
        return self.graphics_context.frame_buffer.to_image()

    def set_console_lines(self, lines):
        self.console.set_lines(lines)

    def mouse_click(self, button, state, x, y):
        self.camera_controller.mouse(button, state, x, y)
        if not self.enable_object_selection:
            return
        if button == LEFT_MOUSE_BUTTON:
            if state == MOUSE_BUTTON_STATE_DOWN:
                ray_start, ray_dir = self.graphics_context.get_ray_from_click(x, y)
                node_id = -1
                if self.use_frame_buffer:
                    node_id = self.graphics_context.get_id_from_color_buffer(x,y)
                if node_id <= 0:
                    node_id = -1
                self.scene.select_object(node_id, (ray_start, ray_dir))
            elif state == MOUSE_BUTTON_STATE_UP:
                self.scene.deactivate_axis()

    def mouse_motion(self, x, y):
        self.camera_controller.mouse_motion(x, y)
        if self.enable_object_selection:
            cam_pos, cam_ray = self.graphics_context.get_ray_from_click(x, y)
            self.scene.handle_mouse_movement(cam_pos[:3], cam_ray[:3])

    def mouse_wheel(self, wheel, direction, x, y):
        self.camera_controller.mouse_wheel(wheel, direction, x, y)
