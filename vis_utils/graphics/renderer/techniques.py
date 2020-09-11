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
from ..shaders import ShaderManager


class Technique(object):

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

    def stop(self):
        glUseProgram(0)


class ColorTechnique(Technique):
    def __init__(self):
        self.shader = ShaderManager().getShader("color")
        self._find_uniform_locations(('modelMatrix', 'viewMatrix', 'projectionMatrix'))

    def prepare(self,modelMatrix,viewMatrix,projectionMatrix):
       glUseProgram(self.shader)
       glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, modelMatrix)
       glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, viewMatrix)
       glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projectionMatrix)

    def use(self, vbo, vertex_array_type, numVertices):
        try:
            vbo.bind()
            # We only have the two standard per-vertex attributes
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_COLOR_ARRAY)
            glVertexPointer(3, GL_FLOAT, 24, vbo)  # The starting point of the VBO, for the vertices. Skip 6 bytes to get to the next element of the interleaved vertex array
            glColorPointer(3, GL_FLOAT, 24, vbo + 12)  # The starting point of normals, 12 bytes away. Skip 6 bytes to get to the next element of the interleaved vertex array
            glDrawArrays(vertex_array_type, 0, numVertices)
        except  GLerror as e:  # http://pyopengl.sourceforge.net/documentation/opengl_diffs.html
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ColoredGeometry", e)  # , self.modelMatrix
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_COLOR_ARRAY)


class ColorSkinningTechnique(Technique):
    def __init__(self, color):

        self.color = color#np.array([0.0, 0.0, 1.0, 1.0], "f")
        self.shader = ShaderManager().getShader("color_skinning")
        self._find_uniform_locations(['modelMatrix', 'viewMatrix', 'projectionMatrix', "gBoneCount", "gBones", "color"])#
        self._find_attribute_locations(('position', 'BoneIDs', "Weights"))
        self.bone_matrices = np.array([np.eye(4)])
        self.bone_count = 1
        self.set_color(color)

    def set_color(self, color):
        if len(color) == 3:
            color = list(color) + [1.0]
        self.color = color

    def set_matrices(self, matrices):
        self.bone_matrices = matrices
        self.bone_count = len(matrices)

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix):
        glUseProgram(self.shader)
        #mvp = np.dot(np.dot(modelMatrix, viewMatrix), projectionMatrix)
        glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, modelMatrix)
        glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, viewMatrix)
        glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projectionMatrix)
        glUniform1i(self.gBoneCount_loc, self.bone_count)
        glUniformMatrix4fv(self.gBones_loc, self.bone_count, GL_TRUE, self.bone_matrices)
        glUniform4f(self.color_loc, *self.color)

    def use(self, vbo, vertex_array_type, n_vertices):
        try:
            vbo.bind()
            glEnableVertexAttribArray(self.position_loc)
            glEnableVertexAttribArray(self.BoneIDs_loc)
            glEnableVertexAttribArray(self.Weights_loc)

            glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, 44, vbo)
            glVertexAttribPointer(self.BoneIDs_loc, 4, GL_FLOAT, False, 44,  vbo+12)
            glVertexAttribPointer(self.Weights_loc, 4, GL_FLOAT, False, 44, vbo+28)

            glDrawArrays(vertex_array_type, 0, n_vertices)
        except GLerror as e:  # http://pyopengl.sourceforge.net/documentation/opengl_diffs.html
           print("error", e)
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.position_loc)
            glDisableVertexAttribArray(self.BoneIDs_loc)
            glDisableVertexAttribArray(self.Weights_loc)


