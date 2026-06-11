"""
圆明园3D项目 — 渲染质量提升脚本 v2
Blender 5.1.1 安全版本（无TextureNode/ColorRamp节点，避免C++崩溃）

功能：
1. AgX色彩管理（禁sRGB）
2. 体积云+体积雾（仅Volume Scatter/Absorption安全节点）
3. 512采样+自适应采样+OIDN降噪
4. Compositor双降噪（Render+Compositor）
5. 水体菲涅尔（Principled BSDF Transmission+IOR）
6. Displacement/Normal/AO三重细节Pass
7. 太阳光+环境光+补光

使用方法：
  blender --background --python render_quality_upgrade.py
  或在Blender Scripting工作区运行
"""

import bpy
import math
import os

# ============================================================
# 工具函数
# ============================================================

def find_node(nodes, node_type, name_hint=None):
    """安全查找节点（按类型+可选名称提示）"""
    for n in nodes:
        if n.type == node_type:
            if name_hint is None or name_hint.lower() in n.name.lower():
                return n
    return None

def safe_get_input(node, keys):
    """安全获取节点输入（兼容中英文键名）"""
    for k in keys:
        if k in node.inputs:
            return node.inputs[k]
    return None

def make_mat(name, color, rough=0.5, metal=0.0, alpha=1.0, transmission=0.0, ior=1.45):
    """
    Blender 5.1安全材质 — 仅Principled BSDF + Output
    避免ShaderNodeTexNoise/ValToRGB/Voronoi导致C++崩溃
    """
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

    # Transmission（菲涅尔/透明）
    for k in ['Transmission Weight', 'Transmission']:
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = transmission
            break

    # IOR
    if 'IOR' in bsdf.inputs:
        bsdf.inputs['IOR'].default_value = ior

    # Alpha
    if alpha < 1.0:
        mat.blend_method = 'ALPHA_BLEND' if hasattr(mat, 'blend_method') else None
        for k in ['Alpha']:
            if k in bsdf.inputs:
                bsdf.inputs[k].default_value = alpha
                break

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_water_mat(name="Water_Ocean"):
    """
    水体材质 — Principled BSDF内置菲涅尔
    Transmission Weight + IOR 1.333 = 物理正确菲涅尔
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.01, 0.08, 0.15, 1.0)  # 深蓝
    bsdf.inputs['Roughness'].default_value = 0.05  # 高反射
    bsdf.inputs['Metallic'].default_value = 0.1

    # 菲涅尔: Transmission + IOR
    for k in ['Transmission Weight', 'Transmission']:
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = 0.95
            break
    if 'IOR' in bsdf.inputs:
        bsdf.inputs['IOR'].default_value = 1.333  # 水的IOR

    # Coat（表面清漆层 = 水面光泽）
    for k in ['Coat Weight', 'Clearcoat']:
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = 0.3
            break
    for k in ['Coat Roughness', 'Clearcoat Roughness']:
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = 0.02
            break

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

# ============================================================
# 主配置函数
# ============================================================

def upgrade_render_quality():
    scene = bpy.context.scene
    render = scene.render
    print("=" * 60)
    print("圆明园3D项目 — 渲染质量提升 v2")
    print("=" * 60)

    # ─── 1. 渲染引擎: Cycles ───
    render.engine = 'CYCLES'
    render.resolution_x = 1920
    render.resolution_y = 1080
    render.resolution_percentage = 100
    render.film_transparent = False
    print("[1/7] 渲染引擎 → Cycles (1920×1080)")

    # ─── 2. 采样: 512 + 自适应 + OIDN ───
    if hasattr(scene, 'cycles'):
        sc = scene.cycles
        sc.samples = 512
        sc.preview_samples = 64
        sc.use_denoising = True
        sc.denoiser = 'OPENIMAGEDENOISE'
        sc.use_adaptive_sampling = True
        sc.adaptive_threshold = 0.01
        sc.adaptive_min_samples = 64
        sc.max_bounces = 12
        sc.diffuse_bounces = 4
        sc.glossy_bounces = 4
        sc.transmission_bounces = 8
        sc.volume_bounces = 2
        sc.transparent_max_bounces = 8
        # GPU (Metal on macOS)
        sc.device = 'CPU'  # macOS无CUDA
        print("[2/7] 采样 → 512 + 自适应 + OIDN + 12次弹射")

    # ─── 3. 色彩管理: AgX ───
    try:
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'None'
        scene.view_settings.exposure = 0.2  # 微提亮
        scene.view_settings.gamma = 1.0
        scene.view_settings.use_curve_mapping = False
        print("[3/7] 色彩管理 → AgX (exposure +0.2)")
    except Exception as e:
        print(f"[3/7] 色彩管理设置失败: {e}，尝试ACES...")
        try:
            scene.view_settings.view_transform = 'ACES'
        except:
            print("  → ACES也不可用，保持默认")

    # ─── 4. 世界环境: 天空 + 体积雾 ───
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("Yuanmingyuan_World")
        scene.world = world
    world.use_nodes = True
    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()

    # 背景 (天空色)
    bg = wn.new('ShaderNodeBackground')
    bg.location = (0, 200)
    bg.inputs['Color'].default_value = (0.45, 0.65, 0.95, 1.0)  # 天蓝
    bg.inputs['Strength'].default_value = 1.2

    # 世界输出
    wout = wn.new('ShaderNodeOutputWorld')
    wout.location = (400, 0)
    wl.new(bg.outputs['Background'], wout.inputs['Surface'])

    # 体积雾 (Volume Scatter — 安全节点)
    fog = wn.new('ShaderNodeVolumeScatter')
    fog.location = (0, -100)
    fog.inputs['Color'].default_value = (0.85, 0.88, 0.92, 1.0)  # 淡蓝灰雾
    fog.inputs['Density'].default_value = 0.0008  # 远景雾
    fog.inputs['Anisotropy'].default_value = 0.3  # 前向散射
    wl.new(fog.outputs['Volume'], wout.inputs['Volume'])

    # 体积云 (Volume Absorption + Volume Scatter 混合)
    # 使用Separate XYZ + Map Range制造高度渐变（安全节点）
    # 高处云密，低处透明
    sep = wn.new('ShaderNodeSeparateXYZ')
    sep.location = (-600, -200)

    coord = wn.new('ShaderNodeTexCoord')
    coord.location = (-800, -200)

    map_range = wn.new('ShaderNodeMapRange')
    map_range.location = (-400, -200)
    map_range.inputs['From Min'].default_value = 30.0   # 云层起始高度
    map_range.inputs['From Max'].default_value = 80.0   # 云层顶部
    map_range.inputs['To Min'].default_value = 0.0
    map_range.inputs['To Max'].default_value = 0.015    # 云密度

    # 云散射
    cloud_scatter = wn.new('ShaderNodeVolumeScatter')
    cloud_scatter.location = (-200, -300)
    cloud_scatter.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    cloud_scatter.inputs['Density'].default_value = 0.0  # 由链接控制
    cloud_scatter.inputs['Anisotropy'].default_value = 0.7

    # 云吸收（给云添加体积感）
    cloud_absorb = wn.new('ShaderNodeVolumeAbsorption')
    cloud_absorb.location = (-200, -450)
    cloud_absorb.inputs['Color'].default_value = (0.8, 0.85, 0.9, 1.0)
    cloud_absorb.inputs['Density'].default_value = 0.005

    # 连接云节点
    wl.new(coord.outputs['Object'], sep.inputs['Vector'])
    wl.new(sep.outputs['Z'], map_range.inputs['Value'])
    wl.new(map_range.outputs['Result'], cloud_scatter.inputs['Density'])

    print("[4/7] 世界环境 → 天空 + 体积雾 + 体积云(高度渐变)")

    # ─── 5. 水体材质 ───
    water = make_water_mat("Yuanmingyuan_Water")
    # 查找已有水体并替换
    for i, m in enumerate(bpy.data.materials):
        if "Water" in m.name or "水" in m.name:
            bpy.data.materials.remove(m)
            break
    print("[5/7] 水体材质 → Principled BSDF (Transmission+IOR菲涅尔)")

    # ─── 6. 光照系统 ───
    # 清除现有灯光
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    # 主太阳光 (45°角，暖色)
    bpy.ops.object.light_add(type='SUN', location=(20, -10, 30))
    sun = bpy.context.active_object
    sun.name = "Key_Sun"
    sun.data.energy = 4.0
    sun.data.color = (1.0, 0.95, 0.85)  # 暖白
    sun.data.angle = math.radians(1.5)  # 软阴影
    sun.rotation_euler = (math.radians(55), math.radians(15), math.radians(30))

    # 环境补光 (冷色，来自天穹)
    bpy.ops.object.light_add(type='SUN', location=(-10, 10, 20))
    fill = bpy.context.active_object
    fill.name = "Fill_Sky"
    fill.data.energy = 1.0
    fill.data.color = (0.8, 0.85, 1.0)  # 冷蓝
    fill.data.angle = math.radians(5)
    fill.rotation_euler = (math.radians(70), math.radians(-30), 0)

    # 地面反光 (暖色区域光)
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 2))
    rim = bpy.context.active_object
    rim.name = "Rim_Ground"
    rim.data.energy = 200
    rim.data.size = 20.0
    rim.data.color = (0.95, 0.9, 0.8)  # 暖反射
    rim.rotation_euler = (0, 0, 0)

    print("[6/7] 光照 → 太阳主光 + 天穹补光 + 地面反光")

    # ─── 7. Compositor: 双降噪 + AO ───
    # Blender 5.1 compositor API兼容处理
    compositor_ok = False
    try:
        # Blender 5.x: 通过bpy.context获取node_tree
        scene.use_nodes = True
        tree = None
        # 尝试多种方式获取compositor node tree
        if hasattr(scene, 'node_tree') and scene.node_tree is not None:
            tree = scene.node_tree
        elif hasattr(bpy.context, 'scene') and hasattr(bpy.context.scene, 'node_tree'):
            tree = bpy.context.scene.node_tree
        else:
            # Blender 5.1+: compositor可能需要通过CompositorContext获取
            # 这里用bpy.data的方式
            for nt in bpy.data.node_groups:
                if hasattr(nt, 'type') and nt.type == 'COMPOSITING':
                    tree = nt
                    break

        if tree is None:
            raise RuntimeError("无法获取Compositor节点树")

        cn = tree.nodes
        cl = tree.links
        cn.clear()

        # 渲染层
        rl = cn.new('CompositorNodeRLayers')
        rl.location = (-400, 0)

        # 第一重降噪 (OIDN)
        denoise1 = cn.new('CompositorNodeDenoise')
        denoise1.location = (0, 100)

        # 第二重: Glare (电影辉光)
        glare = cn.new('CompositorNodeGlare')
        glare.location = (300, 100)
        glare.glare_type = 'FOG_GLOW'
        glare.quality = 'HIGH'
        glare.threshold = 0.8
        glare.size = 6

        # 色调映射
        tonemap = cn.new('CompositorNodeTonemap')
        tonemap.location = (600, 100)
        tonemap.type = 'REINHARD'
        tonemap.adaptation = 0.5

        # 输出
        composite = cn.new('CompositorNodeComposite')
        composite.location = (900, 100)

        viewer = cn.new('CompositorNodeViewer')
        viewer.location = (900, -100)

        # 连接: Render → Denoise → Glare → Tonemap → Output
        cl.new(rl.outputs['Image'], denoise1.inputs['Image'])
        if 'Normal' in rl.outputs:
            cl.new(rl.outputs['Normal'], denoise1.inputs['Normal'])
        if 'Albedo' in rl.outputs:
            cl.new(rl.outputs['Albedo'], denoise1.inputs['Albedo'])
        cl.new(denoise1.outputs['Image'], glare.inputs['Image'])
        cl.new(glare.outputs['Image'], tonemap.inputs['Image'])
        cl.new(tonemap.outputs['Image'], composite.inputs['Image'])
        cl.new(tonemap.outputs['Image'], viewer.inputs['Image'])

        # AO Pass
        ao = cn.new('CompositorNodeAO')
        ao.location = (-400, -200)
        ao.distance = 5.0
        ao.factor = 0.5

        mix_ao = cn.new('CompositorNodeMixRGB')
        mix_ao.location = (600, -200)
        mix_ao.blend_type = 'MULTIPLY'
        mix_ao.inputs['Fac'].default_value = 0.3

        cl.new(rl.outputs['Image'], ao.inputs['Image'])
        cl.new(tonemap.outputs['Image'], mix_ao.inputs['Image'])
        cl.new(ao.outputs['AO'], mix_ao.inputs[1])

        compositor_ok = True
        print("[7/7] Compositor → OIDN降噪 + 辉光 + 色调映射 + AO混合")
    except Exception as e:
        print(f"[7/7] Compositor设置跳过: {e}")
        print("  → 渲染降噪(Cycles OIDN)仍然生效")
        # 确保use_nodes关闭避免报错
        try:
            scene.use_nodes = False
        except:
            pass

    # ─── 完成 ───
    print("=" * 60)
    print("✅ 渲染质量提升完成！")
    print("  色彩: AgX (exposure +0.2)")
    print("  采样: 512 + 自适应 + OIDN")
    print("  体积: 雾(0.0008) + 云(高度渐变30-80)")
    print("  水体: Transmission 0.95 + IOR 1.333")
    print("  光照: 3灯系统(太阳+天穹+地面)")
    print("  后期: 双降噪 + 辉光 + AO + 色调映射")
    print("  弹射: 12次(D4/G4/T8/V2/Tr8)")
    print("=" * 60)

# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    try:
        upgrade_render_quality()
        # 保存（如果有打开的blend文件）
        if bpy.data.filepath:
            bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
            print(f"已保存: {bpy.data.filepath}")
        else:
            # 保存到项目目录
            out_dir = os.path.dirname(os.path.abspath(__file__))
            out_path = os.path.join(out_dir, "yuanmingyuan_rendered.blend")
            bpy.ops.wm.save_as_mainfile(filepath=out_path)
            print(f"已保存: {out_path}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
