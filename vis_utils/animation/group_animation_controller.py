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
from PySignal import Signal
from .animation_controller import AnimationController
from ..scene.components import ComponentBase


class GroupAnimationController(ComponentBase, AnimationController):
    updated_animation_frame = Signal()
    reached_end_of_animation = Signal()

    def __init__(self, scene_object):
        ComponentBase.__init__(self, scene_object)
        self.mainContext = 0
        AnimationController.__init__(self)
        self._animation_controllers = []

    def add_animation_controller(self, animation_controller):
        self._animation_controllers.append(animation_controller)
        self.frameTime = animation_controller.frameTime

    def get_animation_controllers(self):
        return self._animation_controllers

    def update(self, dt):
        """ update current frame and global joint transformation matrices
        """

        dt *= self.animationSpeed
        if self.isLoadedCorrectly():
            if self.playAnimation:
                # frame and transformation matrices
                self.animationTime += dt
                self.currentFrameNumber = int(self.animationTime / self.getFrameTime())
                self.updateTransformation(self.currentFrameNumber)

                # update gui
                if self.currentFrameNumber > self.getNumberOfFrames():
                        self.resetAnimationTime()
                        self.reached_end_of_animation.emit(self.loopAnimation)
                else:
                    self.updated_animation_frame.emit(self.currentFrameNumber)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        return

    def updateTransformation(self, frameNumber=None):
        for controller in self._animation_controllers:
            if frameNumber is not None and 0 <= frameNumber < controller.getNumberOfFrames():
                controller.setCurrentFrameNumber(frameNumber)
            controller.updateTransformation()

    def resetAnimationTime(self):
        AnimationController.resetAnimationTime(self)
        self.currentFrameNumber = 0
        self.updateTransformation(self.currentFrameNumber)

    def setCurrentFrameNumber(self, frameNumber):
         self.currentFrameNumber = frameNumber
         self.updateTransformation(self.currentFrameNumber)
         self.animationTime = self.getFrameTime() * self.currentFrameNumber


    def getNumberOfFrames(self):
        n_frames = [0]
        n_frames += [controller.getNumberOfFrames() for controller in self._animation_controllers]
        return max(n_frames)

    def isLoadedCorrectly(self):
        return len(self._animation_controllers) > 0

    def getFrameTime(self):
        if self.isLoadedCorrectly():
            # print self.frameTime
            return self.frameTime
        else:
            return 0

    def toggle_animation_loop(self):
        self.loopAnimation = not self.loopAnimation