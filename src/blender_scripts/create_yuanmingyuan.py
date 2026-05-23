"""
圆明园数字重建 - Blender自动化建模脚本

直接运行生成完整的圆明园场景，无需手动操作
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector

# ============================================================
# 清空场景
# ============================================================
def clear_scene():
    """清空默认场景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # 清空材质
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    
    # 清空网格
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

# ============================================================
# 材质创建
# ============================================================
def create_material(name, color, roughness=0.5, metallic=0.0):
    """创建材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    # Blender 5.x 兼容性：找到 Principled BSDF 节点
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
    """创建所有材质"""
    materials = {}
    
    # 白色大理石
    materials['marble'] = create_material(
        "Marble_White",
        (0.95, 0.93, 0.88, 1.0),
        roughness=0.3,
        metallic=0.0
    )
    
    # 红色柱子
    materials['red_pillar'] = create_material(
        "Red_Pillar",
        (0.7, 0.15, 0.1, 1.0),
        roughness=0.6
    )
    
    # 金色装饰
    materials['gold'] = create_material(
        "Gold",
        (0.85, 0.65, 0.2, 1.0),
        roughness=0.3,
        metallic=0.9
    )
    
    # 深色屋顶
    materials['roof_dark'] = create_material(
        "Roof_Dark",
        (0.15, 0.15, 0.18, 1.0),
        roughness=0.7
    )
    
    # 琉璃瓦（黄色）
    materials['roof_yellow'] = create_material(
        "Roof_Yellow",
        (0.85, 0.7, 0.2, 1.0),
        roughness=0.4,
        metallic=0.1
    )
    
    # 木质
    materials['wood'] = create_material(
        "Wood",
        (0.4, 0.25, 0.15, 1.0),
        roughness=0.8
    )
    
    # 水面
    mat_water = bpy.data.materials.new(name="Water")
    mat_water.use_nodes = True
    nodes = mat_water.node_tree.nodes
    # 找到或创建 Principled BSDF 节点
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
    elif 'Transmission' in bsdf.inputs:
        bsdf.inputs['Transmission'].default_value = 0.9
    materials['water'] = mat_water
    
    # 草地
    materials['grass'] = create_material(
        "Grass",
        (0.2, 0.45, 0.15, 1.0),
        roughness=0.9
    )
    
    return materials

# ============================================================
# 建筑构建
# ============================================================
def create_base_platform(size=(20, 15, 0.5), location=(0, 0, 0)):
    """创建建筑基座"""
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(location[0], location[1], location[2] + size[2]/2)
    )
    base = bpy.context.active_object
    base.scale = (size[0], size[1], size[2])
    base.name = "Base_Platform"
    return base

def create_pillar(height=4, radius=0.3, location=(0, 0, 0)):
    """创建柱子"""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=radius,
        depth=height,
        location=(location[0], location[1], location[2] + height/2)
    )
    pillar = bpy.context.active_object
    pillar.name = "Pillar"
    return pillar

def create_pillars_grid(rows=4, cols=6, spacing_x=3, spacing_y=2.5, height=4, radius=0.3):
    """创建柱子网格"""
    pillars = []
    start_x = -(cols - 1) * spacing_x / 2
    start_y = -(rows - 1) * spacing_y / 2
    
    for i in range(rows):
        for j in range(cols):
            x = start_x + j * spacing_x
            y = start_y + i * spacing_y
            pillar = create_pillar(height=height, radius=radius, location=(x, y, 0.5))
            pillars.append(pillar)
    return pillars

def create_roof(width=22, depth=17, height=3, location=(0, 0, 7)):
    """创建中国传统屋顶"""
    # 主体屋顶
    bpy.ops.mesh.primitive_cone_add(
        vertices=4,
        radius1=max(width, depth) * 0.7,
        depth=height,
        location=(location[0], location[1], location[2] + height/2)
    )
    roof = bpy.context.active_object
    roof.scale = (width/15, depth/12, height/3)
    roof.name = "Roof_Main"
    
    # 屋顶翘角
    bpy.ops.mesh.primitive_cone_add(
        vertices=4,
        radius1=max(width, depth) * 0.8,
        depth=height * 0.3,
        location=(location[0], location[1], location[2] + height * 1.2)
    )
    roof_top = bpy.context.active_object
    roof_top.scale = (width/18, depth/14, height/4)
    roof_top.name = "Roof_Top"
    
    return [roof, roof_top]

def create_danbi():
    """创建丹陛（台阶中间的龙纹石雕）"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -7, 0.3))
    danbi = bpy.context.active_object
    danbi.scale = (1.5, 3, 0.3)
    danbi.name = "Danbi"
    return danbi

