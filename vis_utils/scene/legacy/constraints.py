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
from ...graphics.renderer import splines, lines
from ..scene_object import SceneObject
from ...graphics import renderer, materials
from ...graphics.utils import get_translation_matrix


class KinematicConstraint():  
    def __init__(self,graphWalkIndex,frameNumber,jointName,position,action = None):
        self.jointName = jointName
        self.position = position
        self.frameNumber = frameNumber
        self.graphWalkIndex = graphWalkIndex
        self.action = action


class ConstraintObject(SceneObject):
    def __init__(self):
        SceneObject.__init__(self)


class SplineObject(ConstraintObject):
    def __init__(self,controlPoints,r,g,b):
        ConstraintObject.__init__(self)
        self.name = "spline"+str(self.node_id)
        self.spline = splines.CatmullRomSplineRenderer(controlPoints, r, g, b)

    def addControlPoint(self,point):
        self.spline.addPoint(point)

    def clear(self):
        self.spline.clear()

    def getFullArcLength(self):
        return self.spline.fullArcLength#getFullArcLength()

    def getPointAtAbsoluteArcLength(self,absoluteArcLength):
        return self.spline.getPointAtAbsoluteArcLength(absoluteArcLength)

    def getLastControlPoint(self):
        return self.spline.getLastControlPoint()

    def getDistanceToPath(self,absoluteArcLength,position):
        return self.spline.getDistanceToPath(absoluteArcLength,position)

    def draw(self,viewMatrix,projectionMatrix,lightSources):
        self.spline.draw(self.transformation,viewMatrix, projectionMatrix)

class BSplineObject(ConstraintObject):
    def __init__(self,controlPoints,r,g,b):
        ConstraintObject.__init__(self)
        self.spline = splines.BSplineRenderer(controlPoints, r, g, b)

    def draw(self,viewMatrix,projectionMatrix,lightSources):
        self.spline.draw(self.transformation,viewMatrix, projectionMatrix)


class PositionConstraintObject(ConstraintObject):
    def __init__(self, position, radius):
        ConstraintObject.__init__(self)
        self.name = "position constraint"+str(self.node_id)
        self.scale = radius*2
        self.visualization = renderer.SphereRenderer(20, 20, radius, material=materials.red)
        self.coordinateSystem = lines.CoordinateSystemRenderer(self.scale)
        self.controlKnobX = renderer.SphereRenderer(20, 20, 0.5, material=materials.red)
        self.controlKnobY = renderer.SphereRenderer(20, 20, 0.5, material=materials.green)
        self.controlKnobZ = renderer.SphereRenderer(20, 20, 0.5, material=materials.blue)
        self.setPosition(position)
        self.active = False

    def setPosition(self,position):
        self.position = position
        self.transformation = get_translation_matrix(self.position)
        self.xKnobPosition = self.position + self.scale * np.array([1.0,0.0,0.0])
        self.yKnobPosition = self.position + self.scale * np.array([0.0,1.0,0.0])
        self.zKnobPosition = self.position + self.scale * np.array([0.0,0.0,1.0])
        self.xKnobTransformation = get_translation_matrix(self.xKnobPosition)
        self.yKnobTransformation = get_translation_matrix(self.yKnobPosition)
        self.zKnobTransformation = get_translation_matrix(self.zKnobPosition)


    def draw(self,viewMatrix,projectionMatrix,lightSources):
        self.visualization.draw(self.transformation, viewMatrix, projectionMatrix, lightSources)
        if self.active:
            self.coordinateSystem.draw(self.transformation,viewMatrix,projectionMatrix)
            self.controlKnobX.draw(self.xKnobTransformation,viewMatrix, projectionMatrix, lightSources)
            self.controlKnobY.draw(self.yKnobTransformation,viewMatrix, projectionMatrix, lightSources)
            self.controlKnobZ.draw(self.zKnobTransformation,viewMatrix, projectionMatrix, lightSources)

    def selectAxis(self, rayStart, rayDir):
        rayStart = vec3(rayStart.x, rayStart.y, rayStart.z)
        rayDir = vec3(rayDir.x,rayDir.y,rayDir.z)
        axisName = ""
        intersectionList =[]
        xResult = self.controlKnobX.intersectRay(self.xKnobPosition, rayStart, rayDir)
        if xResult[0]:
            intersectionList.append(('X',xResult))
        yResult = self.controlKnobY.intersectRay(self.yKnobPosition, rayStart, rayDir)
        if yResult[0]:
            intersectionList.append(('Y',yResult))
        zResult = self.controlKnobZ.intersectRay(self.zKnobPosition, rayStart, rayDir)
        if zResult[0]:
            intersectionList.append(('Z',zResult))
        minIndex = -1
        minDistance = 10000.0
        for i in range(len(intersectionList)):
            #find intersection with least distance to the start
            if intersectionList[i][1][2] < minDistance:
                minIndex = i
                minDistance = intersectionList[i][1][2]

        if minIndex >-1:
             print(intersectionList[minIndex][0],intersectionList[minIndex][1])
             axisName = intersectionList[minIndex][0]

        return axisName


class ControlKnobObject(SceneObject):
    def __init__(self, slices=20, stacks=20, radius=1.0, color=None):
        SceneObject.__init__(self)
        self.active = False
        self.slices = slices
        self.stacks = stacks
        self.radius = radius
        self.positon = [0,0,0]
        self.visualization = Renderer.SphereRenderer(self.slices, self.stacks, self.radius, color=color)#None

    def setPosition(self,position):
        self.position = position
        self.transformation = get_translation_matrix(self.position)

    def draw(self,viewMatrix,projectionMatrix,lightSources):
        if self.active:
            #print "draw"
            self.visualization.draw(self.transformation,viewMatrix,projectionMatrix,lightSources)

    def intersectRay(self,rayStart,rayDir):
        return self.visualization.intersectRay(self.position,rayStart,rayDir)


class MarkerObject(SceneObject):
    def __init__(self, position, color, scale=1.0):
        SceneObject.__init__(self)
        self.position = position
        self.visualization = splines.MarkerRenderer(position, color, scale)
        self.active = False

    def draw(self, viewMatrix, projectionMatrix, lightSources):
        if self.active:
            self.visualization.set_position(self.position)
            self.visualization.draw(self.transformation, viewMatrix, projectionMatrix)#note the position is written into the vertex buffer object


class KinematicConstraintObject(SceneObject, KinematicConstraint):
    def __init__(self, jointName, position, graphWalkIndex, frameNumber, skeletonScaleFactor, action,
                 visualize=False):
        """ note: the position must be given without the skeletonScaleFactor applied to it, because it is only used for the visualization
        """
        SceneObject.__init__(self)
        KinematicConstraint.__init__(self, graphWalkIndex, frameNumber, jointName, position,
                                                          action)
        self.transformation = get_translation_matrix(self.position * skeletonScaleFactor)  # apply skeleton scale factor only for visualization transform
        self.visualize = visualize
        self.skeletonScaleFactor = skeletonScaleFactor
        if self.visualize:
            self.visualization = Renderer.SphereRenderer(20, 20, 1.0, material=materials.red)
        else:
            self.visualization = None

    def draw(self, viewMatrix, projectionMatrix, lightSources):
        if self.visualize:
            self.visualization.draw(self.transformation, viewMatrix, projectionMatrix, lightSources)
        return
