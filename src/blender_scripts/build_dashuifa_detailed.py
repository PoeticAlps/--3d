"""
圆明园大水法精细化建模脚本
包含：
1. 大水法主体建筑（西洋楼巴洛克风格）
2. 十二生肖兽首铜像（动物形象精雕）
3. 喷泉水池系统
4. 观水法平台
"""

import bpy
import bmesh
import math
from mathutils import Vector

# ==================== 清理场景 ====================
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)

# ==================== 材质系统 ====================
def create_materials():
    """创建高质量PBR材质"""
    mats = {}
    
    # 大理石基座
    mats['marble'] = bpy.data.materials.new("Marble")
    mats['marble'].use_nodes = True
    nodes = mats['marble'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.92, 0.89, 0.86, 1)
    principled.inputs['Roughness'].default_value = 0.25
    principled.inputs['Metallic'].default_value = 0.0
    mats['marble'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 铜材质（兽首用）
    mats['bronze'] = bpy.data.materials.new("Bronze")
    mats['bronze'].use_nodes = True
    nodes = mats['bronze'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.65, 0.45, 0.25, 1)
    principled.inputs['Roughness'].default_value = 0.35
    principled.inputs['Metallic'].default_value = 0.9
    mats['bronze'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 风化铜（绿锈）
    mats['patina'] = bpy.data.materials.new("Patina")
    mats['patina'].use_nodes = True
    nodes = mats['patina'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.25, 0.45, 0.35, 1)
    principled.inputs['Roughness'].default_value = 0.6
    principled.inputs['Metallic'].default_value = 0.7
    mats['patina'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 白色石材
    mats['white_stone'] = bpy.data.materials.new("WhiteStone")
    mats['white_stone'].use_nodes = True
    nodes = mats['white_stone'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.85, 0.82, 0.78, 1)
    principled.inputs['Roughness'].default_value = 0.7
    mats['white_stone'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 水材质
    mats['water'] = bpy.data.materials.new("Water")
    mats['water'].use_nodes = True
    nodes = mats['water'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.1, 0.25, 0.35, 1)
    principled.inputs['Roughness'].default_value = 0.05
    principled.inputs['IOR'].default_value = 1.333
    principled.inputs['Transmission Weight'].default_value = 0.95
    mats['water'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return mats

# ==================== 大水法主体 ====================
def create_dashuifa_main(mats):
    """创建大水法主体建筑"""
    # 主基座（三级台阶）
    for i, (w, d, h) in enumerate([(25, 15, 0.5), (23, 13, 0.5), (21, 11, 0.5)]):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i*0.5 + 0.25))
        base = bpy.context.active_object
        base.name = f"Dashuifa_Base_{i}"
        base.scale = (w/2, d/2, h/2)
        bpy.ops.object.transform_apply(scale=True)
        base.data.materials.append(mats['white_stone'])
    
    # 中央拱门
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 3))
    arch = bpy.context.active_object
    arch.name = "Dashuifa_Arch"
    arch.scale = (3, 1.5, 3)
    bpy.ops.object.transform_apply(scale=True)
    arch.data.materials.append(mats['marble'])
    
    # 拱门顶部装饰（巴洛克风格曲线）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=2, location=(0, 0, 6))
    dome = bpy.context.active_object
    dome.name = "Dashuifa_Dome"
    dome.scale = (1.5, 1.5, 0.8)
    bpy.ops.object.transform_apply(scale=True)
    dome.data.materials.append(mats['marble'])
    
    # 两侧塔楼
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=8, location=(side*8, 0, 4))
        tower = bpy.context.active_object
        tower.name = f"Side_Tower_{'L' if side < 0 else 'R'}"
        tower.data.materials.append(mats['marble'])
        
        # 塔楼顶部
        bpy.ops.mesh.primitive_cone_add(radius1=2.5, radius2=0, depth=3, location=(side*8, 0, 9.5))
        top = bpy.context.active_object
        top.name = f"Tower_Top_{'L' if side < 0 else 'R'}"
        top.data.materials.append(mats['white_stone'])
    
    return arch

