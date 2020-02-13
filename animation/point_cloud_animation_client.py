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
import time
from transformations import euler_matrix, quaternion_from_matrix
from ..scene.components import ComponentBase
from ..io import load_json_file
from ..graphics.utils import get_translation_matrix
from ..graphics.renderer.lines import DebugLineRenderer
from ..graphics.renderer.primitive_shapes import SphereRenderer
from anim_utils.retargeting.point_cloud_retargeting import PointCloudRetargeting, generate_joint_map
from anim_utils.animation_data.skeleton_models import SKELETON_MODELS
import socket
import threading
import struct
#https://stackoverflow.com/questions/5415/convert-bytes-to-floating-point-numbers-in-python

DEFAULT_COLOR = [0, 0, 1]

def generate_message(target_dir):
    last_rotation = 0
    running = 0
    last_gender = 0
    message_type = 1 # query_frame
    message = [message_type, target_dir[0],
               target_dir[2],
               target_dir[1],
               last_rotation,
               running,
               last_gender]

    #return bytearray(message)
    message = struct.pack('1b6f', *message)

    return message


def client_thread(client):
    print("client started")
    client.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.socket.connect(client.address)

    while client.run:
        target_dir = client.vis.target_dir * client.vis.target_projection_len
        message = generate_message(target_dir)
        #print(message)
        client.socket.send(message)
        data = client.socket.recv(client.buffer_size)
        unpacked_data = struct.unpack("128f",data)
        #print("recieved", unpacked_data)
        client.vis.add_pose_to_queue(unpacked_data)
        time.sleep(client.dt)
    print("client stopped")
    client.socket.close()


class PCTCPClient(object):
    """ TCP client that sends and receives a single message
        https://pymotw.com/2/socket/tcp.html
    """
    BUFFER_SIZE = 10240
    def __init__(self, vis, url, port, dt, buffer_size=BUFFER_SIZE):
        self.vis = vis
        self.address = (url, port)
        self.buffer_size = buffer_size
        self.socket = None#socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.run = True
        self.dt = dt
        self.target_matrices = []

    def send_message(self,data):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print("call",self.address, len(data))
        self.socket.send(data)
        data = self.socket.recv(self.buffer_size)
        self.socket.close()
        return data

    def start(self):
        t = threading.Thread(target=client_thread, name="c", args=(self,))
        t.start()

PCSKELETON = {
    "Spine": {
        "parent": "LowerBack",
      #  "x_axis_index": 3,
        "index": 7
    },
    "RightHand": {
        "parent": "RightForeArm",
       # "x_axis_index": 23,
        "index": 16
    },
    "RightUpLeg": {
        "parent": "RHipJoint",
       # "x_axis_index": 31,
        "index": 1
    },
    "RightLeg": {
        "parent": "RightUpLeg",
       # "x_axis_index": 33,
        "index": 2
    },
    "RightForeArm": {
        "parent": "RightArm",
       # "x_axis_index": 29,
        "index": 15
    },
    "LeftForeArm": {
        "parent": "LeftArm",
       # "x_axis_index": 13,
        "index": 19
    },
    "RightArm": {
        "parent": "RightShoulder",
       # "x_axis_index": 19,
        "index": 14
    },
    "Hips": {
        "parent": None,
       # "x_axis_index": 1,
        "index": 0
    },
    "LeftFoot": {
        "parent": "LeftLeg",
        #"x_axis_index": 35,
        "index": 6
    },
    "RightShoulder": {
        "parent": "Spine1",
        #"x_axis_index": 17,
        "index": 13
    },
    "LeftShoulder": {
        "parent": "Spine1",
        #"x_axis_index": 9,
        "index": 17
    },
    "Neck1": {
        "parent": "Neck",
       # "x_axis_index": 7,
        "index": 11
    },
    "LeftArm": {
        "parent": "LeftShoulder",
       # "x_axis_index": 11,
        "index": 18
    },
    "LeftLeg": {
        "parent": "LeftUpLeg",
       # "x_axis_index": 27,
        "index": 5
    },
    "LeftUpLeg": {
        "parent": "LHipJoint",
        #"x_axis_index": 25,
        "index": 4
    },
    "LeftHand": {
        "parent": "LeftForeArm",
       # "x_axis_index": 15,
        "index": 20
    },
    "RightFoot": {
        "parent": "RightLeg",
        #"x_axis_index": 37,
        "index": 3
    },
    "Spine1": {
        "parent": "Spine",
        #"x_axis_index": 5,
        "index": 8
    }
}
MODEL_OFFSET = [0,0,80]

