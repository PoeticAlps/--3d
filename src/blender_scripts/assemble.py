"""
Blender场景组装脚本 - 圆明园数字重建

使用方法:
    blender --background --python assemble.py
    
或者在Blender Python控制台中运行:
    exec(open("assemble.py").read())
"""

import bpy
import os
import sys
from pathlib import Path

# ============================================================
# 配置
# ============================================================

# 场景配置
SCENE_CONFIG = {
    "name": "Yuanmingyuan_Reborn",
    "units": "METRIC",
    "scale": 1.0,  # 1单位 = 1米
}

# 景区布局 (相对于中心的位置，单位：米)
SCENES_LAYOUT = {
    "dashuifa": {
        "name": "大水法",
        "position": (0, 0, 0),
        "rotation": (0, 0, 0),
        "scale": (1, 1, 1),
    },
    "jiuzhouqingyan": {
        "name": "九州清晏",
        "position": (200, 0, 0),
        "rotation": (0, 0, 0),
        "scale": (1, 1, 1),
    },
    "fangpuxianjing": {
        "name": "方壶胜境",
        "position": (0, 200, 0),
        "rotation": (0, 0, 0),
        "scale": (1, 1, 1),
    },
    "zhengdaguangming": {
        "name": "正大光明",
        "position": (-200, 0, 0),
        "rotation": (0, 0, 0),
        "scale": (1, 1, 1),
    },
}

# 模型路径
MODELS_DIR = Path(__file__).parent.parent.parent / "data" / "processed" / "models"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


# ============================================================
# 工具函数
# ============================================================

def clear_scene():
    """清空场景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # 清空材质
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    
    print("✓ 场景已清空")


def setup_scene():
    """设置场景属性"""
    scene = bpy.context.scene
    
    # 设置单位
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    
    # 设置渲染引擎
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    
    # 设置分辨率
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    
    print("✓ 场景设置完成")


def import_model(filepath: str, location: tuple = (0, 0, 0)):
    """
    导入3D模型
    
    支持格式: .glb, .gltf, .obj, .fbx
    """
    filepath = str(filepath)
    
    if not os.path.exists(filepath):
        print(f"  ⚠️ 模型不存在: {filepath}")
        return None
    
    # 根据文件扩展名选择导入器
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext in ['.glb', '.gltf']:
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif ext == '.obj':
        bpy.ops.import_scene.obj(filepath=filepath)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=filepath)
    else:
        print(f"  ⚠️ 不支持的格式: {ext}")
        return None
    
    # 获取导入的对象
    imported_objects = bpy.context.selected_objects
    
    if imported_objects:
        # 创建空对象作为父级
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=location)
        parent = bpy.context.active_object
        parent.name = os.path.basename(filepath)
        
        # 将导入的对象设为子级
        for obj in imported_objects:
            obj.parent = parent
        
        print(f"  ✓ 已导入: {os.path.basename(filepath)}")
        return parent
    
    return None


def add_water(size: int = 500, location: tuple = (0, 0, -0.5)):
    """
    添加水面
    """
    bpy.ops.mesh.primitive_plane_add(size=size, location=location)
    water = bpy.context.active_object
    water.name = "Water"
    
    # 创建水材质
    mat = bpy.data.materials.new(name="Water_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.0, 0.1, 0.2, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['IOR'].default_value = 1.33
    
    # 添加输出节点
    output = nodes.new('ShaderNodeOutputMaterial')
    
    # 连接节点
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    water.data.materials.append(mat)
    
    print("✓ 水面已添加")
    return water


def add_sky():
    """
    添加天空环境
    """
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    
    # 添加天空纹理
    sky = nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'NISHITA'
    sky.sun_elevation = 0.8
    sky.sun_rotation = 0.5
    
    # 添加背景节点
    background = nodes.new('ShaderNodeBackground')
    output = nodes.new('ShaderNodeOutputWorld')
    
    # 连接
    world.node_tree.links.new(sky.outputs['Color'], background.inputs['Color'])
    world.node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
    
    print("✓ 天空环境已添加")


def add_lighting():
    """
    添加灯光
    """
    # 太阳光
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 100))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 5.0
    sun.rotation_euler = (0.785, 0, 0.785)  # 45度角
    
    # 补光
    bpy.ops.object.light_add(type='AREA', location=(50, -50, 30))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 500
    fill.data.size = 10
    
    print("✓ 灯光已添加")


def assemble_scene():
    """
    组装完整场景
    """
    print("=" * 60)
    print("🏛️ 圆明园场景组装")
    print("=" * 60)
    
    # 清空并设置场景
    clear_scene()
    setup_scene()
    
    # 添加环境
    add_water()
    add_sky()
    add_lighting()
    
    # 导入各景区模型
    print("\n📦 导入景区模型...")
    
    for scene_id, config in SCENES_LAYOUT.items():
        print(f"\n  处理: {config['name']}")
        
        model_path = MODELS_DIR / f"{scene_id}.glb"
        
        if model_path.exists():
            obj = import_model(
                str(model_path),
                location=config["position"]
            )
            if obj:
                obj.rotation_euler = config["rotation"]
                obj.scale = config["scale"]
        else:
            print(f"    ⚠️ 模型未找到，创建占位符")
            # 创建占位符
            bpy.ops.mesh.primitive_cube_add(
                size=10,
                location=config["position"]
            )
            placeholder = bpy.context.active_object
            placeholder.name = f"Placeholder_{config['name']}"
    
    # 添加摄像机
    bpy.ops.object.camera_add(location=(100, -100, 50))
    camera = bpy.context.active_object
    camera.name = "Main_Camera"
    camera.rotation_euler = (1.1, 0, 0.785)
    bpy.context.scene.camera = camera
    
    print("\n" + "=" * 60)
    print("✅ 场景组装完成!")
    print("=" * 60)


def export_scene(output_path: str = None):
    """
    导出场景为GLB格式
    """
    if not output_path:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(OUTPUT_DIR / "yuanmingyuan_scene.glb")
    
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True
    )
    
    print(f"✓ 场景已导出: {output_path}")
    return output_path


def render_preview(output_path: str = None):
    """
    渲染预览图
    """
    if not output_path:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(OUTPUT_DIR / "preview.png")
    
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    
    print(f"✓ 预览图已渲染: {output_path}")
    return output_path


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("🏛️ 圆明园数字重建 - Blender场景组装")
    print("=" * 60)
    
    # 组装场景
    assemble_scene()
    
    # 导出
    print("\n📦 导出场景...")
    export_scene()
    
    # 渲染预览（可选）
    # render_preview()
    
    print("\n🎉 全部完成!")
