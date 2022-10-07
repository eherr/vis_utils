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
import os
import json
import numpy as np
from PySignal import Signal
import vis_utils.constants as constants
from ..graphics.materials import TextureMaterial, HeightMapMaterial
from ..graphics.texture import Texture
from ..graphics.constants import SHADOW_MAP_WIDTH, SHADOW_MAP_HEIGHT, SHADOW_BOX_LENGTH
from ..graphics.light.directional_light import DirectionalLight
from ..animation.point_cloud_animation_controller import PointCloudAnimationController
from ..animation.group_animation_controller import GroupAnimationController
from anim_utils.animation_data import BVHReader, MotionVector, SkeletonBuilder
from .scene_object import SceneObject
from .legacy import ConstraintObject, CoordinateSystemObject
from .scene import Scene
from .components import StaticMesh, GeometryDataComponent, TerrainComponent, LightComponent
from ..graphics import materials
from ..graphics.renderer import splines
from ..graphics.renderer.primitive_shapes import generate_height_data
from ..graphics.geometry.mesh import Mesh
from ..scene.utils import get_random_color
from .scene_object_builder import SceneObjectBuilder, DEFAULT_DENSITY
from .scene_edit_widget import SceneEditWidget


def load_json_file(file_path):
    if os.path.isfile(file_path):
        with open(file_path, "r") as in_file:
            return json.load(in_file)


