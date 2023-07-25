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
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from .scene.editor_scene import EditorScene
from .graphics.graphics_context import GraphicsContext
from .app_base import AppBase, DEFAULT_CLEAR_COLOR, DEFAULT_SIM_DT, DEFAULT_FPS

try:
    import physics_utils
except:
    physics_utils = None



LEFT_MOUSE_BUTTON = 0
MOUSE_BUTTON_STATE_DOWN = 0
MOUSE_BUTTON_STATE_UP = 1


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
        self.camera.moveVertically(delta[1] * self.translation_scale)

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

    def move_to(self, pos):
        return


class GLUTApp(AppBase):
    def __init__(self, width, height, title="GLUTApp", **kwargs):
        self.width = width
        self.height = height
        self.aspect = float(width) / float(height)
        self.init_graphics_context(width, height, title, **kwargs)
        kwargs["visualize"] = True
        AppBase.__init__(self, **kwargs)
        self.use_frame_buffer=kwargs.get("use_frame_buffer",True)
        self.last_click_position = np.zeros(3)
        self.reshape(width, height)
        self.is_running = False
        self.enable_object_selection = False

    def init_graphics_context(self, width, height, title, **kwargs):
        glutInit(sys.argv)
        # needed for the console which uses font functions of pygame
        pygame.init()
        # Create a double-buffer RGBA window. 
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

        glutInitWindowSize(width, height)
        glutCreateWindow(str.encode(title))
        glutReshapeFunc(self.reshape)
        glutDisplayFunc(self.update)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        self.graphics_context = GraphicsContext(width, height, **kwargs)
        self.graphics_context.show_console = True
        camera_pose=kwargs.get("camera_pose",None)
        self.camera_controller = CameraController(self.graphics_context.camera, camera_pose)
       
        glutKeyboardFunc(self.keyboard)
        glutMouseFunc(self.mouse_click)
        glutMotionFunc(self.mouse_motion)
        glutPassiveMotionFunc(self.passive_mouse_motion)
        glutMouseWheelFunc(self.mouse_wheel)


    def render(self, dt):
        self.graphics_context.update(dt)
        self.graphics_context.render(self.scene)

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


    def save_screenshot(self, filename):
        self.graphics_context.save_screenshot(filename)

    def get_screenshot(self):
        return self.graphics_context.get_screenshot()

    def set_console_lines(self, lines):
        self.graphics_context.console.set_lines(lines)

    def mouse_click(self, button, state, x, y):
        self.camera_controller.mouse(button, state, x, y)
        io = self.graphics_context.io
        io.mouse_down[button] = 1-state
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
   
        self.graphics_context.io.mouse_pos = (x,y)

    def passive_mouse_motion(self, x, y):
        self.graphics_context.io.mouse_pos = (x,y)

    def mouse_wheel(self, wheel, direction, x, y):
        self.camera_controller.mouse_wheel(wheel, direction, x, y)
