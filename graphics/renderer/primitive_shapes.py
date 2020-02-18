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
from OpenGL.GL import *
from OpenGL.arrays import vbo
from OpenGL.raw.GL.ARB.vertex_array_object import glGenVertexArrays, glBindVertexArray
from transformations import quaternion_matrix, quaternion_about_axis, quaternion_multiply, quaternion_from_euler
from ...graphics.geometry.procedural_primitives import *
from ...graphics.renderer.base_types import ShadedGeometryRenderer, DirectionalShadedGeometryRenderer, TexturedGeometryRenderer, DirectionalShadedIndexRenderer, ShadedTextureTechnique
from .techniques import TerrainTechnique
from ...graphics import materials


def generate_quad(width, depth, uv_scale):
    # store xyz and uv coordinates per vertex
    vertices = np.array([[-width / 2, 0, -depth / 2, 0, 0],
              [-width / 2, 5, depth / 2, width / uv_scale, 0],
              [width / 2, 0, depth / 2, width / uv_scale, depth / uv_scale],
              [width / 2, 500, -depth / 2, 0, depth / uv_scale]]
             , 'f')
    return vertices



def generate_quads_with_normals(width, depth, steps, uv_scale):
    # store xyz and uv coordinates per vertex
    vertex_start = np.array([-width / 2, 0, -depth / 2])
    uv_start = np.array([0, 0])
    x_steps = range(steps)
    z_steps = range(steps)
    x_step_size = width / steps
    z_step_size = depth / steps
    uv_step_size = uv_scale / steps
    vertices = []
    for x in x_steps:
        for z in z_steps:
            vertex = vertex_start + [x * x_step_size, 0, 0] + [0, 0, z * z_step_size]
            uv = uv_start + [x * uv_step_size, 0] + [0, z * uv_step_size]
            v1 = vertex.tolist() +[0,1,0] + uv.tolist()
            vertices.append(v1)

            x += 1
            vertex = vertex_start + [x * x_step_size, 0, 0] + [0, 0, z * z_step_size]
            uv = uv_start + [x * uv_step_size, 0] + [0, z * uv_step_size]
            v2 = vertex.tolist()+[0,1,0] + uv.tolist()
            vertices.append(v2)

            z += 1
            vertex = vertex_start + [x * x_step_size, 0, 0] + [0, 0, z * z_step_size]
            uv = uv_start + [x * uv_step_size, 0] + [0, z * uv_step_size]
            v3 = vertex.tolist() +[0,1,0]+ uv.tolist()
            vertices.append(v3)

            x -= 1
            vertex = vertex_start + [x * x_step_size, 0, 0] + [0, 0, z * z_step_size]
            uv = uv_start + [x * uv_step_size, 0] + [0, z * uv_step_size]
            v4 = vertex.tolist() +[0,1,0] + uv.tolist()
            vertices.append(v4)
    vertices = np.array(vertices, 'f')
    return vertices


def generate_quads(width, depth, steps, uv_scale):
    # store xyz and uv coordinates per vertex
    vertex_start = np.array([-width / 2, 0, -depth / 2])
    uv_start = np.array([0, 0])
    x_steps = range(steps)
    z_steps = range(steps)
    x_step_size = width / steps
    z_step_size = depth / steps
    uv_step_size = uv_scale / steps
    vertices = []
    for x in x_steps:
        for z in z_steps:
            vertex = vertex_start + [x * x_step_size, 0, 0] + [0, 0, z * z_step_size]
            uv = uv_start + [x * uv_step_size, 0] + [0, z * uv_step_size]
            v1 = vertex.tolist() + uv.tolist()
            vertices.append(v1)

            x += 1
            vertex = vertex_start + [x * x_step_size, 0, 0] + [0, 0, z * z_step_size]
            uv = uv_start + [x * uv_step_size, 0] + [0, z * uv_step_size]
            v2 = vertex.tolist() + uv.tolist()
            vertices.append(v2)

            z += 1
            vertex = vertex_start + [x * x_step_size, 0, 0] + [0, 0, z * z_step_size]
            uv = uv_start + [x * uv_step_size, 0] + [0, z * uv_step_size]
            v3 = vertex.tolist() + uv.tolist()
            vertices.append(v3)

            x -= 1
            vertex = vertex_start + [x * x_step_size, 0, 0] + [0, 0, z * z_step_size]
            uv = uv_start + [x * uv_step_size, 0] + [0, z * uv_step_size]
            v4 = vertex.tolist() + uv.tolist()
            vertices.append(v4)
    vertices = np.array(vertices, 'f')
    return vertices


