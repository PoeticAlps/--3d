# -*- coding: utf-8 -*-
"""
================================================================================
 海晏堂景区(西洋楼)· 评审级程序化建模脚本  (Blender 5.1 headless / bpy)
================================================================================
考据依据:
  - 西洋楼铜版画二十幅(乾隆五十一年 1786)之《海晏堂》+ 遗址现状 + 清华数字复原成果
  - 海晏堂为西洋楼最大建筑:主楼坐西朝东(正门朝东),两层各十一开间,中西合璧
    (西洋柱式门廊 + 中式庑殿灰瓦顶);门前向东展开八字形叠落式坡台阶,
    台阶两侧设叠落式喷水槽,十二生肖人身兽首铜像沿台阶两侧对称排列,
    每尊口中喷水,水注台阶下的主喷水池;池中央为巨型贝壳石雕 + 海豚喷水意象;
    主楼后方(西)有蓄水楼(抬高土台上的两层蓄水池建筑,供水力钟),有引水管道。
场景结构(东西向主轴;东 = +X = 入口方向;原点 = 八字台阶下主喷水池中心;地面 z=0):
  [1] 主喷水池:海棠形/椭圆池壁 + 池水 + 中央巨型贝壳石雕 + 海豚喷水        → §2/§3
  [2] 八字形叠落式坡台阶:中央坡道 + 两道叠落石阶 + 两侧叠落式喷水槽        → §4
  [3] 十二生肖人身兽首铜像 ×12(南列鼠虎龙马猴狗 / 北列牛兔蛇羊鸡猪,
      沿台阶两侧对称排列,各口喷水柱)                                      → §5
  [4] 主楼:两层各十一开间(开间 3.8m,总宽 41.8m),中央三开间门楼前凸,
      巨柱式西洋门廊 + 西式拱窗 + 中式庑殿灰瓦顶;两翼顶层为白玉栏杆平台    → §6
  [5] 蓄水楼:主楼西侧抬高土台 + 台上两层蓄水池建筑 + 引水管道意象          → §7
  [6] 环境:东西向石板主轴 + 池周步道 + 对称草坪 + 塔柏列 + 两翼矮墙        → §8
新增构件函数(中文注释对应考据):arch_window(西式拱窗)/door_surround(西式门套)
    /cascading_flight(叠落石阶)/cascade_channel(叠落喷水槽)/zodiac_statue
    (人身兽首铜像,十二兽首几何差异化)/shell_sculpture(巨型贝壳石雕)
    /dolphin(海豚喷水)/reservoir_tower(蓄水楼)/pipe_run(引水管道)
材质调色板(与 v4 场景一致,无贴图、几何承载细节):
  灰白大理石 #E8E6E0(r0.40) 白玉 #F2EDE2 铜像红铜 #9A5B3C(m0.70) 铜绿 #4A7A6A
  金饰 #E8A800(仅脊饰少量) 灰瓦 #5A5F66 朱红 #8B2020(门扉少量) 草坪/塔柏绿 池水
用法:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
      --python v4/blender/haiyantang_build.py
输出:
  /tmp/haiyantang_raw.glb(未压缩;export_apply=True 于导出时应用全部修改器)
================================================================================
"""
import bpy, bmesh, math, os, random, re
from mathutils import Vector

OUT_GLB = "/tmp/haiyantang_raw.glb"
random.seed(42)

# ---------------------------------------------------------------- 名称安全化
# Blender 5.1.1 的 namemap 唯一化会对"最后一个'.'之后的纯数字串"调用 std::stoi
# 且无保护(前两个景区脚本已踩坑);对策:ID 名一律去掉"点+数字"段并追加全局序号
_SNC = 0

def safe_name(name):
    global _SNC
    _SNC += 1
    base = re.sub(r"\.[0-9]+", "", str(name))
    return f"{base}_{_SNC:05d}"

# ---------------------------------------------------------------- 清场
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.collections):
    for b in list(block):
        block.remove(b, do_unlink=True)

# ---------------------------------------------------------------- 材质
def _mat(name, hexcol, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    c = ((hexcol >> 16 & 255) / 255, (hexcol >> 8 & 255) / 255, (hexcol & 255) / 255, 1.0)
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.use_backface_culling = False   # 双面渲染:屋面壳/水面等薄壳从背面看不发黑、不透
    return m

M = {
    "marble_g": _mat("M_灰白大理石", 0xE8E6E0, 0.40),          # 主楼墙体/石阶/池壁主材
    "jade":     _mat("M_白玉",       0xF2EDE2, 0.35),          # 台基/栏杆/门套/贝壳石雕
    "bronze":   _mat("M_红铜像",     0x9A5B3C, 0.42, 0.70),    # 十二生肖人身兽首铜像/海豚
    "verd":     _mat("M_铜绿",       0x4A7A6A, 0.55, 0.30),    # 铜绿点缀(衣领/水盘/管道)
    "gold":     _mat("M_金饰",       0xE8A800, 0.25, 0.70),    # 金色仅限脊饰少量
    "red":      _mat("M_朱红",       0x8B2020, 0.60),          # 朱红点缀(门扉/鸡冠/蛇信)
    "grass":    _mat("M_草坪",       0x557A48, 0.95),
    "cyp":      _mat("M_塔柏",       0x2E5236, 0.90),
    "gravel":   _mat("M_石板步道",   0x9A948A, 0.92),
    "tile":     _mat("M_灰瓦",       0x5A5F66, 0.55),          # 主楼中式庑殿顶(铜版画)
    "tile_d":   _mat("M_灰瓦垄",     0x4B5057, 0.58),
    "wood":     _mat("M_木门",       0x5A3E26, 0.70),
    "water":    _mat("M_池水",       0x2E6474, 0.45),
    "earth":    _mat("M_素土场地",   0x8E8878, 0.95),
    "niche":    _mat("M_窗龛暗部",   0x44484E, 0.85),
    "jet":      _mat("M_喷泉水线",   0x7FB0BE, 0.35),          # 生肖口中水线(浅色细流)
    "brick":    _mat("M_蓄水楼砖",   0xB8AFA0, 0.75),          # 蓄水楼台身(清水砖石意象)
}

root = bpy.data.collections.new("HY_海晏堂")
bpy.context.scene.collection.children.link(root)
ROOT_EMPTY = bpy.data.objects.new("HY_海晏堂", None)
bpy.context.scene.collection.objects.link(ROOT_EMPTY)

def coll(name):
    c = bpy.data.collections.new(name)
    root.children.link(c)
    return c

# ================================================================= 基础几何工厂(复用前两景区)
def _obj(name, verts, faces, mat, c, smooth=False):
    name = safe_name(name)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(verbose=False)
    me.update()
    if smooth and len(me.polygons):
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.update()
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    if mat:
        ob.data.materials.append(M[mat] if isinstance(mat, str) else mat)
    return ob

def add_box(name, size, loc, mat, c, rot_z=0.0):
    sx, sy, sz = size
    ca, sa = math.cos(rot_z), math.sin(rot_z)
    v = []
    for z in (-sz / 2, sz / 2):
        for x in (-sx / 2, sx / 2):
            for y in (-sy / 2, sy / 2):
                v.append((loc[0] + x * ca - y * sa, loc[1] + x * sa + y * ca, loc[2] + z))
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (1, 3, 7, 5), (3, 2, 6, 7), (2, 0, 4, 6)]
    return _obj(name, v, f, mat, c)

def add_cyl(name, r0, r1, h, loc, mat, c, n=12, smooth=True):
    v, f = [], []
    for z, r in ((-h / 2, r0), (h / 2, r1)):
        for i in range(n):
            a = 2 * math.pi * i / n
            v.append((loc[0] + r * math.cos(a), loc[1] + r * math.sin(a), loc[2] + z))
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, j + n, i + n))
    f.append(tuple(range(n - 1, -1, -1)))
    f.append(tuple(range(n, 2 * n)))
    return _obj(name, v, f, mat, c, smooth=smooth)

def add_beam(name, p1, p2, w, hh, mat, c):
    """沿 p1→p2 的方梁(宽 w 高 hh)"""
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    if d.length < 1e-6:
        d = Vector((1, 0, 0))
    d.normalize()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    u2 = side.cross(d).normalized()
    v = []
    for p in (p1, p2):
        for s, u in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            v.append(tuple(p + side * (s * w / 2) + u2 * (u * hh / 2)))
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return _obj(name, v, f, mat, c)

def add_prism(name, poly, z0, z1, mat, c, top_mat=None):
    n = len(poly)
    v = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, j + n, i + n))
    ob = _obj(name, v, f, mat, c)
    if top_mat:
        ob.data.materials.append(M[top_mat] if isinstance(top_mat, str) else top_mat)
        for idx, p in enumerate(ob.data.polygons):
            p.material_index = 1 if idx == 1 else 0
    return ob

