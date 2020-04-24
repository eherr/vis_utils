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
from ..graphics.renderer.lines import CoordinateSystemRenderer
from ..graphics.renderer.color_picking_renderer import convert_id_to_color
from ..graphics.geometry.mesh import Mesh
from vis_utils.graphics import materials
import numpy as np

KEY_LEFT = 16777234
KEY_UP = 16777235
KEY_RIGHT = 16777236
KEY_DOWN = 16777237

class SceneEditWidget(object):
    WIDGET_ID_X = 2000000
    WIDGET_ID_Y = WIDGET_ID_X + 1
    WIDGET_ID_Z = WIDGET_ID_Y + 1
    def __init__(self, scale=10):
        radius = 0.05 * scale
        diameter = 2 * radius
        slices = 10
        stacks = 10
        length = 2*scale
        self.scene_object = None
        self.visible = False
        #self.visualization = CoordinateSystemRenderer(scale)
        self.axis_vectors = dict()
        self.axis_vectors[self.WIDGET_ID_X] = np.array([1,0,0])
        self.axis_vectors[self.WIDGET_ID_Y] = np.array([0,1,0])
        self.axis_vectors[self.WIDGET_ID_Z] = np.array([0,0,1])

        self.meshes = dict()
        self.meshes[self.WIDGET_ID_X] =  Mesh.build_capsule(slices, stacks, diameter,length, "x", materials.red, [scale,0,0])
        self.meshes[self.WIDGET_ID_Y] =  Mesh.build_capsule(slices, stacks, diameter,length, "y", materials.green, [0,scale,0])
        self.meshes[self.WIDGET_ID_Z] =  Mesh.build_capsule(slices, stacks, diameter,length, "z", materials.blue, [0,0,scale])
  
        self.colors = dict()
        for key in self.meshes:
            self.colors[key] = convert_id_to_color(key)
        self.transform = np.eye(4)
        self.active_axis = -1
        self.selection_material = materials.yellow
        self.original_position = np.array([0,0,0])
        self.axis_projection_offset = 0
        self.rotation = np.eye(3)
        self._move_callback = None

    def activate_axis(self, axis_id, ray=None):
        
        is_axis = axis_id in self.colors
        if is_axis:
            self.active_axis = axis_id
            self.original_position = self.scene_object.getPosition()
            if ray is not None:
                #store offset along axis
                self.axis_projection_offset = self.get_distance_along_axis(ray[0][:3], ray[1][:3], self.axis_vectors[axis_id])
            else:
                self.axis_projection_offset = 0
        return is_axis

    def deactivate_axis(self):
        self.active_axis = -1

    def get_active_axis(self):
        if self.active_axis in self.axis_vectors:
            return self.axis_vectors[self.active_axis]

    def activate(self, scene_object, show=True):
        self.scene_object = scene_object
        self.visible = show
        self.active_axis = -1

    def deactivate(self):
        self.scene_object = None
        self.visible = False
        self.active_axis = -1

    def update(self, dt):
        if not self.visible or self.scene_object is None:
            return
        self.transform[3, :3] = self.scene_object.getPosition()[:3]
        self.transform[:3,:3] = self.rotation

    def reset_rotation(self):
        self.rotation = np.eye(3)
        
    def draw(self, v, p, l):
        return

    def handle_keyboard_input(self, key):
        if self.scene_object is not None and self.visible:
            if key == KEY_LEFT:
                self.scene_object.translate([-1,0,0])
            elif key == KEY_RIGHT:
                self.scene_object.translate([1,0,0])
            elif key == KEY_UP:
                self.scene_object.translate([0,1,0])
            elif key == KEY_DOWN:
                self.scene_object.translate([0,-1,0])
    
    def get_distance_along_axis(self, cam_pos, cam_ray, axis):
        """ src: https://github.com/ddiakopoulos/tinygizmo/blob/master/tiny-gizmo.cpp
        """
        #create plane with object position and normal towards camera
        object_pos = self.scene_object.getPosition()
        plane_tangent = np.cross(axis, object_pos - cam_pos)
        plane_normal = np.cross(axis, plane_tangent)
        # Define the plane to contain the original position of the object
        plane_point = self.original_position
        # If an intersection exists between the ray and the plane, place the object at that point
        denom = np.dot(cam_ray, plane_normal)
        if denom != 0:
            t = np.dot(plane_point - cam_pos, plane_normal) / denom
            object_pos = cam_pos + cam_ray * t
            return np.dot(object_pos -self.original_position, axis)
        else:
            return 0

    def move(self, cam_pos, cam_ray):
        """ src: https://github.com/ddiakopoulos/tinygizmo/blob/master/tiny-gizmo.cpp
        """
        axis = self.get_active_axis()
        if axis is not None:
            t = self.get_distance_along_axis(cam_pos, cam_ray, axis)
            object_pos = self.original_position + axis * (t - self.axis_projection_offset)
            if self._move_callback is None:
                self.scene_object.setPosition(object_pos)
            else:
                self._move_callback(object_pos)
        
    def register_move_callback(self, callback):
        self._move_callback = callback
