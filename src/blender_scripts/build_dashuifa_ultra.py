"""
大水法十二生肖兽首 - 超精细建模版
每个兽首15-25个部件，包含毛发、皱纹、眼球、鼻孔等细节
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector

# ==================== 超精细材质系统 ====================
def create_advanced_materials():
    """创建超精细PBR材质"""
    mats = {}
    
    # 精细铜材质（带颜色变化）
    mats['bronze_refined'] = bpy.data.materials.new("bronze_refined")
    mats['bronze_refined'].use_nodes = True
    nodes = mats['bronze_refined'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.62, 0.42, 0.22, 1)
    principled.inputs['Roughness'].default_value = 0.32
    principled.inputs['Metallic'].default_value = 0.92
    principled.inputs['Specular IOR Level'].default_value = 0.8
    mats['bronze_refined'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 风化铜（绿锈，多层）
    mats['patina_rich'] = bpy.data.materials.new("patina_rich")
    mats['patina_rich'].use_nodes = True
    nodes = mats['patina_rich'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.22, 0.42, 0.32, 1)
    principled.inputs['Roughness'].default_value = 0.55
    principled.inputs['Metallic'].default_value = 0.75
    mats['patina_rich'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 深色铜（眼睛、鼻孔等）
    mats['bronze_dark'] = bpy.data.materials.new("bronze_dark")
    mats['bronze_dark'].use_nodes = True
    nodes = mats['bronze_dark'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.35, 0.25, 0.15, 1)
    principled.inputs['Roughness'].default_value = 0.4
    principled.inputs['Metallic'].default_value = 0.85
    mats['bronze_dark'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 眼球材质（深色玻璃感）
    mats['eye_glass'] = bpy.data.materials.new("eye_glass")
    mats['eye_glass'].use_nodes = True
    nodes = mats['eye_glass'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.05, 0.03, 0.02, 1)
    principled.inputs['Roughness'].default_value = 0.1
    principled.inputs['Metallic'].default_value = 0.95
    principled.inputs['Specular IOR Level'].default_value = 1.0
    mats['eye_glass'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 白色大理石
    mats['marble_fine'] = bpy.data.materials.new("marble_fine")
    mats['marble_fine'].use_nodes = True
    nodes = mats['marble_fine'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.94, 0.91, 0.88, 1)
    principled.inputs['Roughness'].default_value = 0.22
    principled.inputs['Metallic'].default_value = 0.0
    mats['marble_fine'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 水材质
    mats['water_fine'] = bpy.data.materials.new("water_fine")
    mats['water_fine'].use_nodes = True
    nodes = mats['water_fine'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.08, 0.22, 0.32, 1)
    principled.inputs['Roughness'].default_value = 0.05
    principled.inputs['IOR'].default_value = 1.333
    principled.inputs['Transmission Weight'].default_value = 0.95
    mats['water_fine'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    # 头发/毛发材质
    mats['hair_bronze'] = bpy.data.materials.new("hair_bronze")
    mats['hair_bronze'].use_nodes = True
    nodes = mats['hair_bronze'].node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.55, 0.38, 0.2, 1)
    principled.inputs['Roughness'].default_value = 0.5
    principled.inputs['Metallic'].default_value = 0.88
    mats['hair_bronze'].node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    return mats

# ==================== 工具函数 ====================
def create_eyeball(location, name_prefix, rotation_y=0):
    """创建精细眼球（眼球+瞳孔+高光）"""
    parts = []
    
    # 眼白/眼球主体
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=location)
    eyeball = bpy.context.active_object
    eyeball.name = f"{name_prefix}_Eyeball"
    eyeball.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(eyeball)
    
    # 瞳孔（凹陷效果）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, 
                                          location=(location[0], location[1]+0.025, location[2]))
    pupil = bpy.context.active_object
    pupil.name = f"{name_prefix}_Pupil"
    pupil.data.materials.append(bpy.data.materials['eye_glass'])
    parts.append(pupil)
    
    # 眼睑（上下）
    for y_offset, name in [(0.02, "Upper"), (-0.02, "Lower")]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045,
                                              location=(location[0], location[1], location[2]+y_offset))
        lid = bpy.context.active_object
        lid.name = f"{name_prefix}_{name}Lid"
        lid.scale = (1, 0.5, 0.6 if y_offset > 0 else 0.4)
        lid.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(lid)
    
    # 眉弓/眼眶
    bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.015,
                                      location=(location[0], location[1]-0.01, location[2]))
    brow = bpy.context.active_object
    brow.name = f"{name_prefix}_EyeSocket"
    brow.scale = (1.2, 0.8, 0.6)
    brow.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(brow)
    
    return parts

def create_nostril(location, name_prefix, size=0.025):
    """创建精细鼻孔"""
    parts = []
    
    # 鼻孔凹陷
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size, location=location)
    nostril = bpy.context.active_object
    nostril.name = f"{name_prefix}_Nostril"
    nostril.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nostril)
    
    # 鼻翼
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size*0.8,
                                              location=(location[0]+side*size*1.5, location[1], location[2]))
        wing = bpy.context.active_object
        wing.name = f"{name_prefix}_NoseWing_{side}"
        wing.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(wing)
    
    return parts

def create_ear_inner(location, name_prefix, rotation, is_pointed=False):
    """创建精细耳朵（外耳+内耳+耳道）"""
    parts = []
    
    # 外耳轮廓
    if is_pointed:
        bpy.ops.mesh.primitive_cone_add(radius1=0.12, radius2=0.03, depth=0.15, location=location)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=location)
    outer = bpy.context.active_object
    outer.name = f"{name_prefix}_OuterEar"
    outer.rotation_euler = rotation
    outer.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(outer)
    
    # 内耳凹陷
    inner_loc = (location[0], location[1]+0.02, location[2])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07 if not is_pointed else 0.06, location=inner_loc)
    inner = bpy.context.active_object
    inner.name = f"{name_prefix}_InnerEar"
    inner.rotation_euler = rotation
    inner.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(inner)
    
    # 耳道
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.05,
                                         location=(location[0], location[1]+0.05, location[2]))
    canal = bpy.context.active_object
    canal.name = f"{name_prefix}_EarCanal"
    canal.rotation_euler = (math.radians(90), 0, 0)
    canal.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(canal)
    
    return parts

def create_hair_strand(start_loc, end_loc, name_prefix, index, thickness=0.008):
    """创建单根毛发/鬃毛"""
    direction = Vector(end_loc) - Vector(start_loc)
    length = direction.length
    mid_loc = ((start_loc[0]+end_loc[0])/2, (start_loc[1]+end_loc[1])/2, (start_loc[2]+end_loc[2])/2)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=thickness, depth=length, location=mid_loc)
    strand = bpy.context.active_object
    strand.name = f"{name_prefix}_Hair_{index}"
    
    # 计算旋转
    if length > 0:
        direction.normalize()
        strand.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    
    strand.data.materials.append(bpy.data.materials['hair_bronze'])
    return strand

def create_wrinkle_line(start_loc, end_loc, name_prefix, index):
    """创建皱纹线"""
    direction = Vector(end_loc) - Vector(start_loc)
    length = direction.length
    mid_loc = ((start_loc[0]+end_loc[0])/2, (start_loc[1]+end_loc[1])/2, (start_loc[2]+end_loc[2])/2)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=length, location=mid_loc)
    wrinkle = bpy.context.active_object
    wrinkle.name = f"{name_prefix}_Wrinkle_{index}"
    
    if length > 0:
        direction.normalize()
        wrinkle.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    
    wrinkle.data.materials.append(bpy.data.materials['bronze_dark'])
    return wrinkle

# ==================== 超精细兽首 ====================
def ultra_rat_head(location):
    """超精细鼠首 - 20+部件"""
    parts = []
    
    # 头骨主体
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=location)
    skull = bpy.context.active_object
    skull.name = "Rat_Skull"
    skull.scale = (0.85, 1.05, 0.92)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 颧骨（两侧突出）
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08,
                                              location=(location[0]+side*0.18, location[1]+0.05, location[2]+0.02))
        bone = bpy.context.active_object
        bone.name = f"Rat_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 颌骨
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, 
                                          location=(location[0], location[1]+0.2, location[2]-0.1))
    jaw = bpy.context.active_object
    jaw.name = "Rat_Jaw"
    jaw.scale = (0.7, 1.2, 0.6)
    jaw.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(jaw)
    
    # 上颚/口鼻部
    bpy.ops.mesh.primitive_cone_add(radius1=0.12, radius2=0.05, depth=0.25,
                                     location=(location[0], location[1]+0.3, location[2]))
    snout = bpy.context.active_object
    snout.name = "Rat_Snout"
    snout.rotation_euler = (math.radians(90), 0, 0)
    snout.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(snout)
    
    # 鼻尖
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                          location=(location[0], location[1]+0.45, location[2]))
    nose_tip = bpy.context.active_object
    nose_tip.name = "Rat_NoseTip"
    nose_tip.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nose_tip)
    
    # 鼻孔
    for side in [-1, 1]:
        parts.extend(create_nostril(
            (location[0]+side*0.03, location[1]+0.42, location[2]-0.01),
            f"Rat", size=0.015
        ))
    
    # 眼睛
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.15, location[1]+0.1, location[2]+0.08)
        parts.extend(create_eyeball(eye_loc, f"Rat_{'Left' if side<0 else 'Right'}"))
    
    # 耳朵（大圆薄耳）
    for side in [-1, 1]:
        ear_loc = (location[0]+side*0.22, location[1]-0.08, location[2]+0.25)
        
        # 外耳轮廓
        bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.02,
                                          location=ear_loc)
        outer = bpy.context.active_object
        outer.name = f"Rat_OuterEar_{side}"
        outer.rotation_euler = (math.radians(20), side*math.radians(15), 0)
        outer.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(outer)
        
        # 内耳膜（薄）
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=ear_loc)
        inner = bpy.context.active_object
        inner.name = f"Rat_InnerEar_{side}"
        inner.scale = (1, 0.2, 1)
        inner.rotation_euler = (math.radians(20), side*math.radians(15), 0)
        inner.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(inner)
        
        # 耳道
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.06,
                                             location=(location[0]+side*0.2, location[1]-0.05, location[2]+0.18))
        canal = bpy.context.active_object
        canal.name = f"Rat_EarCanal_{side}"
        canal.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(canal)
    
    # 胡须（每侧3根）
    for i in range(3):
        for side in [-1, 1]:
            start = (location[0]+side*0.08, location[1]+0.38, location[2]-0.02+i*0.02)
            end = (location[0]+side*0.35, location[1]+0.5, location[2]-0.05+i*0.04)
            parts.append(create_hair_strand(start, end, "Rat_Whisker", i+side*3))
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.08,
                                             location=(location[0]+side*0.12, location[1]+0.08, location[2]+0.15))
        brow = bpy.context.active_object
        brow.name = f"Rat_Brow_{side}"
        brow.rotation_euler = (0, math.radians(30*side), math.radians(20))
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    # 额头皱纹
    for i in range(2):
        parts.append(create_wrinkle_line(
            (location[0]-0.08+i*0.08, location[1]+0.02, location[2]+0.2),
            (location[0]-0.08+i*0.08, location[1]-0.05, location[2]+0.22),
            "Rat", i
        ))
    
    return parts

def ultra_ox_head(location):
    """超精细牛首 - 25+部件"""
    parts = []
    
    # 头骨（宽大方形）
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    skull = bpy.context.active_object
    skull.name = "Ox_Skull"
    skull.scale = (0.45, 0.55, 0.4)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 额骨
    bpy.ops.mesh.primitive_cube_add(size=1, location=(location[0], location[1]-0.1, location[2]+0.25))
    forehead = bpy.context.active_object
    forehead.name = "Ox_Forehead"
    forehead.scale = (0.35, 0.15, 0.12)
    forehead.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(forehead)
    
    # 颧骨
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1,
                                              location=(location[0]+side*0.35, location[1], location[2]))
        bone = bpy.context.active_object
        bone.name = f"Ox_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 颌骨
    bpy.ops.mesh.primitive_cube_add(size=1, location=(location[0], location[1]+0.2, location[2]-0.15))
    jaw = bpy.context.active_object
    jaw.name = "Ox_LowerJaw"
    jaw.scale = (0.35, 0.2, 0.15)
    jaw.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(jaw)
    
    # 口鼻部
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2,
                                          location=(location[0], location[1]+0.4, location[2]-0.05))
    muzzle = bpy.context.active_object
    muzzle.name = "Ox_Muzzle"
    muzzle.scale = (1.1, 0.9, 0.7)
    muzzle.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(muzzle)
    
    # 鼻镜（湿润部分）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12,
                                          location=(location[0], location[1]+0.55, location[2]-0.05))
    nose = bpy.context.active_object
    nose.name = "Ox_NosePad"
    nose.scale = (1.3, 0.8, 0.6)
    nose.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nose)
    
    # 鼻孔
    for side in [-1, 1]:
        # 鼻孔凹陷
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                              location=(location[0]+side*0.08, location[1]+0.6, location[2]-0.08))
        nostril = bpy.context.active_object
        nostril.name = f"Ox_Nostril_{side}"
        nostril.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(nostril)
        
        # 鼻翼
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                              location=(location[0]+side*0.15, location[1]+0.52, location[2]-0.05))
        wing = bpy.context.active_object
        wing.name = f"Ox_NoseWing_{side}"
        wing.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(wing)
    
    # 鼻环
    bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.015,
                                      location=(location[0], location[1]+0.62, location[2]-0.12))
    ring = bpy.context.active_object
    ring.name = "Ox_NoseRing"
    ring.rotation_euler = (math.radians(90), 0, 0)
    ring.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(ring)
    
    # 眼睛
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.25, location[1]+0.1, location[2]+0.08)
        parts.extend(create_eyeball(eye_loc, f"Ox_{'Left' if side<0 else 'Right'}"))
    
    # 角（粗壮弯曲）
    for side in [-1, 1]:
        # 角基座
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.15,
                                             location=(location[0]+side*0.25, location[1]-0.15, location[2]+0.35))
        base = bpy.context.active_object
        base.name = f"Ox_HornBase_{side}"
        base.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(base)
        
        # 角主体（弯曲用多段模拟）
        for i in range(4):
            angle = math.radians(i * 15)
            x = location[0] + side * (0.25 + math.sin(angle) * 0.15)
            y = location[1] - 0.2 - i * 0.08
            z = location[2] + 0.45 - i * 0.05
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1-i*0.02, depth=0.12,
                                                 location=(x, y, z))
            segment = bpy.context.active_object
            segment.name = f"Ox_HornSeg_{side}_{i}"
            segment.rotation_euler = (math.radians(-20 + i*10), side*math.radians(15), 0)
            segment.data.materials.append(bpy.data.materials['bronze_refined'])
            parts.append(segment)
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.12,
                                             location=(location[0]+side*0.18, location[1]+0.05, location[2]+0.2))
        brow = bpy.context.active_object
        brow.name = f"Ox_Brow_{side}"
        brow.rotation_euler = (0, math.radians(25*side), math.radians(15))
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    # 额头皱纹
    for i in range(3):
        parts.append(create_wrinkle_line(
            (location[0], location[1]-0.15, location[2]+0.2-i*0.06),
            (location[0], location[1]-0.2, location[2]+0.2-i*0.06),
            "Ox", i
        ))
    
    # 下巴胡须
    bpy.ops.mesh.primitive_cone_add(radius1=0.06, radius2=0, depth=0.15,
                                     location=(location[0], location[1]+0.3, location[2]-0.35))
    beard = bpy.context.active_object
    beard.name = "Ox_Beard"
    beard.data.materials.append(bpy.data.materials['hair_bronze'])
    parts.append(beard)
    
    # 耳朵
    for side in [-1, 1]:
        parts.extend(create_ear_inner(
            (location[0]+side*0.35, location[1]-0.2, location[2]+0.15),
            f"Ox_{'Left' if side<0 else 'Right'}",
            (math.radians(-20), side*math.radians(30), 0),
            is_pointed=True
        ))
    
    return parts

def ultra_tiger_head(location):
    """超精细虎首 - 25+部件"""
    parts = []
    
    # 头骨主体（宽大）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, location=location)
    skull = bpy.context.active_object
    skull.name = "Tiger_Skull"
    skull.scale = (1.15, 1.05, 1.05)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 颧骨（突出）
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12,
                                              location=(location[0]+side*0.32, location[1]+0.1, location[2]+0.02))
        bone = bpy.context.active_object
        bone.name = f"Tiger_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 吻部（突出圆柱形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22,
                                          location=(location[0], location[1]+0.35, location[2]-0.08))
    muzzle = bpy.context.active_object
    muzzle.name = "Tiger_Muzzle"
    muzzle.scale = (0.95, 1.3, 0.85)
    muzzle.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(muzzle)
    
    # 鼻子（皮革质感）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08,
                                          location=(location[0], location[1]+0.52, location[2]-0.05))
    nose = bpy.context.active_object
    nose.name = "Tiger_Nose"
    nose.scale = (1.4, 0.9, 0.7)
    nose.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nose)
    
    # 鼻孔
    for side in [-1, 1]:
        parts.extend(create_nostril(
            (location[0]+side*0.05, location[1]+0.58, location[2]-0.08),
            "Tiger", size=0.025
        ))
    
    # 上唇
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08,
                                              location=(location[0]+side*0.08, location[1]+0.48, location[2]-0.12))
        lip = bpy.context.active_object
        lip.name = f"Tiger_Lip_{side}"
        lip.scale = (0.8, 1.2, 0.6)
        lip.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(lip)
    
    # 獠牙（4颗）
    for front in [-1, 1]:
        for side in [-1, 1]:
            bpy.ops.mesh.primitive_cone_add(radius1=0.03, radius2=0.008, depth=0.15,
                                             location=(location[0]+side*0.06, 
                                                       location[1]+0.5+front*0.04, 
                                                       location[2]-0.22))
            fang = bpy.context.active_object
            fang.name = f"Tiger_Fang_{front}_{side}"
            fang.data.materials.append(bpy.data.materials['bronze_refined'])
            parts.append(fang)
    
    # 小牙齿（下颌）
    for i in range(6):
        bpy.ops.mesh.primitive_cone_add(radius1=0.015, radius2=0, depth=0.05,
                                         location=(location[0]+(i-2.5)*0.04, 
                                                   location[1]+0.52, 
                                                   location[2]-0.2))
        tooth = bpy.context.active_object
        tooth.name = f"Tiger_SmallTooth_{i}"
        tooth.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(tooth)
    
    # 眼睛
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.22, location[1]+0.12, location[2]+0.12)
        parts.extend(create_eyeball(eye_loc, f"Tiger_{'Left' if side<0 else 'Right'}"))
    
    # 圆耳朵
    for side in [-1, 1]:
        ear_loc = (location[0]+side*0.32, location[1]-0.15, location[2]+0.32)
        parts.extend(create_ear_inner(ear_loc, f"Tiger_{'Left' if side<0 else 'Right'}",
                                       (math.radians(15), side*math.radians(20), 0),
                                       is_pointed=False))
        # 耳尖毛簇
        bpy.ops.mesh.primitive_cone_add(radius1=0.02, radius2=0, depth=0.06,
                                         location=(location[0]+side*0.32, location[1]-0.2, location[2]+0.42))
        tuft = bpy.context.active_object
        tuft.name = f"Tiger_EarTuft_{side}"
        tuft.data.materials.append(bpy.data.materials['hair_bronze'])
        parts.append(tuft)
    
    # 眉弓（突出）
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                              location=(location[0]+side*0.18, location[1]+0.1, location[2]+0.22))
        brow = bpy.context.active_object
        brow.name = f"Tiger_Brow_{side}"
        brow.scale = (1.5, 0.6, 0.5)
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    # 额头皱纹
    for i in range(4):
        parts.append(create_wrinkle_line(
            (location[0]-0.12+i*0.08, location[1]-0.05, location[2]+0.28),
            (location[0]-0.12+i*0.08, location[1]-0.1, location[2]+0.3),
            "Tiger", i
        ))
    
    # 胡须（每侧4根，更粗）
    for i in range(4):
        for side in [-1, 1]:
            start = (location[0]+side*0.1, location[1]+0.45, location[2]-0.05+i*0.025)
            end = (location[0]+side*0.45, location[1]+0.6, location[2]-0.08+i*0.03)
            parts.append(create_hair_strand(start, end, "Tiger_Whisker", i+side*4, thickness=0.012))
    
    # 颊部毛簇
    for side in [-1, 1]:
        for i in range(3):
            bpy.ops.mesh.primitive_cone_add(radius1=0.015, radius2=0, depth=0.05,
                                             location=(location[0]+side*0.35, 
                                                       location[1]+0.15+i*0.08, 
                                                       location[2]-0.05+i*0.04))
            fur = bpy.context.active_object
            fur.name = f"Tiger_CheekFur_{side}_{i}"
            fur.rotation_euler = (0, side*math.radians(30), 0)
            fur.data.materials.append(bpy.data.materials['hair_bronze'])
            parts.append(fur)
    
    # 额头"王"字纹（用小方块排列）
    wang_positions = [
        # 一横
        (-0.08, -0.08, 0.32), (0, -0.08, 0.32), (0.08, -0.08, 0.32),
        # 一竖
        (0, -0.12, 0.35), (0, -0.16, 0.38),
        # 下面一横
        (-0.06, -0.2, 0.35), (0, -0.2, 0.35), (0.06, -0.2, 0.35),
    ]
    for i, (dx, dy, dz) in enumerate(wang_positions):
        bpy.ops.mesh.primitive_cube_add(size=0.015, 
                                         location=(location[0]+dx, location[1]+dy, location[2]+dz))
        stroke = bpy.context.active_object
        stroke.name = f"Tiger_Wang_{i}"
        stroke.scale = (1.5, 0.3, 1)
        stroke.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(stroke)
    
    return parts

def ultra_dragon_head(location):
    """超精细龙首 - 30+部件（最复杂）"""
    parts = []
    
    # 头骨主体（拉长形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=location)
    skull = bpy.context.active_object
    skull.name = "Dragon_Skull"
    skull.scale = (0.85, 1.4, 0.95)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 额骨隆起
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15,
                                          location=(location[0], location[1]-0.15, location[2]+0.3))
    forehead = bpy.context.active_object
    forehead.name = "Dragon_Forehead"
    forehead.scale = (1.2, 0.8, 0.8)
    forehead.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(forehead)
    
    # 颧骨
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1,
                                              location=(location[0]+side*0.3, location[1]+0.1, location[2]+0.05))
        bone = bpy.context.active_object
        bone.name = f"Dragon_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 吻部（长形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2,
                                          location=(location[0], location[1]+0.45, location[2]-0.05))
    muzzle = bpy.context.active_object
    muzzle.name = "Dragon_Muzzle"
    muzzle.scale = (0.75, 1.4, 0.7)
    muzzle.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(muzzle)
    
    # 上颚
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15,
                                          location=(location[0], location[1]+0.6, location[2]+0.02))
    upper_jaw = bpy.context.active_object
    upper_jaw.name = "Dragon_UpperJaw"
    upper_jaw.scale = (0.6, 1.2, 0.5)
    upper_jaw.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(upper_jaw)
    
    # 鼻子
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                          location=(location[0], location[1]+0.72, location[2]))
    nose = bpy.context.active_object
    nose.name = "Dragon_Nose"
    nose.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nose)
    
    # 鼻孔
    for side in [-1, 1]:
        parts.extend(create_nostril(
            (location[0]+side*0.04, location[1]+0.75, location[2]-0.02),
            "Dragon", size=0.02
        ))
    
    # 鼻须/龙须根部
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03,
                                              location=(location[0]+side*0.08, location[1]+0.7, location[2]+0.02))
        whisker_base = bpy.context.active_object
        whisker_base.name = f"Dragon_WhiskerBase_{side}"
        whisker_base.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(whisker_base)
    
    # 眼睛（突出，更有神）
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.25, location[1]+0.15, location[2]+0.15)
        
        # 眼眶（更突出）
        bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.02,
                                          location=eye_loc)
        socket = bpy.context.active_object
        socket.name = f"Dragon_EyeSocket_{side}"
        socket.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(socket)
        
        # 眼球
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=eye_loc)
        eyeball = bpy.context.active_object
        eyeball.name = f"Dragon_Eyeball_{side}"
        eyeball.data.materials.append(bpy.data.materials['eye_glass'])
        parts.append(eyeball)
        
        # 竖瞳（龙的眼睛）
        bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.06,
                                             location=(eye_loc[0], eye_loc[1]+0.04, eye_loc[2]))
        pupil = bpy.context.active_object
        pupil.name = f"Dragon_VerticalPupil_{side}"
        pupil.rotation_euler = (math.radians(90), 0, 0)
        pupil.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(pupil)
    
    # 鹿角（复杂分支）
    for side in [-1, 1]:
        # 角基座
        bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.1,
                                             location=(location[0]+side*0.18, location[1]-0.25, location[2]+0.35))
        base = bpy.context.active_object
        base.name = f"Dragon_HornBase_{side}"
        base.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(base)
        
        # 主角干（多段）
        horn_points = [
            (0, -0.3, 0.5, 0.06),
            (side*0.05, -0.38, 0.6, 0.05),
            (side*0.1, -0.45, 0.7, 0.04),
            (side*0.12, -0.5, 0.78, 0.03),
        ]
        for i, (dx, dy, dz, r) in enumerate(horn_points):
            bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.1,
                                                 location=(location[0]+dx, location[1]+dy, location[2]+dz))
            seg = bpy.context.active_object
            seg.name = f"Dragon_HornSeg_{side}_{i}"
            seg.data.materials.append(bpy.data.materials['bronze_refined'])
            parts.append(seg)
        
        # 分叉1
        bpy.ops.mesh.primitive_cone_add(radius1=0.025, radius2=0, depth=0.15,
                                         location=(location[0]+side*0.15, location[1]-0.42, location[2]+0.72))
        tine1 = bpy.context.active_object
        tine1.name = f"Dragon_Tine1_{side}"
        tine1.rotation_euler = (math.radians(-40), side*math.radians(30), 0)
        tine1.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(tine1)
        
        # 分叉2
        bpy.ops.mesh.primitive_cone_add(radius1=0.02, radius2=0, depth=0.12,
                                         location=(location[0]+side*0.18, location[1]-0.48, location[2]+0.75))
        tine2 = bpy.context.active_object
        tine2.name = f"Dragon_Tine2_{side}"
        tine2.rotation_euler = (math.radians(-60), side*math.radians(45), 0)
        tine2.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(tine2)
    
    # 龙须（长飘，每侧2根）
    for side in [-1, 1]:
        for i in range(2):
            whisker_points = []
            for j in range(5):
                t = j / 4
                x = location[0] + side * (0.1 + t * 0.3)
                y = location[1] + 0.7 + t * 0.4
                z = location[2] - 0.05 - t * 0.2 + math.sin(t * math.pi) * 0.1
                whisker_points.append((x, y, z))
            
            for j in range(4):
                start = whisker_points[j]
                end = whisker_points[j+1]
                parts.append(create_hair_strand(start, end, f"Dragon_Whisker_{side}_{i}", j, thickness=0.008))
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                              location=(location[0]+side*0.2, location[1]+0.08, location[2]+0.25))
        brow = bpy.context.active_object
        brow.name = f"Dragon_Brow_{side}"
        brow.scale = (1.8, 0.5, 0.5)
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    # 鳞片（头顶和脸颊）
    scale_positions = []
    for row in range(4):
        for col in range(5):
            x = location[0] + (col - 2) * 0.08
            y = location[1] - 0.2 + row * 0.1
            z = location[2] + 0.35 - abs(col - 2) * 0.03
            scale_positions.append((x, y, z))
    
    for i, (x, y, z) in enumerate(scale_positions):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(x, y, z))
        scale = bpy.context.active_object
        scale.name = f"Dragon_Scale_{i}"
        scale.scale = (1.2, 0.8, 0.3)
        scale.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(scale)
    
    # 下巴须
    for i in range(3):
        start = (location[0]+(i-1)*0.05, location[1]+0.3, location[2]-0.2)
        end = (location[0]+(i-1)*0.08, location[1]+0.2, location[2]-0.45)
        parts.append(create_hair_strand(start, end, "Dragon_ChinBeard", i, thickness=0.01))
    
    # 颈部鳞片
    for i in range(8):
        angle = math.radians(i * 45)
        x = location[0] + math.cos(angle) * 0.25
        y = location[1] - 0.4
        z = location[2] - 0.1 + math.sin(angle) * 0.1
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(x, y, z))
        neck_scale = bpy.context.active_object
        neck_scale.name = f"Dragon_NeckScale_{i}"
        neck_scale.scale = (1, 0.7, 0.4)
        neck_scale.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(neck_scale)
    
    return parts

# ==================== 创建完整场景 ====================

# ==================== 兔首 ====================
def ultra_rabbit_head(location):
    """超精细兔首 - 20+部件"""
    parts = []
    
    # 头骨主体（圆润）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.26, location=location)
    skull = bpy.context.active_object
    skull.name = "Rabbit_Skull"
    skull.scale = (0.95, 1.0, 1.0)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 颧骨
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                              location=(location[0]+side*0.18, location[1]+0.05, location[2]))
        bone = bpy.context.active_object
        bone.name = f"Rabbit_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 吻部（较短）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12,
                                          location=(location[0], location[1]+0.2, location[2]-0.05))
    muzzle = bpy.context.active_object
    muzzle.name = "Rabbit_Muzzle"
    muzzle.scale = (0.7, 1.0, 0.7)
    muzzle.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(muzzle)
    
    # 三瓣嘴中间
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                          location=(location[0], location[1]+0.3, location[2]-0.08))
    lip = bpy.context.active_object
    lip.name = "Rabbit_CenterLip"
    lip.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(lip)
    
    # 三瓣嘴两侧
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035,
                                              location=(location[0]+side*0.04, location[1]+0.28, location[2]-0.1))
        side_lip = bpy.context.active_object
        side_lip.name = f"Rabbit_SideLip_{side}"
        side_lip.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(side_lip)
    
    # 鼻子
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025,
                                          location=(location[0], location[1]+0.32, location[2]-0.05))
    nose = bpy.context.active_object
    nose.name = "Rabbit_Nose"
    nose.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nose)
    
    # 鼻孔
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.01,
                                              location=(location[0]+side*0.02, location[1]+0.33, location[2]-0.06))
        nostril = bpy.context.active_object
        nostril.name = f"Rabbit_Nostril_{side}"
        nostril.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(nostril)
    
    # 眼睛
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.14, location[1]+0.08, location[2]+0.06)
        parts.extend(create_eyeball(eye_loc, f"Rabbit_{'Left' if side<0 else 'Right'}"))
    
    # 长耳朵（内耳+外耳轮廓）
    for side in [-1, 1]:
        # 外耳
        bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.65,
                                             location=(location[0]+side*0.12, location[1]-0.15, location[2]+0.55))
        outer = bpy.context.active_object
        outer.name = f"Rabbit_OuterEar_{side}"
        outer.scale = (0.8, 1, 1)
        outer.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(outer)
        
        # 内耳凹陷
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.6,
                                             location=(location[0]+side*0.12, location[1]-0.12, location[2]+0.55))
        inner = bpy.context.active_object
        inner.name = f"Rabbit_InnerEar_{side}"
        inner.scale = (0.8, 1, 1)
        inner.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(inner)
        
        # 耳尖
        bpy.ops.mesh.primitive_cone_add(radius1=0.06, radius2=0.02, depth=0.1,
                                         location=(location[0]+side*0.12, location[1]-0.25, location[2]+0.9))
        tip = bpy.context.active_object
        tip.name = f"Rabbit_EarTip_{side}"
        tip.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(tip)
    
    # 颊部胡须
    for i in range(3):
        for side in [-1, 1]:
            start = (location[0]+side*0.08, location[1]+0.2, location[2]-0.02+i*0.015)
            end = (location[0]+side*0.3, location[1]+0.35, location[2]-0.03+i*0.02)
            parts.append(create_hair_strand(start, end, "Rabbit_Whisker", i+side*3, thickness=0.006))
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.06,
                                             location=(location[0]+side*0.1, location[1]+0.05, location[2]+0.13))
        brow = bpy.context.active_object
        brow.name = f"Rabbit_Brow_{side}"
        brow.rotation_euler = (0, math.radians(25*side), math.radians(15))
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    # 下巴
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                          location=(location[0], location[1]+0.15, location[2]-0.18))
    chin = bpy.context.active_object
    chin.name = "Rabbit_Chin"
    chin.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(chin)
    
    return parts

# ==================== 蛇首 ====================
def ultra_snake_head(location):
    """超精细蛇首 - 18+部件"""
    parts = []
    
    # 头骨（三角形）
    bpy.ops.mesh.primitive_cone_add(radius1=0.22, radius2=0.12, depth=0.45,
                                     location=(location[0], location[1], location[2]))
    skull = bpy.context.active_object
    skull.name = "Snake_Skull"
    skull.rotation_euler = (math.radians(90), 0, 0)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 头顶扁平
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15,
                                          location=(location[0], location[1]-0.1, location[2]+0.1))
    crown = bpy.context.active_object
    crown.name = "Snake_Crown"
    crown.scale = (1.2, 0.6, 0.5)
    crown.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(crown)
    
    # 颧骨突出
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                              location=(location[0]+side*0.15, location[1]+0.05, location[2]+0.05))
        bone = bpy.context.active_object
        bone.name = f"Snake_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 吻部（锥形）
    bpy.ops.mesh.primitive_cone_add(radius1=0.1, radius2=0.04, depth=0.2,
                                     location=(location[0], location[1]+0.25, location[2]))
    snout = bpy.context.active_object
    snout.name = "Snake_Snout"
    snout.rotation_euler = (math.radians(90), 0, 0)
    snout.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(snout)
    
    # 眼睛（突出，竖瞳）
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.12, location[1]+0.05, location[2]+0.08)
        
        # 眼球
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=eye_loc)
        eyeball = bpy.context.active_object
        eyeball.name = f"Snake_Eyeball_{side}"
        eyeball.data.materials.append(bpy.data.materials['eye_glass'])
        parts.append(eyeball)
        
        # 眼睑
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=eye_loc)
        lid = bpy.context.active_object
        lid.name = f"Snake_Eyelid_{side}"
        lid.scale = (1, 0.3, 0.5)
        lid.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(lid)
        
        # 竖瞳
        bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=0.05,
                                             location=(eye_loc[0], eye_loc[1]+0.035, eye_loc[2]))
        pupil = bpy.context.active_object
        pupil.name = f"Snake_Pupil_{side}"
        pupil.rotation_euler = (math.radians(90), 0, 0)
        pupil.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(pupil)
    
    # 分叉舌
    for side in [-1, 1]:
        # 舌根
        bpy.ops.mesh.primitive_cylinder_add(radius=0.008, depth=0.1,
                                             location=(location[0], location[1]+0.32, location[2]-0.02))
        tongue = bpy.context.active_object
        tongue.name = "Snake_TongueBase"
        tongue.rotation_euler = (math.radians(85), 0, 0)
        tongue.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(tongue)
        
        # 分叉
        bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=0.08,
                                             location=(location[0]+side*0.03, location[1]+0.4, location[2]-0.05))
        fork = bpy.context.active_object
        fork.name = f"Snake_TongueFork_{side}"
        fork.rotation_euler = (math.radians(85), side*math.radians(20), 0)
        fork.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(fork)
    
    # 鳞片（头顶）
    for row in range(3):
        for col in range(4):
            x = location[0] + (col - 1.5) * 0.06
            y = location[1] - 0.15 + row * 0.08
            z = location[2] + 0.12 - abs(col - 1.5) * 0.02
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=(x, y, z))
            scale = bpy.context.active_object
            scale.name = f"Snake_Scale_{row}_{col}"
            scale.scale = (1.1, 0.7, 0.3)
            scale.data.materials.append(bpy.data.materials['bronze_refined'])
            parts.append(scale)
    
    # 颈部
    for i in range(6):
        angle = math.radians(i * 60)
        x = location[0] + math.cos(angle) * 0.15
        y = location[1] - 0.35
        z = location[2] - 0.1 + math.sin(angle) * 0.08
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(x, y, z))
        neck = bpy.context.active_object
        neck.name = f"Snake_NeckScale_{i}"
        neck.scale = (1.2, 0.8, 0.4)
        neck.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(neck)
    
    return parts

# ==================== 马首 ====================
def ultra_horse_head(location):
    """超精细马首 - 25+部件"""
    parts = []
    
    # 头骨（拉长形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=location)
    skull = bpy.context.active_object
    skull.name = "Horse_Skull"
    skull.scale = (0.75, 1.45, 1.05)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 额骨
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12,
                                          location=(location[0], location[1]-0.2, location[2]+0.22))
    forehead = bpy.context.active_object
    forehead.name = "Horse_Forehead"
    forehead.scale = (1.0, 0.7, 0.6)
    forehead.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(forehead)
    
    # 颧骨
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08,
                                              location=(location[0]+side*0.22, location[1], location[2]+0.02))
        bone = bpy.context.active_object
        bone.name = f"Horse_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 下颌
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15,
                                          location=(location[0], location[1]+0.35, location[2]-0.15))
    jaw = bpy.context.active_object
    jaw.name = "Horse_Jaw"
    jaw.scale = (0.7, 1.2, 0.6)
    jaw.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(jaw)
    
    # 口鼻部
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18,
                                          location=(location[0], location[1]+0.55, location[2]-0.08))
    muzzle = bpy.context.active_object
    muzzle.name = "Horse_Muzzle"
    muzzle.scale = (0.8, 1.1, 0.75)
    muzzle.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(muzzle)
    
    # 大鼻孔
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                              location=(location[0]+side*0.1, location[1]+0.68, location[2]-0.1))
        nostril = bpy.context.active_object
        nostril.name = f"horse_Nostril_{side}"
        nostril.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(nostril)
        
        # 鼻翼
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                              location=(location[0]+side*0.15, location[1]+0.62, location[2]-0.08))
        wing = bpy.context.active_object
        wing.name = f"horse_NoseWing_{side}"
        wing.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(wing)
    
    # 嘴唇
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08,
                                          location=(location[0], location[1]+0.65, location[2]-0.15))
    lip = bpy.context.active_object
    lip.name = "horse_Lip"
    lip.scale = (1.2, 0.6, 0.5)
    lip.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(lip)
    
    # 眼睛
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.2, location[1]+0.1, location[2]+0.1)
        parts.extend(create_eyeball(eye_loc, f"horse_{'Left' if side<0 else 'Right'}"))
    
    # 竖耳朵
    for side in [-1, 1]:
        # 外耳
        bpy.ops.mesh.primitive_cone_add(radius1=0.08, radius2=0.03, depth=0.25,
                                         location=(location[0]+side*0.15, location[1]-0.2, location[2]+0.35))
        outer = bpy.context.active_object
        outer.name = f"horse_OuterEar_{side}"
        outer.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(outer)
        
        # 内耳
        bpy.ops.mesh.primitive_cone_add(radius1=0.05, radius2=0.015, depth=0.2,
                                         location=(location[0]+side*0.15, location[1]-0.18, location[2]+0.35))
        inner = bpy.context.active_object
        inner.name = f"horse_InnerEar_{side}"
        inner.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(inner)
    
    # 鬃毛（10根）
    for i in range(10):
        t = i / 9
        x = location[0]
        y = location[1] - 0.3 + t * 0.4
        z = location[2] + 0.35 + t * 0.2
        
        start = (x, y, z)
        end = (x, y + 0.05, z + 0.15)
        parts.append(create_hair_strand(start, end, "horse_Mane", i, thickness=0.015))
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.1,
                                             location=(location[0]+side*0.15, location[1]+0.05, location[2]+0.18))
        brow = bpy.context.active_object
        brow.name = f"horse_Brow_{side}"
        brow.rotation_euler = (0, math.radians(25*side), math.radians(15))
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    # 额头皱纹
    for i in range(3):
        parts.append(create_wrinkle_line(
            (location[0], location[1]-0.25, location[2]+0.18-i*0.04),
            (location[0], location[1]-0.28, location[2]+0.18-i*0.04),
            "horse", i
        ))
    
    # 下巴
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                          location=(location[0], location[1]+0.4, location[2]-0.25))
    chin = bpy.context.active_object
    chin.name = "horse_Chin"
    chin.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(chin)
    
    return parts

# ==================== 羊首 ====================
def ultra_sheep_head(location):
    """超精细羊首 - 25+部件"""
    parts = []
    
    # 头骨
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, location=location)
    skull = bpy.context.active_object
    skull.name = "Sheep_Skull"
    skull.scale = (1.0, 1.05, 1.0)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 额骨（圆润）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1,
                                          location=(location[0], location[1]-0.1, location[2]+0.2))
    forehead = bpy.context.active_object
    forehead.name = "Sheep_Forehead"
    forehead.scale = (1.1, 0.7, 0.6)
    forehead.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(forehead)
    
    # 颧骨
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                              location=(location[0]+side*0.2, location[1]+0.05, location[2]))
        bone = bpy.context.active_object
        bone.name = f"Sheep_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 吻部
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12,
                                          location=(location[0], location[1]+0.22, location[2]-0.05))
    muzzle = bpy.context.active_object
    muzzle.name = "Sheep_Muzzle"
    muzzle.scale = (0.75, 1.0, 0.7)
    muzzle.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(muzzle)
    
    # 鼻子
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                          location=(location[0], location[1]+0.32, location[2]-0.03))
    nose = bpy.context.active_object
    nose.name = "Sheep_Nose"
    nose.scale = (1.3, 0.9, 0.8)
    nose.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nose)
    
    # 鼻孔
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015,
                                              location=(location[0]+side*0.03, location[1]+0.35, location[2]-0.05))
        nostril = bpy.context.active_object
        nostril.name = f"Sheep_Nostril_{side}"
        nostril.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(nostril)
    
    # 眼睛
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.16, location[1]+0.08, location[2]+0.06)
        parts.extend(create_eyeball(eye_loc, f"Sheep_{'Left' if side<0 else 'Right'}"))
    
    # 螺旋角（每侧）
    for side in [-1, 1]:
        # 角基座
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.1,
                                             location=(location[0]+side*0.2, location[1]-0.15, location[2]+0.25))
        base = bpy.context.active_object
        base.name = f"Sheep_HornBase_{side}"
        base.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(base)
        
        # 螺旋角（用多个球模拟）
        for i in range(8):
            angle = math.radians(i * 55)
            r = 0.08 + i * 0.015
            x = location[0] + side * (0.2 + math.cos(angle) * r)
            y = location[1] - 0.2 + math.sin(angle) * r * 0.5
            z = location[2] + 0.35 - i * 0.03
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035-i*0.003, location=(x, y, z))
            curl = bpy.context.active_object
            curl.name = f"Sheep_HornCurl_{side}_{i}"
            curl.data.materials.append(bpy.data.materials['bronze_refined'])
            parts.append(curl)
    
    # 耳朵
    for side in [-1, 1]:
        ear_loc = (location[0]+side*0.25, location[1]-0.1, location[2]+0.1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.15,
                                             location=ear_loc)
        ear = bpy.context.active_object
        ear.name = f"Sheep_Ear_{side}"
        ear.rotation_euler = (math.radians(30), side*math.radians(30), 0)
        ear.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(ear)
        
        # 耳内
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.12,
                                             location=(ear_loc[0], ear_loc[1]+0.02, ear_loc[2]))
        inner = bpy.context.active_object
        inner.name = f"Sheep_EarInner_{side}"
        inner.rotation_euler = (math.radians(30), side*math.radians(30), 0)
        inner.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(inner)
    
    # 下巴胡须
    for i in range(5):
        x = location[0] + (i-2) * 0.03
        start = (x, location[1]+0.15, location[2]-0.2)
        end = (x + (i-2)*0.01, location[1]+0.05, location[2]-0.4-i*0.02)
        parts.append(create_hair_strand(start, end, "Sheep_Beard", i, thickness=0.01))
    
    # 额头卷毛
    for i in range(6):
        x = location[0] + (i-2.5) * 0.06
        y = location[1] - 0.15
        z = location[2] + 0.25
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(x, y, z))
        curl = bpy.context.active_object
        curl.name = f"Sheep_ForeheadCurl_{i}"
        curl.data.materials.append(bpy.data.materials['hair_bronze'])
        parts.append(curl)
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.07,
                                             location=(location[0]+side*0.12, location[1]+0.05, location[2]+0.14))
        brow = bpy.context.active_object
        brow.name = f"Sheep_Brow_{side}"
        brow.rotation_euler = (0, math.radians(25*side), math.radians(15))
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    return parts

# ==================== 猴首 ====================
def ultra_monkey_head(location):
    """超精细猴首 - 22+部件"""
    parts = []
    
    # 头骨（圆形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.26, location=location)
    skull = bpy.context.active_object
    skull.name = "Monkey_Skull"
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 面部（心形/桃形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18,
                                          location=(location[0], location[1]+0.18, location[2]-0.02))
    face = bpy.context.active_object
    face.name = "Monkey_Face"
    face.scale = (0.85, 0.75, 0.95)
    face.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(face)
    
    # 眉骨（突出）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08,
                                          location=(location[0], location[1]+0.1, location[2]+0.18))
    brow_ridge = bpy.context.active_object
    brow_ridge.name = "Monkey_BrowRidge"
    brow_ridge.scale = (1.5, 0.5, 0.5)
    brow_ridge.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(brow_ridge)
    
    # 眼窝
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                              location=(location[0]+side*0.1, location[1]+0.12, location[2]+0.1))
        socket = bpy.context.active_object
        socket.name = f"Monkey_EyeSocket_{side}"
        socket.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(socket)
        
        # 眼球
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                              location=(location[0]+side*0.1, location[1]+0.13, location[2]+0.1))
        eyeball = bpy.context.active_object
        eyeball.name = f"Monkey_Eyeball_{side}"
        eyeball.data.materials.append(bpy.data.materials['eye_glass'])
        parts.append(eyeball)
    
    # 鼻子（扁平）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                          location=(location[0], location[1]+0.25, location[2]+0.02))
    nose = bpy.context.active_object
    nose.name = "Monkey_Nose"
    nose.scale = (1.2, 0.6, 0.8)
    nose.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(nose)
    
    # 鼻孔
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02,
                                              location=(location[0]+side*0.04, location[1]+0.3, location[2]))
        nostril = bpy.context.active_object
        nostril.name = f"Monkey_Nostril_{side}"
        nostril.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(nostril)
    
    # 嘴巴
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                          location=(location[0], location[1]+0.28, location[2]-0.1))
    mouth = bpy.context.active_object
    mouth.name = "Monkey_Mouth"
    mouth.scale = (1.3, 0.5, 0.4)
    mouth.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(mouth)
    
    # 嘴唇
    bpy.ops.mesh.primitive_torus_add(major_radius=0.06, minor_radius=0.015,
                                      location=(location[0], location[1]+0.32, location[2]-0.1))
    lip = bpy.context.active_object
    lip.name = "Monkey_Lip"
    lip.scale = (1.3, 0.5, 1)
    lip.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(lip)
    
    # 圆耳朵
    for side in [-1, 1]:
        # 外耳
        bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.025,
                                          location=(location[0]+side*0.26, location[1]-0.05, location[2]))
        outer = bpy.context.active_object
        outer.name = f"Monkey_OuterEar_{side}"
        outer.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(outer)
        
        # 内耳
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, location=(location[0]+side*0.26, location[1]-0.03, location[2]))
        inner = bpy.context.active_object
        inner.scale = (1, 0.2, 1)
        inner = bpy.context.active_object
        inner.name = f"Monkey_InnerEar_{side}"
        inner.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(inner)
        
        # 耳道
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.05,
                                             location=(location[0]+side*0.25, location[1]-0.02, location[2]))
        canal = bpy.context.active_object
        canal.name = f"Monkey_EarCanal_{side}"
        canal.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(canal)
    
    # 下巴
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                          location=(location[0], location[1]+0.2, location[2]-0.18))
    chin = bpy.context.active_object
    chin.name = "Monkey_Chin"
    chin.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(chin)
    
    # 额头皱纹
    for i in range(3):
        parts.append(create_wrinkle_line(
            (location[0]-0.06+i*0.06, location[1], location[2]+0.22),
            (location[0]-0.06+i*0.06, location[1]-0.05, location[2]+0.24),
            "Monkey", i
        ))
    
    # 颊部毛簇
    for side in [-1, 1]:
        for i in range(3):
            x = location[0]+side*0.2
            y = location[1]+0.1+i*0.06
            z = location[2]-0.05+i*0.03
            start = (x, y, z)
            end = (x+side*0.1, y+0.05, z)
            parts.append(create_hair_strand(start, end, "Monkey_CheekFur", i+side*3, thickness=0.008))
    
    return parts

# ==================== 鸡首 ====================
def ultra_rooster_head(location):
    """超精细鸡首 - 25+部件"""
    parts = []
    
    # 头骨
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=location)
    skull = bpy.context.active_object
    skull.name = "Rooster_Skull"
    skull.scale = (0.9, 1.0, 0.95)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 后脑
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12,
                                          location=(location[0], location[1]-0.18, location[2]-0.02))
    back = bpy.context.active_object
    back.name = "Rooster_BackHead"
    back.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(back)
    
    # 鸡冠（锯齿形，5-7个齿）
    comb_data = [
        (0, -0.08, 0.22, 0.12),
        (0, -0.02, 0.24, 0.1),
        (0, 0.04, 0.22, 0.13),
        (0, 0.1, 0.2, 0.1),
        (0, 0.16, 0.18, 0.12),
        (0, 0.22, 0.15, 0.08),
    ]
    for i, (dx, dy, dz, h) in enumerate(comb_data):
        bpy.ops.mesh.primitive_cone_add(radius1=0.04, radius2=0.01, depth=h,
                                         location=(location[0]+dx, location[1]+dy, location[2]+dz))
        tooth = bpy.context.active_object
        tooth.name = f"Rooster_Comb_{i}"
        tooth.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(tooth)
    
    # 眼睛
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.12, location[1]+0.08, location[2]+0.04)
        parts.extend(create_eyeball(eye_loc, f"Rooster_{'Left' if side<0 else 'Right'}"))
    
    # 喙（尖锐，上下）
    # 上喙
    bpy.ops.mesh.primitive_cone_add(radius1=0.06, radius2=0.015, depth=0.2,
                                     location=(location[0], location[1]+0.25, location[2]))
    upper_beak = bpy.context.active_object
    upper_beak.name = "Rooster_UpperBeak"
    upper_beak.rotation_euler = (math.radians(90), 0, 0)
    upper_beak.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(upper_beak)
    
    # 下喙
    bpy.ops.mesh.primitive_cone_add(radius1=0.04, radius2=0.01, depth=0.15,
                                     location=(location[0], location[1]+0.22, location[2]-0.03))
    lower_beak = bpy.context.active_object
    lower_beak.name = "Rooster_LowerBeak"
    lower_beak.rotation_euler = (math.radians(85), 0, 0)
    lower_beak.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(lower_beak)
    
    # 肉垂（两侧）
    for side in [-1, 1]:
        # 主肉垂
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                              location=(location[0]+side*0.06, location[1]+0.15, location[2]-0.15))
        wattle = bpy.context.active_object
        wattle.name = f"Rooster_Wattle_{side}"
        wattle.scale = (0.7, 0.5, 1.8)
        wattle.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(wattle)
    
    # 耳叶
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03,
                                              location=(location[0]+side*0.15, location[1]-0.05, location[2]+0.05))
        lobe = bpy.context.active_object
        lobe.name = f"Rooster_EarLobe_{side}"
        lobe.scale = (0.6, 0.5, 1.5)
        lobe.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(lobe)
    
    # 颈部羽毛（环状）
    for i in range(8):
        angle = math.radians(i * 45)
        x = location[0] + math.cos(angle) * 0.15
        y = location[1] - 0.2
        z = location[2] - 0.1 + math.sin(angle) * 0.08
        
        # 羽毛片
        bpy.ops.mesh.primitive_plane_add(size=0.06, location=(x, y, z))
        feather = bpy.context.active_object
        feather.name = f"Rooster_NeckFeather_{i}"
        feather.rotation_euler = (math.radians(45), angle, 0)
        feather.scale = (1, 2, 1)
        feather.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(feather)
    
    # 尾羽基部
    for i in range(5):
        x = location[0] + (i-2) * 0.04
        bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.15,
                                             location=(x, location[1]-0.25, location[2]+i*0.02))
        tail = bpy.context.active_object
        tail.name = f"Rooster_TailBase_{i}"
        tail.rotation_euler = (math.radians(45), 0, 0)
        tail.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(tail)
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=0.05,
                                             location=(location[0]+side*0.08, location[1]+0.05, location[2]+0.12))
        brow = bpy.context.active_object
        brow.name = f"Rooster_Brow_{side}"
        brow.rotation_euler = (0, math.radians(25*side), math.radians(15))
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    return parts

# ==================== 狗首 ====================
def ultra_dog_head(location):
    """超精细狗首 - 22+部件"""
    parts = []
    
    # 头骨
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.27, location=location)
    skull = bpy.context.active_object
    skull.name = "Dog_Skull"
    skull.scale = (1.0, 1.0, 0.95)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 额骨
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1,
                                          location=(location[0], location[1]-0.1, location[2]+0.18))
    forehead = bpy.context.active_object
    forehead.name = "Dog_Forehead"
    forehead.scale = (1.0, 0.6, 0.5)
    forehead.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(forehead)
    
    # 颧骨
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07,
                                              location=(location[0]+side*0.2, location[1]+0.05, location[2]+0.02))
        bone = bpy.context.active_object
        bone.name = f"Dog_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 口鼻部（突出）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15,
                                          location=(location[0], location[1]+0.28, location[2]-0.05))
    muzzle = bpy.context.active_object
    muzzle.name = "Dog_Muzzle"
    muzzle.scale = (0.85, 1.3, 0.8)
    muzzle.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(muzzle)
    
    # 鼻子（皮革质感）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                          location=(location[0], location[1]+0.42, location[2]-0.03))
    nose = bpy.context.active_object
    nose.name = "Dog_Nose"
    nose.scale = (1.4, 0.9, 0.7)
    nose.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nose)
    
    # 鼻孔
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02,
                                              location=(location[0]+side*0.04, location[1]+0.45, location[2]-0.05))
        nostril = bpy.context.active_object
        nostril.name = f"Dog_Nostril_{side}"
        nostril.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(nostril)
    
    # 嘴唇
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                              location=(location[0]+side*0.08, location[1]+0.35, location[2]-0.1))
        lip = bpy.context.active_object
        lip.name = f"Dog_Lip_{side}"
        lip.scale = (0.8, 1.2, 0.6)
        lip.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(lip)
    
    # 眼睛
    for side in [-1, 1]:
        eye_loc = (location[0]+side*0.15, location[1]+0.08, location[2]+0.1)
        parts.extend(create_eyeball(eye_loc, f"Dog_{'Left' if side<0 else 'Right'}"))
    
    # 垂耳
    for side in [-1, 1]:
        # 外耳
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1,
                                              location=(location[0]+side*0.25, location[1]-0.08, location[2]-0.05))
        outer = bpy.context.active_object
        outer.name = f"Dog_OuterEar_{side}"
        outer.scale = (0.6, 0.5, 1.8)
        outer.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(outer)
        
        # 内耳
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07,
                                              location=(location[0]+side*0.25, location[1]-0.06, location[2]))
        inner = bpy.context.active_object
        inner.name = f"Dog_InnerEar_{side}"
        inner.scale = (0.5, 0.4, 1.5)
        inner.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(inner)
    
    # 舌头（伸出）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                          location=(location[0], location[1]+0.4, location[2]-0.15))
    tongue = bpy.context.active_object
    tongue.name = "Dog_Tongue"
    tongue.scale = (0.6, 1.5, 0.3)
    tongue.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(tongue)
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=0.08,
                                             location=(location[0]+side*0.12, location[1]+0.05, location[2]+0.18))
        brow = bpy.context.active_object
        brow.name = f"Dog_Brow_{side}"
        brow.rotation_euler = (0, math.radians(25*side), math.radians(15))
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    # 额头皱纹
    for i in range(3):
        parts.append(create_wrinkle_line(
            (location[0], location[1]-0.12, location[2]+0.18-i*0.04),
            (location[0], location[1]-0.15, location[2]+0.2-i*0.04),
            "Dog", i
        ))
    
    # 下巴
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05,
                                          location=(location[0], location[1]+0.2, location[2]-0.18))
    chin = bpy.context.active_object
    chin.name = "Dog_Chin"
    chin.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(chin)
    
    return parts

# ==================== 猪首 ====================
def ultra_pig_head(location):
    """超精细猪首 - 22+部件"""
    parts = []
    
    # 头骨（圆形宽大）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=location)
    skull = bpy.context.active_object
    skull.name = "Pig_Skull"
    skull.scale = (1.1, 1.0, 1.0)
    skull.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(skull)
    
    # 颧骨
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08,
                                              location=(location[0]+side*0.25, location[1]+0.1, location[2]+0.02))
        bone = bpy.context.active_object
        bone.name = f"Pig_Cheekbone_{side}"
        bone.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(bone)
    
    # 额头
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12,
                                          location=(location[0], location[1]-0.15, location[2]+0.2))
    forehead = bpy.context.active_object
    forehead.name = "Pig_Forehead"
    forehead.scale = (1.1, 0.6, 0.5)
    forehead.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(forehead)
    
    # 吻部（长筒形）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18,
                                          location=(location[0], location[1]+0.35, location[2]-0.05))
    muzzle = bpy.context.active_object
    muzzle.name = "Pig_Muzzle"
    muzzle.scale = (1.2, 1.3, 0.9)
    muzzle.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(muzzle)
    
    # 鼻盘（扁平圆形）
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.06,
                                         location=(location[0], location[1]+0.52, location[2]-0.05))
    nose_pad = bpy.context.active_object
    nose_pad.name = "Pig_NosePad"
    nose_pad.rotation_euler = (math.radians(90), 0, 0)
    nose_pad.data.materials.append(bpy.data.materials['bronze_dark'])
    parts.append(nose_pad)
    
    # 鼻孔（两个大椭圆形）
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035,
                                              location=(location[0]+side*0.05, location[1]+0.55, location[2]-0.05))
        nostril = bpy.context.active_object
        nostril.name = f"Pig_Nostril_{side}"
        nostril.scale = (1, 0.7, 1.2)
        nostril.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(nostril)
    
    # 嘴唇（厚实）
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08,
                                          location=(location[0], location[1]+0.48, location[2]-0.12))
    lip = bpy.context.active_object
    lip.name = "Pig_Lip"
    lip.scale = (1.3, 0.8, 0.5)
    lip.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(lip)
    
    # 眼睛（小而深陷）
    for side in [-1, 1]:
        # 眼窝
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04,
                                              location=(location[0]+side*0.18, location[1]+0.08, location[2]+0.08))
        socket = bpy.context.active_object
        socket.name = f"Pig_EyeSocket_{side}"
        socket.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(socket)
        
        # 眼球
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03,
                                              location=(location[0]+side*0.18, location[1]+0.09, location[2]+0.08))
        eyeball = bpy.context.active_object
        eyeball.name = f"Pig_Eyeball_{side}"
        eyeball.data.materials.append(bpy.data.materials['eye_glass'])
        parts.append(eyeball)
    
    # 三角耳朵
    for side in [-1, 1]:
        # 外耳
        bpy.ops.mesh.primitive_cone_add(radius1=0.1, radius2=0.02, depth=0.2,
                                         location=(location[0]+side*0.22, location[1]-0.15, location[2]+0.25))
        outer = bpy.context.active_object
        outer.name = f"Pig_OuterEar_{side}"
        outer.rotation_euler = (math.radians(-25), side*math.radians(25), 0)
        outer.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(outer)
        
        # 内耳
        bpy.ops.mesh.primitive_cone_add(radius1=0.07, radius2=0.01, depth=0.15,
                                         location=(location[0]+side*0.22, location[1]-0.12, location[2]+0.25))
        inner = bpy.context.active_object
        inner.name = f"Pig_InnerEar_{side}"
        inner.rotation_euler = (math.radians(-25), side*math.radians(25), 0)
        inner.data.materials.append(bpy.data.materials['bronze_dark'])
        parts.append(inner)
    
    # 眉弓
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.07,
                                             location=(location[0]+side*0.14, location[1]+0.05, location[2]+0.15))
        brow = bpy.context.active_object
        brow.name = f"Pig_Brow_{side}"
        brow.rotation_euler = (0, math.radians(25*side), math.radians(15))
        brow.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(brow)
    
    # 额头皱纹
    for i in range(2):
        parts.append(create_wrinkle_line(
            (location[0], location[1]-0.18, location[2]+0.2-i*0.05),
            (location[0], location[1]-0.22, location[2]+0.22-i*0.05),
            "Pig", i
        ))
    
    # 下巴
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06,
                                          location=(location[0], location[1]+0.25, location[2]-0.18))
    chin = bpy.context.active_object
    chin.name = "Pig_Chin"
    chin.data.materials.append(bpy.data.materials['bronze_refined'])
    parts.append(chin)
    
    # 颈部褶皱
    for i in range(4):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.2-i*0.02, minor_radius=0.015,
                                          location=(location[0], location[1]-0.2, location[2]-0.15-i*0.05))
        fold = bpy.context.active_object
        fold.name = f"Pig_NeckFold_{i}"
        fold.data.materials.append(bpy.data.materials['bronze_refined'])
        parts.append(fold)
    
    return parts


def create_complete_dashuifa():
    """创建完整的精细化大水法场景"""
    # 清理场景
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    
    print("创建超精细材质...")
    mats = create_advanced_materials()
    
    # 验证材质已创建
    print(f"已创建材质: {list(bpy.data.materials.keys())}")
    
    # 十二生肖位置和建模函数
    animals = [
        ('Rat', '鼠', ultra_rat_head),
        ('Ox', '牛', ultra_ox_head),
        ('Tiger', '虎', ultra_tiger_head),
        ('Rabbit', '兔', ultra_rabbit_head),
        ('Dragon', '龙', ultra_dragon_head),
        ('Snake', '蛇', ultra_snake_head),
        ('Horse', '马', ultra_horse_head),
        ('Sheep', '羊', ultra_sheep_head),
        ('Monkey', '猴', ultra_monkey_head),
        ('Rooster', '鸡', ultra_rooster_head),
        ('Dog', '狗', ultra_dog_head),
        ('Pig', '猪', ultra_pig_head),
    ]
    
    # 创建已完成的兽首
    created_count = 0
    for i, (eng_name, ch_name, create_func) in enumerate(animals):
        if create_func is None:
            continue
            
        angle = math.radians(-90 + i * 15)
        x = math.cos(angle) * 10
        y = math.sin(angle) * 10 + 5
        z = 1.8
        
        location = (x, y, z)
        print(f"  创建 {ch_name}首 ({eng_name})...")
        
        create_func(location)
        created_count += 1
    
    print(f"\n已创建 {created_count} 个兽首")
    return created_count

# ==================== 执行 ====================
if __name__ == "__main__":
    count = create_complete_dashuifa()
    
    # 导出GLB
    output_path = os.path.expanduser("~/Desktop/WX hermes workspace/yuanmingyuan-3d/output/dashuifa_zodiac_ultra.glb")
    print(f"\n导出GLB到: {output_path}")
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_materials='EXPORT'
    )
    print(f"✅ 已导出: {output_path}")
    
    print(f"\n{'='*50}")
    print(f"超精细大水法 - 已创建 {count} 个兽首并导出")
    print(f"{'='*50}")