class PointCloudAnimationClient(ComponentBase):
    def __init__(self, scene_object, url, port, color=DEFAULT_COLOR, visualize=True):
        ComponentBase.__init__(self, scene_object)
        dt = 1/60
        print("dt ", dt)
        self.tcp_client = PCTCPClient(self, url, port,dt)
        self.visualize = visualize
        if visualize:
            self._sphere = SphereRenderer(10, 10, 1, color=color)
            a = [0, 0, 0]
            b = [1, 0, 0]
            self._line = DebugLineRenderer(a, b, [0,1,0])

        self.draw_bone = False
        self.rotation_matrix = np.eye(4)
        self.pose_update_queue = []
        self.current_pose = None
        self.mutex = threading.Lock()
        self.n_joints = 28
        self.root_pos = np.array([0,0,0])
        self.model_offset = np.array(MODEL_OFFSET)
        self.target_dir = np.array([1,0,0])
        self.target_projection_len = 1
        self.max_step_length = 10
        self.target_skeleton = None
        self.point_cloud_retargeting = None
        self.src_model = SKELETON_MODELS["holden"]
        self.src_joints = PCSKELETON
        self.global_pose = None



    def start(self):
        self.tcp_client.start()

    def add_pose_to_queue(self, pose_data):
        self.mutex.acquire()
        pose = []
        o =0
        for idx in range(self.n_joints):
            pos = pose_data[o:o+3]
            if len(pos) < 3:
                break
            pose.append(np.array(pos))
            o+=3
        #o= self.n_joints*3 + 21
        #o = self.n_joints * 4
        o = 99
        root_pos = pose_data[o:o+2]
        root_rot = pose_data[o+2]
        root_pos_copy = [root_pos[0],0, root_pos[1]]
        #print("root pos", root_pos_copy)
        #print()
        pose_update = pose, np.array(root_pos_copy), root_rot
        self.pose_update_queue.append(pose_update)
        self.mutex.release()

    def update(self, dt):
        self.mutex.acquire()
        if len(self.pose_update_queue) > 0:
            pose_update, root_pos, root_rot = self.pose_update_queue.pop(0)
            self.current_pose = pose_update
            self.root_pos = np.array(root_pos)
            self.rotation_matrix = euler_matrix(0,root_rot, 0)
            pos = np.array(self.root_pos)
            pos[1] = 10
            target = pos + self.target_dir * self.target_projection_len
            self._line.set_line(pos, target)
        self.mutex.release()
        if self.current_pose is not None:
            self.global_pose = []
            for position in self.current_pose:
                position = np.concatenate([position, [1]])
                # print(position)
                position = np.dot(self.rotation_matrix, position)[:3]
                self.global_pose.append(position+self.root_pos)

            if self.target_skeleton is not None:
                self.update_skeleton_matrices()


    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        if self._sphere is None:
                return

        if self.current_pose is None:
            return
        #print("root pos", self.root_pos)
        for position in self.global_pose:
            m = get_translation_matrix(position)
            m = np.dot(m, modelMatrix)
            self._sphere.draw(m, viewMatrix, projectionMatrix, lightSources)

        self._line.draw(modelMatrix, viewMatrix, projectionMatrix)

    def setColor(self, color):
        self._sphere.technique.material.diffuse_color = color
        self._sphere.technique.material.ambient_color = color * 0.1

    def getColor(self):
        return self._sphere.technique.material.diffuse_color


    def getPosition(self):
        return self.root_pos
    
    
    def handle_keyboard_input(self, key):
        print("handle", key)
        if key == b"a":
            self.rotate_dir_vector(-10)
        elif key == b"d":
            self.rotate_dir_vector(10)
        elif key == b"w":
            self.target_projection_len += 10
            self.target_projection_len = min(self.target_projection_len, self.max_step_length)
        elif key == b"s":
            self.target_projection_len -= 10
            self.target_projection_len = max(self.target_projection_len, 0)
            # if self.node_type == NODE_TYPE_IDLE:
            #    self.transition_to_next_state_controlled()
            # if not self.play and self.node_type == NODE_TYPE_END and self.target_projection_len > 0:
            #    self.play = True
    
    def rotate_dir_vector(self, angle):
        r = np.radians(angle)
        s = np.sin(r)
        c = np.cos(r)
        self.target_dir = np.array(self.target_dir, float)
        self.target_dir[0] = c * self.target_dir[0] - s * self.target_dir[2]
        self.target_dir[2] = s * self.target_dir[0] + c * self.target_dir[2]
        self.target_dir /= float(np.linalg.norm(self.target_dir))
        print("rotate", self.target_dir)

    def attach_to_visualization(self, target_skeleton, animation_node):
        self.set_target_skeleton(target_skeleton)
        animation_node.anim_controller = self

    def update_skeleton_matrices(self):
        if self.global_pose is None:
            return

        ref_frame = self.target_skeleton.reference_frame
        frame = self.point_cloud_retargeting.retarget_frame(self.global_pose, ref_frame)
        hip_index = self.src_joints["Hips"]["index"]
        frame[:3] = self.root_pos + self.model_offset
        #frame[3:7] = quaternion_from_matrix(self.rotation_matrix)
        self.target_skeleton.clear_cached_global_matrices()
        for idx, joint in enumerate(self._target_joints):
            m = self.target_skeleton.nodes[joint].get_global_matrix(frame, use_cache=True)
            self.target_matrices[idx] = m

    def set_target_skeleton(self, target_skeleton):
        self.target_skeleton = target_skeleton
        self._target_joints = self.target_skeleton.get_joint_names()
        self.target_matrices = [np.eye(4) for j in self._target_joints]
        target_to_src_map = generate_joint_map(self.src_model, target_skeleton.skeleton_model)
        self.point_cloud_retargeting = PointCloudRetargeting(self.src_joints, self.src_model,
                                                             target_skeleton, target_to_src_map)

    def get_bone_matrices(self):
        return self.target_matrices
