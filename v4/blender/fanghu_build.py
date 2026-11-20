# -*- coding: utf-8 -*-
"""
================================================================================
 方壶胜境 · 评审级程序化建模脚本  (Blender 5.1 headless / bpy)
================================================================================
考据依据:
  - 《圆明园四十景图咏·方壶胜境》绢画(唐岱/沈源,乾隆九年 1744 绘,布局自建成未改动)
  - 清宫档案(《日下旧闻考》/样式房图档) + 人大清史所研究文
场景结构(自南向北 = 自 -Y 到 +Y;原点=主台基中心;水面 z=0):
  [1] 南侧入口:三开间六柱两夹墙冲天牌楼 + 四角华表 + 苍松        → §7
  [2] 小湖南侧两座形制不同的木板桥                               → §8
  [3] 湖中"山"字形三座重檐大亭(汉白玉台基伸入湖中)              → §4
  [4] 九孔石桥 + 两端牌楼(西"金鳌"、东"玉蝀")+ 石雕喷盘          → §6
  [5] 正殿序列:哕鸾殿(单层五楹) → 琼华楼(二层,前后各五楹)       → §2/§3
  [6] 后部九座佛楼(二~三层楼阁)+ 若干密檐佛塔                    → §5
  [7] 东侧蕊珠宫建筑组                                           → §9
  [8] 西侧三潭印月:三座小石塔 + 五座亭子与曲折连廊               → §10
  [9] 北侧天宇空明建筑群                                         → §11
  [10]全局:汉白玉台基/白玉栏杆阵列/荷叶/垂柳苍松/青绿山丘         → §1/§12/§13
修改器运用:ARRAY(望柱/斗拱/檐柱/廊柱阵列) MIRROR(山字亭组对称/牌楼夹墙)
            SOLIDIFY(栏杆栏板/夹墙) BEVEL(抱柱石/须弥座)
材质调色板(与 v4 场景一致,无贴图、几何承载细节):
  汉白玉 #F2EDE2(r0.35) 朱红 #8B2020(0.6) 青绿琉璃 #2A6A5A(0.3)
  金黄 #E8A800(0.25, metal0.7) 灰瓦 #5A5F66 木棕 #6B4A2E
用法:
  /Applications/Blender.app/Contents/MacOS/Blender --background \
      --python v4/blender/fanghu_build.py
输出:
  /tmp/fangpu_raw.glb(未压缩;export_apply=True 于导出时应用全部修改器)
================================================================================
"""
import bpy, bmesh, math, os, random, re
from mathutils import Vector

OUT_GLB = "/tmp/fangpu_raw.glb"
random.seed(42)

# ---------------------------------------------------------------- 名称安全化
# Blender 5.1.1 的 BLI_string_split_name_number(每建一个 ID 都会走 namemap 唯一化)
# 会对"最后一个'.'之后的纯数字串"调用 std::stoi 且无 try/catch 保护:
# 若小数点后是超过 int32 的纯数字(如 f"{2.8800000000000003}" 的 16 位小数),
# 抛 std::out_of_range 未捕获 → 进程 abort。
# 对策:所有 ID 名一律去掉"点+数字"段,并追加全局递增序号
# (序号以'_'分隔,最后一个'.'之后永远不是纯数字,解析器不会触碰),
# 顺带保证全局唯一,免去唯一化重名扫描。
_SNC = 0

def safe_name(name):
    global _SNC
    _SNC += 1
    base = re.sub(r"\.[0-9]+", "", str(name))      # 去掉"点+纯数字"段
    return f"{base}_{_SNC:05d}"

# 坐标: x 向东, y 向北, z 向上; 水面 z=0, 岸面 z=0.6
Z_LAND, Z_LOW, Z_UP = 0.6, 1.0, 2.0   # 岸地面 / 主台下层面 / 主台上层面

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
    return m

M = {
    "marble":  _mat("M_汉白玉",   0xF2EDE2, 0.35),
    "red":     _mat("M_朱红",     0x8B2020, 0.60),
    "glaze":   _mat("M_青绿琉璃", 0x2A6A5A, 0.30),
    "glaze_d": _mat("M_琉璃瓦垄", 0x225648, 0.32),
    "gold":    _mat("M_金黄",     0xE8A800, 0.25, 0.7),
    "tile":    _mat("M_灰瓦",     0x5A5F66, 0.55),
    "tile_d":  _mat("M_灰瓦垄",   0x4B5057, 0.58),
    "wood":    _mat("M_木棕",     0x6B4A2E, 0.70),
    "leaf_d":  _mat("M_苍松",     0x3E5A38, 0.90),
    "leaf_l":  _mat("M_垂柳",     0x6E8B5E, 0.90),
    "lotus":   _mat("M_荷叶",     0x3C6B45, 0.75),
    "flower":  _mat("M_荷花",     0xE5B8C4, 0.80),
    "hill":    _mat("M_青绿山丘", 0x5E7D68, 1.00),
    "hill2":   _mat("M_远山",     0x72907E, 1.00),
    "stone":   _mat("M_岸石",     0x8A8D8A, 0.80),
    "earth":   _mat("M_岛岸地表", 0x5E7D68, 0.95),
    # 琼华楼旋子彩画三色(考据④:青绿底+金色线条)
    "cai_blue":  _mat("M_彩画青", 0x2E5E6E, 0.45),
    "cai_green": _mat("M_彩画绿", 0x3E6B52, 0.45),
    "cai_gold":  _mat("M_彩画金", 0xD8A94E, 0.40),
}

root = bpy.data.collections.new("FS_方壶胜境")
bpy.context.scene.collection.children.link(root)
ROOT_EMPTY = bpy.data.objects.new("FS_方壶胜境", None)
bpy.context.scene.collection.objects.link(ROOT_EMPTY)

def coll(name):
    c = bpy.data.collections.new(name)
    root.children.link(c)
    return c

# ================================================================= 基础几何工厂
def _obj(name, verts, faces, mat, c, smooth=False):
    name = safe_name(name)          # 所有 mesh/object ID 名过安全化(防 namemap stoi 崩溃)
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
    name = safe_name(name)          # 同样过安全化
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
    """半圆拱圈:axis='x' 拱开口沿 x(桥沿 y 走);axis='y' 拱开口沿 y"""
    v, f = [], []
    for i in range(major + 1):
        a = math.pi * i / major          # 0..pi, 拱从 (R,0) 到 (-R,0)
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

