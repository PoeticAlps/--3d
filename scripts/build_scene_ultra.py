"""
圆明园数字重建 - 超精细版
增加斗拱、雕花、精细屋顶、更多植被、粒子草地
"""
import bpy
import math
import os
import random
from mathutils import Vector

OUTPUT_DIR = "/Users/saint/Desktop/hermes-workspace-2/yuanmingyuan-3d/output"
OUTPUT_GLB = os.path.join(OUTPUT_DIR, "yuanmingyuan_ultra.glb")

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

def create_material(name, color, roughness=0.5, metallic=0.0, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    
    if emission_strength > 0:
        bsdf.inputs['Emission Color'].default_value = (*color, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_water_material():
    mat = bpy.data.materials.new(name="Water_Ultra")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.02, 0.08, 0.15, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.02
    bsdf.inputs['IOR'].default_value = 1.333
    bsdf.inputs['Transmission Weight'].default_value = 0.98
    bsdf.inputs['Alpha'].default_value = 0.95
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_marble_material():
    """创建大理石材质 - 带噪波纹理"""
    mat = bpy.data.materials.new(name="Marble_Detailed")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 0)
    bsdf.inputs['Roughness'].default_value = 0.15
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
    
    # 添加噪波纹理模拟大理石纹路
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-400, 0)
    
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-200, 0)
    mapping.inputs['Scale'].default_value = (5, 5, 5)
    
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (0, 100)
    noise.inputs['Scale'].default_value = 50.0
    noise.inputs['Detail'].default_value = 8.0
    
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (200, 100)
    color_ramp.color_ramp.elements[0].color = (0.92, 0.90, 0.85, 1.0)
    color_ramp.color_ramp.elements[1].color = (0.98, 0.96, 0.92, 1.0)
    
    links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_gold_material():
    """创建金色材质 - 用于装饰"""
    mat = bpy.data.materials.new(name="Gold_Ultra")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.95, 0.75, 0.2, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.15
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Specular IOR Level'].default_value = 0.9
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_red_lacquer_material():
    """创建红漆材质 - 用于柱子"""
    mat = bpy.data.materials.new(name="Red_Lacquer")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.65, 0.08, 0.05, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.3
    bsdf.inputs['Specular IOR Level'].default_value = 0.7
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def create_materials():
    mats = {}
    mats['marble'] = create_marble_material()
    mats['red_pillar'] = create_red_lacquer_material()
    mats['gold'] = create_gold_material()
    mats['roof_dark'] = create_material("Roof_Dark", (0.08, 0.08, 0.1), 0.7)
    mats['roof_yellow'] = create_material("Roof_Yellow", (0.85, 0.65, 0.15), 0.4, 0.1)
    mats['roof_green'] = create_material("Roof_Green", (0.15, 0.35, 0.25), 0.5)
    mats['wood'] = create_material("Wood", (0.35, 0.22, 0.12), 0.85)
    mats['water'] = create_water_material()
    mats['grass'] = create_material("Grass", (0.12, 0.32, 0.08), 0.95)
    mats['grass_dark'] = create_material("Grass_Dark", (0.08, 0.25, 0.05), 0.95)
    mats['rock'] = create_material("Rock", (0.45, 0.42, 0.38), 0.9)
    mats['white_marble'] = create_material("White_Marble", (0.98, 0.96, 0.92), 0.2)
    mats['stone_path'] = create_material("Stone_Path", (0.55, 0.52, 0.48), 0.85)
    return mats

