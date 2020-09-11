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
from ..renderer.lines import *
from ..renderer.primitive_shapes import *


class PrimitiveManager(object):
    """Singleton class for reuse of standard shapes
    """
    line = None
    unitBox = None
    unitSphere = None
    cs = None
    def init(self):
        """creates an instance of each standard shape and sets is as class attribute
        """
        if self.line is None:
            self.initPrimitives()

    def initPrimitives(self):
        print("init primitive manager")
        self.__class__.unitBox = BoxRenderer(0.02, 0.02, 0.02)
        self.__class__.line = DebugLineRenderer()
        self.__class__.unitSphere = SphereRenderer(10, 10, 0.5)
        self.__class__.cs = CoordinateSystemRenderer(3.0)

    def getUnitBox(self):
        return self.unitBox

    def getLine(self):
        return self.line

    def getUnitSphere(self):
        return self.unitSphere

    def getCoordinateSystem(self):
        return self.cs