def generate_height_map_quad(x, z, vertex_start, uv_start, x_step_size,z_step_size, uv_step_size, height_uv_step_size):
    """store xyz and 4 uv coordinates per vertex"""
    vertices = []
    vertex = vertex_start + [x * x_step_size, 0, -z * z_step_size]
    uv = uv_start + [x * uv_step_size, 0, x * height_uv_step_size, 0] + [0, z * uv_step_size,
                                                                         0, z * height_uv_step_size]
    v1 = vertex.tolist() + uv.tolist()
    vertices.append(v1)

    x += 1
    vertex = vertex_start + [x * x_step_size, 0, -z * z_step_size]
    uv = uv_start + [x * uv_step_size, 0, x * height_uv_step_size, 0] + [0, z * uv_step_size,
                                                                         0, z * height_uv_step_size]
    v2 = vertex.tolist() + uv.tolist()
    vertices.append(v2)

    z += 1
    vertex = vertex_start + [x * x_step_size, 0, -z * z_step_size]
    uv = uv_start + [x * uv_step_size, 0, x * height_uv_step_size, 0] + [0, z * uv_step_size,
                                                                         0, z * height_uv_step_size]
    v3 = vertex.tolist() + uv.tolist()
    vertices.append(v3)

    x -= 1
    vertex = vertex_start + [x * x_step_size, 0, -z * z_step_size]
    uv = uv_start + [x * uv_step_size, 0,
                     x * height_uv_step_size, 0] + [0, z * uv_step_size,
                                                    0, z * height_uv_step_size]
    v4 = vertex.tolist() + uv.tolist()
    vertices.append(v4)
    return vertices


def generate_quads_for_height_map(width, depth, steps, uv_scale):
    """note x is added and z is substracted to make the pixel coordinates work"""

    vertex_start = np.array([-width / 2, 0, depth / 2])
    uv_start = np.array([0, 0, 0, 0])
    x_steps = range(steps)
    z_steps = range(steps)
    x_step_size = width / steps
    z_step_size = depth / steps
    uv_step_size = uv_scale / steps
    height_uv_step_size = 1.0/steps
    vertices = []
    for x in x_steps:
        for z in z_steps:
            quad = generate_height_map_quad(x,z,vertex_start, uv_start, x_step_size,z_step_size, uv_step_size, height_uv_step_size)
            vertices += quad
    vertices = np.array(vertices, 'f')
    return vertices


def calculate_normal(v1, v2, v3):
    """ the order affects the direction"""
    a = v2-v1
    a /= np.linalg.norm(a)
    b = v3-v1
    b /= np.linalg.norm(b)

    normal = np.cross(a,b)
    normal /= np.linalg.norm(normal)
    return normal


def get_height(x, z, width, depth, image, scale):
    lx = x
    lz = z
    lx += width / 2
    lz += depth / 2
    # scale by width and depth to range of 1
    lx /= width
    lz /= depth
    ix = lx * image.size[0]
    iy = lz * image.size[1]
    ix = min(ix, image.size[0]-1)
    iy = min(iy, image.size[1] - 1)
    #print(x, z, lx, lz, ix, iy)
    p = image.getpixel((ix, iy))[0]
    return (p / 255) * scale


def generate_height_data(width, depth, width_samples, depth_samples, image, scale):
    height_data = []
    x_step_size = width/width_samples
    z_step_size = depth/depth_samples
    for j in range(depth_samples):
        for i in range(width_samples):
            x = i* x_step_size
            z = j * z_step_size
            p = image.getpixel((x, z))[0]
            h = (p / 255) * scale
            #print(x,z, h)
            height_data.append(h)
    return np.array(height_data, dtype=np.float32)