# ==================== 十二生肖兽首 ====================
def create_rat_head(location, rotation=0):
    """鼠首 - 尖脸、小耳朵、长胡须特征"""
    parts = []
    
    # 头部（椭圆形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=location)
    head = bpy.context.active_object
    head.name = "Rat_Head"
    head.scale = (0.8, 1, 0.9)
    bpy.ops.object.transform_apply(scale=True)
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 尖嘴部
    bpy.ops.mesh.primitive_cone_add(radius1=0.15, radius2=0.05, depth=0.3, 
                                     location=(location[0], location[1]+0.25, location[2]-0.05))
    mouth = bpy.context.active_object
    mouth.name = "Rat_Mouth"
    mouth.rotation_euler = (math.radians(90), 0, 0)
    mouth.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(mouth)
    
    # 小圆耳朵
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, 
                                              location=(location[0]+side*0.2, location[1], location[2]+0.25))
        ear = bpy.context.active_object
        ear.name = f"Rat_Ear_{'L' if side<0 else 'R'}"
        ear.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(ear)
    
    return parts

def create_ox_head(location, rotation=0):
    """牛首 - 宽脸、弯角、鼻环特征"""
    parts = []
    
    # 头部（宽大方形）
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    head = bpy.context.active_object
    head.name = "Ox_Head"
    head.scale = (0.4, 0.5, 0.35)
    bpy.ops.object.transform_apply(scale=True)
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 弯角
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0.02, depth=0.5,
                                         location=(location[0]+side*0.35, location[1]-0.1, location[2]+0.2))
        horn = bpy.context.active_object
        horn.name = f"Ox_Horn_{'L' if side<0 else 'R'}"
        horn.rotation_euler = (math.radians(-20), side*math.radians(30), 0)
        horn.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(horn)
    
    # 鼻子（突出）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, 
                                          location=(location[0], location[1]+0.4, location[2]-0.1))
    nose = bpy.context.active_object
    nose.name = "Ox_Nose"
    nose.scale = (1.2, 0.8, 0.8)
    nose.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(nose)
    
    # 鼻环
    bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.01,
                                      location=(location[0], location[1]+0.5, location[2]-0.15))
    ring = bpy.context.active_object
    ring.name = "Ox_NoseRing"
    ring.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(ring)
    
    return parts

def create_tiger_head(location, rotation=0):
    """虎首 - 宽脸、王字纹、獠牙、圆耳"""
    parts = []
    
    # 头部（宽大圆形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=location)
    head = bpy.context.active_object
    head.name = "Tiger_Head"
    head.scale = (1.1, 1, 1)
    bpy.ops.object.transform_apply(scale=True)
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 吻部突出
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(location[0], location[1]+0.3, location[2]-0.1))
    muzzle = bpy.context.active_object
    muzzle.name = "Tiger_Muzzle"
    muzzle.scale = (0.9, 1.2, 0.8)
    muzzle.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(muzzle)
    
    # 圆耳朵
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, 
                                              location=(location[0]+side*0.28, location[1]-0.1, location[2]+0.3))
        ear = bpy.context.active_object
        ear.name = f"Tiger_Ear_{'L' if side<0 else 'R'}"
        ear.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(ear)
    
    # 獠牙
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cone_add(radius1=0.03, radius2=0, depth=0.12,
                                         location=(location[0]+side*0.1, location[1]+0.35, location[2]-0.2))
        fang = bpy.context.active_object
        fang.name = f"Tiger_Fang_{'L' if side<0 else 'R'}"
        fang.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(fang)
    
    return parts

def create_rabbit_head(location, rotation=0):
    """兔首 - 长耳朵、三瓣嘴"""
    parts = []
    
    # 头部
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=location)
    head = bpy.context.active_object
    head.name = "Rabbit_Head"
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 长耳朵
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.6,
                                             location=(location[0]+side*0.15, location[1]-0.1, location[2]+0.5))
        ear = bpy.context.active_object
        ear.name = f"Rabbit_Ear_{'L' if side<0 else 'R'}"
        ear.rotation_euler = (math.radians(-15), side*math.radians(10), 0)
        ear.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(ear)
    
    # 三瓣嘴（中间凸起）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, 
                                          location=(location[0], location[1]+0.25, location[2]-0.08))
    lip = bpy.context.active_object
    lip.name = "Rabbit_Lip"
    lip.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(lip)
    
    return parts

