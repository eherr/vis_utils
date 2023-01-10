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
import json
from copy import deepcopy
from PySignal import Signal
from .animation_controller import AnimationController, CONTROLLER_TYPE_ANIMATION
from .skeleton_visualization import SkeletonVisualization, SKELETON_DRAW_MODE_NONE, SKELETON_DRAW_MODE_LINES, SKELETON_DRAW_MODE_BOXES, SKELETON_DRAW_MODE_CS
from .point_cloud_animation_controller import PointCloudAnimationController
from vis_utils.scene.components import ComponentBase
from vis_utils.io import load_model_from_fbx_file, load_json_file
from vis_utils.scene.utils import get_random_color
from anim_utils.animation_data import BVHReader, BVHWriter, MotionVector, parse_amc_file
from anim_utils.retargeting import retarget_from_src_to_target, retarget_from_point_cloud_to_target
from anim_utils.animation_data.fbx import export_motion_vector_to_fbx_file
from anim_utils.animation_data.motion_state import MotionState
from .skeleton_mirror_component import SkeletonMirrorComponent


class SkeletonAnimationControllerBase(ComponentBase):
    updated_animation_frame = Signal()
    reached_end_of_animation = Signal()
    update_scene_object = Signal()

    def __init__(self, scene_object):
        ComponentBase.__init__(self, scene_object)


class LegacySkeletonAnimationController(SkeletonAnimationControllerBase, AnimationController):
    def __init__(self, scene_object):
        SkeletonAnimationControllerBase.__init__(self, scene_object)
        AnimationController.__init__(self)
        self._motion = None

    def get_semantic_annotation(self):
        return None

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        if self.isLoadedCorrectly():
            self._visualization.draw(modelMatrix, viewMatrix, projectionMatrix, lightSources)

    def update(self, dt):
        """ update current frame and global joint transformation matrices
        """
        if not self.isLoadedCorrectly():
            return
        dt *= self.animationSpeed
        if self.playAnimation:
            self.animationTime += dt
            self.currentFrameNumber = int(self.animationTime / self.getFrameTime())
            self.updateTransformation()

            # update gui
            if self.currentFrameNumber > self.getNumberOfFrames():
                self.resetAnimationTime()
                self.reached_end_of_animation.emit(self.loopAnimation)
            else:
                self.updated_animation_frame.emit(self.currentFrameNumber)

    def isLoadedCorrectly(self):
        return self._motion is not None

    def updateTransformation(self):
        if 0 <= self.currentFrameNumber < self.getNumberOfFrames():
            current_frame = self._motion.frames[self.currentFrameNumber]
            self._visualization.updateTransformation(current_frame, self.scene_object.transformation)

    def updateTransformationFromFrame(self, frame):
        self._visualization.updateTransformation(frame, self.scene_object.transformation)

    def resetAnimationTime(self):
        self.currentFrameNumber = 0
        self.animationTime = 0
        self.updateTransformation()

    def setCurrentFrameNumber(self, frame_idx):
        self.currentFrameNumber = frame_idx
        self.animationTime = self.getFrameTime() * frame_idx
        self.updateTransformation()

    def getNumberOfFrames(self):
        return self._motion.n_frames

    def getFrameTime(self):
        if self.isLoadedCorrectly():
            return self._motion.frame_time
        else:
            return 0

    def toggle_animation_loop(self):
        self.loopAnimation = not self.loopAnimation


