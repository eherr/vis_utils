import os
import struct
import numpy as np
import pygltflib as gltf

from transformations import quaternion_from_matrix
from PIL import Image
import io

BYTE_LENGTHS = dict()
BYTE_LENGTHS[gltf.UNSIGNED_SHORT] = 2
BYTE_LENGTHS[gltf.FLOAT] = 4


FORMAT_MAP = dict()
FORMAT_MAP[gltf.UNSIGNED_SHORT] = "H"
FORMAT_MAP[gltf.FLOAT] = 'f'


TYPE_N_COMPONENT_MAP = dict()
TYPE_N_COMPONENT_MAP["SCALAR"] = 1
TYPE_N_COMPONENT_MAP["VEC2"] = 2
TYPE_N_COMPONENT_MAP["VEC3"] = 3
TYPE_N_COMPONENT_MAP["VEC4"] = 4
TYPE_N_COMPONENT_MAP["MAT4"] = 16


SCALE = 1


def extract_values(data, a_idx):
    values = []
    buffer = data._glb_data
    accessor = data.accessors[a_idx]
    if accessor.componentType not in FORMAT_MAP or accessor.type not in TYPE_N_COMPONENT_MAP:
        print("unhandled component type", accessor.type, accessor.componentType)
    else:
        n_components = TYPE_N_COMPONENT_MAP[accessor.type]
        b_view = data.bufferViews[accessor.bufferView]
        #data.buffers[b_view.buffer]
        o = accessor.byteOffset
        o += b_view.byteOffset
        l = b_view.byteLength
        stride = b_view.byteStride
        if stride is None:
            stride = n_components * BYTE_LENGTHS[accessor.componentType]
        buffer_slice = buffer[o:o+l]
        format_str = "<"+ FORMAT_MAP[accessor.componentType]*n_components
        print(format_str, stride, b_view.byteStride)
        for idx in range(accessor.count):
            _idx = idx*stride
            v = struct.unpack(format_str, buffer_slice[_idx:_idx+stride])
            if n_components == 1:
                v = v[0]
            else:
                v = list(v)
            values.append(v)
    return values

def extract_image(data, image):
    """" https://stackoverflow.com/questions/32908639/open-pil-image-from-byte-file"""
    if hasattr(image, "bufferView") and image.bufferView is not None and image.bufferView >0 and image.bufferView < len(data.bufferViews):
        buffer = data._glb_data
        b_view = image.bufferView
        b_offset = data.bufferViews[b_view].byteOffset
        b_length = data.bufferViews[b_view].byteLength
        print(image, data.bufferViews[b_view])
        img = Image.open(io.BytesIO(buffer[b_offset:b_offset+b_length]))
        return img
    elif hasattr(image, "uri") and image.uri is not None:
        print("dasdsa", data._path,str(data._path)+os.sep+image.uri)
        input_file = str(data._path)+os.sep+image.uri
        img = Image.open(input_file)
        return img

def extract_inv_bind_matrices(data, a_idx):
    matrices = []
    buffer = data._glb_data
    accessor = data.accessors[a_idx]
    if accessor.componentType ==gltf.FLOAT:
        b_view_idx = accessor.bufferView
        b_view = data.bufferViews[b_view_idx]
        o = accessor.byteOffset
        o += b_view.byteOffset
        l = b_view.byteLength
        stride = b_view.byteStride#3*4
        if stride is None:
            stride = 16 * BYTE_LENGTHS[accessor.componentType]
        #stride = 16*4
        buffer_slice = buffer[o:o+l]
        format_str = "<"+ FORMAT_MAP[accessor.componentType] * 16
        for idx in range(accessor.count):
            _idx = idx*stride
            m = struct.unpack(format_str, buffer_slice[_idx:_idx+stride])
            m = np.array(m)#.reshape((4,4)).T
            matrix = [[m[0], m[4], m[8], m[12] ],
                     [m[1], m[5], m[9], m[13] ],
                     [m[2], m[6], m[10], m[14] ],
                     [m[3], m[7], m[11], m[15] ]]
            #m[:3,3] *= SCALE
            matrix = np.array(matrix)
            matrices.append(matrix)
    return matrices

