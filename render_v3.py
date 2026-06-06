import bpy
import os
import math
from mathutils import Vector

scene = bpy.context.scene
output_path = "/Users/saint/Desktop/WX hermes workspace/yuanmingyuan-3d/output/dashuifa_render_v2.png"

print(f"场景对象数: {len(bpy.data.objects)}")

min_x = min_y = min_z = float('inf')
max_x = max_y = max_z = float('-inf')
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        for corner in obj.bound_box:
            v = obj.matrix_world @ Vector(corner)
            min_x = min(min_x, v.x); max_x = max(max_x, v.x)
            min_y = min(min_y, v.y); max_y = max(max_y, v.y)
            min_z = min(min_z, v.z); max_z = max(max_z, v.z)

cx = (min_x + max_x) / 2
cy = (min_y + max_y) / 2
cz = (min_z + max_z) / 2
sz = max(max_x - min_x, max_y - min_y, max_z - min_z)
print(f"中心: ({cx:.1f}, {cy:.1f}, {cz:.1f}) 尺寸: {sz:.1f}")

cam = bpy.data.cameras.new("Camera")
cam.lens = 50
cam.clip_start = 0.1
cam.clip_end = 1000
cam_obj = bpy.data.objects.new("Camera", cam)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (cx + sz * 0.8, cy - sz * 0.8, cz + sz * 0.6)
d = Vector((cx, cy, cz)) - cam_obj.location
cam_obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam_obj
print("✓ 摄像机")

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.filepath = output_path
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - High Contrast'
except:
    pass
print("✓ 渲染设置")

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
bpy.context.scene.collection.objects.link(sun)
sun.data.energy = 5.0
sun.data.color = (1.0, 0.95, 0.9)
sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))
print("✓ 灯光")

print(f"渲染: {output_path}")
bpy.ops.render.render(write_still=True)
print(f"✅ 完成: {output_path}")
