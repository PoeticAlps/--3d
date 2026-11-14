# -*- coding: utf-8 -*-
"""
================================================================================
 大水法景区(西洋楼)· 评审级程序化建模脚本  (Blender 5.1 headless / bpy)
================================================================================
考据依据:
  - 西洋楼铜版画二十幅(乾隆五十一年 1786,郎世宁/蒋友仁 制版)之《大水法》《远瀛观》《观水法》
  - 大水法遗址现状(谐奇趣—大水法—远瀛观中轴线)+ 文献(《日下旧闻考》/西洋楼研究文)
场景结构(中轴自南向北 = 自 -Y 到 +Y;原点=海棠形喷水池中心;地面 z=0;x东 y北 z上):
  [1] 观水法(最南,皇帝观喷泉处):石雕屏风×2(巴洛克卷草浮雕意象)+ 石阶 + 铜鹤×2   → §1
  [2] 海棠形大喷水池:汉白玉池壁 + 中央"铜狮头顶双层水盘" + "猎狗逐鹿"铜雕群        → §2
  [3] 大水法石龛(核心):巴洛克屏风式石龛 — 中央大拱门(圆拱+拱心石)+ 两侧各4根       → §3
      镶入式壁柱(环状凸条意象)+ 壁柱间壁龛人像 + 龛顶巴洛克弧形山花 + 顶饰瓶列
      + 石龛底层须弥座 + 两侧对称塔柱(多层收分,顶部球饰)
  [4] 远瀛观(最北,高台上):倒凹字形西洋钟楼式柱廊大殿 — 汉白玉高台须弥座 + 大台阶    → §4
      + 爱奥尼柱廊(涡卷=双小圆柱,凹槽=环槽)+ 殿体两层 + 中式重檐庑殿灰瓦顶(中西合璧)
      + 檐部弧形山花
  [5] 环境:东西草坪 + 对称塔柏(柱形)+ 碎石步道 + 两翼矮墙                          → §5
新增巴洛克构件函数:arch_ring(圆拱圈+拱心石)/arch_slab(圆头屏风板)/pediment_seg
                  (弧形山花)/pilaster(镶入壁柱)/ionic_column(爱奥尼柱)/niche_statue
                  (壁龛人像)/finial_vase(顶饰瓶)/tower_pier(塔柱)
材质调色板(与 v4 场景一致,无贴图、几何承载细节):
  灰白大理石 #E8E6E0(r0.40) 白玉 #F2EDE2 铜雕 #8A6A42(m0.65) 铜绿 #4A7A6A
  金饰 #E8A800(仅顶饰少量) 灰瓦 #5A5F66 草坪/塔柏绿 碎石步道 池水
用法:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
      --python v4/blender/dashuifa_build.py
输出:
  /tmp/dashuifa_raw.glb(未压缩;export_apply=True 于导出时应用全部修改器)
================================================================================
"""
import bpy, bmesh, math, os, random, re
from mathutils import Vector

OUT_GLB = "/tmp/dashuifa_raw.glb"
random.seed(42)

# ---------------------------------------------------------------- 名称安全化
# Blender 5.1.1 的 namemap 唯一化会对"最后一个'.'之后的纯数字串"调用 std::stoi
# 且无保护(方壶胜境脚本已踩坑);对策:ID 名一律去掉"点+数字"段并追加全局序号
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
    "marble_g": _mat("M_灰白大理石", 0xE8E6E0, 0.40),          # 大水法石龛/柱廊主材
    "jade":     _mat("M_白玉",       0xF2EDE2, 0.35),          # 台基/栏杆/屏风/顶饰瓶
    "bronze":   _mat("M_铜雕",       0x8A6A42, 0.42, 0.65),    # 铜狮/鹿/犬/鹤
    "verd":     _mat("M_铜绿",       0x4A7A6A, 0.55, 0.30),    # 铜绿点缀(鬃毛/水盘内壁)
    "gold":     _mat("M_金饰",       0xE8A800, 0.25, 0.70),    # 金色仅限顶饰少量
    "grass":    _mat("M_草坪",       0x557A48, 0.95),
    "cyp":      _mat("M_塔柏",       0x2E5236, 0.90),
    "gravel":   _mat("M_碎石步道",   0x9A948A, 0.92),
    "tile":     _mat("M_灰瓦",       0x5A5F66, 0.55),          # 远瀛观中式顶(铜版画)
    "tile_d":   _mat("M_灰瓦垄",     0x4B5057, 0.58),
    "wood":     _mat("M_木门",       0x5A3E26, 0.70),
    "water":    _mat("M_池水",       0x2E6474, 0.45),
    "earth":    _mat("M_素土场地",   0x8E8878, 0.95),
    "niche":    _mat("M_壁龛暗部",   0x44484E, 0.85),
}

root = bpy.data.collections.new("DS_大水法")
bpy.context.scene.collection.children.link(root)
ROOT_EMPTY = bpy.data.objects.new("DS_大水法", None)
bpy.context.scene.collection.objects.link(ROOT_EMPTY)

def coll(name):
    c = bpy.data.collections.new(name)
    root.children.link(c)
    return c

# ================================================================= 基础几何工厂(复用方壶胜境)
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

def add_torus_arc(name, R, r, loc, mat, c, axis="x", major=12, minor=6, sz=0.9):
    """半圆拱圈/卷草弧条(axis='x':竖立弧面朝 ±y)"""
    v, f = [], []
    for i in range(major + 1):
        a = math.pi * i / major
        for j in range(minor + 1):
            b = 2 * math.pi * j / minor
            rr = r * math.cos(b)
            if axis == "x":
                x = R * math.cos(a) + rr * math.cos(a)
                y = r * math.sin(b)
                z = R * math.sin(a) * sz + r * math.sin(b) * math.sin(a) * sz
            else:
                x = r * math.sin(b)
                y = R * math.cos(a) + rr * math.cos(a)
                z = R * math.sin(a) * sz + r * math.sin(b) * math.sin(a) * sz
            v.append((loc[0] + x, loc[1] + y, loc[2] + z))
    for i in range(major):
        for j in range(minor):
            a0 = i * (minor + 1) + j
            f.append((a0, a0 + minor + 1, a0 + minor + 2, a0 + 1))
    return _obj(name, v, f, mat, c, smooth=True)

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

# ================================================================= 屋面系统(远瀛观中式重檐庑殿顶)
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