def bake_rot_z(obj, pivot, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    for vtx in obj.data.vertices:
        dx, dy = vtx.co.x - pivot[0], vtx.co.y - pivot[1]
        vtx.co.x = pivot[0] + dx * ca - dy * sa
        vtx.co.y = pivot[1] + dx * sa + dy * ca

def bake_rot_x(obj, pivot, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    for vtx in obj.data.vertices:
        dy, dz = vtx.co.y - pivot[1], vtx.co.z - pivot[2]
        vtx.co.y = pivot[1] + dy * ca - dz * sa
        vtx.co.z = pivot[2] + dy * sa + dz * ca

# ================================================================= 屋面系统
_P = 40  # 每环点数

def _rring(hw, hd, e=3.0):
    """超椭圆环(近似中国屋顶平面:方中带圆角)"""
    pts = []
    for i in range(_P):
        t = 2 * math.pi * i / _P
        ct, st = math.cos(t), math.sin(t)
        x = hw * (abs(ct) ** (2 / e)) * (1 if ct >= 0 else -1)
        y = hd * (abs(st) ** (2 / e)) * (1 if st >= 0 else -1)
        pts.append((x, y))
    return pts

def roof_tube(name, c, w, d, h, z0, kind="xieshan", eave=1.2, lift=0.8,
              ridge_w=None, rings=8, mat="glaze", ox=0.0, oy=0.0):
    """
    曲面屋顶壳(檐口起翘 + 举折曲线),返回 (object, info)
      wudian   庑殿/腰檐(四坡,进深收至窄脊)
      xieshan  歇山(下段收深,上段垂直山花,由 add_xieshan_gable 补山花)
      zhanjian 攒尖
    """
    ridge_w = ridge_w if ridge_w else max(0.9, w * 0.05)
    hw0, hd0 = w / 2 + eave, d / 2 + eave
    gable_s, dg = 0.58, d * 0.30
    rows, zs, hs = [], [], []
    for i in range(rings + 1):
        s = i / rings
        if kind == "zhanjian":
            we = s ** 0.92
            wi = hw0 * (1 - we) + 0.22 * we
            di = hd0 * (1 - we) + 0.22 * we
        elif kind == "xieshan":
            we_g = gable_s ** 0.92
            wg = hw0 * (1 - we_g) + (ridge_w / 2) * we_g
            if s <= gable_s:
                t = (s / gable_s) ** 0.92
                wi = hw0 * (1 - t) + wg * t
                di = hd0 * (1 - t) + (dg / 2) * t
            else:
                t = ((s - gable_s) / (1 - gable_s)) ** 0.92
                wi = wg * (1 - t) + (ridge_w / 2) * t
                di = dg / 2
        else:  # wudian
            we = s ** 0.92
            wi = hw0 * (1 - we) + (ridge_w / 2) * we
            di = hd0 * (1 - we) + 0.45 * we
        z = h * (s ** 1.45)   # 举折:檐缓脊陡
        rows.append(_rring(wi, di))
        zs.append(z)
        hs.append((wi, di))
    v, f = [], []
    for ri in range(rings + 1):
        z = zs[ri]
        k = (1 - ri / rings) ** 1.5   # 檐口起翘:角部随高度衰减
        for (x, y) in rows[ri]:
            corner = min(1.0, (abs(x) / max(hw0, 1e-4)) * (abs(y) / max(hd0, 1e-4))) ** 1.5
            v.append((x + ox, y + oy, z0 + z + lift * corner * k))
    for ri in range(rings):
        for k2 in range(_P):
            a = ri * _P + k2
            b = ri * _P + (k2 + 1) % _P
            f.append((a, b, b + _P, a + _P))
    top = rings * _P
    if kind == "zhanjian":
        v.append((ox, oy, z0 + h + 0.12))
        apex = len(v) - 1
        for k2 in range(_P):
            f.append((top + k2, top + (k2 + 1) % _P, apex))
    else:
        f.append(tuple(range(top, top + _P)))
    ob = _obj(name, v, f, mat, c, smooth=True)
    return ob, {"hw0": hw0, "hd0": hd0, "ridge_w": ridge_w, "h": h, "z0": z0,
                "rows": rows, "zs": zs, "hs": hs, "kind": kind, "rings": rings,
                "ox": ox, "oy": oy}

def add_tiles(name, c, info, mat, strip_w=0.30, gap=0.62):
    """瓦垄:顺屋面曲面的细长瓦条(前/后坡;庑殿加左右坡;攒尖放射)"""
    kind = info["kind"]
    zs, hs, z0 = info["zs"], info["hs"], info["z0"]
    parts = []
    if kind == "zhanjian":
        for k in range(18):
            t = 2 * math.pi * k / 18 + 0.09
            ct, st = math.cos(t), math.sin(t)
            vv, f = [], []
            m = 0
            for ri in range(info["rings"] + 1):
                hw, hd = hs[ri]
                r = (hw + hd) / 2
                px, py = ct * r + info["ox"], st * r + info["oy"]
                zz = z0 + zs[ri] + 0.035
                vv += [(px - st * strip_w / 2, py + ct * strip_w / 2, zz),
                       (px + st * strip_w / 2, py - ct * strip_w / 2, zz)]
                m += 1
            for i in range(m - 1):
                a = 2 * i
                f.append((a, a + 1, a + 3, a + 2))
            parts.append(_obj(f"{name}_t{k}", vv, f, mat, c))
        return parts
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
                vv += [(xi + info["ox"] - strip_w / 2, yb + info["oy"], zz), (xi + info["ox"] + strip_w / 2, yb + info["oy"], zz)]
                m += 1
            for i in range(m - 1):
                a = 2 * i
                if side > 0:
                    f.append((a, a + 1, a + 3, a + 2))
                else:
                    f.append((a + 1, a, a + 2, a + 3))
            if m > 1:
                parts.append(_obj(f"{name}_t{xi:.0f}_{side}", vv, f, mat, c))
    if kind == "wudian":
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
                    vv += [(xb + info["ox"], yi + info["oy"] - strip_w / 2, zz), (xb + info["ox"], yi + info["oy"] + strip_w / 2, zz)]
                    m += 1
                for i in range(m - 1):
                    a = 2 * i
                    f.append((a, a + 1, a + 3, a + 2))
                if m > 1:
                    parts.append(_obj(f"{name}_ts{yi:.0f}_{side}", vv, f, mat, c))
    return parts

def roof_ornament(name, c, info, ridge_mat="gold"):
    """正脊+鸱吻(歇山/庑殿)或宝顶(攒尖)——金色仅点缀屋脊宝顶"""
    parts = []
    kind = info["kind"]
    if kind == "zhanjian":
        zt = info["z0"] + info["h"] + 0.12
        parts.append(add_cyl(f"{name}_bdb", 0.5, 0.42, 0.3, (info["ox"], info["oy"], zt + 0.12), "gold", c, n=10))
        parts.append(add_ico(f"{name}_bdb2", 0.34, (info["ox"], info["oy"], zt + 0.56), (1, 1, 1), 1, "gold", c))
        parts.append(add_cyl(f"{name}_bdz", 0.06, 0.0, 1.0, (info["ox"], info["oy"], zt + 1.15), "gold", c, n=8, smooth=False))
    else:
        zt = info["z0"] + info["h"] + 0.2
        rw = info["ridge_w"] if kind == "wudian" else max(info["ridge_w"], 1.2)
        parts.append(add_box(f"{name}_zj", (rw + 0.7, 0.42, 0.4), (info["ox"], info["oy"], zt), ridge_mat, c))
        for s in (-1, 1):
            xe = info["ox"] + s * (rw / 2 + 0.28)
            parts.append(add_box(f"{name}_wen{s}", (0.42, 0.52, 0.8), (xe, info["oy"], zt + 0.32), "gold", c))
            parts.append(add_ico(f"{name}_wenb{s}", 0.22, (xe + s * 0.2, info["oy"], zt + 0.82), (1, 1, 1), 1, "gold", c))
    return parts

def hip_ridges(name, c, info, mat="glaze_d"):
    """垂脊:檐角 → 脊端"""
    parts = []
    if info["kind"] == "zhanjian":
        for k in range(4):
            t = math.pi / 4 + k * math.pi / 2
            hw, hd = info["hs"][2]
            r = (hw + hd) / 2
            parts.append(add_beam(f"{name}_cxj{k}",
                                  (info["ox"] + math.cos(t) * r * 1.12, info["oy"] + math.sin(t) * r * 1.12, info["z0"] + info["h"] * 0.30),
                                  (info["ox"], info["oy"], info["z0"] + info["h"] + 0.12), 0.22, 0.16, mat, c))
    else:
        rw = info["ridge_w"]
        for sx in (-1, 1):
            for sy in (-1, 1):
                hw, hd = info["hs"][0]
                p1 = (info["ox"] + sx * hw * 0.96, info["oy"] + sy * hd * 0.96, info["z0"] + 0.3)
                if info["kind"] == "wudian":
                    p2 = (info["ox"] + sx * rw / 2, info["oy"], info["z0"] + info["h"] + 0.1)
                else:
                    hwg, hdg = info["hs"][int(info["rings"] * 0.58)]
                    p2 = (info["ox"] + sx * hwg * 0.88, info["oy"], info["z0"] + info["h"] * 0.58 ** 1.45 + 0.1)
                parts.append(add_beam(f"{name}_cxj{sx}{sy}", p1, p2, 0.24, 0.18, mat, c))
    return parts

# ================================================================= 构件:栏杆/斗拱/柱
def balustrade_run(name, c, p1, p2, z0, mat="marble", post_gap=2.2, panel=True):
    """望柱+寻杖+栏板 一段(望柱单根 ARRAY 阵列;栏板 SOLIDIFY)"""
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

def dougong_unit(name, c, loc, mat="glaze", s=1.0, along="x"):
    """一朵简化斗拱:大斗+泥道拱+上层拱+散斗×3(共 6 box)"""
    parts = []
    x, y, z = loc
    ry = 0.0 if along == "x" else math.pi / 2
    parts.append(add_box(f"{name}a", (0.52 * s, 0.44 * s, 0.26 * s), (x, y, z + 0.13 * s), mat, c, rot_z=ry))
    parts.append(add_box(f"{name}b", (1.45 * s, 0.20 * s, 0.14 * s), (x, y, z + 0.33 * s), mat, c, rot_z=ry))
    parts.append(add_box(f"{name}c", (1.05 * s, 0.18 * s, 0.12 * s), (x, y, z + 0.46 * s), mat, c, rot_z=ry))
    for k, dx in enumerate((-0.42, 0.0, 0.42)):
        ox, oy = (dx * s, 0) if along == "x" else (0, dx * s)
        parts.append(add_box(f"{name}d{k}", (0.20 * s, 0.18 * s, 0.12 * s),
                             (x + ox, y + oy, z + 0.58 * s), mat, c, rot_z=ry))
    return parts

def dougong_run(name, c, p1, p2, z, n_units, mat="glaze", s=1.0, along="x"):
    """檐下一排斗拱:单朵 ARRAY 阵列"""
    p1, p2 = Vector(p1), Vector(p2)
    unit = dougong_unit(f"{name}u", c, (p1.x, p1.y, z), mat, s, along)
    for o in unit:
        md = o.modifiers.new("arr", "ARRAY")
        md.count = max(2, n_units)
        dirv = (p2 - p1) / max(max(2, n_units) - 1, 1)
        md.use_relative_offset = False
        md.use_constant_offset = True
        md.constant_offset_displace = (dirv.x, dirv.y, 0.0)
    return unit

def column_run(name, c, p1, p2, z0, h, mat="red", r=0.28, n_pts=None):
    """一排檐柱(单柱+石础 ARRAY)"""
    p1, p2 = Vector(p1), Vector(p2)
    d = (p2 - p1).length
    if n_pts is None:
        n_pts = max(2, int(round(d / 3.2)) + 1)
    col = add_cyl(f"{name}c", r, r * 0.92, h, (p1.x, p1.y, z0 + h / 2), mat, c, n=12)
    base = add_box(f"{name}b", (r * 2.4, r * 2.4, 0.22), (p1.x, p1.y, z0 + 0.11), "marble", c)
    for o in (col, base):
        md = o.modifiers.new("arr", "ARRAY")
        md.count = n_pts
        dirv = (p2 - p1) / max(n_pts - 1, 1)
        md.use_relative_offset = False
        md.use_constant_offset = True
        md.constant_offset_displace = (dirv.x, dirv.y, 0.0)
    return [col, base]

def lattice_bay(name, c, cx, cy, w, h, z0, face="y"):
    """一开间格扇门窗:槛板+棂条"""
    parts = []
    if face == "y":
        parts.append(add_box(f"{name}p", (w - 0.5, 0.14, h - 0.6), (cx, cy, z0 + (h - 0.6) / 2 + 0.15), "wood", c))
        for fx in (-w / 2 + 0.32, 0.0, w / 2 - 0.32):
            parts.append(add_box(f"{name}m{fx}", (0.09, 0.2, h - 0.6), (cx + fx, cy, z0 + (h - 0.6) / 2 + 0.15), "red", c))
        parts.append(add_box(f"{name}t", (w - 0.4, 0.22, 0.22), (cx, cy, z0 + h - 0.32), "red", c))
    else:
        parts.append(add_box(f"{name}p", (0.14, w - 0.5, h - 0.6), (cx, cy, z0 + (h - 0.6) / 2 + 0.15), "wood", c))
        for fy in (-w / 2 + 0.32, 0.0, w / 2 - 0.32):
            parts.append(add_box(f"{name}m{fy}", (0.2, 0.09, h - 0.6), (cx, cy + fy, z0 + (h - 0.6) / 2 + 0.15), "red", c))
        parts.append(add_box(f"{name}t", (0.22, w - 0.4, 0.22), (cx, cy, z0 + h - 0.32), "red", c))
    return parts

def stairs(name, c, cx, cy, w, z0, z1, face="S", mat="marble"):
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
    elif face == "E":
        for i, yoff in enumerate((-hw, hw)):
            parts.append(add_beam(f"{name}cb{i}", (cx + 0.05, cy + yoff, z1 + 0.15), (cx + run, cy + yoff, z0 + 0.1), 0.55, 0.42, mat, c))
    else:
        for i, yoff in enumerate((-hw, hw)):
            parts.append(add_beam(f"{name}cb{i}", (cx - 0.05, cy + yoff, z1 + 0.15), (cx - run, cy + yoff, z0 + 0.1), 0.55, 0.42, mat, c))
    return parts

# ================================================================= 通用:殿/楼
def build_hall(name, c, cx, cy, z0, bays, bay_w, d, storeys=1, col_hs=(3.9,),
               roof_h=4.6, roof_kind="xieshan", roof_mat="glaze", eave=1.25,
               dg_per_bay=3, lattice="front", back_lattice=False, ridge_w=None,
               lift=0.85):
    """殿/楼:柱网 + 额枋 + 斗拱 + 格扇 + (层间腰檐) + 主屋面 + 脊饰"""
    parts = []
    w = bays * bay_w
    col_h = col_hs[0]
    # 檐柱:前/后檐各一排(bays+1 根,ARRAY)
    for sy in (1, -1):
        yy = cy + sy * (d / 2 - 0.55)
        parts += column_run(f"{name}cf{sy}", c, (cx - w / 2, yy, z0), (cx + w / 2, yy, z0), z0, col_h, r=0.30)
    if d > 12:
        for sx in (1, -1):
            xx = cx + sx * (w / 2 - 0.55)
            parts += column_run(f"{name}cs{sx}", c, (xx, cy - d / 2 + 1.2, z0), (xx, cy + d / 2 - 1.2, z0), z0, col_h, r=0.30)
    # 额枋
    zb = z0 + col_h
    for sy in (1, -1):
        parts.append(add_beam(f"{name}ef{sy}", (cx - w / 2, cy + sy * (d / 2 - 0.55), zb + 0.42),
                              (cx + w / 2, cy + sy * (d / 2 - 0.55), zb + 0.42), 0.5, 0.5, "red", c))
    for sx in (1, -1):
        parts.append(add_beam(f"{name}es{sx}", (cx + sx * (w / 2 - 0.55), cy - d / 2 + 0.6, zb + 0.42),
                              (cx + sx * (w / 2 - 0.55), cy + d / 2 - 0.6, zb + 0.42), 0.45, 0.45, "red", c))
    # 斗拱(檐下每开间 2-3 朵)
    zd = zb + 0.62
    for sy in (1, -1):
        parts += dougong_run(f"{name}df{sy}", c, (cx - w / 2 + 0.7, cy + sy * (d / 2 + 0.16), zd),
                             (cx + w / 2 - 0.7, cy + sy * (d / 2 + 0.16), zd), zd, bays * dg_per_bay, "glaze", 1.0, "x")
    for sx in (1, -1):
        parts += dougong_run(f"{name}ds{sx}", c, (cx + sx * (w / 2 + 0.16), cy - d / 2 + 1.1, zd),
                             (cx + sx * (w / 2 + 0.16), cy + d / 2 - 1.1, zd), zd, max(3, int(d / 2.4)), "glaze", 0.9, "y")
    # 格扇
    zl0, lh = z0 + 0.25, col_h - 0.55
    if lattice in ("front", "both"):
        for b in range(bays):
            bx = cx - w / 2 + bay_w * (b + 0.5)
            parts += lattice_bay(f"{name}lf{b}", c, bx, cy + d / 2 - 0.5, bay_w, lh, zl0)
    if back_lattice and lattice != "both":   # lattice="both" 时后檐格扇已随 both 建过,避免重复
        for b in range(bays):
            bx = cx - w / 2 + bay_w * (b + 0.5)
            parts += lattice_bay(f"{name}lb{b}", c, bx, cy - d / 2 + 0.5, bay_w, lh, zl0)
    # 上层 + 腰檐
    z2 = z0
    if storeys >= 2:
        for st in range(1, storeys):
            col_h2 = col_hs[st] if st < len(col_hs) else col_hs[-1] * 0.85
            z2 = (z2 + col_h + 1.0) if st == 1 else (z2 + col_h2 + 1.0)
            _wo, winf_info = roof_tube(f"{name}wz{st}", c, w + 0.3, d + 0.3, 1.7, z2 - 0.35,
                                       kind="wudian", eave=1.45, lift=0.55, ridge_w=w * 0.5,
                                       rings=5, mat=roof_mat, ox=cx, oy=cy)
            parts.append(_wo)
            parts += add_tiles(f"{name}wt{st}", c, winf_info, "glaze_d" if roof_mat == "glaze" else "tile_d",
                               strip_w=0.26, gap=0.66)
            w2, d2 = w - 2.4, d - 2.4
            for sy in (1, -1):
                yy = cy + sy * (d2 / 2 - 0.5)
                parts += column_run(f"{name}c{st}f{sy}", c, (cx - w2 / 2, yy, z2), (cx + w2 / 2, yy, z2), z2, col_h2, r=0.26)
            for sx in (1, -1):
                xx = cx + sx * (w2 / 2 - 0.5)
                parts += column_run(f"{name}c{st}s{sx}", c, (xx, cy - d2 / 2 + 0.8, z2), (xx, cy + d2 / 2 - 0.8, z2), z2, col_h2, r=0.26)
            zb2 = z2 + col_h2
            for sy in (1, -1):
                parts.append(add_beam(f"{name}e{st}f{sy}", (cx - w2 / 2, cy + sy * (d2 / 2 - 0.5), zb2 + 0.38),
                                      (cx + w2 / 2, cy + sy * (d2 / 2 - 0.5), zb2 + 0.38), 0.44, 0.44, "red", c))
            for sx in (1, -1):
                parts.append(add_beam(f"{name}e{st}s{sx}", (cx + sx * (w2 / 2 - 0.5), cy - d2 / 2 + 0.7, zb2 + 0.38),
                                      (cx + sx * (w2 / 2 - 0.5), cy + d2 / 2 - 0.7, zb2 + 0.38), 0.4, 0.4, "red", c))
            zd2 = zb2 + 0.58
            for sy in (1, -1):
                parts += dougong_run(f"{name}d{st}f{sy}", c, (cx - w2 / 2 + 0.6, cy + sy * (d2 / 2 + 0.14), zd2),
                                     (cx + w2 / 2 - 0.6, cy + sy * (d2 / 2 + 0.14), zd2), zd2, bays * dg_per_bay, "glaze", 0.9, "x")
            for sx in (1, -1):
                parts += dougong_run(f"{name}d{st}s{sx}", c, (cx + sx * (w2 / 2 + 0.14), cy - d2 / 2 + 0.9, zd2),
                                     (cx + sx * (w2 / 2 + 0.14), cy + d2 / 2 - 0.9, zd2), zd2, max(3, int(d2 / 2.6)), "glaze", 0.85, "y")
            for b in range(bays):
                bw2 = (w2 - 2.0) / bays
                bx = cx - (w2 - 2.0) / 2 + bw2 * (b + 0.5)
                for sy in (1, -1):
                    parts += lattice_bay(f"{name}l{st}_{b}_{sy}", c, bx, cy + sy * (d2 / 2 - 0.45), bw2, col_h2 - 0.5, z2 + 0.2)
        z_top, w_top, d_top = z2, w - 2.4, d - 2.4
    else:
        z_top, w_top, d_top = z0, w, d
    # 主屋面
    top_col = col_hs[-1] if (storeys >= 2 and len(col_hs) > 1) else col_h
    zf = z_top + top_col + 1.05
    roof, info = roof_tube(f"{name}rf", c, w_top, d_top, roof_h, zf, kind=roof_kind,
                           eave=eave, lift=lift, ridge_w=ridge_w or w_top * 0.16, rings=8, mat=roof_mat,
                           ox=cx, oy=cy)
    parts.append(roof)
    tmat = "glaze_d" if roof_mat == "glaze" else "tile_d"
    parts += add_tiles(f"{name}tl", c, info, tmat)
    parts += roof_ornament(f"{name}or", c, info, "gold")
    parts += hip_ridges(f"{name}hr", c, info, tmat)
    if roof_kind == "xieshan":
        hwg, hdg = info["hs"][int(info["rings"] * 0.58)]
        zg = zf + info["h"] * (0.58 ** 1.45)
        for sx in (1, -1):
            v = [(cx + sx * hwg, cy - hdg, zg), (cx + sx * hwg, cy + hdg, zg), (cx + info["ridge_w"] / 2, cy, zf + info["h"])]
            parts.append(_obj(f"{name}sf{sx}", v, [(0, 1, 2)], "wood", c))
            parts.append(add_beam(f"{name}bf{sx}a", v[0], v[2], 0.22, 0.16, tmat, c))
            parts.append(add_beam(f"{name}bf{sx}b", v[1], v[2], 0.22, 0.16, tmat, c))
    return parts

def build_gable_hall(name, c, cx, cy, z0, bays, bay_w, d, col_h=3.2, roof_h=2.6, roof_mat="tile"):
    """硬山配殿:两坡直屋面 + 山墙 + 正脊"""
    parts = []
    w = bays * bay_w
    for sy in (1, -1):
        yy = cy + sy * (d / 2 - 0.5)
        parts += column_run(f"{name}c{sy}", c, (cx - w / 2, yy, z0), (cx + w / 2, yy, z0), z0, col_h, r=0.26)
    zb = z0 + col_h
    for sy in (1, -1):
        parts.append(add_beam(f"{name}e{sy}", (cx - w / 2, cy + sy * (d / 2 - 0.5), zb + 0.36),
                              (cx + w / 2, cy + sy * (d / 2 - 0.5), zb + 0.36), 0.42, 0.42, "red", c))
    for b in range(bays):
        bx = cx - w / 2 + bay_w * (b + 0.5)
        parts += lattice_bay(f"{name}l{b}", c, bx, cy + d / 2 - 0.5, bay_w, col_h - 0.55, z0 + 0.2)
    zr = zb + 0.85
    hw2 = w / 2 + 0.7
    run = d / 2 + 0.9
    ang = math.atan2(roof_h, run)
    slope = math.hypot(roof_h, run)
    for s2 in (1, -1):
        p = add_box(f"{name}r{s2}", (hw2 * 2, slope, 0.1), (cx, cy + s2 * run / 2, zr + roof_h / 2), roof_mat, c)
        bake_rot_x(p, (cx, cy, zr + roof_h / 2), -s2 * ang)
        parts.append(p)
    for sx in (1, -1):
        v = [(sx * hw2, cy - run + 0.4, zr - 0.2), (sx * hw2, cy + run - 0.4, zr - 0.2), (sx * hw2, cy, zr + roof_h)]
        parts.append(_obj(f"{name}sg{sx}", v, [(0, 1, 2)], "red", c))
    parts.append(add_box(f"{name}rj", (hw2 * 2 + 0.4, 0.36, 0.3), (cx, cy, zr + roof_h + 0.1), "glaze_d", c))
    for s2 in (1, -1):
        parts.append(add_box(f"{name}wn{s2}", (0.3, 0.42, 0.5), (cx + s2 * (hw2 + 0.15), cy, zr + roof_h + 0.15), "gold", c))
    return parts

def build_ting(name, c, cx, cy, z0, w, col_h=3.2, roof_h=3.4, roof_mat="glaze",
               storeys=1, cols=4, eave=1.15, waist_h=1.5, lift=0.75, s=1.0):
    """攒尖亭(方四柱):单层或重檐(腰檐+上檐攒尖)"""
    parts = []
    pts = []
    for i in range(cols):
        t = math.pi / 4 + math.pi * 2 / cols * i if cols == 4 else math.pi * 2 / cols * i + math.pi / 6
        pts.append((cx + (w / 2 - 0.5) * math.cos(t), cy + (w / 2 - 0.5) * math.sin(t)))
    for i, p in enumerate(pts):
        parts.append(add_cyl(f"{name}c{i}", 0.26, 0.24, col_h, (p[0], p[1], z0 + col_h / 2), "red", c, n=10))
        parts.append(add_box(f"{name}b{i}", (0.62, 0.62, 0.2), (p[0], p[1], z0 + 0.1), "marble", c))
    hw = w / 2 - 0.5
    for i in range(cols):
        j = (i + 1) % cols
        mx, my = (pts[i][0] + pts[j][0]) / 2, (pts[i][1] + pts[j][1]) / 2
        ang = math.atan2(pts[j][1] - pts[i][1], pts[j][0] - pts[i][0])
        ln = math.hypot(pts[j][0] - pts[i][0], pts[j][1] - pts[i][1])
        parts.append(add_box(f"{name}bn{i}", (ln, 0.12, 0.4), (mx, my, z0 + 0.44), "red", c, rot_z=ang))
    zb = z0 + col_h
    for i in range(cols):
        j = (i + 1) % cols
        parts.append(add_beam(f"{name}e{i}", (pts[i][0], pts[i][1], zb + 0.35), (pts[j][0], pts[j][1], zb + 0.35), 0.4, 0.4, "red", c))
    zd = zb + 0.58
    for i in range(cols):
        j = (i + 1) % cols
        q1 = (pts[i][0] * 0.97 + pts[j][0] * 0.03, pts[i][1] * 0.97 + pts[j][1] * 0.03)
        q2 = (pts[j][0] * 0.97 + pts[i][0] * 0.03, pts[j][1] * 0.97 + pts[i][1] * 0.03)
        al = "x" if abs(pts[j][0] - pts[i][0]) > abs(pts[j][1] - pts[i][1]) else "y"
        parts += dougong_run(f"{name}d{i}", c, (q1[0], q1[1], zd), (q2[0], q2[1], zd), zd, 3, "glaze", 0.8 * s, al)
    zf = zb + 1.1
    if storeys >= 2:
        _wo, winf_info = roof_tube(f"{name}wz", c, w + 0.5, w + 0.5, waist_h, zf - 0.3, kind="wudian",
                                   eave=1.35, lift=0.6, ridge_w=w * 0.42, rings=5, mat=roof_mat,
                                   ox=cx, oy=cy)
        parts.append(_wo)
        parts += add_tiles(f"{name}wt", c, winf_info, "glaze_d" if roof_mat == "glaze" else "tile_d", strip_w=0.24, gap=0.6)
        z2 = zf + waist_h + 0.55
        w2 = w - 2.2
        pts2 = [(cx + (p[0] - cx) * (w2 / w), cy + (p[1] - cy) * (w2 / w)) for p in pts]
        for i, p in enumerate(pts2):
            j = (i + 1) % cols
            parts.append(add_cyl(f"{name}u{i}", 0.22, 0.2, 2.6, (p[0], p[1], z2 + 1.3), "red", c, n=10))
            parts.append(add_beam(f"{name}ue{i}", (p[0], p[1], z2 + 2.9), (pts2[j][0], pts2[j][1], z2 + 2.9), 0.34, 0.34, "red", c))
            al = "x" if abs(pts2[j][0] - p[0]) > abs(pts2[j][1] - p[1]) else "y"
            parts += dougong_run(f"{name}ud{i}", c, (p[0], p[1], z2 + 3.2), (pts2[j][0], pts2[j][1], z2 + 3.2),
                                 z2 + 3.2, 2, "glaze", 0.7 * s, al)
        zf = z2 + 3.35
        w_top = w2
    else:
        w_top = w
    roof, info = roof_tube(f"{name}rf", c, w_top, w_top, roof_h, zf, kind="zhanjian",
                           eave=eave, lift=lift, rings=7, mat=roof_mat, ox=cx, oy=cy)
    parts.append(roof)
    tmat = "glaze_d" if roof_mat == "glaze" else "tile_d"
    parts += add_tiles(f"{name}tl", c, info, tmat, strip_w=0.26, gap=0.6)
    parts += roof_ornament(f"{name}or", c, info)
    parts += hip_ridges(f"{name}hr", c, info, tmat)
    return parts

def build_corridor(name, c, pts, z0, w=2.6, col_h=2.9, roof_mat="tile", roofed=True, posts_every=1.7):
    """游廊/木桥:台面+双侧柱(ARRAY)+矮栏(+两坡顶)"""
    pts = [(p[0], p[1], z0) if len(p) == 2 else tuple(p) for p in pts]  # 允许传 2D 点
    parts = []
    for si in range(len(pts) - 1):
        p1, p2 = Vector(pts[si]), Vector(pts[si + 1])
        d = (p2 - p1).length
        ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
        mid = (p1 + p2) / 2
        parts.append(add_box(f"{name}dk{si}", (d + 0.2, w, 0.16), (mid.x, mid.y, z0 + 0.08), "wood", c, rot_z=ang))
        off = Vector((-math.sin(ang), math.cos(ang), 0))
        n = max(2, int(d / posts_every) + 1)
        for side in (1, -1):
            q1 = p1 + off * (w / 2 - 0.18) * side
            q2 = p2 + off * (w / 2 - 0.18) * side
            col = add_cyl(f"{name}c{si}{side}", 0.13, 0.12, col_h, (q1.x, q1.y, z0 + col_h / 2 + 0.16), "red", c, n=8)
            md = col.modifiers.new("arr", "ARRAY")
            md.count = n
            dv = (q2 - q1) / max(n - 1, 1)
            md.use_relative_offset = False
            md.use_constant_offset = True
            md.constant_offset_displace = (dv.x, dv.y, 0.0)
            parts.append(col)
            parts.append(add_beam(f"{name}rl{si}{side}", (q1.x, q1.y, z0 + 0.82), (q2.x, q2.y, z0 + 0.82), 0.08, 0.08, "red", c))
        if roofed:
            zr = z0 + col_h + 0.28
            for s2 in (1, -1):
                e1 = p1 + off * (w / 2 - 0.02) * s2
                e2 = p2 + off * (w / 2 - 0.02) * s2
                em = (e1 + e2) / 2
                rm = (mid.x, mid.y, zr + 0.85)
                parts.append(add_beam(f"{name}rf{si}{s2}", (em.x, em.y, zr + 0.28), rm, d + 0.4, 0.08, roof_mat, c))
            parts.append(add_beam(f"{name}rj{si}", (p1.x, p1.y, zr + 1.22), (p2.x, p2.y, zr + 1.22), 0.28, 0.18, "glaze_d", c))
    return parts

# ================================================================= §1 主台基 + 白玉栏杆
C1 = coll("FS_主台基")
add_prism("FS_主台基_下层", [(-58, -46), (58, -46), (58, 52), (-58, 52)], -1.6, Z_LOW, "marble", C1)
add_prism("FS_主台基_上层", [(-56, -38), (56, -38), (56, 44), (-56, 44)], -0.8, Z_UP, "marble", C1)
balustrade_run("FS_栏下南东", C1, (14, -46), (57, -46), Z_LOW)
balustrade_run("FS_栏下南西", C1, (-57, -46), (-14, -46), Z_LOW)
balustrade_run("FS_栏下东", C1, (58, -46), (58, 52), Z_LOW)
balustrade_run("FS_栏下北", C1, (58, 52), (-58, 52), Z_LOW)
balustrade_run("FS_栏下西", C1, (-58, 52), (-58, -46), Z_LOW)
balustrade_run("FS_栏上南", C1, (-56, -38), (56, -38), Z_UP)
balustrade_run("FS_栏上东", C1, (56, -38), (56, 44), Z_UP)
balustrade_run("FS_栏上北", C1, (56, 44), (-56, 44), Z_UP)
balustrade_run("FS_栏上西", C1, (-56, 44), (-56, -38), Z_UP)
# 上下层间踏道(南缘两座、北缘两座、东西各一)
stairs("FS_阶S30", C1, 30, -38, 6.0, Z_LOW, Z_UP, "S")
stairs("FS_阶S-30", C1, -30, -38, 6.0, Z_LOW, Z_UP, "S")
stairs("FS_阶N30", C1, 30, 44, 6.0, Z_LOW, Z_UP, "N")
stairs("FS_阶N-30", C1, -30, 44, 6.0, Z_LOW, Z_UP, "N")
stairs("FS_阶E", C1, 56, 3, 7.0, Z_LOW, Z_UP, "E")
stairs("FS_阶W", C1, -56, 3, 7.0, Z_LOW, Z_UP, "W")
stairs("FS_阶N0", C1, 0, 52, 7.0, Z_LOW, Z_UP, "N")

# ================================================================= §2 哕鸾殿(单层五楹)
C2 = coll("FS_哕鸾殿")
build_hall("FS_哕鸾殿", C2, 0, -26, Z_UP, bays=5, bay_w=6.6, d=15, storeys=1,
           col_hs=(4.1,), roof_h=4.8, roof_kind="xieshan", roof_mat="glaze",
           ridge_w=9.5, back_lattice=True)
build_corridor("FS_哕鸾廊东", C2, [(17.4, -26, Z_UP), (30, -26, Z_UP), (40, -33, Z_UP), (48, -33, Z_UP)], Z_UP)
build_corridor("FS_哕鸾廊西", C2, [(-17.4, -26, Z_UP), (-30, -26, Z_UP), (-40, -33, Z_UP), (-48, -33, Z_UP)], Z_UP)

# ================================================================= §3 琼华楼 —— 构件级深化(参赛"参数化考据建模"展示核心)
# ------------------------------------------------------------------------------
# 考据条目对照(下方每个构件段均标注条目号):
#  ①《圆明园四十景图咏·方壶胜境》:方壶胜境正殿,二层楼宇,前后各五楹(五开间),
#    北为琼华楼、前曰哕鸾殿,游廊相连;楼阁供奉佛像(千尊级)。
#  ② 高台:高出地面约 3 米、台上约 3000㎡,重檐楼阁游廊相连围合(副阶周匝意象)。
#  ③ 尺寸推定:《清式营造则例》比例——1 营造尺≈0.32m;面阔记载线索"1丈2尺8寸"
#    ≈4.1m 级(定次间);斗口 0.12m≈七等材。QH_DIM 全部为【按清式营造则例推定】,非实测。
#  ④ 彩画:清官式旋子彩画意象(青绿底+金色线条+皮条线/岔口线几何化)。
# 命名:QH_ 前缀;面位码 f=南前檐 / b=北后檐 / e=东山面 / w=西山面;
#   平身科 QH_斗拱f{间}s{朵},柱头科 QH_斗拱f{间}c{柱},格扇 QH_格扇f{间}s{扇}。
# 结构:QH_ 构件不参与组合并(join),逐构件保留为独立节点导出,便于逐构件答辩核对。
# 通高校核:台明顶→上层正脊顶 ≈ 15.2m(构件逐项累加)。任务区间"约13~14m"系
#   "柱高+层间+屋面"粗估,未含额枋/斗拱/平座层;按构件最小组合取紧缩值,总高与
#   旧楼(≈16.9m)相当;位置(0,4)/朝向/与游廊·哕鸾殿关系均不变。
QH_DIM = {
    # --- 平面(推定:明间>次间>梢间递减律;"1丈2尺8寸"≈4.096m 定次间;面阔五间共 20.4m)
    "bay_ming": 4.6, "bay_ci": 4.1, "bay_shao": 3.8,
    "dep_m": 4.8, "dep_s": 4.4,            # 进深三间共 14.0m(推定)
    "lang_bu": 1.5,                         # 廊深一步(推定 ≈4.7 营造尺)
    # --- 立面(推定:檐柱高≈明间面阔×0.9+0.6→取 4.2;上层≈×0.857 取 3.6;台明 0.9)
    "taiming_h": 0.9,
    "col_h1": 4.2, "col_h2": 3.6,
    "col_r1": 0.22, "col_r2": 0.19,         # 柱脚/柱头半径(收分推定)
    "ce_jiao": 0.035,                       # 侧脚(推定 柱高/120)
    "col_r_gold": 0.24,
    "scale2": 0.85,                         # 上层构件系数(考据要求)
    # --- 额枋三件:檐枋/由额垫板/额枋(断面按斗口倍数推定)
    "yanFang_h": 0.28, "daiBan_h": 0.30, "eFang_h": 0.36,
    # --- 斗拱:斗口 0.12(七等材推定),三踩;平身科每开间 4 朵(前后檐)/3 朵(山面)
    "dou_kou": 0.12, "dg_h1": 0.84, "dg_h2": 0.58,
    "dg_per_bay": 4, "dg_per_bay_side": 3, "dg_per_bay2": 2,
    # --- 层间/屋面(举折"檐缓脊陡":z=h·s^1.45,与场景 roof_tube 同律)
    "yaoYan_h": 1.10, "yaoRun_x": 1.10, "yaoRun_y": 0.90,
    "shangYan_h": 2.30,
    "wa_gap1": 0.80, "wa_gap2": 0.85,
    "plate_h": 0.24, "rail_h": 0.82,
    "geShan_w": 0.74,
    "ridge_w": 5.6,                         # 上檐歇山正脊长(推定 ≈ 面阔/3.5)
    "tai_out": 0.80,                        # 台明自檐柱中线外出(下檐出,推定)
}

# ------------------------------------------------------------ QH 合并网格小工厂
def _box_vf(size, loc, rz=0.0, rx=0.0, ry=0.0):
    """box 的 (verts, faces);依次绕 z/x/y 自转后平移(-y 端下垂用 rx>0,+x 端下垂用 ry>0)"""
    sx, sy, sz = size
    v = []
    for z in (-sz / 2, sz / 2):
        for x in (-sx / 2, sx / 2):
            for y in (-sy / 2, sy / 2):
                px, py, pz = x, y, z
                if rz:
                    ca, sa = math.cos(rz), math.sin(rz)
                    px, py = px * ca - py * sa, px * sa + py * ca
                if rx:
                    cb, sb = math.cos(rx), math.sin(rx)
                    py, pz = py * cb - pz * sb, py * sb + pz * cb
                if ry:
                    cc, sc = math.cos(ry), math.sin(ry)
                    px, pz = px * cc + pz * sc, -px * sc + pz * cc
                v.append((loc[0] + px, loc[1] + py, loc[2] + pz))
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (1, 3, 7, 5), (3, 2, 6, 7), (2, 0, 4, 6)]
    return v, f

def _wedge_vf(w, y0, y1, z1, z0):
    """楔形(昂嘴):顶面自 (y0,z1) 斜降至 (y1,z0),共 5 面 8 三角"""
    v = [(-w / 2, y0, z1), (w / 2, y0, z1), (w / 2, y1, z0), (-w / 2, y1, z0),
         (-w / 2, y0, z0), (w / 2, y0, z0)]
    f = [(0, 1, 2, 3), (1, 0, 4, 5), (5, 4, 3, 2), (0, 3, 4), (1, 5, 2)]
    return v, f

def _cyl_vf(r0, r1, h, n, loc, mat="red"):
    """圆柱 chunk(柱身/鼓镜)"""
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
    return (mat, v, f)

def _ngon_vf(r, n, h, loc, mat, axis="y"):
    """薄多边形片(旋花/团龙/圆光/铺首):axis='y' 面朝 ±y;'x' 面朝 ±x"""
    v, f = [], []
    if axis == "y":
        for yy in (loc[1] - h / 2, loc[1] + h / 2):
            for i in range(n):
                a = 2 * math.pi * i / n
                v.append((loc[0] + r * math.cos(a), yy, loc[2] + r * math.sin(a)))
    else:
        for xx in (loc[0] - h / 2, loc[0] + h / 2):
            for i in range(n):
                a = 2 * math.pi * i / n
                v.append((xx, loc[1] + r * math.cos(a), loc[2] + r * math.sin(a)))
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, j + n, i + n))
    f.append(tuple(range(n - 1, -1, -1)))
    f.append(tuple(range(n, 2 * n)))
    return (mat, v, f)

