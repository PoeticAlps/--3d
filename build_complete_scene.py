"""
圆明园数字重建 - 完整场景版 (Blender 5.1 兼容)
包含：大水法+十二生肖喷泉、九州清晏、方壶胜境、正大光明殿
"""
import bpy
import math
import os
import random

OUTPUT_DIR = "/Users/saint/Desktop/WX hermes workspace/yuanmingyuan-3d/output"
OUTPUT_GLB = os.path.join(OUTPUT_DIR, "yuanmingyuan_complete.glb")

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

def make_mat(name, color, rough=0.5, metal=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (400, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_water():
    mat = bpy.data.materials.new(name="Water")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (400, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.02, 0.08, 0.15, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.02
    bsdf.inputs['IOR'].default_value = 1.333
    bsdf.inputs['Transmission Weight'].default_value = 0.98
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def mats():
    m = {}
    m['marble'] = make_mat("Marble", (0.95, 0.93, 0.88), 0.15)
    m['red'] = make_mat("Red", (0.65, 0.08, 0.05), 0.3)
    m['gold'] = make_mat("Gold", (0.95, 0.75, 0.2), 0.15, 1.0)
    m['bronze'] = make_mat("Bronze", (0.55, 0.47, 0.33), 0.4, 0.9)
    m['roof'] = make_mat("Roof", (0.08, 0.08, 0.1), 0.7)
    m['roof_y'] = make_mat("RoofY", (0.85, 0.65, 0.15), 0.4, 0.1)
    m['wood'] = make_mat("Wood", (0.35, 0.22, 0.12), 0.85)
    m['water'] = make_water()
    m['grass'] = make_mat("Grass", (0.12, 0.32, 0.08), 0.95)
    m['grass2'] = make_mat("Grass2", (0.08, 0.25, 0.05), 0.95)
    m['rock'] = make_mat("Rock", (0.45, 0.42, 0.38), 0.9)
    m['wm'] = make_mat("WM", (0.98, 0.96, 0.92), 0.2)
    m['path'] = make_mat("Path", (0.55, 0.52, 0.48), 0.85)
    return m

def add_cube(name, loc, scale, mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if mat: o.data.materials.append(mat)
    return o

def add_cyl(name, loc, r, d, verts=16, mat=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc)
    o = bpy.context.active_object
    o.name = name
    if mat: o.data.materials.append(mat)
    return o

def add_cone(name, loc, r1, d, verts=6, mat=None):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, depth=d, location=loc)
    o = bpy.context.active_object
    o.name = name
    if mat: o.data.materials.append(mat)
    return o

def add_sphere(name, loc, r, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    if mat: o.data.materials.append(mat)
    return o

def add_ico(name, loc, r, sub=2, mat=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    if mat: o.data.materials.append(mat)
    return o

def pillar(x, y, h, m, r=0.35):
    add_cyl(f"PB_{x}_{y}", (x, y, 0.15), r*1.5, 0.3, mat=m['wm'])
    add_cyl(f"P_{x}_{y}", (x, y, h/2+0.3), r, h, mat=m['red'])

def hall(name, x, y, w=20, d=14, h=5, m=None):
    # 台基
    for i in range(2):
        s = 1 - i*0.3
        add_cube(f"{name}_base{i}", (x, y, 0.3+i*0.3), ((w/2+2)*s, (d/2+2)*s, 0.3), m['marble'])
    # 柱网
    for row in range(3):
        for col in range(5):
            px = x - w/2 + col*w/4
            py = y - d/2 + row*d/2
            if row in [0,2] or col in [0,4]:
                pillar(px, py, h, m, 0.3)
    # 额枋
    for ry in [y-d/2, y+d/2]:
        for i in range(4):
            bx = x - w/2 + i*w/4 + w/8
            add_cube(f"{name}_beam{i}", (bx, ry, h+0.3), (w/8, 0.15, 0.15), m['red'])
    # 屋顶
    add_cone(f"{name}_roof", (x, y, h+1.5), max(w,d)*0.5, 2, verts=4, mat=m['roof'])
    # 正脊
    add_cube(f"{name}_ridge", (x, y, h+2.5), (w*0.35, 0.25, 0.3), m['roof_y'])

def tree(name, x, y, h=8, m=None):
    add_cyl(f"{name}_t", (x, y, h*0.25), 0.25, h*0.5, mat=m['wood'])
    for layer in range(2):
        z = h*0.5 + layer*h*0.15
        for k in range(random.randint(3,5)):
            a = random.uniform(0, math.pi*2)
            d = random.uniform(0.5, 1.5)
            add_ico(f"{name}_l{layer}_{k}", (x+math.cos(a)*d, y+math.sin(a)*d, z), random.uniform(0.8,1.5), mat=random.choice([m['grass'],m['grass2']]))

def rock(x, y, s=2, m=None):
    for i in range(4):
        add_ico(f"R_{x}_{y}_{i}", (x+random.uniform(-s,s), y+random.uniform(-s,s), s*0.3), s*random.uniform(0.3,0.8), mat=m['rock'])

# ============================================================
# 大水法 + 十二生肖
# ============================================================
def build_dashuifa(m):
    # 主背景墙
    add_cube("D_Wall", (0, 0, 2.5), (12, 0.5, 3), m['marble'])
    # 三拱门
    for i, ox in enumerate([-4, 0, 4]):
        add_cyl(f"D_Arch_{i}", (ox, 0, 3), 1.8, 0.3, verts=24, mat=m['marble'])
        add_cyl(f"D_ArchTop_{i}", (ox, 0, 4.5), 0.15, 0.5, mat=m['marble'])
    # 两侧石柱
    for side in [-1, 1]:
        for i in range(3):
            pillar(side*6 + i*side*0.8, 0, 5, m, 0.25)
    # 观水法平台
    add_cyl("D_Platform", (0, 8, 0.15), 8, 0.3, verts=32, mat=m['wm'])
    # 十二生肖铜首
    zodiac = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]
    for i, name in enumerate(zodiac):
        angle = math.pi + (i/11)*math.pi
        r = 7
        zx = math.cos(angle)*r
        zy = 8 + math.sin(angle)*r
        add_cyl(f"Z_{name}_base", (zx, zy, 0.75), 0.2, 1.2, verts=12, mat=m['wm'])
        add_sphere(f"Z_{name}_head", (zx, zy, 1.6), 0.28, m['bronze'])
        add_cyl(f"Z_{name}_noz", (zx, zy-0.25, 1.5), 0.06, 0.25, verts=8, mat=m['bronze'])
    # 中心喷泉池
    add_cyl("D_Pool", (0, 3, -0.2), 4, 0.4, verts=32, mat=m['marble'])
    add_cyl("D_PoolW", (0, 3, 0.02), 3.8, 0.05, verts=32, mat=m['water'])
    # 中心柱
    add_cyl("D_Center", (0, 3, 1.8), 0.35, 3.2, verts=12, mat=m['wm'])
    # 翼墙
    for side in [-1, 1]:
        add_cube(f"D_Wing_{side}", (side*8, 0, 2), (4, 0.35, 2.5), m['marble'])
        for j in range(2):
            pillar(side*7 + j*side*1.2, 0, 4, m, 0.18)

# ============================================================
# 九州清晏
# ============================================================
def build_jiuzhou(m):
    islands = [(0,0,5), (-12,-12,3), (0,-14,3), (12,-12,3),
               (-14,0,3), (14,0,3), (-12,12,3), (0,14,3), (12,12,3)]
    for i,(ix,iy,s) in enumerate(islands):
        add_sphere(f"Island_{i}", (ix, iy, -s*0.2), s*0.9, m['grass'])
        if i == 0:
            hall(f"JZ_Main_{i}", ix, iy, 10, 8, 4, m)
        elif i % 2 == 0:
            add_cyl(f"JZ_Pav_{i}", (ix, iy, s*0.1), 2, 0.2, verts=6, mat=m['wm'])
            pillar(ix, iy, 3, m, 0.15)
            add_cone(f"JZ_PavR_{i}", (ix, iy, 4.5), 2.5, 1.5, mat=m['roof_y'])
        for j in range(random.randint(2,4)):
            tree(f"JZ_T{i}_{j}", ix+random.uniform(-s*0.5,s*0.5), iy+random.uniform(-s*0.5,s*0.5), random.uniform(4,7), m)

# ============================================================
# 方壶胜境（七层宝塔）
# ============================================================
def build_fanghu(m):
    bx, by = 30, -20
    for layer in range(7):
        sz = 3 - layer*0.25
        hz = layer*1.6
        add_cube(f"FH_{layer}", (bx, by, hz+0.8), (sz, sz, 0.7), m['marble'])
        add_cone(f"FH_eave_{layer}", (bx, by, hz+1.5), sz*1.1, 0.5, mat=m['roof_y'])
    for side in [-1, 1]:
        hall(f"FH_Side_{side}", bx+side*10, by, 8, 6, 3, m)

# ============================================================
# 场景组装
# ============================================================
def build_all():
    m = mats()

    # 地面
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.01))
    bpy.context.active_object.name = "Ground"
    bpy.context.active_object.data.materials.append(m['grass'])

    # 水面
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.01))
    w = bpy.context.active_object
    w.name = "Water"
    w.scale = (125, 100, 1)
    w.data.materials.append(m['water'])

    # 核心景区
    build_dashuifa(m)
    build_jiuzhou(m)
    build_fanghu(m)

    # 正大光明殿
    hall("Zhengda", -30, 10, 24, 16, 6, m)
    hall("Side_L", -65, 10, 14, 10, 4, m)
    hall("Side_R", 5, 10, 14, 10, 4, m)

    # 桥梁
    for bx, by, bw, bl in [(0,-8,4,10), (-15,5,3,8), (15,5,3,8)]:
        add_cube(f"Bridge_{bx}_{by}", (bx, by, 1.2), (bw/2, bl/2, 0.2), m['marble'])

    # 树木（40棵）
    for i in range(40):
        tx = random.uniform(-100, 100)
        ty = random.uniform(-80, 80)
        if abs(ty) < 20 and abs(tx) < 50: continue
        tree(f"T_{i}", tx, ty, random.uniform(6,12), m)

    # 假山（10组）
    for i in range(10):
        rock(random.uniform(-80,80), random.uniform(-60,60), random.uniform(1.5,3), m)

    # 草地粒子
    for i in range(200):
        add_ico(f"G_{i}", (random.uniform(-100,100), random.uniform(-80,80), random.uniform(0.03,0.1)),
                random.uniform(0.08,0.2), sub=1, mat=random.choice([m['grass'],m['grass2']]))

