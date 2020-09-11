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
""" http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-16-shadow-mapping/#rendering-the-shadow-map
 https://learnopengl.com/code_viewer_gh.php?code=src/5.advanced_lighting/3.1.2.shadow_mapping_base/shadow_mapping_base.cpp
thin matrix shadow tutorial
src: https://www.youtube.com/watch?v=o6zDfDkOFIc
https://www.dropbox.com/sh/g9vnfiubdglojuh/AACpq1KDpdmB8ZInYxhsKj2Ma/shadows

"""
from OpenGL.GL import *
import numpy as np
from ..shadow_map_buffer import ShadowMapBuffer
from ..shadow_box import ShadowBox, get_lookat_matrix, get_orthographic_matrix


BIAS_MATRIX = np.array([[0.5, 0.0, 0.0, 0.0],
                        [0.0, 0.5, 0.0, 0.0],
                        [0.0, 0.0, 0.5, 0.0],
                        [0.5, 0.5, 0.5, 1.0]
                        ])# transform homogenous to texture coordinates

class DirectionalLight(object):
    def __init__(self, position, target, up_vector, intensities, w=4096, h=4096, scene_scale=1, shadow_box_length=500):
        #w*=4
        #h*=4
        self.up_vector = up_vector
        self.target = target
        self._dir = (target-position)
        self._dir /= np.linalg.norm(self._dir)
        self._pos = position
        self.shadow_box = ShadowBox(self, shadow_box_length)
        self.shadow_buffer = ShadowMapBuffer(w, h)
        scale = 100*scene_scale#10000.0
        near = -1.0# 1.0
        far = 1000*scene_scale
        self.proj_mat = get_orthographic_matrix(-scale, scale, -scale, scale, near, far)
        self.view_mat = get_lookat_matrix(self._pos, target-self._pos, up_vector)
        self.intensities = intensities
        self.position = -np.array([self._dir[0], self._dir[1], self._dir[2], 0])
        self.scale = scale
        self.near = near
        self.far = far

    def update(self, camera):
        """ update the position of the view matrix and based on the center of the shadow box
        """
        self.view_mat,self.proj_mat = self.shadow_box.update(camera, self._dir) # update center and dims from camera frustrum

    def pre_render(self):
        self.shadow_buffer.prepare_buffer()

    def post_render(self):
        self.shadow_buffer.unbind()

    def get_depth_texture(self):
        return self.shadow_buffer.depth_texture




