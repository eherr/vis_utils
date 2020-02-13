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
# -*- coding: utf-8 -*-


import numpy as np
import scipy.interpolate as si
import math
from .utils import closestLowerValueBinarySearch
    
B_SPLINE_DEGREE=3


class BSplineWrapper(object):
    def __init__(self,  points, degree=B_SPLINE_DEGREE, domain=None):
        self.points = np.array(points)
        if isinstance(points[0], (int, float, complex)):
            self.dimensions = 1
        else:
            self.dimensions = len(points[0])
        self.degree = degree
        if domain is not None:
            self.domain = domain
        else:
            self.domain = (0.0, 1.0)
 
        self.initiated = True
        self.spline_def = []
        points_t = np.array(points).T
        t_func = np.linspace(self.domain[0], self.domain[1], len(points)).tolist()
        for d in range(len(points_t)):
            #print d, self.dimensions
            self.spline_def.append(si.splrep(t_func, points_t[d], w=None, k=3))

    def _initiate_control_points(self):
        return

    def clear(self):
        return

    def queryPoint(self, u):
        """

        """
        point = []
        for d in range(self.dimensions):
            point.append(si.splev(u, self.spline_def[d]))
        return np.array(point)

    def get_last_control_point(self):
        return self.points[-1]

class BSpline(object):
    """
    http://demonstrations.wolfram.com/GeneratingABSplineCurveByTheCoxDeBoorAlgorithm/
    http://www.cs.mtu.edu/~shene/COURSES/cs3621/NOTES/spline/B-spline/bspline-basis.html
    """
    def __init__(self,  points, degree=3, domain=None):
        self.points = np.array(points)
        if isinstance(points[0], (int, float, complex)):
            self.dimensions = 1
        else:
            self.dimensions = len(points[0])
        self.degree = degree
        if domain is not None:
            self.domain = domain
        else:
            self.domain = (0.0, 1.0)
        self.knots = None
        self.initiated = False
        self._create_knots()

    def _initiate_control_points(self):
        return

    def clear(self):
        return

    def get_last_control_point(self):
        return self.points[-1]

    def _create_knots(self):
        """
        http://www.cs.mtu.edu/~shene/COURSES/cs3621/NOTES/spline/B-spline/bspline-curve.html
        #To change the shape of a B-spline curve, one can modify one or more of 
        #these control parameters: 
        #the positions of control points, the positions of knots, and the degree of the curve.
        # given n+1 control points and m+1 knots the following property must be true
        #m = n + p + 1. // p+1 = m-n
        # for a campled curve the last knot must be of multiplicity p+1
     
        If you have n+1 control points (n=9) and p = 3. 
        Then, m must be 13 so that the knot vector has 14 knots
         The remaining 14 - (4 + 4) = 6 knots can be anywhere in the domain. 
        U = { 0, 0, 0, 0, 0.14, 0.28, 0.42, 0.57, 0.71, 0.85, 1, 1, 1, 1 }. 
        how do find the knot points C(ui).
        """
        outer_knots = self.degree+1
        print("multiplicity", outer_knots)
        n = len(self.points) - 1 
        print("control points", len(self.points))
        print("n", n)
        p = self.degree
        m = n + p + 1
        n_knots = m + 1
        inner_knots = n_knots-(outer_knots*2 - 2)
        print("knots", n_knots)
        print("free knots", inner_knots)
        print("domain", self.domain)
        #print np.linspace(0.0, 1.0, 4)
        knots = np.linspace(self.domain[0], self.domain[1], inner_knots).tolist()
        #print self.knots
        self.knots = knots[:1] * (outer_knots-1) + knots +\
                    knots[-1:] * (outer_knots-1)
        print(self.knots)
        print(len(self.knots))
        self.initiated = True

    def queryPoint(self, u):
        """

        """
        return self.evaluate(u, algorithm="deboor")

    def evaluate(self, u, algorithm="standard"):
        #print "evaluate", u
        if self.domain[0] < u < self.domain[1]:
            if algorithm == "standard":
                value = 0.0#np.zeros(self.dim)
                n = len(self.points)
                w_list = []
                for i in range(n):
                    #i+=self.degree
                    #print "iteration",i, self.basis(u, i, self.degree)
                    #i = self.get_begin_of_knot_range(u)
                    w = self.basis(u, i, self.degree)
                    w_list.append(w)
                    #print temp
                    value += w * self.points[i]
                #print sum(w_list)
                return value
            elif algorithm == "deboor":
                i = self.get_begin_of_knot_range(u)
                #print u
                return self.deboor(self.degree, self.degree, u, i)
        elif u >= self.domain[1]:
            return self.points[-1]
        elif u <= self.domain[0]:
            return self.points[0]

    def basis(self, u, i, p):
        """http://devosaurus.blogspot.de/2013/10/exploring-b-splines-in-python.html
        """
        if p == 0:
            if self.knots[i] <= u < self.knots[i+1]:
                return 1.0
            else:
                return 0.0
        elif p >= 1:
            #print i+p
            #print "knot interval", i, i+p, self.knots[i+p]
            out = 0.0
            w_nom = (u-self.knots[i])
            w_denom  = (self.knots[i+p]-self.knots[i])
            if w_denom > 0.0:
                w = w_nom / w_denom
                out += w * self.basis(u, i, p-1)
                
            w_inv_nom = (self.knots[i+p+1] - u)
            w_inv_denom = (self.knots[i+p+1] - self.knots[i+1])
            if w_inv_denom > 0.0:
                w_inv = w_inv_nom / w_inv_denom
                out += w_inv * self.basis(u, i+1, p-1)
            return out
            
    def get_begin_of_knot_range(self, u):
        begin_of_range = 0        
        for i, u_i in enumerate(self.knots):
            if u_i < u:
                begin_of_range = i
            else:
                break
        #print "begin", begin_of_range
        return begin_of_range
                
    def deboor(self, k, p, u, i):
        """
        https://chi3x10.wordpress.com/2009/10/18/de-boor-algorithm-in-c/
        """
        if k == 0:
            return self.points[i]
        elif k >= 1:

            denom = (self.knots[i+p+1-k] - self.knots[i])
            if denom >0:
                alpha = (u-self.knots[i])/denom
                return (1-alpha) * self.deboor(k-1, p, u, i-1) \
                        + (alpha * self.deboor(k-1, p, u, i))
            else:
                return np.zeros(self.dimensions)


