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
from OpenGL.GL import *
from OpenGL.GLU import gluUnProject
import imgui
import pygame
from imgui.integrations.opengl import ProgrammablePipelineRenderer
from ..graphics.geometry.primitive_manager import PrimitiveManager
from ..graphics.shaders import ShaderManager
from ..scene.legacy import CoordinateSystemObject
from ..graphics.sceen_frame_buffer import ScreenFramebuffer
from ..graphics.multi_resolution_sceen_frame_buffer import MultiResolutionScreenFramebuffer
from ..graphics.renderer.color_picking_renderer import ColorPickingRenderer
from ..graphics.renderer.main_renderer import MainRenderer
from ..graphics.renderer.shadow_map_renderer import ShadowMapRenderer
from ..graphics.renderer.selection_renderer import SelectionRenderer
from ..graphics.selection_frame_buffer import SelectionFrameBuffer
from ..graphics.plot_manager import PlotManager
from ..graphics.camera3d import OrbitingCamera
from ..graphics.console import IMGUIConsole
from ..graphics.renderer.label_renderer import LabelRenderer

DEFAULT_SKY_COLOR = [0,0,0]
ROTATION_SPEED = 15

def getIfromRGB(rgb):
    red = int(rgb[0]*255)
    green = int(rgb[1]*255)
    blue = int(rgb[2]*255)
    #print red, green, blue
    RGBint = (red<<16) + (green<<8) + blue
    return RGBint


