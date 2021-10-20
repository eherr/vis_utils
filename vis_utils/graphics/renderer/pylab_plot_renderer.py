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
"""
http://www.pygame.org/wiki/MatplotlibPygame
https://stackoverflow.com/questions/29015999/pygame-opengl-how-to-draw-text-after-glbegin
"""
import matplotlib.backends.backend_agg as agg
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import imgui
from collections import deque
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
from .techniques import Technique, ColorTechnique
from ..shaders import ShaderManager


class PylabPlotter(object):
    def __init__(self, title, size, dpi=400, font_size=5):
        self.title = title
        self.size = size
        self.dpi = dpi
        self.fig = plt.figure(figsize=(size[0],size[1]), dpi=dpi)# 100 dots per inch, so the resulting buffer is 400x400 pixels
        self.canvas = agg.FigureCanvasAgg(self.fig)
        self.font_size = font_size


    def set_size(self, size):
        self.size = size
        self.fig = plt.figure(figsize=(size[0], size[1]),
                                dpi=self.dpi)  # 100 dots per inch, so the resulting buffer is 400x400 pixels
        self.canvas = agg.FigureCanvasAgg(self.fig)

    def clear_data(self):
        pass

    def clear_canvas(self):
        ax = self.fig.gca()
        ax.clear()

    def plot_data(self):
        pass

    def get_image(self):
        renderer = self.canvas.get_renderer()
        raw_data = renderer.buffer_rgba()
        return raw_data

    def get_size(self):
        return self.canvas.get_width_height()


class LinePylabPlotter(PylabPlotter):
    def __init__(self, title, size, data_length=100000, dpi=400, font_size=8):
        super().__init__(title, size, dpi, font_size)
        self.data = dict()
        self.colors = dict()
        self.data_length = data_length

    def clear_data(self):
        for key in self.data:
            self.data[key].clear()

    def add_line(self, key, color):
        self.data[key] = deque([], self.data_length)
        self.colors[key] = color

    def update_data(self, key, point):
        if key not in self.data:
            return
        self.data[key].append(point)

    def plot_data(self):
        ax = self.fig.gca()
        ax.clear()
        for key in self.data:
            #ax.set_xticklabels(ax.get_xticklabels(), font_dict)
            #ax.set_yticklabels(ax.get_yticklabels(), font_dict)
            for label in ax.get_yticklabels():
                label.set_fontsize(self.font_size) 
            for label in ax.get_xticklabels():
                label.set_fontsize(self.font_size) 
            ax.plot(self.data[key], c=self.colors[key], label=key)
            #plt.yticks(fontsize=self.font_size)
            #plt.xticks(fontsize=self.font_size)
            if len(self.data) > 1:
                ax.legend(loc='upper left', fontsize=self.font_size)
            ax.get_xaxis().set_visible(True)
            self.canvas.draw()

    def save_to_file(self, filename):
        max_len = 1
        for key in self.data:
            max_len = max(len(self.data[key]), max_len)
        scale = max_len/self.data_length
        size = [self.size[0] * scale,
                 self.size[1]]
        fig = plt.figure(figsize=(size[0], size[1]),
                                dpi=100)  # 100 dots per inch, so the resulting buffer is 400x400 pixels
        canvas = agg.FigureCanvasAgg(self.fig)
        ax = fig.gca()
        ax.clear()
        for key in self.data:
            ax.plot(self.data[key], c=self.colors[key])
        ax.get_xaxis().set_visible(True)
        canvas.draw()
        fig.savefig(filename+".png")
        print("saved to file", filename)


class IMGPylabPlotter(PylabPlotter):
    def __init__(self, title, size, dpi=100, font_size=5):
        super().__init__(title, size, dpi, font_size)
        self.data = None
        self.cb = None

    def clear_data(self):
        self.data = None

    def set_data(self, data):
        self.data = data

    def plot_data(self):
        print("plot img")
        if self.data is None:
            return
        ax = self.fig.gca()
        ax.clear()
        plt.imshow(self.data)
        if self.cb is not None:
            self.cb.remove()
        self.cb = plt.colorbar()
        self.cb.set_label('cost', rotation=270)
        self.canvas.draw()

    def save_to_file(self, filename):
        size = [self.size[0],
                self.size[1]]
        fig = plt.figure(figsize=(size[0], size[1]),
                           dpi=100)  # 100 dots per inch, so the resulting buffer is 400x400 pixels
        canvas = agg.FigureCanvasAgg(self.fig)
        ax = fig.gca()
        ax.clear()
        plt.imshow(self.data)
        cb = plt.colorbar()
        cb.set_label('cost', rotation=270)
        canvas.draw()
        fig.savefig(filename + ".png")
        print("saved to file", filename)


