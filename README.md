# 🏯 重生·圆明园 — AI数字文化遗产3D重建

> 2026第19届全国3D大赛 · 方案C：数字文化遗产3D重生

---

## 📋 参赛信息

| 项目 | 内容 |
|------|------|
| **比赛** | 2026第19届全国3D数字化创新设计大赛 |
| **方案** | 方案C：数字文化遗产3D重建 |
| **主题** | 重生·圆明园 — AI数字文化遗产3D重建 |
| **报名截止** | 2026年6月30日 |
| **作品提交** | 2026年7月20日 |
| **报名平台** | 微信小程序「3D大赛」/ https://ds.3ddl.net |

---

## 🎨 项目简介

圆明园，始建于康熙四十六年（1707年），由圆明园、长春园、绮春园三园组成，占地5200余亩，是清代大型皇家园林，被誉为"万园之园"。1860年遭英法联军焚毁后，仅余残垣断壁。

本项目以**AI辅助3D重建**为核心技术手段，通过历史文献研究、古画参考、AI图像生成与3D建模相结合的方式，对圆明园4大核心景区进行数字复原，并以**Web端实时3D交互展示**的形式，让观者身临其境感受这座"万园之园"的辉煌盛景。

---

## 🖥️ 两个展示入口

本仓库提供**双入口**，两个页面均为自包含单文件 HTML，主题一致、定位互补：

| 入口 | 定位 | 说明 |
|------|------|------|
| **圆明园.html**（根目录） | 🏛️ **实景模型版** | 程序化重建的四大景区环境 + 加载真实扫描级四合院实体 GLB 模型（`v3/models/chinese_courtyard_optimized.glb`），通过 GLTFLoader + MeshoptDecoder 本地解码加载 |
| **v3/index.html** | 🏞️ **程序化场景版** | 纯程序化建模的完整场景（九州清晏、大水法、方壶胜境、正大光明），零模型依赖、零外部网络请求，单文件即可打开 |

两版均使用本地 `three.min.js` + 内联 OrbitControls 实现，无 CDN 依赖，可离线运行。

---

## 🌐 在线访问（GitHub Pages）

仓库将启用 GitHub Pages，启用后访问地址格式：

```
https://poeticalps.github.io/--3d/
```

| 页面 | URL |
|------|-----|
| 实景模型版（根目录入口） | `https://poeticalps.github.io/--3d/` → `圆明园.html` |
| 程序化场景版 | `https://poeticalps.github.io/--3d/v3/index.html` |

> 注：Pages 首页默认指向仓库根目录，可通过根目录 `index.html`（如后续添加跳转页）或直接访问上述具体文件 URL 进入对应版本。

---

## 🗜️ 模型优化（98MB → 10.3MB）

