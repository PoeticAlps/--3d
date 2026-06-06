"""
圆明园大水法（Grand Waterworks）完整3D场景 Blender Python脚本
Blender 5.1.1 - Cycles CPU渲染
"""

import bpy
import math
import os

# ============================================================
# 0. 清理场景
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=False)

scene = bpy.context.scene

# 删除所有默认对象
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ============================================================
# 1. 渲染设置
# ============================================================
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '16'

# 输出路径
output_dir = "/Users/saint/Desktop/WX hermes workspace/yuanmingyuan-3d/output"
os.makedirs(output_dir, exist_ok=True)
scene.render.filepath = os.path.join(output_dir, "dashuifa_complete.png")

# 色彩管理
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - High Contrast'
except:
    try:
        scene.view_settings.look = 'High Contrast'
    except:
        pass

# 世界背景 - 黑色
world = bpy.data.worlds.get("World")
if world is None:
    world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg is None:
    for node in world.node_tree.nodes:
        if node.type == 'BACKGROUND':
            bg = node
            break
if bg:
    bg.inputs[0].default_value = (0.05, 0.05, 0.05, 1.0)

print("渲染设置完成")

# ============================================================
# 2. 材质创建
# ============================================================

def create_material(name, color, roughness=0.5, metallic=0.0, alpha=1.0, 
                    subsurface=0.0, transmission=0.0, emission_strength=0.0):
    """创建Principled BSDF材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 删除默认节点
    for node in nodes:
        nodes.remove(node)
    
    # 输出节点
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0) if len(color) == 3 else color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Alpha'].default_value = alpha
    
    if subsurface > 0:
        bsdf.inputs['Subsurface Weight'].default_value = subsurface
    if transmission > 0:
        bsdf.inputs['Transmission Weight'].default_value = transmission
    if emission_strength > 0:
        bsdf.inputs['Emission Color'].default_value = (*color, 1.0) if len(color) == 3 else color
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    if alpha < 1.0:
        mat.blend_method = 'BLEND' if hasattr(mat, 'blend_method') else None
    
    return mat


def create_marble_material():
    """大理石材质 - 白色带微纹理"""
    mat = bpy.data.materials.new(name="Marble")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in nodes:
        nodes.remove(node)
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.35
    bsdf.inputs['Metallic'].default_value = 0.0
    
    # 节点纹理坐标
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    # Noise纹理
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, 200)
    noise.inputs['Scale'].default_value = 3.0
    noise.inputs['Detail'].default_value = 6.0
    noise.inputs['Roughness'].default_value = 0.4
    
    # ColorRamp - 白色大理石纹理
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (0, 200)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.85, 0.85, 0.87, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.95, 0.94, 0.93, 1.0)
    
    links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    # 微凹凸
    bump = nodes.new('ShaderNodeBump')
    bump.location = (300, -200)
    bump.inputs['Strength'].default_value = 0.05
    
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_bronze_material():
    """青铜材质 - 铜绿色patina"""
    mat = bpy.data.materials.new(name="Bronze_Patina")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in nodes:
        nodes.remove(node)
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.45
    bsdf.inputs['Metallic'].default_value = 0.9
    
    # Texture Coordinate
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    # Voronoi纹理 - patina效果
    voronoi = nodes.new('ShaderNodeTexVoronoi')
    voronoi.location = (-300, 300)
    voronoi.inputs['Scale'].default_value = 5.0
    voronoi.distance = 'EUCLIDEAN'
    
    # Noise纹理
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, 100)
    noise.inputs['Scale'].default_value = 4.0
    noise.inputs['Detail'].default_value = 5.0
    
    # MixRGB - 混合Voronoi和Noise
    mix = nodes.new('ShaderNodeMixRGB')
    mix.location = (-100, 200)
    mix.blend_type = 'MIX'
    mix.inputs[0].default_value = 0.5
    
    # ColorRamp - 铜绿patina颜色
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (100, 200)
    # 设置三个颜色停靠点
    ramp.color_ramp.elements[0].position = 0.2
    ramp.color_ramp.elements[0].color = (0.15, 0.45, 0.35, 1.0)  # 深绿色patina
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (0.55, 0.35, 0.15, 1.0)  # 青铜色
    # 添加中间停靠点
    ele_mid = ramp.color_ramp.elements.new(0.5)
    ele_mid.color = (0.25, 0.50, 0.30, 1.0)  # 浅绿色patina
    
    links.new(tex_coord.outputs['Object'], voronoi.inputs['Vector'])
    links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])
    links.new(voronoi.outputs['Distance'], mix.inputs['Color1'])
    links.new(noise.outputs['Fac'], mix.inputs['Color2'])
    links.new(mix.outputs['Color'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    # 凹凸
    bump = nodes.new('ShaderNodeBump')
    bump.location = (300, -200)
    bump.inputs['Strength'].default_value = 0.15
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_water_material():
    """水材质 - 透明，IOR 1.333"""
    mat = bpy.data.materials.new(name="Water")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in nodes:
        nodes.remove(node)
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Base Color'].default_value = (0.02, 0.05, 0.15, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.02
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Transmission Weight'].default_value = 0.95
    bsdf.inputs['IOR'].default_value = 1.333
    bsdf.inputs['Alpha'].default_value = 0.7
    
    # Texture Coordinate
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    # Noise纹理 - 波纹
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, 100)
    noise.inputs['Scale'].default_value = 2.0
    noise.inputs['Detail'].default_value = 4.0
    noise.inputs['Roughness'].default_value = 0.5
    
    # Bump
    bump = nodes.new('ShaderNodeBump')
    bump.location = (0, -100)
    bump.inputs['Strength'].default_value = 0.08
    bump.inputs['Distance'].default_value = 0.02
    
    links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    mat.blend_method = 'BLEND' if hasattr(mat, 'blend_method') else None
    
    return mat


def create_stone_material():
    """石材材质 - 灰色，粗糙"""
    mat = bpy.data.materials.new(name="Stone")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in nodes:
        nodes.remove(node)
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (600, 0)
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.8
    bsdf.inputs['Metallic'].default_value = 0.0
    
    # Texture Coordinate
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)
    
    # Noise纹理
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-300, 100)
    noise.inputs['Scale'].default_value = 8.0
    noise.inputs['Detail'].default_value = 6.0
    
    # ColorRamp
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (0, 100)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.35, 0.33, 0.30, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.55, 0.52, 0.48, 1.0)
    
    links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    # 凹凸
    bump = nodes.new('ShaderNodeBump')
    bump.location = (300, -200)
    bump.inputs['Strength'].default_value = 0.3
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


# 创建材质
mat_marble = create_marble_material()
mat_bronze = create_bronze_material()
mat_water = create_water_material()
mat_stone = create_stone_material()
mat_dark_stone = create_material("Dark_Stone", (0.25, 0.23, 0.22), roughness=0.9)

print("材质创建完成")

# ============================================================
# 3. 建模辅助函数
# ============================================================

def add_object(primitive_type, name, location=(0, 0, 0), scale=(1, 1, 1), 
               rotation=(0, 0, 0), material=None, **kwargs):
    """添加基本几何体"""
    if primitive_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    elif primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=kwargs.get('radius', 0.5), 
                                             depth=kwargs.get('depth', 1),
                                             vertices=kwargs.get('vertices', 32),
                                             location=location)
    elif primitive_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=kwargs.get('radius', 0.5),
                                              segments=kwargs.get('segments', 24),
                                              ring_count=kwargs.get('ring_count', 16),
                                              location=location)
    elif primitive_type == 'cone':
        bpy.ops.mesh.primitive_cone_add(radius1=kwargs.get('radius1', 0.5),
                                         radius2=kwargs.get('radius2', 0.0),
                                         depth=kwargs.get('depth', 1),
                                         vertices=kwargs.get('vertices', 32),
                                         location=location)
    elif primitive_type == 'torus':
        bpy.ops.mesh.primitive_torus_add(major_radius=kwargs.get('major_radius', 1),
                                          minor_radius=kwargs.get('minor_radius', 0.2),
                                          major_segments=kwargs.get('major_segments', 48),
                                          minor_segments=kwargs.get('minor_segments', 12),
                                          location=location)
    elif primitive_type == 'plane':
        bpy.ops.mesh.primitive_plane_add(size=kwargs.get('size', 2), location=location)
    elif primitive_type == 'ico_sphere':
        bpy.ops.mesh.primitive_ico_sphere_add(radius=kwargs.get('radius', 0.5),
                                               subdivisions=kwargs.get('subdivisions', 2),
                                               location=location)
    
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler = rotation
    
    if material:
        obj.data.materials.append(material)
    
    bpy.ops.object.shade_smooth()
    bpy.ops.object.select_all(action='DESELECT')
    
    return obj

# ============================================================
# 4. 建筑结构
# ============================================================

print("开始创建建筑结构...")

# --- 4.1 石质基座和台阶 ---
# 主基座 - 宽大的平台
add_object('cube', 'Base_Main', location=(0, 0, -0.25), 
           scale=(10, 4, 0.5), material=mat_stone)

# 前台阶（三级）
for i in range(3):
    z = -0.5 - i * 0.15
    depth = 4 + i * 1.5
    add_object('cube', f'Step_{i+1}', location=(0, depth - 1, z),
               scale=(10 + i * 1.0, 1.5, 0.15), material=mat_stone)

# 侧面台阶
for side in [-1, 1]:
    for i in range(3):
        z = -0.5 - i * 0.15
        add_object('cube', f'SideStep_{side}_{i+1}', location=(side * (10 + i * 0.75), 0, z),
                   scale=(1.5, 4 + i * 1.0, 0.15), material=mat_stone)

print("基座台阶完成")

# --- 4.2 中央石拱门（大拱 + 两侧小拱）---
# 中央大拱 - 拱门顶部曲线用torus模拟
arch_height = 3.5
arch_width = 3.0

# 拱门左侧柱
add_object('cube', 'Arch_Left_Pillar', location=(-arch_width/2 - 0.3, 0, arch_height/2),
           scale=(0.4, 0.4, arch_height/2), material=mat_marble)
# 拱门右侧柱
add_object('cube', 'Arch_Right_Pillar', location=(arch_width/2 + 0.3, 0, arch_height/2),
           scale=(0.4, 0.4, arch_height/2), material=mat_marble)

# 拱门顶部横梁
add_object('cube', 'Arch_Top_Beam', location=(0, 0, arch_height + 0.2),
           scale=(arch_width/2 + 0.8, 0.4, 0.25), material=mat_marble)

# 拱形顶部 - 用半圆柱模拟
add_object('cylinder', 'Arch_Top_Curve', location=(0, 0, arch_height),
           scale=(arch_width/2, 0.4, 0.4),
           rotation=(0, math.pi/2, 0), material=mat_marble)

# 拱门装饰性三角形山墙
add_object('cone', 'Arch_Pediment', location=(0, 0, arch_height + 0.7),
           radius1=2.0, radius2=0.0, depth=1.5, vertices=3,
           scale=(1, 0.3, 0.5), material=mat_marble)

# 两侧小拱
small_arch_height = 2.5
small_arch_width = 1.8

for side in [-1, 1]:
    # 小拱柱子
    add_object('cube', f'SmallArch_Left_{side}', 
               location=(side * 4.5 - small_arch_width/2 - 0.2, 0, small_arch_height/2),
               scale=(0.3, 0.3, small_arch_height/2), material=mat_marble)
    add_object('cube', f'SmallArch_Right_{side}', 
               location=(side * 4.5 + small_arch_width/2 + 0.2, 0, small_arch_height/2),
               scale=(0.3, 0.3, small_arch_height/2), material=mat_marble)
    # 小拱顶部
    add_object('cube', f'SmallArch_Top_{side}', 
               location=(side * 4.5, 0, small_arch_height + 0.1),
               scale=(small_arch_width/2 + 0.5, 0.3, 0.2), material=mat_marble)

print("拱门完成")

# --- 4.3 两侧石柱（科林斯柱式）---
# 科林斯柱：柱础 + 柱身(带凹槽) + 柱头(装饰)
column_positions = [
    (-5.5, 0), (-4, 0), (4, 0), (5.5, 0),
    (-7, 0), (7, 0)
]

for idx, (cx, cy) in enumerate(column_positions):
    # 柱础
    add_object('cylinder', f'Col_Base_{idx}', location=(cx, cy, 0.1),
               radius=0.22, depth=0.2, material=mat_marble)
    # 柱身
    add_object('cylinder', f'Col_Shaft_{idx}', location=(cx, cy, 2.0),
               radius=0.18, depth=3.6, vertices=24, material=mat_marble)
    # 柱头 - 多层装饰
    add_object('cube', f'Col_Capital_Square_{idx}', 
               location=(cx, cy, 3.9), scale=(0.25, 0.25, 0.1), material=mat_marble)
    # 柱头卷曲装饰
    add_object('torus', f'Col_Capital_Torus_{idx}', 
               location=(cx, cy, 4.0),
               major_radius=0.22, minor_radius=0.04,
               major_segments=16, minor_segments=8, material=mat_marble)

print("石柱完成")

# --- 4.4 背景石墙/屏风 ---
# 主背景墙
add_object('cube', 'Background_Wall', location=(0, -3.5, 2.0),
           scale=(9, 0.3, 2.5), material=mat_dark_stone)

# 墙顶部装饰
add_object('cube', 'Wall_Top_Decor', location=(0, -3.5, 4.7),
           scale=(9.5, 0.35, 0.15), material=mat_marble)

# 墙壁浮雕装饰（简化为小方块阵列）
for i in range(-6, 7):
    for j in range(3):
        add_object('cube', f'Wall_Ornament_{i}_{j}',
                   location=(i * 1.2, -3.3, 1.0 + j * 1.0),
                   scale=(0.15, 0.1, 0.15), material=mat_marble)

# 侧翼墙壁
for side in [-1, 1]:
    add_object('cube', f'Wing_Wall_{side}',
               location=(side * 9.5, -2, 1.5),
               scale=(0.3, 3, 2), material=mat_dark_stone)

print("背景墙完成")

# ============================================================
# 5. 中央喷泉池
# ============================================================
print("创建喷泉池...")

# 外池壁 - 圆形
pool_radius = 4.5
pool_height = 0.6
add_object('cylinder', 'Pool_Outer', location=(0, 3, pool_height/2 - 0.5),
           radius=pool_radius, depth=pool_height, vertices=48, material=mat_marble)

# 内池壁 - 稍小
add_object('cylinder', 'Pool_Inner', location=(0, 3, pool_height/2 - 0.5),
           radius=pool_radius - 0.3, depth=pool_height + 0.1, vertices=48, material=mat_stone)

# 水面
add_object('cylinder', 'Water_Surface', location=(0, 3, -0.02),
           radius=pool_radius - 0.35, depth=0.05, vertices=48, material=mat_water)

# 池壁顶部装饰环
add_object('torus', 'Pool_Decor_Ring', location=(0, 3, pool_height - 0.5),
           major_radius=pool_radius + 0.05, minor_radius=0.08,
           major_segments=48, minor_segments=8, material=mat_marble)

print("喷泉池完成")

# ============================================================
# 6. 十二生肖兽首喷泉口
# ============================================================
print("创建十二生肖兽首...")

zodiac_names = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"
]

pool_cx, pool_cy = 0, 3
num_animals = 12
pool_r = 3.8  # 兽首距中心距离

for i in range(num_animals):
    angle = (2 * math.pi * i / num_animals) - math.pi / 2
    ax = pool_cx + pool_r * math.cos(angle)
    ay = pool_cy + pool_r * math.sin(angle)
    az = 0.15  # 兽首高度
    
    name = zodiac_names[i]
    
    # 兽首基座 - 方形小台
    add_object('cube', f'{name}_Base', location=(ax, ay, -0.2),
               scale=(0.25, 0.25, 0.4), material=mat_stone)
    
    # 兽首身体 - 球体
    body_radius = 0.22
    add_object('sphere', f'{name}_Body', location=(ax, ay, az),
               radius=body_radius, segments=16, ring_count=12, material=mat_bronze)
    
    # 兽首头部 - 较小球体（微微朝向水池中心）
    head_z = az + 0.28
    # 头部略微朝向水池中心
    dx = pool_cx - ax
    dy = pool_cy - ay
    dist = math.sqrt(dx*dx + dy*dy)
    if dist > 0:
        dx /= dist
        dy /= dist
    
    add_object('sphere', f'{name}_Head', 
               location=(ax + dx * 0.15, ay + dy * 0.15, head_z),
               radius=0.15, segments=16, ring_count=12, material=mat_bronze)
    
    # 嘴部/喷口 - 圆锥，朝向水池中心
    cone_angle = math.atan2(dy, dx)
    add_object('cone', f'{name}_Mouth',
               location=(ax + dx * 0.35, ay + dy * 0.35, head_z - 0.05),
               radius1=0.06, radius2=0.0, depth=0.2, vertices=12,
               rotation=(0, 0, cone_angle), material=mat_bronze)
    
    # 耳朵 - 两个小锥体（简化）
    for ear_side in [-1, 1]:
        ear_x = ax + dx * 0.1 + ear_side * 0.08 * (-dy)
        ear_y = ay + dy * 0.1 + ear_side * 0.08 * dx
        add_object('cone', f'{name}_Ear_{ear_side}',
                   location=(ear_x, ear_y, head_z + 0.15),
                   radius1=0.04, radius2=0.0, depth=0.1, vertices=8,
                   material=mat_bronze)
    
    # 喷水效果 - 水柱（半透明圆柱）
    water_x = ax + dx * 0.5
    water_y = ay + dy * 0.5
    add_object('cylinder', f'{name}_WaterJet',
               location=(water_x, water_y, head_z - 0.1),
               radius=0.02, depth=0.8, vertices=8, material=mat_water)

print("十二生肖兽首完成")

# ============================================================
# 7. 中央大喷泉
# ============================================================
print("创建中央喷泉...")

# 中央喷泉基座 - 多层
add_object('cylinder', 'Fountain_Base_1', location=(0, 3, 0.5),
           radius=0.6, depth=0.4, vertices=24, material=mat_marble)
add_object('cylinder', 'Fountain_Base_2', location=(0, 3, 0.9),
           radius=0.4, depth=0.4, vertices=24, material=mat_marble)
add_object('cylinder', 'Fountain_Column', location=(0, 3, 1.8),
           radius=0.15, depth=1.4, vertices=16, material=mat_marble)

# 顶部装饰
add_object('sphere', 'Fountain_Top_Sphere', location=(0, 3, 2.6),
           radius=0.25, segments=16, ring_count=12, material=mat_marble)
add_object('torus', 'Fountain_Top_Ring', location=(0, 3, 2.5),
           major_radius=0.35, minor_radius=0.05,
           major_segments=24, minor_segments=8, material=mat_marble)

# 中央水柱
add_object('cylinder', 'Central_Water_Jet', location=(0, 3, 3.2),
           radius=0.05, depth=1.2, vertices=8, material=mat_water)

# 水花效果 - 多个小球
import random
random.seed(42)
for i in range(20):
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(0.1, 0.5)
    h = random.uniform(2.5, 3.5)
    add_object('sphere', f'Water_Splash_{i}',
               location=(r * math.cos(angle), 3 + r * math.sin(angle), h),
               radius=random.uniform(0.02, 0.06),
               segments=8, ring_count=6, material=mat_water)

print("中央喷泉完成")

# ============================================================
# 8. 灯光系统
# ============================================================
print("创建灯光系统...")

# 主太阳光 - 暖色，45度角
sun_data = bpy.data.lights.new(name="Sun_Main", type='SUN')
sun_data.energy = 3.5
sun_data.color = (1.0, 0.92, 0.8)  # 暖色
sun_data.angle = math.radians(2)  # 软阴影

sun_obj = bpy.data.objects.new("Sun_Main", sun_data)
scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))

# 补光 - 冷色
fill_data = bpy.data.lights.new(name="Fill_Light", type='AREA')
fill_data.energy = 80
fill_data.color = (0.7, 0.8, 1.0)  # 冷色
fill_data.size = 8

fill_obj = bpy.data.objects.new("Fill_Light", fill_data)
scene.collection.objects.link(fill_obj)
fill_obj.location = (12, 5, 8)
fill_obj.rotation_euler = (math.radians(-40), math.radians(-30), math.radians(0))

# 背光
back_data = bpy.data.lights.new(name="Back_Light", type='AREA')
back_data.energy = 40
back_data.color = (1.0, 0.95, 0.85)
back_data.size = 6

back_obj = bpy.data.objects.new("Back_Light", back_data)
scene.collection.objects.link(back_obj)
back_obj.location = (-5, -8, 6)
back_obj.rotation_euler = (math.radians(30), math.radians(10), 0)

# 环境光设置 - 使用渐变天空
world = scene.world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links

# 清除默认节点
for node in nodes:
    nodes.remove(node)

# Sky Texture节点
sky = nodes.new('ShaderNodeTexSky')
sky.location = (-400, 0)
sky.sky_type = 'MULTIPLE_SCATTERING'
sky.sun_elevation = math.radians(55)
sky.sun_rotation = math.radians(45)
sky.turbidity = 2.0
sky.ground_albedo = 0.3

# Background节点
bg_node = nodes.new('ShaderNodeBackground')
bg_node.location = (-100, 0)
bg_node.inputs['Strength'].default_value = 0.8

# Output节点
output = nodes.new('ShaderNodeOutputWorld')
output.location = (100, 0)

links.new(sky.outputs['Color'], bg_node.inputs['Color'])
links.new(bg_node.outputs['Background'], output.inputs['Surface'])

print("灯光系统完成")

# ============================================================
# 9. 地面
# ============================================================
print("创建地面...")

add_object('plane', 'Ground', location=(0, 3, -0.65),
           scale=(25, 25, 1), material=mat_stone)

# 装饰性铺地
for i in range(-8, 9):
    for j in range(-3, 8):
        if (i + j) % 2 == 0:
            add_object('cube', f'Paving_{i}_{j}',
                       location=(i * 1.1, j * 1.1, -0.62),
                       scale=(0.52, 0.52, 0.02), material=mat_marble)

print("地面完成")

# ============================================================
# 10. 摄像机
# ============================================================
print("创建摄像机...")

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35  # 35mm广角
cam_data.clip_start = 0.1
cam_data.clip_end = 200

cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)

# 正面略偏左45度俯视角度
cam_obj.location = (-14, 12, 10)
# 看向场景中心偏前
direction = (3 - cam_obj.location.x, 3 - cam_obj.location.y, 1 - cam_obj.location.z)
# 计算朝向
import mathutils
target = mathutils.Vector((2, 3, 1.5))
cam_loc = mathutils.Vector(cam_obj.location)
direction = target - cam_loc
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

scene.camera = cam_obj

print("摄像机设置完成")

# ============================================================
# 11. 添加装饰细节
# ============================================================
print("添加装饰细节...")

# 花瓶装饰 - 在拱门两侧
for side in [-1, 1]:
    for i in range(2):
        vx = side * (2 + i * 1.5)
        vy = -1
        add_object('cylinder', f'Vase_{side}_{i}', 
                   location=(vx, vy, 0.8),
                   radius=0.12, depth=0.6, vertices=16, material=mat_marble)
        add_object('sphere', f'Vase_Top_{side}_{i}',
                   location=(vx, vy, 1.2),
                   radius=0.14, segments=12, ring_count=8, material=mat_marble)

# 顶部雕塑装饰 - 拱门上方
for i in range(5):
    sx = (i - 2) * 1.5
    sy = -2.5
    add_object('cone', f'Roof_Sculpture_{i}',
               location=(sx, sy, 4.8),
               radius1=0.15, radius2=0.0, depth=0.5, vertices=8,
               material=mat_marble)

# 侧面石狮/装饰物
for side in [-1, 1]:
    lx = side * 8
    ly = -2
    add_object('cube', f'Lion_Base_{side}', location=(lx, ly, -0.2),
               scale=(0.3, 0.3, 0.3), material=mat_stone)
    add_object('sphere', f'Lion_Body_{side}', location=(lx, ly, 0.3),
               radius=0.25, segments=12, ring_count=8, material=mat_stone)
    add_object('sphere', f'Lion_Head_{side}', location=(lx, ly + 0.15, 0.55),
               radius=0.18, segments=12, ring_count=8, material=mat_stone)

print("装饰细节完成")

# ============================================================
# 12. 场景优化和渲染
# ============================================================
print("场景优化中...")

# 确保所有对象都是smooth shading
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.shade_smooth()
        except:
            pass
        obj.select_set(False)

# 设置视口采样（性能优化）
scene.cycles.preview_samples = 16

print(f"场景对象总数: {len(bpy.data.objects)}")
print(f"场景网格数: {len(bpy.data.meshes)}")
print(f"材质数: {len(bpy.data.materials)}")

# ============================================================
# 13. 渲染
# ============================================================
print("=" * 50)
print("开始渲染大水法场景...")
print(f"输出路径: {scene.render.filepath}")
print(f"分辨率: {scene.render.resolution_x}x{scene.render.resolution_y}")
print(f"采样数: {scene.cycles.samples}")
print(f"渲染引擎: Cycles CPU")
print("=" * 50)

bpy.ops.render.render(write_still=True)

print("=" * 50)
print("渲染完成！")
print(f"输出文件: {scene.render.filepath}")
print("=" * 50)
