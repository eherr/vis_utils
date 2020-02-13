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
import FbxCommon
from fbx import *
import numpy as np
import collections
from transformations import quaternion_matrix, euler_from_quaternion, quaternion_from_euler
from anim_utils.animation_data.skeleton_node import SKELETON_NODE_TYPE_ROOT,SKELETON_NODE_TYPE_JOINT, SKELETON_NODE_TYPE_END_SITE
has_image_library = True
try:
    from PIL import Image
except ImportError as e:
    has_image_library = False
    print("Warning: could not import PIL library")
    pass


def load_fbx_file(file_path):
    importer = FBXSkinnedMeshImporter(file_path)
    importer.load()
    importer.destroy()
    return importer.mesh_list, importer.skeleton, importer.animations


class FBXSkinnedMeshImporter(object):
    def __init__(self, file_path, scale=1.0):
        self.skeleton = None
        self.skinning_data = dict()
        self.animations = dict()
        self.mesh_list = []
        self.scale = scale

        (self.sdk_manager, self.fbx_scene) = FbxCommon.InitializeSdkObjects()
        FbxCommon.LoadScene(self.sdk_manager, self.fbx_scene, file_path)
        FbxAxisSystem.OpenGL.ConvertScene(self.fbx_scene)

    def destroy(self):
        self.sdk_manager.Destroy()

    def load(self):
        self.skeleton = None
        self.skinning_data = dict()
        self.animations = dict()
        self.mesh_list = []
        self.parseFBXNodeHierarchy(self.fbx_scene.GetRootNode(), 0, self.mesh_list)
        self.animations = self.read_animations()


    def parseFBXNodeHierarchy(self, fbx_node, depth, mesh_list):

        if self.skeleton is None and fbx_node.GetChildCount() > 0 and depth > 0:
            self.skeleton = self.create_skeleton(fbx_node)

        n_attributes = fbx_node.GetNodeAttributeCount()
        for idx in range(n_attributes):
            attribute = fbx_node.GetNodeAttributeByIndex(idx)
            if attribute.GetAttributeType() == FbxNodeAttribute.eMesh:
                self.create_mesh_data(fbx_node, attribute, mesh_list)

        for idx in range(fbx_node.GetChildCount()):
            self.parseFBXNodeHierarchy(fbx_node.GetChild(idx), depth + 1, mesh_list)

    def create_mesh_data(self, fbx_node, attribute, mesh_list):
        mesh_name = fbx_node.GetName()
        mesh = self.read_mesh(mesh_name, attribute)
        if has_image_library:
            material = extractMaterialFromNode(fbx_node)
        else:
            material = None
        if material is not None:
            mesh["material"] = material
            mesh["has_material"] = True

        if mesh is not None:
            mesh_list.append(mesh)

    def read_mesh(self, mesh_name, mesh, shift_index=False):
        mesh_data = {"vertices": [], "normals": [], "faces":[], "texture_coordinates": [], "material":"", "has_material": False, "shift_index": shift_index,
                     "skinning_data": {}}
        control_points = mesh.GetControlPoints()
        n_vertices = mesh.GetControlPointsCount()
        n_layers = mesh.GetLayerCount()
        n_faces = mesh.GetPolygonCount()
        if n_vertices <= 0:
            return

        n_poly_vertices = mesh.GetPolygonSize(0)

        if n_poly_vertices == 3:
            mesh_data["type"] = "triangles"
        elif n_poly_vertices == 4:
            mesh_data["type"] = "quads"
        else:
            return "mesh type not supported"

        uv_layer_idx = 0
        vi = 0
        ni = 0
        ti = 0
        uv_layer = mesh.GetElementUV(uv_layer_idx)
        for layer_idx in range(n_layers):
            for f_idx in range(n_faces):
                face = []
                for v_idx in range(n_poly_vertices):

                    control_point_idx = mesh.GetPolygonVertex(f_idx, v_idx)
                    vertex = control_points[control_point_idx]
                    mesh_data["vertices"].append([vertex[0], vertex[1], vertex[2]])

                    normal = get_normal(mesh, layer_idx, vi, f_idx, v_idx)
                    mesh_data["normals"].append([-normal[0], -normal[1], -normal[2]])

                    texture_coordinate = get_texture_coordinate(mesh, uv_layer, vi, f_idx, v_idx)
                    mesh_data["texture_coordinates"].append([texture_coordinate[0], texture_coordinate[1]])
                    face.append([vi, ni, ti])

                    vi += 1
                    ni += 1
                    ti += 1
                mesh_data["faces"].append(face)

        if self.skeleton is not None and mesh.GetDeformerCount() > 0:
            mesh_data["skinning_data"] = self.extract_skinning_data_from_mesh_node(mesh)
        else:
            print("Mesh has no deformers")
        return mesh_data

    def create_skeleton(self, node, set_pose=False):
        current_time = FbxTime()
        current_time.SetFrame(0, FbxTime.eFrames24)
        def add_child_node_recursively(skeleton, fbx_node, parentTransform, set_pose=False):

            node_name = fbx_node.GetName()
            node_idx = len(skeleton["animated_joints"])

            localTransform = fbx_node.EvaluateLocalTransform(current_time)
            transform = parentTransform * localTransform
            lT = localTransform.GetT()

            if set_pose:
                parentRM = FbxAMatrix()
                parentRM.SetIdentity()
                parentRM.SetQ(parentTransform.GetQ())

                localDirM = FbxAMatrix()
                localDirM.SetIdentity()
                localDirM.SetT(lT)

                globalDirM = parentRM * localDirM
                gT = globalDirM.GetT()
                offset = np.array([gT[0], gT[1], gT[2]])
                rotation = [1, 0, 0, 0]
            else:
                o = fbx_node.LclTranslation.Get()
                offset = self.scale*np.array([o[0], o[1], o[2]])
                #rotation = [1, 0, 0, 0]
                #e = fbx_node.LclRotation.Get()
                #rotation = quaternion_from_euler(*e, axes='szyx')
                q = localTransform.GetQ()
                rotation = np.array([q[3],q[0], q[1], q[2]])

                #rotation = [1, 0, 0, 0]
                #offset = np.array([lT[0], lT[1], lT[2]])

            node = {"name": node_name,
                        "children": [],
                        "channels": ["Xrotation", "Yrotation", "Zrotation"],
                        "offset": offset,
                        "rotation": rotation,
                        "fixed": False,
                        "index": node_idx,
                        "inv_bind_pose": np.eye(4),
                        "quaternion_frame_index": node_idx,
                        "node_type": SKELETON_NODE_TYPE_JOINT}
            skeleton["animated_joints"].append(node_name)

            n_children = fbx_node.GetChildCount()
            for idx in range(n_children):
                c_node = add_child_node_recursively(skeleton, fbx_node.GetChild(idx), transform, set_pose)
                node["children"].append(c_node["name"])

            # add endsite
            if n_children == 0:
                end_site_name = node_name+"_EndSite"
                end_site = {"name": end_site_name,"offset":[0,0,0], "rotation": [1,0,0,0], "index": -1,
                            "quaternion_frame_index": -1, "node_type": SKELETON_NODE_TYPE_END_SITE,
                            "channels": [], "children": [], "fixed": True,

                            }
                skeleton["nodes"][end_site_name] = end_site
                node["children"].append(end_site_name)

            skeleton["nodes"][node_name] = node
            return node

        transform = node.EvaluateLocalTransform(current_time)
        if set_pose:
            o = transform.GetT()
            offset = np.array([o[0], o[1], o[2]])
            q = transform.GetQ()
            rotation = [q[3], q[0], q[1], q[2]]

        else:
            o = node.LclTranslation.Get()
            offset = self.scale*np.array([o[0], o[1], o[2]])
            e = node.LclRotation.Get()
            rotation = quaternion_from_euler(*e, axes='sxyz')
            #rotation = [1, 0, 0, 0]


        root_name = node.GetName()
        skeleton = dict()
        skeleton["animated_joints"] = [root_name]
        skeleton["node_names"] = dict()
        skeleton["nodes"] = collections.OrderedDict()
        skeleton["frame_time"] = 0.013889
        root_node = {"name": root_name,
                    "children": [],
                    "channels": ["Xposition", "Yposition", "Zposition",
                                 "Xrotation", "Yrotation", "Zrotation"],
                    "offset": offset,
                    "rotation": rotation,
                    "fixed": False,
                    "index": 0,
                    "quaternion_frame_index": 0,
                    "inv_bind_pose": np.eye(4),
                    "node_type": SKELETON_NODE_TYPE_ROOT}

        skeleton["nodes"][root_name] = root_node
        for idx in range(node.GetChildCount()):
            c_node = add_child_node_recursively(skeleton, node.GetChild(idx), transform, set_pose)
            root_node["children"].append(c_node["name"])

        skeleton["root"] = root_name

        return skeleton

    def extract_skinning_data_from_mesh_node(self, pMesh):
        print("Try to extract skinning info")
        pNode = pMesh.GetNode()
        lT = pNode.GetGeometricTranslation(0)
        lR = pNode.GetGeometricRotation(0)
        lS = pNode.GetGeometricScaling(0)

        geometryTransform = FbxAMatrix(lT, lR, lS)

        skin = pMesh.GetDeformer(0, FbxDeformer.eSkin)
        if not skin:
            return

        skinning_data = dict()
        for idx in range(skin.GetClusterCount()):
            cluster = skin.GetCluster(idx)
            node = cluster.GetLink()

            node_name = node.GetName()
            if node_name not in list(self.skeleton["nodes"].keys()):
                continue

            self.skeleton["nodes"][node_name]["inv_bind_pose"] = getInvBindPose(cluster, geometryTransform)
            weights = cluster.GetControlPointWeights()
            skinning_data[node_name] = []
            for local_p_idx in range(cluster.GetControlPointIndicesCount()):
                global_p_idx = cluster.GetControlPointIndices()[local_p_idx]
                skinning_data[node_name].append((global_p_idx, weights[local_p_idx])) # joint_name: vertex_idx, weight

        return skinning_data

    def read_animations(self):
        """src: http://gamedev.stackexchange.com/questions/59419/c-fbx-animation-importer-using-the-fbx-sdk
        """
        anims = dict()
        count = self.fbx_scene.GetSrcObjectCount(FbxCriteria.ObjectType(FbxAnimStack.ClassId))
        for idx in range(count):
            anim = dict()
            anim_stack = self.fbx_scene.GetSrcObject(FbxCriteria.ObjectType(FbxAnimStack.ClassId), idx)
            self.fbx_scene.SetCurrentAnimationStack(anim_stack)
            anim_name = anim_stack.GetName()
            anim_layer = anim_stack.GetMember(FbxCriteria.ObjectType(FbxAnimLayer.ClassId), 0)
            mLocalTimeSpan = anim_stack.GetLocalTimeSpan()
            start = mLocalTimeSpan.GetStart()
            end = mLocalTimeSpan.GetStop()
            anim["n_frames"] = end.GetFrameCount(FbxTime.eFrames24) - start.GetFrameCount(FbxTime.eFrames24) + 1
            anim["duration"] = end.GetSecondCount() - start.GetSecondCount()
            anim["frame_time"] = 0.013889
            anim["curves"] = collections.OrderedDict()
            print("found animation", anim_name, anim["n_frames"], anim["duration"])
            temp_node = self.fbx_scene.GetRootNode()

            nodes = []
            while temp_node is not None:
                name = temp_node.GetName()

                if has_curve(anim_layer, temp_node):
                    anim["curves"][name] = []
                    current_t = FbxTime()
                    for frame_idx in range(start.GetFrameCount(FbxTime.eFrames24), end.GetFrameCount(FbxTime.eFrames24)):
                        current_t.SetFrame(frame_idx, FbxTime.eFrames24)
                        local_transform = temp_node.EvaluateLocalTransform(current_t)
                        q = local_transform.GetQ()

                        t = local_transform.GetT()
                        transform = {"local_rotation": [q[3], q[0], q[1], q[2]],
                                     "local_translation": [t[0], t[1], t[2]]}
                        anim["curves"][name].append(transform)

                for i in range(temp_node.GetChildCount()):
                    nodes.append(temp_node.GetChild(i))
                if len(nodes) > 0:
                    temp_node = nodes.pop(0)
                else:
                    temp_node = None
            anims[anim_name] = anim
        return anims