class AnnotationPylabPlotter(PylabPlotter):
    def __init__(self, name, size, dpi=100, font_size=5):
        self.size = size
        self.fig = plt.figure(figsize=(size[0], size[1]),
                                dpi=dpi)  # 100 dots per inch, so the resulting buffer is 400x400 pixels
        self.canvas = agg.FigureCanvasAgg(self.fig)
        self.font_size = font_size
        self.data = None
        self.cmap = None
        self.dpi = dpi
        self.name = name

    def clear_data(self):
        self.data = None

    def set_annotation_data(self, data, cmap):
        self.data = data
        self.cmap = cmap

    def plot_data(self):
        """ https://matplotlib.org/users/tight_layout_guide.html"""
        print("plot img")
        if self.data is None:
            return
        idx =1

        self.fig = plt.figure(figsize=(self.size[0], self.size[1]),
                              dpi=self.dpi)  # 100 dots per inch, so the resulting buffer is 400x400 pixels
        self.canvas = agg.FigureCanvasAgg(self.fig)
        self.fig.patch.set_facecolor('red')
        self.fig.patch.set_alpha(0.0)
        n_plots = len(self.data)
        gs1 = gridspec.GridSpec(n_plots, 1)
        for key, v in self.data.items():
            ax = self.fig.add_subplot(gs1[idx-1])
            #ax = self.fig.add_subplot(idx, 111)

            ax.clear()
            plt.imshow(v, self.cmap)
            cb = plt.colorbar()
            if cb is not None:
                cb.remove()
            ax.xaxis.set_label_position("top")
            plt.xlabel(key)
            for xlabel_i in ax.get_yticklabels():
                xlabel_i.set_fontsize(0.0)
                xlabel_i.set_visible(False)
            for xlabel_i in ax.get_xticklabels():
                xlabel_i.set_fontsize(0.1)
            idx+=1
        gs1.tight_layout(self.fig)
        self.canvas.draw()

    def save_to_file(self, filename):
        size = [self.size[0],
                self.size[1]]
        fig = plt.figure(figsize=(size[0], size[1]),
                           dpi=100)  # 100 dots per inch, so the resulting buffer is 400x400 pixels
        canvas = agg.FigureCanvasAgg(self.fig)
        ax = fig.gca()
        ax.clear()
        plt.imshow(self.data)
        canvas.draw()
        fig.savefig(filename + ".png")
        print("saved to file", filename)

class PlotterTechnique(Technique):
    def __init__(self, plotter):
        self.plotter = plotter
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
        self.texture_id = glGenTextures(1)
        glUseProgram(self.shader)
        return self.update_texture()

    def set_size(self, size):
        self.plotter.set_size(size)

    def get_size(self):
        return np.array(self.plotter.get_size())

    def update_texture(self, bind=True):
        image = self.plotter.get_image()
        size = self.plotter.get_size()
        if bind:
            glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        n_dims = size[0]*size[1]
        #img_dta = list(struct.unpack(str(n_dims)+"i", image))
        #for i in range(n_dims):img_dta[i] = 0
        #image = struct.pack(str(n_dims)+"i", *img_dta)
        #print(img_dta)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, size[0], size[1], 0, GL_RGBA, GL_UNSIGNED_INT_8_8_8_8_REV , image)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        if bind:
            glUniform1i(self.tex_loc, 0)

    def stop(self):
        glUseProgram(0)

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


