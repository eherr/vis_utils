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
from math import cos, sin, radians
import numpy as np


def get_rotation_around_x(alpha):
    cx = cos(alpha)
    sx = sin(alpha)
    #Note vectors represent columns
    m = np.array([[1.0 , 0.0, 0.0, 0.0],
                    [0.0, cx ,  sx,0.0],
                    [0.0, -sx,  cx,0.0],
                    [0.0,0.0,0.0,1.0]],np.float32)
    return m


def get_rotation_around_y(beta):
    cy = cos(beta)
    sy = sin(beta)
    #Note vectors represent columns
    m = np.array([[ cy,0.0,-sy ,0.0],
                    [0.0,1.0,0.0,0.0],
                    [ sy,0.0,cy,0.0],
                    [0.0,0.0,0.0,1.0]],np.float32)
    return m


def get_rotation_around_z(gamma):
    cz = cos(gamma)
    sz = sin(gamma)
    #Note vectors represent columns
    m = np.array([[ cz, sz,0.0,0.0],
                    [ -sz, cz,0.0,0.0],
                    [0.0,0.0,1.0,0.0],
                    [0.0,0.0,0.0,1.0]],np.float32)
    return m


def get_rotation_matrix(euler, order):
    e = np.radians(euler)
    m = np.eye(4)
    idx = 0
    while idx < len(order):
        if order[idx] == 'X':
            m = np.dot(get_rotation_around_x(e[0]), m)
        elif order[idx] == 'Y':
            m = np.dot(get_rotation_around_y(e[1]), m)
        elif order[idx] == 'Z':
            m = np.dot(get_rotation_around_z(e[2]), m)
        idx += 1
    return m

#vectors represent columns
def get_translation_matrix(translation):
    translationMatrix = np.array([[1.0, 0.0, 0.0, 0.0],
                           [ 0.0, 1.0, 0.0, 0.0],
                           [ 0.0, 0.0, 1.0, 0.0],
                           [translation[0],translation[1], translation[2], 1.0]], np.float32)
    return translationMatrix

 #vectors represent columns
def get_scale_matrix(scaleFactor):
    scaleMatrix =np.array([[scaleFactor, 0.0, 0.0, 0.0],
                             [ 0.0, scaleFactor, 0.0, 0.0],
                             [ 0.0, 0.0, scaleFactor, 0.0],
                             [0.0,0.0, 0.0, 1.0]], np.float32)
    return scaleMatrix


def get_matrix_from_pos_and_angles(pos,euler,order):
    m= get_rotation_matrix(euler,order)
    m[3,:] = np.array([pos[0],pos[1],pos[2],1.0])
    return m


#http://planning.cs.uiuc.edu/node104.html
# order roll by gamma, pitch by beta, yaw by alpha and translate by x,y,u
def homogeneousTransformationMatrix3D(alpha,beta,gamma,x,y,z):
    m11 = cos(alpha)*cos(beta)
    m12 = cos(alpha)*cos(beta)*sin(gamma) - sin(alpha)*cos(gamma)
    m13 = cos(alpha)*sin(beta)*cos(gamma) + sin(alpha)*cos(gamma)
    m14 = x

    m21 = sin(alpha)*cos(beta)
    m22 = sin(alpha)*sin(beta)*sin(gamma) + cos(alpha) *cos(alpha)
    m23 = sin(alpha)*sin(beta)*cos(gamma) - cos(alpha) * sin(gamma)
    m24 = y

    m31 = -sin(beta)
    m32 = cos(beta) * sin(gamma)
    m33 = cos(beta) * cos(gamma)
    m34 = z

    m41 = 0
    m42 = 0
    m43 = 0
    m44 = 1
    matrix = np.array([m11,m12,m13,m14],[m21,m22,m23,m24],[m31,m32,m33,m34],[m41,m42,m43,m44])
    return matrix



