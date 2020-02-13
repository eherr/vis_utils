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
import os
import c3d
import numpy as np
from .animation_editor import AnimationEditor
from .point_cloud_animation_controller import PointCloudAnimationController
from .skeleton_animation_controller import SkeletonAnimationController
from .skeleton_visualization import SkeletonVisualization 
from .motion_state_machine import MotionStateMachineController
from ..graphics import materials
from ..io import  load_json_file
from ..scene.components import AnimatedMeshComponentLegacy, AnimatedMeshComponent, StaticMesh
from ..scene.scene_object_builder import SceneObjectBuilder, SceneObject
from ..scene.utils import get_random_color
from anim_utils.animation_data import BVHReader, MotionVector, SkeletonBuilder, parse_asf_file
from vis_utils.io.constraints import ConstraintsFormatReader

DEFAULT_POINT_CLOUD_SKELETON = collections.OrderedDict([('Head', {'parent': 'Neck', 'index': 0}),
                                                        ('Neck', {'parent': 'Spine', 'index': 1}),
                                                        ('RightShoulder', {'parent': 'Neck', 'index': 2}),
                                                        ('RightArm', {'parent': 'RightShoulder', 'index': 3}),
                                                        ('RightHand', {'parent': 'RightArm', 'index': 4}),
                                                        ('LeftShoulder', {'parent': 'Neck', 'index': 5}),
                                                        ('LeftArm', {'parent': 'LeftShoulder', 'index': 6}),
                                                        ('LeftHand', {'parent': 'LeftArm', 'index': 7}),
                                                        ('Spine', {'parent': None, 'index': 8}),
                                                        ('RightHip', {'parent': 'Spine', 'index': 9}),
                                                        ('RightKnee', {'parent': 'RightHip', 'index': 10}),
                                                        ('RightFoot', {'parent': 'RightKnee', 'index': 11}),
                                                        ('LeftHip', {'parent': 'Spine', 'index': 12}),
                                                        ('LeftKnee', {'parent': 'LeftHip', 'index': 13}),
                                                        ('LeftFoot', {'parent': 'LeftKnee', 'index': 14})
                                                        ])


def create_skeleton_object(builder, skeleton, color):
    o = SceneObject()
    skeleton_vis = SkeletonVisualization(o, color)
    skeleton_vis.set_skeleton(skeleton)
    frame = skeleton.reference_frame
    skeleton_vis.updateTransformation(frame, np.eye(4))
    skeleton_vis.draw_mode = 2
    o.add_component("skeleton_vis", skeleton_vis)
    return o



def load_skeleton_from_json(builder, file_path, scale=1.0):
    data = load_json_file(file_path)
    #skeleton = SkeletonBuilder().load_from_custom_unity_format(data)
    skeleton = SkeletonBuilder().load_from_json_data(data)
    skeleton.scale(scale)
    motion_vector = MotionVector()
    motion_vector.frames = [skeleton.get_reduced_reference_frame()]
    motion_vector.n_frames = 1

    scene_object = SceneObject()
    vis = builder.create_component("skeleton_vis", scene_object, skeleton, color=get_random_color())
    animation_controller = SkeletonAnimationController(scene_object)
    animation_controller.name = file_path.split("/")[-1]
    animation_controller.set_motion(motion_vector)
    animation_controller.frameTime = 1
    animation_controller.set_visualization(vis)
    scene_object.name = animation_controller.name
    scene_object.add_component("animation_controller", animation_controller)
    print("load mg json from", file_path)
    if scene_object is not None:
        builder._scene.addAnimationController(scene_object, "animation_controller")
    return scene_object

def attach_animation_editor(builder, scene_object):
    editor = AnimationEditor(scene_object)
    scene_object.add_component("animation_editor", editor)


def create_clip_from_reference_frame(skeleton):
    n_joints = len(skeleton.animated_joints)
    frame = np.zeros(3 + 4 * n_joints)

    offset = 3
    for node_name in skeleton.animated_joints:
        frame[offset:offset + 4] = skeleton.nodes[node_name].rotation
        offset += 4

    clip = MotionVector(skeleton)
    clip.n_frames = 1
    clip.frames = np.array([frame])
    return clip

