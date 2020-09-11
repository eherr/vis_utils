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
https://learnopengl.com/code_viewer_gh.php?code=src/4.advanced_opengl/11.anti_aliasing_offscreen/anti_aliasing_offscreen.cpp

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


class MultiResolutionScreenFramebuffer(object):
    def __init__(self, w, h, samples=4):
        self.width = w
        self.height = h
        self.samples = samples
        self.screen_shader = ShaderManager().getShader("screen")

        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        self.color_texture_multi_sampled = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, self.color_texture_multi_sampled)
        glTexImage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE, samples, GL_RGBA, w, h, GL_TRUE)
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.color_texture_multi_sampled, 0)

        self.rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, self.samples, GL_DEPTH_COMPONENT, w, h)
        #glBindRenderbuffer(GL_RENDERBUFFER, 0)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.rbo)
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                print( "ERROR::FRAMEBUFFER:: Framebuffer is not complete!")
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        # configure second post-processing framebuffer
        self.intermediate_fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.intermediate_fbo)
        # create a color attachment texture
        self.screen_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.screen_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.screen_texture, 0)	# we only need a color buffer

        self.depth_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, w, h, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_texture, 0)

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
           print( "ERROR::FRAMEBUFFER:: Intermediate framebuffer is not complete!")
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.vbo = vbo.VBO(np.array(quadVertices, 'f'))

    def resize(self, w, h):
        self.width = w
        self.height = h
        print("resize", w, h)
        glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, self.color_texture_multi_sampled)
        glTexImage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE, self.samples, GL_RGBA, w, h, GL_TRUE)
        glBindTexture(GL_TEXTURE_2D, self.screen_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, w, h, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None)
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, self.samples, GL_DEPTH_COMPONENT, w, h)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

    def __del__(self):
        try:
            glDeleteFramebuffers(1, self.fbo)
            glDeleteTextures(1, self.color_texture_multi_sampled)
            glDeleteTextures(1, self.screen_texture)
            glDeleteRenderbuffers(1, self.rbo)
        except:
            pass

    def prepare_buffer(self):
        self.bind()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) #we're not using the stencil buffer now
        glEnable(GL_DEPTH_TEST)

    def unbind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

    def bind_intermediate(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.intermediate_fbo)

    def blip(self):
        # 2. now blit multisampled buffer(s) to normal colorbuffer of intermediate FBO. Image is stored in screenTexture
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.fbo)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.intermediate_fbo)
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_COLOR_BUFFER_BIT, GL_NEAREST)
        glBlitFramebuffer(0, 0, self.width, self.height, 0, 0, self.width, self.height, GL_DEPTH_BUFFER_BIT, GL_NEAREST)


    def draw_buffer_to_screen(self):
        self.blip()
        glBindFramebuffer(GL_FRAMEBUFFER, 0) #back to default
        glDisable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        self.vbo.bind()
        glUseProgram(self.screen_shader)
        #glBindVertexArray(self.quadVAO)

        #glBindBuffer(GL_ARRAY_BUFFER, self.quadVBO)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(glGetAttribLocation(self.screen_shader, "aPos"), 2, GL_FLOAT, GL_FALSE, 16, self.vbo)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(glGetAttribLocation(self.screen_shader, "aTexCoords"), 2, GL_FLOAT, GL_FALSE, 16, self.vbo+8)
        glActiveTexture(GL_TEXTURE0 + 0)
        glBindTexture(GL_TEXTURE_2D, self.screen_texture)
        #glActiveTexture(GL_TEXTURE0 + 1)
        #glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        #self.texture2.bind()
        glDrawArrays(GL_TRIANGLES, 0, 6)
        self.vbo.unbind()
        glDisableVertexAttribArray(0)
        glDisableVertexAttribArray(1)
        glUseProgram(0)
        glActiveTexture(GL_TEXTURE0 + 0)

    def to_image(self):
        glBindTexture(GL_TEXTURE_2D, self.screen_texture)
        img_data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        glBindTexture(GL_TEXTURE_2D, 0)
        image = Image.new("A", (self.width, self.height))
        image.frombytes(img_data)
        return image

    def save_to_file(self, filename):
        image = ImageOps.flip(self.to_image())
        image.save(filename)
        print("save screenshot", filename)

