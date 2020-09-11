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
""" Copied from ThinMatrix shadow tutorial
src: https://www.youtube.com/watch?v=o6zDfDkOFIc
https://www.dropbox.com/sh/g9vnfiubdglojuh/AACpq1KDpdmB8ZInYxhsKj2Ma/shadows
https://github.com/pyth/sgltk
"""

import numpy as np
import math
from math import tan, radians

UP = np.array([0,1,0])
FORWARD = np.array([0,0,-1])


def normalize(v):
    return v/np.linalg.norm(v)


def get_orthographic_matrix_old(left, right, bottom, top, near, far):
    return np.array([[2.0/(right-left), 0,0,-(right+left)/(right-left)],
                      [0, 2.0/(top-bottom), 0.0, - (top+bottom)/(top-bottom)],
                      [0, 0.0, -2.0/(far-near), - (far+near)/(far-near)],
                      [0, 0.0, 0.0, 1.0],
                      ]).T



def get_perspective_matrix(fov, aspectRatio, near, far):
    f = 1.0 / math.tan(math.radians(fov) * 0.5)
    if aspectRatio == 0:
        aspectRatio = 1
    # note rows equal colums/ visual code representation of the matrix as an numpy array is equal to the transposed matrix
    # reshape is possible to one dimensional array but 2d array is needed for matrix multiplication
    return np.array([[f / aspectRatio, 0.0, 0.0, 0.0],
                                      [0.0, f, 0.0, 0.0],
                                      [0.0, 0.0, (far + near) / (near - far), -1.0],
                                      [0.0, 0.0, 2.0 * far * near / (near - far), 0.0]], np.float32)


def get_orthographic_matrix(left, right, bottom, top, near, far):
    mat = np.zeros((4,4))
    mat[0,0] = 2.0/(right-left)
    mat[1,1] = 2.0/(top-bottom)
    mat[3,0] = - (right + left) / (right - left)
    mat[3,1] = -(top+bottom)/(top-bottom)
    mat[2,2] = - 2.0 / (far - near)
    mat[3,2] = - (far + near) / (far - near)
    mat[3, 3] = 1
    return mat


def get_lookat_matrix(pos, forward, up_vec):
    """ https://www.scratchapixel.com/lessons/mathematics-physics-for-computer-graphics/lookat-function
     copied from glm::lookAtRH"""
    #print("fw",forward)

    forward_n = np.linalg.norm(forward)
    if forward_n != 0:
        forward /= forward_n

    side = np.cross(forward, up_vec)
    side_n = np.linalg.norm(side)
    if side_n != 0:
        side /= side_n


    up = np.cross(side, forward)
    up_n = np.linalg.norm(up)
    if up_n != 0:
        up /= up_n

    view_mat = np.eye(4)
    #view_mat = np.ones((4,4))
    view_mat[0, 0] = side[0]
    view_mat[1, 0] = side[1]
    view_mat[2, 0] = side[2]

    view_mat[0, 1] = up[0]
    view_mat[1, 1] = up[1]
    view_mat[2, 1] = up[2]

    view_mat[0, 2] = -forward[0]
    view_mat[1, 2] = -forward[1]
    view_mat[2, 2] = -forward[2]

    view_mat[3, 0] = -np.dot(side, pos)
    view_mat[3, 1] = -np.dot(up, pos)
    view_mat[3, 2] = np.dot(forward, pos)
    return view_mat


def update_view_matrix(forward, center):
    forward = normalize(forward)
    right = np.cross(forward,np.array([0, 1, 0]))
    if np.linalg.norm(right) == 0:
        right = np.array([1,0,0])
    else:
        right = normalize(right)
    up_vec = normalize(np.cross(right, forward))
    view_mat = get_lookat_matrix(center, forward, up_vec)
    return view_mat