def extract_mesh(data, p):
    mesh = dict()
    start_idx = p.indices
    if p.mode  == gltf.TRIANGLES:
        mesh["type"] = "triangles"
    else:
        print("unsupported primitive type", p.mode)
        return mesh
    if start_idx is not None and data.accessors[start_idx].bufferView is not None:
        mesh["indices"] = extract_values(data, start_idx)
    if hasattr(p.attributes, gltf.POSITION) and p.attributes.POSITION is not None:
        a_idx = p.attributes.POSITION
        if a_idx < len(data.accessors):
            v = extract_values(data, a_idx)
            v = np.array(v)* SCALE
            mesh["vertices"] = v
            print("loaded", len(mesh["vertices"]), "vertices")
            #print(mesh["vertices"][:5])
    if hasattr(p.attributes, gltf.NORMAL) and p.attributes.NORMAL is not None:
        a_idx = p.attributes.NORMAL
        if a_idx < len(data.accessors):
            mesh["normals"] = extract_values(data, a_idx)                       
            print("loaded", len(mesh["normals"]), "normals")
            #print(mesh["normals"][:5])
    if hasattr(p.attributes, gltf.JOINTS_0) and p.attributes.JOINTS_0 is not None:
        a_idx = p.attributes.JOINTS_0
        if a_idx < len(data.accessors):
            mesh["joint_indices"] = extract_values(data, a_idx)                       
            print("loaded", len(mesh["joint_indices"]), "joint indices")
    if hasattr(p.attributes, gltf.WEIGHTS_0) and p.attributes.WEIGHTS_0 is not None:
        a_idx = p.attributes.WEIGHTS_0
        if a_idx < len(data.accessors):
            mesh["weights"] = extract_values(data, a_idx)                 
            print("loaded", len(mesh["weights"]), "joint weights")
    if hasattr(p.attributes, gltf.TEXCOORD_0) and p.attributes.TEXCOORD_0 is not None:
        a_idx = p.attributes.TEXCOORD_0
        if a_idx < len(data.accessors):
            uvs = extract_values(data, a_idx)
            for i in range(len(uvs)):
                uvs[i][0] = uvs[i][0]
                uvs[i][1] = -uvs[i][1]

            mesh["texture_coordinates"] = uvs
            print("loaded", len(mesh["texture_coordinates"]), "joint uv")
    if hasattr(p.attributes, gltf.TEXCOORD_1) and p.attributes.TEXCOORD_1 is not None:
        a_idx = p.attributes.TEXCOORD_1
        if a_idx < len(data.accessors):
            mesh["texture_coordinates"] = extract_values(data, a_idx)                 
            print("loaded", len(mesh["texture_coordinates2"]), "joint uv2")
    return mesh

def extract_material(data, m_idx):
    if 0 > m_idx or m_idx > len(data.materials):
        return None
    mat_dict = dict()
    pbr_mat = data.materials[m_idx].pbrMetallicRoughness
    if pbr_mat is not None and pbr_mat.baseColorTexture is not None:
        tex_idx = pbr_mat.baseColorTexture.index
        image_idx = data.textures[tex_idx].source
        tex_coord  = 0
        if hasattr(data.textures[tex_idx], "textCoord"):
            text_coord = data.textures[tex_idx].textCoord
        mat_dict["text_coord"] = tex_coord
        mat_dict["albedo_texture"] = extract_image(data, data.images[image_idx])
        print("albedo", mat_dict["albedo_texture"])
    return mat_dict

def create_end_site(name):
    node = dict()
    node["name"] = name
    node["children"] = []
    node["channels"] = []
    node["offset"] = [0,0,0]
    node["rotation"] = [1,0,0,0]
    node["fixed"] = True
    node["node_type"] = 2
    node["index"] = -1
    return node

def transform_quat(r):
    q = [r[3], r[0], r[1], r[2]]
    q = np.array(q)
    q /= np.linalg.norm(q)
    return q

def transform_pos(t):
    p = [t[0], t[1], t[2]]
    return np.array(p)* SCALE

def get_local_bind_pose(joint_name, joints, parents):
    if "inv_bind_pose" not in joints[joint_name]:
        return np.eye(4)
    matrix = np.linalg.inv(joints[joint_name]["inv_bind_pose"])
    if parents[joint_name] is None:
        return matrix
    else:
        parent_matrix = joints[parents[joint_name]]["inv_bind_pose"]
        matrix = np.dot(parent_matrix, matrix)
        return matrix

def set_pose_from_bind_pose(joints, parents):
    for j in joints:
        joints[j]["local_inv_bind_pose"] = get_local_bind_pose(j, joints, parents)
        joints[j]["offset"] = joints[j]["local_inv_bind_pose"][3,:3]
        joints[j]["rotation"] = quaternion_from_matrix(joints[j]["local_inv_bind_pose"].T)
        print(j, joints[j]["offset"])