def add_tiles(name, c, info, mat, strip_w=0.30, gap=0.62):
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
    """中式正脊 + 两端金宝珠(全场景金色仅限此类顶饰少量)"""
    zt = info["z0"] + info["h"] + 0.2
    rw = info["ridge_w"]
    parts = [add_box(f"{name}_zj", (rw + 0.7, 0.46, 0.42), (info["ox"], info["oy"], zt), mat, c)]
    for s in (-1, 1):
        parts.append(add_ico(f"{name}_bz{s}", 0.24, (info["ox"] + s * (rw / 2 + 0.38), info["oy"], zt + 0.34), (1, 1, 1), 1, "gold", c))
    return parts

# ================================================================= 构件:栏杆/踏道(复用方壶胜境)
def balustrade_run(name, c, p1, p2, z0, mat="jade", post_gap=2.2, panel=True):
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

def stairs(name, c, cx, cy, w, z0, z1, face="S", mat="jade"):
    """踏道:台阶(由高到低向外排)+ 两侧垂带"""
    parts = []
    drop = max(0.3, z1 - z0)
    n = max(3, int(drop / 0.16))
    for i in range(n):
        zz = z0 + drop * (i + 0.5) / n
        ext = 0.36 * (n - 1 - i)
        if face in ("S", "N"):
            yy = cy - ext if face == "S" else cy + ext
            parts.append(add_box(f"{name}s{i}", (w, 0.75, drop / n + 0.015), (cx, yy, zz), mat, c))
        else:
            xx = cx - ext if face == "W" else cx + ext
            parts.append(add_box(f"{name}s{i}", (0.75, w, drop / n + 0.015), (xx, cy, zz), mat, c))
    hw = w / 2 + 0.18
    run = 0.36 * n + 0.4
    if face == "S":
        for i, xoff in enumerate((-hw, hw)):
            parts.append(add_beam(f"{name}cb{i}", (cx + xoff, cy - 0.05, z1 + 0.15), (cx + xoff, cy - run, z0 + 0.1), 0.55, 0.42, mat, c))
    elif face == "N":
        for i, xoff in enumerate((-hw, hw)):
            parts.append(add_beam(f"{name}cb{i}", (cx + xoff, cy + 0.05, z1 + 0.15), (cx + xoff, cy + run, z0 + 0.1), 0.55, 0.42, mat, c))
    return parts

# ================================================================= 巴洛克/西洋构件(本景区新增)
def extrude_profile(name, c, prof, cx, cy, z0, depth, mat, smooth=False):
    """把 xz 平面闭合轮廓沿 y 挤出 depth(通用:拱圈/山花/圆头板共用)"""
    n = len(prof)
    v, f = [], []
    for yy in (cy - depth / 2, cy + depth / 2):
        for (px, pz) in prof:
            v.append((cx + px, yy, z0 + pz))
    f.append(tuple(range(n)))
    f.append(tuple(range(n, 2 * n)))
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, j + n, i + n))
    return _obj(name, v, f, mat, c, smooth=smooth)

def arch_ring(name, c, cx, cy, z0, r_in, r_out, depth, mat="marble_g", major=18):
    """巴洛克圆拱圈(考据§3:中央大拱门的圆拱)+ 拱心石:
       半环拱券(平拱面)由 r_in→r_out 轮廓挤出;拱心石略凸出券面"""
    prof = []
    for i in range(major + 1):          # 外弧:右→顶→左
        a = math.pi * i / major
        prof.append((r_out * math.cos(a), r_out * math.sin(a)))
    for i in range(major, -1, -1):      # 内弧:左→顶→右(反向闭合)
        a = math.pi * i / major
        prof.append((r_in * math.cos(a), r_in * math.sin(a)))
    ob = extrude_profile(name, c, prof, cx, cy, z0, depth, mat, smooth=False)
    ks = add_box(f"{name}_gxs", (0.85, depth + 0.18, 1.05), (cx, cy, z0 + r_out + 0.18), mat, c)  # 拱心石
    bv = ks.modifiers.new("bev", "BEVEL")
    bv.width = 0.07
    bv.segments = 2
    return [ob, ks]

def arch_slab(name, c, cx, cy, z0, w, h_rect, depth, mat="jade", major=12):
    """圆头石板屏风(考据§1:观水法石雕屏风):矩形板身+半圆顶,挤出深度"""
    hw = w / 2
    prof = [(-hw, 0), (hw, 0), (hw, h_rect)]
    for i in range(1, major + 1):
        t = math.pi * i / major
        prof.append((hw * math.cos(t), h_rect + hw * math.sin(t)))
    return extrude_profile(name, c, prof, cx, cy, z0, depth, mat)

def pediment_seg(name, c, cx, cy, z0, w, h, depth, mat="marble_g", major=12):
    """巴洛克弧形山花(考据§3/§4:龛顶/檐部山花):直下檐+上凸弧线轮廓,挤出深度"""
    hw = w / 2
    prof = [(-hw, 0), (hw, 0)]
    for i in range(1, major + 1):
        t = math.pi * i / major
        prof.append((hw * math.cos(t), h * math.sin(t) ** 1.15))
    ob = extrude_profile(name, c, prof, cx, cy, z0, depth, mat, smooth=False)
    # 龛心圆雕饰:凸出山花前脸(前脸 y = cy-depth/2,朝南),防止被实体山花遮住
    car = add_ico(f"{name}_tk", hw * 0.13, (cx, cy - depth / 2, z0 + h * 0.42), (1.0, 0.30, 0.70), 2, "jade", c)
    return [ob, car]

def pilaster(name, c, x, y, z0, h, w=1.05, depth=0.5, mat="marble_g", bands=5):
    """镶入式壁柱(考据§3:螺旋纹/凹槽意象用环状凸条):柱身+环带×5+柱础+柱头"""
    parts = [add_box(f"{name}sh", (w, depth, h), (x, y, z0 + h / 2), mat, c)]
    for k in range(bands):
        zz = z0 + h * (0.16 + 0.60 * k / (bands - 1))
        parts.append(add_box(f"{name}b{k}", (w + 0.08, depth + 0.06, 0.14), (x, y, zz), mat, c))
    parts.append(add_box(f"{name}bs", (w + 0.32, depth + 0.10, 0.75), (x, y, z0 + 0.38), mat, c))
    parts.append(add_box(f"{name}cp", (w + 0.38, depth + 0.12, 0.75), (x, y, z0 + h - 0.38), mat, c))
    return parts

