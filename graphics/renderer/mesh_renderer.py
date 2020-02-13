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

from motion_analysis.Graphics.geometry.procedural_primitives import *
from motion_analysis.Graphics.renderer.base_types import DirectionalShadedGeometryRenderer, \
    ShadedTexturedRenderer, SkinnedMeshRenderer
from .techniques import ShadedSkinningTextureTechnique, NormalSkinningTextureTechnique
from ...graphics import materials
from ...graphics.utils import get_translation_matrix


class TexturedMeshRenderer(ShadedTexturedRenderer):
    def __init__(self, position, description, material):
        """
        - filePath: optional file path to an .obj file to load
        - description: optional a tuple containing three arrays: faces, vertices, normals.
                        faces contains indices of vertices and normals in the range from 1 to N as found in an obj file
                        vertices list of tuples containing x y z of each vertex at indices 0 to 2
                        normals list of tuples containing  x y z of each face normal at indices 0 to 2
        -material: optional instance of CustomShaders.Material class. if None then standard material is used
        """

        self.initiated = False
        super(TexturedMeshRenderer, self).__init__(material)
        self.vertex_array_type = GL_TRIANGLES
        if description is not None:
            self.buildVBOFromMeshDescription(description)
            self.initiated = True

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        if self.initiated:
            super(TexturedMeshRenderer, self).draw(modelMatrix, viewMatrix, projectionMatrix, lightSources)

    def buildVBOFromMeshDescription(self, description):
         #combine normals and vertices
         if description["type"] == "triangles":
             self.vertex_array_type = GL_TRIANGLES
         elif description["type"] == "quads":
            self.vertex_array_type = GL_QUADS
         else:
            self.vertex_array_type = GL_TRIANGLES
         vertices = description["vertices"]
         normals = description["normals"]
         uvs = description["texture_coordinates"]
         if "faces" in description:
             faces = description["faces"]
             shiftIndices = description["shift_index"]
             # add vertices of each face together with their normals to the vertexList for the vbo
             self.vertexList = []
             self.controlPointIdx = []
             v_count = 0
             for face in faces:
                 for faceVertex in face:
                    v_idx = faceVertex[0]
                    n_idx = faceVertex[1]
                    t_idx = faceVertex[2]
                    #print v_idx, t_idx, texture_coords[v_idx-1], texture_coords[t_idx-1]
                    if shiftIndices:
                        v_idx -= 1
                        n_idx -= 1
                        t_idx -= 1
                    point = vertices[v_idx] + normals[n_idx] + uvs[t_idx]
                    #print "add point", point
                    self.vertexList.append(point)

                    if len(faceVertex) > 3:
                        c_idx = faceVertex[3]
                        self.controlPointIdx.append(c_idx)
                    v_count += 1
         else:
             indices = description["indices"]
             data = list()
             for idx, i in enumerate(indices):
                 v = vertices[idx]
                 n = normals[idx]
                 t = uvs[idx]
                 entry = v + n + t
                 data.append(entry)
             self.vertexList = data

         self.numVertices = len(self.vertexList)
         self.vertexList = np.array(self.vertexList, 'f')
         self.vbo = vbo.VBO(self.vertexList)


    def updateMesh(self, newVertexList):
        #self.vertexList = newVertexList
        self.vbo.set_array(newVertexList)


class ColoredMeshRenderer(DirectionalShadedGeometryRenderer):
    def __init__(self, position, description=None, material=None):
        """
        - filePath: optional file path to an .obj file to load
        - description: optional a tuple containing three arrays: faces, vertices, normals.
                        faces contains indices of vertices and normals in the range from 1 to N as found in an obj file
                        vertices list of tuples containing x y z of each vertex at indices 0 to 2
                        normals list of tuples containing  x y z of each face normal at indices 0 to 2
        -material: optional instance of CustomShaders.Material class. if None then standard material is used
        """

        self.initiated = False
        self.vertex_list = None
        if material is None:
            material = materials.standard

        super(ColoredMeshRenderer, self).__init__(material)
        self.vertex_array_type = GL_TRIANGLES
        if description is not None:
            self.buildVBOFromMeshDescription(description)
            self.initiated = True

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        if self.initiated:
            super(ColoredMeshRenderer, self).draw(modelMatrix, viewMatrix, projectionMatrix, lightSources)

    def buildVBOFromMeshDescription(self, description):
        vertices = description["vertices"]
        normals = description["normals"]
        if description["type"] == "triangles":
            self.vertex_array_type = GL_TRIANGLES

        elif  description["type"] == "quads":
            self.vertex_array_type = GL_QUADS

        else:
            self.vertex_array_type = GL_TRIANGLES
        if "faces" in description:
            faces = description["faces"]
            shiftIndices = description["shift_index"]
            vertex_list = []
            for face in faces:
                 for faceVertex in face:
                    v_idx = faceVertex[0]
                    n_idx = faceVertex[1]
                    if shiftIndices:
                        v_idx -= 1
                        n_idx -= 1
                    # add vertices of each face together with
                    # their normals to the vertexList for the vbo
                    vertex_list.append(vertices[v_idx] + normals[n_idx])
        else:
            indices = description["indices"]
            vertex_list = []
            for idx in indices:
                v = vertices[idx]
                n = normals[idx]
                entry = v + n
                vertex_list.append(entry)

        self.numVertices = len(vertex_list)
        self.vbo = vbo.VBO(np.array(vertex_list, 'f'))
        self.vertex_list = vertex_list

    def updateMesh(self, vertex_list):
        self.vertex_list = vertex_list
        self.vbo.set_array(np.array(vertex_list, 'f'))


