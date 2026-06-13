"""
圆明园数字重建 - 增强版
Ocean Modifier水面 + 精细树木 + PBR材质
"""
import bpy
import math
import os
import random
from mathutils import Vector

OUTPUT_DIR = "/Users/saint/Desktop/hermes-workspace-2/yuanmingyuan-3d/output"
OUTPUT_GLB = os.path.join(OUTPUT_DIR, "yuanmingyuan_enhanced.glb")

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

def create_material(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_water_material():
    mat = bpy.data.materials.new(name="Water")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (500, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = (0.05, 0.2, 0.35, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['IOR'].default_value = 1.33
    bsdf.inputs['Transmission Weight'].default_value = 0.95
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_materials():
    mats = {}
    mats['marble'] = create_material("Marble", (0.95, 0.93, 0.88), 0.25)
    mats['red_pillar'] = create_material("Red_Pillar", (0.75, 0.12, 0.08), 0.5)
    mats['gold'] = create_material("Gold", (0.95, 0.75, 0.2), 0.2, 0.95)
    mats['roof_dark'] = create_material("Roof_Dark", (0.12, 0.12, 0.15), 0.8)
    mats['roof_yellow'] = create_material("Roof_Yellow", (0.9, 0.75, 0.2), 0.35, 0.2)
    mats['wood'] = create_material("Wood", (0.35, 0.22, 0.12), 0.85)
    mats['water'] = create_water_material()
    mats['grass'] = create_material("Grass", (0.15, 0.35, 0.1), 0.95)
    mats['rock'] = create_material("Rock", (0.45, 0.42, 0.38), 0.9)
    mats['white_marble'] = create_material("White_Marble", (0.98, 0.96, 0.92), 0.2)
    return mats

def create_tree(name, x, y, height=8, mats=None):
    """创建带枝叶的树"""
    # 树干
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.3, depth=height*0.4, location=(x, y, height*0.2))
    trunk = bpy.context.active_object
    trunk.name = f"{name}_Trunk"
    if mats and 'wood' in mats:
        trunk.data.materials.append(mats['wood'])
    
    # 枝干和叶子
    num_branches = random.randint(3, 5)
    for i in range(num_branches):
        angle = (i / num_branches) * math.pi * 2 + random.uniform(-0.3, 0.3)
        branch_length = height * 0.5
        branch_height = height * 0.4 + random.uniform(0, height * 0.2)
        
        # 分枝
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8, radius=0.12, depth=branch_length,
            location=(x + math.cos(angle) * branch_length * 0.3, y + math.sin(angle) * branch_length * 0.3, branch_height)
        )
        branch = bpy.context.active_object
        branch.rotation_euler = (math.radians(70) + random.uniform(-0.2, 0.2), 0, angle + math.pi/2)
        branch.name = f"{name}_Branch_{i}"
        if mats and 'wood' in mats:
            branch.data.materials.append(mats['wood'])
        
        # 叶簇
        for j in range(random.randint(2, 4)):
            leaf_size = random.uniform(1.0, 2.5)
            leaf_x = x + math.cos(angle) * (branch_length * 0.4 + random.uniform(-1, 1))
            leaf_y = y + math.sin(angle) * (branch_length * 0.4 + random.uniform(-1, 1))
            leaf_z = branch_height + random.uniform(-0.5, 1.5)
            
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=leaf_size, location=(leaf_x, leaf_y, leaf_z))
            leaves = bpy.context.active_object
            leaves.scale = (random.uniform(0.8, 1.2), random.uniform(0.8, 1.2), random.uniform(0.6, 1.0))
            leaves.name = f"{name}_Leaves_{i}_{j}"
            if mats and 'grass' in mats:
                leaves.data.materials.append(mats['grass'])