def ionic_column(name, c, x, y, z0, h, r=0.42, mat="marble_g", face="S"):
    """爱奥尼柱意象(考据§4):叠础+环槽柱身+双小圆柱涡卷柱头+顶板"""
    parts = []
    parts.append(add_box(f"{name}b1", (r * 2.5, r * 2.5, 0.22), (x, y, z0 + 0.11), mat, c))
    parts.append(add_box(f"{name}b2", (r * 2.1, r * 2.1, 0.18), (x, y, z0 + 0.31), mat, c))
    parts.append(add_cyl(f"{name}sh", r, r * 0.88, h, (x, y, z0 + h / 2), mat, c, n=16))
    for k in range(3):   # 柱身凹槽意象:细环槽
        parts.append(add_cyl(f"{name}g{k}", r * 1.03, r * 1.03, 0.07, (x, y, z0 + h * 0.38 + 0.8 * k), mat, c, n=16))
    zc = z0 + h
    parts.append(add_box(f"{name}ab", (r * 2.6, r * 2.6, 0.30), (x, y, zc + 0.15), mat, c))
    for s2 in (-1, 1):   # 涡卷暗示:两枚横置小圆柱,端面朝观者即两枚圆
        sc = add_cyl(f"{name}vo{s2}", r * 0.40, r * 0.40, r * 1.15, (x + s2 * r * 0.62, y, zc - 0.22), mat, c, n=10)
        if face == "S":
            bake_rot_x(sc, (x + s2 * r * 0.62, y, zc - 0.22), math.pi / 2)   # 轴沿 y(端面朝南北)
        else:
            bake_rot_y(sc, (x + s2 * r * 0.62, y, zc - 0.22), math.pi / 2)   # 轴沿 x(端面朝东西)
        parts.append(sc)
    return parts

def niche_statue(name, c, x, y, z0, h=3.6, mat="jade"):
    """壁龛人像雕像(考据§3:壁柱间壁龛内人像,几何意象:座+袍身+肩+头+垂臂)"""
    parts = [add_box(f"{name}pd", (0.85, 0.5, 0.5), (x, y, z0 + 0.25), "marble_g", c)]
    parts.append(add_cyl(f"{name}bd", 0.31, 0.22, h * 0.62, (x, y, z0 + 0.5 + h * 0.31), mat, c, n=10))
    parts.append(add_box(f"{name}sh", (0.72, 0.4, 0.22), (x, y, z0 + 0.5 + h * 0.62 + 0.11), mat, c))
    parts.append(add_ico(f"{name}hd", 0.19, (x, y, z0 + 0.5 + h * 0.62 + 0.37), (1, 1, 1), 1, mat, c))
    for s2 in (-1, 1):   # 垂臂
        ar = add_cyl(f"{name}ar{s2}", 0.09, 0.07, h * 0.40, (x + s2 * 0.33, y, z0 + 0.5 + h * 0.42), mat, c, n=6)
        parts.append(ar)
    return parts

def finial_vase(name, c, x, y, z0, s=1.0):
    """顶饰瓶(考据§3:龛顶一排瓶饰;金尖=全场景仅有的金色顶饰)"""
    parts = [add_cyl(f"{name}bt", 0.15 * s, 0.19 * s, 0.26 * s, (x, y, z0 + 0.13 * s), "jade", c, n=8)]
    parts.append(add_ico(f"{name}bl", 0.20 * s, (x, y, z0 + 0.52 * s), (1, 1, 1.35), 1, "jade", c))
    parts.append(add_cyl(f"{name}tp", 0.045 * s, 0.004 * s, 0.26 * s, (x, y, z0 + 0.88 * s), "gold", c, n=6, smooth=False))
    return parts

def tower_pier(name, c, x, y, w0, y_d, z0, tiers=4, mat="marble_g"):
    """对称塔柱(考据§3:石龛两侧多层塔状柱墩,层层收分,顶部球形饰;每层加横带线脚)"""
    parts = []
    parts.append(add_box(f"{name}ft", (w0 + 0.8, y_d + 0.7, 0.9), (x, y, 0.45), mat, c))   # 独立基座
    z = z0
    w = w0
    for i in range(tiers):
        th = 3.3 - i * 0.45
        parts.append(add_box(f"{name}t{i}", (w, y_d, th), (x, y, z + th / 2), mat, c))
        for f2 in (0.3, 0.66):   # 层身横带线脚
            parts.append(add_box(f"{name}b{i}{f2}", (w + 0.12, y_d + 0.12, 0.12), (x, y, z + th * f2), mat, c))
        z += th
        parts.append(add_box(f"{name}c{i}", (w + 0.45, y_d + 0.45, 0.28), (x, y, z + 0.14), mat, c))
        z += 0.28
        w -= 0.75
    parts.append(add_ico(f"{name}bl", 0.72, (x, y, z + 0.55), (1, 1, 1), 1, mat, c))
    parts.append(add_cyl(f"{name}tp", 0.05, 0.004, 0.5, (x, y, z + 1.35), "gold", c, n=6, smooth=False))
    return parts

# ================================================================= 铜雕群(考据§2)
def lion_fountain(name, c, cx, cy, z0):
    """铜狮喷水双层水盘(考据§2:狮子头顶水盘喷水;几何意象:座→狮身→双层水盘)"""
    parts = []
    parts.append(add_cyl(f"{name}pd", 1.15, 1.0, 1.7, (cx, cy, z0 + 0.85), "marble_g", c, n=16))
    parts.append(add_ico(f"{name}bd", 0.85, (cx, cy + 0.25, z0 + 2.3), (1.05, 0.8, 0.75), 1, "bronze", c))   # 狮身
    parts.append(add_ico(f"{name}mn", 0.52, (cx, cy - 0.55, z0 + 2.72), (0.9, 0.7, 0.85), 1, "verd", c))     # 鬃毛(铜绿点缀)
    parts.append(add_box(f"{name}fc", (0.42, 0.3, 0.34), (cx, cy - 0.95, z0 + 2.52), "bronze", c))           # 面部
    for s2 in (-1, 1):
        parts.append(add_cyl(f"{name}lg{s2}", 0.16, 0.13, 1.0, (cx + s2 * 0.5, cy - 0.5, z0 + 1.55), "bronze", c, n=8))  # 前肢
    parts.append(add_cyl(f"{name}b1", 2.0, 1.85, 0.34, (cx, cy, z0 + 3.3), "bronze", c, n=24))               # 下层水盘
    parts.append(add_cyl(f"{name}w1", 1.66, 1.66, 0.06, (cx, cy, z0 + 3.42), "verd", c, n=24))               # 盘内水(铜绿)
    parts.append(add_cyl(f"{name}st", 0.24, 0.2, 0.5, (cx, cy, z0 + 3.72), "bronze", c, n=10))               # 中柱
    parts.append(add_cyl(f"{name}b2", 1.25, 1.1, 0.3, (cx, cy, z0 + 4.12), "bronze", c, n=20))               # 上层水盘
    parts.append(add_cyl(f"{name}w2", 0.93, 0.93, 0.06, (cx, cy, z0 + 4.22), "verd", c, n=20))
    parts.append(add_cyl(f"{name}tp", 0.05, 0.004, 0.35, (cx, cy, z0 + 4.46), "gold", c, n=6, smooth=False))  # 顶饰金尖
    parts.append(add_cyl(f"{name}jt", 0.055, 0.075, 0.8, (cx, cy, z0 + 5.3), "water", c, n=8))               # 顶上水柱
    parts.append(add_ico(f"{name}jb", 0.14, (cx, cy, z0 + 5.75), (1, 1, 1), 1, "water", c))                   # 水花
    return parts

