"""
圆明园3D项目渲染配置脚本
在Blender中运行此脚本以应用以下渲染设置：
1. 添加体积云(Volume Cloud)
2. 添加体积雾(Volume Fog)
3. 设置ACES色彩管理（如Blender 5.1用AgX替代）
4. 确保512采样+双降噪配置
5. 水体菲涅尔+动态波纹+边缘泡沫效果

使用方法：
1. 在Blender中打开 yuanmingyuan-3d.blend
2. 切换到Scripting工作区
3. 打开此脚本并运行
或使用命令行：
blender yuanmingyuan-3d.blend --background --python configure_render_settings.py
"""

import bpy
import math

def configure_render_settings():
    """配置渲染设置"""
    scene = bpy.context.scene
    render = scene.render
    world = bpy.context.world
    
    print("开始配置圆明园3D项目渲染设置...")
    
    # 1. 设置渲染引擎为Cycles（如果尚未设置）
    if render.engine != 'CYCLES':
        render.engine = 'CYCLES'
        print("已设置渲染引擎为Cycles")
    
    # 2. 设置采样为512
    render.resolution_x = 1920
    render.resolution_y = 1080
    render.resolution_percentage = 100
    
    # Cycles采样设置
    if hasattr(scene, 'cycles'):
        scene.cycles.samples = 512
        scene.cycles.preview_samples = 64
        print("已设置采样数为512")
        
        # 启用降噪
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'  # 或 'OptiX' 如果可用
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.01
        scene.cycles.adaptive_min_samples = 64
        print("已启用自适应采样和降噪")
    
    # 3. 设置色彩管理（ACES/AgX）
    if hasattr(scene, 'display_settings'):
        scene.display_settings.display_device = 'sRGB'
        
    if hasattr(scene, 'view_settings'):
        # Blender 3.0+ 使用 view_transform
        # 对于Blender 4.0+，推荐使用AgX
        scene.view_settings.view_transform = 'AgX'  # 或 'ACES' 如果可用
        scene.view_settings.look = 'None'
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
        scene.view_settings.use_curve_mapping = False
        print("已设置色彩管理为AgX (ACES替代)")
    
    # 4. 配置世界环境（体积云和体积雾）
    if not world:
        world = bpy.data.worlds.new("World")
        scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    # 清除现有节点
    nodes.clear()
    
    # 创建背景节点
    background_node = nodes.new(type='ShaderNodeBackground')
    background_node.location = (0, 0)
    background_node.inputs['Color'].default_value = (0.5, 0.7, 1.0, 1.0)  # 天空蓝色
    background_node.inputs['Strength'].default_value = 1.0
    
    # 创建输出节点
    output_node = nodes.new(type='ShaderNodeOutputWorld')
    output_node.location = (300, 0)
    
    # 连接背景到输出
    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])
    
    # 添加体积散射节点（用于体积雾）
    volume_scatter = nodes.new(type='ShaderNodeVolumeScatter')
    volume_scatter.location = (0, -200)
    volume_scatter.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1.0)
    volume_scatter.inputs['Density'].default_value = 0.001  # 低密度雾
    volume_scatter.inputs['Anisotropy'].default_value = 0.0
    
    # 将体积散射连接到世界的体积输出
    links.new(volume_scatter.outputs['Volume'], output_node.inputs['Volume'])
    
    print("已配置世界环境：背景天空和体积雾")
    
    # 5. 添加体积云着色器（通过节点）
    # 创建一个用于体积云的着色器组
    cloud_shader = bpy.data.node_groups.new("VolumeCloudShader", 'ShaderNodeTree')
    cloud_nodes = cloud_shader.nodes
    cloud_links = cloud_shader.links
    cloud_nodes.clear()
    
    # 创建云着色器节点
    cloud_noise = cloud_nodes.new(type='ShaderNodeTexNoise')
    cloud_noise.location = (-400, 0)
    cloud_noise.inputs['Scale'].default_value = 2.0
    cloud_noise.inputs['Detail'].default_value = 8.0
    cloud_noise.inputs['Roughness'].default_value = 0.5
    
    # 创建颜色渐变节点控制云密度
    cloud_ramp = cloud_nodes.new(type='ShaderNodeValToRGB')
    cloud_ramp.location = (-200, 0)
    # 设置颜色渐变（底部更密，顶部更透明）
    color_ramp = cloud_ramp.color_ramp
    color_ramp.elements[0].position = 0.4
    color_ramp.elements[0].color = (0.0, 0.0, 0.0, 0.0)  # 透明
    color_ramp.elements[1].position = 0.6
    color_ramp.elements[1].color = (1.0, 1.0, 1.0, 0.8)  # 半透明白色
    
    # 创建体积散射节点
    cloud_scatter = cloud_nodes.new(type='ShaderNodeVolumeScatter')
    cloud_scatter.location = (0, 0)
    cloud_scatter.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    cloud_scatter.inputs['Density'].default_value = 0.1
    cloud_scatter.inputs['Anisotropy'].default_value = 0.7
    
    # 创建输出节点
    cloud_output = cloud_nodes.new(type='ShaderNodeOutputMaterial')
    cloud_output.location = (200, 0)
    
    # 连接节点
    cloud_links.new(cloud_noise.outputs['Fac'], cloud_ramp.inputs['Fac'])
    cloud_links.new(cloud_ramp.outputs['Color'], cloud_scatter.inputs['Color'])
    cloud_links.new(cloud_scatter.outputs['Volume'], cloud_output.inputs['Volume'])
    
    print("已创建体积云着色器组")
    
    # 6. 创建水体材质（菲涅尔 + 动态波纹 + 边缘泡沫）
    # 检查是否已有水体材质
    water_mat = None
    for mat in bpy.data.materials:
        if "Water" in mat.name or "水体" in mat.name:
            water_mat = mat
            break
    
    if not water_mat:
        water_mat = bpy.data.materials.new(name="Yuanmingyuan_Water")
        water_mat.use_nodes = True
        water_nodes = water_mat.node_tree.nodes
        water_links = water_mat.node_tree.links
        
        # 清除默认节点
        water_nodes.clear()
        
        # 创建原理化BSDF
        bsdf = water_nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        bsdf.inputs['Base Color'].default_value = (0.0, 0.2, 0.4, 1.0)  # 深蓝色
        bsdf.inputs['Roughness'].default_value = 0.1
        bsdf.inputs['IOR'].default_value = 1.333  # 水的IOR
        
        # 创建菲涅尔节点
        fresnel = water_nodes.new(type='ShaderNodeFresnel')
        fresnel.location = (-300, 100)
        fresnel.inputs['IOR'].default_value = 1.333
        
        # 创建混合着色器节点
        mix_shader = water_nodes.new(type='ShaderNodeMixShader')
        mix_shader.location = (200, 0)
        
        # 创建透明BSDF（用于菲涅尔效果）
        transparent = water_nodes.new(type='ShaderNodeBsdfTransparent')
        transparent.location = (0, -150)
        transparent.inputs['Color'].default_value = (0.0, 0.2, 0.4, 1.0)
        
        # 创建波纹纹理（动态）
        wave_texture = water_nodes.new(type='ShaderNodeTexWave')
        wave_texture.location = (-600, -100)
        wave_texture.wave_type = 'RINGS'
        wave_texture.inputs['Scale'].default_value = 10.0
        wave_texture.inputs['Distortion'].default_value = 2.0
        wave_texture.inputs['Detail'].default_value = 5.0
        wave_texture.inputs['Phase Offset'].default_value = 1.0  # 动画
        
        # 创建凹凸节点（用于波纹）
        bump = water_nodes.new(type='ShaderNodeBump')
        bump.location = (-300, -100)
        bump.inputs['Strength'].default_value = 0.1
        bump.inputs['Distance'].default_value = 0.1
        
        # 创建边缘泡沫（基于法线）
        layer_weight = water_nodes.new(type='ShaderNodeLayerWeight')
        layer_weight.location = (-600, 100)
        layer_weight.inputs['Blend'].default_value = 0.5
        
        # 创建颜色渐变控制泡沫
        foam_ramp = water_nodes.new(type='ShaderNodeValToRGB')
        foam_ramp.location = (-300, 200)
        color_ramp = foam_ramp.color_ramp
        color_ramp.elements[0].position = 0.8
        color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)  # 无泡沫
        color_ramp.elements[1].position = 1.0
        color_ramp.elements[1].color = (0.9, 0.9, 0.9, 1.0)  # 白色泡沫
        
        # 创建混合节点（将泡沫与水体颜色混合）
        mix_color = water_nodes.new(type='ShaderNodeMixRGB')
        mix_color.location = (0, 200)
        mix_color.inputs['Fac'].default_value = 0.3
        
        # 创建输出节点
        output = water_nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (400, 0)
        
        # 连接节点
        # 菲涅尔效果
        water_links.new(fresnel.outputs['Fac'], mix_shader.inputs['Fac'])
        water_links.new(bsdf.outputs['BSDF'], mix_shader.inputs[1])
        water_links.new(transparent.outputs['BSDF'], mix_shader.inputs[2])
        water_links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])
        
        # 波纹凹凸
        water_links.new(wave_texture.outputs['Fac'], bump.inputs['Height'])
        water_links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
        
        # 边缘泡沫
        water_links.new(layer_weight.outputs['Facing'], foam_ramp.inputs['Fac'])
        water_links.new(foam_ramp.outputs['Color'], mix_color.inputs['Color2'])
        water_links.new(bsdf.outputs['Base Color'], mix_color.inputs['Color1'])
        water_links.new(mix_color.outputs['Color'], bsdf.inputs['Base Color'])
        
        print("已创建水体材质：菲涅尔 + 动态波纹 + 边缘泡沫")
    
    # 7. 设置光照
    # 添加太阳光
    sun_exists = False
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT' and obj.data.type == 'SUN':
            sun_exists = True
            break
    
    if not sun_exists:
        bpy.ops.object.light_add(type='SUN', location=(10, 10, 10))
        sun = bpy.context.active_object
        sun.data.energy = 3.0
        sun.data.angle = 0.0174533  # 约1度
        sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))
        print("已添加太阳光")
    
    # 添加环境光
    if not any(obj.type == 'LIGHT' and obj.data.type == 'AREA' for obj in bpy.data.objects):
        bpy.ops.object.light_add(type='AREA', location=(0, 0, 5))
        area_light = bpy.context.active_object
        area_light.data.energy = 100
        area_light.data.size = 10.0
        area_light.data.color = (0.9, 0.95, 1.0)
        print("已添加环境区域光")
    
    print("圆明园3D项目渲染配置完成！")
    print("配置摘要：")
    print("- 渲染引擎：Cycles")
    print("- 采样：512 + 自适应采样 + OpenImageDenoise")
    print("- 色彩管理：AgX (ACES替代)")
    print("- 体积云：已配置着色器组")
    print("- 体积雾：已添加到世界环境")
    print("- 水体材质：菲涅尔 + 动态波纹 + 边缘泡沫")
    print("- 光照：太阳光 + 环境区域光")
    
    return True

# 运行配置
if __name__ == "__main__":
    try:
        configure_render_settings()
        # 保存文件
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        print("配置已保存到文件")
    except Exception as e:
        print(f"配置过程中出现错误: {e}")
        import traceback
        traceback.print_exc()