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
from .base_types import ColoredGeometryRenderer


class DebugLineRenderer(ColoredGeometryRenderer):
    def __init__(self, start=None, end=None, color=None):
        super(DebugLineRenderer, self).__init__()
        if start is None:
            start = [0, 0, 0]
        if end is None:
            end = [0, 1, 0]
        if color is None:
            color = [1, 1, 1]
        self.numVertices = 2
        self.vertex_array_type = GL_LINES
        self.color = list(color)
        start = list(start)
        end = list(end)
        self.vbo = vbo.VBO(np.array([start + color, end + color], 'f'))

    def set_line(self, a, b, color=None):
        """#set points before drawing http://stackoverflow.com/questions/11125827/how-to-use-glbufferdata-in-pyopengl"""
        if color is not None:
            self.vbo.set_array(np.array([list(a)+list(color), list(b)+list(color)], 'f'))
        else:
            self.vbo.set_array(np.array([list(a) + self.color, list(b) + self.color], 'f'))

    def set_lines(self, points, color=None):
        vertices = []
        if color is not None:
            for idx in range(1, len(points)):
                vertices += list(points[idx-1]) + list(color)
                vertices += list(points[idx]) + list(color)
        else:
            for idx in range(1, len(points)):
                vertices += list(points[idx - 1]) + list(self.color)
                vertices += list(points[idx]) + list(self.color)
        print(vertices)
        self.numVertices = len(points)*2
        self.vbo.set_array(np.array(vertices, 'f'))



class CoordinateSystemRenderer(ColoredGeometryRenderer):
    def __init__(self, scale=1.0):
        super(CoordinateSystemRenderer, self).__init__()
        # self.position = position
        self.numVertices = 6
        self.vertex_array_type = GL_LINES
        self.vbo = vbo.VBO(
            np.array([
                [0, 0, 0, 1, 0, 0], [scale, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0], [0, scale, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1], [0, 0, scale, 0, 0, 1]], 'f'))


class ExtendingLineRenderer(ColoredGeometryRenderer):
    def __init__(self, r=1.0, g=1.0, b=1.0, maxLength=2000):
        ColoredGeometryRenderer.__init__(self)
        self.numVertices = 0
        self.points = []
        self.vertex_array_type = GL_LINES  # GL_LINE_STRIP
        self.r, self.g, self.b = r, g, b
        self.max_length = maxLength
        self.vbo = vbo.VBO(np.array([], 'f'))

    def addPoint(self, point):
        if self.numVertices > self.max_length:  # remove the first point
            self.points.pop(0)
            self.numVertices += 1
        self.points.append([point[0], point[1], point[2], self.r, self.g, self.b])
        self.numVertices += 1
        self.vbo.set_array(np.array(self.points, 'f'))

    def clear(self):
        self.points = []
        self.numVertices = 0


class ExtendingMarkerListRenderer(ColoredGeometryRenderer):
    # todo use other marker representation
    def __init__(self, r=1.0, g=1.0, b=1.0, maxLength=200):
        super(ExtendingMarkerListRenderer, self).__init__()
        self.numVertices = 0
        self.points = []
        self.vertex_array_type = GL_LINES
        self.r, self.g, self.b = r, g, b
        self.maxLength = maxLength
        self.scale = 1
        self.vbo = vbo.VBO(np.array([], 'f'))

    def addPoint(self, point):
        self.points.append([point.x, point.y + 0.5, point.z, self.r, self.g, self.b])
        self.points.append([point.x, point.y - 0.5, point.z, self.r, self.g, self.b])

        if self.numVertices < self.maxLength / 2:
            self.numVertices += 2
        else:
            self.points.pop(0)
            self.points.pop(0)
        self.vbo.set_array(np.array([self.points], 'f'))

    def add_direction(self, point, vec):
        self.points.append([point[0], point[1], point[2], self.r, self.g, self.b])
        self.points.append([point[0]+vec[0]*self.scale, point[1]+vec[1]*self.scale, point[2]+vec[2]*self.scale, self.r, self.g, self.b])

        if self.numVertices < self.maxLength / 2:
            self.numVertices += 2
        else:
            self.points.pop(0)
            self.points.pop(0)
        self.vbo.set_array(np.array([self.points], 'f'))

    def clear(self):
        self.points = []
        self.numVertices = 0


class WireframePlaneRenderer(ColoredGeometryRenderer):
    def __init__(self, width,depth,divisions,r,g,b, normal=[0.0,1.0,0.0,0.0]):
        ColoredGeometryRenderer.__init__(self)
        self.normal = normal
        self.width = width
        self.depth = depth
        self.numVertices = 8*divisions*4
        self.vertex_array_type = GL_LINES

        widthStep = width/divisions
        depthStep = depth/divisions
        startX = -width/2
        startZ = -depth/2
        vertexList = []
        x = 0
        while x < divisions:
            z = 0
            #todo change to use indices
            bottom = startX+widthStep*x
            while z < divisions:
                left = startZ +depthStep*z
                vertexList.append([ bottom, 0, left, r,g,b])
                vertexList.append([ bottom, 0, left+depthStep, r,g,b])
                vertexList.append([ bottom, 0, left+depthStep, r,g,b])
                vertexList.append([ bottom+widthStep, 0, left+depthStep, r,g,b])
                vertexList.append([ bottom+widthStep, 0, left+depthStep, r,g,b])
                vertexList.append([ bottom+widthStep, 0, left, r,g,b])
                vertexList.append([ bottom+widthStep, 0, left, r,g,b])
                vertexList.append([ bottom, 0, left, r,g,b])
                z += 1
            x +=1
        print((self.numVertices))
        print((len(vertexList)))
        self.numVertices = len(vertexList)
        vertexArray = np.array(vertexList,'f')
        self.vbo = vbo.VBO(vertexArray)

    def intersectRay(self, start, rayDir):
        l0 = start
        n = self.normal

        numerator = np.dot(-l0, n)
        denominator = np.dot(rayDir, n)
        if denominator != 0:
            d = numerator / denominator
            intersection = l0 + rayDir * d
            return intersection
        else:
            return None

class MarkerRenderer(DebugLineRenderer):
    def __init__(self, position, color, scale=1.0):
        line_start = position
        line_end = np.array(position) + [0,0.5*scale,0]
        DebugLineRenderer.__init__(self, line_start, line_end, color)
        self.scale = scale

    def set_position(self, position):
        line_start = np.array(position) - [0, 0.5 * self.scale, 0]
        line_end = np.array(position) + [0, 0.5 * self.scale, 0]
        self.set_line(line_start, line_end)