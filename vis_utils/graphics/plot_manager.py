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
import collections
from .renderer.pylab_plot_renderer import LinePlotRenderer, ImgPlotRenderer, AnnotationRenderer, TickRenderer


class PlotManager(object):
    def __init__(self, width, height, dpi=100, padding=5):
        self.min_pos = [0,0]
        self.z = -5
        self.scale = 1
        self.plots = collections.OrderedDict()
        self.size = dict()
        self.pos = dict()

        self.dpi = dpi
        self.padding = padding
        self.width = width
        self.height = height
        self.tick = None

    def add_plot(self, name, size, pos=None):
        self.plots[name] = LinePlotRenderer(size)
        self.size[name] = size
        self.pos[name] = pos
        #self.positions[name] = [self.width-size[0]*self.dpi, self.min_pos[1]]
        #self.min_pos[1] += size[1] * self.dpi + self.padding

    def add_img_plot(self, name, size, pos=None):
        self.plots[name] = ImgPlotRenderer(size)
        self.size[name] = size
        self.pos[name] = pos
        #self.positions[name] = [self.width-size[0]*self.dpi, self.min_pos[1]]
        #self.min_pos[1] += size[1] * self.dpi + self.padding

    def add_annotation(self, name, size, anim_time, pos=None):
        self.plots[name] = AnnotationRenderer(name, np.array(size))
        self.size[name] = size
        self.pos[name] = pos
        color = [1,0.0,0]
        size = np.array([5, 160])
        start, end = 15, 280
        offset = 40
        speed = float(end-start)/anim_time
        self.tick = TickRenderer(self.z+1, size, color, start, end, offset, speed)

    def update_tick(self, dt):
        if self.tick is not None:
            self.tick.update(dt)

    def add_line(self, name, key, color):
        if name in self.plots:
            self.plots[name].add_line(key, color)

    def draw(self, orthographic_matrix):
        min_pos = np.array([0,0])
        for key in self.plots:
            pos = self.pos[key]
            if pos is None:
                pos = [self.width - self.size[key][0] * self.dpi, min_pos[1]]
            self.plots[key].draw(orthographic_matrix, pos, self.z, self.scale)
            min_pos[1] += self.size[key][1] * self.dpi + self.padding
        if self.tick is not None:
            self.tick.draw(orthographic_matrix)

    def update_data(self, plot_name, key, p):
        if plot_name in self.plots:
            self.plots[plot_name].update_data(key, p)

    def set_img_data(self, plot_name, data):
        if plot_name in self.plots:
            self.plots[plot_name].set_data(data)

    def set_annotation_data(self, plot_name, data, cmap):
        if plot_name in self.plots:
            self.plots[plot_name].set_annotation_data(data, cmap)
        return

    def plot_data(self):
        for plot_name in self.plots:
            self.plots[plot_name].plot_data()

    def clear_canvas(self):
        for name in self.plots:
            self.plots[name].clear_canvas()

    def clear_data(self):
        for name in self.plots:
            self.plots[name].clear_data()

    def save_to_file(self, plot_name, file_name):
        if plot_name in self.plots:
            self.plots[plot_name].save_to_file(file_name)

    def resize(self, w, h):
        self.width = w
        self.height = h

