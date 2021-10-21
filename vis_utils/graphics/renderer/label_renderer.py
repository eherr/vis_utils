import numpy as np
from .text_renderer import TextRenderer
from OpenGL.GLU.projection import gluProject
from OpenGL.GL import glGetIntegerv, GL_VIEWPORT


class LabelRenderer:
    def __init__(self, scale=0.6, z=-10,max_label_length=5):
        self.text_renderer = TextRenderer()
        self.scale = scale
        self.z = z
        self.max_label_length = max_label_length

    def render_scene(self, object_list, view_matrix, projection_matrix,  orthographic_matrix, graphics_context):
        projection_matrix = np.array(projection_matrix, np.double)
        viewport = glGetIntegerv(GL_VIEWPORT)
        orthographic_matrix = np.array(orthographic_matrix, np.double)
        view_matrix = np.array(view_matrix, np.double)
        
        for o in object_list:
            if "animation_controller" in o._components:
                c = o._components["animation_controller"]
                if hasattr(c, "get_labeled_points"):
                    labels, points = c.get_labeled_points()
                    for i, l in enumerate(labels):
                        pos = points[i]
                        wx, wy, _ = gluProject(pos[0], pos[1], pos[2], view_matrix, projection_matrix, viewport)
                        wy = graphics_context.height - wy
                        self.draw(orthographic_matrix, (wx, wy), l[:self.max_label_length])

    def draw(self, orthographic_matrix, pos_2d, line):
        self.text_renderer.draw(orthographic_matrix, pos_2d, self.z, line, self.scale)
