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
from ...graphics.geometry.mesh import Mesh
from .component_base import ComponentBase
from ...graphics import materials
from ...graphics.material_manager import MaterialManager


class StaticMesh(ComponentBase):
    def __init__(self, scene_object, position, mesh_list):
        ComponentBase.__init__(self, scene_object)
        self._scene_object = scene_object
        self.meshes = []
        material_manager = MaterialManager()
        for m_desc in mesh_list:
            print("add mesh",m_desc.keys())
            print()
            n_normals = len(m_desc["normals"])
            n_vertices = len(m_desc["vertices"])
            if n_normals != n_vertices:
                print("error vertices and normals do are not the same count",n_vertices, n_normals)
                continue

            if "material" in m_desc and "Kd" in list(m_desc["material"].keys()):
                material = material_manager.get(m_desc["texture"])
                if material is None:
                    material = materials.TextureMaterial.from_image(m_desc["material"])
                    material_manager.set(m_desc["texture"], material)
                texture_name = m_desc["texture"]
                print("reuse material", texture_name)
                if not texture_name.endswith(b'Hair_texture_big.png'):
                    geom = Mesh.build_from_desc(m_desc, material)
                    self.meshes.append(geom)
            else:
                print("create untextured mesh")
                geom = Mesh.build_from_desc(m_desc)
                self.meshes.append(geom)

    def draw(self, modelMatrix, viewMatrix, projectionMatrix, lightSources):
        return
        for m in self.meshes:
            m.draw(modelMatrix, viewMatrix, projectionMatrix, lightSources)
