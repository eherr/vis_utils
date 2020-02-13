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
'''
Created on Aug 6, 2014

@author: erhe01
'''
import os
import numpy as np
from PIL import Image
from copy import copy


def load_obj_file(file_path):
    mesh_list = load_mesh_from_ob_file(file_path)
    file_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    mtl_file = file_dir + os.sep + file_name.split(".")[0] + ".mtl"
    materials = load_materials_from_mtl_file(mtl_file)
    for m in mesh_list:
        print("mesh", m["name"], "material", m["material"], list(materials.keys()))
        if m["material"] in list(materials.keys()):
            key = m["material"]
            print("found material", materials[key])
            m["material"] = materials[key]
            m["has_material"] = True
    return mesh_list


def load_mesh_from_ob_file(filePath):
     '''
     returns a dictionary with the mesh description from an obj. file
     note does not handle exceptions and deviations from the supported obj. format
     '''
     try:
        fo = open(filePath)
        obj_file_lines = fo.readlines()
        fo.close()
     except:
        print("could not read file", filePath)
        return []
     return load_meshes2(obj_file_lines)


def load_meshes(obj_file_lines):
    mesh_desc = {"objects": [], "faces": [], "vertices": [], "normals": [], "shift_index": True,
                 "type": "triangles"}

    m_idx = -1
    for li in range(len(obj_file_lines)):
        split_symbol = '//'
        if split_symbol not in obj_file_lines[li]:
            split_symbol = '/'
        line = (obj_file_lines[li]).split()  # split based on white spaces

        if line[0] == 'o':
            offset = len(mesh_desc["vertices"])
            if m_idx > 0:
                mesh_desc["objects"][m_idx]["end_v_idx"] = offset
            object_desc = {"name": line[1], "start_v_idx": offset, "end_v_idx": offset}
            mesh_desc["objects"].append(object_desc)
            m_idx += 1
        elif line[0] == 'v':
            x = float(line[1])
            y = float(line[2])
            z = float(line[3])
            mesh_desc["vertices"].append([x, y, z])
        elif line[0] == 'vn':
            x = float(line[1])
            y = float(line[2])
            z = float(line[3])
            normal = [x, y, z]
            mesh_desc["normals"].append(normal)

        elif line[0] == 'f':
            faceVertexList = []
            i = 1
            while i < len(line):
                faceVertex = line[i].split(split_symbol)
                if len(faceVertex) == 2:
                    vi = int(faceVertex[0])
                    ti = int(faceVertex[1])
                else:
                    vi = int(faceVertex[0])
                    ti = int(faceVertex[2])

                faceVertexList.append((vi, ti))
                i += 1
            mesh_desc["faces"].append(faceVertexList)
        li += 1

    if m_idx > 0:
        mesh_desc["objects"][m_idx]["end_v_idx"] = len(mesh_desc["vertices"])
    print("loaded", len(mesh_desc["objects"]), "meshes")
    return mesh_desc


