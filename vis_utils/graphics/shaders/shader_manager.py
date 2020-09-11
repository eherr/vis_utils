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
import sys
from OpenGL.GL import *
from OpenGL.GL import shaders
from vis_utils import constants
from .color import *
from .directional import *
from .texture import *
from .normal import *
from .screen import *
from .skinning import *
from .color_picking import *
from .main_shader import *
from .shadow_mapping import *
from .outline import *


SHADER_PROGRAMS = dict()
SHADER_PROGRAMS["color"] = (COLOR_VS, COLOR_FS)
SHADER_PROGRAMS["direction"] = (DIR_VS, DIR_FS)
SHADER_PROGRAMS["texture"] = (TEXTURE_VS, TEXTURE_FS)
SHADER_PROGRAMS["color_skinning"] = (SKINNING_COLOR_VS, SKINNING_COLOR_FS)
SHADER_PROGRAMS["screen"] = (SCREEN_VS, SCREEN_FS)
SHADER_PROGRAMS["color_picking"] = (COLOR_PICKING_VS, COLOR_PICKING_FS)
if constants.activate_shadows:
    SHADER_PROGRAMS["main"] = (MAIN_VS, MAIN_FS % CALCSHADOW_FUNC)
else:
    SHADER_PROGRAMS["main"] = (MAIN_VS, MAIN_FS % CALCSHADOW_STUB)
SHADER_PROGRAMS["shadow_mapping"] = (SHADOW_MAPPING_VS, SHADOW_MAPPING_FS)
SHADER_PROGRAMS["shadow_screen"] = (SHADOW_SCREEN_VS, SHADOW_SCREEN_FS)
SHADER_PROGRAMS["outline"] = (OUTLINE_VS, OUTLINE_FS)

class ShaderManager(object):
     contextShaderMap = dict()
     def __init__(self):
         return

     def initShaderMap(self):
         for key, shader_program in SHADER_PROGRAMS.items():
             try:
                 v = shaders.compileShader(shader_program[0], GL_VERTEX_SHADER)
                 f = shaders.compileShader(shader_program[1], GL_FRAGMENT_SHADER)
                 shader_program = shaders.compileProgram(v, f)
                 self.__class__.contextShaderMap[key] = shader_program
             except:
                 print("Compiling shader program "+key+" crashed with error: ", sys.exc_info()[0], sys.exc_info()[1])

     def getShader(self, key):
         if key in self.__class__.contextShaderMap:
             return self.__class__.contextShaderMap[key]
         else:
             return None
