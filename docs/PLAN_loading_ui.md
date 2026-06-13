# 圆明园V3 · 「启盒见园」加载动效 完整计划

## 概念定义

> 以潘多拉魔盒作为整体视觉叙事载体，将湮没于历史中的圆明园盛景隐喻封存于盒体内部；盒体中心设置专属圆形项目LOGO作为视觉核心锚点，以LOGO完整自转一周作为盒体开启的前置触发条件，整套动画按照「LOGO轮转解锁→盒盖三维启封→光晕漫涌生雾→园景逐层显露→侧边栏下落归位→魔盒退场转主界面」递进排布。

---

## 色彩体系
- 底色: `#0D0F1A`（深邃夜空蓝）
- 国风主色: `#915C2E`（古铜金）
- LOGO光晕: `rgba(145,92,46,0.3)` → `transparent`
- 粒子色调: `rgba(200,180,140, alpha)` 暖金
- 文字: `#c8b070`（金色标题）、`#8a7a68`（次要）

---

## 8阶段时序 × 进度区间

| # | 阶段 | 进度区间 | 类型 | 说明 |
|---|------|----------|------|------|
| 1 | 初始静默 | 0% | 静态 | 全屏暗底+闭合魔盒+静止LOGO |
| 2 | LOGO自转解锁 | 0%→35% | 串行前置 | LOGO 360°匀速自转+呼吸光晕 |
| 3 | 盒盖三维旋开 | 35%→55% | 串行 | 左右盖板CSS 3D rotateY外翻 |
| 4 | 径向金光扩散 | 40%→70% | 与3并行 | LOGO边缘径向渐变柔光向外铺展 |
| 5 | Canvas云雾粒子 | 45%→100% | 长期并行 | 粒子从盒口向外弥散，密度随进度递减 |
| 6 | 园林逐层浮现 | 45%→100% | 与5并行 | 模糊→清晰：水面→洲岛植被→殿宇建筑 |
| 7 | 侧边栏下落 | 90%→100% | 串行 | 左右面板从顶部Y位移归位 |
| 8 | 收尾退场 | 100%完成后 | 串行 | 魔盒缩小渐隐+底部导航淡入→主界面 |

---

## 技术约束
- 单HTML文件，内嵌CSS/JS
- Three.js r150 + 内联OrbitControls
- 不依赖外部CDN
- CSS 3D Transform + @keyframes + Canvas 2D粒子
- 资源加载容错：动画阻塞判断，模型未就绪则暂停收尾转场

---

## 实现清单

### HTML结构
- `.loading` 容器（z-index:1000）
  - `.magic-box` 魔盒3D容器（perspective:800px）
    - `.box-lid-left` 左盖板
    - `.box-lid-right` 右盖板
    - `.box-inner` 盒心区域
      - `.logo-circle` 圆形LOGO锚点
      - `.radial-glow` 径向光晕层
      - `.garden-preview` 园林预览层（CSS渐变模拟）
  - `canvas#fogCanvas` 云雾粒子层
  - `.loading-text` 底部文字+进度条
- `.sidebar-left` / `.sidebar-right` 初始 `translateY(-100%)`

### CSS关键帧
- `@keyframes logoRotate` — LOGO 360°自转
- `@keyframes logoBreathe` — 呼吸光晕 opacity脉冲
- `@keyframes lidOpenLeft` — 左盖板 rotateY(0→-75deg)
- `@keyframes lidOpenRight` — 右盖板 rotateY(0→75deg)
- `@keyframes glowExpand` — 径向光晕 scale(0.3→1.2) + opacity
- `@keyframes fogDrift` — 粒子飘散
- `@keyframes gardenReveal` — 园林 blur(20→0) + opacity
- `@keyframes sidebarDrop` — 侧边栏 translateY(-100%→0)
- `@keyframes boxExit` — 魔盒 scale(1→0.8) + opacity(1→0)

### JS逻辑
1. 进度模拟器（0→100%，3-4秒）
2. 进度回调：根据进度区间触发对应CSS class
3. Canvas 2D粒子系统（40-60粒子）
4. 资源加载检测：Three.js scene.ready判断
5. 收尾转场：loading淡出 → 主UI淡入

---

## 输出
- 原地更新: `/Users/saint/Desktop/WX hermes workspace/yuanmingyuan-3d/v3/index.html`
- 计划文件: `PLAN_loading_ui.md`