def create_hall(name, width=18, depth=12, height=4, mats=None):
    """创建殿宇"""
    # 基座
    for i in range(3):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.4 + i * 0.45))
        base = bpy.context.active_object
        base.scale = ((width/2 + 2 - i), (depth/2 + 2 - i), 0.4)
        base.name = f"{name}_Base_{i}"
        if mats and 'white_marble' in mats:
            base.data.materials.append(mats['white_marble'])
    
    # 柱子
    for row in range(3):
        for col in range(5):
            x = -width/3 + col * width/4
            y = -depth/4 + row * depth/4
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.25, depth=height, location=(x, y, height/2 + 1.2))
            pillar = bpy.context.active_object
            pillar.name = f"{name}_Pillar_{row}_{col}"
            if mats and 'red_pillar' in mats:
                pillar.data.materials.append(mats['red_pillar'])
    
    # 额枋
    for row_y in [-depth/4, depth/4]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, row_y, height + 0.6))
        beam = bpy.context.active_object
        beam.scale = (width/2 - 0.5, 0.2, 0.15)
        beam.name = f"{name}_Beam_{row_y}"
        if mats and 'red_pillar' in mats:
            beam.data.materials.append(mats['red_pillar'])
    
    # 屋顶
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=width*0.55 + 2, depth=height*0.3, location=(0, 0, height + 1.2 + height*0.15))
    roof_lower = bpy.context.active_object
    roof_lower.scale = (1, depth/width + 0.1, 1)
    roof_lower.rotation_euler.z = math.pi/4
    roof_lower.name = f"{name}_Roof_Lower"
    if mats and 'roof_yellow' in mats:
        roof_lower.data.materials.append(mats['roof_yellow'])
    
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=width*0.45, depth=height*0.4, location=(0, 0, height + 1.5 + height*0.4))
    roof_upper = bpy.context.active_object
    roof_upper.scale = (1, depth/width, 1)
    roof_upper.rotation_euler.z = math.pi/4
    roof_upper.name = f"{name}_Roof_Upper"
    if mats and 'roof_yellow' in mats:
        roof_upper.data.materials.append(mats['roof_yellow'])
    
    # 正脊
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height + 2.2 + height*0.6))
    ridge = bpy.context.active_object
    ridge.scale = (width*0.3, 0.3, 0.25)
    ridge.name = f"{name}_Ridge"
    if mats and 'gold' in mats:
        ridge.data.materials.append(mats['gold'])
    
    # 台阶
    for i in range(6):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -depth/2 - 1.5 - i*0.5, 1.2 + i*0.12))
        stair = bpy.context.active_object
        stair.scale = (2.5, 0.25, 0.06)
        stair.name = f"{name}_Stair_{i}"
        if mats and 'white_marble' in mats:
            stair.data.materials.append(mats['white_marble'])

def create_dashuifa(mats=None):
    """创建大水法"""
    # 基座
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    platform = bpy.context.active_object
    platform.scale = (15, 10, 0.5)
    platform.name = "Dashuifa_Platform"
    if mats and 'white_marble' in mats:
        platform.data.materials.append(mats['white_marble'])
    
    # 罗马柱
    x_positions = [-6, -3, 0, 3, 6]
    for i, x in enumerate(x_positions):
        for dx in [-1.2, 1.2]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.3, depth=6, location=(x + dx, 0, 3.5))
            col = bpy.context.active_object
            col.name = f"Dashuifa_Column_{i}_{dx}"
            if mats and 'white_marble' in mats:
                col.data.materials.append(mats['white_marble'])
        
        # 拱门
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 4.5))
        arch = bpy.context.active_object
        arch.scale = (1.2, 0.3, 1.2)
        arch.name = f"Dashuifa_Arch_{i}"
        if mats and 'white_marble' in mats:
            arch.data.materials.append(mats['white_marble'])
    
    # 喷泉水池
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=8, depth=0.8, location=(0, 12, 0.4))
    pool = bpy.context.active_object
    pool.scale = (1, 0.6, 1)
    pool.name = "Dashuifa_Pool"
    if mats and 'white_marble' in mats:
        pool.data.materials.append(mats['white_marble'])
    
    # 铜鹿
    for i, angle in enumerate([-0.3, 0, 0.3]):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.4, depth=1.5, location=(math.sin(angle) * 3, 12, 1.5))
        deer = bpy.context.active_object
        deer.rotation_euler = (math.radians(10), 0, angle)
        deer.name = f"Dashuifa_Deer_{i}"
        if mats and 'gold' in mats:
            deer.data.materials.append(mats['gold'])

