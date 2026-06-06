"""
简洁渲染脚本 - 直接渲染已打开的场景
"""
import bpy
import os

scene = bpy.context.scene

# 输出路径
output_dir = os.path.expanduser("~/Desktop/WX hermes workspace/yuanmingyuan-3d/output")
output_path = os.path.join(output_dir, "dashuifa_render_v2.png")

# 检查场景中有什么
print(f"场景对象数: {len(bpy.data.objects)}")
for obj in bpy.data.objects[:10]:
    print(f"  - {obj.name} ({obj.type})")

# 设置渲染引擎
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64  # 低采样快速测试
scene.cycles.use_denoising = True

# 分辨率
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

# 色彩管理
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - High Contrast'
    print("✓ AgX色彩管理")
except:
    scene.view_settings.view_transform = 'Standard'
    print("✓ Standard色彩管理（AgX不可用）")

# 输出
scene.render.filepath = output_path

# 渲染
print(f"开始渲染: {output_path}")
bpy.ops.render.render(write_still=True)
print(f"✅ 渲染完成: {output_path}")
