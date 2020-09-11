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
from .legacy import SplineObject, PositionConstraintObject

INTERACTION_NONE = "none"
INTERACTION_DEFINE_SPLINE = "spline"
INTERACTION_DEFINE_MARKER = "marker"
OBJECT_OFFSET = np.array([0,50,0])


def create_box(scene, p, q, offset=OBJECT_OFFSET):
    p = np.array([p[0], p[1], p[2]]) + offset
    o = scene.object_builder.create_object("box", p, q, width=1, height=1, depth=1, simulate=True, kinematic=False)
    c = o._components["articulated_body"]
    c.add_force(0,0,-1000)

def create_sphere(scene, p, q, offset=OBJECT_OFFSET):
    p = np.array([p[0], p[1], p[2]]) + offset
    simulate = False
    scene.object_builder.create_object("sphere", "test", p, q, radius=10, simulate=simulate, kinematic=False)

def create_capsule(scene, p, q, offset=OBJECT_OFFSET):
    p = np.array([p[0], p[1], p[2]])+ offset
    scene.object_builder.create_object("capsule", p, q, length=20.0, simulate=True)

def create_linked_capsule(scene, p, q, offset=OBJECT_OFFSET):
    p = np.array([p[0], p[1], p[2]])+ offset
    scene.object_builder.create_object("linked_capsule", p)

def create_ragdoll(scene, p, q, offset=OBJECT_OFFSET):
    p = np.array([p[0], p[1], p[2]])+ offset
    o = scene.object_builder.create_object("ragdoll_from_desc",p)
    scene._scene.addObject(o)


class SceneInteraction(object):
    def __init__(self):
        self._scene = None
        self._mode = INTERACTION_NONE
        self.current_object = None
        self.construction_methods = dict()
        self.construction_methods["box"] = create_box
        self.construction_methods["sphere"] = create_sphere
        self.construction_methods["capsule"] = create_capsule
        self.construction_methods["linked_capsule"] = create_linked_capsule
        self.construction_methods["ragdoll"] = create_ragdoll

    def set_scene(self, s):
        self._scene = s

    def set_mode(self, mode):
        if mode == INTERACTION_DEFINE_SPLINE and self._mode == INTERACTION_NONE:
            self.current_object = SplineObject([], 0.1, 0.6, 0.3)
            self.current_object.transformation[3,:3] = [0,1,0]
            self._scene.addObject(self.current_object)
        elif mode == INTERACTION_DEFINE_MARKER and self._mode == INTERACTION_NONE:
            self.current_object = None
        elif mode == INTERACTION_NONE and self._mode == INTERACTION_DEFINE_SPLINE:
            self.current_object = None
        self._mode = mode

    def handleMouseClick(self, event, rayStart, rayDir, pos):
        """# used to set the goal marker of the state machine based on clicks on the OpenGL widget"""
        if self._scene is None:
            return
        if self._mode != INTERACTION_NONE:
            #position = self._scene.rayCastOnPlane(rayStart, rayDir)
            position = pos
            if self._mode == INTERACTION_DEFINE_SPLINE:
                self.current_object.addControlPoint(position)
            elif self._mode == INTERACTION_DEFINE_MARKER:
                if self.current_object is None:
                    position = np.array([position[0], position[1], position[2]])
                    self.current_object = PositionConstraintObject(position, 2.5)
                    self._scene.addObject(self.current_object)
                self._mode = INTERACTION_NONE
            else:
                p = np.array([position[0], position[1], position[2]])
                q = [1, 0, 0, 0]
                self.create_object(p, q)

    def create_object(self, p, q):
        if self._mode in self.construction_methods:
            self.construction_methods[self._mode](self._scene, p,q)

