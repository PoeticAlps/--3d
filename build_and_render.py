"""
圆明园全景3D重建 + 竞赛级渲染
================================
包含：九州清晏、大水法、方壶胜境、正大光明 + 山水环境
渲染：Cycles CPU / AgX色彩 / 256采样+降噪 / 1920x1080
"""
import bpy, math, os, time

OUT = os.path.expanduser("~/Desktop/WX hermes workspace/yuanmingyuan-3d/output")
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.1f}s] {m}")

# ========== 材质系统 ==========
_mats = {}
def mat(name, color, metallic=0.0, roughness=0.5):
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    # 找到Principled BSDF（兼容中英文节点名）
    bsdf = None
    for node in n:
        if 'Principled' in node.name or '原理化' in node.name:
            bsdf = node; break
    if bsdf is None:
        bsdf = n.get('Principled BSDF') or n.get('原理化BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color[:3], 1)
        # Blender 5.1兼容：Metallic可能叫'Metallic'或'金属度'
        for k in ['Metallic', 'Metallic Weight']:
            if k in bsdf.inputs:
                bsdf.inputs[k].default_value = metallic; break
        bsdf.inputs['Roughness'].default_value = roughness
    _mats[name] = m
    return m

# ========== 建筑组件 ==========
def pillar(x, y, z, h, r, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=h, location=(x, y, z+h/2))
    o = bpy.context.active_object; o.data.materials.append(m)

def platform(x, y, z, w, d, h, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z+h/2))
    o = bpy.context.active_object; o.scale = (w/2, d/2, h/2); o.data.materials.append(m)

def roof(x, y, z, w, d, h, m, layers=1):
    for i in range(layers):
        s = 1 - i*0.15
        hh, ww, dd = h*s, w*s, d*s
        oz = i*h*0.4
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=max(ww,dd)*0.7, depth=hh, location=(x, y, z+oz+hh/2))
        o = bpy.context.active_object
        if ww > 0: o.scale.y = dd/ww
        o.rotation_euler.z = math.pi/4
        o.data.materials.append(m)

def pavilion(x, y, z, sz, rm, pm, bm):
    platform(x, y, z, sz*1.2, sz*1.2, 0.3, bm)
    pillar(x, y, z+0.3, sz*0.8, sz*0.08, pm)
    roof(x, y, z+0.3+sz*0.8, sz*0.8, sz*0.8, sz*0.5, rm)

# ========== 九州清晏 ==========
def build_jiuzhou():
    log("九州清晏...")
    gm = mat("Gold", (0.85,0.65,0.13), 0.6, 0.3)
    rm = mat("Red", (0.7,0.15,0.1), 0, 0.4)
    wm = mat("White", (0.95,0.95,0.92), 0, 0.6)
    pd = mat("Wood", (0.55,0.27,0.07), 0, 0.5)
    cx, cy = 0, 0
    # 三层主殿
    for i, (sw,sd,sh,rh) in enumerate([(6,5,1,1.2),(4.5,3.8,0.8,1),(3,2.5,0.6,0.8)]):
        z = i*4.2
        platform(cx, cy, z, sw, sd, sh, wm)
        n = 4 if i == 0 else 4
        for j in range(n):
            a = j*math.pi/2 + (i*math.pi/4)
            pillar(cx+math.cos(a)*1.8*(1-i*0.15), cy+math.sin(a)*1.4*(1-i*0.15), z+sh, 2-i*0.3, 0.14-i*0.02, pd)
        roof(cx, cy, z+sh, sw-0.5, sd-0.5, rh, gm)
    # 左右配殿
    for s in [-1,1]:
        sx = cx+s*6
        platform(sx, cy, 0, 3, 3, 0.6, gm)
        for j in range(4):
            a = j*math.pi/2
            pillar(sx+math.cos(a)*1, cy+math.sin(a)*1, 0.6, 1.5, 0.1, pd)
        roof(sx, cy, 2.1, 3, 3, 0.8, gm)
    # 围廊
    for s in [-1,1]:
        for i in range(3):
            pillar(cx+s*(2+i*1.2), cy-2, 0.3, 1.2, 0.08, pd)