def bronze_deer(name, c, x, y, ang):
    """铜鹿·昂首(考据§2:猎狗逐鹿群中央;躯干+昂首长颈+角+四肢;局部坐标朝 +x 后统一转向)"""
    parts = []
    for dx in (-0.55, 0.55):
        for dy in (-0.22, 0.22):
            parts.append(add_cyl(f"{name}lg{dx:.1f}{dy:.1f}", 0.085, 0.07, 0.85, (x + dx, y + dy, 0.92), "bronze", c, n=6))
    parts.append(add_ico(f"{name}bd", 0.62, (x, y, 1.78), (0.72, 1.35, 0.7), 1, "bronze", c))     # 躯干
    neck = add_cyl(f"{name}nk", 0.17, 0.12, 0.95, (x + 0.62, y, 2.35), "bronze", c, n=8)
    bake_rot_y(neck, (x + 0.62, y, 1.9), 0.6)                                                    # 长颈昂起
    parts.append(neck)
    parts.append(add_box(f"{name}hd", (0.5, 0.24, 0.24), (x + 1.28, y, 2.88), "bronze", c))       # 头
    parts.append(add_box(f"{name}sn", (0.3, 0.18, 0.16), (x + 1.55, y, 2.82), "bronze", c))       # 吻
    for s2 in (-1, 1):                                                                            # 角(三叉意象)
        parts.append(add_beam(f"{name}an{s2}a", (x + 1.30, y + s2 * 0.08, 3.05), (x + 1.55, y + s2 * 0.30, 3.55), 0.05, 0.05, "bronze", c))
        parts.append(add_beam(f"{name}an{s2}b", (x + 1.42, y + s2 * 0.19, 3.30), (x + 1.75, y + s2 * 0.22, 3.52), 0.04, 0.04, "bronze", c))
        parts.append(add_box(f"{name}er{s2}", (0.08, 0.16, 0.1), (x + 1.15, y + s2 * 0.18, 2.98), "bronze", c, rot_z=0.5 * s2))
    parts.append(add_ico(f"{name}tl", 0.18, (x - 0.72, y, 1.95), (0.4, 0.5, 1.0), 1, "bronze", c))  # 短尾
    for p in parts:
        bake_rot_z(p, (x, y), ang)
    return parts

def bronze_dog(name, c, x, y, ang):
    """铜犬(考据§2:围鹿向鹿喷水;昂首前扑意象;局部坐标朝 +x 后统一转向)"""
    parts = []
    for dx in (-0.4, 0.4):
        for dy in (-0.16, 0.16):
            parts.append(add_cyl(f"{name}lg{dx:.1f}{dy:.1f}", 0.065, 0.055, 0.6, (x + dx, y + dy, 0.8), "bronze", c, n=6))
    parts.append(add_ico(f"{name}bd", 0.4, (x, y, 1.32), (0.68, 1.2, 0.62), 1, "bronze", c))      # 躯干
    neck = add_cyl(f"{name}nk", 0.13, 0.1, 0.5, (x + 0.45, y, 1.52), "bronze", c, n=8)
    bake_rot_y(neck, (x + 0.45, y, 1.42), 0.5)                                                   # 昂首
    parts.append(neck)
    parts.append(add_box(f"{name}hd", (0.34, 0.2, 0.2), (x + 0.72, y, 1.86), "bronze", c))
    parts.append(add_box(f"{name}sn", (0.18, 0.14, 0.13), (x + 0.9, y, 1.8), "bronze", c))
    for s2 in (-1, 1):
        parts.append(add_box(f"{name}er{s2}", (0.1, 0.06, 0.14), (x + 0.62, y + s2 * 0.12, 2.0), "bronze", c))
    parts.append(add_beam(f"{name}tl", (x - 0.5, y, 1.45), (x - 0.78, y, 1.9), 0.07, 0.07, "bronze", c))  # 竖尾
    for p in parts:
        bake_rot_z(p, (x, y), ang)
    return parts

def bronze_crane(name, c, x, y, z0):
    """铜鹤(考据§1:观水法左右铜雕意象;长颈前伸,几何简化)"""
    parts = []
    parts.append(add_cyl(f"{name}pd", 0.62, 0.7, 0.9, (x, y, z0 + 0.45), "marble_g", c, n=12))
    parts.append(add_cyl(f"{name}vr", 0.55, 0.55, 0.08, (x, y, z0 + 0.78), "verd", c, n=12))      # 座上铜绿环带
    for s2 in (-1, 1):
        parts.append(add_cyl(f"{name}lg{s2}", 0.04, 0.035, 0.6, (x + s2 * 0.13, y + 0.12, z0 + 1.25), "bronze", c, n=6))
    parts.append(add_ico(f"{name}bd", 0.42, (x, y, z0 + 1.85), (0.62, 1.05, 0.6), 1, "bronze", c))
    parts.append(add_ico(f"{name}tl", 0.2, (x, y - 0.6, z0 + 2.0), (0.45, 1.1, 0.4), 1, "bronze", c))  # 后翘尾羽
    n1 = add_cyl(f"{name}n1", 0.075, 0.06, 0.55, (x, y + 0.45, z0 + 2.3), "bronze", c, n=8)
    bake_rot_x(n1, (x, y + 0.45, z0 + 2.05), -0.5)        # 颈下段前倾(+y)
    parts.append(n1)
    ty = y + 0.45 + 0.55 * math.sin(0.5)
    tz = z0 + 2.05 + 0.55 * math.cos(0.5)
    n2 = add_cyl(f"{name}n2", 0.06, 0.05, 0.5, (x, ty, tz + 0.25), "bronze", c, n=8)
    bake_rot_x(n2, (x, ty, tz), 0.15)                     # 颈上段微回仰(S 形)
    parts.append(n2)
    hy = ty - 0.5 * math.sin(0.15)
    hz = tz + 0.5 * math.cos(0.15)
    parts.append(add_box(f"{name}hd", (0.14, 0.22, 0.13), (x, hy + 0.08, hz + 0.05), "bronze", c))
    bk = add_cyl(f"{name}bk", 0.045, 0.004, 0.26, (x, hy + 0.22, hz + 0.02), "bronze", c, n=6)
    bake_rot_x(bk, (x, hy + 0.22, hz + 0.02), -math.pi / 2)   # 喙水平前伸
    parts.append(bk)
    return parts

