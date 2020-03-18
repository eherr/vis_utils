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
from abc import abstractmethod
import numpy as np
from .scene_graph_node import SceneGraphNode


class SceneObject(SceneGraphNode):
    def __init__(self, name=""):
        super(SceneObject, self).__init__()
        self.name = name
        self.visible = True
        self.visualization = None
        self.clickable = True
        self._components = dict()

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True

    def handle_keyboard_input(self, key):
        for component in self._components.values():
            component.handle_keyboard_input(key)

    def before_update(self, dt):

        for component in self._components.values():
            component.before_update(dt)

    def update(self, dt):
        """needs to be implemented e.g. to set the model matrix of the visualization or update an animation"""
        for component in self._components.values():
            component.update(dt)

    def after_update(self, dt):
        for component in self._components.values():
            component.after_update(dt)

    def sim_update(self, dt):
        for component in self._components.values():
            component.sim_update(dt)

    def draw(self, viewMatrix, projectionMatrix, lightSources):
        """needs to be implemented. note that scene objects don't have to use the light sources when they have a colored visualization e.g. a line"""
        m = np.dot(self.scale_matrix, self.transformation)
        if self.visualization is not None and self.visible:
            self.visualization.draw(m, viewMatrix, projectionMatrix, lightSources)

        for component in self._components.values():
            if component.visible:
                component.draw(m, viewMatrix, projectionMatrix, lightSources)

    @abstractmethod
    def drawDebugVisualization(self, viewMatrix, projectionMatrix, lightSources):
        """needs to be implemented. note that scene objects don't have to use the light sources when they have a colored visualization e.g. a line"""
        pass

    def update_and_draw(self, viewMatrix, projectionMatrix, lightSources, dt):
        self.update(dt)
        self.draw(viewMatrix, projectionMatrix, lightSources)

    def add_component(self, name, component):
        self._components[name] = component

    def _remove_component(self, name):
        if name in self._components.keys():
            del self._components[name]

    def has_component(self, name):
        return name in self._components.keys()

    def set_attribute(self, name, value):
        for component in self._components.values():
            #print(component)
            if hasattr(component, name):
                func = getattr(component, name)
                func(value)

    def get_attribute(self, name):
        for k in self._components:
            if hasattr(self._components[k], name):
                func = getattr(self._components[k], name)
                return func()
        return None

    def getPosition(self):
        value = self.get_attribute("getPosition")
        if value is None:
            return SceneGraphNode.getPosition(self)
        else:
            return value

    def getColor(self):
        print("get color")
        return self.get_attribute("getColor")

    def setColor(self, color):
        self.set_attribute("setColor", color)

    def set_scale(self, scale_factor):
        print("set attribute", "scale",scale_factor)
        self.set_attribute("set_scale", scale_factor)
        SceneGraphNode.set_scale(self, scale_factor)

    def setPosition(self, position):
        SceneGraphNode.setPosition(self, position)
        if "articulated_body" in self._components:
            self._components["articulated_body"].set_position(position)

    def setQuaternion(self, q):
        SceneGraphNode.setQuaternion(self, q)
        if "articulated_body" in self._components:
            self._components["articulated_body"].set_quaternion(q)

    def setOrientation(self, x, y, z):
        SceneGraphNode.setOrientation(self, x, y, z)
        if "articulated_body" in self._components:
            self._components["articulated_body"].set_rotation(self.getGlobalTransformation())

    def cleanup(self):
        print("cleanup", self.node_id)
        for key in self._components.keys():
            if hasattr(self._components[key], "cleanup"):
                self._components[key].cleanup()