class SkeletonAnimationController(SkeletonAnimationControllerBase):
    """ The class controls the pose of a skeleton based on an instance of a MotionState class.
        The scene containing a controller connects to signals emitted by an instance of the class and relays them to the GUI.
    """
    def __init__(self, scene_object):
        SkeletonAnimationControllerBase.__init__(self, scene_object)
        self.loadedCorrectly = False
        self.hasVisualization = False
        self.filePath = ""
        self.name = ""
        self._visualization = None
        self._motion = None
        self.markers = dict()
        self.recorder = None
        self.relative_root = False
        self.root_pos = None
        self.root_q = None
        self.type = CONTROLLER_TYPE_ANIMATION
        self.animationSpeed = 1.0
        self.loopAnimation = False
        self.activate_emit = True
        self.visualize = True

    def set_skeleton(self, skeleton, visualize=True):
        self.visualize = visualize
        self.skeleton = skeleton
        if visualize and self._visualization is not None:
            self._visualization.set_skeleton(skeleton, visualize)

    def set_motion(self, motion):
        self._motion = MotionState(motion)

    def set_color_annotation(self, semantic_annotation, color_map):
        self._motion.set_color_annotation(semantic_annotation, color_map)

    def set_time_function(self, time_function):
        self._motion.set_time_function(time_function)

    def set_color_annotation_legacy(self, annotation, color_map):
        self._motion.set_color_annotation_legacy(annotation, color_map)

    def set_random_color_annotation(self):
        self._motion.set_random_color_annotation()

    def set_visualization(self, visualization, draw_mode=SKELETON_DRAW_MODE_BOXES):
        self.skeleton = visualization.skeleton
        self._visualization = visualization
        self._visualization.draw_mode = draw_mode
        self._visualization.updateTransformation(self._motion.get_pose(), self.scene_object.scale_matrix)

    def update(self, dt):
        """ update current frame and global joint transformation matrices
        """
        if not self.isLoadedCorrectly():
            return
        if not self._motion.play:
            return
        reset = self._motion.update(dt*self.animationSpeed)
        self.updateTransformation()
        if reset:
            self._motion.play = self.loopAnimation
        if self.activate_emit:
            self.update_gui(reset)

    def update_gui(self, reset):
        if reset:
            self.reached_end_of_animation.emit(self.loopAnimation)
        else:
            self.updated_animation_frame.emit(self._motion.get_current_frame_idx())

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        if self.isLoadedCorrectly():
            self._visualization.draw(modelMatrix, viewMatrix, projectionMatrix, lightSources)

    def updateTransformation(self):
        if self.relative_root:
            return
        self.set_transformation_from_frame(self._motion.get_pose())

    def set_transformation_from_frame(self, frame):
        if frame is None or self._visualization is None:
            return
        self._visualization.updateTransformation(frame, self.scene_object.scale_matrix)
        #self.update_markers()
        self.updateAnnotation()

    def updateAnnotation(self):
        if self._motion.get_current_frame_idx() < self._motion.get_n_annotations():
            current_annotation = self._motion.get_current_annotation()
            self._visualization.set_color(current_annotation["color"])

    def get_current_annotation_label(self):
        return self._motion.get_current_annotation_label()

    def resetAnimationTime(self):
        self._motion.reset()
        self.updateTransformation()

    def setCurrentFrameNumber(self, frame_idx):
        self._motion.set_frame_idx(frame_idx)
        self.updateTransformation()
        #self.update_markers()

    def getNumberOfFrames(self):
        return self._motion.get_n_frames()

    def isLoadedCorrectly(self):
        return self._motion is not None

    def getFrameTime(self):
        if self.isLoadedCorrectly():
            # print self.frameTime
            return self._motion.get_frame_time()
        else:
            return 0

    def getScaleFactor(self):
        if self.isLoadedCorrectly():
            return self.scaleFactor
        else:
            return -1

    def getFilePath(self):
        if self.isLoadedCorrectly():
            return self.filePath

    def getNumberOfJoints(self):
        return len(self.skeleton.get_n_joints())


    def setColor(self, color):
        print("set color", color)
        self._visualization.set_color(color)

    def getColor(self):
        return self._visualization.color

    def getPosition(self):
        m = self.scene_object.transformation
        if self._motion is not None:
            root = self.skeleton.root
            pos = self.skeleton.nodes[root].offset + self._motion.get_pose()[:3]
            pos = [pos[0], pos[1], pos[2], 1]
            pos = np.dot(m, pos)[:3]
            return np.array(pos)
        else:
            return m[3,:3]

    def get_visualization(self):
        return self._visualization

    def create_ragdoll(self, use_reference_frame=True, create_markers=True):
        if self._motion is not None and self.skeleton.skeleton_model is not None:
            frame = self._motion.get_pose()
            skeleton = self.skeleton
            if use_reference_frame:
                frame = skeleton.get_reduced_reference_frame()
            o = self.scene_object.scene.object_builder.create_component("ragdoll_from_skeleton", skeleton, frame, figure_def, add_contact_vis=False)
            #o = self.scene_object.scene.object_builder.create_ragdoll_from_skeleton(self.skeleton, frame)
            self.scene_object.scene.addAnimationController(o, "character_animation_recorder")
            self.recorder = o._components["character_animation_recorder"]
        if create_markers:
            self.create_markers()

    def create_markers(self, figure_def, scale=1.0):
        if self.recorder is not None:
            markers = self.recorder.generate_constraint_markers_v9(self, scale, figure_def)
            self.attach_constraint_markers(markers)

    def attach_constraint_markers(self, markers):
        self.markers = markers

    def detach_constraint_markers(self):
        self.markers = dict()

    def update_markers(self):
        frame = self._motion.get_pose()
        scale = self.scene_object.scale_matrix[0][0]
        for joint in list(self.markers.keys()):
            for marker in self.markers[joint]:
                m = self.skeleton.nodes[joint].get_global_matrix(frame, True)
                position = np.dot(m, marker["relative_trans"])[:3, 3]
                marker["object"].setPosition(position*scale)

    def toggle_animation_loop(self):
        self.loopAnimation = not self.loopAnimation

    def get_bvh_string(self):
        skeleton = self.skeleton
        print("generate bvh string", len(skeleton.animated_joints))
        frames = self._motion.get_frames()
        frames = skeleton.add_fixed_joint_parameters_to_motion(frames)
        frame_time = self._motion.get_frame_time()
        bvh_writer = BVHWriter(None, skeleton, frames, frame_time, True)
        return bvh_writer.generate_bvh_string()

    def get_json_data(self):
        self._motion.mv.skeleton = self.skeleton
        return self._motion.mv.to_db_format()

    def export_to_file(self, filename, export_format="bvh", frame_range=None):
        if self._motion is None: 
            return
        frame_time = self._motion.get_frame_time()
        skeleton = self.skeleton
        frames = self._motion.get_frames()
        frames = np.array(frames)
        print("ref frame length",skeleton.reference_frame_length)
        joint_count = 0
        for joint_name in skeleton.nodes.keys():
            if len(skeleton.nodes[joint_name].children) > 0 and "EndSite" not in joint_name:
                joint_count+=1
        skeleton.reference_frame_length = joint_count * 4 + 3
        frames = skeleton.add_fixed_joint_parameters_to_motion(frames)
        if export_format == "bvh":
            if frame_range is not None:
                bvh_writer = BVHWriter(None, skeleton, frames[frame_range[0]:frame_range[1],:], frame_time, True)
            else:
                bvh_writer = BVHWriter(None, skeleton, frames, frame_time, True)
            bvh_writer.write(filename)
        elif export_format == "fbx":
            mv = MotionVector(skeleton)
            mv.frames = frames
            mv.n_frames = len(frames)
            mv.frame_time = frame_time
            export_motion_vector_to_fbx_file(self.skeleton,
                                                mv, filename)
        elif export_format == "json":
            self.skeleton.save_to_json(filename)
        else:
            print("unsupported format", export_format)

    def retarget_from_src(self, src_controller, scale_factor=1.0, src_model=None, target_model=None, frame_range=None):
        target_skeleton = self.skeleton
        frame_time = src_controller.get_frame_time()
        if target_model is not None:
            target_skeleton.skeleton_model = target_model
        new_frames = None
        if type(src_controller) == SkeletonAnimationController:
            src_skeleton = src_controller.skeleton
            src_frames = src_controller._motion.get_frames()
            if src_model is not None:
                src_skeleton.skeleton_model = src_model
            if src_skeleton.identity_frame is None or target_skeleton.identity_frame is None:
                raise Exception("Error identiframe is None")
            new_frames = retarget_from_src_to_target(src_skeleton, target_skeleton, src_frames, scale_factor=scale_factor, frame_range=frame_range)
        elif type(src_controller) == PointCloudAnimationController:
            src_joints = src_controller._joints
            src_frames = src_controller._animated_points
            if src_model is None:
                src_model = src_controller.skeleton_model
            new_frames = retarget_from_point_cloud_to_target(src_joints, src_model, target_skeleton, src_frames, scale_factor=scale_factor, frame_range=frame_range)

        if new_frames is not None:
            self._motion.mv.frames = new_frames
            self._motion.mv.n_frames = len(new_frames)
            self._motion.frame_idx = 0
            self._motion.mv.frame_time = frame_time
            self.currentFrameNumber = 0
            self.updateTransformation()
            self.update_scene_object.emit(-1)
            self.updated_animation_frame.emit(self.currentFrameNumber)
            print("finished retargeting", self._motion.get_n_frames(), "frames")
        return self._motion.get_n_frames()

    def retarget_from_frames(self, src_skeleton, src_frames, scale_factor=1.0, target_model=None, frame_range=None, place_on_ground=False, joint_filter=None):
        target_skeleton = self.skeleton
        if target_model is not None:
            target_skeleton.skeleton_model = target_model
        new_frames = retarget_from_src_to_target(src_skeleton, target_skeleton, src_frames,
                                                 scale_factor=scale_factor, frame_range=frame_range, place_on_ground=place_on_ground, joint_filter=joint_filter)
        if new_frames is not None:
            self._motion.mv.frames = new_frames
            self._motion.mv.n_frames = len(new_frames)
            print("finished retargeting", self._motion.get_n_frames(), "frames")
        return self._motion.get_n_frames()


    def set_scale(self, scale_factor):
        #self._visualization.set_scale(scale_factor)
        color = self._visualization.color

        #self._motion.mv.frames[:,:3] *= scale_factor
        skeleton = self.skeleton
        skeleton.scale(scale_factor)
        self._motion.mv.scale_root(scale_factor)
        self._visualization = SkeletonVisualization(self.scene_object, color)
        self._visualization.set_skeleton(skeleton)
        self.updateTransformation()
        self.scene_object.transformation = np.eye(4)

    def load_annotation(self, filename):
        with open(filename, "r") as in_file:
            annotation_data = json.load(in_file)
            semantic_annotation = annotation_data["semantic_annotation"]
            color_map = annotation_data["color_map"]
            self.set_color_annotation(semantic_annotation, color_map)

    def save_annotation(self, filename):
        with open(filename, "w") as out_file:
            data = dict()
            data["semantic_annotation"] = self._motion._semantic_annotation
            data["color_map"] = self._motion.label_color_map
            json.dump(data, out_file)

    def plot_joint_trajectories(self, joint_list):
        joint_objects = []
        for j in joint_list:
            o = self.plot_joint_trajectory(j)
            if o is not None:
                joint_objects.append(o)
        return joint_objects

    def plot_joint_trajectory(self, joint_name):
        scene_object = None
        if joint_name in list(self.skeleton.nodes.keys()):
            trajectory = list()
            for f in self._motion.get_frames():
                p = self.get_joint_position(joint_name, f)
                if p is not None:
                    trajectory.append(p)
            if len(trajectory) > 0:
                name = self.scene_object.name + "_" + joint_name + "_trajectory"
                scene_object = self.scene_object.scene.addSplineObject(name, trajectory, get_random_color(), granularity=500)
            else:
                print("No points to plot for joint", joint_name)
        return scene_object

    def get_joint_position(self, joint_name, frame):
        if joint_name in self.skeleton.nodes.keys():
            return self.skeleton.nodes[joint_name].get_global_position(frame)
        else:
            return None

    def get_skeleton_copy(self):
        return deepcopy(self.skeleton)

    def get_motion_vector_copy(self, start_frame=0, end_frame=-1):
        mv_copy = MotionVector()
        if end_frame > 0:
            mv_copy.frames = deepcopy(self._motion.mv.frames[start_frame: end_frame])
        else:
            mv_copy.frames = np.array(self._motion.mv.frames)
        mv_copy.n_frames = len(mv_copy.frames)
        mv_copy.frame_time = self._motion.mv.frame_time
        return mv_copy

    def get_current_frame(self):
        return self._motion.get_pose()

    def apply_delta_frame(self, skeleton, frame):
        self._motion.apply_delta_frame(skeleton, frame)

    def replace_current_frame(self, frame):
        self._motion.replace_current_frame(frame)
        self.updateTransformation()

    def replace_current_frames(self, frames):
        self._motion.replace_frames(frames)

    def replace_motion_from_file(self, filename):
        if filename.endswith(".bvh"):
            bvh_reader = BVHReader(filename)
            motion_vector = MotionVector()
            motion_vector.from_bvh_reader(bvh_reader, False)
            self._motion.replace_frames(motion_vector.frames)
            self.currentFrameNumber = 0
            self.updateTransformation()
            self.update_scene_object.emit(-1)
            self.updated_animation_frame.emit(self.currentFrameNumber)
        elif filename.endswith("_mg.zip"):
            self.scene_object.scene.attach_mg_state_machine(self.scene_object, filename)
            self._motion = self.scene_object._components["morphablegraph_state_machine"]
            self._motion.set_target_skeleton(self.skeleton)
            self.activate_emit = False
        elif filename.endswith("amc"):
            amc_frames = parse_amc_file(filename)
            motion_vector = MotionVector()
            motion_vector.from_amc_data(self.skeleton, amc_frames)
            self._motion.replace_frames(motion_vector.frames)
            self._motion.mv.frame_time = 1.0/120
            self.currentFrameNumber = 0
            self.updateTransformation()
            self.update_scene_object.emit(-1)
            self.updated_animation_frame.emit(self.currentFrameNumber)

    def replace_motion_from_str(self, bvh_str):
        bvh_reader = BVHReader("")
        lines = bvh_str.split("\n")
        print(len(lines))
        lines = [l for l in lines if len(l) > 0]
        bvh_reader.process_lines(lines)
        motion_vector = MotionVector()
        motion_vector.from_bvh_reader(bvh_reader, False)
        self._motion.replace_frames(motion_vector.frames)


    def replace_skeleton_model(self, filename):
        data = load_json_file(filename)
        model = data  # ["skeleton_model"]
        self.set_skeleton_model(model)

    def set_skeleton_model(self, model):
        self.skeleton.skeleton_model = model

    def attach_animated_mesh_component(self, filename, animation_controller="animation_controller"):
        scene = self.scene_object.scene
        model_data = load_model_from_fbx_file(filename)
        scene.object_builder.create_component("animated_mesh", self.scene_object, model_data, animation_controller)

    def get_bone_matrices(self):
        return self._visualization.matrices

    def set_color_annotation_from_labels(self, labels, colors):
        self._motion.set_color_annotation_from_labels(labels, colors)

    def set_reference_frame(self, frame_idx):
        self.skeleton.set_reference_frame(self._motion.get_pose(frame_idx))

    def get_semantic_annotation(self):
        return self._motion.get_semantic_annotation()

    def get_label_color_map(self):
        return self._motion.get_label_color_map()

    def isPlaying(self):
        return self._motion.play

    def stopAnimation(self):
        self._motion.play = False

    def startAnimation(self):
        self._motion.play = True

    def toggleAnimation(self):
        self._motion.play = not self._motion.play

    def setAnimationSpeed(self, speed):
        self.animationSpeed = speed

    def get_current_frame_idx(self):
        return self._motion.get_current_frame_idx()

    def toggle_animation(self):
        self._motion.play = not self._motion.play

    def set_frame_time(self, frame_time):
        self._motion.mv.frame_time = frame_time

    def get_frames(self):
        return self._motion.get_frames()

    def get_max_time(self):
        return self._motion.get_n_frames() * self._motion.get_frame_time()

    def get_frame_time(self):
        return self._motion.get_frame_time()

    def get_skeleton(self):
        return self.skeleton

    def set_time(self, t):
        self._motion.set_time(t)

    def get_animated_joints(self):
        return self.skeleton.animated_joints

    def add_skeleton_mirror(self, snapshot_interval=10):
        skeleton_mirror = SkeletonMirrorComponent(self.scene_object, self._visualization, snapshot_interval)
        self.scene_object._components["skeleton_mirror"] = skeleton_mirror
        return skeleton_mirror

    def set_ticker(self, tick):
        self._motion.set_ticker(tick)

    def replace_frames(self, frames):
        return self._motion.replace_frames(frames)

    def get_labeled_points(self):
        p = [m[:3,3] for m in self._visualization.matrices]
        return self.get_animated_joints(), p