def _prism_xz_vf(poly, y0, y1, mat):
    """XZ 剖面多边形沿 y 拉伸(雀替)"""
    v = [(p[0], y0, p[1]) for p in poly] + [(p[0], y1, p[1]) for p in poly]
    n = len(poly)
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, j + n, i + n))
    return (mat, v, f)

def _merge_rot(chunks, rz, loc):
    """局部 chunk 组绕 z 旋转 rz 后平移 loc(local +y = 面外方向)"""
    ca, sa = math.cos(rz), math.sin(rz)
    out = []
    for mk, vv, ff in chunks:
        v2 = [(loc[0] + x * ca - y * sa, loc[1] + x * sa + y * ca, loc[2] + z) for (x, y, z) in vv]
        out.append((mk, v2, ff))
    return out

FACE_RZ = {"f": math.pi, "b": 0.0, "e": -math.pi / 2, "w": math.pi / 2}

def _merged(name, chunks, c):
    """多材质 chunk 合并为单网格对象(逐构件单节点)"""
    v, f, mats, midx = [], [], [], []
    for mk, vv, ff in chunks:
        if mk not in mats:
            mats.append(mk)
        mi = mats.index(mk)
        base = len(v)
        v += vv
        f += [tuple(i + base for i in fc) for fc in ff]
        midx += [mi] * len(ff)
    name = safe_name(name)
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    c.objects.link(ob)
    for mk in mats:
        ob.data.materials.append(M[mk] if isinstance(mk, str) else mk)
    for idx, p in enumerate(ob.data.polygons):
        p.material_index = midx[idx]
    return ob

# ---------------------------------------------------------------- 构件:斗拱(考据③)
def qh_dougong(name, c, loc, face, L1, s=1.0, zhike=False, layers=3):
    """一朵斗拱(合并单网格;斗口 0.12≈七等材推定,三踩):
       坐斗 + 泥道拱/散斗逐层叠升(三层叠升)+ 顶层平身科出昂(昂嘴斜面楔形)/
       柱头科出桃尖梁头——平身科/柱头科形制区分(考据③)。
       L1=底层拱全长;face 决定朝向,local +y = 出跳朝面外"""
    ch = []
    ch.append(("glaze", *_box_vf((0.36 * s, 0.30 * s, 0.20 * s), (0, 0, 0.10 * s))))   # 坐斗
    zg, Lc = 0.20 * s, L1
    for li in range(layers - 1):                                                        # 拱+散斗 叠升层
        gh = (0.14 if li == 0 else 0.12) * s
        zc = zg + gh / 2 + 0.015 * s
        ch.append(("glaze", *_box_vf((Lc * s, (0.15 - 0.01 * li) * s, gh), (0, 0, zc))))
        for sx in (-1, 1):
            ch.append(("glaze", *_box_vf((0.17 * s, 0.17 * s, 0.10 * s),
                                         (sx * (Lc / 2 - 0.09) * s, 0, zc + gh / 2 + 0.05 * s))))
        zg = zc + gh / 2 + 0.10 * s
        Lc = Lc * 0.80
    gh = 0.13 * s
    zc = zg + gh / 2 + 0.015 * s
    if zhike:                                                                           # 柱头科:桃尖梁头外挑
        ch.append(("glaze", *_box_vf((0.30 * s, 0.95 * s, 0.26 * s), (0, 0.30 * s, zc))))
    else:                                                                               # 平身科:昂+昂嘴斜面
        ch.append(("glaze", *_box_vf((L1 * 0.90 * s, 0.15 * s, gh), (0, 0, zc))))
        wv, wf = _wedge_vf(0.15 * s, 0.14 * s, 0.46 * s, zc + gh / 2, zc - 0.10 * s)
        ch.append(("glaze", wv, wf))
        for sx in (-1, 1):
            ch.append(("glaze", *_box_vf((0.16 * s, 0.16 * s, 0.10 * s),
                                         (sx * L1 * 0.45 * s, 0, zc + gh / 2 + 0.05 * s))))
    return _merged(name, _merge_rot(ch, FACE_RZ[face], loc), c)