def create_dragon_head(location, rotation=0):
    """龙首 - 鹿角、蛇身特征、须、鳞片感"""
    parts = []
    
    # 头部（拉长形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=location)
    head = bpy.context.active_object
    head.name = "Dragon_Head"
    head.scale = (0.8, 1.3, 0.9)
    bpy.ops.object.transform_apply(scale=True)
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 鹿角
    for side in [-1, 1]:
        # 主角
        bpy.ops.mesh.primitive_cone_add(radius1=0.06, radius2=0.01, depth=0.5,
                                         location=(location[0]+side*0.2, location[1]-0.15, location[2]+0.35))
        horn = bpy.context.active_object
        horn.name = f"Dragon_Horn_{'L' if side<0 else 'R'}"
        horn.rotation_euler = (math.radians(-30), side*math.radians(20), 0)
        horn.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(horn)
        
        # 分叉
        bpy.ops.mesh.primitive_cone_add(radius1=0.03, radius2=0, depth=0.25,
                                         location=(location[0]+side*0.25, location[1]-0.25, location[2]+0.55))
        tine = bpy.context.active_object
        tine.name = f"Dragon_Tine_{'L' if side<0 else 'R'}"
        tine.rotation_euler = (math.radians(-50), side*math.radians(40), 0)
        tine.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(tine)
    
    # 龙须
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.4,
                                             location=(location[0]+side*0.15, location[1]+0.4, location[2]-0.05))
        whisker = bpy.context.active_object
        whisker.name = f"Dragon_Whisker_{'L' if side<0 else 'R'}"
        whisker.rotation_euler = (math.radians(80), side*math.radians(30), 0)
        whisker.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(whisker)
    
    # 眼睛（突出）
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                              location=(location[0]+side*0.2, location[1]+0.15, location[2]+0.1))
        eye = bpy.context.active_object
        eye.name = f"Dragon_Eye_{'L' if side<0 else 'R'}"
        eye.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(eye)
    
    return parts

def create_snake_head(location, rotation=0):
    """蛇首 - 三角形头、无耳、分叉舌"""
    parts = []
    
    # 头部（三角形效果）
    bpy.ops.mesh.primitive_cone_add(radius1=0.25, radius2=0.15, depth=0.5,
                                     location=location)
    head = bpy.context.active_object
    head.name = "Snake_Head"
    head.rotation_euler = (math.radians(90), 0, 0)
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 眼睛
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                              location=(location[0]+side*0.12, location[1]+0.05, location[2]+0.08))
        eye = bpy.context.active_object
        eye.name = f"Snake_Eye_{'L' if side<0 else 'R'}"
        eye.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(eye)
    
    # 分叉舌
    for side in [-1, 0, 1]:
        if side == 0:
            continue
        bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.15,
                                             location=(location[0]+side*0.03, location[1]+0.28, location[2]-0.02))
        tongue = bpy.context.active_object
        tongue.name = f"Snake_Tongue_{'L' if side<0 else 'R'}"
        tongue.rotation_euler = (math.radians(70), side*math.radians(15), 0)
        tongue.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(tongue)
    
    return parts

def create_horse_head(location, rotation=0):
    """马首 - 长脸、鼻孔大、鬃毛"""
    parts = []
    
    # 头部（拉长形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.32, location=location)
    head = bpy.context.active_object
    head.name = "Horse_Head"
    head.scale = (0.7, 1.4, 1)
    bpy.ops.object.transform_apply(scale=True)
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 颌部
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, 
                                          location=(location[0], location[1]+0.35, location[2]-0.15))
    jaw = bpy.context.active_object
    jaw.name = "Horse_Jaw"
    jaw.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(jaw)
    
    # 大鼻孔
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                              location=(location[0]+side*0.12, location[1]+0.45, location[2]-0.08))
        nostril = bpy.context.active_object
        nostril.name = f" Nostril_{'L' if side<0 else 'R'}"
        nostril.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(nostril)
    
    # 鬃毛（从头顶到颈部）
    for i in range(5):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.2,
                                             location=(location[0], location[1]-0.2+i*0.1, location[2]+0.35))
        hair = bpy.context.active_object
        hair.name = f"Horse_Mane_{i}"
        hair.rotation_euler = (math.radians(60), 0, 0)
        hair.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(hair)
    
    # 竖耳朵
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cone_add(radius1=0.06, radius2=0.02, depth=0.2,
                                         location=(location[0]+side*0.15, location[1]-0.2, location[2]+0.35))
        ear = bpy.context.active_object
        ear.name = f"Horse_Ear_{'L' if side<0 else 'R'}"
        ear.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(ear)
    
    return parts

