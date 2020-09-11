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
#skinning shader from http://mmmovania.blogspot.de/2012/11/skeletal-animation-and-gpu-skinning.html
SKINNING_VS = """
#version 330

in vec3 vertex;
in vec3 vertex_normal;
in ivec4 BoneIDs;
in vec4 Weights;

const int MAX_BONES = 150;
uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;
uniform vec3 viewerPos;
uniform mat4 Bones[MAX_BONES];

out vec3 vertexNormal;
out vec3 eyeDir;


void main() {
    vec4 tempVertex = vec4(0.0);
    vec4 tempNormal = vec4(0.0,0.0,0.0,0.0);
    for(int i = 0; i < 4; i++)
	 {
		if(BoneIDs[i] < MAX_BONES && Weights[i] > 0.0)
        {
			mat4 boneMatrix = Bones[BoneIDs[i]];
			float w = Weights[i];
            tempVertex += boneMatrix * vec4(vertex, 1.0) * w;
            tempNormal += boneMatrix * vec4(vertex_normal, 0.0) * w;


		}
	 }
	vertexNormal = normalize(tempNormal).xyz;
	vec3 vertexWorldSpace = (modelMatrix *  vec4(tempVertex.xyz,1.0) ).xyz;

    eyeDir = normalize(viewerPos - vertexWorldSpace.xyz);
    gl_Position = projectionMatrix * viewMatrix * vec4(vertexWorldSpace,1.0);


    mat4 normalMatrix = transpose(inverse(modelMatrix));
    vertexNormal = (normalMatrix * vec4(tempNormal.xyz,0.0) ).xyz;

    //vertexNormal = normalize(BoneIDs[0] + (Weights[0] +vertexNormal*0.0000001)).xyz;

}"""



SKINNING_COLOR_VS = """
#version 330

in  vec3 position;
in vec4 BoneIDs;
in vec4 Weights;


uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;
const int MAX_BONES = 150;

uniform int gBoneCount;
uniform vec4 color;
uniform mat4 gBones[MAX_BONES];

out vec4 theColor;

void main()
{
  vec4 tempPosition = vec4(0.0, 0.0, 0.0, 0.0);
    for(int i = 0; i < 4; i++)
     {
        int id = int(BoneIDs[i]);
        if(id >= 0 && id < gBoneCount && Weights[i] > 0.0)
        {

            mat4 boneMatrix = gBones[id];
            tempPosition += boneMatrix*vec4(position, 1.0) * Weights[i];
        }
     }
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(tempPosition.xyz,1.0);
    theColor = color;
}
"""

SKINNING_COLOR_FS = """
#version 330
in vec4 theColor;
out vec4 outColor;

void main()
{
    outColor = theColor;
}
 """