def generate_height_map_quad_normals(x, z, width, depth, offset, x_step_size, z_step_size, uv_step_size, height_map_image, height_scale):
    """store xyz, normals and 2 uv coordinates per vertex"""

    cx = offset[0] + (x * x_step_size)
    cz = offset[2] + (z * z_step_size)
    u = x * uv_step_size
    v = z * uv_step_size

    cy = get_height(cx, cz, width, depth, height_map_image, height_scale)
    v1 = np.array([cx, cy, cz])
    uv1 = [u, v]

    cx += x_step_size
    u += uv_step_size
    cy = get_height(cx, cz, width, depth, height_map_image, height_scale)
    v2 = np.array([cx, cy, cz])
    uv2 = [u, v]

    cz += z_step_size
    v += uv_step_size
    cy = get_height(cx, cz, width, depth, height_map_image, height_scale)
    v3 = np.array([cx, cy, cz])
    uv3 = [u, v]

    cx -= x_step_size
    u -= uv_step_size
    cy = get_height(cx, cz, width, depth, height_map_image, height_scale)
    v4 = np.array([cx, cy, cz])
    uv4 = [u, v]

    n1 = calculate_normal(v1, v3, v2).tolist()
    n2 = calculate_normal(v2, v1, v3).tolist()
    n3 = calculate_normal(v3, v2, v4).tolist()
    n4 = calculate_normal(v4, v3, v2).tolist()

    vertices = []
    vertices.append(v1.tolist() + n1 + uv1)
    vertices.append(v2.tolist() + n2 + uv2)
    vertices.append(v3.tolist() + n3 + uv3)
    vertices.append(v4.tolist() + n4 + uv4)
    return vertices


def generate_quads_for_height_map_with_normals(width, depth, steps, uv_scale, height_map_image, height_scale):
    """note x is added and z is substracted to make the pixel coordinates work"""

    vertex_start = np.array([-width / 2, 0, -depth / 2])
    #vertex_start = np.array([0,0,0])
    x_steps = range(steps)
    z_steps = range(steps)
    x_step_size = width / steps
    z_step_size = depth / steps
    uv_step_size = uv_scale / steps
    vertices = []
    for x in x_steps:
        for z in z_steps:
            quad = generate_height_map_quad_normals(x, z, width, depth, vertex_start, x_step_size, z_step_size, uv_step_size, height_map_image, height_scale)
            #print(quad)
            vertices += quad
    vertices = np.array(vertices, 'f')
    return vertices


class Plane(ShadedGeometryRenderer):
    def __init__(self, width,depth):
        super(Plane,self).__init__()
        self.width = width
        self.depth = depth
        self.numVertices = 4
        self.vertex_array_type = GL_QUADS
        self.vbo = vbo.VBO(
        np.array([[ -width/2, 0, -depth/2, 0,1,0],
            [ -width/2, 0, depth/2, 0,1,0],
            [ width/2, 0, depth/2, 0,1,0],
            [ width/2, 0, -depth/2, 0,1,0]]
            ,'f'))


class TexturedPlaneRenderer(TexturedGeometryRenderer):
    def __init__(self, width, depth, steps, uv_scale, material):
        super(TexturedPlaneRenderer, self).__init__(material)
        self.width = width
        self.depth = depth
        self.vertex_array_type = GL_QUADS
        vertices = generate_quads(width, depth, steps, uv_scale)
        self.vbo = vbo.VBO(vertices)
        self.numVertices = len(vertices)



class TerrainRenderer(object):
    def __init__(self, width, depth, steps, uv_scale, material):
        """
        width/depth: size
        steps: number of subdivsions the higher the more accurate
        uv_scale: zoom applied on the diffuse texture
        material: HeightMapMaterial containing a diffuse texture and a heightmap texture
        """
        self.technique = TerrainTechnique(material)
        self.width = width
        self.depth = depth
        self.vertex_array_type = GL_QUADS
        vertices = generate_quads_for_height_map(width, depth, steps, uv_scale)

        self.vbo = vbo.VBO(vertices)
        self.numVertices = len(vertices)

    def to_relative_coordinates(self, center_x, center_z, x, z):
        """ get position relative to upper left
        """
        relative_x = x - center_x
        relative_z = z - center_z
        relative_x += self.width / 2
        relative_z += self.depth / 2

        # scale by width and depth to range of 1
        relative_x /= self.width
        relative_z /= self.depth
        return relative_x, relative_z

    def get_height(self, relative_x, relative_z):
        if relative_x < 0 or relative_x > 1.0 or relative_z < 0 or relative_z > 1.0:
            print("Coordinates outside of the range")
            return 0
        # scale by image width and height to image range
        height_map_image = self.technique.material.height_map_texture.image
        ix = relative_x*height_map_image.size[0]
        iy = relative_z*height_map_image.size[1]
        p = self.technique.material.height_map_texture.get_pixel(ix, iy)
        return (p[0]/255)*self.technique.material.height_map_scale

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
        self.technique.stop()


