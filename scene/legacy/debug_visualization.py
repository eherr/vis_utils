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
from ...graphics.renderer import lines
from ...graphics.renderer import primitive_shapes
from ..scene_object import SceneObject
from ...graphics.utils import get_translation_matrix


class CoordinateSystemObject(SceneObject):
    def __init__(self, scale=1.0):
        SceneObject.__init__(self)
        #super(self, CoordinateSystemObject).__init__()
        self.visualization = lines.CoordinateSystemRenderer(scale)
        self.active = True

    def setPosition(self, position):
        self.transformation = get_translation_matrix(position)

    def draw(self, viewMatrix, projectionMatrix, lightSources):
        if self.active:
            self.visualization.draw(self.transformation, viewMatrix, projectionMatrix)


class PlaneObject(SceneObject):
    def __init__(self,width = 1000, depth =1000,segments =10, r =0.5,g=0.5,b=0.5):
        SceneObject.__init__(self)
        self.visualization = lines.WireframePlaneRenderer(width, depth, segments, r, g, b)

    def draw(self,viewMatrix,projectionMatrix,lightSources):
        self.visualization.draw(self.transformation,viewMatrix,projectionMatrix)

    def intersectRay(self,start,rayDir):
        return self.visualization.intersectRay(start,rayDir)


class TravelledPathObject(SceneObject):
    def __init__(self,r = 1.0,g = 1.0,b = 1.0,maxLength = 2000):
        SceneObject.__init__(self)
        self.line = lines.ExtendingLineRenderer(r, g, b, maxLength)

    def addPoint(self,point):
        self.line.addPoint(point)

    def clear(self):
        self.line.clear()

    def draw(self,viewMatrix,projectionMatrix,lightSources):
        self.line.draw(self.transformation,viewMatrix, projectionMatrix)


class PointCloudObject(SceneObject):

    def __init__(self):
        SceneObject.__init__(self)
        self.sphere = primitive_shapes.SphereRenderer(20, 20, 1.0, material=CustomShaders.redMaterial)
        self.transformations = []

        return

    def addPoint(self,point):
        print("got point", point)
        transformation = get_translation_matrix(point)
        self.transformations.append(transformation)


    def clear(self):
        self.transformations.clear()

    def draw(self,viewMatrix,projectionMatrix,lightSources):
        for transformation in self.transformations:
            self.sphere.draw(transformation,viewMatrix, projectionMatrix,lightSources)


class TravelledPathWithCorrespondencesObject(SceneObject):
    def __init__(self,r = 1.0,g = 1.0,b = 1.0,maxLength = 2000):
        SceneObject.__init__(self)
        self.line = lines.ExtendingLineRenderer(r, g, b, maxLength)
        self.correspondences = lines.ExtendingLineRenderer(1.0, 0.0, 0.0, maxLength * 2)

    def addPoint(self,point):
        self.line.addPoint(point)

    def addCorrespondence(self,point,correspondence):
        self.correspondences.addPoint(point)
        self.correspondences.addPoint(correspondence)

    def clear(self):
        self.line.clear()
        self.correspondences.clear()

    def draw(self,viewMatrix,projectionMatrix,lightSources):
        self.line.draw(self.transformation,viewMatrix, projectionMatrix)
        self.correspondences.draw(self.transformation,viewMatrix, projectionMatrix)


class TravelledPathWithMarkersObject(SceneObject):
    def __init__(self):
        SceneObject.__init__(self)
        self.line = lines.ExtendingLineRenderer(0.0, 1.0, 0.0)
        self.markers = lines.ExtendingMarkerListRenderer(1.0, 0.0, 0.0)

    def addMarker(self,point):
        self.markers.addPoint(point)

    def addPoint(self,point):
        self.line.addPoint(point)

    def clear(self):
        self.line.clear()
        self.markers.clear()

    def draw(self,viewMatrix,projectionMatrix,lightSources):
        self.line.draw(self.transformation,viewMatrix, projectionMatrix)
        self.markers.draw(self.transformation,viewMatrix, projectionMatrix)


class ListOfLocalCoordinateSystemsObject(SceneObject):
    def __init__(self,scaleFactor = 0.5):
        SceneObject.__init__(self)
        self.scaleFactor = scaleFactor
        self.coordinateSystems =[]

    def addCoordinateSystem(self,transformation):
        cs = lines.CoordinateSystemRenderer(scale = self.scaleFactor)
        print("transformation matrix",transformation.shape)
        self.coordinateSystems.append((cs,transformation))

    def clear(self):
        self.coordinateSystems = []

    def draw(self, viewMatrix, projectionMatrix, lightSources):
        for cs,transformation in self.coordinateSystems:
            #print "draw cs"
            cs.draw(transformation,viewMatrix, projectionMatrix)

