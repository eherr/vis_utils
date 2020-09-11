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
""" https://learnopengl.com/Advanced-OpenGL/Framebuffers
"""
from OpenGL.GL import *
from OpenGL.arrays import vbo
import numpy as np
from .shaders import ShaderManager
from .texture import Texture
from PIL import Image, ImageOps

quadVertices = np.array([
        [-1.0,  1.0,  0.0, 1.0],
        [-1.0, -1.0,  0.0, 0.0],
        [ 1.0, -1.0,  1.0, 0.0],

        [-1.0,  1.0,  0.0, 1.0],
        [ 1.0, -1.0,  1.0, 0.0],
        [ 1.0,  1.0,  1.0, 1.0]]
)

class SelectionFrameBuffer(object):
    def __init__(self, w, h):
        self.width = w
        self.height = h
        self.screen_shader = ShaderManager().getShader("outline")
        self.fbo = glGenFramebuffers(1)
        self.rbo = glGenRenderbuffers(1)
        self.texture = glGenTextures(1)
        self.depth_texture = glGenTextures(1)

        #bind color texture
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, w, h, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.texture, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_texture, 0)

        # bind depth and stencil render buffer
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, w, h)

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print( "ERROR::FRAMEBUFFER:: Framebuffer is not complete!")
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)

        # screen quad VAO
        self.vbo = vbo.VBO(np.array(quadVertices, 'f'))

    def resize(self, w, h):
        self.width = w
        self.height = h
        print("resize", w, h)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)

        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, w, h, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, w, h)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)
        return

    def __del__(self):
        try:
            glDeleteFramebuffers(1, self.fbo)
            glDeleteTextures(1, self.texture)
            glDeleteTextures(1, self.depth_texture)
            glDeleteRenderbuffers(1, self.rbo)
        except:
            pass

    def prepare_buffer(self):
        self.bind()
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) #we're not using the stencil buffer now
        glEnable(GL_DEPTH_TEST)

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

    def draw_buffer_to_screen(self):
        #glBindFramebuffer(GL_FRAMEBUFFER, 0) #back to default
        glDisable(GL_DEPTH_TEST)

        self.vbo.bind()
        glUseProgram(self.screen_shader)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(glGetAttribLocation(self.screen_shader, "aPos"), 2, GL_FLOAT, GL_FALSE, 16, self.vbo)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(glGetAttribLocation(self.screen_shader, "aTexCoords"), 2, GL_FLOAT, GL_FALSE, 16, self.vbo+8)
        glActiveTexture(GL_TEXTURE0 + 0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glActiveTexture(GL_TEXTURE0 + 1)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        self.vbo.unbind()
        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glUseProgram(0)
        glActiveTexture(GL_TEXTURE0 + 0)

    def to_image(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        img_data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        glBindTexture(GL_TEXTURE_2D, 0)
        image = Image.new("RGBA", (self.width, self.height))
        image.frombytes(img_data)
        return image

    def save_to_file(self, filename):
        image = ImageOps.flip(self.to_image())
        image.save(filename)
        print("save screenshot", filename)