def create_animation_controller_from_fbx(builder, name, skeleton_data):
    skeleton = SkeletonBuilder().load_from_fbx_data(skeleton_data)
    scene_object = SceneObject()

    vis = builder.create_component("skeleton_vis", scene_object, skeleton, color=(0,1,0))
    animation_controller = SkeletonAnimationController(scene_object)
    animation_controller.name = name
    animation_controller.currentFrameNumber = 0
    animation_controller.frameTime = 0.011333
    clip = create_clip_from_reference_frame(skeleton)
    animation_controller.set_motion(clip)
    skeleton.reference_frame = clip.frames[0]
    animation_controller.set_visualization(vis, 2)

    scene_object.name = animation_controller.name
    scene_object.add_component("animation_controller", animation_controller)
    return scene_object

def attach_animated_mesh_component(builder, scene_object, model_data, animation_controller, scale=10):
    mesh_list = model_data["mesh_list"]
    skeleton_data = model_data["skeleton"]
    mesh = AnimatedMeshComponent(scene_object, mesh_list, skeleton_data, animation_controller, scale)
    scene_object.add_component("animated_mesh", mesh)
    return mesh

def create_animated_mesh(builder, name, model_data, scale=1, visualize=True):
    scene_object = SceneObject()
    scene_object.name = name

    skeleton_data = model_data["skeleton"]
    skeleton = SkeletonBuilder().load_from_fbx_data(skeleton_data)
    skeleton.scale(scale)

    vis = None
    if visualize:
        vis = builder.create_component("skeleton_vis", scene_object, skeleton, color=(0,1,0), scale=0.1)
        #vis.box_scale = 0.1
    
    animation_controller = SkeletonAnimationController(scene_object)
    clip = create_clip_from_reference_frame(skeleton)
    clip.scale_root(scale)
    animation_controller.name = scene_object.name
    animation_controller.set_motion(clip)
    animation_controller.set_visualization(vis, 1)
    animation_controller.frameTime = skeleton.frame_time
    scene_object.name = animation_controller.name
    scene_object.add_component("animation_controller", animation_controller)

    if visualize:
        if len(model_data["mesh_list"]) > 0 and len(model_data["mesh_list"][0]["vertices"]) > 0:
            builder.create_component("animated_mesh", scene_object, model_data, "animation_controller", scale)
    return scene_object

def attach_static_mesh_component(builder, scene_object, model_data, scale=1):
    mesh_list = model_data["mesh_list"]
    position = [0,0,0]
    static_mesh = StaticMesh(scene_object, position, mesh_list)
    scene_object.add_component("static_mesh", static_mesh)
    return static_mesh

def create_static_mesh(builder, name, model_data, scale=1):
    scene_object = SceneObject()
    scene_object.name = name
    if len(model_data["mesh_list"]) > 0 and len(model_data["mesh_list"][0]["vertices"]) > 0:
        builder.create_component("static_mesh", scene_object, model_data, scale)
    return scene_object


def load_c3d_file(filepath):
    data = dict()
    with open(filepath, "rb") as in_file:
        reader = c3d.Reader(in_file)
        data["labels"] = reader.point_labels
        data["motion_data"] = []
        for frame in reader.read_frames():
            idx, points = frame[0], frame[1]
            data["motion_data"].append(points)
    return data


def load_point_cloud_from_c3d(builder, filename, scale=0.1):
    name = filename.split("/")[-1]
    scene_object = SceneObject()
    scene_object.name = name
    data = load_c3d_file(filename)
    animation_controller = PointCloudAnimationController(scene_object, color=get_random_color())
    animation_controller.set_data(data)
    scene_object.add_component("animation_controller", animation_controller)
    controller = scene_object._components["animation_controller"]
    m = np.array([[1, 0, 0],
                  [0, 0, 1],
                  [0, 1, 0]], dtype="f")
    m *= scale
    controller.apply_transform(m)
    builder._scene.addAnimationController(scene_object, "animation_controller")

def load_point_cloud_from_file(builder, filename):
    data = load_json_file(filename)
    for p in data["points"]:
        builder.create_object("sphere", "p", p, material=materials.red)

def load_point_cloud_animation(builder, file_path, visualize=True):
    data = load_json_file(file_path)
    if data is None:
        print("Could not read", file_path)
        return
    scene_object = SceneObject()
    animation_controller = PointCloudAnimationController(scene_object, visualize=visualize)
    animation_controller.set_data(data)
    scene_object.add_component("animation_controller", animation_controller)
    builder._scene.addAnimationController(scene_object, "animation_controller")
    return scene_object