# ================================================================= 环境构件(考据§5)
def cypress(name, c, x, y, z0=0.0, s=1.0):
    """塔柏(柱形常绿树):干+三段收分塔冠"""
    parts = [add_cyl(f"{name}tr", 0.15 * s, 0.12 * s, 0.9 * s, (x, y, z0 + 0.45 * s), "wood", c, n=6)]
    rs = (0.95, 0.7, 0.42)
    for k, rr in enumerate(rs):
        parts.append(add_cyl(f"{name}f{k}", rr * s, rr * 0.62 * s, 1.5 * s, (x, y, z0 + (1.0 + 1.28 * k) * s), "cyp", c, n=8))
    return parts

def low_wall(name, c, p1, p2, h=1.3, mat="marble_g"):
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

# ================================================================= §1 观水法(最南,皇帝观喷泉处)
C1 = coll("DS_观水法")
# 台地(汉白玉):南缘大台阶上台,北缘中开缺口面池;台缘压沿石
add_prism("DS_观水台", [(-12, -45), (12, -45), (12, -30), (-12, -30)], 0, 0.55, "jade", C1)
add_box("DS_观水沿N", (24.4, 0.55, 0.2), (0, -30.1, 0.62), "marble_g", C1)
add_box("DS_观水沿S", (24.4, 0.55, 0.2), (0, -44.9, 0.62), "marble_g", C1)
add_box("DS_观水沿E", (0.55, 15.0, 0.2), (12.05, -37.5, 0.62), "marble_g", C1)
add_box("DS_观水沿W", (0.55, 15.0, 0.2), (-12.05, -37.5, 0.62), "marble_g", C1)
stairs("DS_观水阶S", C1, 0, -45, 6.0, 0, 0.55, "S")
stairs("DS_观水阶N", C1, 0, -30, 6.0, 0, 0.55, "N")
balustrade_run("DS_观水栏北东", C1, (2.8, -30.15), (11.8, -30.15), 0.55)
balustrade_run("DS_观水栏北西", C1, (-11.8, -30.15), (-2.8, -30.15), 0.55)
balustrade_run("DS_观水栏南东", C1, (3.2, -44.85), (11.8, -44.85), 0.55)
balustrade_run("DS_观水栏南西", C1, (-11.8, -44.85), (-3.2, -44.85), 0.55)
balustrade_run("DS_观水栏东", C1, (11.85, -44.8), (11.85, -30.2), 0.55)
balustrade_run("DS_观水栏西", C1, (-11.85, -44.8), (-11.85, -30.2), 0.55)
# 两座对称石雕屏风(巴洛克卷草浮雕意象:圆头板+三层横带+双卷草弧+中心团花)
for s2 in (-1, 1):
    sx, sy = s2 * 6.5, -33.0
    add_box(f"DS_屏风座{s2}", (3.9, 1.7, 0.62), (sx, sy, 0.55 + 0.31), "marble_g", C1)
    add_box(f"DS_屏风裙{s2}", (4.3, 2.0, 0.12), (sx, sy, 1.11), "marble_g", C1)   # 座上裙线脚
    arch_slab(f"DS_屏风板{s2}", C1, sx, sy, 1.17, w=3.0, h_rect=2.6, depth=0.5, mat="jade")
    for k, zz in enumerate((1.75, 2.35, 2.95)):   # 浮雕横带
        add_box(f"DS_屏带{s2}{k}", (2.7, 0.16, 0.18), (sx, sy + 0.22, zz), "jade", C1)
    a1 = add_torus_arc(f"DS_屏卷{s2}a", 0.5, 0.09, (sx - 0.62, sy + 0.26, 3.3), "jade", C1, axis="x", major=10, minor=5, sz=1.0)
    a2 = add_torus_arc(f"DS_屏卷{s2}b", 0.5, 0.09, (sx + 0.62, sy + 0.26, 3.3), "jade", C1, axis="x", major=10, minor=5, sz=1.0)
    bake_rot_z(a2, (sx + 0.62, sy + 0.26), math.pi)   # 反向卷草 → S 形对卷
    add_ico(f"DS_屏花{s2}", 0.24, (sx, sy + 0.24, 2.55), (1, 1, 0.4), 1, "jade", C1)
    add_box(f"DS_屏边{s2}a", (0.34, 0.66, 2.9), (sx - 1.45, sy, 1.17 + 1.45), "marble_g", C1)
    add_box(f"DS_屏边{s2}b", (0.34, 0.66, 2.9), (sx + 1.45, sy, 1.17 + 1.45), "marble_g", C1)
    add_box(f"DS_屏帽{s2}a", (0.5, 0.8, 0.32), (sx - 1.45, sy, 4.02), "marble_g", C1)
    add_box(f"DS_屏帽{s2}b", (0.5, 0.8, 0.32), (sx + 1.45, sy, 4.02), "marble_g", C1)
    add_ico(f"DS_屏顶{s2}", 0.17, (sx, sy, 5.32), (1, 1, 1.2), 1, "jade", C1)   # 圆顶饰
# 左右铜鹤(铜雕意象)
bronze_crane("DS_铜鹤东", C1, 10.3, -33.0, 0.55)
bronze_crane("DS_铜鹤西", C1, -10.3, -33.0, 0.55)
# 台地四角石雕瓶饰(呼应铜版画观水法台角陈设)
for s2x in (-1, 1):
    for s2y in (-1, 1):
        finial_vase(f"DS_台角瓶{s2x}{s2y}", C1, s2x * 11.2, -31.1 if s2y > 0 else -43.9, 0.55, s=1.45)

# ================================================================= §2 海棠形大喷水池(原点=池中心)
C2 = coll("DS_海棠喷水池")
NSEG = 96
rim_h = 0.95
rim_in, rim_out = [], []
for i in range(NSEG):
    t = 2 * math.pi * i / NSEG
    ri = 8.2 + 1.4 * math.cos(4 * t)          # 海棠四瓣曲线(瓣朝东西南北)
    rim_in.append((math.cos(t) * ri, math.sin(t) * ri))
    ro = ri + 1.05
    rim_out.append((math.cos(t) * ro, math.sin(t) * ro))
# 池壁(汉白玉):外壁/内壁/顶环三段开口条带(不加端盖——端盖会把整个池面封成白板)
v, f = [], []
for zz in (0.0, rim_h):
    for (x, y) in rim_out:
        v.append((x, y, zz))
for i in range(NSEG):
    j = (i + 1) % NSEG
    f += [(i, j, j + NSEG, i + NSEG)]
_obj("DS_池壁外", v, f, "jade", C2)
v, f = [], []
for zz in (0.0, rim_h):
    for (x, y) in rim_in:
        v.append((x, y, zz))