def has_curve(anim_layer, node):
    translation = node.LclTranslation.GetCurve(anim_layer, "X")
    rotation = node.LclRotation.GetCurve(anim_layer, "X")
    return rotation is not None or translation is not None


def FBXMatrixToNumpy(m):
    q = m.GetQ()
    t = m.GetT()
    m = quaternion_matrix([q[0], q[1], q[2], q[3]])
    m[:3,3] = t[0], t[1],t[2]
    return m


def create_material(texture_path):
    img_data = None
    material = None
    print("load from texture path", texture_path)
    if os.path.isfile(texture_path):
        img_data = Image.open(texture_path, "r")
    if img_data is not None:
        material = dict()
        material["Kd"] = img_data
    return material


def extractMaterialFromNode(pNode):
    textures = extract_texture_names_from_node(pNode)
    material = None
    if len(textures) > 0:
        material = create_material(textures[0])
    return material


def getInvBindPose(cluster, geometryTransform):
    transformMatrix = FbxAMatrix()
    transformLinkMatrix = FbxAMatrix()
    cluster.GetTransformMatrix(transformMatrix)  # The transformation of the mesh at binding time
    cluster.GetTransformLinkMatrix(
        transformLinkMatrix)  # The transformation of the cluster(joint) at binding time from joint space to world space
    inverseBindPose = transformLinkMatrix.Inverse() * transformMatrix * geometryTransform

    return FBXMatrixToNumpy(inverseBindPose)