# ---------------------------------------------------------------- 构件:隔扇/窗(考据①③)
def qh_gefan(name, c, loc, face, w, h, door=False, win=False):
    """一扇隔扇(合并单网格):边框+抹头+步步锦意象格心(2竖2横棂,门扇加 1 斜棂)
       +绦环板+裙板;win=True 为二层平座格扇窗(无裙板);door=True 加铜铺首(明间开门,考据①)"""
    ch = []
    fw = 0.075
    ch.append(("red", *_box_vf((fw, 0.09, h), (-(w - fw) / 2, 0, h / 2))))    # 左右梃
    ch.append(("red", *_box_vf((fw, 0.09, h), ((w - fw) / 2, 0, h / 2))))
    ch.append(("red", *_box_vf((w, 0.09, fw), (0, 0, h - fw / 2))))           # 上抹头
    ch.append(("red", *_box_vf((w, 0.09, fw), (0, 0, fw / 2))))               # 下抹头
    if win:
        gw, g0, g1 = w - 2 * fw, 0.55 * h, h - fw
        gh = g1 - g0
        for fx in (-gw / 4, gw / 4):                                          # 格心 2 竖棂
            ch.append(("red", *_box_vf((0.042, 0.05, gh), (fx, 0, (g0 + g1) / 2))))
        for fz in (g0 + gh * 0.33, g0 + gh * 0.66):                           # 2 横棂
            ch.append(("red", *_box_vf((gw, 0.05, 0.042), (0, 0, fz))))
    else:
        ch.append(("red", *_box_vf((w, 0.09, fw), (0, 0, 0.60 * h))))         # 中抹头
        gw, g0, g1 = w - 2 * fw, 0.62 * h + fw / 2, h - 1.5 * fw
        gh = g1 - g0
        for fx in (-gw / 4, gw / 4):                                          # 步步锦 2 竖棂
            ch.append(("red", *_box_vf((0.042, 0.05, gh), (fx, 0, (g0 + g1) / 2))))
        for fz in (g0 + gh * 0.33, g0 + gh * 0.66):                           # 2 横棂
            ch.append(("red", *_box_vf((gw, 0.05, 0.042), (0, 0, fz))))
        if door:                                                              # 门扇加 1 斜棂
            dl = math.hypot(gw, gh) * 0.92
            ch.append(("red", *_box_vf((dl, 0.05, 0.042), (0, 0, (g0 + g1) / 2), rz=math.atan2(gh, gw))))
        ch.append(("wood", *_box_vf((w - 2 * fw, 0.07, 0.24), (0, 0, 0.535 * h))))   # 绦环板
        ch.append(("wood", *_box_vf((w - 2 * fw, 0.08, 0.46 * h), (0, 0, 0.28 * h))))  # 裙板
        if door:
            ch.append(_ngon_vf(0.055, 8, 0.03, (0, 0.055, 1.30), "gold"))  # 铺首(考据①)
    return _merged(name, _merge_rot(ch, FACE_RZ[face], loc), c)

# ---------------------------------------------------------------- 构件:柱(考据③)
def qh_column(name, c, x, y, z0, col_h, r0, r1, dx=0.0, dy=0.0):
    """柱(合并单网格):石鼓镜柱础+柱身(收分 r0→r1)+侧脚(柱头内倾 dx/dy)"""
    chu_h = 0.28
    hb = col_h - chu_h
    ch = [("marble", *_box_vf((r0 * 2.9, r0 * 2.9, 0.16), (0, 0, 0.08)))]       # 础盘
    ch.append(_cyl_vf(r0 * 1.14, r0 * 1.14, 0.12, 8, (0, 0, 0.22), "marble"))   # 鼓镜
    ch.append(_cyl_vf(r0, r1, hb, 8, (0, 0, chu_h + hb / 2)))                   # 柱身(收分)
    ob = _merged(name, ch, c)
    for vtx in ob.data.vertices:                                                # 侧脚:柱头内倾(局部坐标)
        if vtx.co.z > col_h - 0.02:
            vtx.co.x += dx
            vtx.co.y += dy
    ob.location = (x, y, z0)
    return ob

# ---------------------------------------------------------------- 构件:平座栏杆(考据②)
def qh_railing(name, c, p1, p2, z0, post_gap=2.1):
    """一段寻杖栏杆:望柱(方柱+云头,ARRAY)+寻杖+盆唇+地袱+瘿项云拱片(考据②副阶周匝)"""
    parts = []
    p1, p2 = Vector((p1[0], p1[1], 0)), Vector((p2[0], p2[1], 0))
    dlen = (p2 - p1).length
    n = max(2, int(round(dlen / post_gap)) + 1)
    ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
    ch = [("marble", *_box_vf((0.24, 0.24, 0.12), (0, 0, 0.06)))]               # 望柱础
    ch.append(("marble", *_box_vf((0.17, 0.17, 0.56), (0, 0, 0.40))))           # 望柱身
    ch.append(("marble", *_box_vf((0.22, 0.19, 0.14), (0, 0, 0.75))))           # 云头
    unit = _merged(f"{name}望柱", ch, c)
    unit.rotation_euler = (0, 0, ang)
    unit.location = (p1.x, p1.y, z0)
    md = unit.modifiers.new("arr", "ARRAY")
    md.count = n
    md.use_relative_offset = False
    md.use_constant_offset = True
    md.constant_offset_displace = (dlen / max(n - 1, 1), 0.0, 0.0)              # 局部 +x 即走向
    parts.append(unit)
    mid = (p1 + p2) / 2
    zxun = add_cyl(f"{name}寻杖", 0.075, 0.075, dlen, (mid.x, mid.y, z0 + 0.74), "marble", c, n=8)
    zxun.rotation_euler = (math.pi / 2, 0.0, ang + math.pi / 2)                 # 圆寻杖顺走向
    parts.append(zxun)
    parts.append(add_box(f"{name}盆唇", (dlen, 0.10, 0.09), (mid.x, mid.y, z0 + 0.44), "marble", c, rot_z=ang))
    parts.append(add_box(f"{name}地袱", (dlen, 0.12, 0.08), (mid.x, mid.y, z0 + 0.06), "marble", c, rot_z=ang))
    nspan = max(1, n - 1)
    dv = (p2 - p1) / nspan
    ch = []
    for k in range(nspan):
        px = mid.x + dv.x * (k + 0.5 - nspan / 2)
        py = mid.y + dv.y * (k + 0.5 - nspan / 2)
        ch.append(_ngon_vf(0.09, 8, 0.05, (px, py, z0 + 0.58), "marble"))       # 瘿项云拱片
    parts.append(_merged(f"{name}云拱", ch, c))
    return parts

# ---------------------------------------------------------------- 构件:腰檐环壳(考据①②)
def qh_ring_roof(name, c, cx, cy, z0, w, d, h, top_w, top_d, eave=0.85, lift=0.45,
                 rings=5, mat="glaze"):
    """重檐腰檐:截顶四坡环壳,外沿(檐口起翘)→内沿(平座外沿);举折 z=h·s^1.45;
       返回兼容 add_tiles 的 info(.kind='wudian')"""
    hw0, hd0 = w / 2 + eave, d / 2 + eave
    tw, td = top_w / 2, top_d / 2
    rows, zs, hs = [], [], []
    for i in range(rings + 1):
        s = i / rings
        t = s ** 0.92
        wi = hw0 * (1 - t) + tw * t
        di = hd0 * (1 - t) + td * t
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
            v.append((x + cx, y + cy, z0 + z + lift * corner * k))
    for ri in range(rings):
        for k2 in range(_P):
            a = ri * _P + k2
            b = ri * _P + (k2 + 1) % _P
            f.append((a, b, b + _P, a + _P))
    top = rings * _P
    f.append(tuple(range(top, top + _P)))
    ob = _obj(name, v, f, mat, c, smooth=True)
    return ob, {"kind": "wudian", "hw0": hw0, "hd0": hd0, "ridge_w": top_w, "h": h,
                "rows": rows, "zs": zs, "hs": hs, "rings": rings, "z0": z0,
                "ox": cx, "oy": cy}

def qh_tiles(name, c, info, mat, strip_w=0.26, gap=0.80, margin=0.24):
    """截顶四坡瓦垄(前后坡+左右坡;margin 较 add_tiles 更贴檐口)"""
    zs, hs, z0 = info["zs"], info["hs"], info["z0"]
    parts = []
    xs, x = [], -info["hw0"] + margin
    while x <= info["hw0"] - margin:
        xs.append(x); x += gap
    for xi in xs:
        for side in (1, -1):
            vv, ff, m = [], [], 0
            for ri in range(info["rings"] + 1):
                hw, hd = hs[ri]
                if abs(xi) > hw - margin * 0.6:
                    break
                yb = hd * side + info["oy"]
                zz = z0 + zs[ri] + 0.04
                vv += [(xi + info["ox"] - strip_w / 2, yb, zz), (xi + info["ox"] + strip_w / 2, yb, zz)]
                m += 1
            for i in range(m - 1):
                a = 2 * i
                ff.append((a, a + 1, a + 3, a + 2) if side > 0 else (a + 1, a, a + 2, a + 3))
            if m > 1:
                parts.append(_obj(f"{name}t{xi:.0f}_{side}", vv, ff, mat, c))
    ys, y = [], -info["hd0"] + margin
    while y <= info["hd0"] - margin:
        ys.append(y); y += gap
    for yi in ys:
        for side in (1, -1):
            vv, ff, m = [], [], 0
            for ri in range(info["rings"] + 1):
                hw, hd = hs[ri]
                if abs(yi) > hd - margin * 0.6:
                    break
                xb = hw * side + info["ox"]
                zz = z0 + zs[ri] + 0.04
                vv += [(xb, yi + info["oy"] - strip_w / 2, zz), (xb, yi + info["oy"] + strip_w / 2, zz)]
                m += 1
            for i in range(m - 1):
                a = 2 * i
                ff.append((a, a + 1, a + 3, a + 2))
            if m > 1:
                parts.append(_obj(f"{name}ts{yi:.0f}_{side}", vv, ff, mat, c))
    return parts

# ---------------------------------------------------------------- 构件:旋子彩画带(考据④)
def qh_caihua(name, c, loc, bw, face, zc_ef, h_ef, zc_db, h_db, simple=False):
    """一整间旋子彩画意象(合并多材质,考据④):箍头(青)+皮条线(金)+藻头(绿)
       +旋花(金圈)+枋心(青)+岔口线(金)+由额垫板青底;simple=True 为上层简化版"""
    ch = []
    guan = 0.30                                                  # 箍头宽
    zao = min(0.16 * bw, 0.66)                                   # 藻头宽
    fxw = bw - 2 * guan - 2 * zao                                # 枋心宽
    half = bw / 2
    for sx in (-1, 1):
        ch.append(("cai_blue", *_box_vf((guan, 0.03, h_ef), (sx * (half - guan / 2), 0, zc_ef))))
        ch.append(("cai_gold", *_box_vf((0.03, 0.035, h_ef), (sx * (half - guan - 0.035), 0, zc_ef))))  # 皮条线
        if not simple:
            ch.append(("cai_green", *_box_vf((zao, 0.03, h_ef * 0.92),
                                             (sx * (half - guan - zao / 2), 0, zc_ef))))
            ch.append(_ngon_vf(0.105, 8, 0.03,
                               (sx * (half - guan - zao / 2), 0.02, zc_ef), "cai_gold"))
    ch.append(("cai_blue", *_box_vf((fxw, 0.03, h_ef * 0.78), (0, 0, zc_ef))))          # 枋心
    ch.append(("cai_gold", *_box_vf((fxw, 0.035, 0.03), (0, 0, zc_ef + h_ef * 0.42))))  # 岔口线上
    ch.append(("cai_gold", *_box_vf((fxw, 0.035, 0.03), (0, 0, zc_ef - h_ef * 0.42))))  # 岔口线下
    ch.append(("cai_blue", *_box_vf((bw - 0.2, 0.03, h_db * 0.9), (0, 0, zc_db))))      # 垫板青底
    return _merged(name, _merge_rot(ch, FACE_RZ[face], loc), c)

