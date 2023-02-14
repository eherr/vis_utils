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
#===============================================================================
# author: Erik Herrmann (DFKI GmbH, FB: Agenten und Simulierte Realität)
# last update: 3.1.2014
#orbiting camera based on http://www.glprogramming.com/red/chapter03.html
#Horizontal Movement implementation based on
#http://www.youtube.com/watch?v=RInkwoCgIps
#http://www.youtube.com/watch?v=H20stuPG-To
#===============================================================================

import numpy as np
import numpy.linalg as la
import math
import transformations as trans
from ..graphics import utils

UP = np.array([0,1,0])
FORWARD = np.array([0,0,-1])



class BoundigBox(object):
    def __init__(self):
        self.min_v = np.zeros(3)
        self.max_v = np.zeros(3)
        self.min_v[:] = np.inf
        self.max_v[:] = -np.inf

    def update(self, p):
        for d in range(3):
            if p[d] < self.min_v [d]:
                self.min_v[d] = p[d]
            elif p[d] > self.max_v[d]:
                self.max_v[d] = p[d]

    def inside(self, p):
        inside = True
        for d in range(3):
            if p[d] < self.min_v[d]:
                inside = False
                break
            elif p[d] > self.max_v[d]:
                inside = False
                break
        return inside

class Camera(object):
    def __init__(self):
        self.viewMatrix = np.eye(4)
        self.perspective_proj_matrix = np.eye(4)
        self.ortho_proj_matrix = np.eye(4)
        self.aspect = 0
        self.near = 0
        self.far = 0
        self.fov = 0
        self.up_axis = 1

    def get_transform(self):
        """ Copied from ThinMatrix shadow tutorial
        src: https://www.youtube.com/watch?v=o6zDfDkOFIc
        https://www.dropbox.com/sh/g9vnfiubdglojuh/AACpq1KDpdmB8ZInYxhsKj2Ma/shadows
        """
        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)
        
        if self.up_axis == 2:
            rot_y = trans.quaternion_about_axis(-yaw, np.array([0, 0, 1]))# utils.get_rotation_around_z(math.radians(self.yaw))
        else:
            rot_y = trans.quaternion_about_axis(-yaw, np.array([0, 1, 0]))
        rot_y = trans.quaternion_matrix(rot_y)
        rot_x = trans.quaternion_about_axis(-pitch, np.array([1, 0, 0]))
        rot_x = trans.quaternion_matrix(rot_x)
        transform = np.dot(rot_y, rot_x)
        transform[3, :3] = -self.get_world_position()
        return transform

    def get_frustrum_vertices(self):
        """ src:https://github.com/pyth/sgltk P_Camera class
        """
        ndc = [[-1,-1,-1, 1],
                [1, -1, -1, 1],
                [1, 1, -1, 1],
                [-1, 1, -1, 1],

                [-1, -1, 1, 1],
                [1, -1, 1, 1],
                [1, 1, 1, 1],
                [-1, 1, 1, 1]]
        p_m = self.get_projection_matrix().T
        v_m = self.get_view_matrix().T
        rm = np.dot(p_m, v_m)
        m = np.linalg.inv(rm)
        ret = np.zeros((8,3))
        for idx in range(8):
            v = np.dot(m, ndc[idx])
            ret[idx] = v[:3]/ v[3]
        return ret

    def get_frustrum_bounding_box(self):
        v = self.get_frustrum_vertices()
        v_m = self.get_view_matrix().T
        _p = np.zeros(4)
        bb = BoundigBox()
        for p in v:
            _p[0] = p[0]
            _p[1] = p[1]
            _p[2] = p[2]
            _p[3] = 1
            _p = np.dot(v_m, _p)
            bb.update(_p[:3])
        return bb


