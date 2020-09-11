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
""" https://learnopengl.com/Advanced-Lighting/Shadows/Shadow-Mapping
"""
from OpenGL.GL import *
import numpy as np
from OpenGL.arrays import vbo
from .shaders import ShaderManager
import PIL

quad_vertices = np.array([
    [-1.0, 1.0, 0.0, 1.0],
    [-1.0, -1.0, 0.0, 0.0],
    [1.0, -1.0, 1.0, 0.0],

    [-1.0, 1.0, 0.0, 1.0],
    [1.0, -1.0, 1.0, 0.0],
    [1.0, 1.0, 1.0, 1.0]]
)


class ShadowMapBuffer(object):
    def __init__(self, w, h):
        self.width = w
        self.height = h
        self.screen_shader = ShaderManager().getShader("shadow_screen")
        self.rbo = glGenRenderbuffers(1)
        self.fbo = glGenFramebuffers(1)
        self.depth_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, w, h, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # prevent shadow outside of the light view frustrum
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        border_color = np.array([1.0, 1.0, 1.0, 1.0])
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border_color)

        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_texture, 0)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, w, h)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        self.depth_sampler = glGenSamplers(1)

        self.vbo = vbo.VBO(np.array(quad_vertices, 'f'))

        # Always check that our framebuffer is ok
        if(glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE):
            self.success = False
            print("failed to create shadow buffer")
        else:
            print("created shadow buffer")
            self.success = True


    def __del__(self):
        try:
            glDeleteFramebuffers(1, self.fbo)
            glDeleteTextures(1, self.depth_texture)
            glDeleteRenderbuffers(1, self.rbo)
        except:
            pass

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

    def prepare_buffer(self):
        self.bind()
        glViewport(0, 0, self.width, self.height)

        glClear(GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

    def draw_buffer_to_screen(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # back to default
        glDisable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        self.vbo.bind()
        glUseProgram(self.screen_shader)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(glGetAttribLocation(self.screen_shader, "aPos"), 2, GL_FLOAT, GL_FALSE, 16, self.vbo)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(glGetAttribLocation(self.screen_shader, "aTexCoords"), 2, GL_FLOAT, GL_FALSE, 16,
                              self.vbo + 8)
        glActiveTexture(GL_TEXTURE0 + 0)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        self.vbo.unbind()
        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glUseProgram(0)
        glActiveTexture(GL_TEXTURE0 + 0)

    def save_to_file(self, filename):
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        tex_data = glGetTexImage(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, GL_FLOAT)
        img_data = []
        for x in range(self.width):
            for y in range(self.height):
                v = int(tex_data[x,y]*255)
                img_data.append(v)
                img_data.append(v)
                img_data.append(v)
                #img_data.append(255)
        img_data = bytes(img_data)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.image = PIL.Image.new("RGB", (self.width, self.height))
        self.image.frombytes(img_data)
        self.image.save(filename)