# ================================================================= 琼华楼主装配(考据①②)
def build_qionghua(cq):
    d = QH_DIM
    # --- 柱位/尺寸推演(全部自 QH_DIM 取值;坐标:原点=主台基中心,南 -Y)
    xw = [d["bay_shao"], d["bay_ci"], d["bay_ming"], d["bay_ci"], d["bay_shao"]]
    W = sum(xw)                                                     # 面阔 20.4
    xs = []
    x = -W / 2
    for w_ in xw:
        xs.append(x); x += w_
    xs.append(x)                                                    # 檐柱列 x(6 柱位)
    dw = [d["dep_m"], d["dep_s"], d["dep_m"]]
    D = sum(dw)                                                     # 进深 14.0
    ydep = []
    y = -D / 2
    for w_ in dw:
        ydep.append(y); y += w_
    ydep.append(y)                                                  # 进深柱线 y(4 线)
    yf, yb = -D / 2, D / 2
    gsc = (W - 2 * d["lang_bu"]) / W                                # 金柱环缩放(廊深一步)
    xsg = [v * gsc for v in xs]
    ysf, ysb = yf + d["lang_bu"], yb - d["lang_bu"]
    ysg_mid = [v * gsc for v in ydep[1:3]]
    s2 = d["scale2"]
    xs2 = [v * s2 for v in xs]
    y2f, y2b = yf * s2, yb * s2
    y2mid = [v * s2 for v in ydep[1:3]]
    cx, cy = 0.0, 4.0                                               # 与旧 FS_琼华楼 同位同朝向
    zt = Z_UP + d["taiming_h"]                                      # 台明顶 2.9(一层地面)
    hw_tai = W / 2 + d["tai_out"]                                   # 台基半宽 11.0
    hd_tai = D / 2 + d["tai_out"]                                   # 台基半深 7.8
    eave1, eave2 = 0.85, 0.75                                       # 下/上檐出檐(推定)
    z_pillar_top = zt + d["col_h1"]                                 # 7.10
    z_yf1 = z_pillar_top
    z_dai1 = z_yf1 + d["yanFang_h"]
    z_ef1 = z_dai1 + d["daiBan_h"]
    z_ef1t = z_ef1 + d["eFang_h"]                                   # 额枋顶 8.04
    z_dg1 = z_ef1t                                                  # 下檐斗拱底
    z_p1 = z_dg1 + 0.88                                             # 下檐檩心
    z_yao0 = z_dg1 + 0.82                                           # 腰檐外沿
    z_yao1 = z_yao0 + d["yaoYan_h"]                                 # 腰檐内沿=平座板底
    top_hw = W / 2 + eave1 - d["yaoRun_x"]                          # 腰檐内沿半宽 9.95
    top_hd = D / 2 + eave1 - d["yaoRun_y"]
    z_plate2 = z_yao1 + d["plate_h"]                                # 平座面(二层地面)
    hw_pl, hd_pl = top_hw + 0.10, top_hd + 0.10                     # 平座板半宽/半深
    z_pillar2t = z_plate2 + d["col_h2"]                             # 上柱顶
    z_yf2 = z_pillar2t
    z_dai2 = z_yf2 + d["yanFang_h"] * s2
    z_ef2 = z_dai2 + d["daiBan_h"] * s2
    z_ef2t = z_ef2 + d["eFang_h"] * s2                              # 上额枋顶
    z_dg2 = z_ef2t                                                  # 上檐斗拱底
    z_p2 = z_dg2 + 0.62                                             # 上檐檩心
    z_rf2 = z_p2 + 0.11                                             # 上檐屋面外沿
    hw2 = W * s2 / 2 + eave2
    hd2 = D * s2 / 2 + eave2
    C = cq

    # --- ① 台基:须弥座五层线脚(圭角/下枋/下枭/束腰/上枋;各层立面即陡板)(考据①③)
    for nm, w_, d_, h_, z_ in (("圭角", 2 * hw_tai + 0.12, 2 * hd_tai + 0.12, 0.12, Z_UP),
                               ("下枋", 2 * hw_tai + 0.04, 2 * hd_tai + 0.04, 0.26, Z_UP + 0.12),
                               ("下枭", 2 * hw_tai + 0.10, 2 * hd_tai + 0.10, 0.14, Z_UP + 0.38),
                               ("束腰", 2 * hw_tai - 0.08, 2 * hd_tai - 0.08, 0.16, Z_UP + 0.52),
                               ("上枋", 2 * hw_tai + 0.10, 2 * hd_tai + 0.10, 0.22, Z_UP + 0.68)):
        b = add_box(f"QH_须弥座{nm}", (w_, d_, h_), (cx, cy, z_ + h_ / 2), "marble", C)
        bv = b.modifiers.new("bev", "BEVEL")
        bv.width = 0.04
        bv.segments = 2
    stairs("QH_踏道", C, cx, cy - hd_tai, 4.6, Z_UP, zt, "S")        # 前踏道(垂带+踏步,考据①)
    stairs("QH_踏道N", C, cx, cy + hd_tai, 4.2, Z_UP, zt, "N")       # 后踏道(接北游廊,考据②)
    ang_yu = math.atan2(0.86, 1.45)
    _merged("QH_御路石", [                                            # 御路石:云龙意象几何(金线,考据①)
        ("marble", *_box_vf((1.9, 1.78, 0.10), (cx, cy - hd_tai - 0.77, 2.49), rx=ang_yu)),
        ("cai_gold", *_box_vf((0.10, 0.9, 0.035), (cx - 0.55, cy - hd_tai - 0.55, 2.565), rx=ang_yu)),
        ("cai_gold", *_box_vf((0.10, 0.7, 0.035), (cx + 0.55, cy - hd_tai - 0.75, 2.565), rx=ang_yu)),
        ("cai_gold", *_box_vf((0.8, 0.10, 0.035), (cx, cy - hd_tai - 0.95, 2.505), rx=ang_yu)),
        _ngon_vf(0.11, 8, 0.035, (cx, cy - hd_tai - 0.60, 2.60), "cai_gold"),
    ], C)

    # --- ①③ 柱网:檐柱一围(16)+金柱一围(16,廊深一步)+上层檐柱一围(16,0.85 系数)(考据①③)
    cej = d["ce_jiao"]
    for i, x_ in enumerate(xs):
        qh_column(f"QH_檐柱f{i}", C, x_, yf, zt, d["col_h1"], d["col_r1"], d["col_r2"], 0, cej)
        qh_column(f"QH_檐柱b{i}", C, x_, yb, zt, d["col_h1"], d["col_r1"], d["col_r2"], 0, -cej)
        qh_column(f"QH_金柱f{i}", C, xsg[i], ysf, zt, 5.14, d["col_r_gold"], d["col_r_gold"] - 0.03)
        qh_column(f"QH_金柱b{i}", C, xsg[i], ysb, zt, 5.14, d["col_r_gold"], d["col_r_gold"] - 0.03)
    for i, yy in enumerate(ysg_mid):
        qh_column(f"QH_金柱e{i}", C, xsg[-1], yy, zt, 5.14, d["col_r_gold"], d["col_r_gold"] - 0.03)
        qh_column(f"QH_金柱w{i}", C, xsg[0], yy, zt, 5.14, d["col_r_gold"], d["col_r_gold"] - 0.03)
    qh_column("QH_檐柱e1", C, xs[-1], ydep[1], zt, d["col_h1"], d["col_r1"], d["col_r2"], -cej, 0)
    qh_column("QH_檐柱e2", C, xs[-1], ydep[2], zt, d["col_h1"], d["col_r1"], d["col_r2"], -cej, 0)
    qh_column("QH_檐柱w1", C, xs[0], ydep[1], zt, d["col_h1"], d["col_r1"], d["col_r2"], cej, 0)
    qh_column("QH_檐柱w2", C, xs[0], ydep[2], zt, d["col_h1"], d["col_r1"], d["col_r2"], cej, 0)
    qh_column("QH_上檐柱e1", C, xs2[-1], y2mid[0], z_plate2, d["col_h2"], d["col_r1"] * s2 + 0.02,
              d["col_r2"] * s2 + 0.02, -cej * 0.8, 0)
    qh_column("QH_上檐柱e2", C, xs2[-1], y2mid[1], z_plate2, d["col_h2"], d["col_r1"] * s2 + 0.02,
              d["col_r2"] * s2 + 0.02, -cej * 0.8, 0)
    qh_column("QH_上檐柱w1", C, xs2[0], y2mid[0], z_plate2, d["col_h2"], d["col_r1"] * s2 + 0.02,
              d["col_r2"] * s2 + 0.02, cej * 0.8, 0)
    qh_column("QH_上檐柱w2", C, xs2[0], y2mid[1], z_plate2, d["col_h2"], d["col_r1"] * s2 + 0.02,
              d["col_r2"] * s2 + 0.02, cej * 0.8, 0)
    for i, x_ in enumerate(xs2):
        qh_column(f"QH_上檐柱f{i}", C, x_, y2f, z_plate2, d["col_h2"], d["col_r1"] * s2 + 0.02,
                  d["col_r2"] * s2 + 0.02, 0, cej * 0.8)
        qh_column(f"QH_上檐柱b{i}", C, x_, y2b, z_plate2, d["col_h2"], d["col_r1"] * s2 + 0.02,
                  d["col_r2"] * s2 + 0.02, 0, -cej * 0.8)

    # --- ③ 额枋三件(檐枋/由额垫板/额枋,四周围合,上下层各一围)+金栿+走马板(考据③)
    for face, yy in (("f", yf), ("b", yb)):
        add_box(f"QH_檐枋{face}", (W + 0.4, 0.42, d["yanFang_h"]), (cx, yy, z_yf1 + d["yanFang_h"] / 2), "red", C)
        add_box(f"QH_由额垫板{face}", (W + 0.4, 0.30, d["daiBan_h"]), (cx, yy, z_dai1 + d["daiBan_h"] / 2), "red", C)
        add_box(f"QH_额枋{face}", (W + 0.4, 0.50, d["eFang_h"]), (cx, yy, z_ef1 + d["eFang_h"] / 2), "red", C)
        add_box(f"QH_檐枋{face}2", (W * s2 + 0.4, 0.38, d["yanFang_h"] * s2),
                (cx, yy * s2, z_yf2 + d["yanFang_h"] * s2 / 2), "red", C)
        add_box(f"QH_由额垫板{face}2", (W * s2 + 0.4, 0.26, d["daiBan_h"] * s2),
                (cx, yy * s2, z_dai2 + d["daiBan_h"] * s2 / 2), "red", C)
        add_box(f"QH_额枋{face}2", (W * s2 + 0.4, 0.44, d["eFang_h"] * s2),
                (cx, yy * s2, z_ef2 + d["eFang_h"] * s2 / 2), "red", C)
    for face, xx in (("e", xs[-1]), ("w", xs[0])):
        add_box(f"QH_檐枋{face}", (0.42, D + 0.4, d["yanFang_h"]), (xx, cy, z_yf1 + d["yanFang_h"] / 2), "red", C)
        add_box(f"QH_由额垫板{face}", (0.30, D + 0.4, d["daiBan_h"]), (xx, cy, z_dai1 + d["daiBan_h"] / 2), "red", C)
        add_box(f"QH_额枋{face}", (0.50, D + 0.4, d["eFang_h"]), (xx, cy, z_ef1 + d["eFang_h"] / 2), "red", C)
        add_box(f"QH_檐枋{face}2", (0.38, D * s2 + 0.4, d["yanFang_h"] * s2),
                (xx * s2, cy, z_yf2 + d["yanFang_h"] * s2 / 2), "red", C)
        add_box(f"QH_由额垫板{face}2", (0.26, D * s2 + 0.4, d["daiBan_h"] * s2),
                (xx * s2, cy, z_dai2 + d["daiBan_h"] * s2 / 2), "red", C)
        add_box(f"QH_额枋{face}2", (0.44, D * s2 + 0.4, d["eFang_h"] * s2),
                (xx * s2, cy, z_ef2 + d["eFang_h"] * s2 / 2), "red", C)
    for yy in (ysf, ysb):                                            # 金柱间大梁(承平座,内檐可见,考据③)
        add_box("QH_金栿", (2 * xsg[-1] + 0.5, 0.42, 0.42), (cx, yy, zt + 5.14 - 0.10), "wood", C)
    for xx in (xsg[-1], xsg[0]):
        add_box("QH_金栿", (0.42, 2 * ysb + 0.5, 0.42), (xx, cy, zt + 5.14 - 0.10), "wood", C)
    for yy in (ysf, ysb):                                            # 走马板(格扇上段封板)
        add_box("QH_走马板", (2 * xsg[-1], 0.12, 1.16), (cx, yy, zt + 4.55), "red", C)

    # --- ③ 雀替(弧形轮廓+卷草曲线意象,柱头两侧;考据③)
    ktr = [(0.0, 0.26), (0.72, 0.26), (0.72, 0.16), (0.50, 0.06), (0.24, -0.01), (0.0, -0.04)]
    for i in range(1, 5):                                            # 明次梢间柱:两侧各一
        for sx in (-1, 1):
            px0 = xs[i] + sx * (d["col_r1"] + 0.02)
            poly = [(px0 + sx * u, z_pillar_top + v) for (u, v) in ktr]
            _merged(f"QH_雀替f{i}_{sx}", [_prism_xz_vf(poly, yf - 0.27, yf + 0.05, "glaze")], C)
            _merged(f"QH_雀替b{i}_{sx}", [_prism_xz_vf(poly, yb - 0.05, yb + 0.27, "glaze")], C)
    for i, sx in ((0, 1), (5, -1)):                                  # 角柱:仅向内一侧
        px0 = xs[i] + sx * (d["col_r1"] + 0.02)
        poly = [(px0 + sx * u, z_pillar_top + v) for (u, v) in ktr]
        _merged(f"QH_雀替f{i}_{sx}", [_prism_xz_vf(poly, yf - 0.27, yf + 0.05, "glaze")], C)
        _merged(f"QH_雀替b{i}_{sx}", [_prism_xz_vf(poly, yb - 0.05, yb + 0.27, "glaze")], C)
    for j, yy in enumerate(ydep[1:3], start=1):                      # 山面柱
        for sy in (-1, 1):
            poly = [(yy + sy * u, z_pillar_top + v) for (u, v) in ktr]
            _merged(f"QH_雀替e{j}_{sy}", [_prism_xz_vf(poly, xs[-1] + 0.05, xs[-1] + 0.27, "glaze")], C)
            _merged(f"QH_雀替w{j}_{sy}", [_prism_xz_vf(poly, xs[0] - 0.27, xs[0] - 0.05, "glaze")], C)

    # --- ③ 斗拱:平身科每开间 4 朵(前后檐)/3 朵(山面)+柱头科每柱 1 朵;上檐 0.85 系数(考据③)
    bw = [d["bay_shao"], d["bay_ci"], d["bay_ming"], d["bay_ci"], d["bay_shao"]]
    for face, yy, xf in (("f", yf - 0.02, xs), ("b", yb + 0.02, xs)):
        for b in range(5):
            L1 = bw[b] / (d["dg_per_bay"] + 1) - 0.14
            for k in range(d["dg_per_bay"]):
                px = xf[b] + bw[b] * (k + 1) / (d["dg_per_bay"] + 1)
                qh_dougong(f"QH_斗拱{face}{b}s{k}", C, (px, yy, z_dg1), face, L1, 1.0, False, 3)
        for i in range(6):
            L1 = min(bw[max(0, i - 1)], bw[min(4, i)]) / (d["dg_per_bay"] + 1) - 0.10
            qh_dougong(f"QH_斗拱{face}{i}c", C, (xf[i], yy, z_dg1), face, L1, 1.0, True, 3)
        for b in range(5):
            L1 = bw[b] * s2 / (d["dg_per_bay2"] + 1) - 0.12
            for k in range(d["dg_per_bay2"]):
                px = xf[b] * s2 + bw[b] * s2 * (k + 1) / (d["dg_per_bay2"] + 1)
                qh_dougong(f"QH_斗拱{face}{b}s{k}2", C, (px, yy * s2, z_dg2), face, L1, 0.85, False, 2)
        for i in range(6):
            L1 = min(bw[max(0, i - 1)], bw[min(4, i)]) * s2 / (d["dg_per_bay2"] + 1) - 0.09
            qh_dougong(f"QH_斗拱{face}{i}c2", C, (xf[i] * s2, yy * s2, z_dg2), face, L1, 0.85, True, 2)
    dw3 = [d["dep_m"], d["dep_s"], d["dep_m"]]
    for face, xx, yff in (("e", xs[-1] + 0.02, ydep), ("w", xs[0] - 0.02, ydep)):
        for b in range(3):
            L1 = dw3[b] / (d["dg_per_bay_side"] + 1) - 0.14
            for k in range(d["dg_per_bay_side"]):
                py = yff[b] + dw3[b] * (k + 1) / (d["dg_per_bay_side"] + 1)
                qh_dougong(f"QH_斗拱{face}{b}s{k}", C, (xx, py, z_dg1), face, L1, 1.0, False, 3)
        for i in range(4):
            L1 = dw3[max(0, i - 1)] / (d["dg_per_bay_side"] + 1) - 0.10
            qh_dougong(f"QH_斗拱{face}{i}c", C, (xx, yff[i], z_dg1), face, L1, 1.0, True, 3)

    # --- ③ 檐檩(圆檩四围,上下层)+椽望(檐口可见椽头,顺势下斜)+翼角翘椽(考据①③)
    for face, yy in (("f", yf), ("b", yb)):
        add_cyl(f"QH_檐檩{face}", 0.155, 0.155, W + 0.8, (cx, yy, z_p1), "wood", C, n=8)
        add_cyl(f"QH_檐檩{face}2", 0.13, 0.13, W * s2 + 0.8, (cx, yy * s2, z_p2), "wood", C, n=8)
    for face, xx in (("e", xs[-1]), ("w", xs[0])):
        add_cyl(f"QH_檐檩{face}", 0.155, 0.155, D + 0.8, (xx, cy, z_p1), "wood", C, n=8)
        add_cyl(f"QH_檐檩{face}2", 0.13, 0.13, D * s2 + 0.8, (xx * s2, cy, z_p2), "wood", C, n=8)
    chf, chb, che, chw = [], [], [], []
    rx1 = math.atan2(0.19, 0.92)
    x = -W / 2 + 0.20
    while x <= W / 2 - 0.20:                                         # 下檐前后坡椽(椽头出檐口)
        chf.append(("wood", *_box_vf((0.10, 1.0, 0.085), (x, yf - 0.46, z_p1 - 0.10), rx=rx1)))
        chb.append(("wood", *_box_vf((0.10, 1.0, 0.085), (x, yb + 0.46, z_p1 - 0.10), rx=-rx1)))
        x += 0.50
    rx2 = math.atan2(0.12, 0.78)
    x = -W * s2 / 2 + 0.20
    while x <= W * s2 / 2 - 0.20:                                    # 上檐前后坡椽
        chf.append(("wood", *_box_vf((0.09, 0.85, 0.075), (x, y2f - 0.40, z_p2 - 0.08), rx=rx2)))
        chb.append(("wood", *_box_vf((0.09, 0.85, 0.075), (x, y2b + 0.40, z_p2 - 0.08), rx=-rx2)))
        x += 0.55
    ry1 = math.atan2(0.19, 0.85)
    yy = yf + 1.0
    while yy <= yb - 0.9:                                            # 下檐山面椽
        che.append(("wood", *_box_vf((1.0, 0.10, 0.085), (xs[-1] + 0.46, yy, z_p1 - 0.10), ry=ry1)))
        chw.append(("wood", *_box_vf((1.0, 0.10, 0.085), (xs[0] - 0.46, yy, z_p1 - 0.10), ry=-ry1)))
        yy += 0.60
    _merged("QH_椽f", chf, C)
    _merged("QH_椽b", chb, C)
    _merged("QH_椽e", che, C)
    _merged("QH_椽w", chw, C)
    wing = []                                                        # 翼角翘椽(角部扇排,起翘意象,考据①)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(5):
                th = (math.pi / 2) * (0.20 + 0.16 * k)
                ddx, ddy = sx * math.sin(th), sy * math.cos(th)
                wing.append(("wood", *_box_vf((0.10, 1.15, 0.085),
                                              (sx * (W / 2 + 0.10) + ddx * 0.30, sy * (D / 2 + 0.10) + ddy * 0.30, z_p1 - 0.06),
                                              rz=math.atan2(ddy, ddx) - math.pi / 2)))
    _merged("QH_翼角椽", wing, C)

    # --- ④ 檐下旋子彩画带(前后檐额枋+由额垫板面;山面从略;上层简化)(考据④)
    for face, yy, xf in (("f", yf - 0.28, xs), ("b", yb + 0.28, xs)):
        for b in range(5):
            px = (xf[b] + xf[b + 1]) / 2
            qh_caihua(f"QH_彩画{face}{b}", C, (px, yy, 0), bw[b], face,
                      z_ef1 + d["eFang_h"] / 2, d["eFang_h"],
                      z_dai1 + d["daiBan_h"] / 2, d["daiBan_h"])
    for face, yy, xf in (("f", yf * s2 - 0.26, xs), ("b", yb * s2 + 0.26, xs)):
        for b in range(5):
            px = (xf[b] + xf[b + 1]) / 2 * s2
            qh_caihua(f"QH_彩画{face}{b}2", C, (px, yy, 0), bw[b] * s2, face,
                      z_ef2 + d["eFang_h"] * s2 / 2, d["eFang_h"] * s2,
                      z_dai2 + d["daiBan_h"] * s2 / 2, d["daiBan_h"] * s2, simple=True)

    # --- ① 格扇门窗:明间开门(中两扇虚开),次梢间各 4 扇;步步锦格心(考据①③)
    for face, yy, xfl in (("f", ysf, xsg), ("b", ysb, xsg)):
        for b in range(5):
            bwg = xfl[b + 1] - xfl[b]
            n = 6 if b == 2 else 4
            fw2 = bwg / n
            for k in range(n):
                if b == 2 and k in (2, 3):
                    continue                                          # 明间中两扇虚开(开门意象)
                nmw = "门扇" if b == 2 else "格扇"
                qh_gefan(f"QH_{nmw}{face}{b}s{k}", C,
                         (xfl[b] + fw2 * (k + 0.5), yy, zt + 0.12), face, fw2 - 0.05, 3.85,
                         door=(b == 2))
    for face, xx, yfl in (("e", xsg[-1], [ysf] + ysg_mid + [ysb]), ("w", xsg[0], [ysf] + ysg_mid + [ysb])):
        for b in range(3):                                            # 山面墙板(金柱线,考据③山墙意象)
            bwg = yfl[b + 1] - yfl[b]
            add_box(f"QH_墙板{face}{b}", (0.16, bwg - 0.3, 3.9),
                    (xx, (yfl[b] + yfl[b + 1]) / 2, zt + 0.12 + 1.95), "wood", C)

    # --- ② 腰檐(截顶四坡环壳)+瓦垄+平座楼板+寻杖栏杆(副阶周匝,考据①②)
    yao, yinfo = qh_ring_roof("QH_腰檐", C, cx, cy, z_yao0, W, D, d["yaoYan_h"],
                              2 * top_hw, 2 * top_hd, eave=eave1, lift=0.45, rings=5, mat="glaze")
    qh_tiles("QH_腰檐瓦", C, yinfo, "glaze_d", gap=d["wa_gap1"])
    add_box("QH_平座楼板", (2 * hw_pl, 2 * hd_pl, d["plate_h"]), (cx, cy, z_yao1 + d["plate_h"] / 2), "marble", C)
    for face, yy in (("f", -hd_pl + 0.15), ("b", hd_pl - 0.15)):
        qh_railing(f"QH_栏杆{face}", C, (cx - hw_pl + 0.15, cy + yy), (cx + hw_pl - 0.15, cy + yy), z_plate2)
    for face, xx in (("e", hw_pl - 0.15), ("w", -hw_pl + 0.15)):
        qh_railing(f"QH_栏杆{face}", C, (cx + xx, cy - hd_pl + 0.15), (cx + xx, cy + hd_pl - 0.15), z_plate2)

    # --- ② 上层格扇窗(0.85 系数;槛墙+步步锦格心)+山面墙板(考据②)
    for face, yy, xfl in (("f", y2f, xs2), ("b", y2b, xs2)):
        for b in range(5):
            bwg = xfl[b + 1] - xfl[b]
            add_box(f"QH_槛墙{face}{b}", (bwg - 0.1, 0.14, 0.85),
                    ((xfl[b] + xfl[b + 1]) / 2, yy, z_plate2 + 0.425), "red", C)
            fw2 = (bwg - 0.1) / 4
            for k in range(4):
                qh_gefan(f"QH_格扇窗{face}{b}s{k}", C,
                         (xfl[b] + 0.05 + fw2 * (k + 0.5), yy, z_plate2 + 0.85), face, fw2 - 0.06, 2.45, win=True)
    for face, xx, yfl in (("e", xs2[-1], [y2f] + y2mid + [y2b]), ("w", xs2[0], [y2f] + y2mid + [y2b])):
        for b in range(3):
            bwg = yfl[b + 1] - yfl[b]
            add_box(f"QH_墙板{face}{b}2", (0.14, bwg - 0.3, 3.3),
                    (xx, (yfl[b] + yfl[b + 1]) / 2, z_plate2 + 1.65), "wood", C)

    # --- ① 重檐歇山顶:上檐屋面(举折+起翘)+瓦垄+正脊/鸱吻(吻锁/吻钉)/宝顶+垂脊/戗脊/山花(考据①③)
    rf, rinfo = roof_tube("QH_上檐屋面", C, W * s2, D * s2, d["shangYan_h"], z_rf2,
                          kind="xieshan", eave=eave2, lift=0.85, ridge_w=d["ridge_w"],
                          rings=7, mat="glaze", ox=cx, oy=cy)
    add_tiles("QH_上檐瓦", C, rinfo, "glaze_d", strip_w=0.26, gap=d["wa_gap2"])
    zr = z_rf2 + d["shangYan_h"]
    add_box("QH_正脊", (d["ridge_w"] + 0.5, 0.42, 0.38), (cx, cy, zr + 0.19), "gold", C)
    for sx in (-1, 1):
        xe = cx + sx * (d["ridge_w"] / 2 + 0.24)
        add_box(f"QH_鸱吻{sx}", (0.44, 0.50, 0.78), (xe, cy, zr + 0.55), "gold", C)
        add_box(f"QH_吻锁{sx}", (0.18, 0.30, 0.16), (cx + sx * (d["ridge_w"] / 2 + 0.02), cy, zr + 0.42), "gold", C)
        add_cyl(f"QH_吻钉{sx}", 0.045, 0.03, 0.5, (xe, cy, zr + 1.02), "gold", C, n=6)
    add_cyl("QH_宝顶座", 0.17, 0.14, 0.20, (cx, cy, zr + 0.28), "gold", C, n=8)
    add_ico("QH_宝顶珠", 0.20, (cx, cy, zr + 0.58), (1, 1, 1.15), 1, "gold", C)
    add_cyl("QH_宝顶焰", 0.03, 0.0, 0.40, (cx, cy, zr + 0.98), "gold", C, n=6, smooth=False)
    hwg, hdg = rinfo["hs"][int(rinfo["rings"] * 0.58)]
    zg = z_rf2 + d["shangYan_h"] * (0.58 ** 1.45)
    for sx in (-1, 1):
        v = [(cx + sx * hwg, cy - hdg, zg), (cx + sx * hwg, cy + hdg, zg), (cx + sx * d["ridge_w"] / 2, cy, zr)]
        _obj(f"QH_山花{sx}", v, [(0, 1, 2)], "wood", C)
        add_beam(f"QH_博缝{sx}a", v[0], v[2], 0.24, 0.16, "glaze_d", C)
        add_beam(f"QH_博缝{sx}b", v[1], v[2], 0.24, 0.16, "glaze_d", C)
        _merged(f"QH_圆光{sx}", [_ngon_vf(0.42, 10, 0.07, (cx + sx * (hwg + 0.02), cy, zg + 0.45), "gold", axis="x")], C)
        add_beam(f"QH_垂脊{sx}", (cx + sx * d["ridge_w"] / 2, cy, zr + 0.05),
                 (cx + sx * hwg * 0.97, cy, zg + 0.10), 0.24, 0.18, "glaze_d", C)
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_beam(f"QH_戗脊{sx}{sy}", (cx + sx * hwg * 0.98, cy + sy * hdg * 0.98, zg + 0.05),
                     (cx + sx * hw2 * 0.94, cy + sy * hd2 * 0.94, z_rf2 + 0.22), 0.20, 0.15, "glaze_d", C)

    # --- ① 内檐:井字天花+团龙金片+楹联(南面透过格扇可见);明间佛坛/供桌(供佛,考据①)
    ch = []
    for yy in (-4.4, -2.2, 0.0, 2.2, 4.4):
        ch.append(("wood", *_box_vf((2 * xsg[-1] - 0.4, 0.16, 0.14), (cx, cy + yy, zt + 4.96))))
    for xx in (-5.8, 0.0, 5.8):
        ch.append(("wood", *_box_vf((0.14, 2 * ysb - 0.4, 0.12), (cx + xx, cy, zt + 4.96))))
    _merged("QH_天花格", ch, C)
    for i, (tx, ty) in enumerate(((-5.8, -2.2), (0.0, -2.2), (5.8, -2.2), (-5.8, 2.2), (5.8, 2.2), (0.0, 4.4))):
        add_cyl(f"QH_团龙{i}", 0.50, 0.50, 0.05, (cx + tx, cy + ty, zt + 4.90), "gold", C, n=10)
    for sx in (-1, 1):                                               # 楹联(明间金柱,细长板对,考据①)
        add_box(f"QH_楹联{sx}", (0.26, 0.045, 3.4), (cx + sx * (xsg[2] + 0.20), ysf - 0.10, zt + 2.05), "wood", C)
        add_box(f"QH_楹联挂{sx}a", (0.30, 0.06, 0.12), (cx + sx * (xsg[2] + 0.20), ysf - 0.10, zt + 3.80), "gold", C)
        add_box(f"QH_楹联挂{sx}b", (0.30, 0.06, 0.12), (cx + sx * (xsg[2] + 0.20), ysf - 0.10, zt + 0.34), "gold", C)
    fy = cy + 0.6                                                    # 佛坛(明间,千尊级供奉意象,考据①)
    add_prism("QH_佛坛", [(cx - 1.8, fy - 0.95), (cx + 1.8, fy - 0.95), (cx + 1.8, fy + 0.95), (cx - 1.8, fy + 0.95)],
              zt, zt + 0.50, "marble", C)
    add_box("QH_佛坛腰", (3.7, 1.95, 0.09), (cx, fy, zt + 0.31), "gold", C)
    add_cyl("QH_莲座", 0.55, 0.46, 0.30, (cx, fy, zt + 0.65), "gold", C, n=10)
    add_cyl("QH_佛身", 0.34, 0.25, 0.95, (cx, fy, zt + 1.28), "gold", C, n=10)
    add_ico("QH_佛首", 0.20, (cx, fy, zt + 1.98), (1, 1, 1.15), 1, "gold", C)
    bl = add_cyl("QH_背光", 0.80, 0.80, 0.05, (cx, fy + 0.32, zt + 1.60), "gold", C, n=14)
    bake_rot_x(bl, (cx, fy + 0.32, zt + 1.60), math.pi / 2)
    for sx in (-1, 1):
        add_cyl(f"QH_胁侍座{sx}", 0.24, 0.20, 0.16, (cx + sx * 1.45, fy, zt + 0.58), "gold", C, n=8)
        add_cyl(f"QH_胁侍身{sx}", 0.15, 0.11, 0.62, (cx + sx * 1.45, fy, zt + 0.97), "gold", C, n=8)
        add_ico(f"QH_胁侍首{sx}", 0.11, (cx + sx * 1.45, fy, zt + 1.36), (1, 1, 1.1), 1, "gold", C)
    dy2 = cy - 3.4                                                   # 供桌(明间前,考据①)
    add_box("QH_供桌面", (2.0, 0.85, 0.09), (cx, dy2, zt + 1.05), "wood", C)
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(f"QH_供桌腿{sx}{sy}", (0.12, 0.12, 0.96), (cx + sx * 0.85, dy2 + sy * 0.30, zt + 0.48), "wood", C)
    add_box("QH_供桌牙", (1.75, 0.05, 0.16), (cx, dy2 - 0.30, zt + 0.90), "wood", C)


