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
from ..geometry.splines import CatmullRomSpline, BSplineWrapper


class BSplineRenderer(ColoredGeometryRenderer):
    def __init__(self, controlPoints, r, g, b, granularity=100):
        ColoredGeometryRenderer.__init__(self)
        self.r = r
        self.g = g
        self.b = b
        self.vertex_array_type = GL_POINTS
        self.vertexList = []
        self.vbo = vbo.VBO(np.array([self.vertexList], 'f'))
        self.spline = BSplineWrapper(controlPoints)
        self.initiated = True
        self.granularity = granularity
        self.initiateControlPoints(controlPoints)

    def initiateControlPoints(self, controlPoints):
        self.numberOfSegments = len(controlPoints)-1
        # as a workaround add multiple points at the end instead of one
        self.controlPoints = [controlPoints[0]]+controlPoints+[controlPoints[-1], controlPoints[-1]]
        print("length of control point list ",len(self.controlPoints))
        print("number of segments ",self.numberOfSegments)

        for point in controlPoints:
                self.vertexList.append([point[0], point[1], point[2], self.r,self.g,self.b])
        self.numVertices= len(self.vertexList)
        self.vertexArray = np.array(self.vertexList,'f')
        self.vbo.set_array(np.array([self.vertexList],'f'))

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources=None):
       if self.initiated:
           glUseProgram(self.shader)
           try:
               self.vbo.bind()
               try:
                   #set MVP matrix
                   glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, modelMatrix)
                   glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, viewMatrix)
                   glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projectionMatrix)
                   #evaluate the spline
                   glBegin(GL_LINE_STRIP)
                    #the higher the granularity the smoother the curve
                   glColor3f(self.r,self.g,self.b)
                   u = np.arange(self.granularity+1) / float(self.granularity)
                   for i in u:
                      point = self.spline.queryPoint(i)
                      glVertex3f(point[0],point[1],point[2])
                   glEnd()

                   #We only have the two standard per-vertex attributes
                   glPointSize(5)
                   glEnableClientState(GL_VERTEX_ARRAY)
                   glEnableClientState(GL_COLOR_ARRAY)
                   glVertexPointer(3, GL_FLOAT, 24, self.vbo)
                   glColorPointer(3, GL_FLOAT, 24, self.vbo+12)
                   glDrawArrays(self.vertex_array_type, 0, self.numVertices)
                   glPointSize(1)
               except  GLerror as e:
                    #note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
                    print("error in ColoredGeometry",e)
               finally:
                   self.vbo.unbind()
                   glDisableClientState(GL_VERTEX_ARRAY)
                   glDisableClientState(GL_COLOR_ARRAY)
           finally:
               glUseProgram(0)
           glUseProgram(self.shader)


class CatmullRomSplineRenderer(ColoredGeometryRenderer, CatmullRomSpline):
    """  Spline that goes through control points, drawn using immediate mode instead of a shader
    has arc length mapping used by motion planning
    """
    def __init__(self, controlPoints, r, g, b, granularity=100):
        ColoredGeometryRenderer.__init__(self)
        self.r = r
        self.g = g
        self.b = b
        self.vertex_array_type = GL_POINTS
        self.vertexList = []
        self.vbo = vbo.VBO(np.array([self.vertexList], 'f'))

        CatmullRomSpline.__init__(self, controlPoints, dimensions=3, granularity=granularity)

    def initiateControlPoints(self,controlPoints):
        '''
        @param controlPoints array
        '''
        self.numberOfSegments = len(controlPoints)-1
        # as a workaround add multiple points at the end instead of one
        self.controlPoints = [controlPoints[0]]+controlPoints+[controlPoints[-1], controlPoints[-1]]
        #print("length of control point list ", len(self.controlPoints))
        #print("number of segments ", self.numberOfSegments)

        for point in controlPoints:
                self.vertexList.append([point[0], point[1], point[2], self.r, self.g, self.b])
        self.numVertices= len(self.vertexList)
        self.vertexArray = np.array(self.vertexList,'f')
        self.vbo.set_array(np.array( [self.vertexList],'f'))
        self.updateArcLengthMappingTable()

    def addPoint(self, point):
        #print("add point to spline", point)
        #add point replace auxiliary control points
        if self.initiated:
            del self.controlPoints[-2:]
            self.numberOfSegments = len(self.controlPoints)-1
            self.controlPoints += [point,point,point]
            #print(self.controlPoints)
            self.vertexList.append([point[0],point[1],point[2], self.r,self.g,self.b])
            self.numVertices += 1
            self.vbo.set_array(np.array([self.vertexList], 'f'))
            self.updateArcLengthMappingTable()
        else:
            self.initiateControlPoints([point,])
            self.initiated = True

    def clear(self):
        self.controlPoints = []
        self.vertexList = []
        self.initiated = False
        self.fullArcLength = 0
        self.numVertices = 0
        self.numberOfSegments = 0
        self.arcLengthMap = []

    def draw(self,modelMatrix, viewMatrix, projectionMatrix, lightSources=None):
        if len(self.controlPoints) < 2:
            return
        self.technique.prepare(modelMatrix,viewMatrix,projectionMatrix)
        try:
            self.vbo.bind()
            glBegin(GL_LINE_STRIP)
            #the higher the granularity the smoother the curve
            glColor3f(self.r, self.g, self.b)
            for i in np.arange(self.granularity+1) / float(self.granularity):
               point = self.queryPoint(i)
               glVertex3f(point[0],point[1],point[2])
            glEnd()
            glPointSize(5)
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_COLOR_ARRAY)
            glVertexPointer(3, GL_FLOAT, 24, self.vbo)
            glColorPointer(3, GL_FLOAT, 24, self.vbo+12)
            glDrawArrays(self.vertex_array_type, 0, self.numVertices)
            glPointSize(1)
        except GLerror as e:#http://pyopengl.sourceforge.net/documentation/opengl_diffs.html
            #note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
            print("error in ColoredGeometry",e)#, self.modelMatrix
        finally:
           self.vbo.unbind()
           glDisableClientState(GL_VERTEX_ARRAY)
           glDisableClientState(GL_COLOR_ARRAY)
        self.technique.stop()


