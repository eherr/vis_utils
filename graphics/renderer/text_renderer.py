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
import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from .techniques import Technique
from ..shaders import ShaderManager
from OpenGL.arrays import vbo


class TextTechnique(Technique):
    def __init__(self):
        self.shader = ShaderManager().getShader("texture")
        uniform_names = ["MVP","tex"]
        self._find_uniform_locations(uniform_names)
        attributes = ['position', 'vertexUV']
        self._find_attribute_locations(attributes)
        self.texture_id = -1
        self.generate_texture()

    def prepare(self, orthographic_matrix):
        glUseProgram(self.shader)
        glUniformMatrix4fv(self.MVP_loc, 1, GL_FALSE, orthographic_matrix)

    def generate_texture(self):
        """ https://stackoverflow.com/questions/29015999/pygame-opengl-how-to-draw-text-after-glbegin"""

        self.texture_id = glGenTextures(1)
        glUseProgram(self.shader)
        return self.update_texture("")

    def update_texture(self, text):
        font = pygame.font.Font(None, 64)
        textSurface = font.render(text, True, (255, 255, 255, 255),
                                  (0, 0, 0, 255))
        ix, iy = textSurface.get_width(), textSurface.get_height()
        image = pygame.image.tostring(textSurface, "RGBX", True)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        # glBindTexture(GL_TEXTURE_2D, i)
        glUniform1i(self.tex_loc, 0)
        return np.array([ix, iy])

    def stop(self):
        glUseProgram(0)

    def use2(self, min_pos, max_pos, z):
        glEnableVertexAttribArray(self.vertexUV_loc)
        texcoord_index = self.vertexUV_loc
        pos_loc = self.position_loc

        # texcoord_index = glGetAttribLocation(self.shader, "vertexUV")
        print("tex", texcoord_index)
        glBegin(GL_QUADS)
        glVertexAttrib3f(pos_loc, min_pos[0], min_pos[1], z)
        #glVertexAttrib2f(self.vertexUV_loc, 0.0, 0.0)
        glVertexAttrib3f(pos_loc, max_pos[0], min_pos[1], z)
        # glVertexAttrib2f(self.vertexUV_loc, 1.0, 0.0)


        glVertexAttrib3f(pos_loc, max_pos[0], max_pos[1], z)
        # glVertexAttrib2f(self.vertexUV_loc, 1.0, 1.0)


        glVertexAttrib3f(pos_loc, min_pos[0], max_pos[1], z)
        # glVertexAttrib2f(self.vertexUV_loc, 0.0, 1.0)

        glEnd()

    def use(self, vbo, vertex_array_type, n_vertices):

        try:
            vbo.bind()
            glEnableVertexAttribArray(self.position_loc)
            glEnableVertexAttribArray(self.vertexUV_loc)
            glVertexAttribPointer(self.position_loc, 3, GL_FLOAT, False, 20, vbo)
            glVertexAttribPointer(self.vertexUV_loc, 2, GL_FLOAT, False, 20, vbo + 12)
            glDrawArrays(vertex_array_type, 0, n_vertices)  # TRIANGLES
        except GLerror as e:
            print("error in ShadedGeometry", e)  # , self.modelMatrix
        finally:
            vbo.unbind()
            # Need to cleanup, as always.
            glDisableVertexAttribArray(self.position_loc)
            glDisableVertexAttribArray(self.vertexUV_loc)


class TextRenderer(object):
    def __init__(self, ):
        self.technique = TextTechnique()
        self.vertex_array_type = GL_QUADS
        vertices = []
        self._vbo = vbo.VBO(np.array(vertices,'f'))
        self.n_vertices = len(vertices)

    def draw(self, orthographic_matrix, top_left, z, text, scale=1.0):
        # https://stackoverflow.com/questions/10630823/how-to-get-texture-coordinate-to-glsl-in-version-150

        self.technique.prepare(orthographic_matrix)
        rect = self.technique.update_texture(text)
        min_pos = top_left
        max_pos = top_left + rect*scale
        vertices = [[min_pos[0], max_pos[1], z, 0, -1],
                    [max_pos[0], max_pos[1], z, 1, -1],
                    [max_pos[0], min_pos[1], z, 1, 0],
                    [min_pos[0], min_pos[1], z, 0, 0],
                    ]
        self.n_vertices = len(vertices)
        self._vbo.set_array(np.array(vertices, 'f'))
        self.technique.use(self._vbo, self.vertex_array_type, self.n_vertices)
        self.technique.stop()
        return max_pos

