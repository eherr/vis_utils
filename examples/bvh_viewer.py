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
    app = GLUTApp(800, 600, title="bvh player", camera_pose=c_pose)
    c = o._components["animation_controller"]
    app.keyboard_handler["control"] = (control_func, (app, c))
    
    app.scene.draw_task_manager.add("print", Task("print", print_global_vars, app))
    app.run()
main("example.bvh")