# ========== 大水法 ==========
def build_dashuifa():
    log("大水法...")
    sm = mat("Stone", (0.85,0.82,0.75), 0, 0.7)
    bm = mat("Bronze", (0.4,0.35,0.25), 0.8, 0.3)
    x, y = 15, 0
    # 主基座
    platform(x, y, 0, 7, 2.5, 1, sm)
    # 两侧石柱
    for s in [-1,1]:
        bx = x+s*2.8
        platform(bx, y, 1, 0.9, 1.8, 3.5, sm)
        platform(bx, y, 4.5, 1.1, 2, 0.5, sm)
        # 柱顶装饰球
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(bx, y, 5.2))
        o = bpy.context.active_object; o.data.materials.append(bm)
    # 中央拱门
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.8, location=(x, y, 3.2))
    o = bpy.context.active_object; o.scale = (1, 0.4, 1); o.data.materials.append(sm)
    # 顶部尖塔
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1.2, radius2=0.2, depth=2, location=(x, y, 6))
    o = bpy.context.active_object; o.data.materials.append(sm)
    # 喷泉水池
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, -0.2))
    o = bpy.context.active_object; o.scale = (5.5, 2.5, 0.4); o.data.materials.append(sm)
    # 水面
    wm = mat("PoolWater", (0.3,0.6,0.8,0.6), 0, 0.05)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, 0.05))
    o = bpy.context.active_object; o.scale = (5, 2, 1); o.data.materials.append(wm)
    # 铜像（简化兽首）
    for i in range(3):
        sx = x+(i-1)*2.2
        platform(sx, y, 1, 0.6, 0.6, 0.5, sm)
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.22, depth=1.2, location=(sx, y, 1.85))
        o = bpy.context.active_object; o.data.materials.append(bm)
        # 头部
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(sx, y, 2.6))
        o = bpy.context.active_object; o.data.materials.append(bm)
    # 喷泉水柱
    for i in range(7):
        fx = x+(i-3)*1
        fz = 1+abs(i-3)*0.4
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.04, depth=fz, location=(fx, y, fz/2+0.5))
        o = bpy.context.active_object; o.data.materials.append(wm)

# ========== 方壶胜境 ==========
def build_fanghu():
    log("方壶胜境...")
    gm = mat("Green", (0.2,0.45,0.25), 0, 0.8)
    rk = mat("Rock", (0.5,0.48,0.45), 0, 0.9)
    gd = mat("Gold_F", (0.85,0.65,0.13), 0.6, 0.3)
    wd = mat("Wood_F", (0.55,0.27,0.07), 0, 0.5)
    wh = mat("White_F", (0.95,0.95,0.92), 0, 0.6)
    x, y = -12, 10
    # 假山群
    for mx,my,mw,md,mh in [(0,0,3,2,4),(-2,1.5,2,1.5,3),(2,1,2.5,2,3.5),(-1,-1.5,2,1.8,2.5)]:
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=max(mw,md), depth=mh, location=(x+mx,y+my,mh/2))
        o = bpy.context.active_object
        if mw > 0: o.scale.y = md/mw
        o.data.materials.append(rk)
    pavilion(x, y, 4, 1.2, gd, wd, wh)
    # 瀑布
    wm = mat("Wfall", (0.4,0.7,0.9,0.7), 0, 0.1)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.18, depth=3.5, location=(x-1,y+1,1.8))
    o = bpy.context.active_object; o.rotation_euler.x = math.pi/6; o.data.materials.append(wm)

# ========== 正大光明 ==========
def build_zhengda():
    log("正大光明...")
    gd = mat("Gold_Z", (0.9,0.7,0.15), 0.7, 0.25)
    rd = mat("Red_Z", (0.75,0.15,0.1), 0, 0.4)
    mb = mat("Marble", (0.92,0.9,0.85), 0, 0.3)
    pd = mat("Pillar_R", (0.65,0.12,0.08), 0, 0.4)
    x, y = 0, -12
    # 三层汉白玉基座
    for i in range(3):
        s = 1-i*0.15
        platform(x, y, i*0.5, 8*s, 5*s, 0.5, mb)
    # 丹陛石
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y+2.5, 1.6))
    o = bpy.context.active_object; o.scale = (1.5,0.8,0.1); o.data.materials.append(mb)
    # 12根大柱
    for row in range(2):
        for col in range(6):
            pillar(x+(col-2.5)*1.2, y+(row-0.5)*3, 1.5, 3, 0.18, pd)
    # 红墙
    for s in [-1,1]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x+s*3.5, y, 3))
        o = bpy.context.active_object; o.scale = (0.2,2.5,1.5); o.data.materials.append(rd)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y-2.5, 3))
    o = bpy.context.active_object; o.scale = (3.5,0.15,1.5); o.data.materials.append(rd)
    # 重檐庑殿顶
    roof(x, y, 4.5, 7.5, 4.5, 0.8, gd)
    platform(x, y, 5.3, 5, 3.5, 0.4, rd)
    roof(x, y, 5.7, 4.8, 3.3, 1, gd)
    # 脊兽
    for i in range(5):
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.15, depth=0.3, location=(x+(i-2)*1.5, y+2, 7))
        o = bpy.context.active_object; o.data.materials.append(gd)
    # 月台栏杆
    for i in range(8):
        for s in [-1,1]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.08, depth=0.6, location=(x+(i-3.5), y+s*3.2, 1.8))
            o = bpy.context.active_object; o.data.materials.append(mb)

