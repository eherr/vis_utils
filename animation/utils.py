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
from transformations import quaternion_multiply, quaternion_inverse, quaternion_matrix, quaternion_conjugate
from anim_utils.animation_data import BVHReader, MotionVector, SkeletonBuilder
from anim_utils.animation_data.motion_concatenation import get_orientation_vector_from_matrix, get_rotation_angle, quaternion_about_axis

def normalize(v):
    return v/np.linalg.norm(v)

def sign(x):
    return -1 if x < 0.0 else 1


def quaternion_to_av(q):
    """ according to lee 2000
    the purely imaginary quaternion is identical to the angular velocity
    the sign of the real part gives the direction
    Since the unit quaternion space is folded by the antipodal equivalence,
    the angular velocity is twice as fast
    """
    return 2 * np.array(q[1:]) * sign(q[0])


def av_to_quaternion(av):
    # https://math.stackexchange.com/questions/39553/how-do-i-apply-an-angular-velocity-vector3-to-a-unit-quaternion-orientation
    n_av = np.linalg.norm(av)
    if n_av == 0:
        return [1,0,0,0]
    temp = av / n_av * np.sin(n_av / 2)
    q = np.array([np.cos(n_av / 2), temp[0], temp[1], temp[2]])
    q = normalize(q)
    return q

def get_delta_av(a,b, dt):
    delta_q = quaternion_multiply(quaternion_conjugate(a), b)
    delta_q = normalize(delta_q)
    return -quaternion_to_av(delta_q) / dt

def calc_velocity(frames, frame_time):
    """ calculate linear and anuglar velocity in preceding pose coordinate system """
    n_frames = len(frames)
    vel = np.zeros((n_frames, 3))
    angular_vel = np.zeros((n_frames, 3))
    for idx in range(1, frames.shape[0]):
        root_q = frames[idx-1, 3:7]
        root_q = normalize(root_q)
        root_m = quaternion_matrix(root_q)
        #root_m[:3, 3] = motion_vector.frames[idx-1, :3]
        inv_root_m = np.linalg.inv(root_m)[:3,:3]
        v = frames[idx, :3] - frames[idx-1,:3]
        vel[idx] = np.dot(inv_root_m, v)
        av = get_delta_av(frames[idx, 3:7], frames[idx-1, 3:7], frame_time)
        angular_vel[idx] = np.dot(inv_root_m, av)
    return vel, angular_vel



def quaternion_from_vector_to_vector(a, b):
    "src: http://stackoverflow.com/questions/1171849/finding-quaternion-representing-the-rotation-from-one-vector-to-another"
    v = np.cross(a, b)
    w = np.sqrt((np.linalg.norm(a) ** 2) * (np.linalg.norm(b) ** 2)) + np.dot(a, b)
    q = np.array([w, v[0], v[1], v[2]])
    return q/ np.linalg.norm(q)



def add_frames(skeleton, a, b):
    """ returns c = a + b"""
    c = np.zeros(len(a))
    c[:3] = a[:3] + b[:3]
    for idx, j in enumerate(skeleton.animated_joints):
        o = idx * 4 + 3
        q_a = a[o:o + 4]
        q_b = b[o:o + 4]
        #print(q_a,q_b)
        q_prod = quaternion_multiply(q_a, q_b)
        c[o:o + 4] = q_prod / np.linalg.norm(q_prod)
    return c


def substract_frames(skeleton, a, b):
    """ returns c = a - b"""
    c = np.zeros(len(a))
    c[:3] = a[:3] - b[:3]
    for idx, j in enumerate(skeleton.animated_joints):
        o = idx*4 + 3
        q_a = a[o:o+4]
        q_b = b[o:o+4]
        q_delta = get_quaternion_delta(q_a, q_b)
        c[o:o+4] = q_delta / np.linalg.norm(q_delta)
    return c


def get_quaternion_delta(a, b):
    return quaternion_multiply(quaternion_inverse(b), a)


REF_VECTOR = [0,0,1]


def get_root_delta_angle(skeleton, node_name, frames, target_dir, ref_vector=REF_VECTOR):
    """returns the delta quaternion to align the root orientation with the target direction"""
    m = skeleton.nodes[node_name].get_global_matrix(frames[-1])
    dir_vec = get_orientation_vector_from_matrix(m[:3, :3], ref_vector)
    target_dir = [target_dir[0], target_dir[2]]
    angle = get_rotation_angle(dir_vec, target_dir)
    return  angle


def get_root_delta_q(skeleton, node_name, frames, target_dir, ref_vector=REF_VECTOR):
    """returns the delta quaternion to align the root orientation with the target direction"""
    m = skeleton.nodes[node_name].get_global_matrix(frames[-1])
    dir_vec = np.dot(m[:3, :3], ref_vector)
    dir_vec = normalize(dir_vec)
    q = quaternion_from_vector_to_vector(dir_vec, target_dir)
    return q


def generate_smoothing_factors(window, n_frames):
    """ Generate curve of smoothing factors
    """
    w = float(window)
    smoothing_factors = []
    for f in range(n_frames):
        f = float(f)
        value = 0.0
        if f <= w:
            value = 1 - (f/w)
        smoothing_factors.append(value)
    return np.array(smoothing_factors)


def smooth_quaternion_frames2(prev_frame, frames, window=20, include_root=True):
    """ Smooth quaternion frames given discontinuity frame

    Parameters
    ----------
    prev_frame : frame
    \tA quaternion frame
    frames: list
    \tA list of quaternion frames
    window : (optional) int, default is 20
    The smoothing window
    include_root:  (optional) bool, default is False
    \tSets whether or not smoothing is applied on the x and z dimensions of the root translation
    Returns
    -------
    None.
    """
    n_joints = int((len(frames[0]) - 3) / 4)
    # smooth quaternion
    n_frames = len(frames)
    for i in range(n_joints):
        for j in range(n_frames):
            q1 = np.array(prev_frame[3 + i * 4: 3 + (i + 1) * 4])
            q2 = np.array(frames[j][3 + i * 4:3 + (i + 1) * 4])
            if np.dot(q1, q2) < 0:
                frames[j][3 + i * 4:3 + (i + 1) * 4] = -frames[j][3 + i * 4:3 + (i + 1) * 4]

    smoothing_factors = generate_smoothing_factors(window, n_frames)
    #print("smooth", smoothing_factors)
    dofs = list(range(len(frames[0])))[3:]
    if include_root:
        dofs = [0,1,2] + dofs
    else:
        dofs = [1] + dofs
    new_frames = np.array(frames)
    for dof_idx in dofs:
        curve = np.array(frames[:, dof_idx])  # extract dof curve
        magnitude = prev_frame[dof_idx] - curve[0]
        new_frames[:, dof_idx] = curve + (magnitude * smoothing_factors)
    return new_frames


def get_trajectory_end_direction(control_points):
    b = np.array([control_points[-1][0], 0, control_points[-1][2]])
    a = np.array([control_points[-2][0], 0, control_points[-2][2]])
    return normalize(b-a)


def load_motion_from_bvh(filename):
    bvh_reader = BVHReader(filename)
    motion_vector = MotionVector()
    motion_vector.from_bvh_reader(bvh_reader, False)
    animated_joints = list(bvh_reader.get_animated_joints())
    motion_vector.skeleton = SkeletonBuilder().load_from_bvh(bvh_reader, animated_joints=animated_joints)
    return motion_vector
