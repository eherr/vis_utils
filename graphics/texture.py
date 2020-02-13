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
#! /usr/bin/env python
# -*- coding: utf8 -*-
"""Port of NeHe Lesson 16 by Ivan Izuver <izuver@users.sourceforge.net>"""
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image, ImageDraw
from itertools import cycle
import numpy as np
try:
    from noise import pnoise2
except:
    print("Info: Disable noise functions due to missing library")
    pnoise2  = lambda x, y, octaves, base : 0

FOREGROUND_COLOR = (220,220,220)
BACKGROUND_COLOR = (150,150,150)
class Texture(object):
    def __init__(self):
        self.texture_id = -1
        self.image = None

    @classmethod
    def enable(cls):
        glEnable(GL_TEXTURE_2D)

    @classmethod
    def disable(cls):
        glDisable(GL_TEXTURE_2D)

    @classmethod
    def from_image(cls, image):
        texture = Texture()
        texture.image = image
        img_data = image.convert("RGBA").tobytes("raw", "RGBA", 0, -1)
        texture._upload(img_data, image.size[0], image.size[1])
        return texture

    def load_from_file(self, filepath):
        self.image = Image.open(filepath)
        ix = self.image.size[0]
        iy = self.image.size[1]
        img_data = self.image.tobytes("raw", "RGBA", 0, -1)
        #img_data = np.array(list(image.getdata()), np.int8)
        self._upload(img_data, ix, iy)

    def generate_random(self, w, h, octaves=8, persistance=1,lacunarity=1, base=0):
        xnum_points = w
        xspan = 5.0
        ynum_points = h
        yspan =  15.0

        img_data = []
        for x in range(w):
            x = float(x) * xspan / xnum_points - 0.5 * xspan
            for y in range(h):
                y = float(y) * yspan / ynum_points - 0.5 * yspan
                v = pnoise2(x, y, octaves, base=base)
                #print(x,y,v)
                v += 1
                v /=2.0
                v*= 255
                v = int(v)
                #v = 5
                img_data.append(v)
                img_data.append(v)
                img_data.append(v)
                img_data.append(255)
        img_data = bytes(img_data)
        self.image = Image.new("RGBX", (w, h))
        self.image.frombytes(img_data)
        self._upload(img_data, w, h)

    def _upload(self, image, ix, iy):
        #http://www.siafoo.net/article/58
        # Create Texture
        self.texture_id = glGenTextures(1)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)  # 2d texture (x and y size)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        #glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        #glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        #glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        #glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glGenerateMipmap(GL_TEXTURE_2D)#, GL_RGBA,ix, iy, GL_RGBA,UNSINGED_INT 8,8,8,8, image


        #print "loaded texture", self.texture_id,image
    def make_chessboard(self, n=4, pixel_width=200):
        self.image = self._draw_chessboard(n, pixel_width)
        img_data = self.image.tobytes("raw", "RGBX", 0, -1)
        ix = self.image.size[0]
        iy = self.image.size[1]
        self._upload(img_data, ix, iy)
        print("chess board", self.texture_id)

    def make_height_map(self, n=4, pixel_width=200):
        self.image = self._draw_chessboard(n, pixel_width)
        img_data = self.image.tobytes("raw", "RGBX", 0, -1)
        ix = self.image.size[0]
        iy = self.image.size[1]
        self.texture_id = glGenTextures(1)
        print("height map",self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)  # 2d texture (x and y size)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def _draw_chessboard(self, n=4, pixel_width=200, background_color=BACKGROUND_COLOR, square_color=FOREGROUND_COLOR):
        """Draw an n x n chessboard using PIL.
        http://wordaligned.org/articles/drawing-chessboards
        """

        def sq_start(i):
            "Return the x/y start coord of the square at column/row i."
            return i * pixel_width / n

        def square(i, j):
            "Return the square corners, suitable for use in PIL drawings"
            return list(map(sq_start, [i, j, i + 1, j + 1]))

        image = Image.new("RGBX", (pixel_width, pixel_width))
        squares = (square(i, j)
                   for i_start, j in zip(cycle((0, 1)), list(range(n)))
                   for i in range(i_start, n, 2))
        ImageDraw.Draw(image).rectangle([0,0,pixel_width,pixel_width], fill=background_color)
        for sq in squares:
            ImageDraw.Draw(image).rectangle(sq, fill=square_color)
        return image

    def bind(self):
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

    def unbind(self):
        glBindTexture(GL_TEXTURE_2D, 0)

    def get_pixel(self, x, y):
        if self.image is not None:
            return self.image.getpixel((x,y))
