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
import os
import numpy as np
from anim_utils.animation_data import BVHReader, MotionVector, SkeletonBuilder   
from vis_utils.graphics import materials
from vis_utils.scene.scene_object_builder import SceneObjectBuilder, SceneObject
from vis_utils.scene.components import StaticMesh, GeometryDataComponent, TerrainComponent, LightComponent
from vis_utils.graphics.geometry.mesh import Mesh
from .utils import load_json_file, save_json_file, load_latest_json_file
from .obj_format import load_mesh_from_ob_file, load_materials_from_mtl_file, load_obj_file
from .fbx_format import load_model_from_fbx_file
try:
    from .gltf import load_model_from_gltf_file
except:
    print("Info: failed to import gltf library")
    pass




def load_collada_file(builder, file_path):
    """ https://github.com/pycollada/pycollada/blob/master/examples/daeview/renderer/GLSLRenderer.py """
    import collada
    mesh_list = list()
    col = collada.Collada(file_path, ignore=[collada.DaeUnsupportedError,
                                             collada.DaeBrokenRefError])
    if col.scene is not None:
        for geom in col.scene.objects('geometry'):
            for prim in geom.primitives():
                m = dict()
                prim_type = type(prim).__name__
                if prim_type == 'BoundTriangleSet':
                    triangles = prim
                elif prim_type == 'BoundPolylist':
                    triangles = prim.triangleset()
                else:
                    print('Unsupported mesh used:', prim_type)
                    triangles = None
                if triangles is not None:
                    triangles.generateNormals()
                    # We will need flat lists for VBO (batch) initialization
                    m["vertices"] = triangles.vertex.tolist()
                    batch_len = len(m["vertices"]) // 3
                    m["indices"] = triangles.vertex_index.flatten().tolist()
                    m["normals"] = triangles.normal.tolist()
                    m["type"] = "triangles"
                    mesh_list.append(m)

    file_name = os.path.basename(file_path)
    scene_object = SceneObject()
    scene_object.name = file_name
    static_mesh = StaticMesh(scene_object, [0, 0, 0], mesh_list)
    scene_object.add_component("static_mesh", static_mesh)

    builder._scene.addObject(scene_object)
    return scene_object


def load_mesh_from_obj_file(builder, file_path):
    file_name = os.path.basename(file_path)
    scene_object = SceneObject()
    scene_object.name = file_name
    mesh_list2 = load_obj_file(file_path)
    static_mesh = StaticMesh(scene_object, [0, 0, 0], mesh_list2)
    scene_object.add_component("static_mesh", static_mesh)
    builder._scene.addObject(scene_object)
    return scene_object




def create_static_mesh(builder, name, mesh_list):
    scene_object = SceneObject()
    scene_object.name = name
    static_mesh = StaticMesh(scene_object, [0, 0, 0], mesh_list)
    scene_object.add_component("static_mesh", static_mesh)
    return scene_object



def load_unity_constraints(builder, file_path, radius=1, material=materials.green):
    data = load_json_file(file_path)
    for idx, c in enumerate(data["frameConstraints"]):
        p = c["position"]
        p = np.array([p["x"], p["y"], p["z"]])
        q = c["orientation"]
        q = np.array([q["w"], q["x"], q["y"], q["z"]])
        o = c["offset"]
        o = np.array([o["x"], o["y"], o["z"]])

        scene_object = SceneObject()
        geometry = Mesh.build_sphere(20, 20, 2 * radius, materials.blue)
        scene_object._components["geometry"] = GeometryDataComponent(scene_object, geometry)
        scene_object.name = 'c'+str(idx)
        builder._scene.addObject(scene_object)
        scene_object.setPosition(p)
        scene_object.setQuaternion(q)

        scene_object = SceneObject()
        geometry = Mesh.build_sphere(20, 20, 2 * radius, material)
        scene_object._components["geometry"] = GeometryDataComponent(scene_object, geometry)
        scene_object.name = 'co' + str(idx)
        builder._scene.addObject(scene_object)
        scene_object.setPosition(p+o)
        scene_object.setQuaternion(q)
    print("n points", len(data["controlPoints"]))
    for idx, p in enumerate(data["controlPoints"]):
        p = [p["x"], p["y"], p["z"]]
        scene_object = SceneObject()
        geometry = Mesh.build_sphere(20, 20, 2 * radius, materials.grey)
        scene_object._components["geometry"] = GeometryDataComponent(scene_object, geometry)
        scene_object.setPosition(p)
        scene_object.name = 'p' + str(idx)
        builder._scene.addObject(scene_object)


def load_fbx_model(builder, file_path, scale=1.0, visualize=True,  load_skeleton=True):
    model_data = load_model_from_fbx_file(file_path)
    if model_data is None:
        return None
    name = file_path.split("/")[-1]
    if load_skeleton and "skeleton" in model_data:
        scene_object = builder.create_object("animated_mesh", name, model_data, scale, visualize)
        builder._scene.register_animation_controller(scene_object, "animation_controller")
    else:
        scene_object = builder.create_object("static_mesh", name, model_data, scale)
    builder._scene.addObject(scene_object)
    return scene_object



def load_gltf_file(builder, file_path, scale=1.0, visualize=True,  load_skeleton=True):
    model_data = load_model_from_gltf_file(file_path)
    if model_data is None:
        return None
    name = file_path.split("/")[-1]
    if load_skeleton and "skeleton" in model_data and model_data["skeleton"] is not None:
        scene_object = builder.create_object("animated_mesh", name, model_data, scale, visualize)
        builder._scene.register_animation_controller(scene_object, "animation_controller")
    else:
        scene_object = builder.create_object("static_mesh", name, model_data, scale)
    builder._scene.addObject(scene_object)
    return scene_object

SceneObjectBuilder.register_object("mesh_list", create_static_mesh)
SceneObjectBuilder.register_file_handler("obj", load_mesh_from_obj_file)
SceneObjectBuilder.register_file_handler("dae", load_collada_file)
SceneObjectBuilder.register_file_handler("_constraints.json", load_unity_constraints)
SceneObjectBuilder.register_file_handler("gltf", load_gltf_file)
SceneObjectBuilder.register_file_handler("glb", load_gltf_file)