# ============================================================
# 灯光、相机、渲染
# ============================================================
def setup():
    # 太阳
    bpy.ops.object.light_add(type='SUN', location=(50,-50,100))
    s = bpy.context.active_object
    s.name = "Sun"
    s.data.energy = 3.0
    s.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))

    # 补光
    bpy.ops.object.light_add(type='AREA', location=(0,0,30))
    f = bpy.context.active_object
    f.data.energy = 500
    f.data.size = 50

    # 环境
    bpy.context.scene.world.use_nodes = True
    wn = bpy.context.scene.world.node_tree.nodes
    wn.clear()
    bg = wn.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.4, 0.5, 0.7, 1.0)
    bg.inputs['Strength'].default_value = 0.3
    out = wn.new('ShaderNodeOutputWorld')
    bpy.context.scene.world.node_tree.links.new(bg.outputs['Background'], out.inputs['Surface'])

    # 相机
    bpy.ops.object.camera_add(location=(100,-100,60))
    c = bpy.context.active_object
    c.name = "Main_Camera"
    c.rotation_euler = (math.radians(60), 0, math.radians(45))
    c.data.lens = 35
    bpy.context.scene.camera = c

    # 渲染设置
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 256
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 2048
    sc.render.resolution_y = 1536

def export():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        use_selection=True,
        export_format='GLB',
        export_apply=True,
        export_materials='EXPORT'
    )
    print(f"导出: {OUTPUT_GLB}")

def main():
    print("构建圆明园完整场景...")
    clear_scene()
    build_all()
    setup()
    export()
    print("完成!")

if __name__ == "__main__":
    main()
