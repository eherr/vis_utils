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
import math
from copy import copy
import numpy as np


def merge_vertices_and_normals(vertices, normals):
    data = []
    for i in range(len(vertices)):
        data.append(vertices[i] + normals[i])
    return data


def construct_triangle_sphere(slices, stacks, diameter):
    """ src: http://jacksondunstan.com/articles/1904 
    """
    stepTheta = (2.0 * math.pi) / slices
    stepPhi = math.pi / stacks
    verticesPerStack = slices + 1

    positions = []
    normals = []
    triangles = []

    # Pre-compute half the sin/cos of thetas
    halfCosThetas = []
    halfSinThetas = []
    curTheta = 0
    for slice in range(verticesPerStack):
        halfCosThetas.append(math.cos(curTheta) * 0.5)
        halfSinThetas.append(math.sin(curTheta) * 0.5)
        curTheta += stepTheta

    # Generate positions
    curPhi = math.pi
    for stack in range(stacks + 1):
        curY = math.cos(curPhi) * 0.5 * diameter
        sinCurPhi = math.sin(curPhi)
        for slice in range(verticesPerStack):
            point = [halfCosThetas[slice] * sinCurPhi * diameter, curY, halfSinThetas[slice] * sinCurPhi * diameter]
            positions.append(point)
            normals.append([point[0], point[1], point[2]])
        curPhi -= stepPhi

    # Generate triangles
    lastStackFirstVertexIndex = 0
    curStackFirstVertexIndex = verticesPerStack

    for stack in range(stacks):
        for slice in range(slices):
            # Bottom tri of the quad
            a = lastStackFirstVertexIndex + slice + 1
            b = curStackFirstVertexIndex + slice
            c = lastStackFirstVertexIndex + slice
            triangles.append([a, b, c])

            # Top tri of the quad
            a = lastStackFirstVertexIndex + slice + 1
            b = curStackFirstVertexIndex + slice + 1
            c = curStackFirstVertexIndex + slice
            triangles.append([a, b, c])
        lastStackFirstVertexIndex += verticesPerStack
        curStackFirstVertexIndex += verticesPerStack

    data = merge_vertices_and_normals(positions, normals)
    return data, triangles


def construct_quad_box(width, height, depth):
    print("create box", width, height, depth)
    data = np.array([
        # north
        [-width / 2, -height / 2, -depth / 2, 0, 0, -1],
        [-width / 2, height / 2, -depth / 2, 0, 0, -1],
        [width / 2, height / 2, -depth / 2, 0, 0, -1],
        [width / 2, -height / 2, -depth / 2, 0, 0, -1],
        # ,[ width/2, -height/2, -depth/2],[ -width/2, -height/2, -depth/2]
        ###west
        [-width / 2, -height / 2, -depth / 2, -1, 0, 0],
        [-width / 2, height / 2, -depth / 2, -1, 0, 0],
        [-width / 2, height / 2, depth / 2, -1, 0, 0],
        [-width / 2, -height / 2, depth / 2, -1, 0, 0],
        ###south
        [-width / 2, -height / 2, depth / 2, 0, 0, 1],
        [-width / 2, height / 2, depth / 2, 0, 0, 1],
        [width / 2, height / 2, depth / 2, 0, 0, 1],
        [width / 2, -height / 2, depth / 2, 0, 0, 1],
        ###east
        [width / 2, -height / 2, -depth / 2, 1, 0, 0],
        [width / 2, height / 2, -depth / 2, 1, 0, 0],
        [width / 2, height / 2, depth / 2, 1, 0, 0],
        [width / 2, -height / 2, depth / 2, 1, 0, 0],

        ##bottom
        [-width / 2, -height / 2, -depth / 2, 0, -1, 0],
        [-width / 2, -height / 2, depth / 2, 0, -1, 0],
        [width / 2, -height / 2, depth / 2, 0, -1, 0],
        [width / 2, -height / 2, -depth / 2, 0, -1, 0],
        ##top
        [-width / 2, height / 2, -depth / 2, 0, 1, 0],
        [-width / 2, height / 2, depth / 2, 0, 1, 0],
        [width / 2, height / 2, depth / 2, 0, 1, 0],
        [width / 2, height / 2, -depth / 2, 0, 1, 0]
    ], 'f')
    return data