def create_sheep_head(location, rotation=0):
    """羊首 - 卷角、下巴胡须"""
    parts = []
    
    # 头部
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=location)
    head = bpy.context.active_object
    head.name = "Sheep_Head"
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 卷角（螺旋形）
    for side in [-1, 1]:
        # 使用多个小球模拟卷角
        for i in range(6):
            angle = math.radians(i * 50)
            r = 0.1 + i * 0.02
            x = location[0] + side * (0.25 + math.cos(angle) * r)
            y = location[1] + math.sin(angle) * r - 0.1
            z = location[2] + 0.2 - i * 0.03
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(x, y, z))
            curl = bpy.context.active_object
            curl.name = f"Sheep_Horn_{side}_{i}"
            curl.data.materials.append(bpy.data.materials['Bronze'])
            parts.append(curl)
    
    # 下巴胡须
    bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0, depth=0.25,
                                     location=(location[0], location[1]+0.15, location[2]-0.35))
    beard = bpy.context.active_object
    beard.name = "Sheep_Beard"
    beard.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(beard)
    
    return parts

def create_monkey_head(location, rotation=0):
    """猴首 - 桃形脸、圆耳、突出眉骨"""
    parts = []
    
    # 头部（圆形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=location)
    head = bpy.context.active_object
    head.name = "Monkey_Head"
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 面部区域（心形/桃形效果）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, 
                                          location=(location[0], location[1]+0.2, location[2]-0.05))
    face = bpy.context.active_object
    face.name = "Monkey_Face"
    face.scale = (0.9, 0.8, 1)
    face.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(face)
    
    # 圆耳朵
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.03,
                                          location=(location[0]+side*0.3, location[1], location[2]+0.05))
        ear = bpy.context.active_object
        ear.name = f"Monkey_Ear_{'L' if side<0 else 'R'}"
        ear.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(ear)
    
    # 突出眉骨
    bpy.ops.mesh.primitive_cube_add(size=1, location=(location[0], location[1]+0.15, location[2]+0.18))
    brow = bpy.context.active_object
    brow.name = "Monkey_Brow"
    brow.scale = (0.25, 0.08, 0.05)
    brow.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(brow)
    
    return parts

def create_rooster_head(location, rotation=0):
    """鸡首 - 鸡冠、喙、肉垂"""
    parts = []
    
    # 头部
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=location)
    head = bpy.context.active_object
    head.name = "Rooster_Head"
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 鸡冠（锯齿形）
    for i in range(5):
        h = 0.1 + (i % 2) * 0.08
        bpy.ops.mesh.primitive_cone_add(radius1=0.05, radius2=0, depth=h,
                                         location=(location[0], location[1]-0.05+i*0.06, location[2]+0.25+h/2))
        comb = bpy.context.active_object
        comb.name = f"Rooster_Comb_{i}"
        comb.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(comb)
    
    # 喙
    bpy.ops.mesh.primitive_cone_add(radius1=0.06, radius2=0.02, depth=0.2,
                                     location=(location[0], location[1]+0.25, location[2]))
    beak = bpy.context.active_object
    beak.name = "Rooster_Beak"
    beak.rotation_euler = (math.radians(90), 0, 0)
    beak.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(beak)
    
    # 肉垂
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                              location=(location[0]+side*0.08, location[1]+0.15, location[2]-0.2))
        wattle = bpy.context.active_object
        wattle.name = f"Rooster_Wattle_{'L' if side<0 else 'R'}"
        wattle.scale = (0.8, 0.6, 1.5)
        wattle.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(wattle)
    
    # 眼睛
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03,
                                              location=(location[0]+side*0.12, location[1]+0.1, location[2]+0.08))
        eye = bpy.context.active_object
        eye.name = f"Rooster_Eye_{'L' if side<0 else 'R'}"
        eye.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(eye)
    
    return parts