class ShadingTechnique(Technique):
    def __init__(self):
        self.shader = ShaderManager().getShader("ambient")
        uniform_names = ('Global_ambient', 'Light_ambient', 'Light_diffuse', 'Light_location', 'Material_ambient',
            'Material_diffuse',
            'modelMatrix', 'viewMatrix', 'projectionMatrix')

        self._find_uniform_locations(uniform_names)
        attributes = ('Vertex_position', 'Vertex_normal',)
        self._find_attribute_locations(attributes)

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix):
        glUseProgram(self.shader)
        # set MVP matrix
        glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, modelMatrix)
        glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, viewMatrix)
        glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projectionMatrix)
        # We add a strong red tinge so you can see the global ambient light's contribution.
        glUniform4f(self.Global_ambient_loc, .3, .05, .05, .1)
        # In legacy OpenGL we would be using different special-purpose calls to set these variables.
        glUniform4f(self.light_ambient_loc, .2, .2, .2, 1.0)
        glUniform4f(self.light_diffuse_loc, 1, 1, 1, 1)
        glUniform3f(self.light_location_loc, 2, 3, 10)  # todo get light location from scene
        glUniform4f(self.Material_ambient_loc, .2, .2, .2, 1.0)
        glUniform4f(self.Material_diffuse_loc, 1, 1, 1, 1)

    def use(self, vbo, vertex_array_type, numVertices):
        try:
            vbo.bind()
            # We only have the two per-vertex attributes
            glEnableVertexAttribArray(self.Vertex_position_loc)
            glEnableVertexAttribArray(self.Vertex_normal_loc)
            # skip 6 bytes to get to the next element of the interleaved vertex array
            glVertexAttribPointer(self.Vertex_position_loc, 3, GL_FLOAT, False, 24,
                                  vbo)  # The starting point of the VBO, for the vertices
            glVertexAttribPointer(self.Vertex_normal_loc, 3, GL_FLOAT, False, 24,
                                  vbo + 12)  # The starting point of normals, 12 bytes away
            glDrawArrays(vertex_array_type, 0, numVertices)  # TRIANGLES
        except GLerror as e:  # http://pyopengl.sourceforge.net/documentation/opengl_diffs.html
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ShadedGeometry", e)  # , self.modelMatrix
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.Vertex_position_loc)
            glDisableVertexAttribArray(self.Vertex_normal_loc)


class PhongShadingTechnique(Technique):
    def __init__(self, material):
        self.material = material
        self.shader = ShaderManager().getShader("phong2")
        uniform_names = ('modelMatrix', 'viewMatrix', 'projectionMatrix', 'light.ambient_color', 'light.diffuse_color',
            'light.position','lightPos', 'lightPos', 'viewerPos','material.ambient_color','material.diffuse_color','material.specular_color','material.specular_shininess')
        self._find_uniform_locations(uniform_names)
        attributes = ('vertex', 'vertex_normal',)
        self._find_attribute_locations(attributes)

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        glUseProgram(self.shader)
        # set MVP matrix
        viewer_pos = viewMatrix[:, 3]
        glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, modelMatrix)
        glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, viewMatrix)
        glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projectionMatrix)

        # upload light
        light = lightSources[0]
        glUniform3f(glGetUniformLocation(self.shader, "light.ambient_color"), light.ambient_color[0],
                    light.ambient_color[1], light.ambient_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "light.diffuse_color"), light.diffuse_color[0],
                    light.diffuse_color[1], light.diffuse_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "light.specular_color"), light.specular_color[0],
                    light.specular_color[1], light.specular_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "light.position"), light.position[0],light.position[1], light.position[2])
        glUniform3f(self.lightPos_loc, light.position[0],light.position[1], light.position[2])
        glUniform3f(self.viewerPos_loc, viewer_pos[0], viewer_pos[1], viewer_pos[2])

        # upload material properties
        glUniform3f(glGetUniformLocation(self.shader, "material.ambient_color"), self.material.ambient_color[0],
                    self.material.ambient_color[1], self.material.ambient_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "material.diffuse_color"), self.material.diffuse_color[0],
                    self.material.diffuse_color[1], self.material.diffuse_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "material.specular_color"), self.material.specular_color[0],
                    self.material.specular_color[1], self.material.specular_color[2])
        glUniform1f(glGetUniformLocation(self.shader, "material.specular_shininess"), self.material.specular_shininess)

    def use(self, vbo, vertexArrayType, numVertices):
        try:
            vbo.bind()
            # We only have the two per-vertex attributes
            glEnableVertexAttribArray(self.vertex_loc)
            glEnableVertexAttribArray(self.vertex_normal_loc)
            # skip 6 bytes to get to the next element of the interleaved vertex array
            glVertexAttribPointer(self.vertex_loc, 3, GL_FLOAT, False, 24,
                                  vbo)  # The starting point of the VBO, for the vertices
            glVertexAttribPointer(self.vertex_normal_loc, 3, GL_FLOAT, False, 24,
                                  vbo + 12)  # The starting point of normals, 12 bytes away
            glDrawArrays(vertexArrayType, 0, numVertices)  # TRIANGLES
        except GLerror as e:  # http://pyopengl.sourceforge.net/documentation/opengl_diffs.html
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ShadedGeometry", e)  # , self.modelMatrix
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.vertex_loc)
            glDisableVertexAttribArray(self.vertex_normal_loc)