def construct_quad_box_based_on_height(width, height, depth):
    data = np.array([
        # north
        [-width / 2, 0.0, -depth / 2, 0, 0, -1],
        [-width / 2, height, -depth / 2, 0, 0, -1],
        [width / 2, height, -depth / 2, 0, 0, -1],
        [width / 2, 0.0, -depth / 2, 0, 0, -1],
        # ,[ width/2, -height/2, -depth/2],[ -width/2, -height/2, -depth/2]
        ###west
        [-width / 2, 0.0, -depth / 2, -1, 0, 0],
        [-width / 2, height, -depth / 2, -1, 0, 0],
        [-width / 2, height, depth / 2, -1, 0, 0],
        [-width / 2, 0.0, depth / 2, -1, 0, 0],
        ###south
        [-width / 2, 0.0, depth / 2, 0, 0, 1],
        [-width / 2, height, depth / 2, 0, 0, 1],
        [width / 2, height, depth / 2, 0, 0, 1],
        [width / 2, 0.0, depth / 2, 0, 0, 1],
        ###east
        [width / 2, 0.0, -depth / 2, 1, 0, 0],
        [width / 2, height, -depth / 2, 1, 0, 0],
        [width / 2, height, depth / 2, 1, 0, 0],
        [width / 2, 0.0, depth / 2, 1, 0, 0],
        ##bottom
        [-width / 2, 0.0, -depth / 2, 0, 1, 0],
        [-width / 2, 0.0, depth / 2, 0, 1, 0],
        [width / 2, 0.0, depth / 2, 0, 1, 0],
        [width / 2, 0.0, -depth / 2, 0, 1, 0],
        ##top
        [-width / 2, height, -depth / 2, 0, -1, 0],
        [-width / 2, height, depth / 2, 0, -1, 0],
        [width / 2, height, depth / 2, 0, -1, 0],
        [width / 2, height, -depth / 2, 0, -1, 0]
    ], 'f')
    return data


def construct_triangle_cylinder(slices, radius, length):
    """ http://monsterden.net/software/ragdoll-pyode-tutorial
    http://wiki.unity3d.com/index.php/ProceduralPrimitives
    """
    half_length = length / 2.0
    vertices = []
    normals = []
    triangles = []
    v_idx = 0
    #bottom
    vertices.append([0, 0, half_length])
    normals.append([0, 0, -1])
    for i in range(0, slices+1):
        angle = i / float(slices) * 2.0 * np.pi
        ca = np.cos(angle)
        sa = np.sin(angle)
        vertices.append([radius * ca, radius * sa, half_length])
        normals.append([0, 0, 1])

    for idx in range(0, slices):
        triangles.append([0, v_idx+1, v_idx+2])
        v_idx += 1

    #sides
    for i in range(0, slices+1):
        angle = i / float(slices) * 2.0 * np.pi
        ca = np.cos(angle)
        sa = np.sin(angle)
        vertices.append([radius * ca, radius * sa, half_length])
        vertices.append([radius * ca, radius * sa, -half_length])
        normals.append([ca, sa, 0])
        normals.append([ca, sa, 0])

    for idx in range(0, slices*2):
        triangles.append([v_idx, v_idx + 1, v_idx + 2])
        v_idx += 1

    #top
    start = len(vertices)
    vertices.append([0, 0, -half_length])
    normals.append([0, 0, -1])
    for i in range(0, slices+1):
        angle = i / float(slices) * 2.0 * np.pi
        ca = np.cos(angle)
        sa = np.sin(angle)
        vertices.append([radius * ca, radius * sa, -half_length])
        normals.append([0, 0, -1])

    for idx in range(0, slices):
        triangles.append([start, v_idx+1, v_idx + 2])
        v_idx += 1

    return merge_vertices_and_normals(vertices, normals), triangles


def construct_triangle_capsule(slices, stacks, diameter, length, direction="z"):
    data, triangles = construct_triangle_sphere(slices, stacks, diameter)
    data = np.array(data)
    half_idx = int(len(data)/2.0)
    half_len = length/2
    data[:half_idx, 1] -= half_len
    data[half_idx:, 1] += half_len
    if direction == "x":
        m = np.array([[0, 1, 0],
                     [1, 0, 0],
                     [0, 0, -1]])
        data = transform_vertex_data(data, m)
    elif direction == "z":
        m = np.array([[1, 0, 0],
                     [0, 0, -1],
                     [0, 1, 0]])
        data = transform_vertex_data(data, m)
    return data, triangles


def transform_vertex_data(data, m):
    transformed_data = []
    for v in data:
        t_v = np.zeros(6)
        t_v[:3] = np.dot(m, v[:3])[:3]
        t_v[3:] = np.dot(m, v[3:])[:3]
        transformed_data.append(t_v)
    return transformed_data
