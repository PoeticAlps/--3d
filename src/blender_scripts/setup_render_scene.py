"""
圆明园场景渲染优化脚本
包含：
1. AgX色彩管理（替代ACES，Blender 5.1稳定）
2. 体积云 + 体积雾
3. 环境光照设置
4. 渲染输出配置
"""

import bpy
import math

# ==================== 清理场景 ====================
def clean_scene():
    """清理默认场景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # 清理材质
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)

# ==================== AgX色彩管理 ====================
def setup_agx_color_management():
    """设置AgX色彩管理（Blender 5.1推荐，替代ACES）"""
    scene = bpy.context.scene
    
    # 设置色彩管理
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.view_transform = 'AgX'  # 使用AgX
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.sequencer_colorspace_settings.name = 'sRGB'
    
    print("✅ AgX色彩管理已启用")

# ==================== 体积云 ====================
def create_volumetric_clouds(location=(0, 0, 50), size=100):
    """创建体积云层"""
    
    # 云层域
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cloud = bpy.context.active_object
    cloud.name = "CloudVolume"
    cloud.scale = (size, size, 10)
    
    # 创建体积云材质
    mat = bpy.data.materials.new("VolumetricCloud")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 输出节点
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # 体积散射节点
    vol_scatter = nodes.new('ShaderNodeVolumeScatter')
    vol_scatter.location = (0, 0)
    vol_scatter.inputs['Color'].default_value = (0.95, 0.95, 0.98, 1)  # 淡蓝白色
    vol_scatter.inputs['Density'].default_value = 0.02
    vol_scatter.inputs['Anisotropy'].default_value = 0.3
    
    # 体积吸收节点
    vol_absorb = nodes.new('ShaderNodeVolumeAbsorption')
    vol_absorb.location = (0, -150)
    vol_absorb.inputs['Color'].default_value = (0.9, 0.85, 0.8, 1)
    vol_absorb.inputs['Density'].default_value = 0.005
    
    # 混合体积
    mix_vol = nodes.new('ShaderNodeMixShader')
    mix_vol.location = (200, 0)
    mix_vol.inputs['Fac'].default_value = 0.5
    
    # 连接节点
    mat.node_tree.links.new(vol_scatter.outputs['Volume'], mix_vol.inputs[1])
    mat.node_tree.links.new(vol_absorb.outputs['Volume'], mix_vol.inputs[2])
    mat.node_tree.links.new(mix_vol.outputs['Shader'], output.inputs['Volume'])
    
    cloud.data.materials.append(mat)
    
    print("✅ 体积云已创建")
    return cloud

# ==================== 体积雾 ====================
def create_volumetric_fog(density=0.008):
    """创建地面体积雾"""
    
    # 雾域
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 5))
    fog = bpy.context.active_object
    fog.name = "VolumetricFog"
    fog.scale = (60, 60, 8)
    
    # 体积雾材质
    mat = bpy.data.materials.new("VolumetricFog")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    vol_scatter = nodes.new('ShaderNodeVolumeScatter')
    vol_scatter.location = (0, 0)
    vol_scatter.inputs['Color'].default_value = (0.85, 0.82, 0.78, 1)  # 暖白色
    vol_scatter.inputs['Density'].default_value = density
    vol_scatter.inputs['Anisotropy'].default_value = 0.5
    
    # 渐变遮罩（底部浓，顶部淡）
    gradient = nodes.new('ShaderNodeTexGradient')
    gradient.location = (-300, 0)
    
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-500, 0)
    mapping.inputs['Rotation'].default_value = (0, 0, 0)
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-700, 0)
    
    # 连接
    mat.node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    mat.node_tree.links.new(mapping.outputs['Vector'], gradient.inputs['Vector'])
    
    mat.node_tree.links.new(vol_scatter.outputs['Volume'], output.inputs['Volume'])
    
    fog.data.materials.append(mat)
    
    print("✅ 体积雾已创建")
    return fog

# ==================== 环境光照 ====================
def setup_lighting():
    """设置环境光照"""
    
    # 太阳光
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 100))
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.95, 0.9)  # 暖色阳光
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))
    
    # 天空环境光
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputWorld')
    output.location = (400, 0)
    
    sky = nodes.new('ShaderNodeTexSky')
    sky.location = (0, 0)
    sky.sky_type = 'HOSEK_WILKIE'  # Blender 5.1可用的天空模型
    sky.sun_elevation = math.radians(45)
    sky.sun_rotation = math.radians(30)
    
    # 背景节点
    background = nodes.new('ShaderNodeBackground')
    background.location = (200, 0)
    background.inputs['Strength'].default_value = 0.5
    
    # 连接
    world.node_tree.links.new(sky.outputs['Color'], background.inputs['Color'])
    world.node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
    
    # 补光（柔和）
    bpy.ops.object.light_add(type='AREA', location=(-15, -20, 15))
    fill = bpy.context.active_object
    fill.name = "FillLight"
    fill.data.energy = 200
    fill.data.size = 10
    fill.data.color = (0.9, 0.95, 1.0)  # 冷色补光
    fill.rotation_euler = (math.radians(60), 0, math.radians(-45))
    
    print("✅ 环境光照已设置")

# ==================== 地面 ====================
def create_ground():
    """创建地面"""
    bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    
    # 地面材质
    mat = bpy.data.materials.new("GroundMarble")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = (0.85, 0.82, 0.78, 1)
    principled.inputs['Roughness'].default_value = 0.4
    principled.inputs['Metallic'].default_value = 0.0
    
    mat.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    ground.data.materials.append(mat)
    
    print("✅ 地面已创建")
    return ground

# ==================== 相机设置 ====================
def setup_camera():
    """设置相机"""
    bpy.ops.object.camera_add(location=(25, -25, 12))
    camera = bpy.context.active_object
    camera.name = "MainCamera"
    
    # 指向场景中心
    constraint = camera.constraints.new(type='TRACK_TO')
    target = bpy.data.objects.new("CameraTarget", None)
    bpy.context.scene.collection.objects.link(target)
    target.location = (0, 0, 2)
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    
    # 相机设置
    bpy.context.scene.camera = camera
    camera.data.lens = 35
    camera.data.clip_end = 1000
    
    print("✅ 相机已设置")
    return camera

# ==================== 渲染设置 ====================
def setup_render_settings():
    """设置渲染参数"""
    scene = bpy.context.scene
    
    # 使用Cycles渲染器
    scene.render.engine = 'CYCLES'
    
    # GPU加速（如果有）
    if bpy.context.preferences.addons.get('cycles'):
        prefs = bpy.context.preferences.addons['cycles'].preferences
        try:
            prefs.compute_device_type = 'CUDA'  # NVIDIA
        except:
            try:
                prefs.compute_device_type = 'OPTIX'
            except:
                prefs.compute_device_type = 'HIP'  # AMD
        
        scene.cycles.device = 'GPU'
    
    # 渲染采样
    scene.cycles.samples = 512
    scene.cycles.preview_samples = 64
    
    # 降噪
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    
    # 光线追踪设置
    scene.cycles.max_bounces = 12
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 8
    scene.cycles.volume_bounces = 2
    
    # 输出设置
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    
    # 输出路径
    output_path = "/Users/saint/Desktop/WX hermes workspace/yuanmingyuan-3d/output/renders/"
    import os
    os.makedirs(output_path, exist_ok=True)
    scene.render.filepath = output_path
    
    print("✅ 渲染设置完成")

# ==================== 导入大水法模型 ====================
def import_dashuifa_model():
    """导入大水法兽首模型"""
    model_path = "/Users/saint/Desktop/WX hermes workspace/yuanmingyuan-3d/output/dashuifa_zodiac_ultra.glb"
    
    import os
    if not os.path.exists(model_path):
        # 尝试Hermes路径
        model_path = os.path.expanduser("~/Desktop/WX hermes workspace/yuanmingyuan-3d/output/dashuifa_zodiac_ultra.glb")
    
    if os.path.exists(model_path):
        bpy.ops.import_scene.gltf(filepath=model_path)
        print("✅ 已导入大水法模型")
        return True
    else:
        print("⚠️ 未找到大水法模型文件")
        return False

# ==================== 主函数 ====================
def setup_render_scene():
    """设置完整渲染场景"""
    print("=== 设置渲染场景 ===\n")
    
    clean_scene()
    
    print("1. 设置AgX色彩管理...")
    setup_agx_color_management()
    
    print("2. 创建地面...")
    create_ground()
    
    print("3. 设置环境光照...")
    setup_lighting()
    
    print("4. 导入大水法模型...")
    import_dashuifa_model()
    
    print("5. 创建体积雾...")
    create_volumetric_fog()
    
    print("6. 创建体积云...")
    create_volumetric_clouds()
    
    print("7. 设置相机...")
    setup_camera()
    
    print("8. 配置渲染设置...")
    setup_render_settings()
    
    print("\n" + "="*50)
    print("✅ 渲染场景设置完成！")
    print("="*50)
    
    # 保存blend文件
    blend_path = "/Users/saint/Desktop/WX hermes workspace/yuanmingyuan-3d/scenes/dashuifa_render.blend"
    import os
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"\n📁 已保存: {blend_path}")

# ==================== 执行 ====================
if __name__ == "__main__":
    setup_render_scene()
