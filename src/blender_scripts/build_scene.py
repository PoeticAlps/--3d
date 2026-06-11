"""
圆明园数字重建 - 完整脚本（创建场景 + 导出GLB）
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector

# ============================================================
# 输出配置
# ============================================================
OUTPUT_DIR = "/Users/saint/Desktop/hermes-workspace-2/yuanmingyuan-3d/output"
OUTPUT_GLB = os.path.join(OUTPUT_DIR, "yuanmingyuan.glb")

# ============================================================
# 清空场景
# ============================================================
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

# ============================================================
# 材质
# ============================================================
def create_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    if 'Metallic' in bsdf.inputs:
        bsdf.inputs['Metallic'].default_value = metallic
    return mat

def create_materials():
    materials = {}
    materials['marble'] = create_material("Marble", (0.95, 0.93, 0.88, 1.0), 0.3)
    materials['red_pillar'] = create_material("Red_Pillar", (0.7, 0.15, 0.1, 1.0), 0.6)
    materials['gold'] = create_material("Gold", (0.85, 0.65, 0.2, 1.0), 0.3, 0.9)
    materials['roof_dark'] = create_material("Roof_Dark", (0.15, 0.15, 0.18, 1.0), 0.7)
    materials['roof_yellow'] = create_material("Roof_Yellow", (0.85, 0.7, 0.2, 1.0), 0.4, 0.1)
    materials['wood'] = create_material("Wood", (0.4, 0.25, 0.15, 1.0), 0.8)
    
    # 水面
    mat_water = bpy.data.materials.new(name="Water")
    mat_water.use_nodes = True
    nodes = mat_water.node_tree.nodes
    bsdf = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs['Base Color'].default_value = (0.1, 0.3, 0.4, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    if 'IOR' in bsdf.inputs:
        bsdf.inputs['IOR'].default_value = 1.33
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = 0.9
    materials['water'] = mat_water
    
    materials['grass'] = create_material("Grass", (0.2, 0.45, 0.15, 1.0), 0.9)
    
    return materials

# ============================================================
# 建筑构建
# ============================================================
def create_hall(name, width=18, depth=12, height=4):
    parts = []
    
    # 基座
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.4))
    base = bpy.context.active_object
    base.scale = (width/2 + 1, depth/2 + 1, 0.4)
    base.name = f"{name}_Base"
    parts.append(base)
    
    # 柱子
    for row in range(3):
        for col in range(5):
            x = -width/3 + col * width/4
            y = -depth/4 + row * depth/4
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.25, depth=height, location=(x, y, height/2 + 0.8))
            pillar = bpy.context.active_object
            pillar.name = f"{name}_Pillar_{row}_{col}"
            parts.append(pillar)
    
    # 屋顶
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=width*0.5, depth=height*0.6, location=(0, 0, height + 0.8 + height*0.3))
    roof = bpy.context.active_object
    roof.scale = (1, depth/width, 1)
    roof.name = f"{name}_Roof"
    parts.append(roof)
    
    # 屋顶顶部
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=width*0.35, depth=height*0.3, location=(0, 0, height + 0.8 + height*0.9))
    roof_top = bpy.context.active_object
    roof_top.scale = (1, depth/width, 1)
    roof_top.name = f"{name}_Roof_Top"
    parts.append(roof_top)
    
    # 台阶
    for i in range(4):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -depth/2 - 0.8 - i*0.4, 0.8 + i*0.15))
        stair = bpy.context.active_object
        stair.scale = (2, 0.2, 0.075)
        stair.name = f"{name}_Stair_{i}"
        parts.append(stair)
    
    return parts

# ============================================================
# 大水法（西洋楼）
# ============================================================
def create_dashuifa():
    parts = []
    
    # 罗马柱
    positions = [(-4, 0), (-2, 0), (0, 0), (2, 0), (4, 0),
                 (-3, 3), (-1, 3), (1, 3), (3, 3),
                 (-3, -3), (-1, -3), (1, -3), (3, -3)]
    
    for i, (x, y) in enumerate(positions):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.25, depth=5, location=(x, y, 2.5))
        col = bpy.context.active_object
        col.name = f"Dashuifa_Column_{i}"
        parts.append(col)
        
        bpy.ops.mesh.primitive_cube_add(size=0.8, location=(x, y, 5.2))
        cap = bpy.context.active_object
        cap.name = f"Dashuifa_Capital_{i}"
        parts.append(cap)
    
    # 拱门顶部
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 4))
    arch = bpy.context.active_object
    arch.scale = (3, 0.5, 0.8)
    arch.name = "Dashuifa_Arch"
    parts.append(arch)
    
    # 基座
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.3))
    platform = bpy.context.active_object
    platform.scale = (12, 8, 0.3)
    platform.name = "Dashuifa_Platform"
    parts.append(platform)
    
    # 喷泉水池
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=4, depth=0.5, location=(0, 6, 0.25))
    pool = bpy.context.active_object
    pool.name = "Dashuifa_Pool"
    parts.append(pool)
    
    return parts

# ============================================================
# 九州清晏
# ============================================================
def create_jiuzhou():
    parts = []
    
    # 中央主岛
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=20, depth=2, location=(0, 0, -0.5))
    island = bpy.context.active_object
    island.name = "Jiuzhou_Center_Island"
    parts.append(island)
    
    # 八个方位的小岛
    positions = [(50, 0), (-50, 0), (0, 50), (0, -50),
                 (35, 35), (35, -35), (-35, 35), (-35, -35)]
    names = ["E", "W", "N", "S", "NE", "SE", "NW", "SW"]
    
    for (x, y), n in zip(positions, names):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=12, depth=2, location=(x, y, -0.5))
        island = bpy.context.active_object
        island.name = f"Jiuzhou_{n}_Island"
        parts.append(island)
        
        # 小亭子底座
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=3, depth=0.3, location=(x, y, 0.5))
        base = bpy.context.active_object
        base.name = f"Pavilion_Base_{n}"
        parts.append(base)
        
        # 亭子柱子
        for dx, dy in [(-1.5, -1.5), (1.5, -1.5), (-1.5, 1.5), (1.5, 1.5)]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.15, depth=2.5, location=(x+dx, y+dy, 1.8))
            pillar = bpy.context.active_object
            pillar.name = f"Pavilion_Pillar_{n}"
            parts.append(pillar)
        
        # 亭子屋顶
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=4, depth=1.5, location=(x, y, 3.5))
        roof = bpy.context.active_object
        roof.name = f"Pavilion_Roof_{n}"
        parts.append(roof)
    
    return parts

# ============================================================
# 方壶胜境
# ============================================================
def create_fangpu():
    parts = []
    
    # 水上平台
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    platform = bpy.context.active_object
    platform.scale = (25, 20, 0.5)
    platform.name = "Fangpu_Platform"
    parts.append(platform)
    
    # 主殿
    for item in create_hall("Fangpu", 12, 8, 5):
        item.location.y += 5
        parts.append(item)
    
    # 左右楼阁
    for sx in [-12, 12]:
        for floor in range(3):
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=3, depth=3, location=(sx, 0, 2 + floor*3))
            tower = bpy.context.active_object
            tower.name = f"Tower_{sx}_{floor}"
            parts.append(tower)
        
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=4, depth=2, location=(sx, 0, 11))
        roof = bpy.context.active_object
        roof.name = f"Tower_Roof_{sx}"
        parts.append(roof)
    
    # 桥梁
    for by in [-15, 15]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, by, 0.3))
        bridge = bpy.context.active_object
        bridge.scale = (2, 8, 0.3)
        bridge.name = f"Bridge_{by}"
        parts.append(bridge)
    
    return parts

# ============================================================
# 环境
# ============================================================
def create_environment():
    parts = []
    
    # 水面
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.3))
    water = bpy.context.active_object
    water.name = "Lake"
    parts.append(("water", water))
    
    # 地面
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.5))
    ground = bpy.context.active_object
    ground.name = "Ground"
    parts.append(("grass", ground))
    
    # 假山
    for i, (loc, scale) in enumerate([((60, -60, 0), (25, 20, 15)), ((-60, 60, 0), (20, 25, 12))]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=loc)
        mountain = bpy.context.active_object
        mountain.scale = scale
        mountain.name = f"Mountain_{i}"
        parts.append(("marble", mountain))
    
    return parts

# ============================================================
# 灯光和相机
# ============================================================
def setup_lighting():
    bpy.ops.object.light_add(type='SUN', location=(50, -50, 100))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(45))
    
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 50))
    ambient = bpy.context.active_object
    ambient.data.energy = 1000
    ambient.data.size = 100

def setup_camera():
    bpy.ops.object.camera_add(location=(120, -100, 60))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(60), 0, math.radians(50))
    bpy.context.scene.camera = camera

# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 60)
    print("🏛️ 圆明园数字重建")
    print("=" * 60)
    
    clear_scene()
    materials = create_materials()
    
    # 创建四大景区
    print("👑 创建正大光明...")
    for item in create_hall("Zhengda", 20, 14, 5):
        item.location.x = -80
    
    print("🏛️ 创建大水法...")
    for item in create_dashuifa():
        item.location.y += 80
    
    print("🏝️ 创建九州清晏...")
    create_jiuzhou()
    
    print("🏯 创建方壶胜境...")
    for item in create_fangpu():
        item.location.x += 80
    
    # 环境
    print("🌍 创建环境...")
    env_items = create_environment()
    for mat_name, obj in env_items:
        if mat_name in materials:
            obj.data.materials.append(materials[mat_name])
    
    # 灯光和相机
    print("💡 设置灯光...")
    setup_lighting()
    print("📷 设置相机...")
    setup_camera()
    
    # 导出
    print("📦 导出GLB...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=False,
        export_apply=True
    )
    
    file_size = os.path.getsize(OUTPUT_GLB) / 1024
    print("=" * 60)
    print(f"✅ 完成！")
    print(f"📁 文件: {OUTPUT_GLB}")
    print(f"📊 大小: {file_size:.1f} KB")
    print("=" * 60)

if __name__ == "__main__":
    main()
