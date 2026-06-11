"""
圆明园场景导出脚本 - 导出为GLB格式
"""

import bpy
import os

# 导出路径
output_dir = "/Users/saint/Desktop/hermes-workspace-2/yuanmingyuan-3d/output"
os.makedirs(output_dir, exist_ok=True)

# 导出GLB
output_path = os.path.join(output_dir, "yuanmingyuan.glb")

bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_materials='EXPORT',
    export_colors=True,
    export_normals=True
)

print(f"✅ 导出完成: {output_path}")
print(f"📁 文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
