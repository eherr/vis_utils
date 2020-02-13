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


TEXTURE_VS = """
#version 130
//src: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/

in vec3 position;
in vec2 vertexUV;
uniform mat4 MVP;

out vec2 UV;

void main()
{
    gl_Position = MVP*vec4(position, 1.0);
    UV = vertexUV;
}
"""


TEXTURE_FS = """#version 130
//src: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/

in vec2 UV;

out vec4 color;

// Values that stay constant for the whole mesh.
 uniform sampler2D tex;

void main()
{
    //color = vec4(texture2D( tex, UV ).rgb);
    color = vec4(texture( tex, UV ).rgba);
}
"""



TERRAIN_VS = """
//src: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/

in vec3 position;
in vec2 vertexUV;
in vec2 heightMapUV;
uniform mat4 MVP;
uniform sampler2D height_map;
uniform float heightMapScale;
out vec2 UV;
out float height;

float rand(float n){return fract(sin(n) * 43758.5453123);}

float noise(float p){
	float fl = floor(p);
  float fc = fract(p);
	return mix(rand(fl), rand(fl + 1.0), fc);
}

void main()
{
    vec2 uv = vec2(noise(vertexUV.x),noise(vertexUV.y))*0.1;
    height =vertexUV.x;
    height = texture2D(height_map, heightMapUV).r*heightMapScale;
    //height += (uv.x+uv.y)*100;
    vec4 t_position = vec4(position.x, height, position.z, 1.0);
    gl_Position = MVP*t_position;
    UV = vertexUV;
}
"""

TERRAIN_FS = """
//src: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/

in vec2 UV;
in float height;


// Values that stay constant for the whole mesh.
 uniform sampler2D tex;

void main()
{
    //color = vec4(texture2D( tex, UV ).rgb);
    vec4 t_color = vec4(texture( tex, UV ).rgba);
    //height *= 0.01;
    //gl_FragColor = vec4(height, height, height, t_color.a);
    gl_FragColor = t_color;
}
"""




SHADED_TEXTURE_VS = """
#version 140
//src: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/

in vec3 position;
in vec3 normal;
in vec2 vertexUV;


uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;


out vec3 fragVert;
out vec3 fragNormal;
out vec2 fragUV;

void main()
{
   vec3 surfacePos = (modelMatrix *vec4(position,1.0)).xyz;
   gl_Position= projectionMatrix * viewMatrix *  vec4(surfacePos,1.0);

   mat4 normalMatrix = transpose(inverse(modelMatrix));
   fragNormal = (normalMatrix*vec4(normal,0.0)).xyz;

   fragVert = position;
   fragUV = vertexUV;

}"""

SKINNED_SHADED_TEXTURE_VS = """
#version 330

in vec3 position;
in vec3 normal;
in vec2 vertexUV;
in vec4 boneIDs;
in vec4 weights;


uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

const int MAX_BONES = 150;
uniform vec3 viewerPos;
uniform int boneCount;
uniform mat4 bones[MAX_BONES];

out vec3 fragVert;
out vec3 fragNormal;
out vec2 fragUV;

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
    fragVert = vec3(tempPosition.xyz);
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(tempPosition.xyz,1.0);
    mat4 normalMatrix = transpose(inverse(modelMatrix));
    fragNormal = (normalMatrix* tempNormal).xyz;
    fragUV = vertexUV;

}"""




SHADED_TEXTURE_FS = """
#version 330
//src: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/
//src: http://ogldev.atspace.co.uk/www/tutorial38/tutorial38.html
//src http://ruh.li/AnimationVertexSkinning.html
//http://www.lighthouse3d.com/tutorials/glsl-tutorial/texturing-with-images/

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
uniform sampler2D tex;
uniform vec3 viewerPos;

in vec3 fragVert;
in vec3 fragNormal;
in vec2 fragUV;

out vec4 color;

void main()
{

    vec3 surfacePos = vec3(modelMatrix * vec4(fragVert, 1));
    vec3 N = normalize(fragNormal);
    vec3 E = normalize(viewerPos - surfacePos);

    vec3 L = vec3(0);
    if (light.position.w == 0){//directional light
        L = normalize(light.position.xyz);
    }else{
        L = normalize(light.position.xyz - surfacePos);
    }

    vec4 surfaceColor = texture( tex, fragUV ).rgba;

    vec3 ambient = material.ambient_color*surfaceColor.xyz;

    float diffuseCoefficient = max(dot(L,N),0);
    diffuseCoefficient = clamp(diffuseCoefficient, 0, 1);

    vec3 diffuse = diffuseCoefficient * surfaceColor.rgb * light.intensities;
    float specularCoefficient = 0;
    if (diffuseCoefficient > 0.0){
        vec3 H = normalize(E+L)/2;
        specularCoefficient =  pow(max(dot(N,H),0), material.specular_shininess);
    }
    vec3 specular = specularCoefficient * material.specular_color;

    color = vec4(max(diffuse+specular, ambient), surfaceColor.a);
}"""

