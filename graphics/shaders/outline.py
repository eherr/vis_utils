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
#src: http://codeflow.org/entries/2012/aug/02/easy-wireframe-display-with-barycentric-coordinates/
#http://blogs.love2d.org/content/let-it-glow-dynamically-adding-outlines-characters
#https://gist.github.com/xoppa/33589b7d5805205f8f08
#https://github.com/Shrimpey/Outlined-Diffuse-Shader-Fixed/blob/master/RegularOutline.shader
OUTLINE_VS2 = """
attribute vec4 a_position;
attribute vec2 a_texCoord0;
uniform mat4 u_projTrans;
varying vec2 v_texCoords;

void main()
{
	v_texCoords = a_texCoord0;
	gl_Position =  u_projTrans * a_position;
}
"""


OUTLINE_FS2 = """
 #version 330
#ifdef GL_ES
#define LOWP lowp
precision mediump float;
#else
#define LOWP
#endif

const float offset = 1.0 / 128.0;
varying vec2 v_texCoords;
uniform sampler2D u_texture;
void main()
{
	vec4 col = texture2D(u_texture, v_texCoords);
	if (col.a > 0.5)
		gl_FragColor = col;
	else {
		float a = texture2D(u_texture, vec2(v_texCoords.x + offset, v_texCoords.y)).a +
			texture2D(u_texture, vec2(v_texCoords.x, v_texCoords.y - offset)).a +
			texture2D(u_texture, vec2(v_texCoords.x - offset, v_texCoords.y)).a +
			texture2D(u_texture, vec2(v_texCoords.x, v_texCoords.y + offset)).a;
		if (col.a < 1.0 && a > 0.0)
			gl_FragColor = vec4(0.0, 0.0, 0.0, 0.8);
		else
			gl_FragColor = col;
	}
}
 """


OUTLINE_VS = """
#version 330 core
in vec2 aPos;
in vec2 aTexCoords;

out vec2 TexCoords;

void main()
{
    gl_Position = vec4(aPos.x, aPos.y, -1.0, 1.0);
    TexCoords = aTexCoords;
}
"""

OUTLINE_FS = """
 #version 330


out vec4 FragColor;
const float offset = 1.0 / 256;//128.0;
in vec2 TexCoords;
uniform sampler2D screenTexture;

void main()
{
	vec4 col = texture2D(screenTexture, TexCoords);
	if (col.a > 0.5)
		FragColor = vec4(0.0, 0.0, 1.0, 0.0);
	else {
		float a = texture2D(screenTexture, vec2(TexCoords.x + offset, TexCoords.y)).a +
			texture2D(screenTexture, vec2(TexCoords.x, TexCoords.y - offset)).a +
			texture2D(screenTexture, vec2(TexCoords.x - offset, TexCoords.y)).a +
			texture2D(screenTexture, vec2(TexCoords.x, TexCoords.y + offset)).a;
		if (col.a < 1.0 && a > 0.0)
			FragColor =  vec4(1.0, 0.0, 0.0, 0.8);
		else
			FragColor = vec4(0.0, 0.0, 0.0, 0.0);
	}
}
 """
