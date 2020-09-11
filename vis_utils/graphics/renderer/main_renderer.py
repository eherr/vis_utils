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
""" https://www.khronos.org/opengl/wiki/Sampler_(GLSL)"""
import numpy as np
from OpenGL.GL import *
from ..shaders import ShaderManager
MAIN_MAX_LIGHTS = 8


class Renderer(object):
    def _find_uniform_locations(self, uniform_names):
        for uniform in uniform_names:
            location = glGetUniformLocation(self.shader, uniform)
            if location in (None, -1):
                print('Warning, no uniform: %s' % (uniform))
            setattr(self, uniform + '_loc', location)

    def _find_attribute_locations(self, attribute_names):
        for attribute in attribute_names:
            location = glGetAttribLocation(self.shader, attribute)
            if location in (None, -1):
                print('Warning, no attribute: %s' % (attribute))
            setattr(self, attribute + '_loc', location)


class MainRenderer(Renderer):
    uniform_names = ['modelMatrix', 'viewMatrix', 'projectionMatrix', "tex", 'viewerPos', 'material.ambient_color',
                     'material.diffuse_color', 'material.specular_color', #              'light.intensities', 'light.position',
                     'material.specular_shininess', 'useTexture', 'useSkinning', 'bones', 'boneCount', "lightCount", "lights", "useShadow", "skyColor"]
    attribute_names = ['position', "normal", 'uv', 'boneIDs', 'weights']
    def __init__(self, sky_color=[0,0,0]):
        self.shader = ShaderManager().getShader("main")
        self._find_uniform_locations(self.uniform_names)
        self._find_attribute_locations(self.attribute_names)
        self.texture_unit_counter = 0
        self.diffuse_sampler = glGenSamplers(1)
        self.use_shadow = True
        self.sky_color = sky_color

    def upload_material(self, material):
        # upload material properties
        glUniform3f(glGetUniformLocation(self.shader, "material.ambient_color"), material.ambient_color[0],
                    material.ambient_color[1], material.ambient_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "material.diffuse_color"), material.diffuse_color[0],
                    material.diffuse_color[1], material.diffuse_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "material.specular_color"), material.specular_color[0],
                    material.specular_color[1], material.specular_color[2])
        glUniform1f(glGetUniformLocation(self.shader, "material.specular_shininess"),
                    material.specular_shininess)

    def upload_lights_old(self, lightSources):
        light = lightSources[0]
        glUniform1i(self.lightCount_loc, len(lightSources))
        glUniform3f(glGetUniformLocation(self.shader, "light.intensities"), light.intensities[0],
                    light.intensities[1], light.intensities[2])
        glUniform4f(glGetUniformLocation(self.shader, "light.position"), light.position[0], light.position[1],
                    light.position[2], light.position[3])


    def upload_lights(self, lights):
        n_lights = min(len(lights), MAIN_MAX_LIGHTS)
        glUniform1i(self.lightCount_loc, n_lights)
        texture_offset = self.texture_unit_counter
        texture_offset = 2
        for idx in range(n_lights):
            p = lights[idx].position
            intensities = lights[idx].intensities
            glUniform3f(glGetUniformLocation(self.shader, "lights["+str(idx)+"].intensities"), intensities[0],
                        intensities[1], intensities[2])
            glUniform4f(glGetUniformLocation(self.shader, "lights["+str(idx)+"].position"), p[0], p[1],
                        p[2], p[3])
            depth_tex = lights[idx].get_depth_texture()
            glActiveTexture(GL_TEXTURE0 + idx + texture_offset)
            glBindTexture(GL_TEXTURE_2D, depth_tex)
            glUniform1i(glGetUniformLocation(self.shader, "lights[" + str(idx) + "].shadowMap"),  idx + texture_offset)

            glUniformMatrix4fv(glGetUniformLocation(self.shader, "lights[" + str(idx) + "].viewMatrix"), 1, GL_FALSE, lights[idx].view_mat)
            glUniformMatrix4fv(glGetUniformLocation(self.shader, "lights[" + str(idx) + "].projectionMatrix"), 1, GL_FALSE, lights[idx].proj_mat)

        self.texture_unit_counter = n_lights



    def upload_bone_matrices(self, bone_matrices):
        bone_count = len(bone_matrices)
        glUniform1i(self.boneCount_loc, bone_count)
        glUniformMatrix4fv(self.bones_loc, bone_count, GL_TRUE, bone_matrices)

    def prepare(self, view_matrix, projection_matrix, lights):
        self.texture_unit_counter = 0 # diffuse texture
        glUseProgram(self.shader)
        glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, view_matrix)
        glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projection_matrix)
        self.upload_lights(lights)
        glUniform3f(self.viewerPos_loc, view_matrix[0, 3], view_matrix[1, 3], view_matrix[2, 3])
        glUniform1i(self.useShadow_loc, self.use_shadow)
        glUniform3f(self.skyColor_loc,  self.sky_color[0],  self.sky_color[1],  self.sky_color[2])

        #glUniformMatrix4fv(self.lightViewMatrix_loc, 1, GL_FALSE, self.light.view_mat)
        #glUniformMatrix4fv(self.lightProjectionMatrix_loc, 1, GL_FALSE, self.light.proj_mat)


    def render_scene(self, object_list, p_m, v_m, lights):
        self.prepare(v_m, p_m, lights)

        for o in object_list:
            if not o.visible:
                continue
            o.prepare_rendering(self)
            for geom in o.get_meshes():
                self.render(o.transformation, geom)
            if "skeleton_vis" in o._components and o._components["skeleton_vis"].visible:
                skeleton = o._components["skeleton_vis"]
                if skeleton.draw_mode == 2:#only draw boxes
                    for idx, key in enumerate(skeleton._joints):
                        m = skeleton.matrices[idx].T
                        for geom in skeleton.shapes[key]:
                            self.render(np.dot(geom.transform, m), geom)
            if "skeleton_mirror" in o._components and o._components["skeleton_mirror"].visible:
                mirror = o._components["skeleton_mirror"]
                skeleton = mirror.src_skeleton
                for state in mirror.states:
                    for idx, key in enumerate(skeleton._joints):
                        m = state[idx]
                        for geom in skeleton.shapes[key]:
                            self.render(np.dot(geom.transform, m), geom)
            if "character" in o._components and o._components["character"].visible:
                char = o._components["character"]
                for key, geom in char.body_shapes.items():
                    self.render(char.body_matrices[key], geom)
                for key, geom in char.joint_shapes.items():
                    self.render(char.joint_matrices[key], geom)
            if "character_mirror" in o._components and o._components["character_mirror"].visible:
                mirror = o._components["character_mirror"]
                char = mirror.src_figure
                for s in mirror.states:
                    for key, geom in char.body_shapes.items():
                        self.render(s["body_matrices"][key], geom, s["materials"][key])
                    for key, geom in char.joint_shapes.items():
                        self.render(s["joint_matrices"][key], geom)
            if "collision_boundary" in o._components:
                c = o._components["collision_boundary"]
                self.render(c.transformation, c.mesh)
            

        glUseProgram(0)
        #for i in range(self.texture_unit_counter):
        #    glBindSampler(i,i)

    def render(self, model_matrix, geometry, material=None):
        geometry.bind()
        glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, model_matrix)
        stride = geometry.stride
        glEnableVertexAttribArray(self.position_loc)
        glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, stride, geometry.get_vertex_pointer())
        if geometry.has_normal() > 0:
            glEnableVertexAttribArray(self.normal_loc)
            glVertexAttribPointer(self.normal_loc, 3, GL_FLOAT, False, stride, geometry.get_normal_pointer())

        if geometry.has_uv():
            glEnableVertexAttribArray(self.uv_loc)
            glVertexAttribPointer(self.uv_loc, 2, GL_FLOAT, False, stride,  geometry.get_uv_pointer())
        #print(geometry.normal_pos, geometry.uv_pos,  geometry.stride)
        if material is None:
            material = geometry.material
        if material is not None:
            self.upload_material(material)
            if material.diffuse_texture is not None:
                glActiveTexture(GL_TEXTURE0)
                material.diffuse_texture.bind()
                #glBindSampler(0, self.diffuse_sampler)

                glUniform1i(self.tex_loc, 0)
                glUniform1i(self.useTexture_loc, True)
                self.texture_unit_counter +=1
            else:
                glUniform1i(self.useTexture_loc, False)


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
        glDisableVertexAttribArray(self.normal_loc)
        glDisableVertexAttribArray(self.uv_loc)
        glDisableVertexAttribArray(self.boneIDs_loc)
        glDisableVertexAttribArray(self.weights_loc)
        if material is not None:
            if material.diffuse_texture is not None:
                material.diffuse_texture.unbind()


