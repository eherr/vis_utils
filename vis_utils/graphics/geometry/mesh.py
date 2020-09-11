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
import json
from OpenGL.GL import *
from OpenGL.arrays import vbo
from transformations import quaternion_matrix, quaternion_about_axis, quaternion_multiply, quaternion_from_euler
from .procedural_primitives import *
from ..materials import standard
from ..renderer.primitive_shapes import generate_quads_for_height_map_with_normals, generate_quads_with_normals


def combine_vertex_list_from_faces(faces, vertices, normals, uvs, shift_index = False):
    vertex_list = []
    for face in faces:
         for face_vertex in face:
            v_idx = face_vertex[0]
            if shift_index:
                v_idx -= 1
            if normals is not None:
                n_idx = face_vertex[1]
                if shift_index:
                    n_idx -= 1
            if uvs is not None:
                t_idx = face_vertex[2]
                if shift_index:
                    t_idx -= 1

            point = vertices[v_idx]
            if normals is not None:
                point += normals[n_idx]
            if uvs is not None:
                point += uvs[t_idx]
            vertex_list.append(point)
    return vertex_list


def combine_vertex_list_from_indices(index_list, vertices, normals, colors, uvs, weights, shift_index=False):
    vertex_list = []
    for idx in index_list:
        point = list(vertices[idx])
        if normals is not None:
            point += list(normals[idx])
        if colors is not None:
            point += list(colors[idx])
        if uvs is not None:
            point += list(uvs[idx])
        if weights is not None and len(weights) > 0:
            bids = list(weights[idx][0])
            bw = list(weights[idx][1])
            point += bids + bw
        #print(point)
        vertex_list.append(point)
    return vertex_list


def quaternion_from_vector_to_vector(a, b):
    """src: http://stackoverflow.com/questions/1171849/finding-quaternion-representing-the-rotation-from-one-vector-to-another"""
    if np.all(a == b):
        return [1,0,0,0]
    v = np.cross(a, b)
    if np.linalg.norm(v) == 0.0:
        return quaternion_from_euler(*np.radians([180,0,0]))
    w = np.sqrt((np.linalg.norm(a) ** 2) * (np.linalg.norm(b) ** 2)) + np.dot(a, b)
    q = np.array([w, v[0], v[1], v[2]])
    return q / np.linalg.norm(q)


