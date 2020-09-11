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
from copy import copy
from math import acos, degrees
from matplotlib import pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as colors
import numpy as np
from ..scene.legacy import SplineObject, MarkerObject, CoordinateSystemObject, PositionConstraintObject
from .utils import load_json_file
from ..graphics import utils


class ConstraintsFormatReader(object):
    scaleFactor = 100

    def __init__(self, scene, scaleFactor=100):
        self._scene = scene
        self.scaleFactor = scaleFactor

    def loadCoordinateErrorFormat(self, filename):
        data = load_json_file(filename)
        if data is None:
            return
        print("median", np.median(data["errors"]))
        print("average", np.mean(data["errors"]))
        print("median duration", np.median(data["durations"]))
        print("average time", np.mean(data["durations"]))

        jet = plt.get_cmap('jet')
        # a = max(0, 1)
        vmax = max(max(np.log(data["errors"])), 1)
        cNorm = colors.Normalize(vmin=0, vmax=vmax)
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)
        for idx, c in enumerate(data["coordinates"]):
            error = np.log(data["errors"][idx])  # *10
            color = scalarMap.to_rgba(error)
            color = np.array(list(color)[:3])
            print(data["errors"][idx], color)
            self._addConstraintMarkerObject(c, radius=2.0, color=color)

    def loadPath(self, filename):
        data = load_json_file(filename)
        if data is None:
            return
        count = 0
        color = np.random.rand(3)
        if "startPose" in list(data.keys()):
            position = data["startPose"]["position"]
            start_color = [1, 0, 0]
            marker = MarkerObject(position, start_color, scale=100)
            marker.position = position
            marker.active = True
            self._scene.addObject(marker)
        if "tasks" in list(data.keys()):
            for task in data["tasks"]:
                count = self._addElementaryActionConstraints(task["elementaryActions"], count, color[0], color[1],
                                                             color[2])
        elif "elementaryActions" in list(data.keys()):
            self._addElementaryActionConstraints(data["elementaryActions"], count, color[0], color[1], color[2])

    def _addConstraintMarkerObject(self, position, radius=2.5, color=None):
        constraint = PositionConstraintObject(position, radius)
        constraint.setPosition(position)
        constraint.active = False
        self._scene.addObject(constraint)

    def _addElementaryActionConstraints(self, elementaryActionList, count, r, g, b):
        keyframe_constraint_count = 0
        for entry in elementaryActionList:
            print("entry", count)
            elementaryAction = str(entry["action"])
            constraints = entry["constraints"]
            for constraint in constraints:
                if "keyframeConstraints" in list(constraint.keys()):
                    for c in constraint["keyframeConstraints"]:
                        if "position" in list(c.keys()):
                            point = c["position"]
                            point = [p if p is not None else 0 for p in point]
                            point_copy = copy(point)
                            #point = self.transform_point_from_cad_to_opengl_cs(point_copy)
                            self._addConstraintMarkerObject(point)
                            print("add position keyframe constraint", point, elementaryAction)
                            keyframe_constraint_count += 1
                            if "direction" in list(c.keys()):
                                ref_dir = [0, -1]
                                dir_vector = [c["direction"][0], c["direction"][2]]
                                cs = CoordinateSystemObject(10)
                                angle = degrees(acos(np.dot(dir_vector, ref_dir) / (
                                    np.linalg.norm(dir_vector) * np.linalg.norm(ref_dir))))
                                e = [0, angle, 0]
                                order = ["X", "Y", "Z"]
                                cs.transformation = utils.get_matrix_from_pos_and_angles(point,e, order)
                                cs.active = True
                                self._scene.addObject(cs)
                if "trajectoryConstraints" in list(constraint.keys()):
                    controlPoints = []
                    n_control_points = len(constraint["trajectoryConstraints"])
                    for i in range(n_control_points):

                        if "position" in list(constraint["trajectoryConstraints"][i].keys()):
                            point = constraint["trajectoryConstraints"][i]["position"]
                            point = [p if p is not None else 0 for p in point]
                            point_copy = copy(point)
                            #point = self.transform_point_from_cad_to_opengl_cs(point_copy)
                            point = np.array(point)
                            controlPoints.append(point)

                    print("loaded", len(controlPoints), " control points")
                    spline = SplineObject(controlPoints, r, g, b)
                    self._scene.addObject(spline)
                count += 1
        print("loaded", keyframe_constraint_count, "keyframe constraints")
        return count


    def transform_point_from_cad_to_opengl_cs(self, point):
        transform_matrix = np.array([[1, 0, 0],
                                     [0, 0, 1],
                                     [0, -1, 0]])
        return np.dot(transform_matrix, point).tolist()