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


class RootSceneNode(object):
    def __init__(self, parentNode=None):
        self.scene = None
        self.is_root = True
        self.children = []

    def addChildNode(self, node):
        self.children.append(node)

    def removeChildNode(self, node_id):
        for node in self.children:
            if node.node_id == node_id:
                node.cleanup()
                self.children.remove(node)
            else:
                node.removeChildNode(node_id)

    def getSceneNode(self, node_id):
        #print "search for", node_id,"in",self.node_id,self.children
        for c in self.children:
            if c.node_id == node_id:
                return c
            else:
                temp = c.getSceneNode(node_id)
                if temp is not None:
                    return temp
        return None

    def getChildren(self):
        children = self.children
        for c in self.children:
            children += c.getChildren()
        return children

    def get_scene_node_by_name(self, node_name):
        #print "search for", node_id,"in",self.node_id,self.children
        for c in self.children:
            if c.name == node_name:
                return c
            else:
                temp = c.get_scene_node_by_name(node_name)
                if temp is not None:
                    return temp
        return None

class SceneGraph(object):
    """class that holds list of objects to be drawn and interacted with
    """
    def __init__(self):
        self.rootNode = RootSceneNode()

    def objectList(self):
        return self.rootNode.getChildren()

    def addObject(self, sceneObject, parentId=None):
        sceneObject.scene = self
        if parentId is not None:
            parentNode = self.getSceneNode(parentId)
        else:
            parentNode = self.rootNode
        sceneObject.parentNode = parentNode
        parentNode.children.append(sceneObject)

    def getSceneNode(self, node_id):
        return self.rootNode.getSceneNode(node_id)

    def getObject(self, node_id):
        return self.rootNode.getSceneNode(node_id)

    def removeObject(self, node_id):
        self.rootNode.removeChildNode(node_id)

    def get_scene_node_by_name(self, node_name):
        return self.rootNode.get_scene_node_by_name(node_name)