def create_stairs(steps=5, width=4, depth=0.3, height=0.15, location=(0, 0, 0)):
    """创建台阶"""
    stairs = []
    for i in range(steps):
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(
                location[0],
                location[1] + i * depth,
                location[2] + i * height + height/2
            )
        )
        stair = bpy.context.active_object
        stair.scale = (width/2, depth/2, height/2)
        stair.name = f"Stair_{i}"
        stairs.append(stair)
    return stairs

def create_hall(name="Main_Hall", width=18, depth=12, height=4):
    """创建大殿"""
    hall_parts = []
    
    # 基座
    base = create_base_platform(
        size=(width + 2, depth + 2, 0.8),
        location=(0, 0, 0)
    )
    base.name = f"{name}_Base"
    hall_parts.append(base)
    
    # 柱子
    pillars = create_pillars_grid(
        rows=3,
        cols=5,
        spacing_x=width/5,
        spacing_y=depth/3,
        height=height,
        radius=0.25
    )
    for p in pillars:
        p.name = f"{name}_Pillar"
    hall_parts.extend(pillars)
    
    # 屋顶
    roofs = create_roof(
        width=width + 4,
        depth=depth + 4,
        height=height * 0.8,
        location=(0, 0, height + 0.8)
    )
    for r in roofs:
        r.name = f"{name}_Roof"
    hall_parts.extend(roofs)
    
    # 台阶
    stairs = create_stairs(
        steps=4,
        width=3,
        location=(0, -depth/2 - 1.5, 0.8)
    )
    for s in stairs:
        s.name = f"{name}_Stair"
    hall_parts.extend(stairs)
    
    return hall_parts

# ============================================================
# 西洋楼 - 大水法
# ============================================================
def create_dashuifa():
    """创建大水法（西洋楼风格）"""
    parts = []
    
    # 石柱（罗马柱风格）
    column_positions = [
        (-4, 0), (-2, 0), (0, 0), (2, 0), (4, 0),
        (-3, 3), (-1, 3), (1, 3), (3, 3),
        (-3, -3), (-1, -3), (1, -3), (3, -3)
    ]
    
    for i, (x, y) in enumerate(column_positions):
        # 柱身
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12,
            radius=0.25,
            depth=5,
            location=(x, y, 2.5)
        )
        column = bpy.context.active_object
        column.name = f"Dashuifa_Column_{i}"
        parts.append(column)
        
        # 柱头装饰
        bpy.ops.mesh.primitive_cube_add(
            size=0.8,
            location=(x, y, 5.2)
        )
        capital = bpy.context.active_object
        capital.name = f"Dashuifa_Capital_{i}"
        parts.append(capital)
    
    # 中央拱门
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 4))
    arch_top = bpy.context.active_object
    arch_top.scale = (3, 0.5, 0.8)
    arch_top.name = "Dashuifa_Arch_Top"
    parts.append(arch_top)
    
    # 基座
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.3))
    platform = bpy.context.active_object
    platform.scale = (12, 8, 0.3)
    platform.name = "Dashuifa_Platform"
    parts.append(platform)
    
    # 喷泉水池
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=4,
        depth=0.5,
        location=(0, 5, 0.25)
    )
    pool = bpy.context.active_object
    pool.name = "Dashuifa_Pool"
    parts.append(pool)
    
    return parts

# ============================================================
# 环境创建
# ============================================================
def create_water(size=200):
    """创建水面"""
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, -0.3))
    water = bpy.context.active_object
    water.name = "Lake"
    return water

def create_ground(size=300):
    """创建地面/草地"""
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, -0.5))
    ground = bpy.context.active_object
    ground.name = "Ground"
    return ground

def create_mountain(location=(0, 0, 0), scale=(30, 30, 20)):
    """创建假山"""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=location)
    mountain = bpy.context.active_object
    mountain.scale = scale
    mountain.name = "Mountain"
    
    # 添加噪波修改器使其更自然
    mod = mountain.modifiers.new("Displace", 'DISPLACE')
    mod.strength = 3
    
    return mountain