class GraphicsContext(object):
    def __init__(self,  w, h, **kwargs):
        self.width = w
        self.height = h
        imgui.create_context()
        self.imgui_renderer = ProgrammablePipelineRenderer()
        self.io = imgui.get_io()
        self.io.display_size = (w, h)
        self.sky_color = kwargs.get("sky_color", DEFAULT_SKY_COLOR)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        #https://learnopengl.com/Advanced-OpenGL/Blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(1.5)
        ShaderManager().initShaderMap()  # opengl needs to initialize before an object of this class is initialized
        PrimitiveManager().init()
        self.use_shadows =  kwargs.get("use_shadows", True)
        self.use_frame_buffer = kwargs.get("use_frame_buffer", True)
        if self.use_frame_buffer:
            self.frame_buffer = MultiResolutionScreenFramebuffer(w,h, 4)
            #self.frame_buffer = ScreenFramebuffer(800, 600)
            self.color_buffer = ScreenFramebuffer(w,h)
            self.selection_buffer = SelectionFrameBuffer(w, h)

            self.color_picking_renderer = ColorPickingRenderer()
            self.selection_renderer = SelectionRenderer()
        if self.use_shadows:
            self.shadow_renderer = ShadowMapRenderer()
        
        self.main_renderer = MainRenderer(sky_color=self.sky_color)

        self.show_shadow_map = False

        self.cs = CoordinateSystemObject(0.1)
        self.camera = OrbitingCamera()
        self.draw_labels = kwargs.get("draw_labels", False)
        self.activate_plots =  kwargs.get("activate_plots", True)
        if self.activate_plots:
            self.plot_manager = PlotManager(self.width, self.height)
        else:
            self.plot_manager = None
        self.console = IMGUIConsole([0, 0], alpha=20)
        self.label_renderer = LabelRenderer()
        self.show_console = False

        print("init opengl")


    def update(self, dt):
        self.camera.update(dt)

    def resize(self, w, h):
        if h <= 0 or w <= 0:
            return
        print("resize", w, h)
        self.width = w
        self.height = h
        self.io.display_size = (w, h)
        glViewport(0, 0, w, h)
        self.aspect = float(w)/float(h)
        self.camera.set_projection_matrix(45.0, self.aspect, 0.1, 10000.0)
        self.camera.set_orthographic_matrix(0, self.width, self.height, 0, -100.0, 1000.0)
        if self.use_frame_buffer:
            self.frame_buffer.resize(w, h)
            self.color_buffer.resize(w, h)
            self.selection_buffer.resize(w, h)
            if self.activate_plots:
                self.plot_manager.resize(w, h)

    def render(self, scene, draw_debug=True):
        """ draw scene using renderers
        (note before calling this function the context of the view has to be set as current using makeCurrent() 
        and afterwards the doubble buffer has to swapped to display the current frame swapBuffers())
        """

        if scene is None:
            print("scene is None")
            return

        p_m = self.camera.get_projection_matrix()
        v_m = self.camera.get_view_matrix()
        o_m = self.camera.get_orthographic_matrix()


        object_list = scene.get_visible_objects(self.camera)
        light_sources = scene.lightSources

        if self.use_shadows and self.show_shadow_map:
            self.shadow_renderer.render_scene(object_list,  self.camera, light_sources)
            glViewport(0, 0, self.width, self.height)
            scene.lightSources[0].shadow_buffer.draw_buffer_to_screen()
        else:
            
            if self.use_shadows:
                self.shadow_renderer.render_scene(object_list, self.camera, light_sources)
                glViewport(0, 0, self.width, self.height)
            
            if self.use_frame_buffer:
                self.selection_buffer.prepare_buffer()
                self.selection_renderer.render_scene(scene, self.camera)
                self.frame_buffer.prepare_buffer()#
            glClearColor(self.sky_color[0]*255, self.sky_color[1]*255, self.sky_color[1]*255, 255)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
           
            self.main_renderer.render_scene(object_list, p_m, v_m, light_sources)
            #draw local coordinate system of orbiting camera
            self.cs.draw(self.camera.get_pivot_matrix(), p_m, light_sources)
            self.render_legacy(scene, v_m, p_m, draw_debug)

            if self.use_frame_buffer:
                self.frame_buffer.bind()
                self.selection_buffer.draw_buffer_to_screen()
                self.render_edit_widget(scene.scene_edit_widget, v_m, p_m, light_sources)
                #if self.draw_plot:
                #    self.plot_manager.draw(self.camera.get_orthographic_matrix())
                if self.draw_labels:
                    self.label_renderer.render_scene(object_list, v_m, p_m, o_m, self)

                self.color_buffer.prepare_buffer()
                self.color_picking_renderer.render_scene(object_list,  p_m, v_m, scene.scene_edit_widget)
                self.frame_buffer.draw_buffer_to_screen()
            self.draw_imgui()

    def render_edit_widget(self, edit_widget, v_m, p_m, light_sources):
        if edit_widget.visible:
            self.main_renderer.prepare(v_m, p_m, light_sources)
            for key in edit_widget.meshes:
                geometry = edit_widget.meshes[key]
                if key == edit_widget.active_axis:
                    mat = edit_widget.selection_material
                else:
                    mat = geometry.material
                self.main_renderer.render(edit_widget.transform, geometry, mat)
            glUseProgram(0)

    def render_legacy(self, scene, v_m, p_m, draw_debug):
        scene.draw(v_m, p_m)
        if draw_debug:
            scene.drawDebugVisualization(v_m, p_m)
   
    def get_id_from_color_buffer(self, x,y):
        """https://www.opengl.org/discussion_boards/showthread.php/178310-glReadPixels
         https://www.khronos.org/opengl/wiki/Common_Mistakes#Texture_upload_and_pixel_reads"""
        wx = x
        wy = self.height - y
        self.color_buffer.bind()
        color = glReadPixels(wx, wy, 1, 1, GL_RGBA, GL_FLOAT)[0][0]
        self.color_buffer.unbind()
        object_id = getIfromRGB(color)
        return object_id

    def get_position_from_click(self, x, y):
        """https://stackoverflow.com/questions/8739311/opengl-select-sphere-with-mouse?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
           https://learnopengl.com/Advanced-OpenGL/Framebuffers
        """
        viewport = glGetIntegerv(GL_VIEWPORT)
        wx = x
        wy = self.height - y
        if self.use_frame_buffer:
            self.frame_buffer.bind_intermediate()
        #self.frame_buffer.bind()

        wz = glReadPixels(wx, wy, 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)[0]
        if self.use_frame_buffer:
            self.frame_buffer.unbind()
        view = np.array(self.camera.get_view_matrix(), dtype=np.double)
        proj = np.array(self.camera.get_projection_matrix(), dtype=np.double)
        p = gluUnProject(wx, wy, wz, view, proj, viewport)
        return p

    def get_ray_from_click(self, x, y):
        """ copied from http://antongerdelan.net/opengl/raycasting.html and translated into Python
            returns origin and direction of the ray
        """
        # use camera position as origin of the ray
        ray_start = self.camera.get_world_position()

        # transform window X and Y into normalized device coordinates range [-1:1]
        width = self.width
        height = self.height
        ndc_X = ((2.0*x)/width)-1.0
        ndc_Y = 1.0 - ((2.0*y)/height)

        # convert to clipping coordinates range [-1:1, -1:1, -1:1, -1:1]
        cc = [0,0,0,0]
        cc[0] = ndc_X
        cc[1] = ndc_Y
        cc[2] = -1.0  # let ray point forward in negative -z direction
        cc[3] = 1.0

        # unproject x y part of clipping coordinates
        ray_eye = np.dot(self.camera.get_inv_projection_matrix().T, cc)
        ray_eye[2] = -1.0
        ray_eye[3] = 0.0

        # get world coordinates
        ray_world = np.dot(self.camera.get_inv_view_matrix().T, ray_eye)
        ray_world /= np.linalg.norm(ray_world)
        return np.array([ray_start[0], ray_start[1], ray_start[2], 0]), ray_world

    def rotate_left(self):
        self.camera.updateRotationMatrix(self.camera.pitch, self.camera.yaw + ROTATION_SPEED)

    def rotate_right(self):
        self.camera.updateRotationMatrix(self.camera.pitch, self.camera.yaw - ROTATION_SPEED)

    def rotate_up(self):
        self.camera.updateRotationMatrix(self.camera.pitch + ROTATION_SPEED, self.camera.yaw)

    def rotate_down(self):
        self.camera.updateRotationMatrix(self.camera.pitch - ROTATION_SPEED, self.camera.yaw)

    def move_horizontally(self, v):
        self.camera.moveHorizontally(v)

    def move_forward(self, v):
        self.camera.moveForward(v)

    def reset_camera(self):
        self.camera.reset()

    def draw_imgui(self):
        io = self.io
        # start new frame context
        imgui.new_frame()
        if self.activate_plots:
            self.plot_manager.render_imgui()
        if self.show_console:
            self.console.render_lines()

        imgui.render()
        data = imgui.get_draw_data()
        self.imgui_renderer.render(data)
        imgui.end_frame()