class ColoredMeshIndexRenderer(DirectionalShadedGeometryRenderer):
    def __init__(self, position, desc=None, material=None):
        """
        - filePath: optional file path to an .obj file to load
        - desc: optional a tuple containing three arrays: faces, vertices, normals.
                        faces contains indices of vertices and normals in the range from 1 to N as found in an obj file
                        vertices list of tuples containing x y z of each vertex at indices 0 to 2
                        normals list of tuples containing  x y z of each face normal at indices 0 to 2
        -material: optional instance of CustomShaders.Material class. if None then standard material is used
        """
        self.initiated = False
        if material is None:
            material = materials.standard
        super(ColoredMeshIndexRenderer, self).__init__(material)
        self.vertex_array_type = GL_TRIANGLES
        self.modelMatrix = get_translation_matrix(position)
        self.vertexList = np.array([])
        if desc != None:
            self.build_vbo(desc)
            self.initiated = True

    def build_vbo(self, desc):
        #combine normals and vertices
        vertices = desc["vertices"]
        normals = desc["normals"]
        if "triangles" == desc["type"]:
            self.vertex_array_type = GL_TRIANGLES
        elif "quads" == desc["type"]:
            self.vertex_array_type = GL_QUADS
        else:
            self.vertex_array_type = GL_TRIANGLES
        vertexList = []
        offset = 0
        while offset < len(vertices):
            vertexList.append(vertices[offset: offset+3] + normals[offset:offset+3])
            offset += 3
        self.vertexList = np.array(vertexList,'f')

        self.vertexArrayObject = GLuint(0)
        glGenVertexArrays(1, self.vertexArrayObject)
        glBindVertexArray(self.vertexArrayObject)

        # prepare vertex buffer for indexed drawing,
        # this allows to reuse vertices instead of having to define the same
        #  vertex multiple times
        #see http://ogldev.atspace.co.uk/www/tutorial10/tutorial10.html
        indices = np.array(desc["indices"], dtype='uint32')
        self.indexPositions = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)
        self.vertexPositions = vbo.VBO(self.vertexList)
        self.numIndices = len(indices)
        self.numVertices = len(self.vertexList)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):

        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)

        glEnableClientState(GL_VERTEX_ARRAY)

        self.indexPositions.bind()
        self.vertexPositions.bind()

        glEnableVertexAttribArray(self.technique.vertex_loc)
        glVertexAttribPointer(self.technique.vertex_loc, 3, GL_FLOAT,False, 24, self.vertexPositions ) #The starting point of the VBO, for the vertices
        glEnableVertexAttribArray(self.technique.vertex_normal_loc )
        glVertexAttribPointer(self.technique.vertex_normal_loc, 3, GL_FLOAT,False, 24, self.vertexPositions+12 )   #skip 6 bytes to get to the next element of the interleaved vertex array
        glDrawElements(GL_TRIANGLES, self.numIndices, GL_UNSIGNED_INT, None)
        glDrawArrays(self.vertex_array_type, 0, self.numVertices)#TRIANGLES
        self.vertexPositions.unbind()
        self.indexPositions.unbind()
        glDisableVertexAttribArray( self.technique.vertex_loc )
        glDisableVertexAttribArray( self.technique.vertex_normal_loc )
        glDisableClientState(GL_VERTEX_ARRAY)
        glUseProgram(0)

    def updateMesh(self,vertexList):
        """Reuploads the vertexList to the vertex buffer object
        * vertexList : np.ndarray
        """
        self.vertexPositions.set_array(vertexList)