class OrbitingCamera(Camera):
    """ orbiting camera based on http://www.glprogramming.com/red/chapter03.html
    """
    def __init__(self, up_axis=1):
        super().__init__()
        self.position = np.array([0.0,-10.0,0.0])
        self.zoom = -5.0
        self.view_dir = np.array([0.0,0.0,-1.0,1.0])
        self.rotation_matrix = np.eye(4)
        self.yaw = 0
        self.pitch = 0
        self.use_projection = True
        self._target = None
        self.up_axis = up_axis
        self.horizontal_axis = 0
        self.forward_axis = 2
        if self.up_axis ==2:
            self.horizontal_axis = 0
            self.forward_axis = 1
        

    def setTarget(self, target):
        self._target = target

    def removeTarget(self):
        self._target = None

    def update(self, dt):
        if self._target is not None:
            position = self._target.getPosition()
            if position is not None:
                self.position = -np.array(position)

    def moveHorizontally(self, distance):
        """  movement along relative cross vector based on the rotation copied from tutorial http://www.youtube.com/watch?v=RInkwoCgIps
            note direction is given by sign of the parameter
        """
        rad = math.radians(self.yaw)#(math.radians(self.yaw (self.yaw)/math.pi*180
        self.position[self.horizontal_axis] -= distance*math.cos(rad)
        self.position[self.forward_axis] -= distance*math.sin(rad)
    
    def moveVertically(self, distance):
        self.position[self.up_axis] -= distance 

    def moveForward(self, distance):
        """  movement along relative forward vector
        """
        forward_dir = np.array([0,0,0,1])
        forward_dir[self.forward_axis] = -1
        forward_dir = np.dot(self.rotation_matrix, forward_dir)[:3]
        forward_dir /= np.linalg.norm(forward_dir)
        self.position += distance * forward_dir
        
    def updateRotationMatrix(self, pitch, yaw):
        """rotation matrix copied from http://www.rob.uni-luebeck.de/Lehre/2009w/Robotik/Uebung/rotationsdarstellungen.pdf
           http://www.fractalforums.com/fragmentarium/camera-control-via-3dmouse-outputting-simple-rotation-angles-and-trans-values/?PHPSESSID=007234c5bb433cffecc7c11f432697da;wap2
        """
        self.pitch = float(pitch)
        self.yaw = float(yaw)
        if self.up_axis == 2:
            rot_y = utils.get_rotation_around_z(math.radians(self.yaw))
        else:
            rot_y = utils.get_rotation_around_y(math.radians(self.yaw))
        rot_x = utils.get_rotation_around_x(math.radians(self.pitch))
        self.rotation_matrix = np.dot(rot_y, rot_x)
        #self.lockRotation()#prevent degrees over 360 and under 360
        #self.yaw %= 360
        #self.pitch %= 360
      
    def lockRotation(self):
        if self.yaw >360: 
            self.yaw -=360
        if self.yaw < 0:
            self.yaw +=360
        if self.pitch >360:
            self.pitch -=360
        if self.pitch < 0 :
            self.pitch+=360

    def set_projection_matrix(self, fov, aspect, near, far):
        f = 1.0/math.tan(math.radians(fov)*0.5)
        self.fov = fov
        if aspect == 0:
            aspect = 1
        self.aspect = aspect
        self.near = near
        self.far = far
        #note rows equal colums/ visual code representation of the matrix as an numpy array is equal to the transposed matrix
        #reshape is possible to one dimensional array but 2d array is needed for matrix multiplication
        self.perspective_proj_matrix = np.array([[f / aspect, 0.0, 0.0, 0.0],
                               [0.0, f,   0.0,  0.0], 
                               [0.0, 0.0, (far+near)/(near-far),  -1.0], 
                               [0.0, 0.0, 2.0*far*near/(near-far), 0.0]], np.float32)
        return self.perspective_proj_matrix

    def set_orthographic_matrix(self, left, right, bottom, top, near, far):
        if left - right == 0 or top-bottom == 0 or far-near == 0:
            return
        self.ortho_proj_matrix = np.array([[2.0/(right-left), 0,0,-(right+left)/(right-left)],
                                              [0, 2.0/(top-bottom), 0.0, - (top+bottom)/(top-bottom)],
                                              [0, 0.0, -2.0/(far-near), - (far+near)/(far-near)],
                                              [0, 0.0, 0.0, 1.0],
                                              ]).T
        return self.ortho_proj_matrix

    def get_projection_matrix(self):
        return self.perspective_proj_matrix

    def get_near_projection_matrix(self):
        nnear = self.near+0.001
        fov = self.fov
        aspect = self.aspect
        #scale = 0.001
        f = 1.0/math.tan(math.radians(fov)*0.5)
        return np.array([[f / aspect, 0.0, 0.0, 0.0],
                           [0.0,f,  0.0,  0.0],
                           [0.0, 0.0, (self.far+nnear)/(nnear-self.far),  -1.0],
                           [0.0, 0.0, 2.0*self.far*nnear/(nnear-self.far), 0.0]], np.float32)

    def get_orthographic_matrix(self):
        return self.ortho_proj_matrix
    
    def get_inv_projection_matrix(self):
        return la.inv(self.perspective_proj_matrix)

    def get_view_matrix(self):
        zoomVector = [0,0,self.zoom]
        zoomMatrix = utils.get_translation_matrix(zoomVector)
        translationMatrix = utils.get_translation_matrix(self.position)
        # M = Translation * (Zoom *Rotation) 
        transformationMatrix = np.dot(self.rotation_matrix, zoomMatrix)#first zoom zoom out then rotate
        transformationMatrix = np.dot(translationMatrix, transformationMatrix)#then translate on relative cross vector

        self.view_dir = np.dot(self.rotation_matrix, self.view_dir)
        self.view_dir /= np.linalg.norm(self.view_dir)
        return transformationMatrix
    
    def get_inv_view_matrix(self):
        return la.inv(self.get_view_matrix())

    def get_pivot_matrix(self):
        """ same rotation and zoom as view Matrix but no horizontal translation
        """
        #zoom
        zoomVector = [0,0, self.zoom]
        zoomMatrix = utils.get_translation_matrix(zoomVector)
        #rotation
        return np.dot(self.rotation_matrix, zoomMatrix)

    def get_world_position(self):
        return self.get_inv_view_matrix()[3,:3]#extract the translation

    def pose_to_dict(self):
        pose = dict()
        pose["position"] = self.position
        pose["angles"] = (self.pitch, self.yaw)
        pose["zoom"] = self.zoom
        return pose

    def pose_from_dict(self, pose):
        self.position = pose["position"]
        self.pitch, self.yaw = pose["angles"]
        self.zoom = pose["zoom"]

    def print_position(self):
        pose = self.pose_to_dict()
        print(pose)
        #print("Camera Pose:")
        #print("position:", self.position)
        #print("pitch:", self.pitch)
        #print("yaw:", self.yaw)
        #print("zoom:", self.zoom)
        print()


    def reset(self):
        self.position = np.array([0.0,-10.0,0.0])
        self.zoom = -5.0
        self.view_dir = np.array([0.0,0.0,-1.0,1.0])
        self.rotation_matrix = np.eye(4)
        self.yaw = 0
        self.pitch = 0