class Mesh(object):
    def __init__(self, vertex_list, array_type, normal_pos,color_pos, uv_pos,weight_pos, bone_id_pos,  stride, index_list=None, material=None):
        self.vertex_list = vertex_list
        self.index_list = index_list
        self.vertex_buffer = vbo.VBO(np.array(vertex_list, dtype='f'))
        if index_list is not None:
            self.index_buffer = vbo.VBO(np.array(index_list, dtype='uint32'), target=GL_ELEMENT_ARRAY_BUFFER)
        else:
            self.index_buffer = None
        self.array_type = array_type
        self.stride = stride
        self.normal_pos = normal_pos
        self.color_pos = color_pos
        self.uv_pos = uv_pos
        self.weight_pos = weight_pos
        self.bone_id_pos = bone_id_pos
        self.material = material
        self.transform = np.eye(4)

    def bind(self):
        self.vertex_buffer.bind()
        if self.index_buffer is not None:
            self.index_buffer.bind()
    def unbind(self):
        self.vertex_buffer.unbind()
        if self.index_buffer is not None:
            self.index_buffer.unbind()

    def get_vertex_pointer(self):
        return self.vertex_buffer

    def get_normal_pointer(self):
        return self.vertex_buffer+self.normal_pos

    def get_color_pointer(self):
        return self.vertex_buffer+self.color_pos

    def get_uv_pointer(self):
        return self.vertex_buffer+self.uv_pos

    def get_bone_id_pointer(self):
        return self.vertex_buffer+self.bone_id_pos

    def get_weight_pointer(self):
        return self.vertex_buffer+self.weight_pos

    def get_num_vertices(self):
        return len(self.vertex_list)

    def get_num_indices(self):
        if self.index_list is not None:
            return len(self.index_list)
        else:
            return -1

    def scale(self, scale_factor):
        self.vertex_list = np.array(self.vertex_list)
        self.vertex_list[:, :3] *= scale_factor
        self.vertex_buffer = vbo.VBO(np.array(self.vertex_list, dtype='f'))

    def has_uv(self):
        return self.uv_pos > 0

    def has_normal(self):
        return self.normal_pos > 0

    def has_bone_ids(self):
        return self.bone_id_pos > 0

    def has_weights(self):
        return self.weight_pos > 0

    @classmethod
    def build_from_desc(cls, desc, material=None):
        if material is None:
            material = standard
        if desc["type"] == "triangles":
            array_type = GL_TRIANGLES
        elif desc["type"] == "quads":
            array_type = GL_QUADS
        else:
            array_type = GL_TRIANGLES
        shift = False
        if "shift_index" in desc:
            shift = desc["shift_index"]
        vertices = desc["vertices"]
        offset = 12
        colors = None
        normals = None
        uvs = None
        weights = None
        index_list = None
        normal_pos = -1
        color_pos = -1
        uv_pos = -1
        weight_pos = -1
        bone_id_pos = -1
        if "normals" in desc:
            normals = desc["normals"]
            normal_pos = offset
            offset += 12
        if "colors" in desc and desc["colors"] is not None and False:
            colors = desc["colors"]
            color_pos = offset
            offset += 12
        if "texture_coordinates" in desc:
            uvs = desc["texture_coordinates"]
            uv_pos = offset
            offset += 8
        if "weights" in desc and "joint_indices" in desc:
            weights = list(zip(desc["joint_indices"], desc["weights"]))
            bone_id_pos = offset
            weight_pos = offset + 16
            offset += 32
        elif "weights" in desc:
            weights = desc["weights"]
            bone_id_pos = offset
            weight_pos = offset + 16
            offset += 32

        if "faces" in desc:
            faces = desc["faces"]
            vertex_list = combine_vertex_list_from_faces(faces, vertices, normals, uvs, shift)
        elif "indices" in desc:
            index_list = desc["indices"]
            vertex_list = combine_vertex_list_from_indices(index_list, vertices, normals, colors, uvs, weights, shift)
            index_list = None
        else:
            index_list = list(range(len(vertices)))
            vertex_list = combine_vertex_list_from_indices(index_list, vertices, normals, colors, uvs, weights, shift)
            index_list = None
        print("offset",offset, desc.keys())
        return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                    uv_pos=uv_pos, weight_pos=weight_pos,
                    bone_id_pos=bone_id_pos, stride=offset,
                    index_list=index_list, material=material)

    @classmethod
    def build_sphere(cls, slices, stacks, diameter, material=None):
        array_type = GL_TRIANGLES
        uv_pos = -1
        normal_pos = 12
        weight_pos = -1
        color_pos = -1
        bone_id_pos = -1
        offset = 24
        vertex_list, index_list = construct_triangle_sphere(slices, stacks, diameter)
        index_list = np.ravel(index_list)
        return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                    uv_pos=uv_pos, weight_pos=weight_pos,
                    bone_id_pos=bone_id_pos, stride=offset,
                    index_list=index_list, material=material)

    @classmethod
    def build_box(cls, width, height, depth, material=None):
        array_type = GL_QUADS
        uv_pos = -1
        normal_pos = 12
        weight_pos = -1
        color_pos = -1
        bone_id_pos = -1
        offset = 24
        vertex_list = construct_quad_box(width, height, depth)
        index_list = None
        return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                    uv_pos=uv_pos, weight_pos=weight_pos,
                    bone_id_pos=bone_id_pos, stride=offset,
                    index_list=index_list, material=material)

    @classmethod
    def build_capsule(cls, slices, stacks, diameter, length, direction, material=None, pos_offset=None):
        array_type = GL_TRIANGLES
        uv_pos = -1
        normal_pos = 12
        weight_pos = -1
        color_pos = -1
        bone_id_pos = -1
        offset = 24
        vertex_list, index_list = construct_triangle_capsule(slices, stacks, diameter, length, direction)
        if pos_offset is not None:
            n_vertices = len(vertex_list)
            for idx in range(n_vertices):
                vertex_list[idx][:3] += pos_offset
        index_list = np.ravel(index_list)
        return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                    uv_pos=uv_pos, weight_pos=weight_pos,
                    bone_id_pos=bone_id_pos, stride=offset,
                    index_list=index_list, material=material)


    @classmethod
    def build_legacy_animated_mesh(cls, desc, material=None):
        if desc["type"] == "triangles":
            array_type = GL_TRIANGLES
        elif desc["type"] == "quads":
            array_type = GL_QUADS
        else:
            array_type = GL_TRIANGLES

        offset = 12
        if "normals" in desc:
            normals = desc["normals"]
            normal_pos = offset
            offset += 12
        if "colors" in desc and desc["colors"] is not None and False:
            colors = desc["colors"]
            color_pos = offset
            offset += 12
        if "texture_coordinates" in desc:
            uvs = desc["texture_coordinates"]
            uv_pos = offset
            offset += 8
        if "weights" in desc:
            weights = desc["weights"]
            bone_id_pos = offset
            weight_pos = offset + 16
            offset += 32
        vertices = desc["vertices"]
        normals = desc["normals"]
        uvs = desc["texture_coordinates"]
        indices = desc["indices"]
        weights = desc["weights"]
        n_vertices = len(vertices)
        n_uvs = len(uvs)
        n_normals = len(normals)
        n_weights = len(weights)
        vertex_list = None
        print("loaded mesh", n_vertices, n_normals, n_uvs, n_weights)
        if n_normals == n_vertices and n_uvs == n_vertices:
            data = list()
            for idx, i in enumerate(indices):
                v = vertices[idx]
                n = normals[idx]
                t = uvs[idx]
                bids = [-1, -1, -1, -1]
                bw = [0.0, 0.0, 0.0, 0.0]
                if len(weights) > 0:
                    bids = weights[idx][0]
                    bw = weights[idx][1]

                entry = v + n + t + bids + bw
                data.append(entry)
            vertex_list = data

        color_pos = -1

        #offset = weight_pos + 16
        index_list = None
        if vertex_list is not None:
            return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                        uv_pos=uv_pos, weight_pos=weight_pos,
                        bone_id_pos=bone_id_pos, stride=offset,
                        index_list=index_list, material=material)
        else:
            return None


    @classmethod
    def build_terrain(cls, width, depth, steps, uv_scale, material):
        array_type = GL_QUADS
        normal_pos = 12
        uv_pos = 24
        weight_pos = -1
        color_pos = -1
        bone_id_pos = -1
        offset = 32
        vertex_list = generate_quads_for_height_map_with_normals(width, depth, steps, uv_scale,
                                                                   material.height_map_texture.image,
                                                                   material.height_map_scale)
        index_list = None
        return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                    uv_pos=uv_pos, weight_pos=weight_pos,
                    bone_id_pos=bone_id_pos, stride=offset,
                    index_list=index_list, material=material)

    @classmethod
    def build_plane(cls, width, depth, steps, uv_scale, material):
        array_type = GL_QUADS
        normal_pos = 12
        uv_pos = 24
        weight_pos = -1
        color_pos = -1
        bone_id_pos = -1
        offset = 32
        vertex_list = generate_quads_with_normals(width, depth, steps, uv_scale)
        index_list = None
        return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                    uv_pos=uv_pos, weight_pos=weight_pos,
                    bone_id_pos=bone_id_pos, stride=offset,
                    index_list=index_list, material=material)


    @classmethod
    def build_from_triangles(cls, vertices, normals, indices, material):
        array_type = GL_TRIANGLES
        normal_pos = 12
        uv_pos = -1
        weight_pos = -1
        color_pos = -1
        bone_id_pos = -1
        offset = 24
        vertex_list = []
        for p,n in zip(vertices, normals):
            vertex_list.append(p.tolist()+n.tolist())
        vertex_list = np.array(vertex_list)
        index_list = indices
        return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                    uv_pos=uv_pos, weight_pos=weight_pos,
                    bone_id_pos=bone_id_pos, stride=offset,
                    index_list=index_list, material=material)

    @classmethod
    def build_from_file(cls, filename, material=None):
        with open(filename, "rt") as in_file:
            desc = json.load(in_file)
            vertex_list = desc["vertex_list"]
            index_list = None
            if "index_list" in desc:
                index_list = desc["index_list"]
            array_type = desc["array_type"]
            stride = desc["stride"]
            normal_pos = desc["normal_pos"]
            color_pos = desc["color_pos"]
            uv_pos = desc["uv_pos"]
            weight_pos = desc["weight_pos"]
            bone_id_pos = desc["bone_id_pos"]
            return Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                        uv_pos=uv_pos, weight_pos=weight_pos,
                        bone_id_pos=bone_id_pos, stride=stride,
                        index_list=index_list, material=material)

    def save_to_file(self, filename):
        desc = dict()
        desc["vertex_list"] = self.vertex_list.tolist()
        if self.index_list is not None:
            desc["index_list"] = self.index_list.tolist()
        desc["array_type"] = self.array_type
        desc["stride"] = self.stride
        desc["normal_pos"] = self.normal_pos
        desc["color_pos"] = self.color_pos
        desc["uv_pos"] = self.uv_pos
        desc["weight_pos"] = self.weight_pos
        desc["bone_id_pos"] = self.bone_id_pos
        with open(filename, "wt") as out_file:
            json.dump(desc, out_file)

    @classmethod
    def build_bone_shape(cls, offset_vector, size, material=None):
        REF_VECTOR = [0, 1, 0]
        array_type = GL_QUADS
        uv_pos = -1
        normal_pos = 12
        weight_pos = -1
        color_pos = -1
        bone_id_pos = -1
        offset = 24
        rotation = np.eye(4)
        length = np.linalg.norm(offset_vector)
        offset_vector /= length
        q = quaternion_from_vector_to_vector(REF_VECTOR, offset_vector)
        q = quaternion_multiply(q, quaternion_about_axis(np.radians(180), [0, 1, 0]))
        rotation[:3, :3] = quaternion_matrix(q)[:3, :3]
        vertex_list = construct_quad_box_based_on_height(size, length, size)
        index_list = None

        m = Mesh(vertex_list, array_type, normal_pos=normal_pos, color_pos=color_pos,
                 uv_pos=uv_pos, weight_pos=weight_pos,
                 bone_id_pos=bone_id_pos, stride=offset,
                 index_list=index_list, material=material)

        m.transform = rotation
        return m