C3 = coll("FS_琼华楼配廊")     # 配殿+游廊仍按原流程合并
C3Q = coll("QH_琼华楼构件")    # 构件级:不 join,逐构件节点导出
build_qionghua(C3Q)
build_gable_hall("FS_配殿东", C3, 27, 4, Z_UP, bays=3, bay_w=4.6, d=10, roof_mat="tile")
build_gable_hall("FS_配殿西", C3, -27, 4, Z_UP, bays=3, bay_w=4.6, d=10, roof_mat="tile")
build_corridor("FS_廊东段", C3, [(11.05, 4, Z_UP), (30, 4, Z_UP), (40, 4, Z_UP), (48, -6, Z_UP), (48, -30, Z_UP), (40, -33, Z_UP)], Z_UP)
build_corridor("FS_廊西段", C3, [(-11.05, 4, Z_UP), (-30, 4, Z_UP), (-40, 4, Z_UP), (-48, -6, Z_UP), (-48, -30, Z_UP), (-40, -33, Z_UP)], Z_UP)
build_corridor("FS_廊后东", C3, [(0, 14.1, Z_UP), (20, 16, Z_UP), (40, 24, Z_UP), (48, 36, Z_UP)], Z_UP)
build_corridor("FS_廊后西", C3, [(0, 14.1, Z_UP), (-20, 16, Z_UP), (-40, 24, Z_UP), (-48, 36, Z_UP)], Z_UP)

# ================================================================= §4 山字形三座重檐大亭
C4 = coll("FS_山字亭组")
# 中台(纵向一竖)+ 东台(横臂一端):西半由 MIRROR 生成,合为"山"字
add_prism("FS_中台", [(-11, -46), (11, -46), (11, -78), (-11, -78)], -1.8, 1.6, "marble", C4)
balustrade_run("FS_栏中台东", C4, (11, -46), (11, -78), 1.6)
balustrade_run("FS_栏中台南", C4, (-11, -78), (11, -78), 1.6)
balustrade_run("FS_栏中台西", C4, (-11, -46), (-11, -78), 1.6)
# 东台 + 东连桥(MIRROR 母版)
add_prism("FS_东台", [(22, -46), (38, -46), (38, -62), (22, -62)], -1.8, 1.4, "marble", C4)
add_prism("FS_连桥东", [(11, -51.3), (22, -51.3), (22, -56.7), (11, -56.7)], -1.5, 1.5, "marble", C4)
balustrade_run("FS_栏东台外", C4, (38, -46), (38, -62), 1.4)
balustrade_run("FS_栏东台南", C4, (22, -62), (38, -62), 1.4)
balustrade_run("FS_栏连桥北", C4, (11.5, -51.3), (21.5, -51.3), 1.5, post_gap=1.8)
balustrade_run("FS_栏连桥南", C4, (11.5, -56.7), (21.5, -56.7), 1.5, post_gap=1.8)
build_ting("FS_山字东亭", C4, 30, -53, 1.4, w=8.5, col_h=3.2, roof_h=3.3, roof_mat="glaze", storeys=1, cols=4)
add_ico("FS_假山东1", 1.6, (36, -48.5, 1.7), (1, 0.75, 0.75), 1, "marble", C4)
add_ico("FS_假山东2", 1.1, (24, -60, 1.55), (1, 0.8, 0.7), 1, "marble", C4)
# 登舟踏道
stairs("FS_中台阶", C4, 0, -78, 7.0, 0.15, 1.6, "S")
stairs("FS_东台阶", C4, 30, -62, 5.0, 0.15, 1.4, "S")
# 山字中亭(两层重檐,金顶——画中金阙)
build_ting("FS_山字中亭", C4, 0, -60, 1.6, w=10.5, col_h=3.5, roof_h=3.8, roof_mat="gold",
           storeys=2, cols=4, waist_h=1.6)
# MIRROR:东半 → 西半
mir = bpy.data.objects.new("FS_山字镜象心", None)
mir.location = (0, 0, 0)
bpy.context.scene.collection.objects.link(mir)
for o in list(C4.objects):
    if any(k in o.name for k in ("东台", "连桥东", "山字东", "假山东", "栏东台", "栏连桥", "东台阶")):
        md = o.modifiers.new("mir", "MIRROR")
        md.mirror_object = mir
        md.use_axis = (True, False, False)

# ================================================================= §5 九座佛楼 + 密檐佛塔
C5 = coll("FS_佛楼群")
xs9 = [-48, -36, -24, -12, 0, 12, 24, 36, 48]
for i, x in enumerate(xs9):
    st9 = 3 if abs(x) <= 12 else 2
    w9 = 10.0 if abs(x) <= 12 else 8.4
    build_hall(f"FS_佛楼{i+1:02d}", C5, x, 39, Z_UP, bays=3, bay_w=w9 / 3, d=8.6,
               storeys=st9, col_hs=(3.0, 2.7, 2.4), roof_h=2.9, roof_kind="xieshan",
               roof_mat="glaze" if i % 2 == 0 else "tile", ridge_w=w9 * 0.22,
               eave=0.85, dg_per_bay=2, back_lattice=True, lattice="both", lift=0.6)

def build_fota(name, c, cx, cy, z0, tiers=7, tw=4.4, th=13.0):
    """密檐佛塔:须弥座+塔身+八角密檐叠涩+金宝顶"""
    parts = []
    parts.append(add_box(f"{name}b1", (tw, tw, 0.5), (cx, cy, z0 + 0.25), "marble", c))
    b2 = add_box(f"{name}b2", (tw * 0.78, tw * 0.78, 0.4), (cx, cy, z0 + 0.7), "marble", c)
    bv = b2.modifiers.new("bev", "BEVEL")
    bv.width = 0.06
    bv.segments = 2
    parts.append(b2)
    z = z0 + 0.9
    body_h = th * 0.30
    parts.append(add_cyl(f"{name}bd", tw * 0.30, tw * 0.26, body_h, (cx, cy, z + body_h / 2), "red", c, n=8))
    z += body_h
    for i in range(tiers):
        f = 1 - i / (tiers + 1)
        r_e = tw * 0.52 * f + 0.55
        parts.append(add_cyl(f"{name}ev{i}", r_e, r_e * 0.8, 0.30, (cx, cy, z + 0.15), "glaze", c, n=8))
        drum_h = (th * 0.62) / tiers - 0.3
        parts.append(add_cyl(f"{name}dr{i}", r_e * 0.52, r_e * 0.48, drum_h, (cx, cy, z + 0.3 + drum_h / 2), "red", c, n=8))
        z += 0.3 + drum_h
    parts.append(add_ico(f"{name}bl", 0.34, (cx, cy, z + 0.35), (1, 1, 1), 1, "gold", c))
    parts.append(add_cyl(f"{name}sp", 0.05, 0.0, 1.1, (cx, cy, z + 0.95), "gold", c, n=6))
    return parts

