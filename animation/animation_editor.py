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
import collections
import copy
import numpy as np
from transformations import quaternion_matrix, quaternion_multiply, quaternion_from_euler, euler_from_quaternion, quaternion_from_euler, quaternion_matrix, quaternion_from_matrix, quaternion_multiply
from ..scene.scene_object import SceneObject
from ..scene.components import ComponentBase
from ..scene.utils import get_random_color
from anim_utils.motion_editing.motion_editing import MotionEditing, KeyframeConstraint
from anim_utils.motion_editing import FootplantConstraintGenerator
from anim_utils.motion_editing.motion_grounding import MotionGrounding, add_heels_to_skeleton
from anim_utils.motion_editing.footplant_constraint_generator import guess_ground_height
from anim_utils.animation_data.skeleton_models import STANDARD_MIRROR_MAP, JOINT_CONSTRAINTS
from anim_utils.animation_data.motion_blending import create_transition_for_joints_using_slerp, BLEND_DIRECTION_FORWARD, BLEND_DIRECTION_BACKWARD, smooth_translation_in_quat_frames
from anim_utils.motion_editing.cubic_motion_spline import CubicMotionSpline


IK_SETTINGS = {
        "tolerance": 0.05,
        "optimization_method": "L-BFGS-B",
        "max_iterations": 1000,
        "interpolation_window": 120,
        "transition_window": 60,
        "use_euler_representation": False,
        "solving_method": "unconstrained",
        "activate_look_at": True,
        "max_retries": 5,
        "success_threshold": 5.0,
        "optimize_orientation": True,
        "elementary_action_max_iterations": 5,
        "elementary_action_optimization_eps": 1.0,
        "adapt_hands_during_carry_both": True,
        "constrain_place_orientation": False,
        "activate_blending": True
    }

def flip_coordinate_system(q):
    """
    as far as i understand it is assumed that we are already in a different coordinate system
    so we first flip the coordinate system to the original coordinate system to do the original transformation
    then flip coordinate system again to go back to the flipped coordinate system
    this results in the original transformation being applied in the flipped transformation
    http://www.ch.ic.ac.uk/harrison/Teaching/L4_Symmetry.pdf
    http://gamedev.stackexchange.com/questions/27003/flip-rotation-matrix
    https://www.khanacademy.org/math/linear-algebra/alternate_bases/change_of_basis/v/lin-alg-alternate-basis-tranformation-matrix-example
    """
    conv_m = np.array([[-1, 0, 0,  0],
                         [0, 1, 0, 0],
                          [0, 0, 1, 0],
                          [0, 0,  0, 1]])


    m = quaternion_matrix(q)
    new_m = np.dot(conv_m, np.dot(m, conv_m))
    return quaternion_from_matrix(new_m)


def swap_parameters(frame, node_names, mirror_map):
    # mirror joints
    temp = copy.deepcopy(frame[:])
    for node_name in node_names:
        if node_name in mirror_map.keys():
            target_node_name = mirror_map[node_name]
            src = node_names.index(node_name) * 4 + 3
            dst = node_names.index(target_node_name) * 4 + 3
            frame[dst:dst + 4] = temp[src:src + 4]
    return frame



def flip_root_coordinate_system(q1):
    conv_m = np.array([[-1, 0, 0, 0],
                       [0, 1, 0, 0],
                       [0, 0, -1, 0],
                       [0, 0, 0, 1]])


    m = quaternion_matrix(q1)
    new_m = np.dot(conv_m, np.dot(m, conv_m))
    q2 = quaternion_from_matrix(new_m)
    flip_q = quaternion_from_euler(*np.radians([0, 0, 180]))
    q2 = quaternion_multiply(flip_q, q2)
    return q2

def flip_pelvis_coordinate_system(q):
    conv_m = np.array([[1, 0, 0, 0],
                       [0, 1, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]])


    m = quaternion_matrix(q)
    new_m = np.dot(conv_m, np.dot(m, conv_m))
    q = quaternion_from_matrix(new_m)
    flip_q = quaternion_from_euler(*np.radians([0, 0, 180]))
    q = quaternion_multiply(flip_q, q)
    return q

