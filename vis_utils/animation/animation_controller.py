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
# -*- coding: utf-8 -*-
CONTROLLER_TYPE_ANIMATION = 0
CONTROLLER_TYPE_MG = 1
CONTROLLER_TYPE_MP = 2


class AnimationController(object):
    """ Base class for animation controllers.
    """
    def __init__(self):
        self.animationTime = 0.0
        self.currentFrameNumber = 0
        self.loopAnimation = False
        self.playAnimation = False
        self.frameTime = 0.0
        self.animationSpeed = 1.0
        self.type = CONTROLLER_TYPE_ANIMATION

    def startAnimation(self):
        self.playAnimation = True
        return self.playAnimation

    def stopAnimation(self):
        self.playAnimation = False
        return not self.playAnimation

    def resetAnimation(self):
         self.stopAnimation()
         self.resetAnimationTime()  
         
    def resetAnimationTime(self):
        self.animationTime = 0.0
        self.playAnimation = self.loopAnimation
        
    def toggleAnimationLoop(self):
        self.loopAnimation = not self.loopAnimation
        return self.loopAnimation

    def isPlaying(self):
        return self.playAnimation

    def setAnimationSpeed(self, speed):
        self.animationSpeed = speed

    def setCurrentFrameNumber(self, frameNumber):
        self.animationTime = self.frameTime*frameNumber

    def toggleAnimation(self):
        self.playAnimation = not self.playAnimation
        return self.playAnimation
