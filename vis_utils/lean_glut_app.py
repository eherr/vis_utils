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
import pygame
import threading
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import imgui
from .scene.editor_scene import EditorScene
from .graphics.camera3d import OrbitingCamera
from .graphics.shaders import ShaderManager
from .graphics.geometry.primitive_manager import PrimitiveManager
from .graphics.console import IMGUIConsole
from .graphics.renderer.main_renderer import MainRenderer
from .graphics.plot_manager import PlotManager
from .glut_app import DEFAULT_CLEAR_COLOR, CameraController
from . import constants
if constants.activate_simulation:
    from physics_utils.sim import SimWorld

class LeanGLUTApp(object):
    def __init__(self, width, height, title="GLUTApp", console_scale=0.5, camera_pose=None,
                 maxfps=60, sim_settings=None, sync_sim=True,clear_color=DEFAULT_CLEAR_COLOR):
        self.maxfps = maxfps
        self.interval = 1.0/self.maxfps
        self.width = width
        self.height = height
        self.aspect = float(width) / float(height)
        glutInit(sys.argv)

        pygame.init()
        # Create a double-buffer RGBA window
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
        glutInitWindowSize(width, height)

        glutCreateWindow(str.encode(title))
        glutReshapeFunc(self.reshape)
        glutDisplayFunc(self.update)
        glutKeyboardFunc(self.keyboard)
        glutMouseFunc(self.mouse)
        glutMotionFunc(self.mouse_motion)
        glutPassiveMotionFunc(self.passive_mouse_motion)
        glutMouseWheelFunc(self.mouse_wheel)
        glutKeyboardFunc(self.keyboard)
        self.shader_manager = ShaderManager()
        self.shader_manager.initShaderMap()
        self.primitive_manager = PrimitiveManager()
        self.console = IMGUIConsole([0, 0], scale=console_scale)
        self.show_console = True
        if sim_settings is None:
            sim_settings = dict()
        self.sim_settings = sim_settings
        sim = None
        if constants.activate_simulation:
            self.sim_settings["auto_disable"] = False
            self.sim_settings["engine"] = "ode"
            self.sim_settings["add_ground"] = True
            sim = SimWorld(**self.sim_settings)
        self.scene = EditorScene(True, sim=sim)
        self.main_renderer = MainRenderer()
        self.camera = OrbitingCamera()
        self.camera_controller = CameraController(self.camera, camera_pose)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        self.keyboard_handler = dict()
        self.last_time = time.perf_counter()
        self.next_time = self.last_time+self.interval
        self.scene.global_vars["step"] = 0
        self.scene.global_vars["fps"] = self.maxfps
        self.synchronize_simulation = sync_sim
        self.last_click_position = np.zeros(3)
        self.mutex = threading.Lock()
        self.synchronize_updates = True
        self.plot_manager = PlotManager(self.width, self.height)
        self.draw_plot = True
        self.fixed_dt = True
        self.clear_color = clear_color
        imgui.create_context()
        self.imgui_renderer = ProgrammablePipelineRenderer()
        self.io = imgui.get_io()
        self.io.display_size = width, height
        self.reshape(width, height)

    def update(self):
        t = time.perf_counter()
        while t < self.next_time:
            st = self.next_time - t
            time.sleep(st)
            t = time.perf_counter()
        dt = t- self.last_time
        self.last_time = t
        fps= 1.0/dt
        if self.synchronize_updates:
            self.update_scene(dt)
        self.camera.update(dt)
        self.render()
        self.next_time = self.last_time + self.interval
        self.scene.global_vars["fps"] = fps

    def update_scene(self, dt):
        self.mutex.acquire()
        self.scene.before_update(dt)
        self.scene.update(dt)
        self.scene.after_update(dt)
        self.mutex.release()

    def render(self):
        glViewport(0, 0, self.width, self.height)
        glClearColor(self.clear_color[0],self.clear_color[1],self.clear_color[2], 255)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        self.console.reset()
        self.scene.draw(self.camera.get_view_matrix(), self.camera.get_projection_matrix())
        self.main_renderer.use_shadow = False

        p_m = self.camera.get_projection_matrix()
        v_m = self.camera.get_view_matrix()
        object_list = self.scene.get_visible_objects(self.camera)
        light_sources = self.scene.lightSources
        self.main_renderer.render_scene(object_list, p_m, v_m, light_sources)
        self.draw_ui()
        glutSwapBuffers()
        glutPostRedisplay()

    def reshape(self, w, h):
        self.width = w
        self.height = max(h,1)
        self.io.display_size = (w, h)
        glViewport(0, 0, self.width, self.height)
        self.aspect = float(self.width) / float(self.height)
        self.camera.set_projection_matrix(45.0, self.aspect, 0.1, 100000.0)
        self.camera.set_orthographic_matrix(0, self.width, self.height, 0, -100.0, 1000.0)
        if self.draw_plot:
            self.plot_manager.resize(w, h)

    def run(self):
        # Run the GLUT main loop until the user closes the window.
        print("run")
        glutMainLoop()

    def keyboard(self, key, x, y):
        for t in self.keyboard_handler.values():
            handler, params = t
            handler(key, params)

    def mouse(self, button, state, x,y):
        self.camera_controller.last_pos = np.array([x,y])
        self.camera_controller.mode = button
        self.last_click_position = self.get_position_from_click(x,y)
        io = self.io
        io.mouse_down[button] = 1-state

    def get_position_from_click(self, x, y):
        viewport = glGetIntegerv(GL_VIEWPORT)
        wx = x
        wy = self.height - y
        wz = glReadPixels(wx, wy, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)[0]
        view = np.array(self.camera.get_view_matrix(), dtype=np.float)
        proj = np.array(self.camera.get_projection_matrix(), dtype=np.float)
        p = gluUnProject(wx, wy, wz, view, proj, viewport)
        return np.array(p)

    def mouse_motion(self,  x,y):
        delta = [x,y] - self.camera_controller.last_pos
        self.camera_controller.last_pos = np.array([x,y])
        if self.camera_controller.mode == GLUT_RIGHT_BUTTON:
            self.camera_controller.rotate(delta)
        elif self.camera_controller.mode == GLUT_MIDDLE_BUTTON:
            self.camera_controller.move(delta)
        self.io.mouse_pos = (x,y)

    def passive_mouse_motion(self, x, y):
        self.io.mouse_pos = (x,y)
    
    def mouse_wheel(self,  wheel, direction, x, y):
        self.camera_controller.zoom(direction)

    def set_camera_target(self, scene_object):
        self.camera.setTarget(scene_object)
    
    def set_console_lines(self, lines):
        self.console.set_lines(lines)

    def draw_ui(self):
        io = self.io
        # start new frame context
        imgui.new_frame()
        #imgui.begin("Console", True)
        #imgui.text("Hello world!")
        #imgui.end()
        if self.draw_plot:
            #self.plot_manager.draw(self.camera.get_orthographic_matrix())
            self.plot_manager.render_imgui()
        if self.show_console:
            self.console.render_lines()

        imgui.render()
        data = imgui.get_draw_data()
        self.imgui_renderer.render(data)
        imgui.end_frame()