for i in range(NSEG):
    j = (i + 1) % NSEG
    f += [(i + NSEG, j + NSEG, j, i)]
_obj("DS_池壁内", v, f, "jade", C2)
v, f = [], []
for (x, y) in rim_in:
    v.append((x, y, rim_h))
for (x, y) in rim_out:
    v.append((x, y, rim_h))
for i in range(NSEG):
    j = (i + 1) % NSEG
    f.append((i, j, j + NSEG, i + NSEG))
_obj("DS_池壁顶", v, f, "jade", C2)
# 池水(扇形水面)
v = [(0, 0, 0.72)] + [(x, y, 0.72) for (x, y) in rim_in]
f = [(0, i + 1, (i + 1) % NSEG + 1) for i in range(NSEG)]
_obj("DS_池水", v, f, "water", C2, smooth=True)
# 中央"狮子喷水水盘"铜雕(狮身头顶双层水盘)
lion_fountain("DS_铜狮水盘", C2, 0, 0, 0.5)
# "猎狗逐鹿"铜雕群:中央铜鹿(昂首)+ 四只铜犬向鹿喷水
DX, DY = 0.0, 4.2                     # 鹿群中心(池北侧)
bronze_deer("DS_铜鹿", C2, DX, DY, math.radians(-90))   # 鹿面朝南(向铜狮/观水法)
deer_nose = (DX + 1.55 * math.cos(math.radians(-90)), DY + 1.55 * math.sin(math.radians(-90)), 2.82)
dog_spots = [(DX + 3.3, DY - 2.4), (DX - 3.3, DY - 2.4), (DX + 3.0, DY + 2.2), (DX - 3.0, DY + 2.2)]
for k, (dxp, dyp) in enumerate(dog_spots):
    ang = math.atan2(DY - dyp, DX - dxp)   # 朝向铜鹿
    bronze_dog(f"DS_铜犬{k+1}", C2, dxp, dyp, ang)
    nx = dxp + 0.92 * math.cos(ang)
    ny = dyp + 0.92 * math.sin(ang)
    # 水线:犬口 → 鹿身(细杆意象)
    add_beam(f"DS_犬水线{k+1}", (nx, ny, 1.82), (DX, DY, 1.95), 0.06, 0.06, "water", C2)

# ================================================================= §3 大水法石龛(核心,巴洛克屏风式)
C3 = coll("DS_大水法石龛")
# 底层须弥座(两级)
add_box("DS_龛座一", (31.4, 4.6, 0.45), (0, 13.1, 0.225), "marble_g", C3)
add_box("DS_龛座二", (30.6, 3.9, 0.45), (0, 13.15, 0.675), "marble_g", C3)
# 龛体主墙:左右两大块 + 拱跨上 spandrel(中央留出大拱门洞)
add_box("DS_龛墙西", (12.1, 1.8, 9.6), (-8.55, 13.1, 5.7), "marble_g", C3)
add_box("DS_龛墙东", (12.1, 1.8, 9.6), (8.55, 13.1, 5.7), "marble_g", C3)
add_box("DS_龛墙拱上", (5.0, 1.8, 1.8), (0, 13.1, 9.6), "marble_g", C3)
# 中央大拱门:圆拱圈(半环拱券)+ 拱心石
arch_ring("DS_大拱门", C3, 0, 13.1, 6.2, r_in=2.5, r_out=3.35, depth=2.0, mat="marble_g", major=18)
# 两侧各 4 根镶入式壁柱(环状凸条意象)±(4.1, 6.5, 8.9, 11.3)
for s2 in (-1, 1):
    for k, px in enumerate((4.1, 6.5, 8.9, 11.3)):
        pilaster(f"DS_壁柱{s2}{k}", C3, s2 * px, 11.95, 0.9, 9.6, w=1.05, depth=0.5, mat="marble_g", bands=5)
# 壁柱间壁龛(内嵌人像雕像)±(5.3, 7.7, 10.1):龛腔暗板微凸出墙面,立像立于龛前
for s2 in (-1, 1):
    for k, nx in enumerate((5.3, 7.7, 10.1)):
        add_box(f"DS_壁龛{s2}{k}", (1.3, 0.35, 4.4), (s2 * nx, 12.3, 5.2), "niche", C3)   # 龛腔暗部
        niche_statue(f"DS_龛像{s2}{k}", C3, s2 * nx, 12.15, 3.0, h=3.6, mat="jade")
# 龛墙横缝线脚(条石砌筑意象,呼应遗址块石缝;拱门洞范围内断开)
for k in range(7):
    zb = 2.2 + 1.15 * k
    if zb < 8.8:
        oh = 2.5 if zb <= 6.25 else max(0.9, math.sqrt(max(0.0, 2.5 ** 2 - (zb - 6.2) ** 2))) + 0.15
        for s2 in (-1, 1):
            xw = 14.5 - oh
            add_box(f"DS_龛缝{k}{s2}", (xw, 1.86, 0.09), (s2 * (oh + xw / 2), 13.1, zb), "marble_g", C3)
    else:
        add_box(f"DS_龛缝{k}", (29.0, 1.86, 0.09), (0, 13.1, zb), "marble_g", C3)
# 龛顶檐部横带 + 檐下两道线脚 + 巴洛克弧形山花(中跨)+ 顶饰瓶列
add_box("DS_龛檐带", (30.0, 2.2, 0.5), (0, 13.0, 10.75), "marble_g", C3)
add_box("DS_龛檐脚一", (29.8, 2.4, 0.16), (0, 13.0, 10.28), "marble_g", C3)
add_box("DS_龛檐脚二", (29.4, 2.3, 0.14), (0, 13.0, 10.42), "marble_g", C3)
pediment_seg("DS_龛山花", C3, 0, 12.55, 11.0, w=10.5, h=2.5, depth=0.75, mat="marble_g", major=12)
for s2 in (-1, 1):
    for k, vx in enumerate((6.2, 8.4, 10.6, 12.8)):
        finial_vase(f"DS_顶瓶{s2}{k}", C3, s2 * vx, 12.9, 11.0, s=1.0)
