# Skeleton Animation Visualization Utilities

Simple scene graph and OpenGL 3.3 renderer for data structures from [anim_utils](https://github.com/eherr/anim_utils.git)  
The code was developed as a side project for debugging purposes based on the following sources:  
http://www.glprogramming.com/  
https://learnopengl.com  
http://www.lighthouse3d.com/tutorials  
https://www.youtube.com/user/ThinMatrix  


Note: To use the library on Windows, please install the PyOpenGL wheel provided by Cristoph Gohlke which also contains the GLUT-DLLs:
https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyopengl


The library also supports the import of character meshes and skeletons from glb and fbx files. To enable the fbx support a custom [FBX SDK Wrapper](https://github.com/eherr/py_fbx_wrapper) has to be build and copied into the directory "vis_utils/io".


```python   

    app.scene.object_builder.create_object_from_file("glb", glb_file)
    app.scene.object_builder.create_object_from_file("fbx", fbx_file)

```


## Developer

Erik Herrmann (erik.herrmann at dfki.de)



## License
Copyright (c) 2019 DFKI GmbH.  
MIT License, see the LICENSE file.