def create_dougong(x, y, z, size=0.3, mats=None):
    """创建斗拱结构 - 中国古建筑特色"""
    # 斗（底座）
    bpy.ops.mesh.primitive_cube_add(size=size, location=(x, y, z))
    dou = bpy.context.active_object
    dou.scale = (1.2, 1.2, 0.6)
    dou.name = f"Dou_{x}_{y}"
    if mats and 'wood' in mats:
        dou.data.materials.append(mats['wood'])
    
    # 拱（横向木条）
    for i in range(3):
        angle = i * math.pi / 2
        bpy.ops.mesh.primitive_cube_add(
            size=size * 0.8,
            location=(x + math.cos(angle) * size * 0.8, y + math.sin(angle) * size * 0.8, z + size * 0.4)
        )
        gong = bpy.context.active_object
        gong.scale = (1.5, 0.3, 0.2)
        gong.rotation_euler = (0, 0, angle)
        gong.name = f"Gong_{x}_{y}_{i}"
        if mats and 'wood' in mats:
            gong.data.materials.append(mats['wood'])

def create_roof_tiles(width, depth, height, mats, roof_type='hip'):
    """创建精细屋顶 - 带瓦片纹理"""
    # 主屋顶体
    if roof_type == 'hip':
        # 庑殿顶
        bpy.ops.mesh.primitive_cone_add(
            vertices=4,
            radius1=max(width, depth) * 0.6,
            depth=height * 0.4,
            location=(0, 0, height)
        )
        roof = bpy.context.active_object
        roof.scale = (width/max(width, depth) + 0.2, depth/max(width, depth) + 0.2, 1)
    else:
        # 歇山顶
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height))
        roof = bpy.context.active_object
        roof.scale = (width * 0.55, depth * 0.55, height * 0.15)
    
    roof.name = "Roof_Main"
    if mats and 'roof_dark' in mats:
        roof.data.materials.append(mats['roof_dark'])
    
    # 瓦垄（瓦片线条）
    for i in range(int(width / 2)):
        x = -width/2 + i * 2 + 1
        bpy.ops.mesh.primitive_cube_add(size=0.15, location=(x, 0, height + 0.5))
        ridge = bpy.context.active_object
        ridge.scale = (0.1, depth * 0.5, 0.3)
        ridge.name = f"Ridge_{i}"
        if mats and 'roof_yellow' in mats:
            ridge.data.materials.append(mats['roof_yellow'])
    
    # 正脊
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height + height * 0.2))
    main_ridge = bpy.context.active_object
    main_ridge.scale = (width * 0.4, 0.3, 0.4)
    main_ridge.name = "Main_Ridge"
    if mats and 'roof_yellow' in mats:
        main_ridge.data.materials.append(mats['roof_yellow'])
    
    # 脊兽（正吻）
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cone_add(
            vertices=8,
            radius1=0.4,
            depth=0.8,
            location=(side * width * 0.35, 0, height + height * 0.35)
        )
        beast = bpy.context.active_object
        beast.rotation_euler = (math.radians(45) * side, 0, 0)
        beast.name = f"Ridge_Beast_{side}"
        if mats and 'gold' in mats:
            beast.data.materials.append(mats['gold'])

def create_detailed_pillar(x, y, height, diameter=0.35, mats=None):
    """创建精细柱子 - 带柱础和柱头装饰"""
    # 柱础
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=diameter * 1.5,
        depth=0.3,
        location=(x, y, 0.15)
    )
    base = bpy.context.active_object
    base.name = f"Pillar_Base_{x}_{y}"
    if mats and 'white_marble' in mats:
        base.data.materials.append(mats['white_marble'])
    
    # 柱身
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=diameter,
        depth=height,
        location=(x, y, height/2 + 0.3)
    )
    pillar = bpy.context.active_object
    pillar.name = f"Pillar_{x}_{y}"
    if mats and 'red_pillar' in mats:
        pillar.data.materials.append(mats['red_pillar'])
    
    # 柱头
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=diameter * 1.3,
        depth=0.25,
        location=(x, y, height + 0.4)
    )
    capital = bpy.context.active_object
    capital.name = f"Pillar_Capital_{x}_{y}"
    if mats and 'red_pillar' in mats:
        capital.data.materials.append(mats['red_pillar'])
    
    return height + 0.5