class TerrainRenderer2(object):
    def __init__(self, width, depth, steps, uv_scale, material):
        """
        width/depth: size
        steps: number of subdivsions the higher the more accurate
        uv_scale: zoom applied on the diffuse texture
        material: HeightMapMaterial containing a diffuse texture and a heightmap texture
        """
        self.technique = ShadedTextureTechnique(material)
        self.width = width
        self.depth = depth
        self.array_type = GL_QUADS
        self.vertices = generate_quads_for_height_map_with_normals(width, depth, steps, uv_scale, material.height_map_texture.image, material.height_map_scale)

        self.vbo = vbo.VBO(self.vertices)
        self.numVertices = len(self.vertices)

    def to_relative_coordinates(self, center_x, center_z, x, z):
        """ get position relative to upper left
        """
        relative_x = x - center_x
        relative_z = z - center_z
        relative_x += self.width / 2
        relative_z += self.depth / 2

        # scale by width and depth to range of 1
        relative_x /= self.width
        relative_z /= self.depth
        return relative_x, relative_z

    def get_height(self, relative_x, relative_z):
        if relative_x < 0 or relative_x > 1.0 or relative_z < 0 or relative_z > 1.0:
            print("Coordinates outside of the range")
            return 0
        # scale by image width and height to image range
        height_map_image = self.technique.material.height_map_texture.image
        ix = relative_x*height_map_image.size[0]
        iy = relative_z*height_map_image.size[1]
        p = self.technique.material.height_map_texture.get_pixel(ix, iy)
        return (p[0]/255)*self.technique.material.height_map_scale

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vbo, self.array_type, self.numVertices)
        self.technique.stop()


class CylinderRenderer(DirectionalShadedIndexRenderer):
    def __init__(self, slices, radius, length, material=None, color=None):
        if material is None:
            material = copy(materials.standard)
        if color is not None:
            material.diffuse_color = color
        super(CylinderRenderer, self).__init__(material)
        self.constructCylinderMesh(slices, radius, length)

    def constructCylinderMesh(self, slices, radius, length, direction):
        self.slices = slices
        self.radius = radius
        self.vertex_array_type = GL_TRIANGLES
        vertex_list, tris = construct_triangle_cylinder(slices, radius, length)
        self.numVertices = len(vertex_list)
        self.numIndices = len(tris) * 3
        # Create the Vertex Array Object
        self.vertexArrayObject = GLuint(0)
        glGenVertexArrays(1, self.vertexArrayObject)
        glBindVertexArray(self.vertexArrayObject)
        indices = np.array(tris, dtype='uint32')  # np.array(tris).reshape(1,numIndices)[0]
        self.indices = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
        self.vertices = vbo.VBO(np.array(vertex_list, 'f'))


class CapsuleRenderer(DirectionalShadedIndexRenderer):
    def __init__(self, slices, stacks, radius, length, direction="z", material=None, color=None):
        if material is None:
            material = copy(materials.standard)
        if color is not None:
            material.diffuse_color = color
        super(CapsuleRenderer, self).__init__(material)
        self.constructCapsuleMesh(slices, stacks, radius, length, direction)

    def constructCapsuleMesh(self, slices, stacks, radius, length, direction):
        self.slices = slices
        self.stacks = stacks
        self.radius = radius
        self.vertex_array_type = GL_TRIANGLES
        diameter = radius*2
        vertexList, tris = construct_triangle_capsule(slices, stacks, diameter, length, direction)
        self.numVertices = (slices + 1) * (stacks + 1)
        self.numIndices = len(tris) * 3
        # Create the Vertex Array Object
        self.vertexArrayObject = GLuint(0)
        glGenVertexArrays(1, self.vertexArrayObject)
        glBindVertexArray(self.vertexArrayObject)
        indices = np.array(tris, dtype='uint32')  # np.array(tris).reshape(1,numIndices)[0]
        self.indices = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
        self.vertices = vbo.VBO(np.array(vertexList, 'f'))