class ShadowBox(object):
    def __init__(self, light, shadow_box_length=500):
        self.light = light
        self.center = np.array([0,0,0])
        self.width = 0
        self.height = 0
        self.length = 0
        self.shadow_box_length = shadow_box_length

    def update(self, camera, direction):
        """  Update bounds of the shadow box to contain everything inside of the view frustrum of the camera."""
        _vertices = self.get_frustrum_vertices(camera)

        #transform from global into light space to calculate orthographic matrix dimensions?
        light_view_mat = self.light.view_mat.T
        local_vertices = []
        for v in _vertices:
            _v = np.array([v[0], v[1], v[2], 1])
            lv = np.dot(light_view_mat, _v)[:3]
            local_vertices.append(lv)
        #print("")
        min_v = np.array(local_vertices[0])
        max_v = np.array(local_vertices[0])
        for idx in range(1, len(local_vertices)):
            for d in range(3):
                if local_vertices[idx][d] < min_v[d]:
                    min_v[d] = local_vertices[idx][d]
                elif local_vertices[idx][d] > max_v[d]:
                    max_v[d] = local_vertices[idx][d]
        self.width = abs(max_v[0] - min_v[0])
        self.height = abs(max_v[1] - min_v[1])
        self.length = abs(max_v[2] - min_v[2])
        c = (min_v + max_v) / 2.0

        center = np.array([c[0], c[1], c[2], 1])
        center = np.dot(np.linalg.inv(self.light.view_mat.T), center)[:3]

        view_mat = update_view_matrix(direction, center)
        proj_mat = self.get_projection_matrix()
        return view_mat, proj_mat

    def get_projection_matrix(self, offset=0):
        """ Update the orthographic matrix and based on the dimensions of the shadow box
        """
        #proj_mat = np.eye(4)
        #proj_mat[0, 0] = 2.0/self.width
        #proj_mat[1, 1] = 2.0 / self.height
        #proj_mat[2, 2] = -2.0 / self.length
        #proj_mat[3, 3] = 1
        #return  proj_mat
        return get_orthographic_matrix(-0.5 * self.width - offset, 0.5 * self.width + offset,
                                       -0.5 * self.height - offset, 0.5 * self.height + offset,
                                       -0.5 * self.length - offset, 0.5 * self.length + offset).T

    def get_frustrum_vertices(self, camera):
        """ Calculates the global position of the vertex at each corner of the view frustum
              light space (8 vertices in total, so this returns 8 positions).
        """
        far = self.shadow_box_length
        #transform = np.eye(4)
        transform = camera.get_transform()
        #transform = self.viewMatrix.T
        rotation = transform[:3, :3]
        forward = np.dot(rotation, FORWARD)
        #print("forward", forward)
        up = np.dot(rotation, UP)

        right = np.cross(forward, up)
        down = -up
        left = -right
        pos = camera.get_world_position()
        #pos[2] = -pos[2]
        center_near = pos + camera.near * forward
        center_far = pos + far * forward


        far_width, near_width, far_height, near_height = self.calculate_view_frustrum_dimensions(camera)
        far_top = center_far + up * far_height
        far_bottom = center_far + down * far_height
        near_top = center_near + up * far_height
        near_bottom = center_near + down * far_height

        vertices = np.zeros((8,3))
        vertices[0] = far_top + right * far_width
        vertices[1] = far_top + left * far_width
        vertices[2] = far_bottom + right * far_width
        vertices[3] = far_bottom + left * far_width

        vertices[4] = near_top + right * near_width
        vertices[5] = near_top + left * near_width
        vertices[6] = near_bottom + right * near_width
        vertices[7] = near_bottom + left * near_width
        return vertices


    def calculate_view_frustrum_dimensions(self, camera):
        """
         * Calculates the width and height of the near and far planes of the
         * camera's view frustum. However, this doesn't have to use the "actual" far
         * plane of the view frustum. It can use a shortened view frustum if desired
         * by bringing the far-plane closer, which would increase shadow resolution
         * but means that distant objects wouldn't cast shadows.
         */"""
        tan_fov = tan(radians(camera.fov))
        far = self.shadow_box_length
        far_width = far * tan_fov
        near_width = camera.near * tan_fov
        far_height = far_width / camera.aspect
        near_height = near_width / camera.aspect
        return far_width, near_width, far_height, near_height