def get_normal(mesh, layer_idx, control_idx, iPolygon, iPolygonVertex):
    normals = mesh.GetLayer(layer_idx).GetNormals()
    if normals:
        if normals.GetMappingMode() == FbxLayerElement.eByControlPoint:
            if normals.GetReferenceMode() == FbxLayerElement.eDirect:
                return normals.GetDirectArray().GetAt(control_idx)
            elif normals.GetMappingMode() == FbxLayerElement.eIndexToDirect:
                index = normals.GetIndexArray().GetAt(control_idx)
                return normals.GetDirectArray().GetAt(index)
        elif normals.GetMappingMode() == FbxLayerElement.eByPolygonVertex:
            if normals.GetReferenceMode() == FbxLayerElement.eDirect:
                return normals.GetDirectArray().GetAt(control_idx)
            elif normals.GetMappingMode() == FbxLayerElement.eIndexToDirect:
                index = normals.GetIndexArray().GetAt(control_idx)
                return normals.GetDirectArray().GetAt(index)
    else:
        print("no normals")


def get_texture_coordinate(mesh, uv_layer, control_idx, iPolygon, iPolygonVertex):
    if uv_layer.GetMappingMode() == FbxLayerElement.eByControlPoint:
        if uv_layer.GetReferenceMode() == FbxLayerElement.eDirect:
            return uv_layer.GetDirectArray().GetAt(control_idx)
        elif uv_layer.GetMappingMode() == FbxLayerElement.eIndexToDirect:
            index = uv_layer.GetIndexArray().GetAt(control_idx)
            return uv_layer.GetDirectArray().GetAt(index)
        return
    elif uv_layer.GetMappingMode() == FbxLayerElement.eByPolygonVertex:
        if uv_layer.GetReferenceMode() == FbxLayerElement.eDirect:
            return uv_layer.GetDirectArray().GetAt(control_idx)
        elif uv_layer.GetMappingMode() == FbxLayerElement.eIndexToDirect:
            index = uv_layer.GetIndexArray().GetAt(control_idx)
            return uv_layer.GetDirectArray().GetAt(index)
        return


def extract_texture_names_from_node(node):
    """source: http://stackoverflow.com/questions/19634369/read-texture-filename-from-fbx-with-fbx-sdk-c"""
    file_names = []
    materialCount = node.GetSrcObjectCount(FbxCriteria.ObjectType(FbxSurfaceMaterial.ClassId))
    for i in range(materialCount):
        material = node.GetSrcObject(FbxCriteria.ObjectType(FbxSurfaceMaterial.ClassId), i)
        if material is not None:
            prop = material.FindProperty(FbxSurfaceMaterial.sDiffuse)
            textureCount = prop.GetSrcObjectCount(FbxCriteria.ObjectType(FbxTexture.ClassId))
            for j in range(textureCount):
                texture = prop.GetSrcObject(FbxCriteria.ObjectType(FbxTexture.ClassId), j)
                file_names.append(texture.GetFileName())
    return file_names