def create_dog_head(location, rotation=0):
    """狗首 - 垂耳、突出口鼻、忠诚表情"""
    parts = []
    
    # 头部
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=location)
    head = bpy.context.active_object
    head.name = "Dog_Head"
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 垂耳
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12,
                                              location=(location[0]+side*0.28, location[1]-0.05, location[2]-0.05))
        ear = bpy.context.active_object
        ear.name = f"Dog_Ear_{'L' if side<0 else 'R'}"
        ear.scale = (0.6, 0.4, 1.5)
        ear.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(ear)
    
    # 口鼻突出
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15,
                                          location=(location[0], location[1]+0.25, location[2]-0.08))
    muzzle = bpy.context.active_object
    muzzle.name = "Dog_Muzzle"
    muzzle.scale = (0.8, 1.2, 0.8)
    muzzle.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(muzzle)
    
    # 鼻子
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                          location=(location[0], location[1]+0.38, location[2]-0.08))
    nose = bpy.context.active_object
    nose.name = "Dog_Nose"
    nose.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(nose)
    
    return parts

def create_pig_head(location, rotation=0):
    """猪首 - 圆脸、大鼻孔、小耳朵"""
    parts = []
    
    # 头部（圆形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=location)
    head = bpy.context.active_object
    head.name = "Pig_Head"
    head.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(head)
    
    # 鼻子（扁圆形突出）
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.1,
                                         location=(location[0], location[1]+0.3, location[2]-0.05))
    snout = bpy.context.active_object
    snout.name = "Pig_Snout"
    snout.rotation_euler = (math.radians(90), 0, 0)
    snout.data.materials.append(bpy.data.materials['Bronze'])
    parts.append(snout)
    
    # 大鼻孔
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03,
                                              location=(location[0]+side*0.06, location[1]+0.38, location[2]-0.05))
        nostril = bpy.context.active_object
        nostril.name = f"Pig_Nostril_{'L' if side<0 else 'R'}"
        nostril.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(nostril)
    
    # 小三角耳朵
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0.02, depth=0.15,
                                         location=(location[0]+side*0.2, location[1]-0.1, location[2]+0.25))
        ear = bpy.context.active_object
        ear.name = f"Pig_Ear_{'L' if side<0 else 'R'}"
        ear.rotation_euler = (math.radians(-20), side*math.radians(20), 0)
        ear.data.materials.append(bpy.data.materials['Bronze'])
        parts.append(ear)
    
    return parts

# ==================== 十二生肖台座 ====================
def create_zodiac_pedestal(location, index, animal_name):
    """创建兽首台座"""
    # 圆形底座
    bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.8,
                                         location=(location[0], location[1], location[2]-0.5))
    pedestal = bpy.context.active_object
    pedestal.name = f"{animal_name}_Pedestal"
    pedestal.data.materials.append(bpy.data.materials['white_stone'])
    
    # 人形身体（简化柱状）
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.2,
                                         location=(location[0], location[1], location[2]+0.4))
    body = bpy.context.active_object
    body.name = f"{animal_name}_Body"
    body.data.materials.append(bpy.data.materials['bronze'])
    
    # 肩部
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.15,
                                         location=(location[0], location[1], location[2]+0.95))
    shoulder = bpy.context.active_object
    shoulder.name = f"{animal_name}_Shoulder"
    shoulder.data.materials.append(bpy.data.materials['bronze'])
    
    return pedestal, body, shoulder

# ==================== 喷泉水池 ====================
def create_fountain_pool(mats):
    """创建中央喷泉水池"""
    # 主水池（椭圆形）
    bpy.ops.mesh.primitive_cylinder_add(radius=8, depth=1, location=(0, 5, -0.5))
    pool = bpy.context.active_object
    pool.name = "Fountain_Pool"
    pool.scale = (1, 1.5, 1)
    pool.data.materials.append(mats['white_stone'])
    
    # 水面
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 5, 0))
    water = bpy.context.active_object
    water.name = "Pool_Water"
    water.scale = (7.5, 11, 1)
    water.data.materials.append(mats['water'])
    
    # 中央喷泉塔
    bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=4, location=(0, 5, 2))
    tower = bpy.context.active_object
    tower.name = "Central_Tower"
    tower.data.materials.append(mats['marble'])
    
    return pool, water