def create_jiuzhou(mats=None):
    """创建九州清晏"""
    # 主岛
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=25, depth=2.5, location=(0, 0, -0.25))
    main_island = bpy.context.active_object
    main_island.name = "Jiuzhou_Main_Island"
    if mats and 'grass' in mats:
        main_island.data.materials.append(mats['grass'])
    
    # 八方位岛
    positions = [(55, 0), (-55, 0), (0, 55), (0, -55), (40, 40), (40, -40), (-40, 40), (-40, -40)]
    names = ["E", "W", "N", "S", "NE", "SE", "NW", "SW"]
    
    for (x, y), n in zip(positions, names):
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=14, depth=2, location=(x, y, -0.5))
        island = bpy.context.active_object
        island.name = f"Jiuzhou_{n}_Island"
        if mats and 'grass' in mats:
            island.data.materials.append(mats['grass'])
        
        # 亭子
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=3.5, depth=0.4, location=(x, y, 0.5))
        base = bpy.context.active_object
        base.name = f"Pavilion_Base_{n}"
        if mats and 'white_marble' in mats:
            base.data.materials.append(mats['white_marble'])
        
        for j in range(6):
            angle = (j / 6) * math.pi * 2
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.12, depth=2.8, location=(x + math.cos(angle) * 2, y + math.sin(angle) * 2, 2.1))
            pillar = bpy.context.active_object
            pillar.name = f"Pavilion_Pillar_{n}_{j}"
            if mats and 'red_pillar' in mats:
                pillar.data.materials.append(mats['red_pillar'])
        
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=4.5, depth=2, location=(x, y, 4.2))
        roof = bpy.context.active_object
        roof.name = f"Pavilion_Roof_{n}"
        if mats and 'roof_yellow' in mats:
            roof.data.materials.append(mats['roof_yellow'])
        
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.3, location=(x, y, 5.5))
        finial = bpy.context.active_object
        finial.name = f"Pavilion_Finial_{n}"
        if mats and 'gold' in mats:
            finial.data.materials.append(mats['gold'])

def create_fangpu(mats=None):
    """创建方壶胜境"""
    # 平台
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    platform = bpy.context.active_object
    platform.scale = (30, 25, 0.6)
    platform.name = "Fangpu_Platform"
    if mats and 'white_marble' in mats:
        platform.data.materials.append(mats['white_marble'])
    
    # 主殿
    create_hall("Fangpu", 16, 10, 6, mats)
    for obj in bpy.data.objects:
        if "Fangpu" in obj.name:
            obj.location.y += 8
    
    # 左右楼阁
    for sx in [-18, 18]:
        for floor in range(3):
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=4 - floor * 0.5, depth=3.5, location=(sx, 0, 2.5 + floor * 4))
            tower = bpy.context.active_object
            tower.name = f"Tower_{sx}_{floor}"
            if mats:
                mat = mats['red_pillar'] if floor % 2 == 0 else mats['white_marble']
                tower.data.materials.append(mat)
            
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=4.8 - floor * 0.5, depth=0.15, location=(sx, 0, 4.2 + floor * 4))
            eave = bpy.context.active_object
            eave.name = f"Eave_{sx}_{floor}"
            if mats and 'roof_yellow' in mats:
                eave.data.materials.append(mats['roof_yellow'])
        
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=3, depth=3, location=(sx, 0, 14))
        tower_top = bpy.context.active_object
        tower_top.name = f"Tower_Top_{sx}"
        if mats and 'roof_yellow' in mats:
            tower_top.data.materials.append(mats['roof_yellow'])