def create_hall(name, width=20, depth=14, height=5, mats=None):
    """创建精细殿宇"""
    # 三层须弥座台基
    for i in range(3):
        scale_factor = 3 - i * 0.5
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5 + i * 0.5))
        base = bpy.context.active_object
        base.scale = ((width/2 + 3) * scale_factor/3, (depth/2 + 3) * scale_factor/3, 0.5)
        base.name = f"{name}_Base_{i}"
        if mats and 'marble' in mats:
            base.data.materials.append(mats['marble'])
    
    # 栏杆
    for side_x in [-1, 1]:
        for j in range(int(width/2) + 1):
            x = side_x * (width/2 + 2)
            y = -depth/2 + j * 2
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.08, depth=0.8, location=(x, y, 1.8))
            post = bpy.context.active_object
            post.name = f"{name}_Railing_{j}"
            if mats and 'white_marble' in mats:
                post.data.materials.append(mats['white_marble'])
    
    # 柱网
    pillar_positions = []
    cols = 6
    rows = 4
    for row in range(rows):
        for col in range(cols):
            x = -width/2 + col * width/(cols-1)
            y = -depth/2 + row * depth/(rows-1)
            if row == 0 or row == rows-1 or col == 0 or col == cols-1:
                pillar_top = create_detailed_pillar(x, y, height, mats=mats)
                pillar_positions.append((x, y, pillar_top))
    
    # 额枋和雀替
    for row_y in [-depth/2, depth/2]:
        for i in range(cols-1):
            x1 = -width/2 + i * width/(cols-1)
            x2 = -width/2 + (i+1) * width/(cols-1)
            x_mid = (x1 + x2) / 2
            
            # 额枋
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x_mid, row_y, height + 0.3))
            beam = bpy.context.active_object
            beam.scale = ((x2-x1)/2, 0.15, 0.2)
            beam.name = f"{name}_Beam_{row_y}_{i}"
            if mats and 'red_pillar' in mats:
                beam.data.materials.append(mats['red_pillar'])
            
            # 雀替（装饰托架）
            for side in [-1, 1]:
                bpy.ops.mesh.primitive_cube_add(size=0.3, location=(x1 + 0.3 * side, row_y, height + 0.15))
                bracket = bpy.context.active_object
                bracket.scale = (1, 0.5, 0.8)
                bracket.name = f"{name}_Bracket_{row_y}_{i}_{side}"
                if mats and 'gold' in mats:
                    bracket.data.materials.append(mats['gold'])
    
    # 斗拱层
    for x, y, z in pillar_positions:
        create_dougong(x, y, z, size=0.25, mats=mats)
    
    # 屋顶
    create_roof_tiles(width, depth, height + 1, mats, roof_type='hip')
    
    # 藻井（简化）
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=width * 0.2,
        depth=0.1,
        location=(0, 0, height - 0.1)
    )
    ceiling = bpy.context.active_object
    ceiling.name = f"{name}_Ceiling"
    if mats and 'gold' in mats:
        ceiling.data.materials.append(mats['gold'])

