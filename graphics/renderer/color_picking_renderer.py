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
from ..shaders.shader_manager import ShaderManager
from OpenGL.GL import *

#https://stackoverflow.com/questions/33124347/convert-integers-to-rgb-values-and-back-with-python?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
def getRGBfromI(RGBint):
    blue =  RGBint & 255
    green = (RGBint >> 8) & 255
    red =   (RGBint >> 16) & 255
    return red, green, blue

def getIfromRGB(rgb):
    red = rgb[0]
    green = rgb[1]
    blue = rgb[2]
    #print red, green, blue
    RGBint = (red<<16) + (green<<8) + blue
    return RGBint

def convert_id_to_color(id):
    r, g, b = getRGBfromI(id)
    return [r,g,b,255]


class ColorPickingRenderer(object):
    def __init__(self):
        self.shader = ShaderManager().getShader("color_picking")
        self.viewMatrix_loc = glGetUniformLocation(self.shader, "viewMatrix")
        self.projectionMatrix_loc = glGetUniformLocation(self.shader, "projectionMatrix")
        self.modelMatrix_loc = glGetUniformLocation(self.shader, "modelMatrix")
        self.useSkinning_loc = glGetUniformLocation(self.shader, "useSkinning")
        self.bones_loc = glGetUniformLocation(self.shader, "bones")
        self.boneCount_loc = glGetUniformLocation(self.shader, "boneCount")
        self.color_loc = glGetUniformLocation(self.shader, "pickColor")
        self.position_loc = glGetAttribLocation(self.shader, "position")
        self.boneIDs_loc = glGetAttribLocation(self.shader, "boneIDs")
        self.weights_loc = glGetAttribLocation(self.shader, "weights")

    def prepare(self, view_matrix, projection_matrix):
        glUseProgram(self.shader)
        glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, view_matrix)
        glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projection_matrix)

    def upload_bone_matrices(self, bone_matrices):
        bone_count = len(bone_matrices)
        #print("upload bones", bone_count)
        glUniform1i(self.boneCount_loc, bone_count)
        glUniformMatrix4fv(self.bones_loc, bone_count, GL_TRUE, bone_matrices)

    def render_scene(self, object_list, p_m, v_m, scene_edit_widget=None):
        self.prepare(v_m, p_m)
        for o in object_list:
            color = convert_id_to_color(o.node_id)
            if "geometry" in o._components:
                self.render(o.transformation, o._components["geometry"].geometry, color)
            elif "static_mesh" in o._components:
                for geom in o._components["static_mesh"].meshes:
                    self.render(o.transformation, geom, color)
            elif "animated_mesh" in o._components:
                bone_matrices = o._components["animated_mesh"].get_bone_matrices()
                self.upload_bone_matrices(bone_matrices)#  bone matrices once
                for geom in o._components["animated_mesh"].meshes:
                    self.render(o.transformation, geom, color)

        # handle scene edit widget
        if False:
            p_m = np.array(p_m)
            far = 10000.0
            near =  -0.1
            temp = near-far
            p_m[2,2] = (far+near)/temp
            p_m[3,2] = 2.0*far*near/temp
            glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, p_m)
        
        
        if scene_edit_widget is not None and scene_edit_widget.visible:
            glDisable(GL_DEPTH_TEST)
            for key in scene_edit_widget.meshes:
                geometry = scene_edit_widget.meshes[key]
                color = scene_edit_widget.colors[key]
                self.render(scene_edit_widget.transform, geometry, color)
            glEnable(GL_DEPTH_TEST)
        glUseProgram(0)

    def render(self, model_matrix, geometry, color):
        #print("render", color)
        geometry.bind()
        glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, model_matrix)
        #glUniform4fv(self.color_loc, 1, GL_FALSE, color)
        glUniform4f(self.color_loc, color[0]/255, color[1]/255, color[2]/255, color[3]/255)

        stride = geometry.stride
        glEnableVertexAttribArray(self.position_loc)
        glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, stride, geometry.get_vertex_pointer())
        if geometry.has_weights() and geometry.has_bone_ids():
            glUniform1i(self.useSkinning_loc, True)
            glEnableVertexAttribArray(self.boneIDs_loc)
            glVertexAttribPointer(self.boneIDs_loc, 4, GL_FLOAT, False, stride, geometry.get_bone_id_pointer())
            glEnableVertexAttribArray(self.weights_loc)
            glVertexAttribPointer(self.weights_loc, 4, GL_FLOAT, False, stride, geometry.get_weight_pointer())
        else:
            glUniform1i(self.useSkinning_loc, False)

        if geometry.index_buffer is not None:
            glDrawElements(geometry.array_type, geometry.get_num_indices(), GL_UNSIGNED_INT, None)
        else:
            glDrawArrays(geometry.array_type, 0, geometry.get_num_vertices())
        geometry.unbind()

        glDisableVertexAttribArray(self.position_loc)






"""
    def draw_indexed_array(self, vertices, indices, array_type, n_indices, stride):
        try:
            vertices.bind()
            indices.bind()
            glEnableVertexAttribArray(self.vertex_loc)
            glVertexAttribPointer(self.vertex_loc, 3, GL_FLOAT, False, stride, vertices)
            glDrawElements(GL_TRIANGLES, n_indices, GL_UNSIGNED_INT, None)
        except GLerror as e:
            print("error in ShadedGeometry", e)
        finally:
            vertices.unbind()
            indices.unbind()
            glDisableVertexAttribArray(self.vertex_loc)

    def draw_array(self, vertices, array_type, n_vertices, stride):
        try:
            vertices.bind()
            glEnableVertexAttribArray(self.vertex_loc)
            glVertexAttribPointer(self.vertex_loc, 3, GL_FLOAT, False, stride, vertices)
            glDrawArrays(array_type, 0, n_vertices)
        except GLerror as e:
            print("error in ShadedGeometry", e)
        finally:
            vertices.unbind()
            glDisableVertexAttribArray(self.vertex_loc)


"""