class DirectionalShadingTechnique(Technique):
    def __init__(self, material):
        self.material = material
        self.shader = ShaderManager().getShader("direction")
        uniform_names = ('modelMatrix', 'viewMatrix', 'projectionMatrix', 'light.intensities', 'light.position',
           'viewerPos','material.ambient_color','material.diffuse_color','material.specular_color','material.specular_shininess')
        self._find_uniform_locations(uniform_names)
        attributes = ('vertex', 'vertex_normal',)
        self._find_attribute_locations(attributes)

    def upload_mvp(self, modelMatrix, viewMatrix, projectionMatrix):
        glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, modelMatrix)
        glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, viewMatrix)
        glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projectionMatrix)

    def upload_material(self):
        # upload material properties
        glUniform3f(glGetUniformLocation(self.shader, "material.ambient_color"), self.material.ambient_color[0],
                    self.material.ambient_color[1], self.material.ambient_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "material.diffuse_color"), self.material.diffuse_color[0],
                    self.material.diffuse_color[1], self.material.diffuse_color[2])
        glUniform3f(glGetUniformLocation(self.shader, "material.specular_color"), self.material.specular_color[0],
                    self.material.specular_color[1], self.material.specular_color[2])
        glUniform1f(glGetUniformLocation(self.shader, "material.specular_shininess"),
                    self.material.specular_shininess)

    def upload_lights(self, lightSources):
        light = lightSources[0]
        glUniform3f(glGetUniformLocation(self.shader, "light.intensities"), light.intensities[0],
                    light.intensities[1], light.intensities[2])
        glUniform4f(glGetUniformLocation(self.shader, "light.position"), light.position[0], light.position[1],
                    light.position[2], light.position[3])

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        glUseProgram(self.shader)
        # set MVP matrix
        self.upload_mvp(modelMatrix, viewMatrix, projectionMatrix)
        # upload light
        self.upload_lights(lightSources)

        viewer_pos = viewMatrix[:, 3]
        #glUniform3f(self.inLightDirection_loc, light.direction[0],light.direction[1], light.direction[2])
        glUniform3f(self.viewerPos_loc, viewer_pos[0], viewer_pos[1], viewer_pos[2])

        self.upload_material()

    def use(self, vbo, vertexArrayType, numVertices):
        try:
            vbo.bind()
            # We only have the two per-vertex attributes
            glEnableVertexAttribArray(self.vertex_loc)
            glEnableVertexAttribArray(self.vertex_normal_loc)
            glVertexAttribPointer(self.vertex_loc, 3, GL_FLOAT, False, 24, vbo)
            glVertexAttribPointer(self.vertex_normal_loc, 3, GL_FLOAT, False, 24, vbo + 12)
            glDrawArrays(vertexArrayType, 0, numVertices)
        except GLerror as e:
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ShadedGeometry", e)  # , self.modelMatrix
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.vertex_loc)
            glDisableVertexAttribArray(self.vertex_normal_loc)