def load_point_cloud_animation_from_mat_file(builder, mat_file_path):
    import scipy.io
    data = scipy.io.loadmat(mat_file_path)
    # rename the key
    data['motion_data'] = data.pop('md')
    # coordinate transform and rescale data
    trans_mat = np.array([[0.025, 0.0, 0.0], [0.0, 0.0, 0.025], [0.0, 0.025, 0.0]])
    data['motion_data'] = np.dot(data['motion_data'], trans_mat)
    data['has_skeleton'] = True
    data['skeleton'] = DEFAULT_POINT_CLOUD_SKELETON
    if data is None:
        print("Could not read", mat_file_path)
        return
    scene_object = SceneObject()
    animation_controller = PointCloudAnimationController(scene_object)
    animation_controller.set_data(data)
    scene_object.add_component("animation_controller", animation_controller)
    builder._scene.addAnimationController(scene_object, "animation_controller")
    return scene_object

def create_skeleton_animation_controller(builder, name, skeleton, motion_vector, frame_time, draw_mode=2, visualize=True, color=None, semantic_annotation=None):
    scene_object = SceneObject()
    vis = None
    if visualize:
        if color is None:
            color = get_random_color()
        vis = builder.create_component("skeleton_vis", scene_object, skeleton, color=color)

    animation_controller = SkeletonAnimationController(scene_object)
    animation_controller.name = name
    animation_controller.set_motion(motion_vector)
    animation_controller.set_visualization(vis, draw_mode)
    animation_controller.frameTime = frame_time
    if semantic_annotation:
        color_map = dict()
        for k in semantic_annotation:
            color_map[k] = get_random_color()
        animation_controller.set_color_annotation(semantic_annotation, color_map)


    scene_object.name = animation_controller.name
    scene_object.add_component("animation_controller", animation_controller)

    builder._scene.addAnimationController(scene_object, "animation_controller")
    return scene_object


def load_bvh_file(builder, path, scale=1.0, draw_mode=2, offset=None, reference_frame=None, skeleton_model=None, use_clip=False, color=None,visualize=True):
    bvh_reader = BVHReader(path)
    bvh_reader.scale(scale)
    animated_joints = [key for key in list(bvh_reader.node_names.keys()) if not key.endswith("EndSite")]
    skeleton = SkeletonBuilder().load_from_bvh(bvh_reader, animated_joints, reference_frame=reference_frame, skeleton_model=skeleton_model)

    motion_vector = MotionVector()
    motion_vector.from_bvh_reader(bvh_reader, False)
    motion_vector.skeleton = skeleton
    if offset is not None:
        motion_vector.translate_root(offset)
    #motion_vector.scale_root(scale)
    name = path.split("/")[-1]
    o = builder.create_object("animation_controller", name, skeleton, motion_vector, bvh_reader.frame_time, draw_mode, visualize, color)
    #builder.create_component("animation_editor",o)
    return o

def load_asf_file(builder, filename):
    scene_object = SceneObject()
    scene_object.scene = builder._scene
    asf_data = parse_asf_file(filename)
    skeleton = SkeletonBuilder().load_from_asf_data(asf_data)
    
    color = get_random_color()
    builder.create_component("skeleton_vis", scene_object, skeleton, color)

    motion_vector = MotionVector()
    motion_vector.frames = [skeleton.get_reduced_reference_frame()]
    motion_vector.n_frames = 1

    scene_object = SceneObject()
    vis = builder.create_component("skeleton_vis", scene_object, skeleton, color=get_random_color())
    animation_controller = SkeletonAnimationController(scene_object)
    animation_controller.name = filename.split("/")[-1]
    animation_controller.set_motion(motion_vector)
    animation_controller.frameTime = 1
    animation_controller.set_visualization(vis)
    scene_object.name = animation_controller.name
    scene_object.add_component("animation_controller", animation_controller)
    builder._scene.addAnimationController(scene_object, "animation_controller")
    return scene_object

def load_motion_from_bvh(filename):
    bvh_reader = BVHReader(filename)
    motion_vector = MotionVector()
    motion_vector.from_bvh_reader(bvh_reader, False)
    animated_joints = list(bvh_reader.get_animated_joints())
    motion_vector.skeleton = SkeletonBuilder().load_from_bvh(bvh_reader, animated_joints=animated_joints)
    return motion_vector