class CatmullRomSpline():
    '''
    spline that goes through control points with arc length mapping used by motion planning
    implemented using the following resources and examples:
    #http://www.cs.cmu.edu/~462/projects/assn2/assn2/catmullRom.pdf
    #http://algorithmist.net/docs/catmullrom.pdf
    #http://www.mvps.org/directx/articles/catmull/
    #http://hawkesy.blogspot.de/2010/05/catmull-rom-spline-curve-implementation.html
    #http://pages.cpsc.ucalgary.ca/~jungle/587/pdf/5-interpolation.pdf
    '''
    def __init__(self,controlPoints, dimensions, granularity=100):
        self.granularity = granularity
        #http://algorithmist.net/docs/catmullrom.pdf
        #base matrix to calculate one component of a point on the spline based on the influence of control points
        self.catmullRomBaseMatrix = np.array([[-1.0, 3.0, -3.0, 1.0],
                                              [2.0, -5.0, 4.0, -1.0],
                                              [-1.0, 0.0, 1.0, 0.0],
                                              [0.0, 2.0, 0.0, 0.0]])
        self.dimensions = dimensions
        self.fullArcLength = 0
        self.initiated = False
        self.controlPoints = []
        self.numberOfSegments = 0
        if len (controlPoints) >0:
            self.initiateControlPoints(controlPoints)
            self.initiated = True


    def initiateControlPoints(self,controlPoints):
        '''
        @param controlPoints array of class accessible by controlPoints[index][dimension]
        '''
        self.numberOfSegments = len(controlPoints)-1
        self.controlPoints = [controlPoints[0]]+controlPoints+[controlPoints[-1],controlPoints[-1]]#as a workaround add multiple points at the end instead of one
        print("length of control point list ",len(self.controlPoints))
        print("number of segments ",self.numberOfSegments)
        print("number of dimensions",self.dimensions)


        self.updateArcLengthMappingTable()

        return

    def addPoint(self,point):

        #add point replace auxiliary control points
        if  self.initiated:
            del self.controlPoints[-2:]
            self.numberOfSegments = len(self.controlPoints)-1#"-2 + 1
            self.controlPoints += [point,point,point]
            print(self.controlPoints)

            #update arc length mapping
            self.updateArcLengthMappingTable()
        else:
            self.initiateControlPoints([point,])
            self.initiated = True


    def clear(self):
        self.controlPoints = []
        self.initiated = False
        self.fullArcLength = 0
        self.numberOfSegments = 0
        self.arcLengthMap = []

    def transformByMatrix(self,matrix):
        '''
        matrix nxn transformation matrix where n is the number of dimensions of the catmull rom spline
        '''
        if self.dimensions < matrix.shape[0]:
            for i in range(len(self.controlPoints)):
                self.controlPoints[i] = np.dot(matrix, self.controlPoints[i])
        else:
            print("failed",matrix.shape)
        return

    def updateArcLengthMappingTable(self):
        '''
        creates a table that maps from parameter space of query point to relative arc length based on the given granularity in the constructor of the catmull rom spline
        http://pages.cpsc.ucalgary.ca/~jungle/587/pdf/5-interpolation.pdf
        '''
        self.fullArcLength = 0
        granularity = self.granularity
        u = np.arange(granularity+1) / float(granularity)
        lastPoint = None
        numberOfEvalulations = 0
        self.arcLengthMap = []
        for i in u:
            point = self.queryPoint(i)
            if lastPoint is not None:
                delta = []
                d = 0
                while d < self.dimensions:
                    delta.append(math.sqrt((point[d]-lastPoint[d])**2))
                    d += 1
                self.fullArcLength += np.sum(delta)#(point-lastPoint).length()
                #print self.fullArcLength
            self.arcLengthMap.append([i,self.fullArcLength])
            numberOfEvalulations+=1
            lastPoint= point

        # self.fullArcLength = arcLength
        #normalize values
        if self.fullArcLength > 0 :
            for i in range(numberOfEvalulations):
                self.arcLengthMap[i][1] /= self.fullArcLength


    def getFullArcLength(self, granularity = 100):
        #granularity = self.granularity
        u = np.arange(granularity+1) / float(granularity)
        arcLength = 0.0
        lastPoint = None
        for i in  u:
            print("sample",i)
            point = self.queryPoint(i)
            if lastPoint != None:
                arcLength += np.linalg.norm(point-lastPoint)#(point-lastPoint).length()
                lastPoint= point
                print(point)
        return arcLength

    def getDistanceToPath(self,absoluteArcLength, position):
        '''
        evaluates a point with absoluteArcLength on self to get a point on the path
        then the distance between the given position and the point on the path is returned
        '''
        pointOnPath = self.getPointAtAbsoluteArcLength(absoluteArcLength)
        return np.linalg.norm(position-pointOnPath)

    def getLastControlPoint(self):
        if len(self.controlPoints)> 0:
            return self.controlPoints[-1]
        else:
            return [0,0,0]

    def getArcLengthForParameter(self,t):
        stepSize = 1/self.granularity
        tableIndex = int(t/stepSize)
        return self.arcLengthMap[tableIndex][1]*self.fullArcLength



    def getPointAtAbsoluteArcLength(self,absoluteArcLength):
        point = np.zeros((1,self.dimensions))#source of bug
        if absoluteArcLength <= self.fullArcLength:
            # parameterize curve by arc length
            relativeArcLength = absoluteArcLength/self.fullArcLength
            point = self.queryPointByRelativeArcLength(relativeArcLength)
        else:
            return None
