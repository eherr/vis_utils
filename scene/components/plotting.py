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
https://stackoverflow.com/questions/10944621/dynamically-updating-plot-in-matplotlib
https://github.com/matplotlib/matplotlib/issues/9606
https://stackoverflow.com/questions/15908371/matplotlib-colorbars-and-its-text-labels
"""
import json
import os
import socket
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from ...graphics.renderer.lines import ExtendingLineRenderer
from morphablegraphs.utilities import write_to_json_file
from .component_base import ComponentBase

#import seaborn as sns; sns.set()

BUFFER_SIZE = 1024000


def array_to_grid(segment_errors, n_iterations, n_frames):
    #print(segment_errors)
    grid = np.zeros((n_iterations, n_frames))
    for i in range(n_iterations):
        for j in range(n_frames):
            key = str(j)
            if key in segment_errors[i]:
                grid[i,j] = segment_errors[i][key]
            else:
                grid[i,j] = -1
    print("converted to grid")
    return grid


def export_figure(server, fig, heatmap_data, n_iterations):
    time_stamp = datetime.now().strftime("%d%m%y_%H%M%S")
    filename =  server.data_dir + os.sep + "heatmaps"+os.sep+"heatmap_" + str(n_iterations) + "_" + time_stamp
    plt.savefig(filename=filename+".png", format="png")
    print("export to file", filename)
    write_to_json_file(filename+".json", heatmap_data.tolist())


def save_plot_data(server, heatmap_data, n_iterations):
    time_stamp = datetime.now().strftime("%d%m%y_%H%M%S")
    filename = server.data_dir +os.sep+"heatmap_" + str(n_iterations) + "_" + time_stamp
    write_to_json_file(filename+".json", heatmap_data)
    print("export to file", filename)

def parse_messages(buffer):
    #print("parse buffer", buffer)
    start_offset = 0
    end_offset = 0
    n_bytes = len(buffer)
    messages = []
    while start_offset < n_bytes:
        while end_offset < n_bytes and buffer[end_offset] != 0:
            end_offset += 1
        #print("found end at", end_offset, buffer[end_offset])
        msg = ""
        for idx in range(start_offset, end_offset):
            #print("serious what is your problem", str(chr(buffer[idx])))
            #print(str(chr(buffer[idx])))
            msg += str(chr(buffer[idx]))
        #print("attempty",msg)
        messages.append(json.loads(msg))
        start_offset = end_offset + 1
        end_offset+=1

    print("parsed", len(messages))
    return messages


def on_new_client_plot_heatmap(server, conn, addr):
    fig, ax = plt.subplots()
    errors = []
    ax.set_ylabel('Iterations')
    ax.set_xlabel('Frame')
    segment_errors = []
    fig.show()
    n_iterations = 0
    cb = None
    heatmap = None
    while True:
        try:
            time.sleep(1)
            buffer = conn.recv(BUFFER_SIZE)
            conn.send(b"OK")
            try:
                messages = parse_messages(buffer)
            except:
                print("Error: could not decode message", buffer)
                continue
            for data in messages:

                if "trajectories" in data:
                    for (label, points) in data["trajectories"].items():
                        #server.mutex.acquire()
                        if points is not None and len(points) > 0:
                            server.schedule_trajectory_plot_update(label, points)

                            #server.mutex.release()
                if "error" in data and "segmentErrors" in data:
                    error = data["error"]
                    server.update_error_plot(error)
                    n_frames = data["n_frames"]
                    segment_error_frame = data["segmentErrors"]
                    if segment_error_frame is not None:
                        errors.append(error)
                        segment_errors.append(segment_error_frame)
                        n_iterations+=1
                    print("error at",n_iterations, error)
                    if n_frames > 0 and n_iterations > 0:
                        heatmap = array_to_grid(segment_errors, n_iterations, n_frames)
                    if (n_iterations > 0 and n_iterations % server.n_save_iters == 0 or
                            ("finished" in data and data["finished"])) \
                            and heatmap is not None:
                        heatmap_data = []
                        for row in heatmap_data:
                            heatmap_data.append(row.to_list())
                        data["heatmap"] = heatmap_data
                    export_figure(server, fig, heatmap, n_iterations)

        except Exception as e:
            print(e.args)
    conn.close()


def random_color():
    color = [0,0,0]
    color[0] = np.random.rand(1,1 )[0]
    color[1] = np.random.rand(1, 1)[0]
    color[2] = np.random.rand(1, 1)[0]
    return color


def on_new_client(server, conn, addr):
    print("create tcp connection to ", addr)
    while True:
        try:
            time.sleep(1)
            msg = conn.recv(BUFFER_SIZE)
            conn.send(b"OK")
            try:
                data = json.loads(msg.decode("utf-8"))
            except:
                print("Error: could not decode message", msg)
                continue
            if "trajectories" in data:
                for (label, points) in data["trajectories"].items():
                    if points is not None and len(points) > 0:
                        server.schedule_trajectory_plot_update(label,points)
        except Exception as e:
            print(e.args)
            print("connection was closed")
            return
    conn.close()


def client_thread(server, conn, addr):
    server.scene_object.scene.internal_vars["segment_errors"] = []
    n_iterations = 0
    while True:
        try:
            time.sleep(1)
            buffer = conn.recv(BUFFER_SIZE)
            conn.send(b"OK")
            try:
                messages = parse_messages(buffer)
            except:
                print("Error: could not decode message", buffer)
                continue
            for data in messages:
                if "trajectories" in data:
                    for (label, points) in data["trajectories"].items():
                        if points is not None and len(points) > 0:
                            server.schedule_trajectory_plot_update(label, points)

                if "error" in data and "segmentErrors" in data:
                    error = data["error"]
                    server.scene_object.scene.internal_vars["error"] = error
                    n_frames = data["n_frames"]
                    segment_error_frame = data["segmentErrors"]
                    if segment_error_frame is not None:
                        server.scene_object.scene.internal_vars["segment_errors"].append(segment_error_frame)
                        n_iterations += 1
                        heatmap = array_to_grid(server.scene_object.scene.internal_vars["segment_errors"], n_iterations, n_frames)
                        server.scene_object.scene.internal_vars["heatmap"] = heatmap
                        server.schedule_plot_update()
                        print("heatmap", heatmap.shape, (n_iterations, n_frames))
                        if (n_iterations > 0 and n_iterations % server.n_save_iters == 0 or ("finished" in data and data["finished"])):
                            heatmap_data = []
                            for row in heatmap:
                                heatmap_data.append(row.tolist())
                            data["heatmap"] = heatmap_data
                            save_plot_data(server, data, n_iterations)
        except Exception as e:
                print(e.args)
                print("connection was closed")
    conn.close()


def server_thread(server, s):
    print("sever started")
    while server.run:
        c, addr = s.accept()
        t = threading.Thread(target=client_thread, name="addr", args=(server, c, addr))
        t.start()
        server.connections[addr] = t
    print("server stopped")
    s.close()

DATA_DIR = r"C:\Users\erhe01\Documents\Visual Studio 2015\Projects\simulation\SimulationAnalysisTool\mg-tools\experiments\particle_filter\data"


class PlottingServerComponent(ComponentBase):
    """ TCP server that sends and receives a single message
        https://pymotw.com/2/socket/tcp.html
    """
    BUFFER_SIZE = 10485760

    def __init__(self, scene_object, port, export_dir=DATA_DIR, buffer_size=BUFFER_SIZE):
        ComponentBase.__init__(self, scene_object)
        self.address = ("", port)
        self.buffer_size = buffer_size
        self.connections = dict()
        self.run = True
        self.mutex = threading.Lock()
        self.n_save_iters = 10
        self.lines = dict()
        #self.add_line("rec",[1,0,1])
        self.add_line("ref", [0,1,1])
        self.plot_update_queue = list()
        self.data_dir = export_dir

    def add_line(self, label, color):
        #self.mutex.acquire()
        line = ExtendingLineRenderer(color[0], color[1], color[2])
        line.addPoint([0, 0, 0])
        line.addPoint([10, 10, 0])
        self.lines[label] = line
        #self.mutex.release()

    def update(self, dt):
        self.mutex.acquire()
        for (label, points) in self.plot_update_queue:
            if label not in self.lines:
                color = random_color()
                self.add_line(label, color)
            self.update_line(label, points)
        self.plot_update_queue = list()
        self.mutex.release()

    def schedule_trajectory_plot_update(self, label, points):
        #print("schedule update for", label, len(points))
        self.mutex.acquire()
        self.plot_update_queue.append((label, points))
        self.mutex.release()

    def schedule_plot_update(self):
        print("update plot")
        self.scene_object.scene.internal_vars["update_plot"] = True

    def draw(self, m, v, p, l):
        for k, line in self.lines.items():
            line.draw(m, v, p)

    def update_line(self, label, points):
        self.lines[label].clear()
        for p in points:
            self.lines[label].addPoint(p)

    def start(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(self.address)
        except socket.error:
            print("Binding failed")
            return

        s.listen(10)
        t = threading.Thread(target=server_thread, name="c", args=(self, s))
        t.start()
        print("started server")

    def close(self):
        self.run = False

    def get_frame(self):
        return b"frame\n"


