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
from .component_base import ComponentBase


class TerrainComponent(ComponentBase):
    def __init__(self, scene_object, width, depth, mesh, height_image, height_map_scale):
        ComponentBase.__init__(self, scene_object)
        self._scene_object = scene_object
        self.width = width
        self.depth = depth
        self.mesh = mesh
        self.height_map_scale = height_map_scale
        self.height_image = height_image

    def to_relative_coordinates(self, center_x, center_z, x, z):
        """ get position relative to upper left
        """
        relative_x = x - center_x
        relative_z = z - center_z
        relative_x += self.width / 2
        relative_z += self.depth / 2

        # scale by width and depth to range of 1
        relative_x /= self.width
        relative_z /= self.depth
        return relative_x, relative_z

    def get_height(self, relative_x, relative_z):
        if relative_x < 0 or relative_x > 1.0 or relative_z < 0 or relative_z > 1.0:
            #print("Coordinates outside of the range")
            return 0
        # scale by image width and height to image range
        height_map_image = self.height_image
        ix = relative_x*height_map_image.size[0]
        iy = relative_z*height_map_image.size[1]
        p = self.height_image.getpixel((ix, iy))
        return (p[0]/255)*self.height_map_scale