def flip_custom_coordinate_system_legs(q):
    conv_m = np.array([[1, 0, 0, 0],
                       [0, -1, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]])


    m = quaternion_matrix(q)
    new_m = np.dot(conv_m, np.dot(m, conv_m))
    q = quaternion_from_matrix(new_m)

    conv_m = np.array([[-1, 0, 0, 0],
                       [0, 1, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]])


    m = quaternion_matrix(q)
    new_m = np.dot(conv_m, np.dot(m, conv_m))
    q = quaternion_from_matrix(new_m)
    return q

def flip_custom_coordinate_system(q):
    conv_m = np.array([[1, 0, 0, 0],
                       [0, 1, 0, 0],
                       [0, 0, 1, 0],
                       [0, 0, 0, 1]])


    m = quaternion_matrix(q)
    new_m = np.dot(conv_m, np.dot(m, conv_m))
    q = quaternion_from_matrix(new_m)
    return q


def flip_custom_coordinate_system_hips(q):
    conv_m = np.array([[1, 0, 0, 0],
                       [0, 1, 0, 0],
                       [0, 0, -1, 0],
                       [0, 0, 0, 1]])


    m = quaternion_matrix(q)
    new_m = np.dot(conv_m, np.dot(m, conv_m))
    q = quaternion_from_matrix(new_m)
    flip_q = quaternion_from_euler(*np.radians([0, 180, 0]))
    q = quaternion_multiply(flip_q, q)
    return q



def flip_custom_coordinate_system_shoulders(q):
    flip_q = quaternion_from_euler(*np.radians([180, 0, 0]))
    q = quaternion_multiply(flip_q, q)
    return q


def flip_custom_root_coordinate_system(q):
    conv_m = np.array([[1, 0, 0, 0],
                       [0, -1, 0, 0],
                       [0, 0, -1, 0],
                       [0, 0, 0, 1]])


    m = quaternion_matrix(q)
    new_m = np.dot(conv_m, np.dot(m, conv_m))
    q = quaternion_from_matrix(new_m)
    return q



def mirror_animation_custom(node_names, frames, mirror_map):
    """
    http://www.gamedev.sk/mirroring-animations
    http://stackoverflow.com/questions/1263072/changing-a-matrix-from-right-handed-to-left-handed-coordinate-system
    """
    new_frames = []
    temp = frames[:]
    for frame in temp:
        new_frame = frame[:]
        #handle root separately
        new_frame[:3] =[-new_frame[0],new_frame[1],new_frame[2]]
        # bring rotation into different coordinate system
        for idx, node_name in enumerate(node_names):
            o = idx * 4 + 3
            q = copy.copy(new_frame[o:o + 4])
            if node_name in ["FK_back1_jnt","FK_back2_jnt","FK_back3_jnt", "FK_back4_jnt"]:
                q = flip_custom_root_coordinate_system(q)
            elif "upLeg" in node_name:
                q = flip_custom_coordinate_system_hips(q)
            elif "Leg" in node_name or "foot" in node_name:
                q = flip_custom_coordinate_system_legs(q)
            elif "shoulder_jnt" in node_name:
                q = flip_custom_coordinate_system_shoulders(q)
            elif node_name == "Root":
                q = flip_root_coordinate_system(q)
            else:
                q = flip_custom_coordinate_system(q)
            new_frame[o:o+4] = q
        new_frame = swap_parameters(new_frame, node_names, mirror_map)

        new_frames.append(new_frame)
    return np.array(new_frames)