def load_meshes2(obj_file_lines, flip_normals=True, shift_index=True):

    mesh_type = "triangles"
    mesh_list = []
    mesh_desc = {"name": "default", "faces": [],
                 "vertices": [], "normals": [],
                 "texture_coordinates": [],
                 "face_groups": [], "shift_index": shift_index,
                 "type": mesh_type, "material": "",
                 "has_material": False}
    mesh_list.append(mesh_desc)
    faces = []
    latest_material = None
    m_idx = 0
    face_group_idx = -1
    for li in range(len(obj_file_lines)):
        split_symbol = '//'
        if split_symbol not in obj_file_lines[li]:
            split_symbol = '/'
        line = (obj_file_lines[li]).split()
        if len(line) < 1:
            continue

        if line[0] == 'o':
            mesh_name = line[1]
            mesh_desc = {"name": mesh_name, "faces": [], "vertices": [],
                         "normals": [], "texture_coordinates": [],
                         "face_groups": [], "shift_index": shift_index,
                         "type": mesh_type, "material": "",
                         "has_material": False}
            mesh_list.append(mesh_desc)
            m_idx += 1
        elif line[0] == 'g':
            if len(mesh_list[m_idx]["face_groups"]) > 0:
                mesh_list[m_idx]["face_groups"][-1]["end"] = len(faces)
            group = dict()
            group["name"] = line[1]
            group["material"] = latest_material
            group["start"] = len(faces)
            group["end"] = None
            mesh_list[m_idx]["face_groups"].append(group)
            face_group_idx += 1
        elif line[0] == 'v':
            if m_idx < 0:
                continue
            vertex = list(map(float, line[1:4]))
            mesh_list[m_idx]["vertices"].append(vertex)
        elif line[0] == 'vn':
            if m_idx < 0:
                continue
            normal = list(map(float, line[1:4]))
            if flip_normals:
                normal = [-n for n in normal]
            mesh_list[m_idx]["normals"].append(normal)
        elif line[0] == 'vt':
            if m_idx < 0:
                continue
            texture_coord = list(map(float, line[1:3]))
            mesh_list[m_idx]["texture_coordinates"].append(texture_coord)
        elif line[0] == 'f':
            if m_idx < 0:
                continue
            face_vertex_list = []
            i = 1
            n_face_vertices = len(line)-1
            while i < n_face_vertices+1:
                face_vertex = line[i].split(split_symbol)
                if len(face_vertex) == 2:
                    vi = int(face_vertex[0])
                    ti = -1
                    ni = int(face_vertex[1])
                else:
                    vi = int(face_vertex[0])
                    ti = int(face_vertex[1])
                    ni = int(face_vertex[2])
                face_vertex_list.append((vi, ni, ti))
                i += 1
            faces.append(face_vertex_list)
        elif line[0] == "usemtl":
            if m_idx < 0:
                continue
            mesh_list[m_idx]["material"] = line[1]
            latest_material = line[1]
        li += 1
    print("loaded", len(mesh_list), "meshes")

    if len(mesh_list) == 1:
        # there is only one mesh defined so all
        # faces belong to this mesh
        mesh_list[0]["faces"] = faces
        mesh_list[0]["type"] = "quads"
        n_face_vertices = len(faces[0])
        if n_face_vertices == 4:
            mesh_list[0]["type"] = "quads"
        else:
            mesh_list[0]["type"] = "triangles"
    else:
        # there are multiple meshes so map faces
        # to meshes based on vertex indices
        mesh_list = map_faces_to_meshes(mesh_list, faces)

    # if there are face groups defined for a mesh split it up
    # into multiple meshes, one per face group
    mesh_list = split_face_groups_to_meshes(mesh_list)

    return mesh_list




def map_faces_to_meshes(mesh_list, faces):
    v_index_list = []
    n_index_list = []
    t_index_list = []
    v_offset = 0
    n_offset = 0
    t_offset = 0
    #calculate index offset for each mesh
    for m in mesh_list:
        n_vertices = len(m["vertices"])
        n_normals = len(m["normals"])
        n_texture_coords = len(m["texture_coordinates"])

        v_index_list.append((v_offset, v_offset + n_vertices))
        n_index_list.append((n_offset, n_offset + n_normals))
        t_index_list.append((t_offset, t_offset + n_texture_coords))

        v_offset += n_vertices
        n_offset += n_normals
        t_offset += n_texture_coords

    #substract offset from indices
    for face in faces:
        #find mesh index
        mesh_idx = -1
        for idx, mesh_vertex_range in enumerate(v_index_list):
            v1 = face[0]
            if mesh_vertex_range[0] <= v1[0] < mesh_vertex_range[1]:
                mesh_idx = idx
        #assign to mesh
        if mesh_idx > 0:
            v_index_offset = v_index_list[mesh_idx][0]
            n_index_offset = n_index_list[mesh_idx][0]
            t_index_offset = t_index_list[mesh_idx][0]
            n_face_vertices = len(face)
            new_face = np.zeros((n_face_vertices, 3), dtype=int)
            for v_idx, v in enumerate(face):
                new_face[v_idx][0] = v[0] - v_index_offset
                new_face[v_idx][1] = v[1] - n_index_offset
                new_face[v_idx][2] = v[2] - t_index_offset

            mesh_list[mesh_idx]["faces"].append(new_face.tolist())

            if n_face_vertices == 4:
                mesh_list[mesh_idx]["type"] = "quads"
            else:
                mesh_list[mesh_idx]["type"] = "triangles"
    return mesh_list