def create_island(location=(0, 0, 0), radius=15):
    """创建岛屿"""
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=2, location=(location[0], location[1], -0.5))
    island = bpy.context.active_object
    island.name = "Island"
    return island

# ============================================================
# 场景布局 - 九州清晏
# ============================================================
def create_jiuzhouqingyan():
    """创建九州清晏（九岛布局）"""
    parts = []
    
    # 中央主岛 - 皇帝寝宫
    island_main = create_island(location=(0, 0, 0), radius=20)
    parts.append(island_main)
    
    hall_main = create_hall(name="Jiuzhou_Main", width=15, depth=10, height=4)
    parts.extend(hall_main)
    
    # 八个方位的岛屿
    island_positions = [
        (50, 0, "East"),      # 东
        (-50, 0, "West"),     # 西
        (0, 50, "North"),     # 北
        (0, -50, "South"),    # 南
        (35, 35, "NE"),       # 东北
        (35, -35, "SE"),      # 东南
        (-35, 35, "NW"),      # 西北
        (-35, -35, "SW"),     # 西南
    ]
    
    for x, y, name in island_positions:
        island = create_island(location=(x, y, 0), radius=12)
        island.name = f"Island_{name}"
        parts.append(island)
        
        # 每个岛上一个小亭子
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=3, depth=0.3, location=(x, y, 0.5))
        pavilion_base = bpy.context.active_object
        pavilion_base.name = f"Pavilion_Base_{name}"
        parts.append(pavilion_base)
        
        # 亭子柱子
        for dx, dy in [(-1.5, -1.5), (1.5, -1.5), (-1.5, 1.5), (1.5, 1.5)]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.15, depth=2.5, location=(x+dx, y+dy, 1.8))
            pillar = bpy.context.active_object
            pillar.name = f"Pavilion_Pillar_{name}"
            parts.append(pillar)
        
        # 亭子屋顶
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=4, depth=1.5, location=(x, y, 3.5))
        roof = bpy.context.active_object
        roof.name = f"Pavilion_Roof_{name}"
        parts.append(roof)
    
    return parts

# ============================================================
# 场景布局 - 方壶胜境
# ============================================================
def create_fangpuxianjing():
    """创建方壶胜境（仙境主题）"""
    parts = []
    
    # 水上平台
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    main_platform = bpy.context.active_object
    main_platform.scale = (25, 20, 0.5)
    main_platform.name = "Fangpu_Platform"
    parts.append(main_platform)
    
    # 主殿
    hall = create_hall(name="Fangpu_Hall", width=12, depth=8, height=5)
    for h in hall:
        h.location.x += 0
        h.location.y += 5
    parts.extend(hall)
    
    # 左右楼阁
    for side_x in [-12, 12]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(side_x, 0, 0.5))
        tower_base = bpy.context.active_object
        tower_base.scale = (4, 4, 0.5)
        tower_base.name = f"Tower_Base_{side_x}"
        parts.append(tower_base)
        
        for floor in range(3):
            bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=3, depth=3, location=(side_x, 0, 2 + floor*3))
            tower_floor = bpy.context.active_object
            tower_floor.name = f"Tower_Floor_{side_x}_{floor}"
            parts.append(tower_floor)
        
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=4, depth=2, location=(side_x, 0, 11))
        tower_roof = bpy.context.active_object
        tower_roof.name = f"Tower_Roof_{side_x}"
        parts.append(tower_roof)
    
    # 桥梁连接
    for bridge_y in [-15, 15]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, bridge_y, 0.3))
        bridge = bpy.context.active_object
        bridge.scale = (2, 8, 0.3)
        bridge.name = f"Bridge_{bridge_y}"
        parts.append(bridge)
    
    return parts

# ============================================================
# 灯光和相机
# ============================================================
def setup_lighting():
    """设置灯光"""
    # 太阳光
    bpy.ops.object.light_add(type='SUN', location=(50, -50, 100))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(45))
    
    # 环境光
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 50))
    ambient = bpy.context.active_object
    ambient.name = "Ambient_Light"
    ambient.data.energy = 1000
    ambient.data.size = 100
    
    return [sun, ambient]