`v3/models/chinese_courtyard_optimized.glb` 由原版 `chinese_courtyard.glb`（Sketchfab 导出）经 [gltf-transform](https://gltf-transform.dev/) 优化而来：

| 指标 | 原版 | 优化版 |
|------|------|--------|
| **文件体积** | 98 MB（102,934,464 字节） | **10.3 MB**（10,331,484 字节，↓ 90%） |
| **几何数据** | f32 全精度，最多 9 套 UV 坐标（大量未使用） | Meshopt 压缩（`EXT_meshopt_compression`）+ 顶点量化（`KHR_mesh_quantization`），未使用 UV 通道已清除 |
| **纹理** | JPEG/PNG 混合，≤1024×1024 | 43 张全部转为 WebP（`EXT_texture_webp`），**分辨率保持不变** |
| **材质** | PBR + `KHR_materials_specular` | 保持不变（未做调色板合并） |

优化命令：

```bash
npx @gltf-transform/cli optimize v3/models/chinese_courtyard.glb \
  v3/models/chinese_courtyard_optimized.glb \
  --compress meshopt --texture-compress webp \
  --texture-size 2048 --palette false --simplify false
```

- `--simplify false`：不做网格简化，保留全部几何细节
- 运行时解码依赖本地 `MeshoptDecoder.js`（主线程 WASM 解码，约 1.6s，无 Worker 依赖）
- 已通过浏览器实测：模型正常渲染、纹理无丢失发黑、交互正常

---

## ✨ 功能特性

### 🏞️ 四大核心景区

| 景区 | 说明 | 特色 |
|------|------|------|
| **九州清晏** | 后湖核心，九岛环水，象征华夏九州 | 黄琉璃瓦主殿、九岛桥梁系统 |
| **大水法** | 西洋楼核心，巴洛克+洛可可风格 | 三拱门+十二生肖铜首喷泉群 |
| **方壶胜境** | 仿神仙仙境，水上楼阁 | 七层宝塔、九座桥梁、假山群 |
| **正大光明** | 圆明园正殿，朝政举行地 | 重檐庑殿顶、华表、石狮 |

### 🎮 交互体验
- 🖱️ **鼠标左键旋转** — 360°全景浏览
- 🔄 **滚轮缩放** — 远近细节切换
- 🖐️ **右键平移** — 自由视角探索
- ✈️ **飞行动画** — 景区切换平滑过渡（easeInOutCubic缓动）
- 📊 **数字滚动** — 景区数据动态展示
- 🏷️ **详情面板** — 点击景区查看历史介绍与标签

### 🌤️ 视觉效果
- **自定义天空穹顶** — GLSL着色器渐变天空（深蓝→蓝灰→地平线白灰）
- **体积云层** — 半透明球体模拟积云（15组云团散布）
- **ACES色调映射** — 电影级色彩表现
- **PCFSoft阴影** — 柔和自然的光影效果
- **四光源系统** — 环境光+半球光+主光源+补光+背光
- **固定屋顶颜色** — 按历史等级严格区分（黄色/绿色/灰色/红色/蓝色/黑色）

### 🏗️ 程序化建筑建模
- **歇山顶** — 完整八面屋顶+山花+屋脊+脊兽
- **庑殿顶** — 四坡攒尖+正脊+垂脊
- **攒尖顶** — 宝塔顶部结构
- **桥/廊/亭** — 程序化生成辅助建筑
- **植被系统** — 8种树木类型+多层叶簇+花圃+荷花

---

## 📊 技术栈

| 模块 | 技术 | 说明 |
|------|------|------|
| **Web 3D渲染** | Three.js (r160, 内联OrbitControls) | 浏览器端实时渲染，无外部依赖 |
| **模型加载** | GLTFLoader + MeshoptDecoder | 实景 GLB 模型本地解码加载 |
| **模型优化** | gltf-transform CLI | Meshopt 几何压缩 + WebP 纹理压缩（98MB→10.3MB） |
| **3D建模** | Blender + Python | Cycles渲染引擎，程序化场景构建 |
| **AI图像转3D** | TripoSR / Meshy API | 图片驱动的3D模型生成 |
| **AI纹理生成** | Stable Diffusion | 建筑材质与纹理辅助生成 |
| **着色器** | GLSL (自定义) | 天空穹顶渐变效果 |
| **色彩管理** | AgX (ACES替代) | Blender端自然色彩转换 |
| **降噪** | OpenImageDenoise | 双重降噪（渲染时+后期） |
| **模型格式** | GLB/GLTF | Web端高效3D模型格式 |

---

## 📁 项目结构

```
yuanmingyuan-3d/
├── 圆明园.html                 # 🏛️ 实景模型版入口（程序化景区 + 实体四合院GLB）
├── three.min.js                # Three.js r160 运行时（根目录版）
├── GLTFLoader.js               # GLTF 加载器（根目录版）
├── MeshoptDecoder.js           # Meshopt 解码器（WASM, 主线程）
├── logo.svg / ico.jpg / compass.svg  # 品牌素材
├── v3/
│   ├── index.html              # 🏞️ 程序化场景版入口（2948行单文件，纯程序化）
│   ├── three.min.js            # Three.js 运行时（v3版）
│   ├── logo.svg / ico.jpg / compass.svg / UI_DESIGN_PLAN.md
│   └── models/
│       ├── chinese_courtyard_optimized.glb  # 🌟 优化后实体模型（10.3MB）
│       └── chinese_courtyard.glb            # 原版模型（98MB，仅在git历史中保留）
├── models/                     # 历史参考图片（圆明园四十景图等，6.3MB）
├── docs/                       # 项目文档（进度/工作流/UI设计方案等）
├── scripts/                    # Blender 场景构建与渲染脚本
│   ├── build_scene.py          # 场景构建
│   ├── build_scene_ultra.py    # 完整场景超级建模
│   ├── create_yuanmingyuan.py  # 基础场景创建
│   └── export_glb.py / render_quality_upgrade.py ...
├── src/                        # 源码（blender脚本/AI重建/前端/后端）
├── 创作过程文档.docx / .pdf     # 创作过程文档
└── README.md                   # 📖 本文件
```

---

## 🚀 使用方法

### 方式一：程序化场景版（可直接打开）

```bash
# v3/index.html 零模型依赖，直接双击打开即可
open v3/index.html
```

### 方式二：实景模型版（需本地服务器）

`圆明园.html` 需要通过 HTTP 加载 GLB 模型（浏览器对 `file://` 协议下的模型加载有限制）：

```bash
# 在仓库根目录启动本地服务器
python3 -m http.server 8080
# 浏览器访问 http://localhost:8080/圆明园.html
```

### 方式三：Blender场景构建

```bash
# 在Blender中运行场景构建脚本
blender --background --python scripts/build_scene.py
```

### 操作指南

| 操作 | 效果 |
|------|------|
| 🖱️ 鼠标左键拖动 | 旋转视角 |
| 🔄 滚轮 | 缩放远近 |
| 🖐️ 鼠标右键拖动 | 平移视角 |
| 📍 点击景区按钮 | 切换景区（带飞行动画） |
| 📖 点击详情面板 | 查看景区历史介绍 |
| 🖼️ 点击顶部Logo | 查看高清大图 |

---

## 🔧 自定义配置

### 调整场景参数

在 `v3/index.html` 中修改配置：

```javascript
// 修改相机初始位置
camera.position.set(80, 55, 80);

// 修改场景雾效
scene.fog = new THREE.Fog(0x9bb8cc, 60, 280);

// 修改色调映射曝光
renderer.toneMappingExposure = 1.35;
```

### 添加新景区

在 `SCENES` 配置对象中添加：

```javascript
SCENES['newScene'] = {
  cam: [x, y, z],       // 相机位置
  look: [x, y, z],       // 注视点
  title: '景区名称',
  year: '历史年代',
  desc: '景区描述',
  tags: ['标签1', '标签2'],
  stats: { buildings: '100', area: '20', docs: '500', models: '100', extra: null }
};
```

---

## 📝 设计说明（200字以内）

本作品以"重生·圆明园"为主题，运用AI辅助3D重建技术，对圆明园九州清晏、大水法、方壶胜境、正大光明四大核心景区进行数字复原。通过TripoSR/Meshy实现图片转3D，Blender完成场景组装与精细建模，Three.js打造Web端实时交互展示。作品包含程序化生成的歇山顶、庑殿顶等传统建筑结构，自定义GLSL天空穹顶着色器，以及完整的植被、水体、假山环境系统。以数字化方式重现"万园之园"的辉煌盛景，探索AI技术在文化遗产保护与传承中的创新应用。

---

## ⚠️ AIGC使用声明

本作品在以下环节使用了AIGC技术：
1. **图片转3D模型** — TripoSR / Meshy API
2. **建筑纹理生成** — Stable Diffusion
3. **代码辅助开发** — 大语言模型（Three.js/Python代码生成）
4. **历史文献整理** — 大语言模型辅助归纳

**人机参与比例：** 人工创意与构架 65%，AI辅助生成 35%

---

## 📚 参考资料

- 《圆明园四十景图》— 乾隆九年(1744年)宫廷画师唐岱、沈源绘制
- 清华大学数字圆明园项目 — 郭黛姮教授团队
- 《圆明园的故事》— 刘阳著，故宫出版社
- 《远逝的辉煌》— 郭黛姮编

---

## 👥 作者信息

- **作者**：[待填写]
- **学校**：[待填写]
- **指导教师**：[待填写]

---

*重生·圆明园 · AI数字文化遗产3D重建 · 2026全国3D大赛参赛作品*
