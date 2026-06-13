"""
圆明园3D项目 — 新增景点建模脚本
Blender 5.1.1 安全版本

新增景点：
1. 镂月开云 — 牡丹台，康熙赏花处，三层圆形月台+牡丹花圃
2. 碧桐书院 — 乾隆读书处，方形书院+碧桐树+书卷气息
3. 海晏堂 — 十二生肖铜首喷泉主殿
4. 文源阁 — 藏书楼，仿天一阁

使用方法：
  blender --background --python build_new_spots.py
  或与 build_scene_detailed.py 配合使用
"""

import bpy
import math

# ============================================================
# 工具函数 (与render_quality_upgrade.py一致)
# ============================================================

def make_mat(name, color, rough=0.5, metal=0.0):
    """Blender 5.1安全材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_pillar(x, y, z, h, r, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=h, location=(x, y, z+h/2))
    obj = bpy.context.active_object
    obj.data.materials.append(mat)
    return obj

def make_platform(x, y, z, w, d, h, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z+h/2))
    obj = bpy.context.active_object
    obj.scale = (w/2, d/2, h/2)
    obj.data.materials.append(mat)
    return obj

def make_roof(x, y, z, w, d, h, mat):
    """简单四坡屋顶"""
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=max(w,d)*0.7, depth=h, location=(x, y, z+h/2))
    obj = bpy.context.active_object
    if w > 0:
        obj.scale.y = d/w
    obj.rotation_euler.z = math.pi/4
    obj.data.materials.append(mat)
    return obj

def make_round_roof(x, y, z, r, h, mat):
    """圆形攒尖顶"""
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=r, depth=h, location=(x, y, z+h/2))
    obj = bpy.context.active_object
    obj.data.materials.append(mat)
    return obj

def make_tree(x, y, z, trunk_h, crown_r, trunk_mat, crown_mat):
    """简单树木"""
    # 树干
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.12, depth=trunk_h, location=(x, y, z+trunk_h/2))
    trunk = bpy.context.active_object
    trunk.data.materials.append(trunk_mat)
    # 树冠
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=crown_r, location=(x, y, z+trunk_h+crown_r*0.6))
    crown = bpy.context.active_object
    crown.scale.z = 0.7
    crown.data.materials.append(crown_mat)
    return trunk, crown

# ============================================================
# 景点1: 镂月开云 (牡丹台)
# ============================================================

def create_louyuekaiyun(cx=-8, cy=12, cz=0):
    """
    镂月开云 — 康熙四十八年(1709)建
    特征：三层圆形月台，遍植牡丹，乾隆赞"国色天香"
    结构：中心圆亭+三层同心圆台+环形花圃+曲桥连接
    """
    print("创建镂月开云...")

    # 材质
    gold = make_mat("Gold_LY", (0.85, 0.65, 0.13), rough=0.3, metal=0.6)
    red = make_mat("Red_LY", (0.7, 0.15, 0.1), rough=0.4)
    white = make_mat("White_LY", (0.95, 0.93, 0.88), rough=0.5)
    wood = make_mat("Wood_LY", (0.55, 0.27, 0.07), rough=0.5)
    marble = make_mat("Marble_LY", (0.92, 0.9, 0.85), rough=0.3)
    pink = make_mat("Peony_Pink", (0.9, 0.4, 0.5), rough=0.7)
    deep_pink = make_mat("Peony_Deep", (0.8, 0.2, 0.35), rough=0.7)
    green = make_mat("Leaf_LY", (0.2, 0.45, 0.2), rough=0.8)

    # ── 第一层圆形月台（最大）──
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=6, depth=0.4, location=(cx, cy, cz+0.2))
    tier1 = bpy.context.active_object
    tier1.data.materials.append(marble)

    # 第一层栏杆（24根）
    for i in range(24):
        angle = i * math.pi * 2 / 24
        rx = cx + math.cos(angle) * 5.8
        ry = cy + math.sin(angle) * 5.8
        make_pillar(rx, ry, cz+0.4, 0.5, 0.05, marble)

    # ── 第二层圆形月台 ──
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=4, depth=0.35, location=(cx, cy, cz+0.75))
    tier2 = bpy.context.active_object
    tier2.data.materials.append(marble)

    # 第二层栏杆（16根）
    for i in range(16):
        angle = i * math.pi * 2 / 16
        rx = cx + math.cos(angle) * 3.8
        ry = cy + math.sin(angle) * 3.8
        make_pillar(rx, ry, cz+1.1, 0.45, 0.04, marble)

    # ── 第三层圆形月台（最小）──
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=2.2, depth=0.3, location=(cx, cy, cz+1.1))
    tier3 = bpy.context.active_object
    tier3.data.materials.append(marble)

    # ── 中心圆亭 ──
    # 6根圆柱
    for i in range(6):
        angle = i * math.pi * 2 / 6
        px = cx + math.cos(angle) * 1.5
        py = cy + math.sin(angle) * 1.5
        make_pillar(px, py, cz+1.4, 2.5, 0.12, red)

    # 攒尖圆顶
    make_round_roof(cx, cy, cz+3.9, 2.0, 1.5, gold)
    # 顶饰（宝顶）
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.2, location=(cx, cy, cz+5.6))
    finial = bpy.context.active_object
    finial.data.materials.append(gold)

    # ── 牡丹花圃（三层同心环）──
    # 外环花圃
    for i in range(12):
        angle = i * math.pi * 2 / 12
        fx = cx + math.cos(angle) * 5.0
        fy = cy + math.sin(angle) * 5.0
        # 花台
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.3, depth=0.15, location=(fx, fy, cz+0.55))
        bed = bpy.context.active_object
        bed.data.materials.append(marble)
        # 牡丹花（用球体模拟花丛）
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.25, location=(fx, fy, cz+0.8))
        flower = bpy.context.active_object
        flower.data.materials.append(pink if i % 2 == 0 else deep_pink)

    # 中环花圃
    for i in range(8):
        angle = i * math.pi * 2 / 8 + math.pi/8
        fx = cx + math.cos(angle) * 3.2
        fy = cy + math.sin(angle) * 3.2
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.2, location=(fx, fy, cz+1.0))
        flower = bpy.context.active_object
        flower.data.materials.append(deep_pink if i % 3 == 0 else pink)

    # ── 曲桥（连接到岸边）──
    bridge_mat = make_mat("Bridge_LY", (0.88, 0.86, 0.82), rough=0.6)
    for i in range(5):
        bx = cx + 6 + i * 1.5
        by = cy - i * 0.8  # 曲折
        bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by, cz+0.15))
        slab = bpy.context.active_object
        slab.scale = (0.7, 0.6, 0.08)
        slab.data.materials.append(bridge_mat)
        # 桥栏
        for side in [-1, 1]:
            make_pillar(bx + side*0.5, by, cz+0.2, 0.3, 0.03, bridge_mat)

    # ── 水面 ──
    water = make_mat("Water_LY", (0.01, 0.08, 0.15), rough=0.05, metal=0.1)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx+3, cy-3, cz-0.05))
    pond = bpy.context.active_object
    pond.scale = (10, 8, 1)
    pond.data.materials.append(water)

    print("  镂月开云完成: 三层圆台 + 圆亭 + 牡丹花圃 + 曲桥")

# ============================================================
# 景点2: 碧桐书院
# ============================================================

def create_bitongshuyuan(cx=8, cy=-8, cz=0):
    """
    碧桐书院 — 乾隆读书处
    特征：方形院落，四面回廊，中庭碧桐，书卷气息
    结构：正殿+东西配殿+回廊+中庭梧桐+假山水池
    """
    print("创建碧桐书院...")

    # 材质
    gold = make_mat("Gold_BT", (0.85, 0.65, 0.13), rough=0.3, metal=0.6)
    gray = make_mat("Gray_Roof_BT", (0.45, 0.43, 0.4), rough=0.6)
    red = make_mat("Red_BT", (0.7, 0.15, 0.1), rough=0.4)
    white = make_mat("White_BT", (0.95, 0.93, 0.88), rough=0.5)
    wood = make_mat("Wood_BT", (0.55, 0.27, 0.07), rough=0.5)
    dark_wood = make_mat("DarkWood_BT", (0.35, 0.18, 0.05), rough=0.5)
    marble = make_mat("Marble_BT", (0.92, 0.9, 0.85), rough=0.3)
    green = make_mat("Paulownia", (0.15, 0.4, 0.18), rough=0.8)
    water = make_mat("Water_BT", (0.01, 0.08, 0.15), rough=0.05, metal=0.1)

    # ── 正殿（面阔五间，进深三间）──
    bw, bd = 8, 5  # 殿身尺寸
    make_platform(cx, cy, cz, bw, bd, 0.5, marble)  # 台基

    # 柱网 (5×3 = 15根)
    for col in range(5):
        for row in range(3):
            px = cx + (col - 2) * 2
            py = cy + (row - 1) * 2
            make_pillar(px, py, cz+0.5, 2.8, 0.12, red)

    # 墙壁（三面实墙，正面明间开门）
    # 后墙
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy-2.5, cz+1.9))
    wall = bpy.context.active_object
    wall.scale = (4, 0.15, 1.4)
    wall.data.materials.append(white)
    # 左右墙
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx+side*4, cy, cz+1.9))
        wall = bpy.context.active_object
        wall.scale = (0.15, 2.5, 1.4)
        wall.data.materials.append(white)
    # 前墙（留门洞）
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx+side*3, cy+2.5, cz+1.9))
        wall = bpy.context.active_object
        wall.scale = (1.5, 0.15, 1.4)
        wall.data.materials.append(white)

    # 歇山顶
    make_roof(cx, cy, cz+3.3, bw+1.5, bd+1, 1.2, gray)
    # 正脊
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz+4.5))
    ridge = bpy.context.active_object
    ridge.scale = (3.5, 0.08, 0.1)
    ridge.data.materials.append(gold)

    # ── 东西配殿 ──
    for side in [-1, 1]:
        px = cx + side * 7
        make_platform(px, cy, cz, 4, 3.5, 0.4, marble)
        for col in range(3):
            for row in range(2):
                make_pillar(px+(col-1)*1.5, cy+(row-0.5)*2, cz+0.4, 2.2, 0.1, red)
        make_roof(px, cy, cz+2.6, 5, 4, 0.9, gray)

    # ── 回廊（连接正殿与配殿）──
    corridor_mat = make_mat("Corridor_BT", (0.5, 0.25, 0.06), rough=0.5)
    for side in [-1, 1]:
        for i in range(4):
            lx = cx + side * (4 + i * 0.8)
            make_pillar(lx, cy+1.5, cz+0.3, 1.8, 0.06, wood)
            make_pillar(lx, cy-1.5, cz+0.3, 1.8, 0.06, wood)
        # 廊顶
        make_platform(cx+side*5.5, cy, cz+2.1, 3, 0.6, 0.08, gray)

    # ── 中庭：两棵碧桐（梧桐树）──
    for tx, ty in [(-1.5, 0), (1.5, 0)]:
        # 树干（梧桐树干灰白色）
        trunk_mat = make_mat("Trunk_BT", (0.7, 0.68, 0.6), rough=0.7)
        make_tree(cx+tx, cy+ty, cz+0.5, 3.5, 1.8, trunk_mat, green)

    # ── 假山水池（中庭前方）──
    # 小水池
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1.2, depth=0.15, location=(cx, cy+4, cz-0.05))
    pool = bpy.context.active_object
    pool.scale.z = 0.3
    pool.data.materials.append(marble)
    # 水面
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, cy+4, cz+0.05))
    water_surface = bpy.context.active_object
    water_surface.scale = (1.1, 1.1, 1)
    water_surface.data.materials.append(water)
    # 假山石
    rock = make_mat("Rock_BT", (0.5, 0.48, 0.45), rough=0.9)
    for rx, ry, rs in [(0.4, 0.3, 0.3), (-0.3, 0.5, 0.25), (0.1, -0.2, 0.2)]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rs, location=(cx+rx, cy+4+ry, cz+0.3))
        stone = bpy.context.active_object
        stone.data.materials.append(rock)

    # ── 书卷装饰（殿前石碑）──
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy+3.5, cz+0.6))
    stela = bpy.context.active_object
    stela.scale = (0.3, 0.08, 0.5)
    stela.data.materials.append(dark_wood)

    print("  碧桐书院完成: 正殿五间 + 东西配殿 + 回廊 + 碧桐 + 假山水池")

# ============================================================
# 景点3: 海晏堂 (十二生肖铜首)
# ============================================================

def create_hanyuetang(cx=15, cy=5, cz=0):
    """
    海晏堂 — 长春园西洋楼核心区
    特征：工字形殿堂+大型喷泉池+十二生肖铜首人身像
    """
    print("创建海晏堂...")

    stone = make_mat("Stone_HY", (0.85, 0.82, 0.75), rough=0.7)
    bronze = make_mat("Bronze_HY", (0.55, 0.38, 0.18), rough=0.3, metal=0.85)
    marble_h = make_mat("Marble_HY", (0.95, 0.93, 0.9), rough=0.3)
    water_h = make_mat("Water_HY", (0.01, 0.08, 0.15), rough=0.05, metal=0.1)

    # ── 工字形殿堂 ──
    # 前殿
    make_platform(cx, cy-4, cz, 8, 4, 0.6, marble_h)
    for col in range(5):
        for row in range(2):
            make_pillar(cx+(col-2)*1.8, cy-4+(row-0.5)*2.5, cz+0.6, 3, 0.15, stone)
    make_roof(cx, cy-4, cz+3.6, 9, 5, 1, stone)

    # 后殿
    make_platform(cx, cy+4, cz, 8, 4, 0.6, marble_h)
    for col in range(5):
        for row in range(2):
            make_pillar(cx+(col-2)*1.8, cy+4+(row-0.5)*2.5, cz+0.6, 3, 0.15, stone)
    make_roof(cx, cy+4, cz+3.6, 9, 5, 1, stone)

    # 连廊
    make_platform(cx, cy, cz, 3, 6, 0.4, marble_h)
    for side in [-1, 1]:
        for i in range(3):
            make_pillar(cx+side*1.2, cy+(i-1)*2, cz+0.4, 2.5, 0.1, stone)

    # ── 大型喷泉池 ──
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=5, depth=0.3, location=(cx, cy, cz-0.15))
    outer_pool = bpy.context.active_object
    outer_pool.data.materials.append(marble_h)

    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=3.5, depth=0.2, location=(cx, cy, cz+0.05))
    inner_wall = bpy.context.active_object
    inner_wall.data.materials.append(stone)

    # 水面
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, cy, cz+0.15))
    water_hy = bpy.context.active_object
    water_hy.scale = (3.3, 3.3, 1)
    water_hy.data.materials.append(water_h)

    # ── 十二生肖铜首（简化为圆柱底座+球体头像）──
    zodiac_names = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]
    for i in range(12):
        angle = i * math.pi * 2 / 12
        zx = cx + math.cos(angle) * 4.2
        zy = cy + math.sin(angle) * 4.2
        # 人身柱
        make_pillar(zx, zy, cz+0.3, 1.2, 0.15, bronze)
        # 铜首头像
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=8, radius=0.2, location=(zx, zy, cz+1.6))
        head = bpy.context.active_object
        head.data.materials.append(bronze)
        # 基座
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.25, depth=0.15, location=(zx, zy, cz+0.2))
        base = bpy.context.active_object
        base.data.materials.append(marble_h)

    # ── 中央大水法石屏 ──
    make_platform(cx, cy, cz+0.3, 1.5, 0.3, 2, stone)
    # 顶部装饰
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.5, radius2=0.15, depth=0.8, location=(cx, cy, cz+3.5))
    top = bpy.context.active_object
    top.data.materials.append(stone)

    print("  海晏堂完成: 巴洛克殿堂 + 喷泉池 + 十二生肖铜首")

# ============================================================
# 景点4: 文源阁 (藏书楼)
# ============================================================

def create_wenyinge(cx=-15, cy=-5, cz=0):
    """
    文源阁 — 仿宁波天一阁，藏《四库全书》
    特征：两层楼阁+硬山顶+前有方池（防火）+假山
    """
    print("创建文源阁...")

    dark = make_mat("DarkRoof_WY", (0.25, 0.23, 0.22), rough=0.7)
    red = make_mat("Red_WY", (0.7, 0.15, 0.1), rough=0.4)
    white = make_mat("White_WY", (0.95, 0.93, 0.88), rough=0.5)
    wood = make_mat("Wood_WY", (0.5, 0.25, 0.06), rough=0.5)
    marble = make_mat("Marble_WY", (0.92, 0.9, 0.85), rough=0.3)
    water = make_mat("Water_WY", (0.01, 0.08, 0.15), rough=0.05, metal=0.1)

    bw, bd = 6, 4

    # ── 台基 ──
    make_platform(cx, cy, cz, bw+1, bd+1, 0.5, marble)

    # ── 第一层 ──
    for col in range(4):
        for row in range(3):
            px = cx + (col - 1.5) * 1.8
            py = cy + (row - 1) * 1.8
            make_pillar(px, py, cz+0.5, 2.5, 0.1, red)

    # 墙壁
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(cx+side*3, cy, cz+1.75))
        w = bpy.context.active_object
        w.scale = (0.12, 2, 1.25)
        w.data.materials.append(white)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy-2, cz+1.75))
    bw1 = bpy.context.active_object
    bw1.scale = (3, 0.12, 1.25)
    bw1.data.materials.append(white)

    # 第一层屋顶（硬山式）
    make_roof(cx, cy, cz+3, bw+0.5, bd+0.5, 0.8, dark)

    # ── 第二层 ──
    make_platform(cx, cy, cz+3.8, bw-0.5, bd-0.5, 0.3, white)
    for col in range(3):
        for row in range(2):
            px = cx + (col - 1) * 1.6
            py = cy + (row - 0.5) * 1.5
            make_pillar(px, py, cz+4.1, 2, 0.08, red)

    # 第二层屋顶
    make_roof(cx, cy, cz+6.1, bw, bd, 0.7, dark)

    # 脊饰
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz+6.8))
    ridge = bpy.context.active_object
    ridge.scale = (2.5, 0.06, 0.08)
    ridge.data.materials.append(white)

    # ── 方池（天一阁"天一生水"防火理念）──
    bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=2, depth=0.15, location=(cx, cy+4, cz-0.05))
    pool = bpy.context.active_object
    pool.rotation_euler.z = math.pi/4
    pool.data.materials.append(marble)

    bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, cy+4, cz+0.05))
    pool_w = bpy.context.active_object
    pool_w.scale = (1.8, 1.8, 1)
    pool_w.data.materials.append(water)

    # ── 前方小假山 ──
    rock = make_mat("Rock_WY", (0.5, 0.48, 0.45), rough=0.9)
    for rx, ry, rs in [(-0.8, 5, 0.4), (0.5, 5.5, 0.3), (0, 4.5, 0.25)]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rs, location=(cx+rx, cy+ry, cz+rs*0.5))
        stone = bpy.context.active_object
        stone.data.materials.append(rock)

    print("  文源阁完成: 两层藏书楼 + 方池防火 + 假山")

# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 50)
    print("圆明园3D项目 — 新增景点建模")
    print("=" * 50)

    create_louyuekaiyun()
    create_bitongshuyuan()
    create_hanyuetang()
    create_wenyinge()

    print("=" * 50)
    print("✅ 新增景点建模完成！")
    print("  镂月开云 | 碧桐书院 | 海晏堂 | 文源阁")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
        if bpy.data.filepath:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        else:
            import os
            out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yuanmingyuan_all_spots.blend")
            bpy.ops.wm.save_as_mainfile(filepath=out)
            print(f"已保存: {out}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