def create_environment(mats=None):
    """创建环境"""
    # Ocean Modifier水面
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, -0.2))
    water = bpy.context.active_object
    water.name = "Ocean"
    if mats and 'water' in mats:
        water.data.materials.append(mats['water'])
    
    # Ocean Modifier（波纹！）
    ocean_mod = water.modifiers.new(name="Ocean", type='OCEAN')
    ocean_mod.geometry_mode = 'GENERATE'
    ocean_mod.resolution = 12
    ocean_mod.spatial_size = 100
    ocean_mod.wave_scale = 0.8
    
    # 地面
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.6))
    ground = bpy.context.active_object
    ground.name = "Ground"
    if mats and 'grass' in mats:
        ground.data.materials.append(mats['grass'])
    
    # 假山
    rock_positions = [((80, -80, 0), (30, 25, 20)), ((-80, 80, 0), (25, 30, 18)), ((70, 70, 0), (20, 22, 15))]
    for i, (loc, scale) in enumerate(rock_positions):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=loc)
        rock = bpy.context.active_object
        rock.scale = scale
        rock.name = f"Rock_{i}"
        if mats and 'rock' in mats:
            rock.data.materials.append(mats['rock'])
    
    # 树木（60棵）
    tree_count = 0
    for i in range(80):
        x = random.uniform(-140, 140)
        y = random.uniform(-140, 140)
        # 避开建筑
        if (abs(x) < 35 and abs(y) < 35) or (abs(x - 80) < 30 and abs(y) < 30) or (abs(x + 80) < 30 and abs(y) < 30) or (abs(x) < 30 and abs(y - 80) < 30) or (abs(x) < 30 and abs(y + 80) < 30):
            continue
        if tree_count >= 60:
            break
        create_tree(f"Tree_{tree_count}", x, y, random.uniform(6, 12), mats)
        tree_count += 1

def setup_lighting():
    """设置灯光"""
    bpy.ops.object.light_add(type='SUN', location=(80, -60, 120))
    sun = bpy.context.active_object
    sun.data.energy = 4.0
    sun.data.color = (1.0, 0.95, 0.9)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(45))
    
    bpy.ops.object.light_add(type='AREA', location=(-40, 40, 60))
    fill = bpy.context.active_object
    fill.data.energy = 800
    fill.data.size = 80
    fill.data.color = (0.7, 0.8, 1.0)
    
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.4, 0.5, 0.7, 1.0)
        bg.inputs['Strength'].default_value = 0.5

def setup_camera():
    """设置相机"""
    bpy.ops.object.camera_add(location=(150, -120, 70))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(65), 0, math.radians(50))
    camera.data.lens = 35
    bpy.context.scene.camera = camera

def main():
    print("=" * 70)
    print("圆明园数字重建 - 增强版")
    print("Ocean Modifier水面 + 精细树木 + PBR材质")
    print("=" * 70)
    
    clear_scene()
    print("创建材质...")
    mats = create_materials()
    
    print("创建正大光明殿...")
    create_hall("Zhengda", 24, 16, 7, mats)
    for obj in bpy.data.objects:
        if "Zhengda" in obj.name:
            obj.location.x = -80
    
    print("创建大水法...")
    create_dashuifa(mats)
    for obj in bpy.data.objects:
        if "Dashuifa" in obj.name:
            obj.location.y += 80
    
    print("创建九州清晏...")
    create_jiuzhou(mats)
    
    print("创建方壶胜境...")
    create_fangpu(mats)
    for obj in bpy.data.objects:
        if any(x in obj.name for x in ["Fangpu", "Tower", "Eave"]):
            obj.location.x += 80
    
    print("创建环境...")
    create_environment(mats)
    
    print("设置灯光...")
    setup_lighting()
    print("设置相机...")
    setup_camera()
    
    print("导出GLB...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=OUTPUT_GLB, export_format='GLB', use_selection=False, export_apply=True)
    
    file_size = os.path.getsize(OUTPUT_GLB) / 1024
    print("=" * 70)
    print(f"完成！文件: {OUTPUT_GLB}")
    print(f"大小: {file_size:.1f} KB")
    print("=" * 70)

if __name__ == "__main__":
    main()