def mirror_animation(node_names,frames,mirror_map, joint_map):
    """
    http://www.gamedev.sk/mirroring-animations
    http://stackoverflow.com/questions/1263072/changing-a-matrix-from-right-handed-to-left-handed-coordinate-system
    """
    new_frames = []
    temp = frames[:]
    for frame in temp:
        new_frame = frame[:]
        #handle root separately
        new_frame[:3] =[-new_frame[0],new_frame[1],new_frame[2]]

        # bring rotation into different coordinate system
        for idx, node_name in enumerate(node_names):
            o = idx * 4 + 3
            q = copy.copy(new_frame[o:o + 4])
            #if node_name == joint_map["pelvis"]:
            #    q = flip_pelvis_coordinate_system(q)
            if node_name == joint_map["root"]:
                q = flip_pelvis_coordinate_system(q)
                #q = flip_root_coordinate_system(q)
            else:
                #q = flip_coordinate_system(q)
                q = flip_custom_coordinate_system(q)

            new_frame[o:o+4] = q


        new_frame = swap_parameters(new_frame, node_names, mirror_map)

        new_frames.append(new_frame)
    return new_frames



def smooth_using_moving_average(src_frames, window=4):
    """ https://www.wavemetrics.com/products/igorpro/dataanalysis/signalprocessing/smoothing.htm#MovingAverage
    """
    n_frames = len(src_frames)
    n_dims = len(src_frames[0])
    new_frames = np.zeros(src_frames.shape)
    new_frames[0,:] = src_frames[0,:]
    hw = int(window/2)
    for i in range(0, n_frames):
        for j in range(n_dims):
            start = max(0, i-hw)
            end = min(n_frames-1, i+hw)
            w = end-start
            new_frames[i, j] = np.sum(src_frames[start:end, j])/w
    return new_frames


def apply_blending(skeleton, frames, joint_list, joint_index_list, dest_start, dest_end, n_blend_range):
    n_frames = len(frames)
    blend_start = max(dest_start- n_blend_range, 0)
    start_window = dest_start -blend_start
    blend_end =  min(dest_end +n_blend_range, n_frames-1)
    end_window = blend_end- dest_end
        #remove root indices
    print("blend ", dest_start, dest_end, n_blend_range, start_window, end_window)
    quat_joint_index_list = list(joint_index_list)
    if skeleton.root in joint_list:
        # apply root smnoothing and remove from index list
        if start_window > 0:
            frames = smooth_translation_in_quat_frames(frames, dest_start, start_window)
        if end_window > 0:
            frames = smooth_translation_in_quat_frames(frames, dest_end, end_window)
        for i in range(3):
            quat_joint_index_list.remove(i)
    
    if len(quat_joint_index_list) > 0:
        o = 0
        for j in joint_list:
            q_indices = quat_joint_index_list[o:o+4]
            if start_window > 0:
                frames = create_transition_for_joints_using_slerp(frames, q_indices, blend_start, dest_start, start_window, BLEND_DIRECTION_FORWARD)
            if end_window > 0:
                print(j, q_indices)
                frames = create_transition_for_joints_using_slerp(frames, q_indices, dest_end, blend_end, end_window, BLEND_DIRECTION_BACKWARD)
            o += 4
    
    return frames




