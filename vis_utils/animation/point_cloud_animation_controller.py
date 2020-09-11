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
from PySignal import Signal
from ..graphics.renderer.lines import DebugLineRenderer
from .animation_controller import AnimationController
from ..graphics.renderer import SphereRenderer
from ..scene.components import ComponentBase
from ..graphics.utils import get_translation_matrix
from ..io import load_json_file

DEFAULT_COLOR = [0, 0, 1]

class PointCloudAnimationController(ComponentBase, AnimationController):
    updated_animation_frame = Signal()
    reached_end_of_animation = Signal()

    def __init__(self, scene_object, color=DEFAULT_COLOR, visualize=True):
        ComponentBase.__init__(self, scene_object)
        AnimationController.__init__(self)
        self.animated_joints = []
        self.visualize = visualize
        self.skeleton = None
        if visualize:
            self._sphere = SphereRenderer(10, 10, 1, color=color)
            a = [0, 0, 0]
            b = [1, 0, 0]
            self._line = DebugLineRenderer(a, b, color)
        self.draw_bone = False
        self._semantic_annotation = None
        self.frameTime = 1.0/30
        self.motion_data = []
        self.skeleton_model = None
        self.target_skeleton = None

    def toggle_animation_loop(self):
        self.loopAnimation = not self.loopAnimation

    def isLoadedCorrectly(self):
        return len(self.motion_data) > 0

    def set_data(self, data):
        self.motion_data = []
        for idx, frame in enumerate(data["motion_data"]):
            pc_frame = []
            for p in frame:
                pc_frame.append(list(map(float, p)))
            self.motion_data.append(pc_frame)
        self.motion_data = np.array(self.motion_data)

        if 'skeleton' in list(data.keys()):
            self.skeleton = data["skeleton"]
        else:
            self.skeleton = None

        if 'has_skeleton' in list(data.keys()) and 'skeleton' in list(data.keys()):
            self.draw_bone = False#data['has_skeleton']

    def update(self, dt):
        dt *= self.animationSpeed
        if self.isLoadedCorrectly():
            if self.playAnimation:
                self.animationTime += dt
                self.currentFrameNumber = int(self.animationTime / self.getFrameTime())

                # update gui
                if self.currentFrameNumber > self.getNumberOfFrames():
                    self.resetAnimationTime()
                else:
                    self.updated_animation_frame.emit(self.currentFrameNumber)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        if self._sphere is None:
                return

        if self.currentFrameNumber < 0 or self.currentFrameNumber >= self.getNumberOfFrames():
            return

        for position in self.motion_data[self.currentFrameNumber]:
            m = get_translation_matrix(position[:3])
            m = np.dot(m, modelMatrix)
            self._sphere.draw(m, viewMatrix, projectionMatrix, lightSources)

        if self.draw_bone:
            for joint, value in list(self.skeleton.items()):
                if value['parent'] is not None:
                    joint_idx = value['index']
                    joint_parent_idx = self.skeleton[value['parent']]['index']
                    start_point = self.motion_data[self.currentFrameNumber][joint_parent_idx]
                    end_point = self.motion_data[self.currentFrameNumber][joint_idx]
                    self._line.set_line(start_point, end_point)
                    self._line.draw(modelMatrix, viewMatrix, projectionMatrix)

    def getNumberOfFrames(self):
        return len(self.motion_data)

    def getFrameTime(self):
        return self.frameTime

    def updateTransformation(self, frame_number=None):
        if frame_number is not None:
            self.currentFrameNumber = frame_number
        self.animationTime = self.getFrameTime() * self.currentFrameNumber

    def setCurrentFrameNumber(self, frame_number=None):
        if frame_number is not None:
            self.currentFrameNumber = frame_number
        self.animationTime = self.getFrameTime() * self.currentFrameNumber

    def apply_scale(self, scale):
        self.motion_data[:, :, :3] *= scale

    def apply_transform(self, m):
        for i, frame in enumerate(self.motion_data):
            for j, p in enumerate(frame):
                p = self.motion_data[i, j, :3]
                self.motion_data[i, j, :3] = np.dot(m, p)

    def setColor(self, color):
        self._sphere.technique.material.diffuse_color = color
        self._sphere.technique.material.ambient_color = color * 0.1

    def getColor(self):
        return self._sphere.technique.material.diffuse_color

    def replace_skeleton_model(self, filename):
        data = load_json_file(filename)
        self.set_skeleton_model(data)

    def set_skeleton_model(self, model):
        self.skeleton_model = model
        #self.skeleton = SkeletonBuilder().load_from_json_data(data)
        #self.skeleton.joints = self._joints

    def get_semantic_annotation(self):
        return dict()

    def get_current_frame(self):
        if self.currentFrameNumber < 0 or self.currentFrameNumber >= self.getNumberOfFrames():
            return None
        return self.motion_data[self.currentFrameNumber]

    def get_skeleton(self):
        return self.skeleton

    def get_frame_time(self):
        return self.getFrameTime()

    def get_label_color_map(self):
        return dict()

    def set_frame_time(self, frame_time):
        self.frameTime = frame_time

