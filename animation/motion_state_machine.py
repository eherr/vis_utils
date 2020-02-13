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
from transformations import quaternion_matrix, quaternion_multiply
from .state_machine_controller import StateMachineController
from .utils import normalize, av_to_quaternion, calc_velocity
from PySignal import Signal


class MotionLoopState(object):
    def __init__(self, poses, frame_time):
        self.poses = poses
        self.frame_time = frame_time
        self.vel,self.angular_vel = calc_velocity(self.poses, frame_time)
        self.n_frames = len(self.poses)
        self.time = 0
        self.max_time = self.frame_time*self.n_frames
        self.current_pose = np.array(self.poses[0])
        self.global_pos = self.current_pose[:3]
        self.global_rot = self.current_pose[3:7]

    def update_pose(self, dt):
        self.time += dt
        self.time %= self.max_time
        #print(self.time)

        frame_idx = int(self.time / self.frame_time)
        self.current_pose = np.array(self.poses[frame_idx])
        lv = self.vel[frame_idx]
        av = self.angular_vel[frame_idx]
        av *= self.frame_time

        global_rot_m = quaternion_matrix(self.global_rot)[:3, :3]
        lv = np.dot(global_rot_m, lv)
        av = np.dot(global_rot_m, av)
        # print(global_rot_m, lv, av)

        av[0] = 0
        av[2] = 0
        delta_q = av_to_quaternion(av)
        # print(delta_q)
        self.global_pos[0] += lv[0]
        self.global_pos[2] += lv[2]
        global_rot = quaternion_multiply(self.global_rot, delta_q)

        self.global_rot = normalize(global_rot)

        self.current_pose[:3] = self.global_pos
        self.current_pose[3:7] = self.global_rot
        # print(self.global_pos, self.global_rot)
        return self.current_pose

    def reset(self):
        self.time = 0
        self.max_time = self.frame_time * self.n_frames
        self.current_pose = self.poses[0]
        self.global_pos = self.current_pose[:3]
        self.global_rot = self.current_pose[3:7]


class MotionStateMachineController(StateMachineController):
    """ can be combined with a SkeletonVisualization component"""
    update_scene_object = Signal()
    def __init__(self, scene_object, skeleton, motion_vector):
        StateMachineController.__init__(self, scene_object)
        self.skeleton = skeleton
        self.state = MotionLoopState(motion_vector.frames, motion_vector.frame_time)
        self.vis = None
        self.play = False

    def update(self, dt):
        if self.play:
            self.state.update_pose(dt)
            if self.vis is not None and self.visible:
                self.vis.updateTransformation(self.state.current_pose, self.scene_object.scale_matrix)

    def get_pose(self, frame_idx=None):
        return self.state.current_pose

    def get_skeleton(self):
        return self.skeleton

    def toggleAnimation(self):
        self.play = not self.play

