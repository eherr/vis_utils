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


SKYBOX_VS = """
#version 300
//src: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/
//https://www.youtube.com/watch?v=_Ix5oN8eC1E

in vec3 position;
uniform mat4 modelMatrix;
uniform mat4 viewMatrix;
uniform mat4 projectionMatrix;

out vec3 textureCoords;

void main()
{
   gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(position,1.0);
   textureCoords = position;
}
"""


SKYBOX_FS = """
#version 300
//src: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-5-a-textured-cube/
//https://www.youtube.com/watch?v=_Ix5oN8eC1E
in vec3 textureCoords;

out vec4 color;

uniform sampleCube tex;

void main()
{
    color = (texture( tex, textureCoords);
}
"""