class AnimatedMeshRenderer(SkinnedMeshRenderer):
    def __init__(self, position, description=None, material=None):
        """
        - filePath: optional file path to an .obj file to load
        - description: optional a tuple containing three arrays: faces, vertices, normals.
                        faces contains indices of vertices and normals in the range from 1 to N as found in an obj file
                        vertices list of tuples containing x y z of each vertex at indices 0 to 2
                        normals list of tuples containing  x y z of each face normal at indices 0 to 2
        -material: optional instance of CustomShaders.Material class. if None then standard material is used
        """
        self.initiated = False
        if material is None:
            material = materials.standard

        super(AnimatedMeshRenderer, self).__init__(material)
        self.vertex_array_type = GL_TRIANGLES
        if description is not None:
            self.buildVBOFromMeshDescription(description)
            self.initiated = True

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources, boneMatrices):
        if self.initiated:
            super(AnimatedMeshRenderer, self).draw(modelMatrix, viewMatrix, projectionMatrix, lightSources, boneMatrices)

    def buildVBOFromMeshDescription(self, description):

        if "triangles" == description["type"]:
            self.vertex_array_type = GL_TRIANGLES
        elif "quads" == description["type"]:
            self.vertex_array_type = GL_QUADS
        else:
            self.vertex_array_type = GL_TRIANGLES

        vertices = description["vertices"]
        normals = description["normals"]
        if "faces" in description:
            faces = description["faces"]
            bone_ids = description["boneIds"]
            bone_weights = description["boneWeights"]
            shiftIndices = description["shift_index"]
            vertex_list = []
            for face in faces:
                # print "face", face
                for faceVertex in face:
                    v_idx = faceVertex[0]
                    n_idx = faceVertex[1]
                    b_idx = v_idx
                    if shiftIndices:
                        v_idx -= 1
                        n_idx -= 1
                    # add vertices of each face together with
                    # their normals to the vertexList for the vbo
                    print(bone_ids[b_idx] + bone_weights[b_idx])
                    vertex_list.append(vertices[v_idx] + normals[n_idx] +
                                       bone_ids[b_idx] + bone_weights[b_idx])
        else:
            indices = description["indices"]
            uvs = description["indices"]
            data = list()
            for idx, i in enumerate(indices):
                v = vertices[idx]
                n = normals[idx]
                t = uvs[idx]
                entry = v + n + t
                data.append(entry)
            self.vertex_list = data
        self.numVertices = len(vertex_list)
        self.vbo = vbo.VBO(np.array(vertex_list, 'f'))


class AnimatedTexturedMeshRenderer(object):
    def __init__(self, description, material):
        self.technique = ShadedSkinningTextureTechnique(material)
        if description["type"] == "triangles":
            self.vertex_array_type = GL_TRIANGLES
        elif description["type"] == "quads":
            self.vertex_array_type = GL_QUADS
        else:
            self.vertex_array_type = GL_TRIANGLES

        vertices = description["vertices"]
        normals = description["normals"]
        uvs = description["texture_coordinates"]
        indices = description["indices"]
        weights = description["weights"]
        n_vertices = len(vertices)
        n_uvs = len(uvs)
        n_normals = len(normals)
        self.initialized = False
        print("loaded mesh", n_vertices, n_normals, n_uvs)
        if n_normals == n_vertices and n_uvs == n_vertices:
            data = list()
            for idx, i in enumerate(indices):
                v = vertices[idx]
                n = normals[idx]
                t = uvs[idx]
                bids = [-1,-1,-1,-1]
                bw = [0.0,0.0,0.0,0.0]
                if len(weights) > 0:
                    bids = weights[idx][0]
                    bw = weights[idx][1]

                entry = v + n + t + bids + bw
                data.append(entry)
            self.vertex_list = data
            self.num_vertices = len(self.vertex_list)
            self.vbo = vbo.VBO(np.array(self.vertex_list, 'f'))
            self.initialized = True

    def set_matrices(self, matrices):
        self.technique.set_matrices(matrices)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vbo, self.vertex_array_type, self.num_vertices)
        self.technique.stop()

    def scale(self, scale_factor):
        self.vertex_list = np.array(self.vertex_list)
        self.vertex_list[:,:3] *= scale_factor
        self.vbo = vbo.VBO(np.array(self.vertex_list, 'f'))


class AnimatedNormalMeshRenderer(object):
    def __init__(self, description):
        self.technique = NormalSkinningTextureTechnique()
        if description["type"] == "triangles":
            self.vertex_array_type = GL_TRIANGLES
        elif description["type"] == "quads":
            self.vertex_array_type = GL_QUADS
        else:
            self.vertex_array_type = GL_TRIANGLES

        vertices = description["vertices"]
        normals = description["normals"]
        indices = description["indices"]
        weights = description["weights"]
        n_vertices = len(vertices)
        n_normals = len(normals)
        self.initialized = False
        print("loaded mesh", n_vertices, n_normals)
        if n_normals == n_vertices:
            data = list()
            for idx, i in enumerate(indices):
                v = vertices[idx]
                n = normals[idx]
                bids = [-1, -1, -1, -1]
                bw = [0.0, 0.0, 0.0, 0.0]
                if len(weights) > 0:
                    bids = weights[idx][0]
                    bw = weights[idx][1]

                entry = v + n + bids + bw
                data.append(entry)
            self.vertex_list = data
            self.num_vertices = len(self.vertex_list)
            self.vbo = vbo.VBO(np.array(self.vertex_list, 'f'))
            self.initialized = True

    def set_matrices(self, matrices):
        self.technique.set_matrices(matrices)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        self.technique.prepare(modelMatrix, viewMatrix, projectionMatrix, lightSources)
        self.technique.use(self.vbo, self.vertex_array_type, self.num_vertices)
        self.technique.stop()

    def scale(self, scale_factor):
        self.vertex_list = np.array(self.vertex_list)
        self.vertex_list[:, :3] *= scale_factor
        self.vbo = vbo.VBO(np.array(self.vertex_list, 'f'))