class AnimationEditorBase(object):
    """ class for interactive definition of a set of ik constraints and wrapper for other animation editing functions
    """
    def __init__(self, skeleton, motion_vector):
        self.skeleton = skeleton
        self.motion_vector = motion_vector
        self.motion_backup = None
        self.constraints = []
        self.ik_settings = IK_SETTINGS
        self.motion_editing = MotionEditing(self.skeleton, self.ik_settings)
        
        if skeleton.skeleton_model is not None and "joint_constraints" in skeleton.skeleton_model:
            self.motion_editing.add_constraints_to_skeleton(skeleton.skeleton_model["joint_constraints"])
        self.edit_stash = list()
        self.command_history = list()
        self.foot_joints = []
        self.set_foot_joints()
        self.motion_grounding = MotionGrounding(self.skeleton, self.ik_settings, self.skeleton.skeleton_model, use_analytical_ik=True)
        self.footplant_settings = {"window": 20, "tolerance": 1, "constraint_range": 10, "smoothing_constraints_window": 15}

    def set_foot_joints(self):
        self.foot_joints = []
        if "joints" in self.skeleton.skeleton_model:
            for j in ["left_ankle", "right_ankle", "left_toe", "right_toe"]:
                joint_name = self.skeleton.skeleton_model["joints"][j]
                if joint_name is not None:
                    self.foot_joints.append(joint_name)

    def guess_ground_height(self, use_feet=True):
        motion = self.get_motion()
        skeleton = self.get_skeleton()
        if use_feet and len(self.foot_joints) > 0:
            minimum_height = guess_ground_height(skeleton, motion.frames, 0, 5, self.foot_joints)
        else:
            minimum_height = motion.frames[0, 1]
        return minimum_height
        
    def undo(self):
        frames = None
        if len(self.edit_stash) > 0:
            self.command_history.pop(-1)
            frames = self.edit_stash.pop(-1)
            self.motion_vector.frames = frames
            self.motion_vector.n_frames = len(frames)
            print("undo")
        return frames

    def save_state(self, command, parameters):
        frames = np.array(self.motion_vector.frames)
        self.edit_stash.append(frames)
        self.command_history.append((command, parameters))

    def get_constraints(self):
        return self.constraints

    def add_constraint(self, frame_idx, joint_name, constraint_object):
        c = (frame_idx, joint_name, constraint_object)
        self.constraints.append(c)

    def clear_constraints(self):
        self.constraints = []

    def translate_joint(self, joint_name, offset, frame_range, use_ccd=True, plot=False, apply=True):
        self.save_state("translate_joint", (joint_name, offset, frame_range))
        edit_start, edit_end = frame_range
        if joint_name != self.skeleton.root:
            frames = self.motion_vector.frames
            for frame_idx in range(edit_start, edit_end):
                p = self.skeleton.nodes[joint_name].get_global_position(frames[frame_idx])
                p += offset
                self.add_constraint(frame_idx, joint_name, p)
            if apply:
                if use_ccd:
                    self.apply_constraints_using_ccd(plot)
                else:
                    self.apply_constraints(plot)
            #self._animation_editor.apply_joint_translation_offset(joint_name, [x,y,z], frame_range)
        else:
            self.translate_frames(offset, frame_range)

    def rotate_joint(self, joint_name, offset, frame_range, window_size):
        self.save_state("rotate_joint", (joint_name, offset, frame_range, window_size))
        if joint_name != self.skeleton.root:
            self.apply_joint_rotation_offset(joint_name, offset, frame_range, window_size)
        else:
            self.rotate_frames(offset, frame_range)

    def fix_joint(self, joint_name, position, frame_range, apply=True):
        self.save_state("fix_joint",(joint_name, position, frame_range))
        edit_start, edit_end = frame_range
        #self._animation_editor.clear_constraints()
        for frame_idx in range(edit_start, edit_end):
            self.add_constraint(frame_idx, joint_name, position)
        if apply:
            self.apply_constraints_using_ccd()

    def apply_constraints(self, plot_curve=False):
        motion = self.get_motion()
        frames = motion.frames
        self.motion_backup = np.array(frames[:])
        # get current position from objects
        _constraints = collections.OrderedDict()
        for c in self.constraints:
            frame_idx = c[0]
            joint_name = c[1]
            if frame_idx not in _constraints.keys():
                _constraints[frame_idx] = dict()
            
            if isinstance(c[2], SceneObject):
                p = c[2].getPosition()
            else:
                p = c[2]
            _constraints[frame_idx][joint_name] = KeyframeConstraint(c[0], c[1], p)

        # sort https://docs.python.org/dev/library/collections.html#ordereddict-examples-and-recipes
        _constraints = collections.OrderedDict(sorted(_constraints.items(), key=lambda t: t[0]))

        new_frames = self.motion_editing.edit_motion_using_displacement_map(frames, _constraints, plot=plot_curve)
        #self._animation_controller.replace_current_frames(new_frames)
        motion.frames = new_frames

    def apply_constraints_using_ccd(self, plot_curve=False):
        motion = self.get_motion()
        frames = motion.frames
        self.motion_backup = np.array(frames[:])
        # get current position from objects
        _constraints = collections.OrderedDict()
        for c in self.constraints:
            frame_idx = c[0]
            joint_name = c[1]
            if frame_idx not in _constraints.keys():
                _constraints[frame_idx] = dict()
            
            if isinstance(c[2], SceneObject):
                p = c[2].getPosition()
            else:
                p = c[2]
            _constraints[frame_idx][joint_name] = KeyframeConstraint(c[0], c[1], p)

        # sort https://docs.python.org/dev/library/collections.html#ordereddict-examples-and-recipes
        _constraints = collections.OrderedDict(sorted(_constraints.items(), key=lambda t: t[0]))
        if len(frames) > 1:
            new_frames = self.motion_editing.edit_motion_using_displacement_map_and_ccd(frames, _constraints, plot=plot_curve)
        else:
            frame_idx = 0
            frame_constraints = [_constraints[frame_idx][joint_name]]
            n_max_iter = 2
            chain_end_joints = None
            new_frames = np.array(frames)
            new_frames[0] = self.skeleton.reach_target_positions(new_frames[0], frame_constraints, chain_end_joints, n_max_iter=n_max_iter, verbose=False)
        #self._animation_controller.replace_current_frames(new_frames)
        motion.frames = new_frames


    def get_skeleton(self):
        return self.skeleton

    def get_motion(self):
        return self.motion_vector

    def delete_frames_after(self, frame_idx):
        self.save_state("delete_after", (frame_idx,))
        motion = self.get_motion()
        motion.frames = motion.frames[:frame_idx + 1]
        motion.n_frames = len(motion.frames)
        #self.set_object(self._controller)

    def delete_frames_before(self, frame_idx):
        self.save_state("delete_before", (frame_idx,))
        motion = self.get_motion()
        motion.frames = motion.frames[frame_idx:]
        motion.n_frames = len(motion.frames)
        # self.animationFrameSlider.setValue(0)
        # self.set_object(self._controller)

    def translate_frames(self, offset, frame_range=None):
        motion = self.get_motion()
        motion.frames = np.array(motion.frames)
        if frame_range is None:
            start_frame = 0
            end_frame = motion.n_frames
        else:
            start_frame, end_frame = frame_range
            end_frame = min(motion.n_frames, end_frame+1)
        if motion.frames.ndim == 1:
            motion.frames = motion.frames.reshape((1, len(motion.frames)))
     
        for idx in range(start_frame, end_frame): 
            motion.frames[idx,:3] += offset

    def rotate_frames(self, euler, frame_range=None):
        motion = self.get_motion()
        motion.frames = np.array(motion.frames)
        if frame_range is None:
            start_frame = 0
            end_frame = motion.n_frames
        else:
            start_frame, end_frame = frame_range
            end_frame = min(motion.n_frames, end_frame+1)
        if motion.frames.ndim == 1:
            motion.frames = motion.frames.reshape((1, len(motion.frames)))
        delta_q = quaternion_from_euler(*np.radians(euler))
        delta_m = quaternion_matrix(delta_q)[:3, :3]
        for idx in range(start_frame, end_frame):
            old_t = motion.frames[idx, :3]
            old_q = motion.frames[idx, 3:7]
            motion.frames[idx, :3] = np.dot(delta_m, old_t)[:3]
            motion.frames[idx, 3:7] = quaternion_multiply(delta_q, old_q)

    def apply_joint_rotation_offset(self, joint_name, euler, frame_range=None, blend_window_size=None):
        motion = self.get_motion()
        print("euler ", euler)
        delta_q = quaternion_from_euler(*np.radians(euler))
        if motion.frames.ndim == 1:
            motion.frames = motion.frames.reshape((1, len(motion.frames)))
        j_offset = self.get_skeleton().animated_joints.index(joint_name)*4 + 3
        if frame_range is None:
            start_frame = 0
            end_frame = motion.n_frames
        else:
            start_frame, end_frame = frame_range
            end_frame = min(motion.n_frames, end_frame+1)
        for idx in range(start_frame, end_frame):
            old_q = motion.frames[idx, j_offset:j_offset+4]
            motion.frames[idx,  j_offset:j_offset+4] = quaternion_multiply(delta_q, old_q)
        
        if frame_range is not None and blend_window_size is not None:
            joint_list = [joint_name]
            offset = self.skeleton.nodes[joint_name].quaternion_frame_index * 4 + 3
            joint_index_list = list(range(offset,offset+4))
            motion.frames = apply_blending(self.skeleton, motion.frames, 
                        joint_list, joint_index_list, start_frame, end_frame-1, blend_window_size)


    def concatenate(self, other, apply_smoothing, window_size):
        other_frames = np.array(other._motion.mv.frames[:])
        motion = self.get_motion()
        self.motion_backup = np.array(motion.frames[:])
        motion.smoothing_window = window_size
        motion.apply_spatial_smoothing = apply_smoothing
        motion.append_frames(other_frames)

    def smooth_using_moving_average(self, window=4):
        """ https://www.wavemetrics.com/products/igorpro/dataanalysis/signalprocessing/smoothing.htm#MovingAverage
        """
        self.save_state("smooth",(window,))
        motion = self.get_motion()
        motion.frames = smooth_using_moving_average(motion.frames, window)
        motion.n_frames = len(motion.frames)

    def get_animated_joints(self):
        return self.get_skeleton().animated_joints

    def mirror_animation(self):
        self.save_state("mirror_animation", None)
        motion = self.get_motion()
        skeleton = self.get_skeleton()
        if skeleton.skeleton_model is None or "joints" not in skeleton.skeleton_model:
            print("Error: The skeleton has no model")
            return
        standard_mirror_map = STANDARD_MIRROR_MAP
        joint_map = skeleton.skeleton_model["joints"]
        mirror_map = dict()
        for k, v in standard_mirror_map.items():
            if k not in joint_map or v not in joint_map:
                print("skip", k, v)
                continue
            mk = joint_map[k]
            mv = joint_map[v]
            mirror_map[mk] = mv
        frames = np.array(motion.frames)
        motion.frames = mirror_animation_custom(skeleton.animated_joints, frames, mirror_map)

    def apply_edit(self, func_name, params):
        """ call method with corresponding name and parameters"""
        if hasattr(self, func_name):
            print("apply", func_name, params)
            func = getattr(self, func_name)
            if params is not None:
                func(*params)
            else:
                func()
        else:
            print(func_name, "not found")

    def resample_motion(self, resample_factor):
        self.save_state("resample_motion", resample_factor)
        motion = self.get_motion()
        frames = motion.frames
        n_frames = len(frames)
        times = list(range(0, n_frames))
        spline = CubicMotionSpline.fit_frames(self.skeleton, times, frames)
        n_dest_frames = n_frames*resample_factor
        step_size = (n_frames-1)/n_dest_frames
        streched_times = np.arange(0,n_frames-1,step_size)
        #print(streched_times)
        new_frames = []
        for t in streched_times:
            f = spline.evaluate(t)
            new_frames.append(f)
        print("new frames", len(new_frames))
        motion.frames = new_frames
        motion.n_frames = len(new_frames)
        return motion.n_frames

    def flip_blender_coordinate_systems(self):
        self.save_state("flip_blender_coordinatesystem", None)
        motion = self.get_motion()
        motion.frames = np.array(motion.frames)
        skeleton = self.get_skeleton()
        for j in skeleton.nodes.keys():
            offset = skeleton.nodes[j].offset
            x = offset[0]
            y = offset[1]
            z = offset[2]
            skeleton.nodes[j].offset = [x,z,-y]
        for idx in range(motion.n_frames):
            t = motion.frames[idx,:3] 
            motion.frames[idx,:3] = [t[0],t[2],-t[1]]
            o = 3
            for j in skeleton.animated_joints:
                q = motion.frames[idx,o:o+4]
                q = [q[0], q[1], q[3], -q[2]]
                motion.frames[idx,o:o+4] = q
                o+=4