def setup_camera():
    """设置相机"""
    bpy.ops.object.camera_add(location=(120, -100, 60))
    camera = bpy.context.active_object
    camera.name = "Main_Camera"
    camera.rotation_euler = (math.radians(60), 0, math.radians(50))
    bpy.context.scene.camera = camera
    
    return camera

def setup_world():
    """设置世界环境"""
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    
    # 天空
    sky = nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'HOSEK_WILKIE'  # Blender 5.x 兼容
    sky.sun_elevation = math.radians(45)
    if hasattr(sky, 'sun_rotation'):
        sky.sun_rotation = math.radians(45)
    elif hasattr(sky, 'sun_azimuth'):
        sky.sun_azimuth = math.radians(45)
    
    background = nodes.new('ShaderNodeBackground')
    output = nodes.new('ShaderNodeOutputWorld')
    
    world.node_tree.links.new(sky.outputs['Color'], background.inputs['Color'])
    world.node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])

# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("🏛️ 圆明园数字重建 - 开始生成场景")
    print("=" * 60)
    
    # 清空场景
    print("📦 清空场景...")
    clear_scene()
    
    # 创建材质
    print("🎨 创建材质...")
    materials = create_materials()
    
    # 设置环境
    print("🌍 设置环境...")
    setup_world()
    
    # 创建地面和水
    print("🌊 创建水面和地面...")
    water = create_water()
    water.data.materials.append(materials['water'])
    
    ground = create_ground()
    ground.data.materials.append(materials['grass'])
    
    # ==========================================
    # 景区1: 大水法（西洋楼）
    # ==========================================
    print("🏛️ 创建大水法...")
    dashuifa_parts = create_dashuifa()
    for part in dashuifa_parts:
        if "Column" in part.name or "Arch" in part.name:
            part.data.materials.append(materials['marble'])
        elif "Pool" in part.name:
            part.data.materials.append(materials['marble'])
        else:
            part.data.materials.append(materials['marble'])
        part.location.x += 0
        part.location.y += 80  # 移到北边
    
    # ==========================================
    # 景区2: 九州清晏
    # ==========================================
    print("🏝️ 创建九州清晏...")
    jiuzhou_parts = create_jiuzhouqingyan()
    for part in jiuzhou_parts:
        part.location.x += 0
        part.location.y += 0  # 保持在中央
        if "Roof" in part.name:
            part.data.materials.append(materials['roof_yellow'])
        elif "Pillar" in part.name:
            part.data.materials.append(materials['red_pillar'])
        elif "Island" in part.name:
            part.data.materials.append(materials['grass'])
        else:
            part.data.materials.append(materials['marble'])
    
    # ==========================================
    # 景区3: 方壶胜境
    # ==========================================
    print("🏯 创建方壶胜境...")
    fangpu_parts = create_fangpuxianjing()
    for part in fangpu_parts:
        part.location.x += 80  # 移到东边
        if "Roof" in part.name:
            part.data.materials.append(materials['roof_yellow'])
        elif "Tower" in part.name:
            part.data.materials.append(materials['red_pillar'])
        else:
            part.data.materials.append(materials['marble'])
    
    # ==========================================
    # 景区4: 正大光明（正殿）
    # ==========================================
    print("👑 创建正大光明...")
    zhengda_parts = create_hall(name="Zhengda", width=20, depth=14, height=5)
    for part in zhengda_parts:
        part.location.x -= 80  # 移到西边
        if "Roof" in part.name:
            part.data.materials.append(materials['roof_dark'])
        elif "Pillar" in part.name:
            part.data.materials.append(materials['red_pillar'])
        else:
            part.data.materials.append(materials['marble'])
    
    # 添加假山
    print("⛰️ 添加假山...")
    mountain1 = create_mountain(location=(60, -60, 0), scale=(25, 20, 15))
    mountain1.data.materials.append(materials['marble'])
    
    mountain2 = create_mountain(location=(-60, 60, 0), scale=(20, 25, 12))
    mountain2.data.materials.append(materials['marble'])
    
    # 设置灯光
    print("💡 设置灯光...")
    setup_lighting()
    
    # 设置相机
    print("📷 设置相机...")
    setup_camera()
    
    # 渲染设置
    print("⚙️ 配置渲染...")
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    
    print("=" * 60)
    print("✅ 圆明园场景生成完成！")
    print("=" * 60)

# 执行
if __name__ == "__main__":
    main()
