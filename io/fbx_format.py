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
import os
from PIL import Image
try:
    from . import geom_io
except:
    print("Info: Disable FBX due to missing library")
    geom_io = None


def load_textures(model_data):
    loaded_images = dict()
    if "mesh_list" not in model_data:
        return
    for mesh in model_data["mesh_list"]:
        texture_path = mesh["texture"]
        if texture_path in loaded_images:
            img_data = loaded_images[texture_path]
        elif os.path.isfile(texture_path):
            img_data = Image.open(texture_path, "r")
        else:
            if "texture_not_found" not in loaded_images:
                loaded_images["texture_not_found"] = Image.new("RGB", (400,400), "grey")
            img_data = loaded_images["texture_not_found"]

        mesh["material"] = dict()
        mesh["material"]["Kd"] = img_data


def load_model_from_fbx_file(filename):
    if geom_io is None:
        return None
    model_data = geom_io.load_fbx_file(str.encode(filename))
    if model_data is None:
        return
    print(" model", model_data.keys())
    load_textures(model_data)
    return model_data
