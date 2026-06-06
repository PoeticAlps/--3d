import bpy
import math

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_material(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

def create_roof(x, y, z, width, depth, height, mat, layers=2):
    """创建多层中式屋顶"""
    for i in range(layers):
        scale = 1.0 - i * 0.15
        h = height * scale
        w = width * scale
        d = depth * scale
        offset_z = i * height * 0.4
        
        bpy.ops.mesh.primitive_cone_add(
            vertices=4,
            radius1=max(w, d) * 0.7,
            depth=h,
            location=(x, y, z + offset_z + h/2)
        )
        roof = bpy.context.active_object
        roof.scale.y = d / w if w > 0 else 1
        roof.rotation_euler.z = math.pi / 4
        roof.data.materials.append(mat)

def create_pillar(x, y, z, height, radius, mat):
    """创建柱子"""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=radius,
        depth=height,
        location=(x, y, z + height/2)
    )
    pillar = bpy.context.active_object
    pillar.data.materials.append(mat)
    return pillar

def create_base_platform(x, y, z, width, depth, height, mat):
    """创建基座平台"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + height/2))
    base = bpy.context.active_object
    base.scale = (width/2, depth/2, height/2)
    base.data.materials.append(mat)
    return base

def create_pavilion(x, y, z, size, roof_mat, pillar_mat, base_mat):
    """创建小亭子"""
    create_base_platform(x, y, z, size*1.2, size*1.2, 0.3, base_mat)
    create_pillar(x, y, z+0.3, size*0.8, size*0.08, pillar_mat)
    create_roof(x, y, z+0.3+size*0.8, size*0.8, size*0.8, size*0.5, roof_mat, layers=1)

def create_jiuzhouqingyan():
    """创建九州清晏 - 中央最大殿宇群"""
    print("创建九州清晏...")
    
    # 材质
    gold_mat = create_material("Gold_Roof", (0.85, 0.65, 0.13, 1), metallic=0.6, roughness=0.3)
    red_mat = create_material("Red_Wall", (0.7, 0.15, 0.1, 1), roughness=0.4)
    white_mat = create_material("White_Base", (0.95, 0.95, 0.92, 1), roughness=0.6)
    wood_mat = create_material("Wood_Pillar", (0.55, 0.27, 0.07, 1), roughness=0.5)
    
    # 中央主殿 - 三层建筑
    cx, cy, cz = 0, 0, 0
    
    # 第一层
    create_base_platform(cx, cy, cz, 6, 5, 1, white_mat)
    for i in range(4):
        angle = i * math.pi / 2
        px = cx + math.cos(angle) * 2
        py = cy + math.sin(angle) * 1.5
        create_pillar(px, py, cz+1, 2, 0.15, wood_mat)
    create_roof(cx, cy, cz+3, 5.5, 4.5, 1.2, gold_mat, layers=1)
    
    # 第二层
    create_base_platform(cx, cy, cz+4.2, 4.5, 3.8, 0.8, white_mat)
    for i in range(4):
        angle = i * math.pi / 2 + math.pi/4
        px = cx + math.cos(angle) * 1.5
        py = cy + math.sin(angle) * 1.2
        create_pillar(px, py, cz+5, 1.5, 0.12, wood_mat)
    create_roof(cx, cy, cz+6.5, 4, 3.3, 1, gold_mat, layers=1)
    
    # 第三层
    create_base_platform(cx, cy, cz+7.5, 3, 2.5, 0.6, white_mat)
    create_roof(cx, cy, cz+8.1, 2.8, 2.3, 0.8, gold_mat, layers=1)
    
    # 左右配殿
    for side in [-1, 1]:
        sx = cx + side * 6
        create_base_platform(sx, cy, cz, 3, 3, 0.6, white_mat)
        for i in range(4):
            angle = i * math.pi / 2
            px = sx + math.cos(angle) * 1
            py = cy + math.sin(angle) * 1
            create_pillar(px, py, cz+0.6, 1.5, 0.1, wood_mat)
        create_roof(sx, cy, cz+2.1, 3, 3, 0.8, gold_mat, layers=1)
    
    # 前方小亭
    create_pavilion(cx, cy-5, cz, 1.5, gold_mat, wood_mat, white_mat)
    
    # 围廊连接
    for side in [-1, 1]:
       廊长 = 4
        for i in range(3):
            lx = cx + side * (2 + i * 1.2)
            create_pillar(lx, cy-2, cz+0.3, 1.2, 0.08, wood_mat)

def create_dashuifa():
    """创建大水法 - 西洋喷泉建筑"""
    print("创建大水法...")
    
    stone_mat = create_material("Stone", (0.85, 0.82, 0.75, 1), roughness=0.7)
    bronze_mat = create_material("Bronze", (0.4, 0.35, 0.25, 1), metallic=0.8, roughness=0.3)
    water_mat = create_material("Fountain_Water", (0.3, 0.6, 0.8, 0.6), roughness=0.1)
    
    x, y, z = 12, 0, 0
    
    # 主拱门结构
    create_base_platform(x, y, z, 6, 2, 1, stone_mat)
    
    # 两侧柱子
    for side in [-1, 1]:
        bx = x + side * 2.5
        create_base_platform(bx, y, z+1, 0.8, 1.5, 3, stone_mat)
        create_base_platform(bx, y, z+4, 1, 1.7, 0.5, stone_mat)
    
    # 中央拱门（用半球代替）
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16,
        ring_count=8,
        radius=1.5,
        location=(x, y, z+3)
    )
    arch = bpy.context.active_object
    arch.scale = (1, 0.5, 1)
    arch.data.materials.append(stone_mat)
    
    # 顶部装饰
    bpy.ops.mesh.primitive_cone_add(
        vertices=8,
        radius1=1,
        radius2=0.3,
        depth=1.5,
        location=(x, y, z+5.5)
    )
    top = bpy.context.active_object
    top.data.materials.append(stone_mat)
    
    # 喷泉水池
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z-0.2))
    pool = bpy.context.active_object
    pool.scale = (5, 2, 0.3)
    pool.data.materials.append(stone_mat)
    
    # 水面
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z-0.1))
    water = bpy.context.active_object
    water.scale = (4.5, 1.5, 1)
    water.data.materials.append(water_mat)
    
    # 雕塑底座和铜像
    for i in range(3):
        sx = x + (i-1) * 2
        create_base_platform(sx, y, z+1, 0.6, 0.6, 0.5, stone_mat)
        # 简化的铜像
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.2,
            depth=1,
            location=(sx, y, z+1.75)
        )
        statue = bpy.context.active_object
        statue.data.materials.append(bronze_mat)
    
    # 喷泉水柱
    for i in range(5):
        fx = x + (i-2) * 1.2
        fz = z + 1 + i * 0.3
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8,
            radius=0.05,
            depth=1,
            location=(fx, y, fz)
        )
        fountain = bpy.context.active_object
        fountain.data.materials.append(water_mat)

def create_fanghushengjing():
    """创建方壶胜境 - 山水仙境"""
    print("创建方壶胜境...")
    
    green_mat = create_material("Mountain_Green", (0.2, 0.45, 0.25, 1), roughness=0.8)
    rock_mat = create_material("Rock", (0.5, 0.48, 0.45, 1), roughness=0.9)
    gold_mat = create_material("Gold_Roof_F", (0.85, 0.65, 0.13, 1), metallic=0.6, roughness=0.3)
    wood_mat = create_material("Wood_F", (0.55, 0.27, 0.07, 1), roughness=0.5)
    white_mat = create_material("White_F", (0.95, 0.95, 0.92, 1), roughness=0.6)
    
    x, y, z = -10, 8, 0
    
    # 假山群
    mountain_positions = [
        (0, 0, 0, 3, 2, 4),
        (-2, 1.5, 0, 2, 1.5, 3),
        (2, 1, 0, 2.5, 2, 3.5),
        (-1, -1.5, 0, 2, 1.8, 2.5),
        (1.5, -1, 0, 1.8, 1.5, 2),
    ]
    
    for mx, my, mw, md, mh, _ in mountain_positions:
        bpy.ops.mesh.primitive_cone_add(
            vertices=6,
            radius1=max(mw, md),
            depth=mh,
            location=(x+mx, y+my, z+mh/2)
        )
        mt = bpy.context.active_object
        mt.scale.y = md/mw if mw > 0 else 1
        mt.data.materials.append(rock_mat)
    
    # 山顶小亭
    create_pavilion(x, y, z+4, 1.2, gold_mat, wood_mat, white_mat)
    
    # 山间楼阁
    for i in range(3):
        gx = x + (i-1) * 2.5
        gy = y + 2
        gz = z + 1.5 + i * 0.5
        create_base_platform(gx, gy, gz, 1.5, 1.2, 0.3, white_mat)
        create_roof(gx, gy, gz+0.3, 1.4, 1.1, 0.5, gold_mat, layers=1)
    
    # 小桥
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x+3, y-1, z+0.5))
    bridge = bpy.context.active_object
    bridge.scale = (1.5, 0.3, 0.1)
    bridge.data.materials.append(white_mat)
    
    # 瀑布水流
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8,
        radius=0.15,
        depth=3,
        location=(x-1, y+1, z+2)
    )
    waterfall = bpy.context.active_object
    waterfall.rotation_euler.x = math.pi/6
    water_mat = create_material("Waterfall", (0.4, 0.7, 0.9, 0.7), roughness=0.1)
    waterfall.data.materials.append(water_mat)

def create_zhengdaguangming():
    """创建正大光明 - 仿太和殿正殿"""
    print("创建正大光明...")
    
    gold_mat = create_material("Gold_ZDG", (0.9, 0.7, 0.15, 1), metallic=0.7, roughness=0.25)
    red_mat = create_material("Red_ZDG", (0.75, 0.15, 0.1, 1), roughness=0.4)
    white_mat = create_material("White_ZDG", (0.95, 0.95, 0.9, 1), roughness=0.5)
    marble_mat = create_material("Marble", (0.92, 0.9, 0.85, 1), roughness=0.3)
    
    x, y, z = 0, -10, 0
    
    # 三层汉白玉基座（仿太和殿）
    for i in range(3):
        scale = 1 - i * 0.15
        create_base_platform(x, y, z + i*0.5, 8*scale, 5*scale, 0.5, marble_mat)
    
    # 丹陛石（中央龙纹台阶）
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y+2.5, z+1.6))
    stairs = bpy.context.active_object
    stairs.scale = (1.5, 0.8, 0.1)
    stairs.data.materials.append(marble_mat)
    
    # 殿身柱子 - 12根大柱
    pillar_positions = []
    for row in range(2):
        for col in range(6):
            px = x + (col - 2.5) * 1.2
            py = y + (row - 0.5) * 3
            pillar_positions.append((px, py))
    
    for px, py in pillar_positions:
        create_pillar(px, py, z+1.5, 3, 0.18, red_mat)
    
    # 殿墙（红色）
    for side_x in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x + side_x*3.5, y, z+3))
        wall = bpy.context.active_object
        wall.scale = (0.2, 2.5, 1.5)
        wall.data.materials.append(red_mat)
    
    # 后墙
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y-2.5, z+3))
    back_wall = bpy.context.active_object
    back_wall.scale = (3.5, 0.15, 1.5)
    back_wall.data.materials.append(red_mat)
    
    # 重檐庑殿顶（两层屋顶）
    # 下层檐
    create_roof(x, y, z+4.5, 7.5, 4.5, 0.8, gold_mat, layers=1)
    # 上层
    create_base_platform(x, y, z+5.3, 5, 3.5, 0.4, red_mat)
    create_roof(x, y, z+5.7, 4.8, 3.3, 1, gold_mat, layers=1)
    
    # 脊兽装饰（简化）
    for i in range(5):
        sx = x + (i-2) * 1.5
        bpy.ops.mesh.primitive_cone_add(
            vertices=4,
            radius1=0.15,
            depth=0.3,
            location=(sx, y+2, z+7)
        )
        beast = bpy.context.active_object
        beast.data.materials.append(gold_mat)
    
    # 月台栏杆
    for i in range(8):
        lx = x + (i-3.5) * 1
        for side in [-1, 1]:
            ly = y + side * 3.2
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=6,
                radius=0.08,
                depth=0.6,
                location=(lx, ly, z+1.8)
            )
            rail = bpy.context.active_object
            rail.data.materials.append(marble_mat)

def create_landscape():
    """创建整体山水环境"""
    print("创建山水环境...")
    
    # 大湖面
    water_mat = create_material("Lake_Water", (0.25, 0.5, 0.7, 0.6), roughness=0.05)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.05))
    lake = bpy.context.active_object
    lake.scale = (25, 20, 1)
    lake.data.materials.append(water_mat)
    
    # 地面
    ground_mat = create_material("Ground", (0.25, 0.4, 0.2, 1), roughness=0.9)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.15))
    ground = bpy.context.active_object
    ground.scale = (40, 40, 1)
    ground.data.materials.append(ground_mat)
    
    # 远山
    mountain_mat = create_material("Far_Mountain", (0.4, 0.5, 0.45, 1), roughness=0.8)
    for i in range(6):
        mx = (i - 2.5) * 10
        my = 25
        mh = 3 + (i % 3) * 2
        bpy.ops.mesh.primitive_cone_add(
            vertices=8,
            radius1=4 + (i % 2) * 2,
            depth=mh,
            location=(mx, my, mh/2 - 0.1)
        )
        mt = bpy.context.active_object
        mt.data.materials.append(mountain_mat)
    
    # 石桥连接各区域
    bridge_mat = create_material("Stone_Bridge", (0.88, 0.86, 0.82, 1), roughness=0.6)
    
    # 主桥到九州清晏
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -4, 0.1))
    main_bridge = bpy.context.active_object
    main_bridge.scale = (1.2, 3, 0.15)
    main_bridge.data.materials.append(bridge_mat)
    
    # 桥栏杆
    for side in [-1, 1]:
        for i in range(4):
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=6,
                radius=0.06,
                depth=0.5,
                location=(side*1, -4 + (i-1.5)*1.5, 0.4)
            )
            rail = bpy.context.active_object
            rail.data.materials.append(bridge_mat)

def setup_lighting():
    """设置光照"""
    print("设置光照...")
    
    # 太阳光
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
    sun = bpy.context.active_object
    sun.data.energy = 3
    sun.data.color = (1, 0.95, 0.9)
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))
    
    # 补光
    bpy.ops.object.light_add(type='AREA', location=(-8, 5, 15))
    fill = bpy.context.active_object
    fill.data.energy = 200
    fill.data.color = (0.8, 0.85, 1)
    fill.data.size = 10
    
    # 环境光
    bpy.context.scene.world.use_nodes = True
    bg = bpy.context.scene.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.6, 0.7, 0.85, 1)
    bg.inputs['Strength'].default_value = 0.4

def setup_camera():
    """设置摄像机"""
    print("设置摄像机...")
    
    bpy.ops.object.camera_add(location=(18, -18, 12))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(55), 0, math.radians(45))
    cam.data.lens = 35
    bpy.context.scene.camera = cam
    
    # 渲染设置
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

def main():
    print("=" * 50)
    print("圆明园精细3D重建 - 参考复原图")
    print("=" * 50)
    
    clear_scene()
    
    # 创建各景点
    create_landscape()
    create_jiuzhouqingyan()
    create_dashuifa()
    create_fanghushengjing()
    create_zhengdaguangming()
    
    # 环境和相机
    setup_lighting()
    setup_camera()
    
    print("=" * 50)
    print("场景创建完成！")
    print("景点：九州清晏 | 大水法 | 方壶胜境 | 正大光明")
    print("=" * 50)

if __name__ == "__main__":
    main()