def create_detailed_tree(name, x, y, height=10, mats=None):
    """创建精细树木 - 带树皮纹理和多层树叶"""
    # 主树干
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.4,
        depth=height * 0.5,
        location=(x, y, height * 0.25)
    )
    trunk = bpy.context.active_object
    trunk.name = f"{name}_Trunk"
    if mats and 'wood' in mats:
        trunk.data.materials.append(mats['wood'])
    
    # 主分枝
    num_main_branches = random.randint(4, 6)
    for i in range(num_main_branches):
        angle = (i / num_main_branches) * math.pi * 2 + random.uniform(-0.3, 0.3)
        branch_length = height * 0.6
        branch_start_z = height * 0.4 + random.uniform(0, height * 0.15)
        
        # 分枝
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.15,
            depth=branch_length,
            location=(x + math.cos(angle) * branch_length * 0.3,
                     y + math.sin(angle) * branch_length * 0.3,
                     branch_start_z + branch_length * 0.3)
        )
        branch = bpy.context.active_object
        branch.rotation_euler = (math.radians(65) + random.uniform(-0.15, 0.15), 0, angle + math.pi/2)
        branch.name = f"{name}_Branch_{i}"
        if mats and 'wood' in mats:
            branch.data.materials.append(mats['wood'])
        
        # 小分枝
        for j in range(random.randint(2, 4)):
            sub_angle = angle + random.uniform(-0.5, 0.5)
            sub_length = branch_length * 0.4
            
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=6,
                radius=0.05,
                depth=sub_length,
                location=(x + math.cos(angle) * branch_length * 0.5 + math.cos(sub_angle) * sub_length * 0.3,
                         y + math.sin(angle) * branch_length * 0.5 + math.sin(sub_angle) * sub_length * 0.3,
                         branch_start_z + branch_length * 0.5 + sub_length * 0.3)
            )
            sub_branch = bpy.context.active_object
            sub_branch.rotation_euler = (math.radians(60), 0, sub_angle + math.pi/2)
            sub_branch.name = f"{name}_SubBranch_{i}_{j}"
            if mats and 'wood' in mats:
                sub_branch.data.materials.append(mats['wood'])
    
    # 多层叶簇
    for layer in range(3):
        layer_z = height * 0.5 + layer * height * 0.15
        num_leaves = random.randint(5, 8)
        for k in range(num_leaves):
            leaf_angle = random.uniform(0, math.pi * 2)
            leaf_dist = random.uniform(1, 3 - layer * 0.5)
            leaf_x = x + math.cos(leaf_angle) * leaf_dist
            leaf_y = y + math.sin(leaf_angle) * leaf_dist
            leaf_z = layer_z + random.uniform(-0.5, 0.5)
            leaf_size = random.uniform(1.5, 2.5) - layer * 0.3
            
            bpy.ops.mesh.primitive_ico_sphere_add(
                subdivisions=3,
                radius=leaf_size,
                location=(leaf_x, leaf_y, leaf_z)
            )
            leaves = bpy.context.active_object
            leaves.scale = (
                random.uniform(0.8, 1.3),
                random.uniform(0.8, 1.3),
                random.uniform(0.5, 0.9)
            )
            leaves.name = f"{name}_Leaves_{layer}_{k}"
            mat_choice = random.choice(['grass', 'grass_dark']) if mats else None
            if mats and mat_choice in mats:
                leaves.data.materials.append(mats[mat_choice])

def create_ground_plane(size=200, mats=None):
    """创建地面"""
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, -0.01))
    ground = bpy.context.active_object
    ground.name = "Ground"
    if mats and 'grass' in mats:
        ground.data.materials.append(mats['grass'])

def create_water_plane(width=100, depth=60, mats=None):
    """创建水面"""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -10, 0.01))
    water = bpy.context.active_object
    water.scale = (width/2, depth/2, 1)
    water.name = "Water"
    if mats and 'water' in mats:
        water.data.materials.append(mats['water'])
    
    # 添加Ocean Modifier
    mod = water.modifiers.new(name="Ocean", type='OCEAN')
    mod.geometry_mode = 'GENERATE'
    mod.repeat_x = 2
    mod.repeat_y = 2
    mod.resolution = 12
    mod.spatial_size = 50
    mod.wave_scale = 0.3
    mod.wave_scale_min = 0.1
    mod.choppiness = 1.0

