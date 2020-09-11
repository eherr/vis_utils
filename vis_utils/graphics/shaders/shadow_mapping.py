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
"""http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-16-shadow-mapping/#rendering-the-shadow-map
https://learnopengl.com/Advanced-Lighting/Shadows/Shadow-Mapping
"""
SHADOW_MAPPING_VS = """
#version 330 core

// Input vertex data, different for all executions of this shader.
in vec3 position;
in vec4 boneIDs;
in vec4 weights;

// Values that stay constant for the whole mesh.
uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projMatrix;
uniform int useSkinning;
uniform int boneCount;
const int MAX_BONES = 150;
uniform mat4 bones[MAX_BONES];

void main(){
if(!bool(useSkinning)){
    gl_Position =  projMatrix  * viewMatrix * modelMatrix * vec4(position,1);
 }else{
        vec4 tempPosition = vec4(0.0);
        for(int i = 0; i < 4; i++)
        {
            int id = int(boneIDs[i]);
            if(id >=  0 && boneIDs[i] < boneCount && weights[i] > 0.0)
            {
                mat4 boneMatrix = bones[id];
                tempPosition += boneMatrix * vec4(position, 1.0) * weights[i];
            }
        }
        gl_Position = projMatrix * viewMatrix * modelMatrix * tempPosition;
    }
}
"""



SHADOW_MAPPING_FS = """
#version 330 core
out vec4 FragColor;

void main()
{
    // gl_FragDepth = gl_FragCoord.z;
    int depthValue =  int(gl_FragCoord.z*255);
    //FragColor = vec4(gl_FragCoord.z,gl_FragCoord.z,gl_FragCoord.z,1)*255
     FragColor = vec4(vec3(depthValue), 1.0);
}
"""




SHADOW_SCREEN_VS ="""
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoords;

out vec2 TexCoords;

void main()
{
    TexCoords = aTexCoords;
    gl_Position = vec4(aPos, 1.0);
}
"""

SHADOW_SCREEN_FS = """
#version 330 core
out vec4 FragColor;

in vec2 TexCoords;

uniform sampler2D depthMap;

void main()
{
    float depthValue = texture(depthMap, TexCoords).r;
    FragColor = vec4(vec3(depthValue), 1.0);
    FragColor = texture(depthMap, TexCoords);
}
"""