# 墙两端转角壁柱(收边)
pilaster("DS_壁柱端东", C3, 13.7, 11.95, 0.9, 9.6, w=1.0, depth=0.5, mat="marble_g", bands=5)
pilaster("DS_壁柱端西", C3, -13.7, 11.95, 0.9, 9.6, w=1.0, depth=0.5, mat="marble_g", bands=5)
# 两侧对称塔柱(多层收分,顶部球饰)+ 塔柱南面底层小拱门
tower_pier("DS_塔柱东", C3, 16.9, 13.2, w0=4.6, y_d=2.4, z0=0.9, tiers=4)
tower_pier("DS_塔柱西", C3, -16.9, 13.2, w0=4.6, y_d=2.4, z0=0.9, tiers=4)
for s2 in (-1, 1):
    arch_ring(f"DS_塔柱门{s2}", C3, s2 * 16.9, 11.95, 1.7, r_in=0.62, r_out=0.9, depth=0.35, mat="marble_g", major=10)
    add_box(f"DS_塔柱膛{s2}", (1.24, 0.4, 1.7), (s2 * 16.9, 12.0, 0.9 + 0.85), "niche", C3)   # 门洞暗部

# ================================================================= §4 远瀛观(最北,高台上,倒凹字形柱廊大殿)
C4 = coll("DS_远瀛观")
# 高台须弥座(汉白玉,三级)
add_box("DS_远瀛台一", (35.0, 18.5, 0.5), (0, 37.75, 0.25), "jade", C4)
add_box("DS_远瀛台二", (34.2, 17.7, 0.5), (0, 37.75, 0.75), "jade", C4)
add_box("DS_远瀛台三", (33.6, 17.1, 1.2), (0, 37.75, 1.6), "jade", C4)
# 大台阶(南面正中)+ 台周白玉栏杆(南面留阶口)
stairs("DS_远瀛阶", C4, 0, 29, 12.0, 0, 2.2, "S")
balustrade_run("DS_远瀛栏南东", C4, (6.2, 29.15), (17.3, 29.15), 2.2)
balustrade_run("DS_远瀛栏南西", C4, (-17.3, 29.15), (-6.2, 29.15), 2.2)
balustrade_run("DS_远瀛栏东", C4, (17.35, 29.2), (17.35, 46.4), 2.2)
balustrade_run("DS_远瀛栏西", C4, (-17.35, 29.2), (-17.35, 46.4), 2.2)
balustrade_run("DS_远瀛栏北", C4, (-17.3, 46.35), (17.3, 46.35), 2.2)
# 倒凹字形柱廊:前排 9 柱(南)+ 两翼各 5 柱(东西),爱奥尼意象
front_y, side_x, col_h = 31.8, 13.0, 5.8
for k in range(9):
    ionic_column(f"DS_廊柱F{k}", C4, -13.0 + 3.25 * k, front_y, 2.2, col_h, r=0.42, mat="marble_g", face="S")
for s2 in (-1, 1):
    for k in range(1, 5):   # k 从 1 起:前排转角柱已占 (±13, 31.8),避免重柱
        ionic_column(f"DS_廊柱{s2}{k}", C4, s2 * side_x, 31.8 + 3.05 * k, 2.2, col_h, r=0.42, mat="marble_g", face="E")
# 檐部(檐框+檐壁两道+饰线三条)沿倒凹形三边
add_box("DS_檐框F", (29.0, 1.1, 0.45), (0, front_y, 8.22), "marble_g", C4)
add_box("DS_檐壁F", (29.6, 1.3, 0.55), (0, front_y, 8.72), "marble_g", C4)
for k, zz in enumerate((8.52, 8.72, 8.92)):   # 檐壁饰线(三道齿线意象)
    add_box(f"DS_檐饰F{k}", (29.5, 1.36, 0.08), (0, front_y, zz), "jade", C4)
for s2 in (-1, 1):
    add_box(f"DS_檐框{s2}", (1.1, 14.6, 0.45), (s2 * side_x, 37.9, 8.22), "marble_g", C4)
    add_box(f"DS_檐壁{s2}", (1.3, 14.6, 0.55), (s2 * side_x, 37.9, 8.72), "marble_g", C4)
    for k, zz in enumerate((8.52, 8.72, 8.92)):
        add_box(f"DS_檐饰{s2}{k}", (1.36, 14.5, 0.08), (s2 * side_x, 37.9, zz), "jade", C4)
add_box("DS_檐框B", (27.0, 1.1, 0.45), (0, 44.0, 8.22), "marble_g", C4)
add_box("DS_檐壁B", (27.0, 1.3, 0.55), (0, 44.0, 8.72), "marble_g", C4)
# 檐部弧形山花(中跨)+ 柱廊顶二楼层栏杆
pediment_seg("DS_观山花", C4, 0, front_y, 9.0, w=10.0, h=2.6, depth=0.9, mat="marble_g", major=12)
balustrade_run("DS_层栏东", C4, (5.7, 31.4), (14.0, 31.4), 9.0, post_gap=1.9)
balustrade_run("DS_层栏西", C4, (-14.0, 31.4), (-5.7, 31.4), 9.0, post_gap=1.9)
for s2 in (-1, 1):   # 两翼檐顶栏杆(倒凹侧边)
    balustrade_run(f"DS_层栏翼{s2}", C4, (s2 * 13.0, 33.0), (s2 * 13.0, 43.0), 9.0, post_gap=1.9)
# 殿体两层(柱廊后部)+ 层间线脚带
add_box("DS_殿一层", (21.6, 11.6, 5.8), (0, 40.0, 5.1), "marble_g", C4)
add_box("DS_殿二层", (21.0, 11.0, 4.4), (0, 40.0, 10.2), "marble_g", C4)
add_box("DS_层间带F", (21.8, 0.3, 0.32), (0, 34.1, 8.15), "jade", C4)
for s2 in (-1, 1):
    add_box(f"DS_层间带{s2}", (0.3, 11.8, 0.32), (s2 * 10.9, 40.0, 8.15), "jade", C4)
# 一层:正门 + 门侧双壁柱 + 前窗四樘(西式弧形窗楣)
add_box("DS_殿门", (2.2, 0.5, 3.6), (0, 34.15, 4.0), "wood", C4)
for s2 in (-1, 1):
    pilaster(f"DS_门柱{s2}", C4, s2 * 2.0, 34.3, 2.2, 5.8, w=0.9, depth=0.45, mat="marble_g", bands=4)
for k, wx in enumerate((-6.5, -3.25, 3.25, 6.5)):
    add_box(f"DS_殿窗1F{k}", (1.4, 0.4, 2.8), (wx, 34.15, 4.7), "niche", C4)
    add_box(f"DS_殿窗1F{k}h", (1.6, 0.45, 0.25), (wx, 34.15, 6.25), "jade", C4)
    pediment_seg(f"DS_窗楣{k}", C4, wx, 34.05, 6.4, w=1.9, h=0.55, depth=0.35, mat="marble_g", major=8)
# 二层:前窗五樘 + 侧窗
for k, wx in enumerate((-6.5, -3.25, 0, 3.25, 6.5)):
    add_box(f"DS_殿窗2F{k}", (1.2, 0.4, 2.0), (wx, 34.45, 10.3), "niche", C4)
