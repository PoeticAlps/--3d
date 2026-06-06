"""
大水法竞赛级渲染 - 正式版
=========================
CPU渲染，AgX色彩管理，256采样+降噪
"""

import bpy, os, math, sys, time

PROJECT = os.path.expanduser("~/Desktop/WX hermes workspace/yuanmingyuan-3d")
OUTPUT = os.path.join(PROJECT, "output")
GLB = os.path.join(OUTPUT, "dashuifa_zodiac_ultra.glb")
OUT_FILE = os.path.join(OUTPUT, "dashuifa_final_render.png")

t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.1f}s] {m}")

# 1. 清理
log("清理场景...")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 2. 加载模型
log(f"加载: {GLB}")
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.context.selected_objects if o.type == 'MESH']
log(f"导入 {len(meshes)} 个网格")

# 3. 渲染设置
sc = bpy.context.scene
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
log(f"渲染: {sc.render.resolution_x}x{sc.render.resolution_y}, {sc.cycles.samples}采样")

# 4. AgX色彩管理
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - High Contrast'
except: pass
sc.view_settings.exposure = 0.3
log("AgX锁定")

# 5. 清除灯光
for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)

# 6. 太阳光
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sc.collection.objects.link(sun)
sun.data.energy = 5.0
sun.data.color = (1.0, 0.95, 0.88)
sun.data.angle = math.radians(1.5)
sun.rotation_euler = (math.radians(55), math.radians(12), math.radians(-25))

# 7. 补光
fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
sc.collection.objects.link(fill)
fill.data.energy = 800
fill.data.size = 12
fill.data.color = (0.85, 0.92, 1.0)
fill.location = (20, -15, 8)
fill.rotation_euler = (math.radians(60), 0, math.radians(40))

rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", 'AREA'))
sc.collection.objects.link(rim)
rim.data.energy = 1500
rim.data.size = 18
rim.data.color = (1.0, 0.97, 0.93)
rim.location = (-18, -18, 12)
rim.rotation_euler = (math.radians(50), 0, math.radians(-130))
log("三光源设置完成")

# 8. 世界环境
if sc.world is None:
    sc.world = bpy.data.worlds.new("World")
world = sc.world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
bg = wn.new('ShaderNodeBackground')
bg.inputs['Color'].default_value = (0.55, 0.65, 0.75, 1.0)
bg.inputs['Strength'].default_value = 0.5
vol = wn.new('ShaderNodeVolumeScatter')
vol.inputs['Color'].default_value = (0.92, 0.96, 1.0, 1.0)
vol.inputs['Density'].default_value = 0.008
vol.inputs['Anisotropy'].default_value = 0.35
out = wn.new('ShaderNodeOutputWorld')
wl.new(bg.outputs['Background'], out.inputs['Surface'])
wl.new(vol.outputs['Volume'], out.inputs['Volume'])
log("世界环境+体积雾")

# 9. 相机
cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 35
cam_d.dof.use_dof = True
cam_d.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("Cam", cam_d)
sc.collection.objects.link(cam)
cam.location = (16, -10, 7)
cam.rotation_euler = (math.radians(72), 0, math.radians(42))
sc.camera = cam
log("相机设置完成")

# 10. 水面
bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, -0.1))
water = bpy.context.active_object
water.name = "Water"
wm = bpy.data.materials.new("WaterMat")
wm.use_nodes = True
wn2 = wm.node_tree.nodes
wl2 = wm.node_tree.links
wn2.clear()
pr = wn2.new('ShaderNodeBsdfPrincipled')
pr.inputs['Base Color'].default_value = (0.08, 0.25, 0.35, 1.0)
pr.inputs['Roughness'].default_value = 0.05
pr.inputs['IOR'].default_value = 1.333
pr.inputs['Transmission Weight'].default_value = 0.95
wv = wn2.new('ShaderNodeTexWave')
wv.wave_type = 'RINGS'
wv.inputs['Scale'].default_value = 2.0
wv.inputs['Distortion'].default_value = 6.0
wv.inputs['Detail'].default_value = 3.0
bmp = wn2.new('ShaderNodeBump')
bmp.inputs['Strength'].default_value = 0.12
fs = wn2.new('ShaderNodeFresnel')
fs.inputs['IOR'].default_value = 1.333
cp = wn2.new('ShaderNodeValToRGB')
cp.color_ramp.elements[0].position = 0.3
cp.color_ramp.elements[0].color = (0.1, 0.3, 0.4, 1.0)
cp.color_ramp.elements[1].position = 0.8
cp.color_ramp.elements[1].color = (0.5, 0.75, 0.85, 1.0)
o2 = wn2.new('ShaderNodeOutputMaterial')
wl2.new(wv.outputs['Fac'], bmp.inputs['Height'])
wl2.new(bmp.outputs['Normal'], pr.inputs['Normal'])
wl2.new(fs.outputs['Fac'], cp.inputs['Fac'])
wl2.new(cp.outputs['Color'], pr.inputs['Base Color'])
wl2.new(pr.outputs['BSDF'], o2.inputs['Surface'])
water.data.materials.append(wm)
log("水面材质完成")

# 11. 地面
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.3))
gnd = bpy.context.active_object
gnd.name = "Ground"
gm = bpy.data.materials.new("GndMat")
gm.use_nodes = True
gn = gm.node_tree.nodes
gl = gm.node_tree.links
gn.clear()
gp = gn.new('ShaderNodeBsdfPrincipled')
gp.inputs['Base Color'].default_value = (0.35, 0.32, 0.28, 1.0)
gp.inputs['Roughness'].default_value = 0.85
gn2 = gn.new('ShaderNodeTexNoise')
gn2.inputs['Scale'].default_value = 15.0
gn2.inputs['Detail'].default_value = 6.0
gb = gn.new('ShaderNodeBump')
gb.inputs['Strength'].default_value = 0.3
go = gn.new('ShaderNodeOutputMaterial')
gl.new(gn2.outputs['Fac'], gb.inputs['Height'])
gl.new(gb.outputs['Normal'], gp.inputs['Normal'])
gl.new(gp.outputs['BSDF'], go.inputs['Surface'])
gnd.data.materials.append(gm)
log("地面完成")

# 12. 体积雾容器
bpy.ops.mesh.primitive_cube_add(size=80, location=(0, 0, 8))
fog = bpy.context.active_object
fog.name = "Fog"
fm = bpy.data.materials.new("FogMat")
fm.use_nodes = True
fn = fm.node_tree.nodes
fl = fm.node_tree.links
fn.clear()
fv = fn.new('ShaderNodeVolumeScatter')
fv.inputs['Color'].default_value = (0.93, 0.97, 1.0, 1.0)
fv.inputs['Density'].default_value = 0.003
fv.inputs['Anisotropy'].default_value = 0.4
fo = fn.new('ShaderNodeOutputMaterial')
fl.new(fv.outputs['Volume'], fo.inputs['Volume'])
fog.data.materials.append(fm)
log("体积雾完成")

# 13. 渲染
sc.render.filepath = OUT_FILE
log(f"开始渲染 → {OUT_FILE}")
bpy.ops.render.render(write_still=True)

fsize = os.path.getsize(OUT_FILE) if os.path.exists(OUT_FILE) else 0
log(f"✅ 渲染完成! {fsize/1024:.0f}KB, 耗时{(time.time()-t0)/60:.1f}分钟")
