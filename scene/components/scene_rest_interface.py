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
from .component_base import ComponentBase
from .terrain_component import TerrainComponent
import tornado.ioloop
import tornado.web
import json
import threading
import asyncio
import os
from PIL import Image


class ServerThread(threading.Thread):
    """ Controls a WebSocketApplication by starting a tornado IOLoop instance
    """
    def __init__(self, web_app, port=8889):
        threading.Thread.__init__(self)
        self.web_app = web_app
        self.port = port

    def run(self):
        print("starting web socket server on port", self.port)
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.web_app.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


    def stop(self):
        print("stopping server")
        tornado.ioloop.IOLoop.instance().stop()


class SetHeightMapHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self.app = application

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

    @tornado.gen.coroutine
    def post(self):
        try:
            input_str = self.request.body.decode("utf-8")
            data = json.loads(input_str)
            answer_str = self.app.server.set_height_map(data)
            self.write(answer_str)

        except Exception as e:
            print("caught exception in post")
            self.write("Caught an exception: %s" % e)
            raise
        finally:
            self.finish()



class WebApp(tornado.web.Application):
    """ extends the Application class by a list of connections to allow access from other classes
    """
    def __init__(self, server, handlers=None, default_host="", transforms=None, **settings):
        self.server = server
        tornado.web.Application.__init__(self, handlers, default_host, transforms)


class SceneRESTInterface(ComponentBase):
    def __init__(self, scene_object, port):
        ComponentBase.__init__(self, scene_object)
        self._scene_object = scene_object
        self.scene = scene_object.scene
        self.port = port
        self.web_app = WebApp(self, [(r"/set_height_map", SetHeightMapHandler),
                                       ])
        self.server_thread = ServerThread(self.web_app, port)


    def start(self):
        self.server_thread.start()
        print("started scene REST interface on port ", self.port)

    def stop(self):
        self.server_thread.stop()
        print("stopped scene REST interface on port ", self.port)

    def set_height_map(self, data):
        mesh = None
        success = False
        if "image_path" in data:
            image_path = data["image_path"]
            width = data["width"]
            depth = data["depth"]
            scale = [1.0, 1.0]
            if "scale" in data:
                scale = data["scale"]
            height_scale = data["height_scale"]
            if os.path.isfile(image_path):
                with open(image_path, "rb") as input_file:
                    img = Image.open(input_file)
                    height_map_image = img.copy()  # work with a copy of the image to close the file
                    img.close()
                    pixel_is_tuple = not image_path.endswith("bmp")
                    success = True

        elif "image" in data:
            import base64
            size = data["size"]
            mode = data["mode"]
            width = data["width"]
            depth = data["depth"]
            height_scale = data["height_scale"]
            height_map_image = Image.frombytes(mode, size, base64.decodebytes(data["image"]))
            success = success


        if success:
            builder = self.scene.object_builder
            terrain = builder.construction_methods["terrain"]
            self.scene.schedule_func_call("terrain", terrain, (builder, width, depth, height_map_image, height_scale))
            return "OK"
        else:
            return "Missing required data"



