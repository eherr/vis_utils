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
from OpenGL.GL import *
import numpy as np
from .main_renderer import Renderer
from ..shaders import ShaderManager


class ShadowMapRenderer(Renderer):
    uniform_names = ['projMatrix', 'viewMatrix',"modelMatrix", "boneCount","useSkinning","bones" ]
    attribute_names = ['position', 'boneIDs', 'weights']
    def __init__(self):
        self.shader = ShaderManager().getShader("shadow_mapping")
        self._find_uniform_locations(self.uniform_names)
        self._find_attribute_locations(self.attribute_names)
        self.counter = 0

    def upload_bone_matrices(self, bone_matrices):
        bone_count = len(bone_matrices)
        #print("upload bones", bone_count)
        glUniform1i(self.boneCount_loc, bone_count)
        glUniformMatrix4fv(self.bones_loc, bone_count, GL_TRUE, bone_matrices)

    def render_scene(self, object_list, camera, light_sources):
        glCullFace(GL_FRONT)
        glUseProgram(self.shader)
        self.counter = 0
        for l in light_sources:
            l.update(camera)
            #l.bind_matrix(self.lightSpaceMatrix_loc)
            #glUniformMatrix4fv(self.lightSpaceMatrix_loc, 1, GL_FALSE, l.light_space)
            l.pre_render()
            for o in object_list:
                if not o.visible:
                    continue
                if "geometry" in o._components:
                    #print("render", o._components.keys())
                    self.render(o.transformation, o._components["geometry"].geometry, l)
                if "static_mesh" in o._components:
                    for geom in o._components["static_mesh"].meshes:
                        self.render(o.transformation, geom, l)
                if "skeleton_vis" in o._components and o._components["skeleton_vis"].visible:
                    skeleton = o._components["skeleton_vis"]
                    if skeleton.draw_mode == 2:#only draw boxes
                        for idx, key in enumerate(skeleton._joints):
                            m = skeleton.matrices[idx].T
                            for geom in skeleton.shapes[key]:
                                self.render(np.dot(geom.transform, m), geom, l)
                if "animated_mesh" in o._components and o._components["animated_mesh"].visible:
                    bone_matrices = o._components["animated_mesh"].get_bone_matrices()
                    self.upload_bone_matrices(bone_matrices)  # bone matrices once
                    for geom in o._components["animated_mesh"].meshes:
                        self.render(o.transformation, geom, l)
                if "character" in o._components and o._components["character"].visible:
                    char = o._components["character"]
                    for key, geom in char.body_shapes.items():
                        model_matrix = char.articulated_figure.bodies[key].get_transformation()
                        self.render(model_matrix, geom, l)
                    model_matrix = np.eye(4)
                    for key, geom in char.joint_shapes.items():
                        model_matrix[3, :3] = char.articulated_figure.joints[key].get_position()
                        self.render(model_matrix, geom, l)
            l.post_render()
        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glCullFace(GL_BACK)
        #print("drew", self.counter, "objects")


    def render(self, model_matrix, geometry, light):

        #print("draw")
        self.counter += 1
        geometry.bind()

        glUniformMatrix4fv(self.projMatrix_loc, 1, GL_FALSE, light.proj_mat)
        glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, light.view_mat)
        glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, model_matrix)
        #print("light mat", light.view_mat)
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
        glDisableVertexAttribArray(self.boneIDs_loc)
        glDisableVertexAttribArray(self.weights_loc)
