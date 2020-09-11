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
from ..scene.components import ComponentBase


class SkeletonMirrorComponent(ComponentBase):
    def __init__(self, scene_object, src_skeleton, snapshot_interval=10):
        ComponentBase.__init__(self, scene_object)
        self.src_skeleton = src_skeleton
        self.states = list()
        self.anim_src = None
        self.next_snapshot_shot = 0
        self.snapshot_interval =snapshot_interval

    def update(self, dt):
        if self.anim_src is not None:
            frame_idx = self.anim_src.get_current_frame_idx()
            if frame_idx >= self.next_snapshot_shot:
                self.next_snapshot_shot = frame_idx + self.snapshot_interval
                self.add_current_state()

    def add_current_state(self):
        state = list()
        for m in self.src_skeleton.matrices:
            state.append(np.array(m).T)
        self.states.append(state)

    def clear(self):
        self.next_snapshot_shot = 0
        self.states = list()