build_fota("FS_佛塔01", C5, -55, 41, Z_UP, tiers=7, th=13.5)
build_fota("FS_佛塔02", C5, 55, 41, Z_UP, tiers=7, th=13.5)
build_fota("FS_佛塔03", C5, -20, 27, Z_UP, tiers=5, th=10.0)
build_fota("FS_佛塔04", C5, 20, 27, Z_UP, tiers=5, th=10.0)

# ================================================================= §6 九孔石桥 + 金鳌/玉蝀牌楼 + 石雕喷盘
C6 = coll("FS_九孔石桥")
bx0, bx1, by = -92, -58, 6
n_arch = 9
span = (bx1 - bx0) / n_arch
seg_n = 12
rows = []
for i in range(seg_n + 1):
    t = i / seg_n
    x = bx0 + (bx1 - bx0) * t
    z = 1.0 + 0.9 * math.sin(math.pi * t) ** 1.2
    rows.append((x, z))
v, f = [], []
for i, (x, z) in enumerate(rows):
    v += [(x, by - 2.8, z), (x, by + 2.8, z)]
    if i > 0:
        a = 2 * (i - 1)
        f += [(a, a + 1, a + 3, a + 2)]
_obj("FS_桥面", v, f, "marble", C6)
v, f = [], []
for i, (x, z) in enumerate(rows):
    v += [(x, by - 2.8, z - 0.55), (x, by + 2.8, z - 0.55)]
    if i > 0:
        a = 2 * (i - 1)
        f += [(a, a + 2, a + 3, a + 1)]
_obj("FS_桥腹", v, f, "marble", C6)
for k in range(1, n_arch):
    px = bx0 + span * k
    add_box(f"FS_墩{k}", (1.1, 6.2, 2.6), (px, by, -0.1), "marble", C6)
    add_prism(f"FS_墩尖{k}", [(px - 0.55, by - 3.1), (px + 0.55, by - 3.1), (px, by - 4.2)], -1.0, 0.9, "marble", C6)
    add_prism(f"FS_墩尖b{k}", [(px - 0.55, by + 3.1), (px + 0.55, by + 3.1), (px, by + 4.2)], -1.0, 0.9, "marble", C6)
for k in range(n_arch):
    cxm = bx0 + span * (k + 0.5)
    add_torus_arc(f"FS_拱{k}", span * 0.42, 0.35, (cxm, by, 0.3), "marble", C6, axis="y", major=10, minor=5, sz=0.9)
for side in (1, -1):
    yy = by + side * 2.65
    for i in range(seg_n // 2):
        x1 = bx0 + (bx1 - bx0) * (2 * i) / seg_n
        x2 = bx0 + (bx1 - bx0) * (2 * i + 2) / seg_n
        z1 = 1.0 + 0.9 * math.sin(math.pi * (2 * i) / seg_n) ** 1.2
        balustrade_run(f"FS_桥栏{side}{i}", C6, (x1, yy), (x2, yy), z1, post_gap=1.9)

def build_paifang_small(name, c, cx, cy, w=5.6, h_col=5.0):
    """二柱一间冲天坊(金鳌/玉蝀):冲天柱+双重额枋+金匾"""
    parts = []
    parts.append(add_box(f"{name}bs", (2.4, w + 3.2, 0.55), (cx, cy, 0.28), "marble", c))
    for s2 in (1, -1):
        y = cy + s2 * (w / 2)
        parts.append(add_cyl(f"{name}c{s2}", 0.30, 0.26, h_col, (cx, y, 0.55 + h_col / 2), "red", c, n=10))
        parts.append(add_box(f"{name}bz{s2}", (0.9, 0.9, 0.5), (cx, y, 0.8), "marble", c))
        parts.append(add_ico(f"{name}cp{s2}", 0.30, (cx, y, 0.55 + h_col + 0.25), (1, 1, 1.25), 1, "gold", c))
        parts.append(add_cyl(f"{name}tp{s2}", 0.05, 0.0, 0.5, (cx, y, 0.55 + h_col + 0.7), "gold", c, n=6))
    parts.append(add_beam(f"{name}e1", (cx, cy - w / 2 - 0.6, 3.1), (cx, cy + w / 2 + 0.6, 3.1), 0.42, 0.42, "red", c))
    parts.append(add_beam(f"{name}e2", (cx, cy - w / 2 - 0.4, 3.75), (cx, cy + w / 2 + 0.4, 3.75), 0.34, 0.34, "red", c))
    parts.append(add_box(f"{name}bi", (0.16, 1.7, 0.62), (cx, cy, 4.35), "gold", c))
    return parts

build_paifang_small("FS_金鳌牌楼", C6, -95.5, 6)
build_paifang_small("FS_玉蝀牌楼", C6, -54.5, 6)

def build_fountain(name, c, cx, cy):
    """石雕喷盘:圆台座 + 双层石盘 + 中央柱(喷泉意象简化)"""
    parts = []
    add_prism(f"{name}zt", [(cx + 2.6 * math.cos(a * math.pi / 12), cy + 2.6 * math.sin(a * math.pi / 12))
                            for a in range(24)], -1.4, 0.9, "marble", c)
    parts.append(add_cyl(f"{name}p1", 1.8, 1.9, 0.5, (cx, cy, 1.15), "marble", c, n=16))
    parts.append(add_cyl(f"{name}p2", 0.35, 0.3, 1.0, (cx, cy, 1.9), "marble", c, n=10))
    parts.append(add_cyl(f"{name}p3", 1.05, 1.15, 0.35, (cx, cy, 2.55), "marble", c, n=16))
    parts.append(add_ico(f"{name}tp", 0.28, (cx, cy, 2.9), (1, 1, 1), 1, "marble", c))
    return parts

build_fountain("FS_喷盘西", C6, -88, 16)
build_fountain("FS_喷盘东", C6, -63, 16)

# ================================================================= §7 南侧入口:冲天牌楼 + 华表
C7 = coll("FS_冲天牌楼")

def build_paifang_chongtian(name, c, cx, cy):
    """三开间六柱两夹墙冲天牌楼(砖木混合,柱头冲天)
       主柱 ±2.3 / ±4.6,夹墙端柱 ±6.4,共六柱;边门内两段夹墙(SOLIDIFY)"""
    parts = []
    add_box(f"{name}zt", (16.4, 3.0, 0.6), (cx, cy, 0.3), "marble", c)
    for i, xo in enumerate((-6.4, -4.6, -2.3, 2.3, 4.6, 6.4)):
        parts.append(add_cyl(f"{name}c{i}", 0.34, 0.30, 6.4, (cx + xo, cy, 0.6 + 3.2), "red", c, n=12))
        bs = add_box(f"{name}bz{i}", (1.0, 1.0, 1.3), (cx + xo, cy, 1.25), "marble", c)
        bv = bs.modifiers.new("bev", "BEVEL")
        bv.width = 0.18
        bv.segments = 3
        parts.append(bs)
        parts.append(add_ico(f"{name}cp{i}", 0.34, (cx + xo, cy, 7.35), (1, 1, 1.3), 1, "gold", c))
        parts.append(add_cyl(f"{name}tp{i}", 0.06, 0.0, 0.55, (cx + xo, cy, 7.9), "gold", c, n=6, smooth=False))
    parts.append(add_beam(f"{name}e1", (cx - 6.9, cy, 4.6), (cx + 6.9, cy, 4.6), 0.5, 0.5, "red", c))
    parts.append(add_beam(f"{name}e2", (cx - 5.1, cy, 5.25), (cx + 5.1, cy, 5.25), 0.36, 0.36, "red", c))
    parts.append(add_box(f"{name}hb", (9.6, 0.3, 0.5), (cx, cy, 4.95), "glaze", c))
    parts.append(add_box(f"{name}bi", (2.6, 0.22, 0.8), (cx, cy, 5.75), "gold", c))
    for s2 in (1, -1):
        wv = [(cx + s2 * 2.4, cy - 0.25, 0.6), (cx + s2 * 4.5, cy - 0.25, 0.6),
              (cx + s2 * 4.5, cy + 0.25, 0.6), (cx + s2 * 2.4, cy + 0.25, 0.6),
              (cx + s2 * 2.4, cy - 0.25, 4.0), (cx + s2 * 4.5, cy - 0.25, 4.0),
              (cx + s2 * 4.5, cy + 0.25, 4.0), (cx + s2 * 2.4, cy + 0.25, 4.0)]
        wl = _obj(f"{name}jw{s2}", wv, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], "red", c)
        sd = wl.modifiers.new("sol", "SOLIDIFY")
        sd.thickness = 0.5
        parts.append(wl)
        parts.append(add_box(f"{name}jcap{s2}", (2.4, 0.9, 0.22), (cx + s2 * 3.45, cy, 4.12), "tile", c))
    return parts

build_paifang_chongtian("FS_冲天牌楼", C7, 0, -141)

def build_huabiao(name, c, cx, cy):
    """华表:八角石柱 + 交叉云板 + 莲座承露盘 + 蹲兽"""
    parts = []
    parts.append(add_cyl(f"{name}bs", 0.95, 1.05, 0.7, (cx, cy, 0.95), "marble", c, n=8))
    parts.append(add_cyl(f"{name}cl", 0.34, 0.30, 6.2, (cx, cy, 0.7 + 3.1), "marble", c, n=8))
    for k, ang in enumerate((0.0, math.pi / 2)):
        e = add_ico(f"{name}yb{k}", 0.9, (0, 0, 0), (1.0, 0.22, 0.5), 1, "marble", c)
        bake_rot_z(e, (0, 0), ang)
        for vtx in e.data.vertices:
            vtx.co.x += cx
            vtx.co.y += cy
            vtx.co.z += 5.2
        parts.append(e)
    parts.append(add_cyl(f"{name}pn", 0.55, 0.42, 0.4, (cx, cy, 7.15), "marble", c, n=10))
    parts.append(add_ico(f"{name}sh", 0.30, (cx, cy, 7.65), (1, 1, 1.4), 1, "marble", c))
    return parts

for i, (hx, hy) in enumerate(((-13.5, -133.5), (13.5, -133.5), (-13.5, -148.5), (13.5, -148.5))):
    build_huabiao(f"FS_华表{i+1:02d}", C7, hx, hy)

# ================================================================= §8 小湖南侧两座形制不同的木板桥
C8 = coll("FS_木板桥")

def build_wood_bridge_straight(name, c, p1, p2, w=2.4):
    """木板桥A:直平桥 + 朱红栏杆 + 水中排桩"""
    parts = []
    p1, p2 = Vector(p1), Vector(p2)
    d = (p2 - p1).length
    ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
    mid = (p1 + p2) / 2
    parts.append(add_box(f"{name}dk", (d, w, 0.16), (mid.x, mid.y, 0.85), "wood", c, rot_z=ang))
    for k in range(max(2, int(d / 3))):
        t = (k + 0.5) / max(2, int(d / 3))
        px, py = p1.x + (p2.x - p1.x) * t, p1.y + (p2.y - p1.y) * t
        for s2 in (1, -1):
            parts.append(add_cyl(f"{name}pl{k}{s2}", 0.16, 0.14, 2.2,
                                 (px - math.sin(ang) * (w / 2 - 0.3) * s2, py + math.cos(ang) * (w / 2 - 0.3) * s2, -0.2),
                                 "wood", c, n=6))
    for s2 in (1, -1):
        ox, oy = -math.sin(ang) * (w / 2 - 0.15) * s2, math.cos(ang) * (w / 2 - 0.15) * s2
        parts.append(add_beam(f"{name}ra{s2}", (p1.x + ox, p1.y + oy, 1.25), (p2.x + ox, p2.y + oy, 1.25), 0.09, 0.09, "red", c))
        parts.append(add_beam(f"{name}rb{s2}", (p1.x + ox, p1.y + oy, 0.95), (p2.x + ox, p2.y + oy, 0.95), 0.07, 0.07, "red", c))
        n2 = max(2, int(d / 2.2) + 1)
        col = add_cyl(f"{name}rc{s2}", 0.07, 0.07, 0.5, (p1.x + ox, p1.y + oy, 1.1), "red", c, n=6)
        md = col.modifiers.new("arr", "ARRAY")
        md.count = n2
        dirv = (p2 - p1) / max(n2 - 1, 1)
        md.use_relative_offset = False
        md.use_constant_offset = True
        md.constant_offset_displace = (dirv.x, dirv.y, 0.0)
        parts.append(col)
    return parts

# 木板桥B:折角曲桥(木栏、无顶)——与A形制不同
build_wood_bridge_straight("FS_木板桥A", C8, (-84, -128.5), (-79, -112))
build_corridor("FS_木板桥B", C8, [(-62, -128), (-59, -120), (-64, -113), (-70, -107)], 0.6,
               w=2.2, col_h=1.1, roofed=False, posts_every=1.6)

# ================================================================= §9 东侧蕊珠宫
C9 = coll("FS_蕊珠宫")
add_prism("FS_蕊珠台基", [(68, -58), (124, -58), (124, 28), (68, 28)], -1.4, 1.2, "marble", C9)
add_prism("FS_蕊珠接桥", [(58, -15), (68, -15), (68, -9), (58, -9)], -1.2, 1.2, "marble", C9)
balustrade_run("FS_蕊珠桥栏a", C9, (58, -15), (68, -15), 1.2, post_gap=1.8)
balustrade_run("FS_蕊珠桥栏b", C9, (58, -9), (68, -9), 1.2, post_gap=1.8)
for (a, b) in (((68, -58), (124, -58)), ((124, -58), (124, 28)), ((124, 28), (68, 28)), ((68, 28), (68, -58))):
    balustrade_run(f"FS_蕊珠栏{a[0]}{a[1]}", C9, a, b, 1.2, post_gap=2.6)
# 宫墙(南墙留门)
for seg in (((70, -54), (122, -54)), ((122, -54), (122, 26)), ((122, 26), (70, 26)),
            ((70, 26), (70, -8)), ((70, -16), (70, -47))):
    p1, p2 = Vector(seg[0]), Vector(seg[1])
    d = (p2 - p1).length
    ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
    mid = (p1 + p2) / 2
    add_box(f"FS_蕊珠墙{seg[0][0]}{seg[0][1]}", (d, 0.6, 2.6), (mid.x, mid.y, 1.2 + 1.3), "red", C9, rot_z=ang)
    add_box(f"FS_蕊珠帽{seg[0][0]}{seg[0][1]}", (d, 0.85, 0.22), (mid.x, mid.y, 3.85), "tile", C9, rot_z=ang)
build_gable_hall("FS_蕊珠门殿", C9, 96, -47, 1.2, bays=3, bay_w=4.4, d=7.5, col_h=3.0, roof_h=2.2)
build_hall("FS_蕊珠正殿", C9, 96, -12, 1.2, bays=5, bay_w=5.2, d=11.5, storeys=1,
           col_hs=(3.6,), roof_h=3.8, roof_kind="xieshan", roof_mat="glaze",
           ridge_w=6.0, eave=1.0, dg_per_bay=2, back_lattice=True)
build_gable_hall("FS_蕊珠配东", C9, 78, -12, 1.2, bays=3, bay_w=4.2, d=8, roof_mat="tile")
build_gable_hall("FS_蕊珠配西", C9, 114, -12, 1.2, bays=3, bay_w=4.2, d=8, roof_mat="tile")
build_gable_hall("FS_蕊珠后东", C9, 88, 12, 1.2, bays=3, bay_w=4.2, d=8, roof_mat="tile")
build_gable_hall("FS_蕊珠后西", C9, 106, 12, 1.2, bays=3, bay_w=4.2, d=8, roof_mat="tile")
for (tx, ty) in ((78, 0), (114, 0)):
    add_cyl("FS_柏干", 0.18, 0.14, 2.2, (tx, ty, 1.2 + 1.1), "wood", C9, n=6)
    add_cyl("FS_柏冠", 1.3, 0.5, 4.6, (tx, ty, 1.2 + 4.4), "leaf_d", C9, n=8)

# ================================================================= §10 西侧三潭印月
C10 = coll("FS_三潭印月")

def build_shita(name, c, cx, cy):
    """三潭印月石塔(石灯笼式)"""
    parts = []
    parts.append(add_box(f"{name}b1", (1.5, 1.5, 0.45), (cx, cy, 0.2), "marble", c))
    parts.append(add_cyl(f"{name}b2", 0.55, 0.65, 0.3, (cx, cy, 0.55), "marble", c, n=6))
    parts.append(add_cyl(f"{name}s", 0.26, 0.24, 1.5, (cx, cy, 1.45), "marble", c, n=6))
    parts.append(add_cyl(f"{name}e1", 0.62, 0.5, 0.18, (cx, cy, 2.28), "marble", c, n=6))
    parts.append(add_cyl(f"{name}e2", 0.5, 0.4, 0.16, (cx, cy, 2.62), "marble", c, n=6))
    parts.append(add_ico(f"{name}t", 0.24, (cx, cy, 2.92), (1, 1, 1.3), 1, "marble", c))
    parts.append(add_cyl(f"{name}sp", 0.04, 0.0, 0.5, (cx, cy, 3.3), "marble", c, n=5))
    return parts

for i, (tx, ty) in enumerate(((-98, -112), (-108, -121), (-97, -127))):
    build_shita(f"FS_石塔{i+1:02d}", C10, tx, ty)