def create_stone_path(start_x, start_y, end_x, end_y, width=2, mats=None):
    """创建石板路"""
    length = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
    num_stones = int(length / 1.5)
    
    for i in range(num_stones):
        t = i / num_stones
        x = start_x + (end_x - start_x) * t + random.uniform(-0.3, 0.3)
        y = start_y + (end_y - start_y) * t + random.uniform(-0.3, 0.3)
        
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(x, y, 0.05)
        )
        stone = bpy.context.active_object
        stone.scale = (random.uniform(0.6, 1.0), random.uniform(0.6, 1.0), 0.05)
        stone.rotation_euler = (0, 0, random.uniform(0, math.pi))
        stone.name = f"Stone_{i}"
        if mats and 'stone_path' in mats:
            stone.data.materials.append(mats['stone_path'])

def create_bridge(x, y, width=6, length=15, mats=None):
    """创建拱桥"""
    # 桥面
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 1.5))
    bridge = bpy.context.active_object
    bridge.scale = (width/2, length/2, 0.3)
    bridge.name = "Bridge_Deck"
    if mats and 'white_marble' in mats:
        bridge.data.materials.append(mats['marble'])
    
    # 拱形支撑
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_torus_add(
            major_radius=width/2 + 0.5,
            minor_radius=0.2,
            location=(x, y + side * length/2 * 0.8, 0.5)
        )
        arch = bpy.context.active_object
        arch.rotation_euler = (math.radians(90), 0, 0)
        arch.scale = (1, 1, 0.8)
        arch.name = f"Bridge_Arch_{side}"
        if mats and 'marble' in mats:
            arch.data.materials.append(mats['marble'])
    
    # 栏杆
    for side_z in [-1, 1]:
        for i in range(int(length / 2) + 1):
            rail_y = y - length/2 + i * 2
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=6,
                radius=0.08,
                depth=1.0,
                location=(x + side_z * width/2 * 0.8, rail_y, 2.2)
            )
            post = bpy.context.active_object
            post.name = f"Bridge_Post_{side_z}_{i}"
            if mats and 'white_marble' in mats:
                post.data.materials.append(mats['marble'])

def create_rock_formation(x, y, size=2, mats=None):
    """创建假山石"""
    num_rocks = random.randint(3, 6)
    for i in range(num_rocks):
        rock_size = size * random.uniform(0.4, 1.0)
        offsetX = random.uniform(-size, size)
        offsetY = random.uniform(-size, size)
        offsetZ = rock_size * 0.3
        
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2,
            radius=rock_size,
            location=(x + offsetX, y + offsetY, offsetZ)
        )
        rock = bpy.context.active_object
        rock.scale = (
            random.uniform(0.6, 1.2),
            random.uniform(0.6, 1.2),
            random.uniform(0.5, 1.0)
        )
        rock.name = f"Rock_{x}_{y}_{i}"
        if mats and 'rock' in mats:
            rock.data.materials.append(mats['rock'])

