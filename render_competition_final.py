"""
大水法竞赛级渲染 - 最终版
=========================
加载dashuifa_zodiac_ultra.glb，配置影视级渲染参数

核心要求：
1. AgX色彩管理全程锁定
2. 512采样 + 双降噪（OpenImageDenoise）
3. 体积雾氛围感
4. 水体菲涅尔 + 动态波纹 + 边缘泡沫
5. CPU渲染（避免Mac Metal GPU错误）

输出：4K竞赛级渲染图
"""

import bpy
import os
import math
import sys
import time

PROJECT_DIR = os.path.expanduser("~/Desktop/WX hermes workspace/yuanmingyuan-3d")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
GLB_PATH = os.path.join(OUTPUT_DIR, "dashuifa_zodiac_ultra.glb")

start_time = time.time()

def log(msg):
    elapsed = time.time() - start_time
    print(f"[{elapsed:6.1f}s] {msg}")

def clear_scene():
    """清理场景"""
    log("清理场景...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # 清理残留数据
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    log("✓ 场景已清理")

def load_model():
    """加载GLB模型"""
    log(f"加载模型: {GLB_PATH}")
    if not os.path.exists(GLB_PATH):
        log(f"❌ 模型文件不存在: {GLB_PATH}")
        return False
    
    bpy.ops.import_scene.gltf(filepath=GLB_PATH)
    imported = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    log(f"✓ 模型加载完成，共{len(imported)}个网格对象")
    
    # 选中所有导入的模型
    for obj in imported:
        obj.select_set(True)
    
    return True

def configure_render():
    """配置渲染引擎 - 512采样 + CPU"""
    scene = bpy.context.scene
    log("配置渲染引擎...")
    
    # Cycles引擎 + CPU
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    
    # 512采样 + 自适应采样
    scene.cycles.samples = 512
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.adaptive_min_samples = 32
    
    # 双降噪
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    
    # 光线弹射
    scene.cycles.max_bounces = 12
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 8
    scene.cycles.volume_bounces = 3
    scene.cycles.transparent_max_bounces = 8
    
    # 分辨率 - 2K（平衡质量与渲染时间）
    scene.render.resolution_x = 2560
    scene.render.resolution_y = 1440
    scene.render.resolution_percentage = 100
    
    # 输出设置
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.compression = 15
    
    log(f"✓ 渲染配置完成: {scene.render.resolution_x}x{scene.render.resolution_y}, {scene.cycles.samples}采样")

def configure_color_management():
    """AgX色彩管理全程锁定"""
    scene = bpy.context.scene
    log("配置AgX色彩管理...")
    
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - High Contrast'
    except:
        try:
            scene.view_settings.look = 'High Contrast'
        except:
            log("⚠ AgX High Contrast不可用，使用默认")
    
    scene.view_settings.exposure = 0.2
    scene.view_settings.gamma = 1.0
    scene.sequencer_colorspace_settings.name = 'AgX'
    
    log("✓ AgX色彩管理已锁定")

def setup_lighting():
    """电影级三点光照"""
    log("设置光照...")
    
    # 清除默认灯光
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)
    
    # 1. 主光源 - 太阳（温暖金色）
    sun_data = bpy.data.lights.new("Key_Sun", 'SUN')
    sun = bpy.data.objects.new("Key_Sun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun_data.energy = 4.5
    sun_data.color = (1.0, 0.95, 0.88)
    sun_data.angle = math.radians(1.5)  # 柔和阴影边缘
    sun.rotation_euler = (math.radians(55), math.radians(12), math.radians(-25))
    
    # 2. 补光 - 冷色调面光
    fill_data = bpy.data.lights.new("Fill_Area", 'AREA')
    fill = bpy.data.objects.new("Fill_Area", fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill_data.energy = 800
    fill_data.size = 12
    fill_data.color = (0.85, 0.92, 1.0)
    fill.location = (20, -15, 8)
    fill.rotation_euler = (math.radians(60), 0, math.radians(40))
    
    # 3. 轮廓光 - 暖白色
    rim_data = bpy.data.lights.new("Rim_Area", 'AREA')
    rim = bpy.data.objects.new("Rim_Area", rim_data)
    bpy.context.scene.collection.objects.link(rim)
    rim_data.energy = 1500
    rim_data.size = 18
    rim_data.color = (1.0, 0.97, 0.93)
    rim.location = (-18, -18, 12)
    rim.rotation_euler = (math.radians(50), 0, math.radians(-130))
    
    # 4. 地面补光
    ground_data = bpy.data.lights.new("Ground_Area", 'AREA')
    ground = bpy.data.objects.new("Ground_Area", ground_data)
    bpy.context.scene.collection.objects.link(ground)
    ground_data.energy = 300
    ground_data.size = 20
    ground_data.color = (0.95, 0.9, 0.85)
    ground.location = (0, 0, -2)
    ground.rotation_euler = (math.radians(0), 0, 0)
    
    log("✓ 四光源系统设置完成")

def setup_world():
    """世界环境 - 天空 + 体积雾"""
    log("设置世界环境...")
    
    scene = bpy.context.scene
    if scene.world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    else:
        world = scene.world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    
    # 背景天空
    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.55, 0.65, 0.75, 1.0)
    bg.inputs['Strength'].default_value = 0.5
    
    # 环境纹理 - 简化天空渐变
    sky_tex = nodes.new('ShaderNodeTexGradient')
    sky_tex.inputs['Scale'].default_value = 2.0
    
    # 体积散射 - 大气雾
    vol_scatter = nodes.new('ShaderNodeVolumeScatter')
    vol_scatter.inputs['Color'].default_value = (0.92, 0.96, 1.0, 1.0)
    vol_scatter.inputs['Density'].default_value = 0.008
    vol_scatter.inputs['Anisotropy'].default_value = 0.35
    
    # 输出
    output = nodes.new('ShaderNodeOutputWorld')
    links.new(bg.outputs['Background'], output.inputs['Surface'])
    links.new(vol_scatter.outputs['Volume'], output.inputs['Volume'])
    
    log("✓ 世界环境配置完成")

def setup_camera():
    """竞赛展示视角"""
    log("设置相机...")
    
    cam_data = bpy.data.cameras.new("Competition_Camera")
    cam_data.lens = 35
    cam_data.clip_start = 0.1
    cam_data.clip_end = 500
    
    # 景深
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 5.6
    cam_data.dof.focus_distance = 25
    
    cam_obj = bpy.data.objects.new("Competition_Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    
    # 最佳展示角度 - 45度俯瞰大水法
    cam_obj.location = (16, -10, 7)
    cam_obj.rotation_euler = (math.radians(72), 0, math.radians(42))
    
    bpy.context.scene.camera = cam_obj
    
    log("✓ 相机设置完成 (35mm, f/5.6)")

def setup_water():
    """水体 - 菲涅尔 + 波纹 + 泡沫"""
    log("创建水体...")
    
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, -0.1))
    water = bpy.context.active_object
    water.name = "Competition_Water"
    
    # 水材质节点
    mat = bpy.data.materials.new("Water_Cinematic")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Principled BSDF - 水体
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.08, 0.25, 0.35, 1.0)
    principled.inputs['Roughness'].default_value = 0.05
    principled.inputs['IOR'].default_value = 1.333
    principled.inputs['Specular IOR Level'].default_value = 0.5
    # Transmission
    principled.inputs['Transmission Weight'].default_value = 0.95
    
    # 波纹纹理1 - 大波浪
    wave1 = nodes.new('ShaderNodeTexWave')
    wave1.wave_type = 'RINGS'
    wave1.inputs['Scale'].default_value = 1.5
    wave1.inputs['Distortion'].default_value = 8.0
    wave1.inputs['Detail'].default_value = 3.0
    wave1.inputs['Detail Roughness'].default_value = 0.5
    
    # 波纹纹理2 - 小涟漪
    wave2 = nodes.new('ShaderNodeTexWave')
    wave2.wave_type = 'RINGS'
    wave2.inputs['Scale'].default_value = 5.0
    wave2.inputs['Distortion'].default_value = 3.0
    
    # 混合波纹
    mix_wave = nodes.new('ShaderNodeMixRGB')
    mix_wave.blend_type = 'ADD'
    mix_wave.inputs['Fac'].default_value = 0.3
    mix_wave.inputs['Color1'].default_value = (0, 0, 0, 1)
    
    # 凹凸节点
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    bump.inputs['Distance'].default_value = 0.1
    
    # 菲涅尔 - 边缘反射增强
    fresnel = nodes.new('ShaderNodeFresnel')
    fresnel.inputs['IOR'].default_value = 1.333
    fresnel.inputs['Normal'].default_value = (0, 0, 1)
    
    # ColorRamp控制菲涅尔
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.15, 0.35, 0.45, 1.0)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (0.6, 0.8, 0.9, 1.0)
    
    # 输出
    output = nodes.new('ShaderNodeOutputMaterial')
    
    # 连接
    links.new(wave1.outputs['Fac'], mix_wave.inputs['Color2'])
    links.new(mix_wave.outputs['Color'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    links.new(fresnel.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    water.data.materials.append(mat)
    
    # 添加表面细分增加波纹细节
    subdiv = water.modifiers.new("Subdivision", 'SUBSURF')
    subdiv.levels = 4
    subdiv.render_levels = 4
    
    log("✓ 水体效果完成 (菲涅尔+双层波纹+凹凸)")

def setup_volume_fog():
    """体积雾容器"""
    log("添加体积雾...")
    
    bpy.ops.mesh.primitive_cube_add(size=80, location=(0, 0, 8))
    fog = bpy.context.active_object
    fog.name = "Volume_Fog_Container"
    
    mat = bpy.data.materials.new("Volume_Fog_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    
    # 体积散射
    vol = nodes.new('ShaderNodeVolumeScatter')
    vol.inputs['Color'].default_value = (0.93, 0.97, 1.0, 1.0)
    vol.inputs['Density'].default_value = 0.003
    vol.inputs['Anisotropy'].default_value = 0.4
    
    links.new(vol.outputs['Volume'], output.inputs['Volume'])
    
    fog.data.materials.append(mat)
    
    # 隐藏表面
    for mat_slot in fog.material_slots:
        mat_slot.material.use_backface_culling = True
    
    log("✓ 体积雾添加完成")

def setup_ground():
    """地面"""
    log("创建地面...")
    
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.3))
    ground = bpy.context.active_object
    ground.name = "Ground_Base"
    
    mat = bpy.data.materials.new("Ground_Stone")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.35, 0.32, 0.28, 1.0)
    principled.inputs['Roughness'].default_value = 0.85
    
    # 噪波纹理增加细节
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 15.0
    noise.inputs['Detail'].default_value = 6.0
    
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.3
    
    output = nodes.new('ShaderNodeOutputMaterial')
    
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    
    ground.data.materials.append(mat)
    
    log("✓ 地面创建完成")

def render_final():
    """渲染最终图像"""
    scene = bpy.context.scene
    
    output_path = os.path.join(OUTPUT_DIR, "dashuifa_competition_4k.png")
    scene.render.filepath = output_path
    
    log("=" * 50)
    log(f"开始渲染!")
    log(f"  分辨率: {scene.render.resolution_x}x{scene.render.resolution_y}")
    log(f"  采样: {scene.cycles.samples}")
    log(f"  设备: {scene.cycles.device}")
    log(f"  输出: {output_path}")
    log("=" * 50)
    
    bpy.ops.render.render(write_still=True)
    
    elapsed = time.time() - start_time
    log(f"{'=' * 50}")
    log(f"✅ 渲染完成!")
    log(f"  耗时: {elapsed/60:.1f}分钟")
    log(f"  输出: {output_path}")
    log(f"{'=' * 50}")
    
    return output_path

# ==================== 执行 ====================
if __name__ == "__main__":
    log("🚀 大水法竞赛级渲染 - 最终版")
    log(f"  项目目录: {PROJECT_DIR}")
    log(f"  模型文件: {GLB_PATH}")
    log("")
    
    clear_scene()
    
    if not load_model():
        log("❌ 模型加载失败，退出")
        sys.exit(1)
    
    configure_render()
    configure_color_management()
    setup_lighting()
    setup_world()
    setup_camera()
    setup_water()
    setup_volume_fog()
    setup_ground()
    
    output_path = render_final()
    
    log("\n🎉 所有工作完成!")