for s2 in (-1, 1):
    for k, wy in enumerate((35.4, 37.8, 40.2, 42.6)):
        add_box(f"DS_殿窗1{s2}{k}", (0.4, 1.4, 2.8), (s2 * 10.95, wy, 4.7), "niche", C4)
        add_box(f"DS_殿窗2{s2}{k}", (0.4, 1.2, 2.0), (s2 * 10.62, wy, 10.3), "niche", C4)
# 重檐庑殿顶(中式灰瓦 — 中西合璧,按铜版画):下檐腰檐 + 上檐主顶
roof_l, info_l = roof_tube("DS_远瀛腰檐", C4, 25.5, 15.0, 2.3, 12.35, kind="wudian",
                           eave=1.35, lift=0.6, ridge_w=12.0, rings=6, mat="tile", ox=0, oy=40.0)
add_tiles("DS_腰檐瓦", C4, info_l, "tile_d", strip_w=0.26, gap=0.52)
hip_ridges("DS_腰檐脊", C4, info_l, "tile_d")
add_box("DS_上檐墙", (13.0, 7.0, 1.2), (0, 40.0, 15.1), "marble_g", C4)   # 上檐短墙(重檐之间)
for k, wx in enumerate((-4.0, -2.0, 0, 2.0, 4.0)):                        # 上檐墙通气小窗
    add_box(f"DS_檐窗{k}", (0.9, 0.35, 0.6), (wx, 36.45, 15.1), "niche", C4)
roof_u, info_u = roof_tube("DS_远瀛主顶", C4, 17.0, 10.0, 5.0, 14.9, kind="wudian",
                           eave=1.5, lift=0.7, ridge_w=2.8, rings=7, mat="tile", ox=0, oy=40.0)
add_tiles("DS_主顶瓦", C4, info_u, "tile_d", strip_w=0.26, gap=0.52)
hip_ridges("DS_主顶脊", C4, info_u, "tile_d")
ridge_cn("DS_主顶正脊", C4, info_u, "tile_d")

# ================================================================= §5 环境:场地/草坪/步道/塔柏/矮墙
C5 = coll("DS_环境")
# 素土大场地(兜底地面,防止草坪/步道边缘外露空洞;尺寸贴近草坪外缘)
add_prism("DS_场地", [(-64, -58), (64, -58), (64, 58), (-64, 58)], -0.05, 0.05, "earth", C5)
# 碎石步道:中轴南北两段 + 池周回廊盘 + 东西横道
add_prism("DS_步道南", [(-2.6, -52), (2.6, -52), (2.6, -9.9), (-2.6, -9.9)], 0, 0.14, "gravel", C5)
add_prism("DS_步道北", [(-2.6, 9.9), (2.6, 9.9), (2.6, 24.4), (-2.6, 24.4)], 0, 0.14, "gravel", C5)
add_cyl("DS_池周道", 11.9, 11.9, 0.12, (0, 0, 0.06), "gravel", C5, n=72)
add_prism("DS_步道横东", [(9.8, -2.6), (19.8, -2.6), (19.8, 2.6), (9.8, 2.6)], 0, 0.14, "gravel", C5)
add_prism("DS_步道横西", [(-19.8, -2.6), (-9.8, -2.6), (-9.8, 2.6), (-19.8, 2.6)], 0, 0.14, "gravel", C5)
# 东西草坪(对称;中段让开东西横步道,分成南北两块)
add_prism("DS_草坪东南", [(11.9, -52), (58, -52), (58, -2.7), (11.9, -2.7)], 0, 0.26, "grass", C5)
add_prism("DS_草坪东北", [(11.9, 2.7), (58, 2.7), (58, 52), (11.9, 52)], 0, 0.26, "grass", C5)
add_prism("DS_草坪西南", [(-58, -52), (-11.9, -52), (-11.9, -2.7), (-58, -2.7)], 0, 0.26, "grass", C5)
add_prism("DS_草坪西北", [(-58, 2.7), (-11.9, 2.7), (-11.9, 52), (-58, 52)], 0, 0.26, "grass", C5)
add_prism("DS_草坪南东", [(2.7, -52), (11.8, -52), (11.8, -9.9), (2.7, -9.9)], 0, 0.26, "grass", C5)
add_prism("DS_草坪南西", [(-11.8, -52), (-2.7, -52), (-2.7, -9.9), (-11.8, -9.9)], 0, 0.26, "grass", C5)
add_prism("DS_草坪龛后东", [(2.7, 9.9), (11.8, 9.9), (11.8, 24.4), (2.7, 24.4)], 0, 0.26, "grass", C5)
add_prism("DS_草坪龛后西", [(-11.8, 9.9), (-2.7, 9.9), (-2.7, 24.4), (-11.8, 24.4)], 0, 0.26, "grass", C5)
add_prism("DS_草坪北", [(-11.9, 46.6), (11.9, 46.6), (11.9, 52), (-11.9, 52)], 0, 0.26, "grass", C5)
# 两翼矮墙(东西对称,中段留横道口,北端接大水法塔柱)
low_wall("DS_矮墙东a", C5, (19.6, -24), (19.6, -6.5), h=1.3)
low_wall("DS_矮墙东b", C5, (19.6, 6.5), (19.6, 14.2), h=1.3)
low_wall("DS_矮墙西a", C5, (-19.6, -24), (-19.6, -6.5), h=1.3)
low_wall("DS_矮墙西b", C5, (-19.6, 6.5), (-19.6, 14.2), h=1.3)
# 对称塔柏列(柱形柏)
cyp_rows = [(-42), (-34), (-26), (-18), (-10), (-2), 6]
for s2 in (-1, 1):
    for k, yy in enumerate(cyp_rows):
        cypress(f"DS_塔柏{s2}{k}", C5, s2 * 15.8, yy, 0.26, s=random.uniform(0.85, 1.15))
cypress("DS_塔柏门南东", C5, 4.5, -47.5, 0.26, s=1.05)
cypress("DS_塔柏门南西", C5, -4.5, -47.5, 0.26, s=1.05)
cypress("DS_塔柏阶东", C5, 8.5, 23.8, 0.26, s=1.0)
cypress("DS_塔柏阶西", C5, -8.5, 23.8, 0.26, s=1.0)

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

GROUPS = [("DS_观水法", C1), ("DS_海棠喷水池", C2), ("DS_大水法石龛", C3),
          ("DS_远瀛观", C4), ("DS_环境", C5)]
for gname, c in GROUPS:
    finalize_group(list(c.objects), gname, c)

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
    print(f"{o.name:<16} {t:>8} tris")
print(f"{'TOTAL':<16} {total:>8} tris  (预算 ≤ 250k)")

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