def attach_skeleton_visualization(builder, scene_object, skeleton, color, scale=1.0):
    skeleton_vis = SkeletonVisualization(scene_object, color)
    skeleton_vis.set_skeleton(skeleton, True, scale)
    frame = skeleton_vis.skeleton.reference_frame
    skeleton_vis.updateTransformation(frame, np.eye(4))
    skeleton_vis.draw_mode = 2
    #animation_src.vis = skeleton_vis
    scene_object.add_component("skeleton_vis", skeleton_vis)
    print("attached skeleton vis", scale)
    return skeleton_vis


def attach_motion_state_machine(builder, scene_object, skeleton, mv):
    ms = MotionStateMachineController(scene_object, skeleton, mv)
    scene_object.add_component("motion_state_machine", ms)
    return ms

def create_motion_state_machine_from_bvh(builder, filepath):
    scene_object = SceneObject()
    scene_object.scene = builder._scene
    mv = load_motion_from_bvh(filepath)
    print("call motion_state_machine")
    animation_src = builder.create_component("motion_state_machine", scene_object, mv.skeleton, mv)
    if builder._scene.visualize:
        builder.create_component("skeleton_vis", scene_object, animation_src, color=get_random_color())
        animation_src.update_scene_object.connect(builder._scene.slotUpdateSceneObjectRelay)
    builder._scene.addObject(scene_object)
    return scene_object


def load_custom_unity_format_file(builder, filename, draw_mode=2):
    data = load_json_file(filename)
    if data is not None:
        frame_time = data["frameTime"]
        motion_vector = MotionVector()
        motion_vector.from_custom_unity_format(data)
        skeleton = SkeletonBuilder().load_from_json_data(data)
        o = builder.create_object("animation_controller", filename.split("/")[-1], skeleton, motion_vector, motion_vector.frame_time, draw_mode, visualize, color)
        return o

def load_point_cloud_animation_collection(builder, file_path):
    collection_data = load_json_file(file_path)
    if collection_data is None:
        print("Could not read", file_path)
        return
    scene_object = None
    for key in list(collection_data.keys()):
        scene_object = SceneObject()
        scene_object.name = key
        data = dict()
        data["motion_data"] = collection_data[key]
        animation_controller = PointCloudAnimationController(scene_object)
        animation_controller.set_data(data)
        scene_object.add_component("animation_controller", animation_controller)
        builder._scene.addAnimationController(scene_object, "animation_controller")
        scene_object.hide()
    return scene_object

def load_coordinate_error_format(builder, filename):
    ConstraintsFormatReader(builder._scene).loadCoordinateErrorFormat(filename)



SceneObjectBuilder.register_object("skeleton", create_skeleton_object)
SceneObjectBuilder.register_object("fbx_skeleton_controller", create_animation_controller_from_fbx)
SceneObjectBuilder.register_object("animated_mesh", create_animated_mesh)
SceneObjectBuilder.register_object("static_mesh", create_static_mesh)
SceneObjectBuilder.register_object("animation_controller", create_skeleton_animation_controller)
SceneObjectBuilder.register_component("animation_editor", attach_animation_editor)
SceneObjectBuilder.register_component("animated_mesh", attach_animated_mesh_component)
SceneObjectBuilder.register_component("static_mesh", attach_static_mesh_component)
SceneObjectBuilder.register_component("motion_state_machine", attach_motion_state_machine)
SceneObjectBuilder.register_component("skeleton_vis", attach_skeleton_visualization)
SceneObjectBuilder.register_file_handler("bvh", load_bvh_file)
SceneObjectBuilder.register_file_handler("skeleton.json", load_skeleton_from_json)
SceneObjectBuilder.register_file_handler("c3d", load_point_cloud_from_c3d)
SceneObjectBuilder.register_file_handler("bvh_loop", create_motion_state_machine_from_bvh)
SceneObjectBuilder.register_file_handler("pc", load_point_cloud_from_file)
SceneObjectBuilder.register_file_handler("panim", load_point_cloud_animation)
SceneObjectBuilder.register_file_handler("mat", load_point_cloud_animation_from_mat_file)
SceneObjectBuilder.register_file_handler("_m.json", load_custom_unity_format_file)
SceneObjectBuilder.register_file_handler("panim_collection", load_point_cloud_animation_collection)
SceneObjectBuilder.register_file_handler("cee", load_coordinate_error_format)
SceneObjectBuilder.register_file_handler("asf",load_asf_file)




