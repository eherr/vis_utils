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

from collections import OrderedDict
from vis_utils.graphics.asset_manager import AssetManager
from .scene_object import SceneObject


DEFAULT_COLOR = (0.5, 0.5, 0.0)


DEFAULT_DENSITY = 0.5
DEFAULT_DENSITY = 1
PRIMITIVE_BODY_DENSITY = 1
#DEFAULT_DENSITY = 1
#DEFAULT_DENSITY = 10



class SceneObjectBuilder(object):
    construction_methods = OrderedDict()
    component_methods = OrderedDict()
    file_handler = OrderedDict()
    instance = None

    def __init__(self):
        self._scene = None
        self.asset_manager = AssetManager.get_instance()

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = SceneObjectBuilder()
        return cls.instance

    def set_scene(self, s):
        self._scene = s

    @classmethod
    def register_object(cls, name, method):
        cls.construction_methods[name] = method

    @classmethod
    def register_file_handler(cls, name, method):
        cls.file_handler[name] = method

    @classmethod
    def register_component(cls, name, method):
        cls.component_methods[name] = method

    def create_object(self, type, *args, **kwargs):
        return self.construction_methods[type](self, *args, **kwargs)

    def create_component(self, type, *args, **kwargs):
        return self.component_methods[type](self, *args, **kwargs)

    def create_object_from_file(self, type, *args, **kwargs):
        return self.file_handler[type](self, *args, **kwargs)

    def load_file(self, filename):
        o = None
        for key in self.file_handler:
            if filename.endswith(key):
                o = self.create_object_from_file(key, filename)
                break
        return o