class SkinningShadingTechnique(DirectionalShadingTechnique):
    def __init__(self, material):
        self.material = material
        self.shader = ShaderManager().getShader("skinning_shader")
        uniform_names = ('modelMatrix', 'viewMatrix', 'projectionMatrix',
                         'light.intensities', 'light.position',
                         'viewerPos', 'material.ambient_color',
                         'material.diffuse_color', 'material.specular_color',
                         'material.specular_shininess', 'Bones')
        self._find_uniform_locations(uniform_names)
        attributes = ('vertex', 'vertex_normal', 'BoneIDs', 'Weights')
        self._find_attribute_locations(attributes)

    def upload_bones(self, bone_matrices):
        print("bone matrices",len(bone_matrices))
        glUniformMatrix4fv(self.Bones_loc, 62, GL_FALSE, bone_matrices)#np.zeros((62,16))

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix, lightSources, boneMatrices):
        super(SkinningShadingTechnique, self).prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.upload_bones(boneMatrices)

    def use(self, vbo, vertexArrayType, numVertices):

        try:
            vbo.bind()
            # We only have the two per-vertex attributes
            glEnableVertexAttribArray(self.vertex_loc)
            glEnableVertexAttribArray(self.vertex_normal_loc)
            glEnableVertexAttribArray(self.BoneIDs_loc)
            glEnableVertexAttribArray(self.Weights_loc)
            #assuming 1 flaot 4 bytes and 1 integer 4 bytes 14*4 = 56
            glVertexAttribPointer(self.vertex_loc, 3, GL_FLOAT, False, 56, vbo)
            glVertexAttribPointer(self.vertex_normal_loc, 3, GL_FLOAT, False, 56, vbo + 12)
            glVertexAttribPointer(self.BoneIDs_loc, 4, GL_INT, False, 56, vbo + 24)
            glVertexAttribPointer(self.Weights_loc, 4, GL_FLOAT, False, 56, vbo + 40)
            glDrawArrays(vertexArrayType, 0, numVertices)

        except GLerror as e:
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ShadedGeometry", e)  # , self.modelMatrix
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.vertex_loc)
            glDisableVertexAttribArray(self.vertex_normal_loc)
            glDisableVertexAttribArray(self.BoneIDs_loc)
            glDisableVertexAttribArray(self.Weights_loc)


class TextureTechnique(Technique):
    def __init__(self, material):
        self.material = material
        self.shader = ShaderManager().getShader("texture")
        uniform_names = ["MVP","tex"]
        self._find_uniform_locations(uniform_names)
        attributes = ['position', 'vertexUV']
        self._find_attribute_locations(attributes)

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):

        glUseProgram(self.shader)
        mvp = np.dot(np.dot(modelMatrix,  viewMatrix), projectionMatrix)
        glUniformMatrix4fv(self.MVP_loc, 1, GL_FALSE, mvp)
        self.upload_texture()

    def upload_texture(self):
        glActiveTexture(GL_TEXTURE0)
        self.material.diffuse_texture.bind()
        glUniform1i(self.tex_loc, 0)

    def use(self, vbo, vertexArrayType, numVertices):

        try:
            vbo.bind()
            glEnableVertexAttribArray(self.position_loc)
            glEnableVertexAttribArray(self.vertexUV_loc)
            glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, 20, vbo)
            glVertexAttribPointer(self.vertexUV_loc, 2, GL_FLOAT, False, 20, vbo + 12)
            glDrawArrays(vertexArrayType, 0, numVertices)  # TRIANGLES
        except GLerror as e:
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ShadedGeometry", e)  # , self.modelMatrix
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.position_loc)
            glDisableVertexAttribArray(self.vertexUV_loc)

    def stop(self):
        self.material.diffuse_texture.unbind()
        glUseProgram(0)


class TerrainTechnique(TextureTechnique):
    def __init__(self, material):
        self.material = material
        self.shader = ShaderManager().getShader("terrain")
        print(self.shader)
        uniform_names = ["MVP", "tex", "height_map", "heightMapScale"]
        self._find_uniform_locations(uniform_names)
        attributes = ['position', 'vertexUV', "heightMapUV"]
        self._find_attribute_locations(attributes)

    def upload_texture(self):

        glActiveTexture(GL_TEXTURE0)
        self.material.diffuse_texture.bind()
        glUniform1i(self.tex_loc, 0)

        glActiveTexture(GL_TEXTURE0 + 2)
        self.material.height_map_texture.bind()
        glUniform1i(self.height_map_loc, 2)

        glUniform1f(self.heightMapScale_loc, self.material.height_map_scale)

    def use(self, vbo, vertexArrayType, numVertices):

        try:
            vbo.bind()
            glEnableVertexAttribArray(self.position_loc)
            glEnableVertexAttribArray(self.vertexUV_loc)
            glEnableVertexAttribArray(self.heightMapUV_loc)

            glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, 28, vbo)
            glVertexAttribPointer(self.vertexUV_loc, 2, GL_FLOAT, False, 28, vbo + 12)
            glVertexAttribPointer(self.heightMapUV_loc, 2, GL_FLOAT, False, 28, vbo + 20)

            glDrawArrays(vertexArrayType, 0, numVertices)
        except GLerror as e:
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ShadedGeometry", e)  #
        finally:
            vbo.unbind()
            glDisableVertexAttribArray(self.position_loc)
            glDisableVertexAttribArray(self.vertexUV_loc)
            glDisableVertexAttribArray(self.heightMapUV_loc)

    def stop(self):
        self.material.diffuse_texture.unbind()
        self.material.height_map_texture.unbind()
        glUseProgram(0)


