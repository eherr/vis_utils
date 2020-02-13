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
# -*- coding: utf-8 -*-
from .task_manager import TaskManager, FuncCallTask
import vis_utils.constants as constants
import collections
from .scene_graph import SceneGraph
from .scene_object_builder import SceneObjectBuilder
import numpy as np
from .components.scene_rest_interface import SceneRESTInterface
from .components.terrain_component import TerrainComponent
from .scene_object import SceneObject
from threading import Lock


class Scene(SceneGraph):
    """class that keeps and uodates a list of objects 
    """
    def __init__(self, visualize=True, sim=None):
        super().__init__()
        self.visualize = visualize
        self.object_list = []
        self.lightSources = []
        self.selected_scene_object = None
        self.sim = sim
        self.mutex = Lock()
        self.task_manager = TaskManager()
        self.draw_task_manager = TaskManager()
        self.sim_task_manager = TaskManager()
        self.global_vars = collections.OrderedDict()
        self.internal_vars = collections.OrderedDict()
        self.height = 0
        self.has_height_map = False
        self.lightSources = []
        self.ground = None
        self.object_builder = SceneObjectBuilder()
        self.object_builder.set_scene(self)

    def objectList(self):
        return self.rootNode.getChildren()

    def get_visible_objects(self, camera):
        bb = camera.get_frustrum_bounding_box()
        v_m = camera.get_view_matrix().T
        _p = np.zeros(4)
        objects = []
        for o in self.object_list:
            if self.ground is not None and o.node_id == self.ground.node_id:
                objects.append(o)
            elif o.visible:
                p = o.getPosition()
                _p[0] = p[0]
                _p[1] = p[1]
                _p[2] = p[2]
                _p[3] = 1
                _p = np.dot(v_m, _p)
                if bb.inside(_p[:3]):
                    objects.append(o)
        return objects

    def addObject(self, sceneObject, parentId=None):
        super().addObject(sceneObject, parentId)
        self.object_list.append(sceneObject)
        return sceneObject.node_id

    def sim_update(self, dt):
        if self.sim is None:
            return
        self.mutex.acquire()
        self.sim_task_manager.update(dt)
        self.sim.update(dt)
        for sceneObject in self.object_list:
            if sceneObject.visible:
                sceneObject.sim_update(dt)
        self.mutex.release()

    def before_update(self, dt):
        for sceneObject in self.object_list:
            if sceneObject.visible:
                sceneObject.before_update(dt)

    def get_light_sources(self):
        light_sources = []
        for o in self.object_list:
            if o.has_component("light"):
                light_sources.append(o._components["light"].light)
        return light_sources

    def update(self, dt):
        self.lightSources = self.get_light_sources()
        self.task_manager.update(dt)
        if self.sim is not None:
            self.sim.update_contacts()
        for sceneObject in self.object_list:
            if sceneObject.visible:
                sceneObject.update(dt)

    def after_update(self, dt):
        for sceneObject in self.object_list:
            if sceneObject.visible:
                sceneObject.after_update(dt)

    def draw(self, viewMatrix, projectionMatrix):
        self.draw_task_manager.update(0.0)
        for sceneObject in self.object_list:
            if sceneObject.visible:
                sceneObject.draw(viewMatrix,projectionMatrix,self.lightSources)
            
    def update_and_draw(self, viewMatrix, projectionMatrix,dt):
        for sceneObject in self.object_list:
            sceneObject.update_and_draw(viewMatrix, projectionMatrix, self.lightSources,dt)
            #print(str(object.getId()))
          
    def drawDebugVisualization(self, viewMatrix, projectionMatrix):
         for sceneObject in self.object_list:
             sceneObject.drawDebugVisualization(viewMatrix,projectionMatrix,self.lightSources)

    def select_object(self, sceneId):
        self.selected_scene_object = self.getObject(sceneId)
        return self.selected_scene_object

    def getSelectedObject(self):
        return self.selected_scene_object
    
    def removeObject(self, node_id):
        print("before", len(self.object_list))
        for sceneObject in self.object_list:
            if sceneObject.node_id == node_id:
                self.object_list.remove(sceneObject)
        print("after", len(self.object_list))
        super().removeObject(node_id)

    def showSceneObject(self, node_id):
        sceneObject = self.getObject(node_id)
        if sceneObject is not None:
            sceneObject.visible = True

    def hideSceneObject(self, node_id):
        sceneObject = self.getObject(node_id)
        if sceneObject is not None:
            sceneObject.visible = False

    def toggle_simulation(self):
        self.sim.toggle_simulation()

    def save_simulation_state(self):
        self.sim.save_state()

    def restore_simulation_state(self):
        self.sim.restore_state()

    def hide_all_objects(self):
        for sceneObject in self.object_list:
            if sceneObject.node_id > 4:
                sceneObject.hide()

    def toggle_visibility(self, node_ids):
        for node_id in node_ids:
            sceneObject = self.getObject(node_id)
            if sceneObject is not None:
                sceneObject.visible = not sceneObject.visible

    def delete_objects(self, node_ids):
        for node_id in node_ids:
            sceneObject = self.getObject(node_id)
            if sceneObject is not None:
                self.removeObject(node_id)

    def get_selected_objects(self):
        return [self.selected_scene_object]

    def get_height(self, x, z):
        if self.ground is not None and self.ground.has_component("terrain"):
            terrain = self.ground._components["terrain"]
            p = self.ground.getPosition()
            center_x = p[0]
            center_z = p[2]
            rel_x, rel_z = terrain.to_relative_coordinates(center_x, center_z, x, z)
            height = terrain.get_height(rel_x, rel_z)
            #print("get height at point", x, z, rel_x, rel_z, height)
            return height
        else:
            return self.height

    def schedule_func_call(self, func_name, func, params):
        task = FuncCallTask(func_name, func, params, self, self.task_manager)
        self.task_manager.add(func_name, task)

def create_scene_rest_interface(builder, port):
    scene_object = SceneObject()
    builder._scene.addObject(scene_object)
    scene_rest_interface = SceneRESTInterface(scene_object, port)
    scene_object.add_component("scene_rest_interface", scene_rest_interface)
    return scene_object



def create_terrain(builder, width, depth, height_map_image, height_map_scale):
    print("create terrain", width, depth, height_map_scale)
    scene = builder._scene
    if scene.ground is None:
        scene.ground = SceneObject()
        scene.addObject(scene.ground)    
    if scene.ground.has_component("terrain"):
        del scene.ground._components["terrain"]

    terrain = TerrainComponent(scene.ground, width, depth, None, height_map_image, height_map_scale)
    scene.ground.add_component("terrain", terrain)

    return scene.ground


SceneObjectBuilder.register_object("terrain", create_terrain)
SceneObjectBuilder.register_object("scene_rest_interface", create_scene_rest_interface)