def split_face_groups_to_meshes(mesh_list):
    print("split meshes", len(mesh_list))
    new_meshes = []
    for mesh in mesh_list:
        mesh_list.remove(mesh)
        if len(mesh["face_groups"]) > 0:
            for face_group in mesh["face_groups"]:
                new_mesh = {"name": face_group["name"],
                            "faces": [],
                            "vertices": [],
                            "normals": [],
                            "texture_coordinates": [],
                            "face_groups": [],
                            "shift_index": mesh["shift_index"],
                            "type": mesh["type"],
                            "material": face_group["material"],
                            "has_material": True}
                print("create new mesh ", face_group["start"], face_group["end"], len(mesh["faces"]))
                if face_group["end"] is None:
                    face_group["end"] = len(mesh["faces"])
                for f_idx in range(face_group["start"], face_group["end"]):
                    new_mesh["faces"].append(mesh["faces"][f_idx])
                    #for vertex in mesh["faces"][f_idx]:
                    #    new_mesh["vertices"].append(mesh["vertices"][vertex[0]])
                    #    new_mesh["normals"].append(mesh["normals"][vertex[1]])
                    #    new_mesh["texture_coordinates"].append(mesh["texture_coordinates"][vertex[2]])

                new_mesh["vertices"] = copy(mesh["vertices"])
                new_mesh["normals"] = copy(mesh["normals"])
                new_mesh["texture_coordinates"] = copy(mesh["texture_coordinates"])
                new_meshes.append(new_mesh)

    return mesh_list + new_meshes


def load_image(root_dir, line):
    texture_path = line[1][:-1]
    if not os.path.isabs(texture_path):
        path_list = root_dir.split("/") + texture_path.split('\\')
        texture_path = "/".join(path_list)
    print("try to load", texture_path, os.path.isfile(str(texture_path)))

    if os.path.isfile(texture_path):
        return Image.open(texture_path, "r")


def load_materials_from_mtl_file(file_path):
    materials = dict()
    if os.path.isfile(file_path):
        print("load mtl",file_path)
        fo = open(file_path)
        mtl = fo.readlines()
        fo.close()
        root_dir = os.path.dirname(file_path)
        split_symbol = ' '
        current_material = None
        for li in range(len(mtl)):
            if len(mtl[li]) == 0:
                continue
            if "#" in mtl[li][0]:
                continue
            if split_symbol in mtl[li]:
                line = (mtl[li]).split(split_symbol)
                if len(line) == 0:
                    continue
                if line[0] == "newmtl":
                    current_material = line[1][:-1]
                    materials[current_material] = dict()
                elif line[0] == "map_Kd":
                    print("found diffuse map")
                    if current_material is not None and len(line) >= 2:
                        img_data = load_image(root_dir, line)
                        if img_data is not None:
                            materials[current_material]["Kd"] = img_data

                elif line[0] == "Ns":
                    continue
                elif line[0] == "Ka":
                    continue
                elif line[0] == "Kd":
                    continue
                elif line[0] == "Ks":
                    continue
                elif line[0] == "Ni":
                    continue
                elif line[0] == "d":
                    continue
                elif line[0] == "illum":
                    continue
    print("loaded", len(materials), "materials")
    return materials