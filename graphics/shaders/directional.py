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
#http://www.lighthouse3d.com/tutorials/glsl-core-tutorial/directional-lights-per-pixel/
#http://en.wikibooks.org/wiki/GLSL_Programming/GLUT/Smooth_Specular_Highlights

DIR_VS ="""
#version 330
in vec3 vertex;
in vec3 vertex_normal;

uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

uniform vec3 viewerPos;

out vec3 fragVert;
out vec3 vertexNormal;
out vec3 eyeDir;


void main(void)
{
    mat4 normalMatrix = transpose(inverse(modelMatrix));
    vertexNormal = (normalMatrix * vec4(vertex_normal, 0.0)).xyz;

    vec3 vertexWorldSpace = (viewMatrix * modelMatrix * vec4(vertex, 1.0)).xyz;
    eyeDir = -normalize(vertexWorldSpace.xyz - viewerPos);
    vec4 tempPosition = projectionMatrix * vec4(vertexWorldSpace, 1.0); // projectionMatrix*viewMatrix* modelMatrix * vec4( vertex, 1.0 );
    gl_Position = tempPosition;
    fragVert = vec3(tempPosition.xyz);
}

"""

DIR_FS = """
#version 330
struct LightSource{
    vec3 intensities;
    vec4 position;
    float attenuation;
    float ambientCoefficient;
};


struct Material{
    vec3 ambient_color;
    vec3 diffuse_color;
    vec3 specular_color;
    float specular_shininess;
};

uniform mat4 modelMatrix;
uniform LightSource light;
uniform Material material;

in vec3 fragVert;
in vec3 vertexNormal;
in vec3 eyeDir;

out vec4 color;

void main (void)
{
    vec3 surfacePos = vec3(modelMatrix * vec4(fragVert, 1));
    vec3 E = normalize(eyeDir);
    vec3 N = normalize(vertexNormal);

    vec3 L = vec3(0);
    if (light.position.w == 0){//directional light
        L = normalize(light.position.xyz);
    }else{
        L = normalize(light.position.xyz - surfacePos);
    }


    vec3 specular = vec3(0);
    vec3 ambient = material.ambient_color * light.intensities;
    float brightness = max(dot(L,N),0);
    brightness = clamp(brightness, 0, 1);

    vec3 diffuse = light.intensities * brightness * material.diffuse_color;
    float specularCoefficient = 0;
    if (brightness > 0.0){
        vec3 H = normalize(E+L);
        specularCoefficient= pow(max(dot(N,H),0),material.specular_shininess );
    }
    specular = specularCoefficient* material.specular_color * light.intensities;
    color = vec4( ambient+diffuse+specular,1.0);

}
"""

