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
from OpenGL.GL import *
from OpenGL.arrays import vbo
from .techniques import ColorSkinningTechnique


def create_line_data_from_skeleton(skeleton, joint_names, data, joint_name):
    idx = joint_names.index(joint_name)
    for c in skeleton.nodes[joint_name].children:
        line_start = [0.0, 0.0, 0.0, idx, -1, -1, -1, 1.0, 0.0, 0.0, 0.0]
        data.append(line_start)
        line_end = list(c.offset) + [idx, -1, -1, -1, 1.0, 0.0, 0.0, 0.0]
        data.append(line_end)
        if c.node_name in joint_names:
            create_line_data_from_skeleton(skeleton, joint_names, data, c.node_name)


class DebugSkeletonRenderer(object):
    def __init__(self, skeleton, joint_names, color):
        self.technique = ColorSkinningTechnique(color)
        self.vertex_array_type = GL_LINES
        data = []
        create_line_data_from_skeleton(skeleton, joint_names, data, skeleton.root)
        data = np.array(data, 'f')
        self.vbo = vbo.VBO(data)
        self.n_vertices = len(data)

    def set_color(self, color):
        self.technique.set_color(color)

    def set_matrices(self, matrices):
        self.technique.set_matrices(matrices)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix)
        self.technique.use(self.vbo, self.vertex_array_type, self.n_vertices)
        self.technique.stop()

