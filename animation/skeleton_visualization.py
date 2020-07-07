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
from copy import copy
import numpy as np
from ..graphics.geometry.mesh import Mesh
from ..graphics.renderer.debug_skeleton import DebugSkeletonRenderer
from ..graphics.renderer.lines import CoordinateSystemRenderer
from ..graphics import materials
from ..scene.components import ComponentBase
from ..graphics.renderer.lines import DebugLineRenderer

SKELETON_DRAW_MODE_NONE = 0
SKELETON_DRAW_MODE_LINES = 1
SKELETON_DRAW_MODE_BOXES = 2
SKELETON_DRAW_MODE_CS = 3
DEFAULT_BOX_SIZE = 2.0


class SkeletonVisualization(ComponentBase):
    """ The component manages the transforms and geometry used for the visualization of a skeleton by the OpenGL renderer.
    """
    def __init__(self, scene_object, color):
        ComponentBase.__init__(self, scene_object)
        self.color = color
        self.skeleton = None
        self.matrices = []
        self.shapes = dict()
        self._has_shapes = False
        self._material = None
        self.draw_mode = SKELETON_DRAW_MODE_BOXES
        self.debug_skeleton = None
        self.fk = None
        self.visualize = True
        self.box_scale = 1.0
        self.line_renderer = None
        self.line_color = [0,0,1]

    def set_skeleton(self, skeleton, visualize=True, scale=1.0):
        self.visualize = visualize
        self.skeleton = skeleton
        self._joints = skeleton.animated_joints
        self._parents_map = dict()
        for idx, j in enumerate(self._joints):
            if self.skeleton.nodes[j].parent is not None:
                parent_name = self.skeleton.nodes[j].parent.node_name
                self._parents_map[idx] = self._joints.index(parent_name)
            else:
                self._parents_map[idx] = None

        self.matrices = [None for j in self._joints]
        self._has_shapes = False
        if visualize:
            self._create_shapes(scale)
            self.debug_skeleton = DebugSkeletonRenderer(skeleton, self._joints, self.color)
            

    def _create_shapes(self, scale=1.0):
        self.box_scale = scale
        size = DEFAULT_BOX_SIZE *scale#*0.1 for physics environemnt
        self._material = copy(materials.standard)
        self._material.diffuse_color = self.color
        self._material.ambient_color = np.array(self.color)*0.3
        for idx, j in enumerate(self._joints):
            self.shapes[j] = []
            for c in self.skeleton.nodes[j].children:
                v = np.array(c.offset)
                if np.linalg.norm(v) > 0.0:
                    bone = Mesh.build_bone_shape(v, size, self._material)
                    #bone = BoneRenderer(vector, size, self._material)
                    self.shapes[j].append(bone)
        self._has_shapes = True
        self.cs = CoordinateSystemRenderer(3.0)

    def updateTransformation(self, frame, global_transformation):
        self.skeleton.clear_cached_global_matrices()
        for idx, joint in enumerate(self._joints):
            m = self.skeleton.nodes[joint].get_global_matrix(frame, use_cache=True)
            self.matrices[idx] = np.dot(global_transformation, m)
        if self.visualize:
            self.debug_skeleton.set_matrices(np.array(self.matrices))

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        if self.draw_mode == SKELETON_DRAW_MODE_LINES:
            self.debug_skeleton.draw(modelMatrix, viewMatrix, projectionMatrix, None)
        elif self.draw_mode == SKELETON_DRAW_MODE_BOXES and False:# dont draw boxes
            for idx, j in enumerate(self._joints):
                self.drawBoneShape(viewMatrix, projectionMatrix, lightSources, idx, j)
        elif self.draw_mode == SKELETON_DRAW_MODE_CS:
            self.debug_skeleton.draw(modelMatrix, viewMatrix, projectionMatrix, None)
            self.drawCoordinateSystems(viewMatrix, projectionMatrix)
        if self.line_renderer is not None:
            self.line_renderer.draw(modelMatrix, viewMatrix, projectionMatrix)

    def drawCoordinateSystems(self, viewMatrix, projectionMatrix):
        for idx, j in enumerate(self._joints):
            self.drawCoordinateSystem(viewMatrix, projectionMatrix, idx)

    def drawBoneShape(self, viewMatrix, projectionMatrix, lightSources, idx, j):
        m = self.scene_object.transformation
        if self.matrices[idx] is None:
            return
        for shape in self.shapes[j]:
            shape.draw(m, viewMatrix, projectionMatrix, lightSources)

    def drawCoordinateSystem(self, viewMatrix, projectionMatrix, idx):
        if self.matrices[idx] is not None:
            self.cs.draw(self.matrices[idx].T, viewMatrix, projectionMatrix)

    def set_color(self, color):
        self.color = color
        if self._material is not None:
            self._material.diffuse_color = color
            self._material.ambient_color = np.array(color) * 0.3
        self.debug_skeleton.set_color(color)

    def get_bone_transformations(self, index_list):
        mapped_matrices = []
        for idx in index_list:
            if idx > 0:
                mapped_matrices.append(self.matrices[idx])
            else:
                mapped_matrices.append(np.eye(4))
        return mapped_matrices

    def get_bone_index(self, name):
        if name in self._joints:
            return self._joints.index(name)
        else:
            return -1

    def get_transform(self, name):
        idx = self.get_bone_index(name)
        return self.matrices[idx]

    def set_scale(self, scale_factor):
        self.skeleton.scale(scale_factor)
        self.debug_skeleton = DebugSkeletonRenderer(self.skeleton, self._joints, self.color)
        self._create_shapes(scale_factor)

    def update(self, dt):
        return

    def getPosition(self):
        if len(self.matrices) > 0:
            return self.matrices[0][:3,3]
        else:
            return self.scene_object.getPosition()

    def get_bone_matrices(self):
        return self.matrices

    def update_dir_vis(self, direction_vector, target_projection_len):
        p = np.array(self.getPosition())
        if self.line_renderer is None:
            self.line_renderer = DebugLineRenderer(p, direction_vector*target_projection_len,self.line_color)
        else:
            pelvis = self.skeleton.skeleton_model["joints"]["pelvis"]
            p[1] += np.linalg.norm(self.skeleton.nodes[pelvis].offset) * 0.5
            self.line_renderer.set_line(p, p + direction_vector * target_projection_len)