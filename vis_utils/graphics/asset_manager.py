from  ..graphics.geometry.mesh import Mesh
from ..graphics import materials
from ..graphics.material_manager import MaterialManager


class AssetManager():
    instance = None
    def __init__(self):
        if self.instance is None:
            self.instance = self
            self.material_manager = MaterialManager()
            
    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = AssetManager()
        return cls.instance

    def create_material(self, m_desc):
        material = None
        if "material" in m_desc and "Kd" in list(m_desc["material"].keys()):
            texture_name = m_desc["texture"]
            if texture_name is not None and texture_name.endswith(b'Hair_texture_big.png'):
                return None
            material = self.material_manager.get(m_desc["texture"])
            if material is None:
                material = materials.TextureMaterial.from_image(m_desc["material"])
                self.material_manager.set(m_desc["texture"], material)
        return material
    
    def create_mesh_from_desc(self, m_desc):
        n_normals = len(m_desc["normals"])
        n_vertices = len(m_desc["vertices"])
        if n_normals != n_vertices:
            print("error vertices and normals do are not the same count",n_vertices, n_normals)
            return None
        material = self.create_material(m_desc)
        mesh = Mesh.build_from_desc(m_desc, material)
        return mesh

    def create_animated_mesh(self, m_desc):
        material = self.create_material(m_desc)
        mesh = Mesh.build_legacy_animated_mesh(m_desc, material)
        return mesh