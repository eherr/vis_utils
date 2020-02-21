# Visualization Utilities

Simple scene graph and OpenGL 3.3 renderer for data structures from [anim_utils](https://github.com/eherr/anim_utils.git)  
The code was developed as a side project for debugging purposes based on the following sources:  
http://www.glprogramming.com/  
https://learnopengl.com  
http://www.lighthouse3d.com/tutorials  
https://www.youtube.com/user/ThinMatrix  


## Example 

```python   
from vis_utils.glut_app import GLUTApp
from vis_utils.scene.task_manager import Task

def print_global_vars(dt, app):
    scene = app.scene
    lines = []
    for key in scene.global_vars:
        value = str(scene.global_vars[key])
        lines.append(key+": "+value)
    app.set_console_lines(lines)

    
def control_func(key, params):
    app, controller = params
    if key == str.encode(" "):
        controller.toggleAnimation()
    elif key == str.encode("l"):
        controller.loopAnimation = not controller.loopAnimation

    app.scene.global_vars["frame"] = controller.get_current_frame_idx()
    app.scene.global_vars["loop"] = controller.loopAnimation
    app.scene.global_vars["speed"] = controller.animationSpeed

def main(bvh_file):
    c_pose = dict()
    c_pose["zoom"] = -500
    c_pose["position"] = [0, 0, -50]
    c_pose["angles"] = (45, 200)
    a = GLUTApp(800, 600, title="bvh player",console_scale=0.4, camera_pose=c_pose)
    o = a.scene.object_builder.create_object_from_file("bvh", bvh_file)
    c = o._components["animation_controller"]
    a.keyboard_handler["control"] = (control_func, (a, c))
    a.scene.draw_task_manager.add("print", Task("print", print_global_vars, a))
    a.run()
main("example.bvh")


```
## Developer

Erik Herrmann (erik.herrmann at dfki.de)



## License
Copyright (c) 2019 DFKI GmbH.  
MIT License, see the LICENSE file.



