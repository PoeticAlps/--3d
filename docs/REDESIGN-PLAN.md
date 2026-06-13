# 圆明园V3 重构方案

> 基于 Taste-Skill + Redesign-Skill 审计，针对3D交互式文化遗产体验项目

---

## Design Read

3D交互式文化遗产体验，面向竞赛评委和设计学者，国风美学语言，原生CSS + Three.js + 宋体排版 + 克制动效

## Dial 值

| 参数 | 值 | 理由 |
|------|-----|------|
| DESIGN_VARIANCE | 7 | 遗产项目需要庄重但不死板，适度不对称 |
| MOTION_INTENSITY | 5 | 功能性动效为主，避免装饰性过度 |
| VISUAL_DENSITY | 3 | 文化遗产需要呼吸感，画廊级留白 |

---

## 一、重构范围

### 保留不动（已达标）
- ✅ 国风配色体系（#8B6E3E/#B89F7A/#DCD3BF/#E8A800）
- ✅ 流光线双层结构 + 三段动效
- ✅ 潘多拉魔盒加载动画
- ✅ 无障碍基础设施（focus-visible/reduced-motion/aria-label）
- ✅ 响应式四断点
- ✅ Three.js 3D场景 + OrbitControls
- ✅ 场景切换逻辑 + 数据联动

### 需要重构

#### P0：布局去居中化（taste-skill §4.3）
**问题：** 19处 `text-align:center` / `justify-content:center`，整体过于对称
**方案：**
- Header：左logo+标题左对齐，右全屏按钮右对齐（已达标）
- 数据面板：标题居中保留（面板内居中合理），但面板本身左置不动
- 详情面板：标题左对齐，内容左对齐（已达标）
- 底部控制提示：左对齐替代居中
- 加载页：保留居中（加载页居中是合理的）

#### P1：像素单位→相对单位（taste-skill §3.E）
**问题：** 20处固定px宽度
**方案：**
- `.stats` width: 210px → max-width: 220px + width: auto
- `.detail` width: 280px → width: min(280px, 40vw)
- `.pandora-scene` width/height → 相对单位
- 所有固定padding改为rem或clamp()

#### P2：阴影色调化（taste-skill §4.4）
**问题：** 2处纯黑阴影
**方案：**
- `box-shadow: 0 0 60px rgba(212,168,75,0.3)` → 保留（已色调化）
- 检查所有shadow，确保与背景色调一致

#### P3：添加 scroll-behavior: smooth
**方案：** `html { scroll-behavior: smooth; }`（虽然本项目overflow:hidden，但为未来扩展预留）

#### P4：内联样式抽取
**问题：** HTML中大量 `style=""` 
**方案：** 将高频内联样式抽取为CSS类（如 .tag-inline, .stats-ai-badge 等）

#### P5：z-index系统化
**方案：** 建立z-index scale：
```
--z-canvas: 0
--z-ui: 100
--z-controls: 101
--z-detail: 120
--z-header: 130
--z-modal: 200
--z-loading: 1000
```

#### P6：面板层级优化
**方案：**
- 详情面板添加 Escape 键关闭
- 详情面板添加点击外部关闭
- 面板滚动时添加滚动指示器

---

## 二、重构顺序

1. **备份确认** → GitHub推送完成
2. **z-index系统** → 建立CSS变量（5分钟）
3. **像素→相对单位** → 逐个替换（15分钟）
4. **布局去居中** → 调整控制提示等（10分钟）
5. **内联样式抽取** → 清理HTML（15分钟）
6. **交互增强** → Escape关闭/点击外部关闭（10分钟）
7. **测试验证** → 全断点检查 + 动效验证（10分钟）
8. **提交推送** → commit + push

---

## 三、回退方案

- 本地：`git reset --hard b66f7e1`（当前commit hash）
- 远端：`git revert HEAD` 或 `git reset --hard origin/main`

---

## 四、预期效果

重构后项目将：
- 布局更有层次感，打破居中单调
- 单位系统更健壮，适配各种屏幕
- 交互更完善，键盘可操作
- 代码更整洁，维护性提升
- 保持国风美学和3D交互核心体验不变
