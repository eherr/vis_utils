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
from copy import deepcopy
import numpy as np
from ...graphics.geometry.mesh import Mesh
from .component_base import ComponentBase
from ...graphics import materials
from ...graphics import renderer
from ...graphics.material_manager import MaterialManager

SKELETON_NODE_TYPE_ROOT = 0
SKELETON_NODE_TYPE_JOINT = 1
SKELETON_NODE_TYPE_END_SITE = 2
MAX_BONES = 150



RENDER_MODE_NONE = 0
RENDER_MODE_STANDARD = 1
RENDER_MODE_NORMAL_MAP = 2
RENDER_MODES = [RENDER_MODE_NONE, RENDER_MODE_STANDARD, RENDER_MODE_NORMAL_MAP]


class AnimatedMeshComponent(ComponentBase):
    def __init__(self, scene_object, mesh_list, skeleton_def, animation_source="animation_controller", scale=1):
        ComponentBase.__init__(self, scene_object)
        self._scene_object = scene_object
        self.anim_controller = scene_object._components[animation_source]
        self.render_mode = RENDER_MODE_STANDARD
        self.meshes = []

        material_manager = MaterialManager()

        for m_desc in mesh_list:
            geom = None
            if "material" in m_desc and "Kd" in list(m_desc["material"].keys()):
                texture_name = m_desc["texture"]
                if texture_name is not None and texture_name.endswith(b'Hair_texture_big.png'):
                    continue
                material = material_manager.get(m_desc["texture"])
                if material is None:
                    material = materials.TextureMaterial.from_image(m_desc["material"])
                    material_manager.set(m_desc["texture"], material)
                print("reuse material", m_desc["texture"])
                geom = Mesh.build_legacy_animated_mesh(m_desc, material)
            else:
                geom = Mesh.build_from_desc(m_desc, materials.red)
            if geom is not None:
                self.meshes.append(geom)
        self.inv_bind_poses = []
        for idx, name in enumerate(skeleton_def["animated_joints"]):
             inv_bind_pose = skeleton_def["nodes"][name]["inv_bind_pose"]
             self.inv_bind_poses.append(inv_bind_pose)
        self.vertex_weight_info = [] # store for each vertex a list of tuples with bone id and weights
        for idx, m in enumerate(mesh_list):
            self.vertex_weight_info.append(mesh_list[idx]["weights"])
        self.scale_mesh(scale)
        print("number of matrices", len(self.inv_bind_poses))

    def update(self, dt):
        return

    def get_bone_matrices(self):
        matrices = self.anim_controller.get_bone_matrices()
        bone_matrices = []
        for idx in range(len(self.inv_bind_poses)):
            m = np.dot(matrices[idx], self.inv_bind_poses[idx])
            bone_matrices.append(m)
        return np.array(bone_matrices)

    def scale_mesh(self, scale_factor):
        for m in self.meshes:
            m.scale(scale_factor)
        for idx, m in enumerate(self.inv_bind_poses):
            self.inv_bind_poses[idx][:3, 3] *= scale_factor