def add_ico(name, r, loc, scale, subdiv, mat, c):
    name = safe_name(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    ob.data.materials.append(M[mat] if isinstance(mat, str) else mat)
    for vtx in ob.data.vertices:
        vtx.co = Vector((vtx.co.x * scale[0] + loc[0],
                         vtx.co.y * scale[1] + loc[1],
                         vtx.co.z * scale[2] + loc[2]))
    ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    ob.data.update()
    return ob

def bake_rot_x(obj, pivot, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    for vtx in obj.data.vertices:
        dy, dz = vtx.co.y - pivot[1], vtx.co.z - pivot[2]
        vtx.co.y = pivot[1] + dy * ca - dz * sa
        vtx.co.z = pivot[2] + dy * sa + dz * ca

def bake_rot_y(obj, pivot, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    for vtx in obj.data.vertices:
        dx, dz = vtx.co.x - pivot[0], vtx.co.z - pivot[2]
        vtx.co.x = pivot[0] + dx * ca + dz * sa
        vtx.co.z = pivot[2] - dx * sa + dz * ca

def bake_rot_z(obj, pivot, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    for vtx in obj.data.vertices:
        dx, dy = vtx.co.x - pivot[0], vtx.co.y - pivot[1]
        vtx.co.x = pivot[0] + dx * ca - dy * sa
        vtx.co.y = pivot[1] + dx * sa + dy * ca

# ================================================================= 屋面系统(主楼中式庑殿灰瓦顶)
_P = 40

def _rring(hw, hd, e=3.0):
    pts = []
    for i in range(_P):
        t = 2 * math.pi * i / _P
        ct, st = math.cos(t), math.sin(t)
        x = hw * (abs(ct) ** (2 / e)) * (1 if ct >= 0 else -1)
        y = hd * (abs(st) ** (2 / e)) * (1 if st >= 0 else -1)
        pts.append((x, y))
    return pts

def roof_tube(name, c, w, d, h, z0, kind="wudian", eave=1.2, lift=0.8,
              ridge_w=None, rings=8, mat="tile", ox=0.0, oy=0.0):
    """曲面屋顶壳(檐口起翘+举折曲线;支持 ox/oy 平面偏移)"""
    ridge_w = ridge_w if ridge_w else max(0.9, w * 0.05)
    hw0, hd0 = w / 2 + eave, d / 2 + eave
    rows, zs, hs = [], [], []
    for i in range(rings + 1):
        s = i / rings
        we = s ** 0.92
        wi = hw0 * (1 - we) + (ridge_w / 2) * we
        di = hd0 * (1 - we) + 0.45 * we
        z = h * (s ** 1.45)
        rows.append(_rring(wi, di))
        zs.append(z)
        hs.append((wi, di))
    v, f = [], []
    for ri in range(rings + 1):
        z = zs[ri]
        k = (1 - ri / rings) ** 1.5
        for (x, y) in rows[ri]:
            corner = min(1.0, (abs(x) / max(hw0, 1e-4)) * (abs(y) / max(hd0, 1e-4))) ** 1.5
            v.append((x + ox, y + oy, z0 + z + lift * corner * k))
    for ri in range(rings):
        for k2 in range(_P):
            a = ri * _P + k2
            b = ri * _P + (k2 + 1) % _P
            f.append((a, b, b + _P, a + _P))
    top = rings * _P
    f.append(tuple(range(top, top + _P)))
    ob = _obj(name, v, f, mat, c, smooth=True)
    return ob, {"hw0": hw0, "hd0": hd0, "ridge_w": ridge_w, "h": h, "z0": z0,
                "rows": rows, "zs": zs, "hs": hs, "kind": kind, "rings": rings,
                "ox": ox, "oy": oy}

def add_tiles(name, c, info, mat, strip_w=0.30, gap=0.55):
    """瓦垄:顺屋面曲面的细长瓦条(前后坡+左右坡)"""
    zs, hs, z0 = info["zs"], info["hs"], info["z0"]
    parts = []
    xs = []
    x = -info["hw0"] + 0.45
    while x <= info["hw0"] - 0.45:
        xs.append(x)
        x += gap
    for xi in xs:
        for side in (1, -1):
            vv, f = [], []
            m = 0
            for ri in range(info["rings"] + 1):
                hw, hd = hs[ri]
                if abs(xi) > hw - 0.35:
                    break
                yb = hd * side
                zz = z0 + zs[ri] + 0.04
                vv += [(xi + info["ox"] - strip_w / 2, yb + info["oy"], zz),
                       (xi + info["ox"] + strip_w / 2, yb + info["oy"], zz)]
                m += 1
            for i in range(m - 1):
                a = 2 * i
                if side > 0:
                    f.append((a, a + 1, a + 3, a + 2))
                else:
                    f.append((a + 1, a, a + 2, a + 3))
            if m > 1:
                parts.append(_obj(f"{name}_t{xi:.0f}_{side}", vv, f, mat, c))
    ys = []
    y = -info["hd0"] + 0.45
    while y <= info["hd0"] - 0.45:
        ys.append(y)
        y += gap
    for yi in ys:
        for side in (1, -1):
            vv, f = [], []
            m = 0
            for ri in range(info["rings"] + 1):
                hw, hd = hs[ri]
                if abs(yi) > hd - 0.35:
                    break
                xb = hw * side
                zz = z0 + zs[ri] + 0.04
                vv += [(xb + info["ox"], yi + info["oy"] - strip_w / 2, zz),
                       (xb + info["ox"], yi + info["oy"] + strip_w / 2, zz)]
                m += 1
            for i in range(m - 1):
                a = 2 * i
                f.append((a, a + 1, a + 3, a + 2))
            if m > 1:
                parts.append(_obj(f"{name}_ts{yi:.0f}_{side}", vv, f, mat, c))
    return parts

def hip_ridges(name, c, info, mat="tile_d"):
    """垂脊:檐角 → 脊端"""
    parts = []
    rw = info["ridge_w"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            hw, hd = info["hs"][0]
            p1 = (info["ox"] + sx * hw * 0.96, info["oy"] + sy * hd * 0.96, info["z0"] + 0.3)
            p2 = (info["ox"] + sx * rw / 2, info["oy"], info["z0"] + info["h"] + 0.1)
            parts.append(add_beam(f"{name}_cxj{sx}{sy}", p1, p2, 0.24, 0.18, mat, c))
    return parts

def ridge_cn(name, c, info, mat="tile_d"):
    """中式正脊 + 两端金鸱吻宝珠(全场景金色仅限此类顶饰少量)"""
    zt = info["z0"] + info["h"] + 0.2
    rw = info["ridge_w"]
    parts = [add_box(f"{name}_zj", (rw + 0.7, 0.46, 0.42), (info["ox"], info["oy"], zt), mat, c)]
    for s in (-1, 1):
        parts.append(add_ico(f"{name}_bz{s}", 0.24, (info["ox"] + s * (rw / 2 + 0.38), info["oy"], zt + 0.34), (1, 1, 1), 1, "gold", c))
    return parts

# ================================================================= 构件:栏杆/壁柱/爱奥尼柱(复用大水法)
def balustrade_run(name, c, p1, p2, z0, mat="jade", post_gap=2.0, panel=True):
    """望柱+寻杖+栏板 一段(望柱 ARRAY 阵列;栏板 SOLIDIFY)"""
    parts = []
    p1, p2 = Vector((p1[0], p1[1], 0)), Vector((p2[0], p2[1], 0))
    d = (p2 - p1).length
    n = max(2, int(round(d / post_gap)) + 1)
    base = add_box(f"{name}_pb", (0.34, 0.30, 0.14), (p1.x, p1.y, z0 + 0.07), mat, c)
    post = add_cyl(f"{name}_pc", 0.105, 0.09, 0.72, (p1.x, p1.y, z0 + 0.48), mat, c, n=8)
    head = add_box(f"{name}_ph", (0.24, 0.22, 0.16), (p1.x, p1.y, z0 + 0.90), mat, c)
    for b in (base, post, head):
        md = b.modifiers.new("arr", "ARRAY")
        md.count = n
        md.use_relative_offset = False
        md.use_constant_offset = True
        dirv = (p2 - p1) / max(n - 1, 1)
        md.constant_offset_displace = (dirv.x, dirv.y, 0.0)
    parts += [base, post, head]
    for zz, w in ((z0 + 0.80, 0.10), (z0 + 0.46, 0.08), (z0 + 0.10, 0.08)):
        parts.append(add_beam(f"{name}_rl{zz}", (p1.x, p1.y, zz), (p2.x, p2.y, zz), w, w, mat, c))
    if panel and d > 1.2:
        mid = (p1 + p2) / 2
        ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
        ca, sa = math.cos(ang), math.sin(ang)
        pw, ph = d - 0.4, 0.34
        v = []
        for zz in (z0 + 0.13, z0 + 0.13 + ph):
            for t in (-pw / 2, pw / 2):
                v.append((mid.x + t * ca, mid.y + t * sa, zz))
        pn = _obj(f"{name}_pl", v, [(0, 1, 3, 2)], mat, c)
        sd = pn.modifiers.new("sol", "SOLIDIFY")
        sd.thickness = 0.05
        parts.append(pn)
    return parts

def pilaster(name, c, x, y, z0, h, w=1.0, depth=0.45, mat="marble_g", bands=4, face="y"):
    """镶入式壁柱(考据:主楼檐壁柱式意象):柱身+环带+柱础+柱头(face='y' 柱面朝 ±y,'x' 朝 ±x)"""
    sx = w if face == "y" else depth
    sy = depth if face == "y" else w
    parts = [add_box(f"{name}sh", (sx, sy, h), (x, y, z0 + h / 2), mat, c)]
    for k in range(bands):
        zz = z0 + h * (0.14 + 0.62 * k / max(bands - 1, 1))
        parts.append(add_box(f"{name}b{k}", (sx + 0.07, sy + 0.07, 0.13), (x, y, zz), mat, c))
    parts.append(add_box(f"{name}bs", (sx + 0.28, sy + 0.10, 0.55), (x, y, z0 + 0.28), mat, c))
    parts.append(add_box(f"{name}cp", (sx + 0.34, sy + 0.12, 0.55), (x, y, z0 + h - 0.28), mat, c))
    return parts

def ionic_column(name, c, x, y, z0, h, r=0.40, mat="marble_g"):
    """爱奥尼柱意象(考据:门廊巨柱式):叠础+环槽柱身+双小圆柱涡卷柱头+顶板"""
    parts = []
    parts.append(add_box(f"{name}b1", (r * 2.5, r * 2.5, 0.24), (x, y, z0 + 0.12), mat, c))
    parts.append(add_box(f"{name}b2", (r * 2.1, r * 2.1, 0.18), (x, y, z0 + 0.33), mat, c))
    parts.append(add_cyl(f"{name}sh", r, r * 0.88, h, (x, y, z0 + h / 2), mat, c, n=16))
    for k in range(3):
        parts.append(add_cyl(f"{name}g{k}", r * 1.03, r * 1.03, 0.07, (x, y, z0 + h * 0.36 + 0.9 * k), mat, c, n=16))
    zc = z0 + h
    parts.append(add_box(f"{name}ab", (r * 2.6, r * 2.6, 0.30), (x, y, zc + 0.15), mat, c))
    for s2 in (-1, 1):
        sc = add_cyl(f"{name}vo{s2}", r * 0.40, r * 0.40, r * 1.15, (x + s2 * r * 0.62, y, zc - 0.24), mat, c, n=10)
        bake_rot_x(sc, (x + s2 * r * 0.62, y, zc - 0.24), math.pi / 2)   # 涡卷端面朝东西(门廊朝东)
        parts.append(sc)
    return parts

def pediment_seg(name, c, cx, cy, z0, w, h, depth, mat="marble_g", major=12, axis="y"):
    """巴洛克弧形山花(门套/窗楣用;axis='y' 弧面朝 ±y 挤出沿 y,axis='x' 挤出沿 x)"""
    hw = w / 2
    prof = [(-hw, 0), (hw, 0)]
    for i in range(1, major + 1):
        t = math.pi * i / major
        prof.append((hw * math.cos(t), h * math.sin(t) ** 1.15))
    n = len(prof)
    v, f = [], []
    if axis == "y":
        for yy in (cy - depth / 2, cy + depth / 2):
            for (px, pz) in prof:
                v.append((cx + px, yy, z0 + pz))
    else:
        for xx in (cx - depth / 2, cx + depth / 2):
            for (px, pz) in prof:
                v.append((xx, cy + px, z0 + pz))
    f.append(tuple(range(n)))
    f.append(tuple(range(n, 2 * n)))
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, j + n, i + n))
    return _obj(name, v, f, mat, c)

# ================================================================= 新增构件:西式拱窗/门套
def arch_window(name, c, pos, w, h, face="E", frame_mat="marble_g", sill=True):
    """西式拱窗(考据:主楼墙面开西式拱窗):拱形窗洞暗部 + 拱肩窗套 + 窗台 + 两竖棂"""
    x, y, z0 = pos
    hw, r = w / 2, w / 2
    parts = []
    # 轮廓:底直边→两竖边→半圆拱顶(窗洞闭合轮廓)
    prof = [(-hw, 0), (-hw, h - r)]
    for i in range(1, 11):
        a = math.pi * i / 10
        prof.append((-hw * math.cos(a), h - r + r * math.sin(a)))
    prof.append((hw, h - r))
    n = len(prof)

    def _extrude(nm, off, depth, mat2, shrink=0.0):
        vv, ff = [], []
        sc = 1.0 - shrink
        for d2 in (off, off + depth):
            for (px, pz) in prof:
                px2, pz2 = px * (1.0 if shrink == 0 else 1.0), pz
                if shrink:
                    px2 = px * sc
                    pz2 = min(pz, h - r) if pz <= h - r else (h - r + (pz - (h - r)) * sc)
                if face in ("E", "W"):
                    vv.append((x + (d2 if face == "E" else -d2), y + px2, z0 + pz2))
                else:
                    vv.append((x + px2, y + (d2 if face == "S" else -d2), z0 + pz2))
        ff.append(tuple(range(n)))
        ff.append(tuple(range(n, 2 * n)))
        for i in range(n):
            j = (i + 1) % n
            ff.append((i, j, j + n, i + n))
        return _obj(nm, vv, ff, mat2, c)

    parts.append(_extrude(f"{name}kd", 0.04, 0.14, "niche"))                       # 窗洞暗部(浅凸,避免斜看出楔形)
    parts.append(_extrude(f"{name}tk", 0.14, 0.18, frame_mat, shrink=0.0))         # 窗套外框(凸出暗部之外)
    for s2 in (-1, 1):                                                             # 两竖棂(十字格心意象)
        zz = z0 + (h - r) * 0.5
        if face in ("E", "W"):
            parts.append(add_box(f"{name}m{s2}", (0.26, 0.06, h - 0.2), (x + s2 * 0.03, y, zz), frame_mat, c))
        else:
            parts.append(add_box(f"{name}m{s2}", (0.06, 0.26, h - 0.2), (x, y + s2 * 0.03, zz), frame_mat, c))
    if sill:
        if face in ("E", "W"):
            parts.append(add_box(f"{name}st", (0.5, w + 0.7, 0.24), (x + (0.3 if face == "E" else -0.3), y, z0 - 0.12), frame_mat, c))
        else:
            parts.append(add_box(f"{name}st", (w + 0.7, 0.5, 0.24), (x, y + (0.3 if face == "S" else -0.3), z0 - 0.12), frame_mat, c))
    return parts

def door_surround(name, c, x, y, z0, w=3.0, h=4.6, face="E"):
    """西式门套(考据:入口西式门套):层叠门框 + 弧形山花门楣 + 侧壁柱 + 朱红门扇"""
    parts = []
    sgn = 1 if face == "E" else -1
    parts.append(add_box(f"{name}mn", (0.42, w, h), (x + sgn * 0.1, y, z0 + h / 2), "niche", c))        # 门洞暗部
    parts.append(add_box(f"{name}mf", (0.5, w + 0.6, h + 0.35), (x + sgn * 0.24, y, z0 + (h + 0.35) / 2 - 0.12), "marble_g", c))  # 门套框
    parts.append(add_box(f"{name}mf2", (0.62, w + 1.3, h + 0.8), (x + sgn * 0.16, y, z0 + (h + 0.8) / 2 - 0.2), "jade", c))       # 外层套框
    parts.append(add_box(f"{name}rs", (0.34, w - 0.7, h - 0.7), (x - sgn * 0.06, y, z0 + (h - 0.7) / 2), "red", c))               # 朱红门扇
    for k in range(4):                                                                                                    # 门扇分格线
        parts.append(add_box(f"{name}rg{k}", (0.1, w - 0.75, 0.07), (x + sgn * 0.02, y, z0 + 0.6 + (h - 1.3) * k / 3), "jade", c))
    for s2 in (-1, 1):                                                                                                    # 门侧双壁柱
        parts += pilaster(f"{name}pl{s2}", c, x, y + s2 * (w / 2 + 0.55), z0, h + 0.5, w=0.85, depth=0.4, mat="marble_g", bands=4)
    parts.append(pediment_seg(f"{name}sm", c, x, y, z0 + h + 0.55, w=w + 1.2, h=1.05, depth=0.55, mat="jade", axis="x"))  # 弧形山花门楣(朝东)
    return parts

# ================================================================= 新增构件:八字台阶系统(考据§2)
# 台阶整体:自主楼台基东缘 x=X_ST0(z=Z_PLAT) 向东跌落至 x=X_ST1(z≈0),八字形外张
X_ST0, X_ST1 = -16.5, -6.0
Z_PLAT, Z_ST1 = 1.6, 0.08
ST_RUN = X_ST1 - X_ST0                     # 10.5m
ST_DROP = Z_PLAT - Z_ST1                   # 1.52m

def slope_z(x):
    """台阶坡面高程(西端=台基面 Z_PLAT,东端=地面 Z_ST1,x 越东越低)"""
    return Z_PLAT + (Z_ST1 - Z_PLAT) * (x - X_ST0) / ST_RUN

def splay_y(x, side):
    """八字形外张:台阶中线 y 随 x 外移(side=1 北 / -1 南)"""
    return side * (2.85 + (x - X_ST0) / ST_RUN * 2.55)

def cascading_flight(name, c, side, n=9):
    """叠落式石阶一道(考据:八字形叠落式坡台阶,逐级下跌):
       沿外张中线布置 n 级阶梯(每级含踏步+侧帮),呈叠落瀑布意象"""
    parts = []
    ang = math.atan2(side * 2.55, ST_RUN)          # 外张角
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        xm = X_ST0 + ST_RUN * (t0 + t1) / 2
        ym = splay_y(xm, side)
        seg = ST_RUN / n + 0.06
        zt = slope_z(xm)
        parts.append(add_box(f"{name}s{i}", (seg, 3.2, 0.62), (xm, ym, zt - 0.31), "marble_g", c, rot_z=ang))
        parts.append(add_box(f"{name}t{i}", (seg, 3.2, 0.10), (xm, ym, zt + 0.005), "jade", c, rot_z=ang))   # 踏面白玉石条
    # 台阶两侧斜垂带石
    for k, dy in ((0, -1.75), (1, 1.75)):
        p1 = (X_ST0 - 0.3, splay_y(X_ST0, side) + side * 0 + dy, Z_PLAT + 0.18)
        p2 = (X_ST1 + 0.3, splay_y(X_ST1, side) + dy * 1.28, Z_ST1 + 0.05)
        parts.append(add_beam(f"{name}cb{k}", p1, p2, 0.6, 0.45, "marble_g", c))
    return parts

def cascade_channel(name, c, side, n=8):
    """叠落式喷水槽(考据:石阶两侧设叠落式喷水槽):
       沿台阶外侧布置 n 只跌水石槽,逐级下跌,槽内水面 + 级间落水线"""
    parts = []
    for i in range(n):
        t = (i + 0.5) / n
        xm = X_ST0 + 0.9 + (ST_RUN - 1.8) * t
        ym = splay_y(xm, side) + side * 2.75
        ang = math.atan2(side * 2.55, ST_RUN)
        zt = slope_z(xm) + 0.42
        parts.append(add_box(f"{name}b{i}", (1.3, 1.15, 0.32), (xm, ym, zt - 0.16), "jade", c, rot_z=ang))   # 槽体
        parts.append(add_box(f"{name}w{i}", (1.1, 0.9, 0.08), (xm, ym, zt - 0.02), "water", c, rot_z=ang))    # 槽内水
        if i > 0:                                                                                             # 级间跌水(上槽缘 → 下槽水面)
            px, py2 = xm - (ST_RUN - 1.8) / n, splay_y(xm - (ST_RUN - 1.8) / n, side) + side * 2.75
            parts.append(add_beam(f"{name}f{i}", (px, py2, slope_z(px) + 0.42), (xm, ym, zt - 0.05), 0.09, 0.09, "water", c))
    parts.append(add_beam(f"{name}lr", (X_ST0 + 0.2, splay_y(X_ST0 + 0.2, side) + side * 2.75, slope_z(X_ST0 + 0.2) + 0.60),
                          (X_ST1 + 0.4, splay_y(X_ST1 + 0.4, side) + side * 2.75 * 1.24, slope_z(X_ST1 + 0.4) + 0.55), 0.14, 0.12, "jade", c))
    return parts

def central_ramp(name, c):
    """中央御道坡道(台阶中脉):交错踏步 + 两侧垂带石 + 白玉矮栏"""
    parts = []
    n = 12
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        xm = X_ST0 + ST_RUN * (t0 + t1) / 2
        zt = slope_z(xm)
        parts.append(add_box(f"{name}r{i}", (ST_RUN / n + 0.05, 2.8, 0.55), (xm, 0, zt - 0.27), "marble_g", c))
        parts.append(add_box(f"{name}c{i}", (ST_RUN / n + 0.05, 2.8, 0.08), (xm, 0, zt + 0.01), "jade", c))
    for s2 in (-1, 1):
        parts.append(add_beam(f"{name}cb{s2}", (X_ST0 - 0.3, s2 * 1.55, Z_PLAT + 0.2),
                              (X_ST1 + 0.3, s2 * 1.62, Z_ST1 + 0.05), 0.55, 0.5, "marble_g", c))
        parts.append(add_beam(f"{name}rl{s2}", (X_ST0 + 0.1, s2 * 1.55, Z_PLAT + 0.95),
                              (X_ST1 + 0.1, s2 * 1.62, Z_ST1 + 0.72), 0.14, 0.12, "jade", c))
    return parts

# ================================================================= 新增构件:十二生肖人身兽首铜像(考据§3)
def zodiac_statue(name, c, x, y, z0, kind, yaw=0.0):
    """人身着袍坐像 + 兽首(几何差异化可辨),口中喷出水柱(细长水线)
       局部坐标:面朝 +X(东),构建完成后绕 z 轴 bake 旋转 yaw"""
    parts = []
    zx = x   # 局部原点(构建时先在原方位建,再整体旋转)——为简化直接按世界位姿建,面部朝东后整体绕 (x,y) 旋 yaw
    # ---- 基座(灰白大理石须弥座意象)
    parts.append(add_box(f"{name}jb", (1.0, 1.0, 0.30), (x, y, z0 + 0.15), "marble_g", c))
    parts.append(add_box(f"{name}jb2", (0.86, 0.86, 0.30), (x, y, z0 + 0.45), "marble_g", c))
    parts.append(add_box(f"{name}jt", (0.94, 0.94, 0.10), (x, y, z0 + 0.65), "marble_g", c))
    zp = z0 + 0.70        # 袍身起点
    coiled = (kind == "蛇")   # 蛇无足盘坐:以三层盘线圈代替袍摆
    if coiled:
        parts.append(add_ico(f"{name}cl1", 0.40, (x, y, zp + 0.06), (1.0, 1.0, 0.36), 1, "bronze", c))
        parts.append(add_ico(f"{name}cl2", 0.30, (x, y, zp + 0.24), (1.0, 1.0, 0.42), 1, "bronze", c))
        parts.append(add_ico(f"{name}cl3", 0.22, (x, y, zp + 0.44), (1.0, 1.0, 0.50), 1, "bronze", c))
        torso_z0, torso_h = zp + 0.56, 0.58
    else:
        parts.append(add_cyl(f"{name}pb", 0.40, 0.47, 0.55, (x, y, zp + 0.28), "bronze", c, n=16))     # 袍摆下段
        parts.append(add_cyl(f"{name}ps", 0.47, 0.44, 0.16, (x, y, zp + 0.08), "bronze", c, n=16))     # 袍摆铺地
        for s2 in (-1, 1):                                                                             # 袍褶(两道竖褶)
            parts.append(add_box(f"{name}pz{s2}", (0.07, 0.09, 0.52), (x + s2 * 0.22, y - s2 * 0.13, zp + 0.30), "bronze", c, rot_z=s2 * 0.5))
        torso_z0, torso_h = zp + 0.55, 0.78
    parts.append(add_cyl(f"{name}to", 0.24, 0.30, torso_h, (x, y, torso_z0 + torso_h / 2), "bronze", c, n=16))  # 袍身上段
    parts.append(add_cyl(f"{name}yl", 0.31, 0.28, 0.09, (x, y, torso_z0 + torso_h * 0.42), "verd", c, n=16))    # 腰带(铜绿点缀)
    parts.append(add_box(f"{name}ylk", (0.09, 0.13, 0.11), (x + 0.27, y, torso_z0 + torso_h * 0.42), "gold", c)) # 腰带扣(金点)
    shz = torso_z0 + torso_h
    parts.append(add_box(f"{name}jn", (0.50, 0.30, 0.16), (x, y, shz + 0.04), "bronze", c))            # 肩部
    parts.append(add_cyl(f"{name}lh", 0.15, 0.17, 0.10, (x + 0.01, y, shz + 0.15), "verd", c, n=12))   # 衣领(铜绿)
    if not coiled:
        for s2 in (-1, 1):                                                                             # 两臂前拱扶膝 + 袖口
            arm = add_cyl(f"{name}ar{s2}", 0.075, 0.06, 0.60, (x + 0.22, y + s2 * 0.24, shz - 0.16), "bronze", c, n=10)
            bake_rot_y(arm, (x + 0.22, y + s2 * 0.24, shz + 0.06), 0.85)
            parts.append(arm)
            parts.append(add_box(f"{name}xk{s2}", (0.13, 0.14, 0.13), (x + 0.43, y + s2 * 0.21, zp + 0.56), "bronze", c))
            parts.append(add_ico(f"{name}ha{s2}", 0.07, (x + 0.44, y + s2 * 0.21, zp + 0.46), (1, 1, 0.8), 1, "bronze", c))
    hz = shz + 0.32        # 兽首球心
    hx = x + 0.03
    head = add_ico(f"{name}hd", 0.235, (hx, y, hz), (1, 1, 1), 1, "bronze", c)
    parts.append(head)
    # ---- 兽首几何差异化(考据:鼠圆耳/牛弯角/虎额纹/兔长耳/龙角/蛇无足/马长脸/羊弯角/猴瘦/鸡冠/狗竖耳/猪鼻)
    if kind == "鼠":
        for s2 in (-1, 1):     # 圆圆大耳(薄圆盘)
            e = add_cyl(f"{name}e{s2}", 0.095, 0.095, 0.045, (hx - 0.03, y + s2 * 0.185, hz + 0.16), "bronze", c, n=8)
            bake_rot_y(e, (hx - 0.03, y + s2 * 0.185, hz + 0.16), math.pi / 2)
            parts.append(e)
        parts.append(add_ico(f"{name}sn", 0.095, (hx + 0.19, y, hz - 0.02), (1.5, 0.85, 0.8), 1, "bronze", c))   # 尖吻
    elif kind == "牛":
        parts.append(add_box(f"{name}fc", (0.26, 0.30, 0.26), (hx + 0.02, y, hz - 0.02), "bronze", c))
        for s2 in (-1, 1):     # 弯角(两段外扬上挑)
            parts.append(add_beam(f"{name}h{s2}a", (hx - 0.02, y + s2 * 0.14, hz + 0.12), (hx + 0.16, y + s2 * 0.36, hz + 0.34), 0.06, 0.06, "bronze", c))
            parts.append(add_beam(f"{name}h{s2}b", (hx + 0.16, y + s2 * 0.36, hz + 0.34), (hx + 0.30, y + s2 * 0.40, hz + 0.52), 0.045, 0.045, "bronze", c))
            parts.append(add_box(f"{name}e{s2}", (0.07, 0.14, 0.05), (hx - 0.10, y + s2 * 0.20, hz + 0.04), "bronze", c))
        parts.append(add_box(f"{name}mz", (0.10, 0.18, 0.12), (hx + 0.20, y, hz - 0.08), "bronze", c))           # 吻部
    elif kind == "虎":
        for s2 in (-1, 1):
            parts.append(add_ico(f"{name}e{s2}", 0.075, (hx - 0.04, y + s2 * 0.15, hz + 0.17), (1, 1, 1), 1, "bronze", c))
        for k, zz in enumerate((0.12, 0.05, -0.02)):   # 额头"王"字纹(三横)
            parts.append(add_box(f"{name}w{k}", (0.03, 0.17, 0.032), (hx + 0.19, y, hz + zz), "verd", c))
        parts.append(add_box(f"{name}wv", (0.03, 0.04, 0.14), (hx + 0.195, y, hz + 0.05), "verd", c))            # 王字中竖
        parts.append(add_ico(f"{name}mz", 0.10, (hx + 0.19, y, hz - 0.06), (1.2, 1.1, 0.7), 1, "bronze", c))
    elif kind == "兔":
        for s2 in (-1, 1):     # 长耳(细长柱,略外撇)
            e = add_cyl(f"{name}e{s2}", 0.055, 0.045, 0.52, (hx - 0.05, y + s2 * 0.09, hz + 0.30), "bronze", c, n=8)
            bake_rot_z(e, (hx - 0.05, y, hz + 0.06), s2 * 0.10)
            bake_rot_x(e, (hx - 0.05, y, hz + 0.06), -s2 * 0.12)
            parts.append(e)
        parts.append(add_ico(f"{name}mz", 0.08, (hx + 0.18, y, hz - 0.04), (1.1, 0.9, 0.7), 1, "bronze", c))
    elif kind == "龙":
        parts.append(add_box(f"{name}fc", (0.30, 0.26, 0.26), (hx + 0.04, y, hz - 0.01), "bronze", c))
        parts.append(add_box(f"{name}mz", (0.16, 0.17, 0.13), (hx + 0.24, y, hz - 0.04), "bronze", c))           # 前突吻
        for s2 in (-1, 1):     # 鹿角式双角(两段后掠)
            parts.append(add_beam(f"{name}h{s2}a", (hx - 0.04, y + s2 * 0.10, hz + 0.14), (hx - 0.20, y + s2 * 0.22, hz + 0.40), 0.05, 0.05, "bronze", c))
            parts.append(add_beam(f"{name}h{s2}b", (hx - 0.20, y + s2 * 0.22, hz + 0.40), (hx - 0.12, y + s2 * 0.26, hz + 0.55), 0.035, 0.035, "bronze", c))
            parts.append(add_beam(f"{name}ws{s2}", (hx + 0.26, y + s2 * 0.10, hz - 0.02), (hx + 0.42, y + s2 * 0.26, hz + 0.02), 0.022, 0.022, "bronze", c))  # 长须
        for k in range(3):                                                                                       # 颈后鬃鬣
            parts.append(add_ico(f"{name}mn{k}", 0.085, (hx - 0.16 - 0.06 * k, y + (k - 1) * 0.07, hz + 0.10 - 0.09 * k), (1, 0.7, 1.1), 1, "verd", c))
    elif kind == "蛇":
        parts.append(add_cyl(f"{name}nk", 0.09, 0.075, 0.18, (hx, y, hz - 0.16), "bronze", c, n=8))              # 颈
        head = add_ico(f"{name}hd2", 0.14, (hx, y, hz), (1.1, 1.0, 0.8), 1, "bronze", c)
        parts.append(head)
        parts.append(add_box(f"{name}xn", (0.09, 0.03, 0.018), (hx + 0.20, y, hz - 0.04), "red", c))             # 红蛇信
    elif kind == "马":
        parts.append(add_box(f"{name}fc", (0.24, 0.22, 0.30), (hx + 0.05, y, hz - 0.03), "bronze", c))
        parts.append(add_box(f"{name}mz", (0.16, 0.15, 0.15), (hx + 0.22, y, hz - 0.10), "bronze", c))           # 长脸前伸
        for s2 in (-1, 1):
            parts.append(add_box(f"{name}e{s2}", (0.05, 0.04, 0.12), (hx - 0.02, y + s2 * 0.10, hz + 0.19), "bronze", c))
        for k in range(3):                                                                                       # 颈鬃
            parts.append(add_box(f"{name}mg{k}", (0.05, 0.05, 0.15), (hx - 0.10 - 0.05 * k, y, hz + 0.06 - 0.13 * k), "bronze", c))
    elif kind == "羊":
        for s2 in (-1, 1):     # 弯角向后卷(两段)
            parts.append(add_beam(f"{name}h{s2}a", (hx, y + s2 * 0.12, hz + 0.15), (hx - 0.20, y + s2 * 0.28, hz + 0.30), 0.055, 0.055, "bronze", c))
            parts.append(add_beam(f"{name}h{s2}b", (hx - 0.20, y + s2 * 0.28, hz + 0.30), (hx - 0.30, y + s2 * 0.22, hz + 0.10), 0.04, 0.04, "bronze", c))
            parts.append(add_box(f"{name}e{s2}", (0.06, 0.12, 0.05), (hx + 0.06, y + s2 * 0.20, hz + 0.02), "bronze", c))   # 垂耳
        parts.append(add_ico(f"{name}mz", 0.085, (hx + 0.17, y, hz - 0.05), (1.1, 0.9, 0.75), 1, "bronze", c))
    elif kind == "猴":
        parts.append(add_ico(f"{name}fc", 0.115, (hx + 0.13, y, hz - 0.01), (0.7, 0.85, 1.0), 1, "verd", c))     # 凸脸(铜绿点缀)
        for s2 in (-1, 1):
            parts.append(add_ico(f"{name}e{s2}", 0.062, (hx - 0.02, y + s2 * 0.175, hz + 0.02), (1, 1, 1), 0, "bronze", c)) # 圆侧耳
    elif kind == "鸡":
        for s2 in (-1, 1):
            parts.append(add_ico(f"{name}e{s2}", 0.05, (hx + 0.02, y + s2 * 0.16, hz + 0.05), (1, 1, 1), 0, "bronze", c))
        for k, (dz, dy) in enumerate(((0.20, 0.0), (0.17, 0.03), (0.13, 0.05))):                                 # 肉冠(朱红点缀)
            parts.append(add_box(f"{name}g{k}", (0.05, 0.045, 0.065), (hx + dy * 0.5, y + dy, hz + dz), "red", c))
        bk = add_cyl(f"{name}bk", 0.035, 0.004, 0.15, (hx + 0.26, y, hz - 0.03), "verd", c, n=6)
        bake_rot_y(bk, (hx + 0.26, y, hz - 0.03), math.pi / 2)                                                   # 喙朝前
        parts.append(bk)
        parts.append(add_box(f"{name}wt", (0.04, 0.035, 0.07), (hx + 0.17, y, hz - 0.14), "red", c))             # 肉垂
    elif kind == "狗":
        parts.append(add_ico(f"{name}mz", 0.10, (hx + 0.18, y, hz - 0.05), (1.3, 1.0, 0.8), 1, "bronze", c))
        for s2 in (-1, 1):     # 竖耳(尖三角,外撇)
            e = add_box(f"{name}e{s2}", (0.05, 0.035, 0.17), (hx - 0.03, y + s2 * 0.135, hz + 0.19), "bronze", c)
            bake_rot_z(e, (hx - 0.03, y, hz + 0.05), s2 * 0.3)
            parts.append(e)
    elif kind == "猪":
        sn = add_cyl(f"{name}mz", 0.088, 0.088, 0.09, (hx + 0.22, y, hz - 0.04), "bronze", c, n=8)               # 鼻吻圆盘
        bake_rot_y(sn, (hx + 0.22, y, hz - 0.04), math.pi / 2)
        parts.append(sn)
        for s2 in (-1, 1):     # 耷拉耳(外斜下)
            e = add_box(f"{name}e{s2}", (0.10, 0.045, 0.09), (hx - 0.02, y + s2 * 0.15, hz + 0.15), "bronze", c)
            bake_rot_z(e, (hx - 0.02, y, hz + 0.05), s2 * 0.55)
            bake_rot_x(e, (hx - 0.02, y, hz + 0.05), -s2 * 0.35)
            parts.append(e)
    # ---- 口中喷水柱(细长浅色水线,抛向下前方台阶水槽,落点带水花)
    mz = hz - 0.08
    tx, ty = x + 1.7, y + (0.85 if y >= 0 else -0.85)
    tz = z0 + 0.72
    parts.append(add_beam(f"{name}wjt", (hx + 0.20, y, mz), (tx, ty, tz), 0.035, 0.035, "jet", c))
    parts.append(add_ico(f"{name}wh", 0.05, (tx, ty, tz), (1, 1, 1), 1, "jet", c))
    # ---- 整体朝向:绕 (x,y) 旋转 yaw(局部已朝 +X)
    if abs(yaw) > 1e-6:
        for p in parts:
            bake_rot_z(p, (x, y), yaw)
    return parts

# ================================================================= 新增构件:巨型贝壳石雕 + 海豚(考据§1)
def shell_sculpture(name, c, cx, cy, z0):
    """巨型贝壳石雕(考据:池中央扇贝张开意象):
       三层石座 + 张开扇贝(扇面朝东上竖起,缘口呈波浪扇齿,放射石肋凸出)+
       缘口两侧滴水兽首意象;扇面立在池心,自东侧观为满开扇"""
    parts = []
    parts.append(add_cyl(f"{name}st1", 2.6, 2.2, 0.55, (cx, cy, z0 + 0.28), "marble_g", c, n=20))   # 座一层
    parts.append(add_cyl(f"{name}st2", 1.9, 1.6, 0.5, (cx, cy, z0 + 0.80), "marble_g", c, n=20))    # 座二层
    parts.append(add_cyl(f"{name}st3", 1.25, 1.05, 0.45, (cx, cy, z0 + 1.26), "jade", c, n=16))     # 座三层
    hx, hz = cx - 0.2, z0 + 1.55     # 贝壳铰链(底尖,座顶)
    NU, NV = 7, 14
    FAN = math.radians(62)           # 扇面半张角
    R = 4.2                          # 展开半径
    TILT = 0.50                      # 扇面后仰(顶向西倾,开口朝东)
    def _pt(u, v):
        th = (v / NV - 0.5) * 2 * FAN
        scallop = 1 + 0.055 * math.sin(v / NV * math.pi * 7)     # 缘口扇齿波浪
        rr = R * (0.14 + 0.86 * u) * (1 + (scallop - 1) * u * u)
        yy = math.sin(th) * rr
        zz0 = math.cos(th) * rr * 0.98 + 0.55 * u * u            # 缘线上翘
        xx0 = -0.55 * u * u + 0.85 * (math.sin(th) ** 2) * u * u # 凹面(中心西凹、缘东凸)
        xx = hx + xx0 * math.cos(TILT) + zz0 * math.sin(TILT) * 0.25
        zz = hz + zz0 * math.cos(TILT) - xx0 * math.sin(TILT) * 0.5
        return (xx, cy + yy, zz)
    v, f = [], []
    for iu in range(NU + 1):
        for iv in range(NV + 1):
            v.append(_pt(iu / NU, iv / NV))
    for iu in range(NU):
        for iv in range(NV):
            a = iu * (NV + 1) + iv
            f.append((a, a + 1, a + NV + 2, a + NV + 1))
    shell = _obj(f"{name}sy", v, f, "marble_g", c, smooth=True)
    parts.append(shell)
    for k in range(1, NV):        # 放射石肋:白玉窄条凸出扇面 0.2(明暗对比可辨扇形)
        vv, ff = [], []
        for iu in range(NU + 1):
            p0 = _pt(iu / NU, k / NV - 0.016)
            p1 = _pt(iu / NU, k / NV + 0.016)
            lift = 0.06 + 0.20 * (iu / NU)
            vv += [(p0[0], p0[1], p0[2] + lift), (p1[0], p1[1], p1[2] + lift)]
        for iu in range(NU):
            a = 2 * iu
            ff.append((a, a + 1, a + 3, a + 2))
        parts.append(_obj(f"{name}lb{k}", vv, ff, "jade", c))
    for s2 in (-1, 1):            # 铰链两侧抱鼓石
        parts.append(add_ico(f"{name}bg{s2}", 0.42, (hx + 0.3, cy + s2 * 0.55, hz - 0.1), (1, 0.8, 1.1), 1, "marble_g", c))
    return parts

def dolphin(name, c, cx, cy, z0):
    """海豚喷水意象(考据:海豚自贝壳上跃出喷水):
       弓身三段自扇面上缘跃向东上空,吻部水柱上喷 + 顶花"""
    parts = []
    bx, bz = cx + 0.85, z0 + 4.55    # 身体中心(贝壳扇面上部,叠于扇面剪影内)
    parts.append(add_ico(f"{name}bd", 0.38, (bx, cy, bz), (1.55, 0.60, 0.52), 1, "bronze", c))    # 躯干
    n1 = add_cyl(f"{name}n1", 0.17, 0.10, 0.58, (bx + 0.70, cy, bz + 0.40), "bronze", c, n=8)
    bake_rot_y(n1, (bx + 0.70, cy, bz + 0.11), 0.75)                                                          # 前段昂起
    parts.append(n1)
    n2 = add_cyl(f"{name}n2", 0.10, 0.04, 0.42, (bx + 1.17, cy, bz + 0.80), "bronze", c, n=8)
    bake_rot_y(n2, (bx + 1.17, cy, bz + 0.68), 0.35)                                                          # 吻部
    parts.append(n2)
    for s2 in (-1, 1):               # 尾鳍(竖板,后下摆)
        tf = add_box(f"{name}tf{s2}", (0.28, 0.08, 0.38), (bx - 0.80, cy + s2 * 0.10, bz - 0.40), "bronze", c)
        bake_rot_z(tf, (bx - 0.80, cy, bz - 0.40), s2 * 0.5)
        parts.append(tf)
    parts.append(add_box(f"{name}df", (0.22, 0.08, 0.26), (bx + 0.05, cy, bz + 0.40), "bronze", c))           # 背鳍
    for s2, dx in ((-1, -0.15), (1, 0.2)):                                                                    # 胸鳍
        parts.append(add_box(f"{name}ff{s2}", (0.28, 0.06, 0.15), (bx + dx, cy + s2 * 0.28, bz - 0.12), "bronze", c, rot_z=s2 * 0.4))
    parts.append(add_cyl(f"{name}jt", 0.06, 0.10, 1.1, (bx + 1.32, cy, bz + 1.40), "water", c, n=8))          # 水柱
    parts.append(add_ico(f"{name}jb", 0.15, (bx + 1.32, cy, bz + 2.05), (1, 1, 1), 1, "water", c))            # 顶花
    return parts

# ================================================================= 新增构件:蓄水楼(考据§5)
def reservoir_tower(name, c, cx, cy):
    """蓄水楼(考据:主楼西侧抬高的大土台 + 台上两层蓄水池建筑,供水力钟,有引水管道)"""
    parts = []
    px0, px1, py = -8.2, 8.2, 10.5     # 土台半尺寸
    parts.append(add_prism(f"{name}tt", [(cx + px0, cy - py), (cx + px1, cy - py), (cx + px1, cy + py), (cx + px0, cy + py)], 0, 5.0, "brick", c, top_mat="earth"))
    for s2, (wx, wy, ox, oy) in enumerate(((px1 * 2 + 0.5, 0.5, 0, -py), (py * 2 + 0.5, 0.5, px1, 0),
                                           (px1 * 2 + 0.5, 0.5, 0, py), (py * 2 + 0.5, 0.5, -px1, 0))):
        pass  # 土台以砖石本体呈现,四角包边石
    for sx2 in (-1, 1):               # 台身四角包边石
        for sy2 in (-1, 1):
            parts.append(add_box(f"{name}cn{sx2}{sy2}", (1.3, 1.3, 5.3), (cx + sx2 * px1, cy + sy2 * py, 2.65), "marble_g", c))
    for s2 in (-1, 1):                # 台顶压沿石
        parts.append(add_box(f"{name}yl{s2}", (px1 * 2 + 0.6, 0.75, 0.3), (cx, cy + s2 * py, 5.1), "marble_g", c))
        parts.append(add_box(f"{name}ylx{s2}", (0.75, py * 2 + 0.6, 0.3), (cx + s2 * px1, cy, 5.1), "marble_g", c))
    # 台上蓄水池建筑(两层,灰瓦顶)
    bx, by, bw, bd = cx, cy, 11.0, 8.0
    parts.append(add_box(f"{name}f1", (bw, bd, 3.2), (bx, by, 5.0 + 1.6), "marble_g", c))      # 一层
    parts.append(add_box(f"{name}fl", (bw + 0.5, bd + 0.5, 0.3), (bx, by, 8.25), "jade", c))   # 层间檐线
    parts.append(add_box(f"{name}f2", (bw - 0.8, bd - 0.8, 2.6), (bx, by, 8.4 + 1.3), "marble_g", c))  # 二层
    for s2 in (-1, 1):          # 拱窗(东西正面各二,南北各一)
        for k, wx in enumerate((-2.6, 2.6)):
            parts.append(add_box(f"{name}wd{s2}{k}", (1.2, 0.4, 1.9), (bx + wx, by + s2 * (bd / 2 + 0.05), 6.6), "niche", c))
            parts.append(add_box(f"{name}wv{s2}{k}", (1.5, 0.35, 0.28), (bx + wx, by + s2 * (bd / 2 + 0.08), 7.75), "jade", c))
        parts.append(add_box(f"{name}ws{s2}", (0.4, 1.2, 1.9), (bx + s2 * (bw / 2 + 0.05), by, 6.6), "niche", c))
    for k, wy in enumerate((-1.8, 1.8)):
        parts.append(add_box(f"{name}wu{k}", (0.4, 1.1, 1.5), (bx + (bw - 0.8) / 2 + 0.05, by + wy, 9.6), "niche", c))
        parts.append(add_box(f"{name}wu2{k}", (0.4, 1.1, 1.5), (bx - (bw - 0.8) / 2 - 0.05, by + wy, 9.6), "niche", c))
    zr = 11.0
    roof, info = roof_tube(f"{name}rf", c, bw + 0.6, bd + 0.6, 2.7, zr, kind="wudian",
                           eave=1.0, lift=0.55, ridge_w=2.2, rings=6, mat="tile", ox=bx, oy=by)
    parts.append(roof)
    parts += add_tiles(f"{name}tl", c, info, "tile_d", strip_w=0.22, gap=0.55)
    parts += hip_ridges(f"{name}hr", c, info, "tile_d")
    parts += ridge_cn(f"{name}rj", c, info, "tile_d")
    # 引水管道意象:自台东壁南端引出铜管(绕 y 轴放平,沿 x 东行),沿矮墩东行,末端竖管入地
    parts.append(add_cyl(f"{name}pp1", 0.20, 0.20, 15.0, (cx + px1 + 7.5, cy - 4.0, 3.6), "bronze", c, n=8))
    bake_rot_y(parts[-1], (cx + px1 + 7.5, cy - 4.0, 3.6), math.pi / 2)
    parts.append(add_cyl(f"{name}pp2", 0.16, 0.16, 3.4, (cx + px1 + 15.0, cy - 4.0, 1.9), "bronze", c, n=8))
    for k, px in enumerate((2.5, 6.5, 10.5, 14.0)):   # 管道支墩
        parts.append(add_box(f"{name}pd{k}", (0.6, 0.6, 3.5), (cx + px1 + px, cy - 4.0, 1.75), "marble_g", c))
    parts.append(add_cyl(f"{name}vr", 0.26, 0.26, 0.16, (cx + px1 + 0.35, cy - 4.0, 3.6), "verd", c, n=8))  # 出口铜绿环
    return parts

# ================================================================= 环境构件(复用大水法)
def cypress(name, c, x, y, z0=0.0, s=1.0):
    """塔柏(柱形常绿树):干+三段收分塔冠"""
    parts = [add_cyl(f"{name}tr", 0.15 * s, 0.12 * s, 0.9 * s, (x, y, z0 + 0.45 * s), "wood", c, n=6)]
    rs = (0.95, 0.7, 0.42)
    for k, rr in enumerate(rs):
        parts.append(add_cyl(f"{name}f{k}", rr * s, rr * 0.62 * s, 1.5 * s, (x, y, z0 + (1.0 + 1.28 * k) * s), "cyp", c, n=8))
    return parts

def low_wall(name, c, p1, p2, h=1.25, mat="marble_g"):
    """两翼矮墙:墙身+压顶+端柱+柱头球"""
    p1, p2 = Vector((p1[0], p1[1], 0)), Vector((p2[0], p2[1], 0))
    d = (p2 - p1).length
    ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
    mx, my = (p1.x + p2.x) / 2, (p1.y + p2.y) / 2
    parts = [add_box(f"{name}w", (d, 0.62, h), (mx, my, h / 2), mat, c, rot_z=ang)]
    parts.append(add_box(f"{name}c", (d, 0.9, 0.16), (mx, my, h + 0.08), mat, c, rot_z=ang))
    for p in (p1, p2):
        parts.append(add_box(f"{name}p", (1.1, 1.1, h + 0.3), (p.x, p.y, (h + 0.3) / 2), mat, c))
        parts.append(add_ico(f"{name}b", 0.28, (p.x, p.y, h + 0.42), (1, 1, 1), 1, mat, c))
    return parts

# ================================================================= §1 场地(素土兜底)
C1 = coll("HY_场地")
add_prism("HY_素土场地", [(-58, -38), (26, -38), (26, 38), (-58, 38)], -0.05, 0.05, "earth", C1)

# ================================================================= §2 主喷水池(原点=池中心,考据§1)
C2 = coll("HY_主喷水池")
NSEG = 96
rim_h = 0.95
PA, PB, PLOBE = 9.0, 7.2, 1.55      # 椭圆半轴(x/y)+ 海棠四瓣起伏
def pool_r(t):
    re = PA * PB / math.sqrt((PB * math.cos(t)) ** 2 + (PA * math.sin(t)) ** 2)
    return re + PLOBE * math.cos(4 * t)
rim_in, rim_out = [], []
for i in range(NSEG):
    t = 2 * math.pi * i / NSEG
    ri = pool_r(t)
    rim_in.append((math.cos(t) * ri, math.sin(t) * ri))
    ro = ri + 1.05
    rim_out.append((math.cos(t) * ro, math.sin(t) * ro))
v, f = [], []
for zz in (0.0, rim_h):
    for (x, y) in rim_out:
        v.append((x, y, zz))
for i in range(NSEG):
    j = (i + 1) % NSEG
    f += [(i, j, j + NSEG, i + NSEG)]
_obj("HY_池壁外", v, f, "jade", C2)
v, f = [], []
for zz in (0.0, rim_h):
    for (x, y) in rim_in:
        v.append((x, y, zz))
for i in range(NSEG):
    j = (i + 1) % NSEG
    f += [(i + NSEG, j + NSEG, j, i)]
_obj("HY_池壁内", v, f, "jade", C2)
v, f = [], []
for (x, y) in rim_in:
    v.append((x, y, rim_h))
for (x, y) in rim_out:
    v.append((x, y, rim_h))
for i in range(NSEG):
    j = (i + 1) % NSEG
    f.append((i, j, j + NSEG, i + NSEG))
_obj("HY_池壁顶", v, f, "jade", C2)
v = [(0, 0, 0.72)] + [(x, y, 0.72) for (x, y) in rim_in]
f = [(0, i + 1, (i + 1) % NSEG + 1) for i in range(NSEG)]
_obj("HY_池水", v, f, "water", C2, smooth=True)

# ================================================================= §3 巨型贝壳石雕 + 海豚喷水(考据§1)
C3 = coll("HY_贝壳石雕")
SHELL_PARTS = shell_sculpture("HY_贝壳石雕", C3, 0, 0, 0.35)
SHELL_PARTS += dolphin("HY_海豚喷水", C3, -0.4, 0, 0.35)

# ================================================================= §4 八字形叠落式坡台阶 + 叠落喷水槽(考据§2)
C4 = coll("HY_八字台阶")
parts_st = central_ramp("HY_中央坡道", C4)
parts_st += cascading_flight("HY_叠落阶北", C4, 1)
parts_st += cascading_flight("HY_叠落阶南", C4, -1)
parts_st += cascade_channel("HY_喷水槽北", C4, 1)
parts_st += cascade_channel("HY_喷水槽南", C4, -1)
# 台阶下落水grounding:台阶东西两端接地条石
parts_st.append(add_box("HY_阶顶台条", (1.2, 13.5, 0.5), (X_ST0 - 0.4, 0, Z_PLAT - 0.22), "marble_g", C4))
parts_st.append(add_box("HY_阶脚地条", (1.6, 15.0, 0.3), (X_ST1 + 0.5, 0, Z_ST1 - 0.05), "marble_g", C4))

# ================================================================= §5 十二生肖人身兽首铜像(考据§3)
C5 = coll("HY_生肖像")
# 南列(自台阶上端至下端):鼠/虎/龙/马/猴/狗;北列:牛/兔/蛇/羊/鸡/猪
SOUTH = ["鼠", "虎", "龙", "马", "猴", "狗"]
NORTH = ["牛", "兔", "蛇", "羊", "鸡", "猪"]
statue_objs = {}
for row, side in ((NORTH, 1), (SOUTH, -1)):
    for k, kind in enumerate(row):
        sx = X_ST0 + 1.2 + k * (ST_RUN - 2.6) / 5          # 沿坡自上而下均匀排布(留出端部)
        sy = splay_y(sx, side) + side * 2.15               # 立于台阶外侧坡肩(阶与水槽之间)
        sz = slope_z(sx) + 0.30                            # 坡肩高程
        yaw = math.atan2(side * 0.55, 1.5)                 # 微朝外(喷水方向)
        ps = zodiac_statue(f"HY_生肖{kind}", C5, sx, sy, sz, kind, yaw=yaw)
        statue_objs[f"HY_生肖{kind}"] = ps

# ================================================================= §6 主楼(考据§6)
C6 = coll("HY_主楼")
# ---- 主楼台基(两级白玉,东缘接八字台阶)
add_prism("HY_台基一级", [(-37.5, -23.5), (-16.5, -23.5), (-16.5, 23.5), (-37.5, 23.5)], 0, 0.8, "jade", C6)
add_prism("HY_台基二级", [(-36.7, -22.7), (-17.3, -22.7), (-17.3, 22.7), (-36.7, 22.7)], 0.8, 1.6, "jade", C6)
# 台基周圈白玉栏杆(东缘中段让出八字台阶开口)
balustrade_run("HY_台栏南", C6, (-36.9, -23.3), (-16.9, -23.3), 0.8, post_gap=2.2)
balustrade_run("HY_台栏北", C6, (-16.9, 23.3), (-36.9, 23.3), 0.8, post_gap=2.2)
balustrade_run("HY_台栏西", C6, (-37.3, 23.3), (-37.3, -23.3), 0.8, post_gap=2.2)
balustrade_run("HY_台栏东上", C6, (-16.7, 7.8), (-16.7, 23.3), 1.6, post_gap=2.2)
balustrade_run("HY_台栏东下", C6, (-16.7, -23.3), (-16.7, -7.8), 1.6, post_gap=2.2)
# ---- 主楼主体:两层各十一开间(开间 3.8m,总宽 41.8m;进深 14m)
BAYS, BAYW = 11, 3.8
W_ALL = BAYS * BAYW                     # 41.8
HALF_W = W_ALL / 2                      # 20.9
X_F, X_B = -22.0, -36.0                 # 前檐面(东)/后檐面
D_HALL = X_F - X_B                      # 14
Z1, Z2, ZC = 1.6, 6.4, 10.4             # 地层面/楼层面/檐口(台基加高,叠落感更强)
H1, H2 = Z1, Z2 - Z1                    # 4.8 / 4.0
PC_W = 11.4                             # 中央门楼三开间
PC_XF = X_F + 2.5                       # 门楼前凸面 x=-19.5
# 翼楼墙体(南北两翼各四开间,实墙承载)
for s2 in (-1, 1):
    yc = s2 * (PC_W / 2 + (HALF_W - PC_W / 2) / 2)
    ywn = HALF_W - PC_W / 2             # 翼宽 15.2
    add_box(f"HY_翼墙1{s2}", (D_HALL, ywn, Z2 - Z1), (X_B + D_HALL / 2, yc, Z1 + (Z2 - Z1) / 2), "marble_g", C6)
    add_box(f"HY_翼墙2{s2}", (D_HALL, ywn, ZC - Z2), (X_B + D_HALL / 2, yc, Z2 + (ZC - Z2) / 2), "marble_g", C6)
    add_box(f"HY_翼檐线{s2}", (D_HALL + 0.5, ywn + 0.5, 0.35), (X_B + D_HALL / 2, yc, ZC + 0.1), "jade", C6)     # 檐口横带
    add_box(f"HY_翼女儿墙{s2}", (D_HALL - 1.2, ywn - 1.2, 0.55), (X_B + D_HALL / 2, yc, ZC + 0.55), "marble_g", C6)  # 顶层平台女儿墙
    # 翼楼顶层白玉栏杆平台(铜版画:两翼层顶为栏杆平台)
    balustrade_run(f"HY_翼顶栏前{s2}", C6, (-22.0 + 0.4, s2 * (PC_W / 2 + 0.3)), (-22.0 + 0.4, s2 * (HALF_W - 0.35)), ZC + 0.82, post_gap=2.0)
    balustrade_run(f"HY_翼顶栏外{s2}", C6, (-22.0 + 0.4, s2 * (HALF_W - 0.35)), (-36.0 + 0.6, s2 * (HALF_W - 0.35)), ZC + 0.82, post_gap=2.0)
    balustrade_run(f"HY_翼顶栏后{s2}", C6, (-36.0 + 0.6, s2 * (HALF_W - 0.35)), (-36.0 + 0.6, s2 * (PC_W / 2 + 0.3)), ZC + 0.82, post_gap=2.0)
    for k in range(4):                 # 翼顶四角+中点石雕瓶饰
        vx = -22.6 - (D_HALL - 1.6) * k / 3
        add_cyl(f"HY_翼顶瓶{s2}{k}", 0.14, 0.17, 0.3, (vx, s2 * (HALF_W - 1.0), ZC + 1.15), "jade", C6, n=8)
        add_ico(f"HY_翼顶瓶珠{s2}{k}", 0.13, (vx, s2 * (HALF_W - 1.0), ZC + 1.42), (1, 1, 1.25), 1, "jade", C6)
# 中央门楼(前凸,两层,上承主屋顶)
add_box("HY_门楼墙1", (X_B - PC_XF, PC_W, Z2 - Z1), ((X_B + PC_XF) / 2, 0, Z1 + (Z2 - Z1) / 2), "marble_g", C6)
add_box("HY_门楼墙2", (X_B - PC_XF, PC_W, ZC - Z2), ((X_B + PC_XF) / 2, 0, Z2 + (ZC - Z2) / 2), "marble_g", C6)
add_box("HY_门楼檐线", (X_B - PC_XF + 0.6, PC_W + 0.6, 0.4), ((X_B + PC_XF) / 2, 0, ZC + 0.12), "jade", C6)
add_box("HY_门楼顶层墙", (X_B - PC_XF, PC_W - 2.0, 1.35), ((X_B + PC_XF) / 2, 0, ZC + 0.45 + 0.45), "marble_g", C6)  # 檐口上短墙(承屋顶)
# ---- 西式拱窗:两翼前檐(每翼地上一层 4 樘 + 二层 4 樘)、侧面、后檐
for s2 in (-1, 1):
    for k in range(4):
        wy = s2 * (PC_W / 2 + BAYW * (k + 0.5))
        arch_window(f"HY_拱窗1F{s2}{k}", C6, (X_F, wy, Z1 + 0.9), 1.7, 3.0, face="E")
        arch_window(f"HY_拱窗2F{s2}{k}", C6, (X_F, wy, Z2 + 0.85), 1.5, 2.6, face="E")
    for k, wx in enumerate((-25.5, -29.0, -32.5)):
        arch_window(f"HY_拱窗侧1{s2}{k}", C6, (wx, s2 * HALF_W, Z1 + 0.9), 1.7, 3.0, face="S" if s2 > 0 else "N")
        arch_window(f"HY_拱窗侧2{s2}{k}", C6, (wx, s2 * HALF_W, Z2 + 0.85), 1.5, 2.6, face="S" if s2 > 0 else "N")
for k in range(5):
    wy = -HALF_W + BAYW * (k + 0.5) + 3.8
    arch_window(f"HY_拱窗后1{k}", C6, (X_B, wy, Z1 + 0.9), 1.6, 2.8, face="W")
    arch_window(f"HY_拱窗后2{k}", C6, (X_B, wy, Z2 + 0.85), 1.4, 2.4, face="W")
# ---- 檐壁柱式(前檐巨柱式壁柱分位:11 开间 12 位,角位加粗)
for k in range(12):
    py = -HALF_W + BAYW * k
    if abs(py) < PC_W / 2 + 0.1:
        continue                       # 门楼范围内由门楼自身壁柱承担
    pilaster(f"HY_前壁柱{k}", C6, X_F, py, Z1, ZC - Z1, w=0.85, depth=0.34, mat="marble_g", bands=5, face="x")
for s2 in (-1, 1):
    pilaster(f"HY_前角柱{s2}", C6, X_F, s2 * HALF_W, Z1, ZC - Z1, w=1.05, depth=0.45, mat="marble_g", bands=5, face="x")
    pilaster(f"HY_侧壁柱N{s2}", C6, X_B + D_HALL * 0.28, s2 * HALF_W, Z1, ZC - Z1, w=0.8, depth=0.3, mat="marble_g", bands=4, face="x")
    pilaster(f"HY_侧壁柱S{s2}", C6, X_B + D_HALL * 0.72, s2 * HALF_W, Z1, ZC - Z1, w=0.8, depth=0.3, mat="marble_g", bands=4, face="x")
# ---- 巨柱式西洋门廊(考据:西洋柱式门廊;四根巨柱贯通两层)+ 门廊顶白玉栏杆
PORT_X = -17.6
for k, py in enumerate((-4.3, -1.45, 1.45, 4.3)):
    ionic_column(f"HY_门廊柱{k}", C6, PORT_X, py, Z1, (ZC - Z1) - 0.9, r=0.40)
add_box("HY_门廊楣一", (1.0, 10.6, 0.5), (PORT_X, 0, ZC - 0.72), "marble_g", C6)
add_box("HY_门廊楣二", (1.1, 10.9, 0.42), (PORT_X, 0, ZC - 0.25), "jade", C6)
balustrade_run("HY_门廊顶栏", C6, (PORT_X, -5.3), (PORT_X, 5.3), ZC - 0.04, post_gap=1.9)
door_surround("HY_西门套", C6, PC_XF, 0, Z1, w=3.0, h=4.6, face="E")
for k, py in enumerate((-3.8, 3.8)):   # 门楼前檐地上一层侧窗
    arch_window(f"HY_门楼窗1{k}", C6, (PC_XF, py, Z1 + 0.9), 1.7, 3.0, face="E")
for k, py in enumerate((-3.8, 0.0, 3.8)):   # 门楼前檐二层拱窗
    arch_window(f"HY_门楼窗2{k}", C6, (PC_XF, py, Z2 + 0.85), 1.5, 2.6, face="E")
# 门楼侧壁柱
for s2 in (-1, 1):
    pilaster(f"HY_门楼角柱{s2}", C6, PC_XF, s2 * (PC_W / 2), Z1, ZC - Z1, w=1.0, depth=0.42, mat="marble_g", bands=5, face="x")
# 层间腰线(两层分位,环绕四周)
add_box("HY_腰线前", (0.28, W_ALL + 0.2, 0.35), (X_F + 0.12, 0, Z2 - 0.1), "jade", C6)
add_box("HY_腰线后", (0.28, W_ALL + 0.2, 0.35), (X_B - 0.12, 0, Z2 - 0.1), "jade", C6)
for s2 in (-1, 1):
    add_box(f"HY_腰线侧{s2}", (D_HALL, 0.28, 0.35), (X_B + D_HALL / 2, s2 * (HALF_W + 0.12), Z2 - 0.1), "jade", C6)
# ---- 中式庑殿灰瓦主屋顶(考据:铜版画中式庑殿/歇山灰瓦顶 —— 中西合璧)
ROOF_D = (PC_XF - X_B) + 1.2              # 屋顶进深(正值 17.7)
roof, info = roof_tube("HY_主楼庑殿顶", C6, PC_W + 1.2, ROOF_D, 3.6, ZC + 0.75,
                       kind="wudian", eave=1.35, lift=0.7, ridge_w=2.6, rings=7, mat="tile",
                       ox=(X_B + PC_XF) / 2, oy=0)
add_tiles("HY_主楼瓦", C6, info, "tile_d", strip_w=0.26, gap=0.55)
hip_ridges("HY_主楼垂脊", C6, info, "tile_d")
ridge_cn("HY_主楼正脊", C6, info, "tile_d")

# ================================================================= §7 蓄水楼(考据§5)
C7 = coll("HY_蓄水楼")
reservoir_tower("HY_蓄水楼", C7, -46.75, 0)

# ================================================================= §8 环境:石板主轴/草坪/塔柏/矮墙(考据§6)
C8 = coll("HY_环境")
# 池周步道盘 + 台阶下接地条
add_cyl("HY_池周步道", 11.8, 11.8, 0.10, (0, 0, 0.05), "gravel", C8, n=72)
# 台阶下东西接地步道(台阶脚 → 池西缘,避开池壁)
add_prism("HY_步道西", [(-11.0, -7.6), (-5.9, -7.6), (-5.9, 7.6), (-11.0, 7.6)], 0, 0.10, "gravel", C8)
# 东西向石板主轴(池东缘 → 场地东端)
add_prism("HY_石板主轴", [(11.2, -2.8), (24.5, -2.8), (24.5, 2.8), (11.2, 2.8)], 0, 0.12, "gravel", C8)
add_box("HY_主轴镶边北", (13.3, 0.5, 0.16), (17.85, 2.75, 0.08), "jade", C8)
add_box("HY_主轴镶边南", (13.3, 0.5, 0.16), (17.85, -2.75, 0.08), "jade", C8)
# 对称草坪(池东西两侧)
add_prism("HY_草坪东北", [(12.0, 3.4), (24.5, 3.4), (24.5, 36), (12.0, 36)], 0, 0.26, "grass", C8)
add_prism("HY_草坪东南", [(12.0, -36), (24.5, -36), (24.5, -3.4), (12.0, -3.4)], 0, 0.26, "grass", C8)
add_prism("HY_草坪北", [(-40, 9.9), (11.4, 9.9), (11.4, 36), (-40, 36)], 0, 0.26, "grass", C8)
add_prism("HY_草坪南", [(-40, -36), (11.4, -36), (11.4, -9.9), (-40, -9.9)], 0, 0.26, "grass", C8)
add_prism("HY_草坪楼后", [(-58, 11.0), (-38.5, 11.0), (-38.5, 36), (-58, 36)], 0, 0.26, "grass", C8)
add_prism("HY_草坪楼后南", [(-58, -36), (-38.5, -36), (-38.5, -11.0), (-58, -11.0)], 0, 0.26, "grass", C8)
# 对称塔柏列(轴线路两侧)
cyp_xs = (-15.5, -10.5, -5.5, -0.5, 4.5, 9.5, 15.5, 21.0)
for s2 in (-1, 1):
    for k, cx2 in enumerate(cyp_xs):
        cypress(f"HY_塔柏{s2}{k}", C8, cx2, s2 * 12.6, 0.26, s=random.uniform(1.15, 1.45))
for s2 in (-1, 1):     # 主楼台基东北/东南角一对
    cypress(f"HY_塔柏角{s2}", C8, -18.3, s2 * 25.0, 0.26, s=1.4)
# 两翼矮墙(中轴对称,东西各一段)
low_wall("HY_矮墙北a", C8, (-14.0, 14.6), (8.0, 14.6))
low_wall("HY_矮墙南a", C8, (8.0, -14.6), (-14.0, -14.6))
low_wall("HY_矮墙北b", C8, (-30.0, 14.6), (-22.0, 14.6))
low_wall("HY_矮墙南b", C8, (-22.0, -14.6), (-30.0, -14.6))

# ================================================================= 收尾:按建筑合并→法线→统计→导出
def finalize_group(objs, name, c):
    objs = [o for o in objs if o and o.name in bpy.data.objects]
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    try:
        bpy.ops.object.convert(target='MESH')
    except Exception as e:
        print("convert warn:", e)
    try:
        if len(bpy.context.selected_objects) > 1:
            bpy.ops.object.join()
    except Exception as e:
        print("join warn:", e)
    obj = bpy.context.view_layer.objects.active
    if obj:
        obj.name = name
        obj.data.name = name
        for cc in list(obj.users_collection):
            cc.objects.unlink(obj)
        c.objects.link(obj)
    return obj

# 常规建筑组合并
GROUPS = [("HY_场地", C1), ("HY_主喷水池", C2), ("HY_贝壳石雕", C3),
          ("HY_八字台阶", C4), ("HY_主楼", C6), ("HY_蓄水楼", C7), ("HY_环境", C8)]
for gname, c in GROUPS:
    finalize_group(list(c.objects), gname, c)
# 十二生肖像:各自单独成体(对象名 = HY_生肖鼠 等,保证可辨识命名)
for kind in SOUTH + NORTH:
    finalize_group(statue_objs[f"HY_生肖{kind}"], f"HY_生肖{kind}", C5)

# 统一法线方向(防止 from_pydata 产生翻转面)
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

for o in bpy.data.objects:
    if o.type == 'MESH':
        o.parent = ROOT_EMPTY

# ---- 三角面统计
dg = bpy.context.evaluated_depsgraph_get()
total = 0
print("\n=============== 三角面分布 ===============")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type != 'MESH':
        continue
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    t = sum(len(p.vertices) - 2 for p in me.polygons) if me else 0
    oe.to_mesh_clear()
    total += t
    print(f"{o.name:<20} {t:>8} tris")
print(f"{'TOTAL':<20} {total:>8} tris  (预算 ≤ 250k)")

# ---- 包围盒
mins = Vector((1e9,) * 3)
maxs = Vector((-1e9,) * 3)
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    if me:
        for vtx in me.vertices:
            co = oe.matrix_world @ vtx.co
            mins = Vector(map(min, mins, co))
            maxs = Vector(map(max, maxs, co))
    oe.to_mesh_clear()
print("=============== 场景包围盒(Blender z-up) ===============")
print("min", tuple(round(v, 1) for v in mins))
print("max", tuple(round(v, 1) for v in maxs))

# ---- 导出 GLB(未压缩)
os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_materials='EXPORT',
    export_normals=True,
    export_cameras=False,
    export_lights=False,
)
print(f"=============== 导出完成: {OUT_GLB}  {os.path.getsize(OUT_GLB)/1024/1024:.2f} MB ===============")