def create_scenic_area():
    """创建完整景区"""
    mats = create_materials()
    
    # 地面
    create_ground_plane(size=300, mats=mats)
    
    # 水面
    create_water_plane(width=120, depth=80, mats=mats)
    
    # 正大光明殿（主殿）
    create_hall("Main_Hall", width=24, depth=16, height=6, mats=mats)
    
    # 偏殿
    for side in [-1, 1]:
        create_hall(f"Side_Hall_{side}", width=14, depth=10, height=4, mats=mats)
        bpy.context.active_object.location = (side * 40, -10, 0)
    
    # 亭子
    for i in range(3):
        angle = i * math.pi * 2 / 3 + math.pi / 6
        px = math.cos(angle) * 35
        py = math.sin(angle) * 35 - 20
        
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=3, depth=0.2, location=(px, py, 0.1))
        pav_base = bpy.context.active_object
        pav_base.name = f"Pavilion_Base_{i}"
        if mats and 'marble' in mats:
            pav_base.data.materials.append(mats['marble'])
        
        create_detailed_pillar(px, py, 3.5, diameter=0.2, mats=mats)
        
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=4, depth=2, location=(px, py, 5.5))
        pav_roof = bpy.context.active_object
        pav_roof.name = f"Pavilion_Roof_{i}"
        if mats and 'roof_yellow' in mats:
            pav_roof.data.materials.append(mats['roof_yellow'])
    
    # 桥梁
    create_bridge(x=0, y=-35, width=5, length=12, mats=mats)
    
    # 石板路
    create_stone_path(0, -8, 0, -25, width=2.5, mats=mats)
    create_stone_path(-20, -10, -10, -25, width=2, mats=mats)
    create_stone_path(20, -10, 10, -25, width=2, mats=mats)
    
    # 树木
    tree_positions = [
        (-30, 20), (-35, 30), (30, 25), (35, 35),
        (-40, 0), (40, 5), (-25, 40), (25, 45),
        (-50, -20), (50, -15), (-45, 10), (45, 15),
        (-60, 30), (60, 25), (-55, -30), (55, -25),
        (-70, 0), (70, 5), (-65, 40), (65, 45)
    ]
    for i, (tx, ty) in enumerate(tree_positions):
        height = random.uniform(8, 14)
        create_detailed_tree(f"Tree_{i}", tx, ty, height=height, mats=mats)
    
    # 假山
    rock_positions = [(-25, 30), (25, 35), (-30, -30), (35, -25), (0, 45)]
    for i, (rx, ry) in enumerate(rock_positions):
        create_rock_formation(rx, ry, size=random.uniform(2, 4), mats=mats)
    
    # 草地粒子（用小球体模拟）
    for _ in range(200):
        gx = random.uniform(-80, 80)
        gy = random.uniform(-60, 60)
        
        # 检查是否在水面区域
        if abs(gy + 10) < 35 and abs(gx) < 55:
            continue
        
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1,
            radius=random.uniform(0.1, 0.3),
            location=(gx, gy, random.uniform(0.05, 0.15))
        )
        grass = bpy.context.active_object
        grass.scale = (1, 1, random.uniform(0.5, 1.5))
        grass.name = f"Grass_{_}"
        mat_choice = random.choice(['grass', 'grass_dark']) if mats else None
        if mats and mat_choice in mats:
            grass.data.materials.append(mats[mat_choice])

def setup_lighting():
    """设置灯光"""
    # 太阳光
    bpy.ops.object.light_add(type='SUN', location=(50, -50, 100))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.98, 0.95)
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))
    
    # 补光
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 30))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 500
    fill.data.size = 50
    fill.data.color = (0.9, 0.95, 1.0)
    
    # 环境光
    bpy.context.scene.world.use_nodes = True
    world_nodes = bpy.context.scene.world.node_tree.nodes
    world_nodes.clear()
    
    bg = world_nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.4, 0.5, 0.7, 1.0)
    bg.inputs['Strength'].default_value = 0.3
    
    output = world_nodes.new('ShaderNodeOutputWorld')
    bpy.context.scene.world.node_tree.links.new(bg.outputs['Background'], output.inputs['Surface'])

def setup_camera():
    """设置相机"""
    bpy.ops.object.camera_add(location=(80, -80, 50))
    camera = bpy.context.active_object
    camera.name = "Main_Camera"
    camera.rotation_euler = (math.radians(65), 0, math.radians(45))
    camera.data.lens = 35
    bpy.context.scene.camera = camera

def export_glb():
    """导出GLB"""
    # 选择所有网格对象
    bpy.ops.object.select_all(action='SELECT')
    
    # 导出
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        use_selection=True,
        export_format='GLB',
        export_apply=True,
        export_materials='EXPORT',
        export_colors=True,
        export_normals=True,
        export_texcoords=True,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6
    )
    print(f"导出完成: {OUTPUT_GLB}")

def main():
    """主函数"""
    print("开始构建超精细圆明园场景...")
    
    clear_scene()
    create_scenic_area()
    setup_lighting()
    setup_camera()
    export_glb()
    
    print("超精细场景构建完成!")

if __name__ == "__main__":
    main()