class EditorScene(Scene):
    """class for scenes that are supposed to be visualized """

    def __init__(self, visualize=True, sim=None, **kwargs):
        Scene.__init__(self, visualize, sim)
        self.added_scene_object = Signal()
        self.updated_animation_frame = Signal()
        self.reached_end_of_animation = Signal()
        self.deleted_scene_object = Signal()
        self.update_scene_object = Signal()
        self.create_ground = kwargs.get("create_ground", True)
        if self.visualize:
            self._create_visual_reference_frame()
            if constants.activate_simulation:
                self.contact_renderer = self.object_builder.create_object("contact_renderer",0.5, [0, 5, 0])
                self.addObject(self.contact_renderer)
            self.scene_edit_widget = SceneEditWidget()
        else:
            self.ground = None
            self.scene_edit_widget = None
        self.enable_scene_edit_widget = False

    def toggle_scene_edit_widget(self):
        self.enable_scene_edit_widget = not self.enable_scene_edit_widget
        if self.selected_scene_object is not None and self.selected_scene_object != self.ground:
            self.scene_edit_widget.visible = self.enable_scene_edit_widget

    def _create_visual_reference_frame(self, scale=1):
        self.add_directional_light(scale)
        self.addObject(CoordinateSystemObject(10))
        if not self.create_ground:
            return
        self.ground = SceneObject()
        self.ground.clickable = False
        diffuse_texture = Texture()
        diffuse_texture.make_chessboard()
        material = TextureMaterial(diffuse_texture)
        geom = Mesh.build_plane(10000, 10000, 8, 100, material)
        self.ground._components["geometry"] = GeometryDataComponent(self.ground, geom)
        self.addObject(self.ground)

    def add_directional_light(self, scale):
        o = SceneObject()
        origin = np.array([0.0, 0.0, 0.0])
        intensities = np.array([1, 1, 1])
        pos = np.array([20 * scale, 100 * scale, 10 * scale])
        w = SHADOW_MAP_WIDTH
        h = SHADOW_MAP_HEIGHT
        shadow_box_length = SHADOW_BOX_LENGTH
        l = DirectionalLight(pos, origin, np.array([0.0, 1.0, 0.0]), intensities, w, h, scene_scale=scale,shadow_box_length=shadow_box_length)
        o._components["light"] = LightComponent(o, l)
        self.addObject(o)

    def addObject(self, sceneObject, parentId=None):
        sceneId = Scene.addObject(self, sceneObject, parentId)
        sceneObject.scene = self
        self.added_scene_object.emit(sceneId)
        return sceneId

    def update_and_draw(self, viewMatrix, projectionMatrix, dt):
        Scene.update_and_draw(self, viewMatrix, projectionMatrix, dt)

    def addAnimationController(self, scene_object, key):
        self.register_animation_controller(scene_object, key)
        self.addObject(scene_object)

    def register_animation_controller(self, scene_object, key):
        scene_object._components[key].updated_animation_frame.connect(self.slotUpdateAnimationFrameRelay)
        scene_object._components[key].reached_end_of_animation.connect(self.slotEndOfAnimationFrameRelay)
        if hasattr(scene_object._components[key], "update_scene_object"):
            scene_object._components[key].update_scene_object.connect(self.slotUpdateSceneObjectRelay)


    def slotUpdateAnimationFrameRelay(self, frameNumber):
        self.updated_animation_frame.emit(frameNumber)

    def slotEndOfAnimationFrameRelay(self, loop):
        self.reached_end_of_animation.emit(0, loop)

    def slotUpdateSceneObjectRelay(self, node_id):
        self.update_scene_object.emit(node_id)

    def loadUnityConstraintsFile(self, file_path):
        self.object_builder.create_object_from_file("unity_constraints",file_path)

    def loadAnimatedMesh(self,  rig_path):
        scene_object = self.object_builder.create_object_from_file("rig",rig_path)
        self.addAnimationController(scene_object, "animation_controller")


    def getSplineObjects(self):
        for sceneObject in self.object_list:
            if isinstance(sceneObject, ConstraintObject):
                yield sceneObject

    def addSphere(self, name, position, radius=1.0, material=materials.blue, simulate=False, kinematic=True):
        #return self.object_builder.create_sphere_object(name, position, [1,0,0,0], radius, material, simulate, kinematic)
        return self.object_builder.create_object("sphere", name, position, [1, 0, 0, 0], radius, material, simulate, kinematic)

    def createGroupAnimationController(self, node_ids):
        anim_controllers = self.get_animation_controllers(node_ids)
        if len(anim_controllers) > 0:
            scene_object = SceneObject()
            group_animation_controller = GroupAnimationController(scene_object)
            for anim_controller in anim_controllers:
                group_animation_controller.add_animation_controller(anim_controller)
            scene_object.name = "Animation Group " + str(scene_object.node_id)
            scene_object.add_component("group_player", group_animation_controller)
            self.addAnimationController(scene_object, "group_player")

    def addArticulatedBody(self, node_id):
        scene_object = self.getSceneNode(node_id)
        if "static_mesh" in list(scene_object._components.keys()):
            self.object_builder.create_component("articulated_body", scene_object)

    def addSplineObject(self, name, points, color, granularity):
        scene_object = SceneObject()
        scene_object.name = name
        scene_object.visualization = splines.CatmullRomSplineRenderer(points, color[0], color[1], color[2], granularity)
        self.addObject(scene_object)
        return scene_object

    def removeObject(self, node_id):
        Scene.removeObject(self, node_id)
        self.deleted_scene_object.emit(node_id)

    def get_animation_controllers(self, node_ids):
        anim_objects = [self.getSceneNode(node_id) for node_id in node_ids]
        anim_controllers = []
        for anim_object in anim_objects:
            if "animation_controller" in list(anim_object._components.keys()):
                anim_controller = anim_object._components["animation_controller"]
                anim_controllers.append(anim_controller)
        return anim_controllers

    def runPythonScript(self, filename):
        with open(filename, "r") as script_file:
            lines = script_file.read()
            #globals = globals()locals(), globals()
            context = dict()
            context["scene"] = self
            exec(lines, context)

    def select_object(self, scene_id, ray=None):
        self.selected_scene_object = self.getObject(scene_id)
        if self.selected_scene_object is not None and not self.selected_scene_object.clickable:
            self.selected_scene_object = None

        if self.scene_edit_widget is not None:
            if self.selected_scene_object is not None and self.selected_scene_object != self.ground:
                self.scene_edit_widget.activate(self.selected_scene_object, self.enable_scene_edit_widget)
            else:
                if not self.scene_edit_widget.activate_axis(scene_id, ray):
                    self.scene_edit_widget.deactivate()
                elif self.scene_edit_widget.visible:
                    self.selected_scene_object = self.scene_edit_widget.scene_object
        return self.selected_scene_object

    def update(self, dt):
        super().update(dt)
        self.scene_edit_widget.update(dt)

    def deactivate_axis(self):
        if self.scene_edit_widget is not None:
            self.scene_edit_widget.deactivate_axis()

    def handle_mouse_movement(self, cam_pos, cam_ray):
        if self.scene_edit_widget is not None:
            self.scene_edit_widget.move(cam_pos, cam_ray)
