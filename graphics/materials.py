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
from .texture import Texture


class Material(object):
    def __init__(self):
        self.ambient_color = np.array([0,0,0], dtype=np.float32)
        self.diffuse_color = np.array([0,0,0], dtype=np.float32)
        self.specular_color = np.array([1,1,1], dtype=np.float32)
        self.specular_shininess = 500.0
        self.diffuse_texture = None


class TextureMaterial(Material):
    def __init__(self, texture):
        super(TextureMaterial, self).__init__()
        self.ambient_color = np.array([0.1, 0.1, 0.1])
        self.diffuse_color = np.array([0.0, 0.0, 0.0])
        self.specular_color = np.array([0.0, 0.0, 0.0])
        self.diffuse_texture = texture

    @classmethod
    def from_image(cls, image):
        print(image)
        texture = Texture.from_image(image["Kd"])
        return TextureMaterial(texture)


class HeightMapMaterial(TextureMaterial):
    def __init__(self, diffuse_texture, height_map_texture, height_map_scale):
        """
        height_map_scale: scale applied on the normalized height_map_texture
        """
        super(HeightMapMaterial, self).__init__(diffuse_texture)
        self.ambient_color = np.array([0.1, 0.1, 0.1])
        self.diffuse_color = np.array([0.0, 0.0, 0.0])
        self.specular_color = np.array([0.0, 0.0, 0.0])
        self.height_map_texture = height_map_texture
        self.height_map_scale = height_map_scale


standard = Material()
standard.ambient_color = np.array([0.3, 0.1, 0.1])
standard.diffuse_color = np.array([1.0, 0.0, 0.0])

red = Material()
red.ambient_color = np.array([0.3, 0.1, 0.1])
red.diffuse_color = np.array([1.0, 0.0, 0.0])

green = Material()
green.ambient_color = np.array([0.1, 0.3, 0.1])
green.diffuse_color = np.array([0.0, 1.0, 0.0])

blue = Material()
blue.ambient_color = np.array([0.1, 0.1, 0.3])
blue.diffuse_color = np.array([0.0, 0.0, 1.0])

purple = Material()
purple.ambient_color = np.array([0.3, 0.1, 0.3])
purple.diffuse_color = np.array([0.5, 0.0, 0.5])

grey = Material()
grey.ambient_color = np.array([0.3, 0.3, 0.3])
grey.diffuse_color = np.array([0.3, 0.3, 0.3])

yellow = Material()
yellow.ambient_color = np.array([0.3, 0.3, 0.1])
yellow.diffuse_color = np.array([1.0, 1.0, 0.0])