# ==================== 组装场景 ====================
def assemble_dashuifa():
    """组装完整的大水法场景"""
    print("开始创建大水法场景...")
    
    mats = create_materials()
    
    # 创建主体建筑
    print("创建主体建筑...")
    create_dashuifa_main(mats)
    
    # 创建喷泉水池
    print("创建喷泉水池...")
    create_fountain_pool(mats)
    
    # 十二生肖位置（围绕水池弧形排列）
    animals = [
        ('Rat', '鼠', create_rat_head),
        ('Ox', '牛', create_ox_head),
        ('Tiger', '虎', create_tiger_head),
        ('Rabbit', '兔', create_rabbit_head),
        ('Dragon', '龙', create_dragon_head),
        ('Snake', '蛇', create_snake_head),
        ('Horse', '马', create_horse_head),
        ('Sheep', '羊', create_sheep_head),
        ('Monkey', '猴', create_monkey_head),
        ('Rooster', '鸡', create_rooster_head),
        ('Dog', '狗', create_dog_head),
        ('Pig', '猪', create_pig_head),
    ]
    
    print("创建十二生肖兽首...")
    for i, (eng_name, ch_name, create_func) in enumerate(animals):
        # 弧形排列
        angle = math.radians(-90 + i * 15)  # 从左侧开始，间隔15度
        x = math.cos(angle) * 10
        y = math.sin(angle) * 10 + 5
        z = 1.5  # 兽首高度
        
        location = (x, y, z)
        print(f"  创建 {ch_name}首 ({eng_name}) at ({x:.1f}, {y:.1f}, {z:.1f})")
        
        # 创建台座
        create_zodiac_pedestal(location, i, f"Zodiac_{eng_name}")
        
        # 创建兽首
        create_func(location, math.degrees(angle) + 90)
    
    # 设置摄像机和灯光
    print("设置灯光...")
    setup_lighting()
    
    print("设置摄像机...")
    setup_camera()
    
    print("✅ 大水法场景创建完成！")

# ==================== 灯光 ====================
def setup_lighting():
    """设置影视级灯光"""
    # 主光（太阳）
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
    sun = bpy.context.active_object
    sun.name = "Sun_Main"
    sun.data.energy = 5
    sun.data.color = (1, 0.95, 0.9)
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))
    
    # 补光
    bpy.ops.object.light_add(type='AREA', location=(-10, 10, 8))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 500
    fill.data.size = 10
    fill.data.color = (0.8, 0.9, 1)
    
    # 轮廓光
    bpy.ops.object.light_add(type='SPOT', location=(0, -20, 15))
    rim = bpy.context.active_object
    rim.name = "Rim_Light"
    rim.data.energy = 1000
    rim.data.spot_size = math.radians(60)

# ==================== 摄像机 ====================
def setup_camera():
    """设置摄像机"""
    bpy.ops.object.camera_add(location=(25, -25, 15))
    cam = bpy.context.active_object
    cam.name = "Main_Camera"
    cam.data.lens = 35
    
    # 对准场景中心
    constraint = cam.constraints.new(type='TRACK_TO')
    target = bpy.data.objects.new("Camera_Target", None)
    bpy.context.collection.objects.link(target)
    target.location = (0, 5, 3)
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    
    bpy.context.scene.camera = cam

# ==================== 导出 ====================
def export_glb():
    """导出GLB文件"""
    output_path = "//../../output/dashuifa_zodiac.glb"
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_materials='EXPORT',
        export_colors=True,
        export_normals=True
    )
    print(f"✅ 已导出: {output_path}")

# ==================== 主函数 ====================
def main():
    """主执行函数"""
    clear_scene()
    assemble_dashuifa()
    export_glb()
    print("\n" + "="*50)
    print("大水法十二生肖兽首场景已完成！")
    print("="*50)

if __name__ == "__main__":
    main()