# 汀洲(白玉窄台伸入湖中)
spine = [(-92, -96), (-83, -105), (-77, -111), (-71, -117), (-65, -123)]
plat, plat2 = [], []
for k in range(len(spine)):
    ang = math.atan2(spine[min(k + 1, len(spine) - 1)][1] - spine[max(k - 1, 0)][1],
                     spine[min(k + 1, len(spine) - 1)][0] - spine[max(k - 1, 0)][0])
    plat.append((spine[k][0] - math.sin(ang) * 3.2, spine[k][1] + math.cos(ang) * 3.2))
for k in range(len(spine) - 1, -1, -1):
    ang = math.atan2(spine[min(k + 1, len(spine) - 1)][1] - spine[max(k - 1, 0)][1],
                     spine[min(k + 1, len(spine) - 1)][0] - spine[max(k - 1, 0)][0])
    plat2.append((spine[k][0] + math.sin(ang) * 3.2, spine[k][1] - math.cos(ang) * 3.2))
add_prism("FS_三潭汀洲", plat + plat2, -1.4, 0.9, "marble", C10)
# 五座亭/殿 + 曲折连廊
build_ting("FS_三潭亭一", C10, -90, -97.5, 0.9, w=5.6, col_h=2.7, roof_h=2.7, roof_mat="tile", cols=4, eave=0.85, s=0.8)
build_corridor("FS_三潭廊一", C10, [(-87, -100.5), (-84.5, -105), (-81.5, -106.5)], 0.9, w=2.2, col_h=2.5, roof_mat="tile")
build_ting("FS_三潭亭二", C10, -80.5, -107.5, 0.9, w=5.6, col_h=2.7, roof_h=2.7, roof_mat="glaze", cols=4, eave=0.85, s=0.8)
build_corridor("FS_三潭廊二", C10, [(-77.5, -110), (-75, -113), (-73.5, -114.5)], 0.9, w=2.2, col_h=2.5, roof_mat="tile")
build_ting("FS_三潭亭三", C10, -72.5, -115, 0.9, w=5.2, col_h=2.6, roof_h=2.6, roof_mat="tile", cols=4, eave=0.8, s=0.75)
build_corridor("FS_三潭廊三", C10, [(-70.5, -117.5), (-67.5, -119.5)], 0.9, w=2.0, col_h=2.4, roof_mat="tile")
build_gable_hall("FS_三潭水殿", C10, -66, -121.5, 0.9, bays=3, bay_w=3.4, d=6.0, col_h=2.8, roof_h=2.2, roof_mat="tile")
balustrade_run("FS_三潭栏a", C10, (-90.5, -97.5), (-67, -121.5), 0.9, post_gap=2.6)

# ================================================================= §11 北侧天宇空明
C11 = coll("FS_天宇空明")
add_prism("FS_天宇台基", [(-64, 64), (36, 64), (36, 104), (-64, 104)], -1.2, 1.0, "marble", C11)
add_prism("FS_天宇接桥", [(-19, 52), (-11, 52), (-11, 64), (-19, 64)], -1.2, 1.5, "marble", C11)
for k in range(2):
    add_torus_arc(f"FS_天宇拱{k}", 1.7, 0.3, (-15, 56.5 + k * 3.4, 0.35), "marble", C11, axis="x", major=8, minor=5, sz=0.85)
balustrade_run("FS_天宇桥栏a", C11, (-19, 52), (-19, 64), 1.5, post_gap=1.8)
balustrade_run("FS_天宇桥栏b", C11, (-11, 52), (-11, 64), 1.5, post_gap=1.8)
for (a, b) in (((-64, 64), (36, 64)), ((36, 64), (36, 104)), ((36, 104), (-64, 104)), ((-64, 104), (-64, 64))):
    balustrade_run(f"FS_天宇栏{a[0]}{a[1]}", C11, a, b, 1.0, post_gap=2.8)
build_gable_hall("FS_天宇门殿", C11, -15, 70, 1.0, bays=3, bay_w=4.2, d=7, col_h=3.0, roof_h=2.2)
build_hall("FS_天宇正殿", C11, -15, 90, 1.0, bays=5, bay_w=5.0, d=10.5, storeys=1,
           col_hs=(3.5,), roof_h=3.4, roof_kind="xieshan", roof_mat="tile",
           ridge_w=5.0, eave=0.95, dg_per_bay=2, back_lattice=True)
build_gable_hall("FS_天宇配东", C11, 6, 90, 1.0, bays=3, bay_w=4.0, d=7.5, roof_mat="tile")
build_gable_hall("FS_天宇配西", C11, -36, 90, 1.0, bays=3, bay_w=4.0, d=7.5, roof_mat="tile")
for seg in (((-60, 67), (-21, 67)), ((-9, 67), (32, 67)), ((32, 67), (32, 101)), ((32, 101), (-60, 101))):
    p1, p2 = Vector(seg[0]), Vector(seg[1])
    d = (p2 - p1).length
    ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
    mid = (p1 + p2) / 2
    add_box(f"FS_天宇墙{seg[0][0]}{seg[0][1]}", (d, 0.55, 2.4), (mid.x, mid.y, 1.0 + 1.2), "red", C11, rot_z=ang)
    add_box(f"FS_天宇帽{seg[0][0]}{seg[0][1]}", (d, 0.8, 0.2), (mid.x, mid.y, 3.5), "tile", C11, rot_z=ang)

# ================================================================= §12 地形/荷叶/舟
C12 = coll("FS_地形")
south_poly = [(-110, -170), (100, -170), (100, -128), (66, -128), (58, -124), (20, -128),
              (-50, -128), (-56, -131), (-63, -128.5), (-66, -124), (-64, -119), (-67, -113),
              (-73, -110), (-80, -113), (-84, -118), (-84, -124), (-88, -128), (-110, -128)]
add_prism("FS_南岸", south_poly, -1.6, Z_LAND, "stone", C12, top_mat="earth")
balustrade_run("FS_南岸栏东", C12, (14, -127.4), (56, -127.4), Z_LAND, post_gap=2.6)
balustrade_run("FS_南岸栏西", C12, (-50, -127.4), (-14, -127.4), Z_LAND, post_gap=2.6)
west_poly = [(-140, -140), (-92, -140), (-92, -128), (-92, -96), (-96, -90), (-104, -60), (-104, 60), (-140, 60)]
add_prism("FS_西岸", west_poly, -1.6, Z_LAND, "stone", C12, top_mat="earth")
east_poly = [(126, -62), (150, -62), (150, 30), (126, 30), (126, -30), (124, -58)]
add_prism("FS_东岸", east_poly, -1.6, Z_LAND, "stone", C12, top_mat="earth")
north_poly = [(-70, 104), (40, 104), (40, 118), (-70, 118)]
add_prism("FS_北岸", north_poly, -1.2, Z_LAND, "stone", C12, top_mat="earth")
add_ico("FS_小岛1", 5.0, (-120, -105, -0.4), (1, 0.8, 0.55), 2, "earth", C12)
add_ico("FS_小岛2", 4.0, (-124, -75, -0.4), (1, 0.9, 0.5), 2, "earth", C12)

C13 = coll("FS_荷叶")
for (px, py, rx, ry, n) in ((22, -78, 20, 12, 46), (-42, -92, 14, 10, 30),
                            (44, -100, 12, 8, 22), (-30, -70, 10, 7, 18)):
    for i in range(n):
        a = random.uniform(0, math.pi * 2)
        rr = math.sqrt(random.uniform(0.05, 1))
        x, y = px + math.cos(a) * rr * rx, py + math.sin(a) * rr * ry
        r0 = random.uniform(0.4, 0.85)
        add_cyl(f"FS_荷叶{i}", r0, r0 * 0.82, 0.07, (x, y, 0.05), "lotus", C13, n=10)
for i in range(16):
    px, py = random.choice([(22, -78), (-42, -92), (44, -100)])
    x, y = px + random.uniform(-14, 14), py + random.uniform(-8, 8)
    add_cyl(f"FS_荷花{i}", 0.14, 0.05, 0.32, (x, y, 0.24), "flower", C13, n=6)
    add_cyl(f"FS_荷花b{i}", 0.09, 0.02, 0.16, (x, y, 0.45), "flower", C13, n=5)

C14 = coll("FS_舟")

def build_boat(name, c, cx, cy, ang, ln=5.2):
    v, f = [], []
    prof = [(-ln / 2, 0.15), (-ln / 2 + 0.8, 0.75), (ln / 2 - 1.1, 0.95), (ln / 2, 0.55), (ln / 2 + 0.35, 0.0)]
    ca, sa = math.cos(ang), math.sin(ang)
    for x, hwk in prof:
        for s2 in (1, -1):
            v.append((cx + x * ca - (hwk * s2) * sa, cy + x * sa + (hwk * s2) * ca, 0.12))
    for k in range(len(prof) - 1):
        a = k * 2
        f.append((a, a + 1, a + 3, a + 2))
    _obj(f"{name}hl", v, f, "wood", c)
    bm_pts = []
    for i in range(7):
        t = -1 + 2 * i / 6
        x = 0.6 * t
        z = 1.05 + 0.55 * math.cos(t * math.pi / 2)
        w2 = 0.75 * math.sin(t * math.pi / 2 + 0.35)
        bm_pts.append((x, z, w2))
    v, f = [], []
    for x, z, w2 in bm_pts:
        v.append((cx + x * ca - w2 * sa, cy + x * sa + w2 * ca, z))
        v.append((cx + x * ca + w2 * sa, cy + x * sa - w2 * ca, z))
    for k in range(len(bm_pts) - 1):
        a = k * 2
        f.append((a, a + 1, a + 3, a + 2))
    _obj(f"{name}cn", v, f, "tile", c)

build_boat("FS_舟01", C14, 4, -86, math.radians(20))
build_boat("FS_舟02", C14, -8, -92, math.radians(-35))

# ================================================================= §13 苍松/垂柳/山丘
C15 = coll("FS_草木")

def build_pine(name, c, x, y, z0=Z_LAND, s=1.0):
    add_cyl(f"{name}tr", 0.24 * s, 0.18 * s, 2.4 * s, (x, y, z0 + 1.2 * s), "wood", c, n=6)
    for k, (zh, rr) in enumerate(((2.6, 1.9), (3.7, 1.5), (4.6, 1.05))):
        add_ico(f"{name}f{k}", rr * s, (x, y, z0 + zh * s), (1, 1, 0.62), 1, "leaf_d", c)

def build_willow(name, c, x, y, z0=Z_LAND, s=1.0):
    add_cyl(f"{name}tr", 0.28 * s, 0.2 * s, 3.0 * s, (x, y, z0 + 1.5 * s), "wood", c, n=6)
    add_ico(f"{name}c1", 2.6 * s, (x, y, z0 + 4.1 * s), (1, 1, 0.85), 2, "leaf_l", c)
    add_ico(f"{name}c2", 1.7 * s, (x + 1.1 * s, y - 0.7 * s, z0 + 3.0 * s), (1, 1, 1.15), 1, "leaf_l", c)
    add_ico(f"{name}c3", 1.5 * s, (x - 1.2 * s, y + 0.9 * s, z0 + 2.9 * s), (1, 1, 1.2), 1, "leaf_l", c)

pine_spots = [(-24, -152), (-19, -160), (-8, -158), (6, -159), (18, -157), (24, -150),
              (-27, -140), (27, -141), (-30, -158), (30, -159), (-15, -166), (12, -166)]
for i, (x, y) in enumerate(pine_spots):
    build_pine(f"FS_松{i+1:02d}", C15, x, y, Z_LAND, random.uniform(0.85, 1.25))
willow_spots = [(8, -125), (-8, -125.6), (24, -126), (-24, -126), (40, -126), (-40, -125.5),
                (52, -125), (-52, -126), (64, -122), (-66, -88), (-68, -78), (-70, -68),
                (-94, -50), (-95, 20), (-96, 44), (60, -122), (70, -116), (-88, -60)]
for i, (x, y) in enumerate(willow_spots):
    build_willow(f"FS_柳{i+1:02d}", C15, x, y, Z_LAND, random.uniform(0.8, 1.2))
more = [(-58, 110), (-30, 111), (0, 110), (28, 111), (-66, 108), (20, -122), (34, -123),
        (-98, -60), (-100, 8), (130, -40), (130, 8), (-112, 40)]
for i, (x, y) in enumerate(more):
    if i % 3 == 0:
        build_willow(f"FS_柳b{i+1:02d}", C15, x, y, Z_LAND, random.uniform(0.8, 1.1))
    else:
        build_pine(f"FS_松b{i+1:02d}", C15, x, y, Z_LAND, random.uniform(0.8, 1.2))

C16 = coll("FS_山丘")
hills = [(-30, 152, 90, 34, 30), (60, 148, 70, 30, 24), (-110, 140, 60, 30, 22),
         (130, 60, 55, 40, 20), (-140, 90, 55, 40, 22), (150, -110, 70, 45, 18),
         (-150, -60, 60, 40, 16), (100, -150, 60, 30, 14), (-120, -170, 80, 35, 15)]
for i, (x, y, rx, ry, h) in enumerate(hills):
    add_ico(f"FS_山丘{i+1:02d}", 1.0, (x, y, -h * 0.35), (rx, ry, h * 1.35), 2,
            "hill" if i % 2 == 0 else "hill2", C16)

# ================================================================= 收尾:应用修改器→按建筑合并→统计→导出
def finalize_group(objs, name, c):
    objs = [o for o in objs if o and o.name in bpy.data.objects]
    if not objs:
        return None
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    try:
        bpy.ops.object.convert(target='MESH')   # 应用 Array/Mirror/Solidify/Bevel
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

GROUPS = [("FS_主台基", C1), ("FS_哕鸾殿", C2), ("FS_琼华楼配廊", C3), ("FS_山字亭组", C4),
          ("FS_佛楼群", C5), ("FS_九孔石桥", C6), ("FS_冲天牌楼", C7), ("FS_木板桥", C8),
          ("FS_蕊珠宫", C9), ("FS_三潭印月", C10), ("FS_天宇空明", C11), ("FS_地形", C12),
          ("FS_荷叶", C13), ("FS_舟", C14), ("FS_草木", C15), ("FS_山丘", C16)]
for gname, c in GROUPS:
    finalize_group(list(c.objects), gname, c)

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

# ---- 琼华楼构件分类统计(逐构件,QH_ 前缀;每件只计入首个匹配类别)
QH_CATS = [
    ("台基(须弥座/御路/踏道)", ("QH_须弥座", "QH_御路", "QH_踏道")),
    ("柱网(檐柱/金柱/上檐柱)", ("QH_檐柱", "QH_金柱", "QH_上檐柱")),
    ("斗拱(平身科/柱头科)", ("QH_斗拱",)),
    ("额枋三件/金栿/走马板", ("QH_檐枋", "QH_由额垫板", "QH_额枋", "QH_金栿", "QH_走马板")),
    ("雀替", ("QH_雀替",)),
    ("旋子彩画带", ("QH_彩画",)),
    ("檐檩/椽望/翼角椽", ("QH_檐檩", "QH_椽", "QH_翼角")),
    ("格扇/窗/槛墙/墙板", ("QH_格扇", "QH_门扇", "QH_槛墙", "QH_墙板")),
    ("腰檐/平座/栏杆", ("QH_腰檐", "QH_平座", "QH_栏杆")),
    ("上檐屋面/瓦/脊饰/山花", ("QH_上檐屋面", "QH_上檐瓦", "QH_正脊", "QH_鸱吻", "QH_吻锁",
                            "QH_吻钉", "QH_宝顶", "QH_垂脊", "QH_戗脊", "QH_山花", "QH_博缝", "QH_圆光")),
    ("内檐天花/团龙/楹联", ("QH_天花", "QH_团龙", "QH_楹联")),
    ("佛坛/供桌/陈设", ("QH_佛", "QH_莲座", "QH_背光", "QH_胁侍", "QH_供桌")),
]
_dgs = bpy.context.evaluated_depsgraph_get()
_qh_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("QH_")]
_counted, _qh_total = set(), 0
print("\n=============== 琼华楼构件分类(逐构件,合并前) ===============")
for cat, keys in QH_CATS:
    t, n = 0, 0
    for o in _qh_objs:
        if o.name in _counted:
            continue
        if any(o.name.startswith(k) for k in keys):
            oe = o.evaluated_get(_dgs)
            me = oe.to_mesh()
            t += sum(len(p.vertices) - 2 for p in me.polygons) if me else 0
            oe.to_mesh_clear()
            _counted.add(o.name)
            n += 1
    _qh_total += t
    print(f"{cat:<24} {n:>4} 件 {t:>8} tris")
_unc = [o for o in _qh_objs if o.name not in _counted]
if _unc:
    t = 0
    for o in _unc:
        oe = o.evaluated_get(_dgs)
        me = oe.to_mesh()
        t += sum(len(p.vertices) - 2 for p in me.polygons) if me else 0
        oe.to_mesh_clear()
    _qh_total += t
    print(f"{'(其余 QH_ 构件)':<24} {len(_unc):>4} 件 {t:>8} tris")
print(f"{'QH_琼华楼单体合计':<24} {len(_qh_objs):>4} 件 {_qh_total:>8} tris  (单体预算 ≤ 60000)")

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
print(f"{'TOTAL':<16} {total:>8} tris  (预算 ≤ 400k)")

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

# ---- 导出 GLB
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