class BezierSplineRenderer(ColoredGeometryRenderer):
    """ Bezier spline code based on http://www.nongnu.org/pyformex/
        uses immediate mode to draw the spline. best option would be to use a spline geometry shader http://www.computer-graphics.se/TSBK07-files/PDF12/13g.pdf
    """
    def __init__(self, controlPoints, r, g, b, granularity=100):
        ColoredGeometryRenderer.__init__(self)
        self.r = r
        self.g = g
        self.b = b
        self.vertex_array_type = GL_POINTS
        vertexList = []
        for point in controlPoints:
             vertexList.append([point.x, point.y, point.z, r, g, b])
        self.numVertices = len(vertexList)
        self.vertexArray = np.array(vertexList, 'f')
        self.vbo = vbo.VBO(self.vertexArray)
        self.granularity = granularity
        #start,end,distance between points in array for pointer arithmetic,numpy array with shape [n][3] where n is the number of control points
        glMap1f(GL_MAP1_VERTEX_3, 0.0, 1.0,self.vertexArray)#  http://wiki.delphigl.com/index.php/glMap1
        colorArray = np.array([[r,g,b,1.0],],'f')
        glMap1f(GL_MAP1_COLOR_4,0.0,1.0,colorArray)

    def draw(self, viewMatrix, projectionMatrix):
       glUseProgram(self.shader)
       try:
           self.vbo.bind()
           try:
               glUniformMatrix4fv(self.modelMatrix_loc, 1, GL_FALSE, self.modelMatrix)
               glUniformMatrix4fv(self.viewMatrix_loc, 1, GL_FALSE, viewMatrix)
               glUniformMatrix4fv(self.projectionMatrix_loc, 1, GL_FALSE, projectionMatrix)
               #evaluate the spline
               glEnable(GL_MAP1_VERTEX_3)
               glEnable(GL_MAP1_COLOR_4)
               glBegin(GL_LINE_STRIP)
               glColor3f(self.r,self.g,self.b)
               u = np.arange(self.granularity+1) / float(self.granularity)
               for i in u:
                  glEvalCoord1f(i)
               glEnd()
               glDisable(GL_MAP1_VERTEX_3)
               glDisable(GL_MAP1_COLOR_4)
               #We only have the two standard per-vertex attributes
               glPointSize(5)
               glEnableClientState(GL_VERTEX_ARRAY)
               glEnableClientState(GL_COLOR_ARRAY)
               glVertexPointer(3, GL_FLOAT, 24, self.vbo)
               glColorPointer(3, GL_FLOAT, 24, self.vbo+12)
               glDrawArrays(self.vertex_array_type, 0, self.numVertices)
               glPointSize(1)
           except  GLerror as e:
                #note: type errors at this point can also hint on missing uniform locations in the shader or simply on a shader that is inaccessible for the current thread and therefore has no uniform locations
                print("error in ColoredGeometry",e, self.modelMatrix)
           finally:
               self.vbo.unbind()
               #Need to cleanup, as always.
               glDisableClientState(GL_VERTEX_ARRAY)
               glDisableClientState(GL_COLOR_ARRAY)
       finally:
           glUseProgram(0)
       glUseProgram(self.shader)