class AnimationEditor(AnimationEditorBase, ComponentBase):
    def __init__(self, scene_object):
        ComponentBase.__init__(self, scene_object)
        self._animation_controller = scene_object._components["animation_controller"]
        skeleton = self._animation_controller._visualization.skeleton
        if skeleton.skeleton_model is None:
            skeleton.skeleton_model = dict()
        AnimationEditorBase.__init__(self, skeleton, self._animation_controller._motion.mv)
    
    def undo_edit(self):
        if self.motion_backup is not None:
            self._animation_controller.replace_current_frames(self.motion_backup)

    def move_to_ground(self, source_ground_height, target_ground_height):
        motion = self.get_motion()
        frames = motion.frames
        for f in frames:
            f[1] += target_ground_height - source_ground_height
        self._animation_controller.replace_current_frames(frames)

    def detect_ground_contacts(self, source_ground_height):
        motion = self.get_motion()
        if "ik_chains" not in self.skeleton.skeleton_model:
            return
        constraint_generator = FootplantConstraintGenerator(self.skeleton, self.skeleton.skeleton_model,
                                                            self.footplant_settings, None, source_ground_height)
        ground_contacts = constraint_generator.detect_ground_contacts(motion.frames, foot_joints)

        color_map = {j: get_random_color() for j in self.foot_joints}
        semantic_annotation = dict()
        for idx in range(motion.n_frames):
            for label in ground_contacts[idx]:
                if label not in semantic_annotation:
                    semantic_annotation[label] = []
                semantic_annotation[label].append(idx)
        self._animation_controller.set_color_annotation(semantic_annotation, color_map)
        # self.init_label_time_line()

    def apply_foot_constraints(self, target_ground_height):
        motion = self.get_motion()
        if "ik_chains" not in self.skeleton.skeleton_model:
            return
        ground_contacts = [[] for f in range(motion.n_frames)]
        for label in self.foot_joints:
            if label in self.animation_controller._semantic_annotation:
                for idx in self.animation_controller._semantic_annotation[label]:
                    ground_contacts[idx].append(label)

        constraint_generator = FootplantConstraintGenerator(self.skeleton, self.skeleton.skeleton_model,
                                                            self.footplant_settings, None, target_ground_height)
        constraints, blend_ranges = foot_constraint_generator.generate(motion, ground_contacts)
        self.motion_grounding.clear()
        root = self.skeleton.root
        for joint_name, frame_ranges in blend_ranges.items():
            ik_chain = skeleton.skeleton_model["ik_chains"][joint_name]
            for frame_range in frame_ranges:
                joint_names = [root] + [ik_chain["root"], ik_chain["joint"], joint_name]
                self.motion_grounding.add_blend_range(joint_names, tuple(frame_range))
        self.motion_grounding.set_constraints(constraints)
        self._animation_controller._motion.mv.frames = self.motion_grounding.run(motion, target_ground_height)

    def undo(self):
        frames = AnimationEditorBase.undo(self)
        self._animation_controller.updateTransformation()
        return frames

    def apply_constraints(self, plot_curve=False):
        AnimationEditorBase.apply_constraints(self, plot_curve)
        self._animation_controller.updateTransformation()
    
    def apply_constraints_using_ccd(self, plot_curve=False):
        AnimationEditorBase.apply_constraints_using_ccd(self, plot_curve)
        self._animation_controller.updateTransformation()

    def rotate_frames(self, euler, frame_range=None):
        AnimationEditorBase.rotate_frames(self, euler, frame_range)
        self._animation_controller.updateTransformation()

    def apply_joint_rotation_offset(self, joint_name, euler, frame_range=None, blend_window_size=None):
        AnimationEditorBase.apply_joint_rotation_offset(self, joint_name, euler,frame_range, blend_window_size)
        self._animation_controller.updateTransformation()

    
    def translate_frames(self, offset, frame_range=None):
        AnimationEditorBase.translate_frames(self, offset, frame_range)
        self._animation_controller.updateTransformation()

    def get_current_frame_number(self):
        return self._animation_controller.get_current_frame_idx()