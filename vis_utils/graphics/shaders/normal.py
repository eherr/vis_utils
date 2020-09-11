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
SKINNED_NORMAL_VS = """
#version 330

in vec3 position;
in vec3 normal;
in vec4 boneIDs;
in vec4 weights;


uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

const int MAX_BONES = 150;
uniform int boneCount;
uniform mat4 bones[MAX_BONES];

out vec3 fragNormal;

void main()
{
    vec4 tempPosition = vec4(0.0);
    vec4 tempNormal = vec4(0.0);
    for(int i = 0; i < 4; i++)
    {
        int id = int(boneIDs[i]);
        if(id >=  0 && boneIDs[i] < boneCount && weights[i] > 0.0)
        {
            mat4 boneMatrix = bones[id];
            tempPosition += boneMatrix * vec4(position, 1.0) * weights[i];
            tempNormal +=  boneMatrix * vec4(normal, 0.0) * weights[i];
        }
    }
    vec3 fragVert = vec3(tempPosition.xyz);
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(tempPosition.xyz,1.0);
    mat4 normalMatrix = transpose(inverse(modelMatrix));
    fragNormal = (normalMatrix* tempNormal).xyz;

}"""

NORMAL_FS = """#version 330

in vec3 fragNormal;

out vec4 color;

void main()
{
    color = vec4(fragNormal.xyz, 1.0);
}
"""