class PlotRenderer(object):
    def __init__(self, title):
        self.title = title
        self.technique = None
        self.vertex_array_type = GL_QUADS
        vertices = []
        self._vbo = vbo.VBO(np.array(vertices,'f'))
        self.n_vertices = len(vertices)
        self.scale = 1
        self.is_drawn = False

    def set_size(self,size):
        self.technique.set_size(size)

    def clear_canvas(self):
        self.technique.plotter.clear_canvas()

    def clear_data(self):
        self.technique.plotter.clear_data()

    def plot_data(self):
        self.technique.plotter.plot_data()
        self.technique.update_texture(False)

    def save_to_file(self, filename):
        self.technique.plotter.save_to_file(filename)

    def draw(self, orthographic_matrix, top_left, z, wscale=1.0):
        # https://stackoverflow.com/questions/10630823/how-to-get-texture-coordinate-to-glsl-in-version-150
        self.technique.prepare(orthographic_matrix)
        self.technique.update_texture()
        size = self.technique.get_size()
        min_pos = top_left
        max_pos = top_left + size*wscale
        vertices = [[min_pos[0], max_pos[1], z, 0, self.scale],
                    [max_pos[0], max_pos[1], z, self.scale, self.scale],
                    [max_pos[0], min_pos[1], z, self.scale, 0],
                    [min_pos[0], min_pos[1], z, 0, 0],
                    ]
        self.n_vertices = len(vertices)
        self._vbo.set_array(np.array(vertices, 'f'))
        self.technique.use(self._vbo, self.vertex_array_type, self.n_vertices)
        self.technique.stop()
        return max_pos

    def render_imgui(self):
        imgui.begin(self.title,True)
        size = self.technique.get_size()
        if self.is_drawn and imgui.is_mouse_clicked() and False:
            new_size = imgui.get_window_size()
            if new_size[0] != size[0] or new_size[1] != size[1]:
                size = new_size
                self.set_size((size[0], size[1]))
                #print("sets",self.technique.get_size(), (size[0], size[1]))
        size = self.technique.get_size()
        if self.is_drawn:
            size = imgui.get_window_size()
        imgui.image(self.technique.texture_id, size[0], size[1])
        imgui.end()
        self.is_drawn = True


class LinePlotRenderer(PlotRenderer):
    def __init__(self, title, size, font_size=5):
        super().__init__(title)
        self.technique = PlotterTechnique(LinePylabPlotter(title, size, font_size=font_size))

    def add_line(self, key, color):
        self.technique.plotter.add_line(key, color)

    def has_line(self, key):
        return key in self.technique.plotter.data

    def update_data(self, key, point):
        self.technique.plotter.update_data(key, point)

    def clear_data(self):
        self.technique.plotter.clear_data()


class ImgPlotRenderer(PlotRenderer):
    def __init__(self, title, size):
        super().__init__(title)
        self.technique = PlotterTechnique(IMGPylabPlotter(title, size))

    def set_data(self, data):
        self.technique.plotter.set_data(data)

    def clear_data(self):
        self.technique.plotter.clear_data()


class AnnotationRenderer(PlotRenderer):
    def __init__(self, name, size):
        super().__init__(name)
        self.technique = PlotterTechnique(AnnotationPylabPlotter(name, size))

    def set_annotation_data(self, data, cmap):
        self.technique.plotter.set_annotation_data(data, cmap)

    def clear_data(self):
        self.technique.plotter.clear_data()





class TickRenderer(object):
    def __init__(self, z, size, color, start_pos, end_pos,offset,speed = 0.102):
        self.technique = ColorTechnique()
        self.vertex_array_type = GL_QUADS
        vertices = []
        self._vbo = vbo.VBO(np.array(vertices,'f'))
        self.n_vertices = len(vertices)
        self.model_matrix = np.eye(4)
        self.view_matrix = np.eye(4)
        self.size = size
        self.r, self.g, self.b = color
        self.end_pos = end_pos
        self.start_pos = start_pos
        self.pos = self.start_pos
        self.offset = offset
        self.speed = speed

        top_left = np.array([0,0])
        min_pos = top_left
        max_pos = top_left + self.size
        vertices = [[min_pos[0], max_pos[1], z, self.r, self.g, self.b],
                    [max_pos[0], max_pos[1], z, self.r, self.g, self.b],
                    [max_pos[0], min_pos[1], z, self.r, self.g, self.b],
                    [min_pos[0], min_pos[1], z, self.r, self.g, self.b]
                    ]
        self.n_vertices = len(vertices)
        self._vbo.set_array(np.array(vertices, 'f'))

    def draw(self, orthographic_matrix):
        self.model_matrix[3, 0] = self.pos
        self.model_matrix[3, 1] = self.offset
        self.technique.prepare(self.model_matrix, self.view_matrix, orthographic_matrix)
        self.technique.use(self._vbo, self.vertex_array_type, self.n_vertices)
        self.technique.stop()


    def update(self, dt):
        self.pos += self.speed*dt
        if self.pos > self.end_pos:
            self.pos = self.start_pos
        return

    def reset(self):
        self.pos = self.start_pos
