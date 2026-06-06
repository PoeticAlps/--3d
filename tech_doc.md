# 📘 技术文档 — 重生·圆明园 3D重建

> 本文档详细描述圆明园数字文化遗产3D重建项目的技术架构、建模方法、渲染技术与性能优化策略。

---

## 目录

1. [技术架构](#1-技术架构)
2. [建模方法](#2-建模方法)
3. [渲染技术](#3-渲染技术)
4. [Web 3D展示](#4-web-3d展示)
5. [性能优化](#5-性能优化)
6. [材质系统](#6-材质系统)
7. [光照系统](#7-光照系统)
8. [动画系统](#8-动画系统)
9. [数据规格](#9-数据规格)
10. [部署与运行](#10-部署与运行)

---

## 1. 技术架构

### 1.1 系统总览

```
┌─────────────────────────────────────────────────────┐
│                    前端展示层                         │
│  Three.js (WebGL) ← index.html (2048行)            │
│  · OrbitControls · 材质库 · 场景构建 · UI交互       │
├─────────────────────────────────────────────────────┤
│                    3D模型层                          │
│  GLB/GLTF模型 ← Blender Python脚本                 │
│  · build_complete_scene.py · render_*.py            │
├─────────────────────────────────────────────────────┤
│                    AI生成层                          │
│  TripoSR / Meshy API ← 历史图片                     │
│  · 图片转3D · 纹理生成 · 风格迁移                    │
├─────────────────────────────────────────────────────┤
│                    数据层                            │
│  历史文献 · 四十景图 · 考古资料 · 现代复原图          │
│  data/raw/images/                                   │
└─────────────────────────────────────────────────────┘
```

### 1.2 技术选型

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| Web 3D | Three.js | 内联集成 | 浏览器端实时渲染，生态成熟 |
| 着色器 | GLSL | ES 1.0 | 自定义天空穹顶，性能优异 |
| 3D建模 | Blender | 5.1 | 开源，Python API，Cycles渲染 |
| AI转3D | TripoSR/Meshy | — | 单图转3D，速度快 |
| AI纹理 | Stable Diffusion | — | 高质量建筑纹理生成 |
| 模型格式 | GLB | 2.0 | Web端高效，单文件打包 |

### 1.3 数据流

```
历史图片/古画
    ↓
AI图像转3D (TripoSR/Meshy)
    ↓
Blender导入 + 人工修复拓扑/法线
    ↓
Python脚本程序化场景组装
    ↓
Cycles渲染 (静态) / GLB导出 (Web)
    ↓
Three.js Web展示 (动态交互)
```

---

## 2. 建模方法

### 2.1 程序化建筑建模

项目采用**Python脚本驱动的程序化建模**方式，通过几何体组合与顶点操作生成传统中式建筑。

#### 歇山顶（Gable-and-hip Roof）

```python
# 核心参数
width: 建筑面宽
depth: 建筑进深
height: 屋顶高度
eaveOverhang: 出檐深度（默认2.2单位）

# 八面屋顶结构
1. 上前坡（正脊→山花线）
2. 上后坡（正脊→山花线）
3. 下前坡（山花线→檐口）
4. 下后坡（山花线→檐口）
5. 左戗坡（山花→左檐角）
6. 右戗坡（山花→右檐角）
7. 左山花（三角形侧面）
8. 右山花（三角形侧面）

# 装饰元素
- 正脊：gold材质圆柱体
- 垂脊：沿山花线
- 戗脊：至四角檐口
- 脊兽：戗脊端部金色球体
- 封檐板：四周一圈厚度感
```

#### 庑殿顶（Hip Roof）

用于正大光明等正殿建筑：
- 四坡攒尖结构
- 正脊+四条垂脊
- 檐角飞檐起翘（lift = eaveOverhang × 0.18）

#### 攒尖顶（Pointed Roof）

用于方壶胜境宝塔：
- 多层叠加（7层递减）
- 每层独立出檐
- 顶部宝刹

### 2.2 辅助建筑组件

| 组件 | 几何体 | 材质 |
|------|--------|------|
| 柱子 | CylinderGeometry | 木质红 |
| 台基 | BoxGeometry | 汉白玉 |
| 门窗 | BoxGeometry挖空 | 木质/金色 |
| 栏杆 | 细CylinderGeometry | 汉白玉 |
| 华表 | 组合几何体 | 汉白玉 |
| 石狮 | 组合几何体 | 汉白玉 |

### 2.3 植被系统

```javascript
// 8种树木类型（基于圆明园历史植被）
treeTypes = [
  { name: '深绿松', height: 5, radius: 1.8, weight: 20 },
  { name: '浅绿乔木', height: 4.5, radius: 1.6, weight: 12 },
  { name: '嫩绿柳', height: 4, radius: 1.5, weight: 8 },
  { name: '黄绿柳', height: 4.5, radius: 1.7, weight: 10 },
  { name: '金黄落叶松', height: 5, radius: 1.9, weight: 8 },
  { name: '金黄乔木', height: 4, radius: 1.5, weight: 6 },
  { name: '红褐枫', height: 4.5, radius: 2.0, weight: 6 },
  { name: '红枫', height: 4, radius: 1.8, weight: 5 }
];

// 单棵树结构
- 主干：CylinderGeometry (高度随机 ×0.7~1.3)
- 分枝：4-6根主分枝 + 2-3根子分枝
- 叶簇：3层球体（SphereGeometry），层间距递减
- 总计：75棵树散布在场景中
```

### 2.4 地形与水体

- **水面**：PlaneGeometry(400, 400)，半透明材质，IOR 1.333
- **草地**：PlaneGeometry(500, 500)，接收阴影
- **假山**：DodecahedronGeometry，12组固定位置
- **花圃**：牡丹、芍药、荷花，球体+茎干组合

---

## 3. 渲染技术

### 3.1 Three.js渲染配置

```javascript
// WebGL渲染器
renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));  // 高DPI适配
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;        // 柔和阴影
renderer.toneMapping = THREE.ACESFilmicToneMapping;      // 电影级色调
renderer.toneMappingExposure = 1.35;                     // 曝光补偿
```

### 3.2 天空穹顶（GLSL着色器）

自定义顶点/片段着色器实现三色渐变天空：

```glsl
// 顶点着色器
varying vec3 vWorldPos;
void main() {
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vWorldPos = wp.xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}

// 片段着色器
varying vec3 vWorldPos;
void main() {
    float h = normalize(vWorldPos).y;
    vec3 top     = vec3(0.42, 0.58, 0.78);  // 深天蓝
    vec3 mid     = vec3(0.62, 0.72, 0.82);  // 中层蓝灰
    vec3 horizon = vec3(0.82, 0.86, 0.90);  // 地平线浅灰白
    vec3 col;
    if (h > 0.3) col = mix(mid, top, smoothstep(0.3, 0.8, h));
    else         col = mix(horizon, mid, smoothstep(-0.05, 0.3, h));
    gl_FragColor = vec4(col, 1.0);
}
```

- **几何体**：SphereGeometry(400, 32, 20)，BackSide渲染
- **渲染顺序**：renderOrder = -1000（最先渲染）

### 3.3 Blender Cycles渲染

| 参数 | 配置 |
|------|------|
| 渲染引擎 | Cycles |
| 采样数 | 512（自适应采样） |
| 降噪器 | OpenImageDenoise（渲染+后期双重） |
| 色彩空间 | AgX (ACES替代) |
| 分辨率 | 1920×1080 |
| 体积散射密度 | 0.001（大气雾效） |
| 水体IOR | 1.333（物理准确折射率） |

### 3.4 水体渲染

```python
# 菲涅尔效应
bsdf.inputs['Base Color'] = (0.0, 0.2, 0.4, 1.0)
bsdf.inputs['Roughness'] = 0.05
bsdf.inputs['Metallic'] = 0.4

# 动态波纹
wave_texture.inputs['Scale'] = 5.0
wave_texture.inputs['Phase Offset']  # 添加关键帧动画

# 边缘泡沫
# 基于法线角度的泡沫效果
```

---

## 4. Web 3D展示

### 4.1 场景管理

```javascript
// 5个场景配置
SCENES = {
  overview:  { cam: [80,55,80],  look: [0,0,0] },     // 全景
  jiuzhou:   { cam: [25,18,25],  look: [0,2,0] },     // 九州清晏
  dashuifa:  { cam: [20,14,88],  look: [0,4,70] },    // 大水法
  fangpu:    { cam: [88,18,20],  look: [70,3,0] },    // 方壶胜境
  zhengda:   { cam: [-50,20,22], look: [-70,4,0] }    // 正大光明
};
```

### 4.2 相机控制

```javascript
controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;         // 惯性阻尼
controls.dampingFactor = 0.08;         // 阻尼系数
controls.minDistance = 10;              // 最近缩放
controls.maxDistance = 200;             // 最远缩放
controls.maxPolarAngle = Math.PI * 0.48;  // 限制俯仰角（防止穿地）
```

### 4.3 飞行动画

场景切换时执行平滑飞行动画：

```javascript
// 缓动函数：easeInOutCubic
ease = t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3) / 2;

// 插值
camera.position.lerpVectors(startPos, endPos, ease);
controls.target.lerpVectors(startLook, endLook, ease);

// 动画时长
animDuration = 1200;  // 毫秒
```

### 4.4 自定义OrbitControls

项目内联实现了完整的OrbitControls（非外部依赖），支持：
- 球坐标系旋转（theta/phi）
- 平移（panLeft/panUp）
- 缩放（zoomScale）
- 极角限制（min/maxPolarAngle）
- 距离限制（min/maxDistance）

---

## 5. 性能优化

### 5.1 渲染优化

| 策略 | 实现 | 效果 |
|------|------|------|
| **像素比限制** | `Math.min(devicePixelRatio, 2)` | 防止高DPI设备过载 |
| **阴影贴图尺寸** | 2048×2048 | 平衡质量与性能 |
| **阴影偏移** | -0.001 | 防止阴影失真（shadow acne） |
| **雾效裁剪** | Fog(60, 280) | 远处物体渐隐，减少绘制 |
| **背面剔除** | 屋顶材质 DoubleSide | 减少面数 |
| **深度写入控制** | 云层 `depthWrite: false` | 防止透明排序问题 |

### 5.2 几何体优化

```javascript
// 简化几何体段数
SphereGeometry(radius, 8, 6)    // 云层（低精度）
SphereGeometry(radius, 6, 6)    // 叶簇（更低精度）
CylinderGeometry(r1, r2, h, 8)  // 柱子（适中精度）
DodecahedronGeometry(s, 1)      // 假山（参数化细分）

// BufferGeometry直接构建
triFace(a, b, c)   // 三角面：3顶点
quadFace(a, b, c, d) // 四边面：4顶点→2三角面
```

### 5.3 内存优化

- **材质复用**：全局材质库 `M` 对象，所有建筑共享材质实例
- **屋顶颜色固定**：按历史等级分配，不随机生成（减少材质数量）
- **模型格式**：GLB单文件打包，减少网络请求
- **渐进加载**：loading界面 + 进度条反馈

### 5.4 响应式适配

```javascript
window.addEventListener('resize', function() {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
});
```

---

## 6. 材质系统

### 6.1 材质库（M对象）

| 材质名 | 颜色 | 粗糙度 | 金属度 | 用途 |
|--------|------|--------|--------|------|
| marble | #F5F0E8 | 0.3 | 0.05 | 汉白玉台基/栏杆 |
| pillar | #8B2020 | 0.6 | — | 朱红柱子 |
| gold | #D4A84B | 0.3 | 0.7 | 金色装饰/屋脊 |
| roofY | #C9A227 | 0.4 | 0.15 | 黄琉璃瓦（皇帝级） |
| roofGreen | #2A6A3A | 0.5 | 0.1 | 绿琉璃瓦 |
| roofGray | #5A5A5A | 0.6 | — | 灰瓦（普通建筑） |
| roofRed | #8A3020 | 0.55 | 0.1 | 红瓦 |
| roofBlue | #3A4A6A | 0.5 | 0.1 | 蓝琉璃瓦 |
| roofBlack | #1A1A1A | 0.7 | — | 黑瓦 |
| water | #7A9AB8 | 0.05 | 0.4 | 水面（透明0.82） |
| bronze | #8B7355 | 0.35 | 0.75 | 铜像/兽首 |
| rock | #6A6A6A | 0.9 | — | 假山石 |
| grass | #3A6A3A | 0.95 | — | 草地 |

### 6.2 屋顶颜色等级制度

圆明园建筑屋顶颜色严格遵循清代等级制度：

```
黄色琉璃瓦（roofY）→ 皇帝级建筑（正大光明、九州清晏主殿）
绿色琉璃瓦（roofGreen）→ 王公级建筑
灰色瓦（roofGray）→ 普通建筑/配殿
红色瓦（roofRed）→ 特殊建筑
蓝色琉璃瓦（roofBlue）→ 天坛建筑风格
黑色瓦（roofBlack）→ 藏书楼等
```

所有屋顶材质启用 `DoubleSide` 渲染，确保内外两侧可见。

---

## 7. 光照系统

### 7.1 四光源配置

```javascript
// 1. 环境光 — 冷调散射，模拟阴天漫射
AmbientLight(0x9aafcc, 0.7)

// 2. 半球光 — 天蓝→地面绿，模拟天空穹顶散射
HemisphereLight(0x8ab4d8, 0x4a6a4a, 0.5)

// 3. 主光源 — 偏冷白，高位侧光
DirectionalLight(0xe8eeff, 1.6)
position: (-50, 90, 60)
shadow: 2048×2048, range ±130

// 4. 补光 — 冷蓝，来自对侧
DirectionalLight(0xaaccee, 0.35)
position: (40, 60, -40)

// 5. 背光 — 微暖，增加层次
DirectionalLight(0xddccaa, 0.2)
position: (0, 25, -80)
```

### 7.2 阴影配置

```javascript
sun.shadow.mapSize.set(2048, 2048);    // 阴影贴图分辨率
sun.shadow.camera.left = -130;          // 阴影相机范围
sun.shadow.camera.right = 130;
sun.shadow.camera.top = 130;
sun.shadow.camera.bottom = -130;
sun.shadow.camera.near = 10;
sun.shadow.camera.far = 350;
sun.shadow.bias = -0.001;               // 防止shadow acne
```

### 7.3 Blender端光照

| 光源类型 | 参数 | 说明 |
|----------|------|------|
| 太阳光 | 强度1.0，角度45° | 主光源 |
| 环境光 | 强度0.3 | 基础照明 |
| 体积散射 | 密度0.001 | 大气雾效 |
| HDRI | 可选 | 环境贴图照明 |

---

## 8. 动画系统

### 8.1 渲染循环

```javascript
function animate() {
    requestAnimationFrame(animate);
    
    // 飞行动画插值
    if (animating) {
        var t = Math.min((Date.now() - animStart) / animDuration, 1);
        var ease = t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2, 3) / 2;
        camera.position.lerpVectors(startPos, endPos, ease);
        controls.target.lerpVectors(startLook, endLook, ease);
        if (t >= 1) animating = false;
    }
    
    controls.update();
    renderer.render(scene, camera);
}
```

### 8.2 数字滚动动画

```javascript
// easeOutCubic缓动
ease = 1 - Math.pow(1 - progress, 3);

// 千分位格式化
function fmt(n) {
    return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
```

### 8.3 水波纹动画

Blender端通过关键帧动画实现：
```python
wave_texture.inputs['Phase Offset'].default_value = 1.0
# 设置关键帧产生动态水波效果
```

---

## 9. 数据规格

### 9.1 景区统计数据

| 景区 | 建筑数 | 面积(公顷) | 历史文献 | 数字模型 | 特殊元素 |
|------|--------|-----------|----------|----------|----------|
| 全景 | 1,247 | 350 | 8,432 | 2,048 | — |
| 九州清晏 | 186 | 42 | 1,240 | 328 | 9座岛屿 |
| 大水法 | 53 | 18 | 680 | 156 | 13座喷水塔 |
| 方壶胜境 | 124 | 28 | 920 | 267 | 9座桥梁 |
| 正大光明 | 67 | 15 | 1,080 | 189 | 2座华表 |

### 9.2 模型文件

| 文件 | 大小 | 格式 | 说明 |
|------|------|------|------|
| yuanmingyuan_complete.glb | 7.4MB | GLB | 完整场景模型 |
| dashuifa_zodiac_ultra.glb | — | GLB | 大水法十二生肖 |
| dashuifa_render.blend | — | Blender | 大水法场景文件 |

### 9.3 场景规模

| 指标 | 数值 |
|------|------|
| 场景范围 | 500×500 单位 |
| 天空穹顶半径 | 400 单位 |
| 水面尺寸 | 400×400 单位 |
| 树木数量 | 75棵 |
| 云团数量 | 15组 |
| 假山组数 | 12组 |
| 花圃点位 | 6处 |
| 荷花数量 | 20朵 |

---

## 10. 部署与运行

### 10.1 环境要求

| 环境 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 浏览器 | Chrome 80+ / Firefox 75+ | Chrome 最新版 |
| WebGL | 1.0 | 2.0 |
| Blender | 3.0+ | 5.1 |
| Python | 3.8+ | 3.14 |

### 10.2 快速启动

```bash
# 1. 克隆项目
cd "yuanmingyuan-3d"

# 2. 启动Web展示
cd v3 && python3 -m http.server 8080
# 浏览器访问 http://localhost:8080

# 3. 或直接打开
open v3/index.html
```

### 10.3 Blender场景构建

```bash
# 完整场景构建
blender --background --python build_complete_scene.py

# 大水法精细建模
blender --background --python src/blender_scripts/build_dashuifa_detailed.py

# 渲染输出
blender --background --python render_dashuifa_competition.py
```

### 10.4 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 页面空白 | WebGL不支持 | 升级浏览器或启用硬件加速 |
| 渲染卡顿 | 设备性能不足 | 降低devicePixelRatio上限 |
| AgX不可用 | Blender版本过低 | 升级至4.0+或改用Filmic |
| 模型加载慢 | GLB文件过大 | 使用Draco压缩或减面 |
| 阴影失真 | bias设置不当 | 调整shadow.bias值 |

---

## 附录：关键代码索引

| 功能 | 文件 | 行号范围 |
|------|------|----------|
| OrbitControls实现 | v3/index.html | 122-303 |
| 场景配置 | v3/index.html | 308-329 |
| 材质库 | v3/index.html | 332-365 |
| 初始化 | v3/index.html | 384-421 |
| 灯光系统 | v3/index.html | 428-457 |
| 天空穹顶GLSL | v3/index.html | 470-547 |
| 地形构建 | v3/index.html | 549-674 |
| 歇山顶建模 | v3/index.html | 718-800+ |
| 九州清晏场景 | v3/index.html | (buildJiuzhouScene) |
| 大水法场景 | v3/index.html | (buildDashuifaScene) |
| 方壶胜境场景 | v3/index.html | (buildFangpuScene) |
| 正大光明场景 | v3/index.html | (buildZhengdaScene) |
| UI交互 | v3/index.html | 1943-1993 |
| 动画循环 | v3/index.html | 2018-2034 |

---

*文档版本：1.0 | 更新日期：2026-06-02 | 项目：重生·圆明园*