class ShadedTextureTechnique(DirectionalShadingTechnique, TextureTechnique):
    uniform_names = ['modelMatrix', 'viewMatrix', 'projectionMatrix', "tex", 'light.intensities',
                     'light.position', 'viewerPos', 'material.ambient_color',
                     'material.diffuse_color', 'material.specular_color',
                     'material.specular_shininess'
                     ]

    def __init__(self, material):
        self.material = material
        self.shader = ShaderManager().getShader("shaded_texture")
        self._find_uniform_locations(self.uniform_names)
        attributes = ['position', "normal", 'vertexUV']
        self._find_attribute_locations(attributes)

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):

        glUseProgram(self.shader)
        self.upload_mvp(modelMatrix, viewMatrix, projectionMatrix)
        self.upload_lights(lightSources)
        glUniform3f(self.viewerPos_loc, viewMatrix[0, 3], viewMatrix[1, 3], viewMatrix[2, 3])
        self.upload_material()
        self.upload_texture()

    def use(self, vbo, vertexArrayType, numVertices):

        try:
            vbo.bind()
            glEnableVertexAttribArray(self.position_loc)
            glEnableVertexAttribArray(self.normal_loc)
            glEnableVertexAttribArray(self.vertexUV_loc)
            glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, 32, vbo)
            glVertexAttribPointer(self.normal_loc, 3, GL_FLOAT, False, 32, vbo + 12)
            glVertexAttribPointer(self.vertexUV_loc, 2, GL_FLOAT, False, 32, vbo + 24)
            glDrawArrays(vertexArrayType, 0, numVertices)  # TRIANGLES
        except GLerror as e:
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ShadedGeometry", e)  # , self.modelMatrix
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.position_loc)
            glDisableVertexAttribArray(self.normal_loc)
            glDisableVertexAttribArray(self.vertexUV_loc)

    def stop(self):
        self.material.diffuse_texture.unbind()
        glUseProgram(0)


class DirectionalShadingIndexTechnique(DirectionalShadingTechnique):
    def use(self, vertices, indices, vertexArrayType, numIndices):
        try:
            vertices.bind()
            indices.bind()
            # We only have the two per-vertex attributes
            glEnableVertexAttribArray(self.vertex_loc)
            glEnableVertexAttribArray(self.vertex_normal_loc)
            glVertexAttribPointer(self.vertex_loc, 3, GL_FLOAT, False, 24,
                                  vertices)  # The starting point of the VBO, for the vertices
            glEnableVertexAttribArray(self.vertex_normal_loc)
            glVertexAttribPointer(self.vertex_normal_loc, 3, GL_FLOAT, False, 24,
                                  vertices + 12)  # skip 6 bytes to get to the next element of the interleaved vertex array
            glDrawElements(GL_TRIANGLES, numIndices, GL_UNSIGNED_INT, None)
        except GLerror as e:
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ShadedGeometry", e)  # , self.modelMatrix
        finally:
            vertices.unbind()
            indices.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.vertex_loc)
            glDisableVertexAttribArray(self.vertex_normal_loc)


