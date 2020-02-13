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
"""
sources:
http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/
http://ogldev.atspace.co.uk/www/tutorial38/tutorial38.html
http://ruh.li/AnimationVertexSkinning.html
http://www.lighthouse3d.com/tutorials/glsl-tutorial/texturing-with-images/
https://learnopengl.com/Advanced-Lighting/Shadows/Shadow-Mapping
fog https://www.youtube.com/watch?v=qslBNLeSPUc
"""


MAIN_VS = """
#version 330 core

in vec3 position;
in vec3 normal;
in vec2 uv;
in vec4 boneIDs;
in vec4 weights;

const int MAX_LIGHTS = 8;
const int MAX_BONES = 150;

struct LightSource{
    vec3 intensities;
    vec4 position;
    float attenuation;
    float ambientCoefficient;
    mat4 viewMatrix;
    mat4 projectionMatrix;
    sampler2D shadowMap;
};
uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;
uniform int useSkinning;
uniform int boneCount;
uniform mat4 bones[MAX_BONES];
uniform int lightCount;
uniform LightSource lights[MAX_LIGHTS];
uniform int useShadow;


out vec3 fragVert;
out vec3 fragNormal;
out vec2 fragUV;
out vec4 shadowCoord[MAX_LIGHTS];
out float fogFactor;

const float density = 0.0007;
const float gradient = 1.5;

void main()
{
    float distance = 0;
    if(!bool(useSkinning)){
       vec3 surfacePos = (modelMatrix * vec4(position,1.0)).xyz;
        vec4 relCameraPos = viewMatrix *  vec4(surfacePos,1.0);
       gl_Position = projectionMatrix * relCameraPos;
        if(bool(useShadow)){
            for(int i=0; i < lightCount; i++){
                shadowCoord[i] = lights[i].projectionMatrix* lights[i].viewMatrix * vec4(surfacePos, 1.0);
            }
        }
       mat4 normalMatrix = transpose(inverse(modelMatrix));
       fragNormal = (normalMatrix*vec4(normal,0.0)).xyz;
       distance = length(relCameraPos);
    }else{
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
        vec4 relCameraPos = viewMatrix * modelMatrix * tempPosition;
        gl_Position = projectionMatrix *relCameraPos;
        mat4 normalMatrix = transpose(inverse(modelMatrix));
        fragNormal = (normalMatrix* tempNormal).xyz;
        if(bool(useShadow)){
            for(int i=0; i < lightCount; i++){
                shadowCoord[i] = lights[i].projectionMatrix* lights[i].viewMatrix * tempPosition;
            }
        }

        distance = length(relCameraPos);
    }


   fragVert = position;
   fragUV = uv;
   fogFactor = exp(-pow((distance*density), gradient));

}"""

CALCSHADOW_STUB =""" 
float calculateShadow(sampler2D shadowMap, vec4 fragPosLightSpace, vec3 lightDir)
{
    return 0;
}
"""

CALCSHADOW_FUNC= """

float calculateShadow(sampler2D shadowMap, vec4 fragPosLightSpace, vec3 lightDir)
{
    // perform perspective divide
    vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
    // transform to [0,1] range
    projCoords = projCoords * 0.5 + 0.5;
    // get closest depth value from light's perspective (using [0,1] range fragPosLight as coords)
    float closestDepth = texture(shadowMap, projCoords.xy).r;
    // get depth of current fragment from light's perspective
    float currentDepth = projCoords.z;
    // calculate bias (based on depth map resolution and slope)
    vec3 normal = normalize(fragNormal);
    //vec3 lightDir = normalize(lightPos - fragVert);
    float bias = max(0.005 * (1.0 - dot(normal, lightDir)), 0.0005);//0.05 0.005
    //float bias = 0.0005;
    // check whether current frag pos is in shadow
    // float shadow = currentDepth - bias > closestDepth  ? 1.0 : 0.0;
    // PCF
    float shadow = 0.0;
    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
    for(int x = -1; x <= 1; ++x)
    {
        for(int y = -1; y <= 1; ++y)
        {
            float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize).r;
            shadow += currentDepth - bias > pcfDepth  ? 1.0 : 0.0;
        }
    }
    shadow /= 9.0;

    // keep the shadow at 0.0 when outside the far_plane region of the light's frustum.
    if(projCoords.z > 1.0)
        shadow = 0.0;

    return shadow;
}
"""

MAIN_FS =  """
#version 330 core



struct LightSource{
    vec3 intensities;
    vec4 position;
    float attenuation;
    float ambientCoefficient;
    mat4 viewMatrix;
    mat4 projectionMatrix;
    sampler2D shadowMap;
};


struct Material{
    vec3 ambient_color;
    vec3 diffuse_color;
    vec3 specular_color;
    float specular_shininess;
};

const int MAX_LIGHTS = 8;

uniform mat4 modelMatrix;
uniform int lightCount;
uniform LightSource lights[MAX_LIGHTS];
uniform Material material;
uniform sampler2D tex;
//uniform sampler2D shadowMap;
uniform vec3 viewerPos;
uniform int useTexture;
uniform int useShadow;
uniform vec3 skyColor;

in vec3 fragVert;
in vec3 fragNormal;
in vec2 fragUV;
in vec4 shadowCoord[MAX_LIGHTS];
in float fogFactor;

out vec4 color;

//insert function to calculate shadow
 %s

void main()
{

    vec3 surfacePos = vec3(modelMatrix * vec4(fragVert, 1));
    vec3 normalDir = normalize(fragNormal);
    vec3 eyeDir = normalize(viewerPos - surfacePos);
    vec3 ambient = material.ambient_color;
    vec4 surfaceColor = vec4(material.diffuse_color,1);
    if(bool(useTexture)){
        surfaceColor = texture( tex, fragUV ).rgba;
        ambient = material.ambient_color*surfaceColor.xyz;
    }
    vec3 diffuseSum = vec3(0);
    vec3 specularSum = vec3(0);
    float visibility = 1.0;
    for(int i = 0; i < lightCount; i++)
    {
        vec3 lightDir = vec3(0);
        if (lights[i].position.w == 0){//directional light
            lightDir = normalize(lights[i].position.xyz);
        }else{
            lightDir = normalize(lights[i].position.xyz - surfacePos);
        }
        if (bool(useShadow)){
            float shadow = calculateShadow(lights[i].shadowMap, shadowCoord[i], lightDir);
            //visibility = shadow ? 0.5 : 1.0;
            visibility = 1.0-shadow;
        }

        float diffuseBrightness = max(dot(lightDir,normalDir),0);
        diffuseBrightness = clamp(diffuseBrightness, 0, 1);
        vec3 diffuseLightColor = diffuseBrightness * lights[i].intensities;
        float specularCoefficient = 0;
        if (diffuseBrightness > 0.0){
            vec3 halfDir = normalize(eyeDir+lightDir)/2;
            specularCoefficient =  pow(max(dot(normalDir,halfDir),0), material.specular_shininess);
        }
         vec3 specularLightColor =  specularCoefficient*  lights[i].intensities;
        diffuseSum += visibility * diffuseLightColor;
        specularSum += visibility * specularLightColor;
    }
    //color = vec4( ambient+lightSum,1.0);
    diffuseSum = clamp(diffuseSum,0,1) * surfaceColor.rgb;
    specularSum = clamp(specularSum,0,1)* material.specular_color;
    color = vec4(ambient+clamp(diffuseSum+specularSum,0,1),1.0);
    color = mix(vec4(skyColor,1), color, fogFactor);
}"""