class SphereRenderer(DirectionalShadedIndexRenderer):
    def __init__(self, slices, stacks, radius, material=None, color=None):
        if material is None:
            material = copy(materials.standard)
        if color is not None:
            color = np.array(color)
            material.diffuse_color = color
            material.ambient_color = color*0.1
        super(SphereRenderer, self).__init__(material)
        self.constructSphereMesh(slices,stacks,radius)

    def constructSphereMesh(self, slices, stacks, radius):
        self.slices = slices
        self.stacks = stacks
        self.radius = radius
        self.vertex_array_type = GL_TRIANGLES
        vertexList, tris = construct_triangle_sphere(slices, stacks, radius * 2)
        self.numVertices = (slices+1) * (stacks + 1)
        self.numIndices = len(tris)*3
        #Create the Vertex Array Object
        self.vertexArrayObject = GLuint(0)
        glGenVertexArrays(1, self.vertexArrayObject)
        glBindVertexArray(self.vertexArrayObject)
        indices = np.array(tris, dtype='uint32')#np.array(tris).reshape(1,numIndices)[0]
        self.indices = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
        self.vertices = vbo.VBO(np.array(vertexList, 'f'))

    def intersectRay(self, sphereOrigin, rayStart, rayDir):
        """ Using equations from  https://www.cl.cam.ac.uk/teaching/1999/AGraphHCI/SMAG/node2.html#eqn:rectray
        http://stackoverflow.com/questions/6533856/ray-sphere-intersection
        http://en.wikipedia.org/wiki/Line%E2%80%93sphere_intersection
        returns triple (intersection (True or False), intersection point, distance to ray origin)
        """
        result = (False, [-1,-1,-1], -1)
        # print sphereOrigin
        originToStart = rayStart - sphereOrigin
        a = (rayDir.x ** 2) + (rayDir.y ** 2) + (rayDir.z ** 2)
        # dirTimesOriginToStart =
        b = 2 * ((rayDir.x * originToStart.x) + (rayDir.y * originToStart.y) + (rayDir.z * originToStart.z))
        c = (originToStart.x) ** 2 + (originToStart.y) ** 2 + (originToStart.z) ** 2 - (self.radius ** 2)
        delta = (b ** 2) - (4 * a * c)
        # print delta
        if delta > 0:
            d1 = -b + math.sqrt(delta) / 2 * a
            d2 = -b - math.sqrt(delta) / 2 * a
            if d1 < d2:  # choose smallest distance from the origin as intersection point
                intersectionPoint = rayStart + (d1 * rayDir)
                result = (True, intersectionPoint, d1)
            else:
                intersectionPoint = rayStart + (d2 * rayDir)
                result = (True, intersectionPoint, d2)
        elif delta == 0:
            d = -b / 2 * a
            intersectionPoint = rayStart + (d * rayDir)
            result = (True, intersectionPoint, d)
        return result


class BoxRenderer(DirectionalShadedGeometryRenderer):
    def __init__(self, width, height, depth, material=None):
        if material is None:
            material = copy(materials.standard)
        super(BoxRenderer, self).__init__(material)
        self.width = width
        self.height = height
        self.depth = depth

        self.vertex_array_type = GL_QUADS
        data = construct_quad_box(width, height, depth)
        self.numVertices = len(data)
        self.vbo = vbo.VBO(data)


class BoneRenderer(DirectionalShadedGeometryRenderer):
    REF_VECTOR = [0, 1, 0]

    def __init__(self, offset_vector, size, material=None):
        if material is None:
            material = copy(materials.standard)
        super(BoneRenderer, self).__init__(material)
        self.rotation = np.eye(4)
        length = np.linalg.norm(offset_vector)
        offset_vector /= length
        q = self.quaternion_from_vector_to_vector(self.REF_VECTOR, offset_vector)
        q = quaternion_multiply(q, quaternion_about_axis(np.radians(180), [0, 1, 0]))
        self.rotation[:3, :3] = quaternion_matrix(q)[:3, :3]
        self.vertex_array_type = GL_QUADS
        data = construct_quad_box_based_on_height(size, length, size)
        self.numVertices = len(data)
        self.vbo = vbo.VBO(data)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        modelMatrix = np.dot(self.rotation, modelMatrix)
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vbo, self.vertex_array_type, self.numVertices)
        self.technique.stop()

    def quaternion_from_vector_to_vector(self, a, b):
        """src: http://stackoverflow.com/questions/1171849/finding-quaternion-representing-the-rotation-from-one-vector-to-another"""
        if np.all(a == b):
            return [1,0,0,0]
        v = np.cross(a, b)
        if np.linalg.norm(v) == 0.0:
            return quaternion_from_euler(*np.radians([180,0,0]))
        w = np.sqrt((np.linalg.norm(a) ** 2) * (np.linalg.norm(b) ** 2)) + np.dot(a, b)
        q = np.array([w, v[0], v[1], v[2]])
        return q / np.linalg.norm(q)