#         else:
#             raise ValueError('%f exceeded arc length %f' % (absoluteArcLength,self.fullArcLength))
        return point

    def findClosestValuesInArcLengthMap(self,relativeArcLength):
        '''
        - given a relative arc length between 0 and 1 it uses closestLowerValueBinarySearch from the Generic Algorithms module to search the self.arcLengthMap for the values bounding the searched value
        - returns floor parameter, ceiling parameter, floor arc length, ceiling arc length and a bool if the exact value was found
        '''
        foundExactValue = True
        result = closestLowerValueBinarySearch(self.arcLengthMap,0,len(self.arcLengthMap)-1,relativeArcLength, getter = lambda A,i: A[i][1])#returns the index and a flag value, requires a getter for the array

        index = result[0]

        if result[1] == 0:#found exact value
            floorP, ceilP = self.arcLengthMap[index][0],self.arcLengthMap[index][0]
            floorL, ceilL = self.arcLengthMap[index][1],self.arcLengthMap[index][1]
            foundExactValue = True
        elif result[1] ==1:#found lower value
            floorP = self.arcLengthMap[index][0]
            floorL = self.arcLengthMap[index][1]
            if index <len(self.arcLengthMap):#check array bounds
                ceilP = self.arcLengthMap[index+1][0]
                ceilL = self.arcLengthMap[index+1][1]
                foundExactValue = False
            else:
                foundExactValue = True
                ceilP= floorP
                ceilL = floorL
        elif result[1] ==2:#value smaller than smallest element in the array
            ceilP = self.arcLengthMap[index][0]
            floorL = self.arcLengthMap[index][1]
            floorP  = ceilP
            ceilL = floorL
            foundExactValue = True
        elif result[1] ==3:#value larger than largest element in the array
            ceilP = self.arcLengthMap[index][0]
            ceilL = self.arcLengthMap[index][1]
            floorP = ceilP
            floorL = ceilL
            foundExactValue = True
        #print relativeArcLength,floorL,ceilL,foundExactValue
        return floorP,ceilP,floorL,ceilL,foundExactValue

    #see slide 30 of http://pages.cpsc.ucalgary.ca/~jungle/587/pdf/5-interpolation.pdf
    #note it does a binary search so it is rather expensive to be called at every frame
    def queryPointByRelativeArcLength(self,relativeArcLength):

        floorP,ceilP,floorL,ceilL,foundExactValue = self.findClosestValuesInArcLengthMap(relativeArcLength)
        if not foundExactValue:
            alpha = (relativeArcLength-floorL)/(ceilL-floorL)#can be reused a-
            #t = floorL+alpha*(ceilL-floorL)
            t = floorP+alpha*(ceilP-floorP)
        else:
            t = floorP
        #t = relativeArcLength#todo add correct mapping

        return self.queryPoint(t)

    def mapToSegment(self,t):

        i =  min(math.floor( self.numberOfSegments *t),self.numberOfSegments)#the part of t before i
        localT =(self.numberOfSegments*t) -math.floor( self.numberOfSegments *t)#the rest, e.g. N = 10 and t = 0.62 => i = 6 and the rest is 0.02
        #i = min(i,self.numberOfSegments)
        return i+1,localT#increment i by 1 to ignore the first auxiliary control point


    def getControlPointVectors(self,i):
        i = int(i)
        #if i<=self.numberOfSegments-2:
        d = 0
        vectors = []

        while d < self.dimensions:
            v = [float(self.controlPoints[i-1][d]),float(self.controlPoints[i][d]),float(self.controlPoints[i+1][d]),float(self.controlPoints[i+2][d])]
            vectors.append(np.array(v))
            d+=1

        return vectors

#
    def queryPoint(self, t):
        i,localT = self.mapToSegment(t)
        weightVector = np.array([localT**3,localT**2,localT,1])
        controlPointVectors = self.getControlPointVectors(i)
        point =[]
        d =0
        while d < self.dimensions:
            point.append(self.queryValue(weightVector, controlPointVectors[d]))
            d += 1
        return np.array(point)

    def queryValue(self, weightVector, controllPointVector):
        v = np.dot(self.catmullRomBaseMatrix, controllPointVector)
        v = np.dot(weightVector, v)
        return 0.5 * v
