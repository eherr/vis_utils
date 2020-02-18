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
from abc import ABCMeta, abstractmethod
from .techniques import ColorTechnique, ShadingTechnique, PhongShadingTechnique,\
    DirectionalShadingTechnique, TextureTechnique, DirectionalShadingIndexTechnique,\
    ShadedTextureTechnique, SkinningShadingTechnique, TerrainTechnique


class GeometryRenderer(object, metaclass=ABCMeta):
    @abstractmethod
    def draw(self, viewMatrix, projectionMatrix): pass


class ColoredGeometryRenderer(GeometryRenderer):
    '''
    abstract base class that provides methods use an OpenGL Shader to draw geometry. It needs to be inherited by a class that creates and fills a Vertex Buffer Object (self.vbo)
    based on a tutorial https://www.youtube.com/watch?v=msHV_y-RmaI
    '''
    def __init__(self):
        self.technique = ColorTechnique()

    def draw(self, m, v, p):
        self.technique.prepare(m,v,p)
        self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
        self.technique.stop()


class ShadedGeometryRenderer(GeometryRenderer, metaclass=ABCMeta):
    '''
    abstract base class that provides methods use an OpenGL Shader to draw geometry. It needs to be inherited by a class that creates and fills a Vertex Buffer Object (self.vbo)
    '''

    def __init__(self):
        self.technique = ShadingTechnique()

    def draw(self, modelMatrix,viewMatrix,projectionMatrix):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix)
        self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
        self.technique.stop()


class PhongShadedGeometryRenderer(GeometryRenderer, metaclass=ABCMeta):
     '''
     abstract base class that provides methods use an OpenGL Shader to draw geometry. It needs to be inherited by a class that creates and fills a Vertex Buffer Object (self.vbo)
     based on a tutorial https://www.youtube.com/watch?v=msHV_y-RmaI
     '''

     def __init__(self, material):
         self.technique = PhongShadingTechnique(material)

     def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
         self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
         self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
         self.technique.stop()


class DirectionalShadedGeometryRenderer(GeometryRenderer, metaclass=ABCMeta):
    def __init__(self, material):
        self.technique = DirectionalShadingTechnique(material)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
        self.technique.stop()


class SkinnedMeshRenderer(GeometryRenderer, metaclass=ABCMeta):
    def __init__(self, material):
        self.technique = SkinningShadingTechnique(material)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources, boneMatrices):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources, boneMatrices)
        self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
        self.technique.stop()


class TexturedGeometryRenderer(GeometryRenderer, metaclass=ABCMeta):
    def __init__(self, material):
        self.technique = TextureTechnique(material)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
        self.technique.stop()


class ShadedTexturedRenderer(GeometryRenderer, metaclass=ABCMeta):
    def __init__(self, material):
        self.technique = ShadedTextureTechnique(material)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
        self.technique.stop()


class DirectionalShadedIndexRenderer(GeometryRenderer, metaclass=ABCMeta):
    def __init__(self, material):
        self.technique = DirectionalShadingIndexTechnique(material)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vertices, self.indices, self.vertex_array_type, self.numIndices)
        self.technique.stop()