class ShadedSkinningTextureTechnique(DirectionalShadingTechnique, TextureTechnique):
    uniform_names = ['modelMatrix', 'viewMatrix', 'projectionMatrix', "tex", 'light.intensities',
                     'light.position', 'viewerPos', 'material.ambient_color',
                     'material.diffuse_color', 'material.specular_color',
                     'material.specular_shininess', 'bones', 'boneCount']
    attribute_names = ['position', "normal", 'vertexUV', 'boneIDs', 'weights']

    def __init__(self, material):
        self.material = material
        self.shader = ShaderManager().getShader("skinned_shaded_texture")
        self._find_uniform_locations(self.uniform_names)
        self._find_attribute_locations(self.attribute_names)
        self.bone_count = 0
        self.bone_matrices = []

    def set_matrices(self, bone_matrices):
        self.bone_count = len(bone_matrices)
        self.bone_matrices = np.array(bone_matrices)

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        glUseProgram(self.shader)
        self.upload_mvp(modelMatrix, viewMatrix, projectionMatrix)
        self.upload_lights(lightSources)
        glUniform3f(self.viewerPos_loc, viewMatrix[0, 3], viewMatrix[1, 3], viewMatrix[2, 3])
        self.upload_material()
        self.upload_texture()
        self.upload_bone_matrices()

    def upload_bone_matrices(self):
        glUniform1i(self.boneCount_loc, self.bone_count)
        glUniformMatrix4fv(self.bones_loc, self.bone_count, GL_TRUE, self.bone_matrices)

    def use(self, vbo, vertex_array_type, num_vertices):

        try:
            vbo.bind()
            glEnableVertexAttribArray(self.position_loc)
            glEnableVertexAttribArray(self.normal_loc)
            glEnableVertexAttribArray(self.vertexUV_loc)
            glEnableVertexAttribArray(self.boneIDs_loc)
            glEnableVertexAttribArray(self.weights_loc)

            glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, 64, vbo)
            glVertexAttribPointer(self.normal_loc, 3, GL_FLOAT, False, 64, vbo + 12)
            glVertexAttribPointer(self.vertexUV_loc, 2, GL_FLOAT, False, 64, vbo + 24)
            glVertexAttribPointer(self.boneIDs_loc, 4, GL_FLOAT, False, 64, vbo + 32)
            glVertexAttribPointer(self.weights_loc, 4, GL_FLOAT, False, 64, vbo + 48)

            glDrawArrays(vertex_array_type, 0, num_vertices)
        except GLerror as e:
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("Error in ShadedSkinningTextureTechnique", e)
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.position_loc)
            glDisableVertexAttribArray(self.normal_loc)
            glDisableVertexAttribArray(self.vertexUV_loc)
            glDisableVertexAttribArray(self.boneIDs_loc)
            glDisableVertexAttribArray(self.weights_loc)

    def stop(self):
        self.material.diffuse_texture.unbind()
        glUseProgram(0)



class NormalSkinningTextureTechnique(Technique):
    uniform_names = ['modelMatrix', 'viewMatrix', 'projectionMatrix', 'bones', 'boneCount']
    attribute_names = ['position', "normal",  'boneIDs', 'weights']

    def __init__(self):
        self.shader = ShaderManager().getShader("skinned_normal")
        self._find_uniform_locations(self.uniform_names)
        self._find_attribute_locations(self.attribute_names)
        self.bone_count = 0
        self.bone_matrices = []

    def set_matrices(self, bone_matrices):
        self.bone_count = len(bone_matrices)
        self.bone_matrices = np.array(bone_matrices)

    def prepare(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        glUseProgram(self.shader)
        self.upload_mvp(modelMatrix, viewMatrix, projectionMatrix)
        self.upload_bone_matrices()

    def upload_mvp(self, modelMatrix, viewMatrix, projectionMatrix):
        glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, modelMatrix)
        glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, viewMatrix)
        glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projectionMatrix)

    def upload_bone_matrices(self):
        glUniform1i(self.boneCount_loc, self.bone_count)
        glUniformMatrix4fv(self.bones_loc, self.bone_count, GL_TRUE, self.bone_matrices)

    def use(self, vbo, vertex_array_type, num_vertices):

        try:
            vbo.bind()
            glEnableVertexAttribArray(self.position_loc)
            glEnableVertexAttribArray(self.normal_loc)
            glEnableVertexAttribArray(self.boneIDs_loc)
            glEnableVertexAttribArray(self.weights_loc)

            glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, 56, vbo)
            glVertexAttribPointer(self.normal_loc, 3, GL_FLOAT, False, 56, vbo + 12)
            glVertexAttribPointer(self.boneIDs_loc, 4, GL_FLOAT, False, 56, vbo + 24)
            glVertexAttribPointer(self.weights_loc, 4, GL_FLOAT, False, 56, vbo + 40)

            glDrawArrays(vertex_array_type, 0, num_vertices)
        except GLerror as e:
            # note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("Error in ShadedSkinningTextureTechnique", e)
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.position_loc)
            glDisableVertexAttribArray(self.normal_loc)
            glDisableVertexAttribArray(self.boneIDs_loc)
            glDisableVertexAttribArray(self.weights_loc)

    def stop(self):
        glUseProgram(0)