# ========== 山水环境 ==========
def build_landscape():
    log("山水环境...")
    # 湖面
    wm = mat("Lake", (0.25,0.5,0.7,0.6), 0, 0.05)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,-0.05))
    o = bpy.context.active_object; o.scale = (30,25,1); o.data.materials.append(wm)
    # 地面
    gm = mat("Ground", (0.25,0.4,0.2), 0, 0.9)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0,0,-0.15))
    o = bpy.context.active_object; o.scale = (50,50,1); o.data.materials.append(gm)
    # 远山
    fm = mat("FarMtn", (0.4,0.5,0.45), 0, 0.8)
    for i in range(8):
        mx = (i-3.5)*8
        mh = 3+(i%3)*2.5
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=4+(i%2)*2, depth=mh, location=(mx,28,mh/2-0.1))
        o = bpy.context.active_object; o.data.materials.append(fm)
    # 石桥
    bm = mat("Bridge", (0.88,0.86,0.82), 0, 0.6)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,-5,0.1))
    o = bpy.context.active_object; o.scale = (1.5,4,0.15); o.data.materials.append(bm)
    for s in [-1,1]:
        for i in range(5):
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.06, depth=0.5, location=(s*1.2,-5+(i-2)*1.5,0.4))
            o = bpy.context.active_object; o.data.materials.append(bm)

# ========== 渲染环境 ==========
def setup_render():
    log("渲染环境...")
    sc = bpy.context.scene
    # Cycles CPU
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 256
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.volume_bounces = 2
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1080
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    # AgX
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - High Contrast'
    except: pass
    sc.view_settings.exposure = 0.3
    log("Cycles CPU / AgX / 256采样")

def setup_lighting():
    log("光照...")
    # 太阳
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun",'SUN'))
    bpy.context.scene.collection.objects.link(sun)
    sun.data.energy = 5; sun.data.color = (1,0.95,0.88); sun.data.angle = math.radians(1.5)
    sun.rotation_euler = (math.radians(55), math.radians(12), math.radians(-25))
    # 补光
    fl = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill",'AREA'))
    bpy.context.scene.collection.objects.link(fl)
    fl.data.energy = 800; fl.data.size = 12; fl.data.color = (0.85,0.92,1)
    fl.location = (20,-15,8); fl.rotation_euler = (math.radians(60),0,math.radians(40))
    # 轮廓光
    rl = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim",'AREA'))
    bpy.context.scene.collection.objects.link(rl)
    rl.data.energy = 1500; rl.data.size = 18; rl.data.color = (1,0.97,0.93)
    rl.location = (-18,-18,12); rl.rotation_euler = (math.radians(50),0,math.radians(-130))

def setup_world():
    log("世界环境...")
    sc = bpy.context.scene
    if sc.world is None: sc.world = bpy.data.worlds.new("World")
    w = sc.world; w.use_nodes = True
    n = w.node_tree.nodes; l = w.node_tree.links; n.clear()
    bg = n.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.55,0.65,0.75,1)
    bg.inputs['Strength'].default_value = 0.5
    vs = n.new('ShaderNodeVolumeScatter')
    vs.inputs['Color'].default_value = (0.92,0.96,1,1)
    vs.inputs['Density'].default_value = 0.008
    vs.inputs['Anisotropy'].default_value = 0.35
    o = n.new('ShaderNodeOutputWorld')
    l.new(bg.outputs['Background'], o.inputs['Surface'])
    l.new(vs.outputs['Volume'], o.inputs['Volume'])

def setup_camera():
    log("相机...")
    cd = bpy.data.cameras.new("Cam")
    cd.lens = 35; cd.dof.use_dof = True; cd.dof.aperture_fstop = 5.6
    c = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(c)
    c.location = (20, -18, 14)
    c.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = c

def setup_volume_fog():
    log("体积雾...")
    bpy.ops.mesh.primitive_cube_add(size=100, location=(0,0,10))
    f = bpy.context.active_object; f.name = "Fog"
    m = bpy.data.materials.new("FogMat"); m.use_nodes = True
    n = m.node_tree.nodes; l = m.node_tree.links; n.clear()
    vs = n.new('ShaderNodeVolumeScatter')
    vs.inputs['Color'].default_value = (0.93,0.97,1,1)
    vs.inputs['Density'].default_value = 0.003
    vs.inputs['Anisotropy'].default_value = 0.4
    o = n.new('ShaderNodeOutputMaterial')
    l.new(vs.outputs['Volume'], o.inputs['Volume'])
    f.data.materials.append(m)

# ========== 主程序 ==========
if __name__ == "__main__":
    log("🏯 圆明园全景3D重建 + 竞赛渲染")
    
    # 清理
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # 建模
    build_landscape()
    build_jiuzhou()
    build_dashuifa()
    build_fanghu()
    build_zhengda()
    
    # 渲染设置
    setup_render()
    setup_lighting()
    setup_world()
    setup_camera()
    setup_volume_fog()
    
    # 渲染
    out_path = os.path.join(OUT, "yuanmingyuan_scene_render.png")
    bpy.context.scene.render.filepath = out_path
    log(f"开始渲染 → {out_path}")
    bpy.ops.render.render(write_still=True)
    
    fsize = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    log(f"✅ 渲染完成! {fsize/1024:.0f}KB, 耗时{(time.time()-t0)/60:.1f}分钟")