def extract_skeleton(data, skin_idx):
    skeleton = dict()
    skin = data.skins[skin_idx]
    a_idx = skin.inverseBindMatrices
    if a_idx < len(data.accessors):
        skeleton["inv_bind_matrices"] = extract_inv_bind_matrices(data, a_idx)                 
        print("loaded", len(skeleton["inv_bind_matrices"]), "matrices")
    joints = dict()
    joint_count = 0
    animated_joints = []
    for node_idx in skin.joints:
        node = data.nodes[node_idx]
        animated_joints.append(node.name)
    parent_map = dict()
    for node_idx in skin.joints:
        node = data.nodes[node_idx]
        parent_map[node.name] = None
        joint = dict()
        joint["index"] = joint_count
        joint["name"] = node.name
        children = []
        for c_idx in node.children:
            c_name = data.nodes[c_idx].name
            if c_name != node.name:
                children.append(c_name)
                parent_map[c_name] = node.name
                if c_name not in animated_joints:
                    joints[c_name] = create_end_site(c_name)
        joint["children"] = children
        joint["offset"] = transform_pos(node.translation)
        joint["rotation"] = transform_quat(node.rotation)
        joint["scale"] = node.scale
        joint["fixed"] = False
        joint["inv_bind_pose"] = skeleton["inv_bind_matrices"][joint_count]
        #print("bind matrices", node.name, joint["inv_bind_pose"])
        #joint["offset"] = offset#joint["inv_bind_pose"][:3,3]
        #joint["rotation"] = quaternion_from_matrix(np.linalg.inv(joint["inv_bind_pose"]))
        joint["channels"] = ["Xrotation","Yrotation","Zrotation"]
        joint["node_type"] = 1
        joints[node.name] = joint
        if len(children) == 0:
            end_site_name = node.name + "EndSite"
            end_site = create_end_site(end_site_name)
            joints[end_site_name] = end_site
            joints[node.name]["children"].append(end_site_name)
        joint_count+=1
    root_joint = animated_joints[0]
    while parent_map[root_joint] is not None:
        root_joint = parent_map[root_joint]
    joints[root_joint]["node_type"] = 0
    #set_pose_from_bind_pose(joints, parent_map)
    skeleton["nodes"] = joints
    skeleton["root"] = root_joint
    skeleton["animated_joints"] = animated_joints
    skeleton["frame_time"] = 1.0/30
    assert len(animated_joints)==len(skeleton["inv_bind_matrices"])
    print("loaded",len(animated_joints), "joints")
    return skeleton

def extract_anim_func(data, sampler):
    time_a_idx = sampler.input
    value_a_idx = sampler.output
    interpolation = sampler.interpolation
    time_func = extract_values(data, time_a_idx)
    value_func = extract_values(data, value_a_idx)
    return list(zip(time_func, value_func))

def extract_animations(data):
    animations = dict()
    if hasattr(data, "animations") and data.animations is not None:
        for a in data.animations:
            print(a.channels)
            for c in a.channels:
                channel_desc = dict()
                sampler_idx = c.sampler
                if sampler_idx > len(a.samplers):
                    continue
                node_id = c.target.node
                node_name = data.nodes[node_id].name
                if node_name not in animations:
                    animations[node_name] = dict()
                print(node_name, c.target.path)
                animations[node_name][c.target.path] = extract_anim_func(data, a.samplers[sampler_idx])
    return animations

def load_model_from_gltf_file(filename):
    data = gltf.GLTF2().load(filename)
    data.convert_buffers(gltf.BufferFormat.BINARYBLOB)
    #print(data.nodes[0])
    model_data = dict()
    meshes = list()
    skeleton = None

    for node in data.nodes:
        if node.mesh is not None:
            for p in data.meshes[node.mesh].primitives:
                mesh = extract_mesh(data, p)
                if "vertices" not in mesh:
                    continue
                if p.material is not None:
                    mesh["material"] = extract_material(data, p.material)
                meshes.append(mesh)
        if node.skin is not None:
            skeleton = extract_skeleton(data, node.skin)
            print(skeleton)
    #skeleton = None
    animations = extract_animations(data)
    print("found",len(animations), "animations")
    model_data["mesh_list"] = meshes
    model_data["skeleton"] = skeleton
    model_data["animations"] = animations
    return model_data


if __name__ == "__main__":
    filename = r"C:\Users\herrmann\Downloads\Box.gltf"
    load_model_from_gltf_file(filename)
