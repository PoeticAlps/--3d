import bpy

# 创建一个平面并添加Ocean修改器
bpy.ops.mesh.primitive_plane_add(size=10)
obj = bpy.context.active_object
mod = obj.modifiers.new(name="Ocean", type='OCEAN')
print("Ocean modifier attributes:")
for attr in dir(mod):
    if not attr.startswith('_'):
        print(f"  {attr}: {getattr(mod, attr, 'N/A')}")
# 检查是否存在chop_level
print("\nChecking chop_level...")
print(hasattr(mod, 'chop_level'))
print("Checking chop...")
print(hasattr(mod, 'chop'))
print("Checking chop_amount...")
print(hasattr(mod, 'chop_amount'))