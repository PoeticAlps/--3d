# Hermes Agent 完整交接文档
> 最后更新：2026-06-12 | Profile: second | 平台: WeChat DM

---

## 1. 用户身份

| 字段 | 值 |
|------|-----|
| 姓名 | 张艺 |
| 学校 | 广西艺术学院 |
| 专业 | 设计学 |
| GitHub | PoeticAlps |
| 指导教师 | 待定 |
| 沟通语言 | 中文 |
| 风格偏好 | Caveman Style（≤50字、无寒暄、直接结果） |
| 称呼 | 叫用户"宝宝" |
| 隐私 | 不翻墙、不违法、优先国产方案 |
| 教学模式 | 执行性任务→直接给结果不列步骤；学习性任务可参与 |
| 视觉要求 | AgX色彩+位移法线AO做旧+体积云雾+菲涅尔水体 |
| 项目质量 | 主动测试视觉效果并报告bug，画面质量要求高 |

---

## 2. 系统环境

### 硬件/OS
- Mac (Apple Silicon M3)
- macOS（具体版本未记录）
- GPU: Apple M3 Metal API（Blender渲染存在MTLCommandBufferErrorDomain Code=1错误）

### 关键路径
| 用途 | 路径 |
|------|------|
| **工作区（WX）** | `/Users/saint/Desktop/WX hermes workspace/` |
| **圆明园项目** | `/Users/saint/Desktop/WX hermes workspace/yuanmingyuan-3d/` |
| **V3展示页** | `yuanmingyuan-3d/v3/index.html`（端口8766 serve） |
| **桌面** | `/Users/saint/Desktop/` |
| **Hermes Profile** | `~/.hermes/profiles/second/` |
| **配置文件** | `~/.hermes/profiles/second/config.yaml` |
| **环境变量** | `~/.hermes/profiles/second/.env` |
| **会话数据库** | `~/.hermes/profiles/second/state.db`（~941MB） |
| **技能目录** | `~/.hermes/profiles/second/skills/` |
| **记忆文件** | `~/.hermes/profiles/second/memories/`（MEMORY.md, USER.md） |
| **日志** | `~/.hermes/profiles/second/logs/` |
| **备份** | `~/Desktop/hermes-config-backup/` |
| **旧备份** | `~/Desktop/agent 工作区/hermes/hermes-workspace-2/` |
| **Blender插件** | `~/Library/Application Support/Blender/5.1/scripts/addons/` |
| **桌面屋顶模型** | `~/Desktop/roof_models/`（8个传统屋顶blend文件） |
| **Rust** | `~/.cargo/bin/rustc`（1.96.0） |
| **Tauri项目** | `/Users/saint/tauri-app/` |
| **EasyHermes** | `~/Desktop/EasyHermes_macOS_files/`（未解压运行） |

### 软件版本
- Blender 5.1.1（`/Applications/Blender.app`）
- Rust 1.96.0
- Tauri CLI v1.6.6
- Headroom v0.22.4（已装，PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1）
- OMO已安装
- Clawd on Desk v0.9.0已装
- OpenDataLoader PDF v2.4.7

---

## 3. Hermes Agent 配置

### Profile 架构
| Profile | 用途 | 状态 |
|---------|------|------|
| **second** | 主力（WeChat + QQ Bot） | ✅ 运行中 |
| **default** | 老大，已停用 | ⚠️ 已禁用自动启动 |

### API & Provider
| 服务 | 配置 |
|------|------|
| LLM Model | mimo-v2.5 (Xiaomi MiMo) |
| Provider URL | `token-plan-sgp.xiaomimimo.com/v1` |
| OpenClaw Key | `tp-sis27...5tcynfv9`（URL=token-plan-sgp.xiaomimimo.com/v1） |
| Reasonix | v1.2.0，同OpenClaw的sk-* key，base_url=api.xiaomimimo.com/v1 |
| 搜索引擎 | Tavily（主要），MiMo web search（备用，上限9元） |
| Tavily Key | `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` |
| 搜索预警 | MiMo用量到8元预警 |

### 平台连接
| 平台 | 状态 |
|------|------|
| WeChat (iLink) | ✅ Connected（home: o9cq800ir9-kY0mBT4lKLgIvl4bI@im.wechat） |
| QQ Bot | ✅ Connected（home: 78E4A633E622D2ED9D001D6F7BE3DCFA） |
| HF API | ❌ 全站被墙，替代：ModelScope/豆包MCP |

### 服务管理
```bash
# 重启 second profile
hermes gateway stop --profile second && hermes gateway start --profile second
# 重启 default profile（已禁用）
hermes gateway stop --profile default && hermes gateway start --profile default
# 查看状态
hermes gateway status --profile second
```

### 速率限制注意事项
- 微信 iLink API 有速率限制（`rate limited`），消息过多会触发
- 配置了微信发送延迟和重试参数
- 多Hermes进程不要同时连接同一微信账号

---

## 4. 竞赛项目清单

### 截止日期
| 竞赛 | 报名截止 | 提交截止 | 状态 |
|------|---------|---------|------|
| 数字分身 | — | 6/20 | ⏰ 紧急 |
| 软件杯 | — | 6/30 15:00 | ⏳ |
| 东方之星(ogdcn.com) | — | 6/30 | ⏳，A3展板JPG或MP4≤5min≤100MB |
| 3D大赛(ds.3ddl.net) | 6/30 | 7/20 | ⏳，报名需小程序"3D大赛" |
| 广西AI教育大赛 | — | 8/28 | ✅ 有余裕 |

### 8个比赛项目（均已做基础UI优化，5个做了taste-skill深度重构）

| # | 项目 | 目录 | 深度重构 |
|---|------|------|---------|
| 1 | 圆明园V3（主力） | `yuanmingyuan-3d/v3/` | ✅ commit 6ce87fe |
| 2 | 马栏山杯AIGC | `ncda-malanshan/` | ✅ |
| 3 | AIGC生态城市 | `ncda-aigc-eco-city/` | ✅ |
| 4 | AIGC参赛 | `ncda-aigc-entry/` | ✅ |
| 5 | AI教育Agent | `ai-education-agent/` | ✅ |
| 6 | A5景区导览 | `ncda-a5-scenic-guide/` | ✅ |
| 7 | 圆明园NCDA | `ncda-yuanmingyuan-entry/` | ❌ 基础优化 |
| 8 | 咕噜比/马栏山AIGC | — | 6个SVG已创建 |

### 提交材料标准清单（每个项目都需要）
1. README.md
2. design_report.md
3. AIGC使用声明（HTML页脚）
4. 无障碍支持（skip-nav+ARIA+键盘导航）
5. 作者/学校信息
6. 代码docx/pdf（每行行号5位右对齐灰色Courier）
7. 金色=#FFD700禁#E8A800
8. 优先级：文档/AIGC/无障碍 > 移动端适配和演示视频

---

## 5. 圆明园V3项目详情

### GitHub
- 仓库：`https://github.com/PoeticAlps/yuanmingyuan-3d.git`
- 分支：main
- 最新commit：`6ce87fe`（refactor: taste-skill审计重构）
- 回滚commit：`b66f7e1`（pre-refactor）
- ⚠️ 远程URL变更：旧`yuanmingyuan-3d.git`→新`--3d.git`

### 关键文件
| 文件 | 说明 |
|------|------|
| `v3/index.html` | 主展示页（Three.js，纯前端无依赖） |
| `v3/logo.svg` | 金色水墨风SVG logo |
| `v3/ico.jpg` | 大水法logo大图 |
| `output/yuanmingyuan_enhanced.glb` | 主场景模型（7.7MB） |
| `output/dashuifa_zodiac_ultra.glb` | 大水法生肖兽首模型（3.5MB） |
| `output/626K.glb` | 轻量模型 |
| `scripts/render_cinematic.py` | 影视级渲染脚本（783行） |
| `scripts/render_quality_upgrade.py` | 渲染质量升级脚本 |
| `render_dashuifa_competition.py` | 竞赛渲染脚本（261行） |
| `src/blender_scripts/build_scene_ultra.py` | 超精细场景构建（712行） |
| `data/raw/images/` | 31张参考图 |
| `REDESIGN-PLAN.md` | taste-skill重构计划 |

### 本地服务
```bash
cd ~/Desktop/"WX hermes workspace"/yuanmingyuan-3d/v3 && python3 -m http.server 8766
```

### V3已实现功能
- 金色渐变logo（SVG）+ 点击放大modal
- 8种历史树种（松/柳/槲/落叶松/竹/梅/紫藤/灌木）加权随机
- 6处牡丹花圃 + 20朵荷花水面散布
- 8种屋顶材质（黄琉璃/灰瓦/绿琉璃/深褐/红/蓝/黑/青）
- 官式建筑等级屋顶（歇山顶/庑殿顶/攒尖顶）几何函数
- Pandora魔盒加载动效（CSS 3D perspective）
- 细线流光动效（800ms 3阶段）
- Escape键+点击外部关闭面板
- taste-skill重构（z-index变量、px→rem/clamp、去居中化）

### taste-skill 配置
- VARIANCE: 7 / MOTION: 5 / DENSITY: 3（遗产项目需呼吸感）
- z-index CSS变量：`--z-base:10; --z-panel:100; --z-overlay:500; --z-modal:900; --z-toast:1000; --z-tooltip:1100; --z-loading:2000`
- 流光颜色：base `#DCD3BF`，head `#8B6E3E`，mid `#B89F7A`，tail→`#DCD3BF`

### 未完成项
- ⚠️ **高质量渲染未成功** — Mac Metal GPU驱动报错，CPU渲染超时
- ⚠️ **屋顶精细化** — 距竞赛标准仍有差距
- ⚠️ **竞赛材料未制作** — 演示视频、提交文档

---

## 6. 工具安装状态

### 已安装
| 工具 | 版本 | 状态 |
|------|------|------|
| Blender | 5.1.1 | ✅ |
| Rust | 1.96.0 | ✅ |
| Tauri CLI | v1.6.6 | ✅ |
| Headroom | v0.22.4 | ✅ |
| Clawd on Desk | v0.9.0 | ✅ |
| OpenDataLoader PDF | v2.4.7 | ✅ |
| OMO | — | ✅ |
| Codex CLI | @openai/codex | ✅（但需翻墙，实际不可用） |
| Reasonix | v1.2.0 | ✅ |
| EasyHermes | — | ⚠️ 已下载未运行（运行会杀Gateway） |

### 已卸载
| 工具 | 说明 |
|------|------|
| OpenClaw | 已完全卸载npm包+LaunchAgent，数据目录保留 |
| QQ Hermes代理 | 已停止+移除LaunchAgent，会话已导出 |

### 未安装/失败
| 工具 | 原因 |
|------|------|
| Headroom | Python 3.14版本过高导致安装失败（后来成功装v0.22.4） |
| HF全站 | 国内被墙 |

### 已安装技能（13个taste-skill相关）
taste-skill, ui-ux-pro-max, redesign-skill, visual-intelligence, skill-vetter等已安装到skills目录。

---

## 7. 文件组织历史

### 5/27 桌面workspace整理
- `agent 工作区` 下创建7个分类：RAG/finance/medical/hermes/3d/tools/web/other
- 移动32个项目到对应目录，仅移动不删除
- RAG项目识别：7个官方开源 + 10个自建学习项目

### 6/10 配置备份
- 全量备份到 `~/Desktop/hermes-config-backup/`
- 包含：config.yaml、.env、auth.json、state.db(941MB)、sessions/、logs/、memories/

### 6/10 QQ会话导出
- `qq_hermes_sessions_export.jsonl`（165会话、8157条消息、20.5MB）

---

## 8. 关键技术知识

### Blender 5.1.1 API 陷阱
- Voronoi纹理输出：`'Distance'`（非`'Fac'`）
- 材质字典键：`'red_pillar'`（非`'vermilion'`）
- 渲染设置：移除`use_denoising_passes`
- AgX Look：`'AgX - High Contrast'`（非`'High Contrast'`）
- Compositor：`scene.node_tree`不存在，需先`scene.use_nodes = True`
- World：`bpy.context.world`可能为None，需先创建
- 命令行路径：`/Applications/Blender.app/Contents/Resources/5.1/Blender.app/Contents/MacOS/Blender --background --python script.py`

### Blender渲染配置
- 引擎='BLENDER_EEVEE'
- ACES不稳→用AgX
- color_ramp用`elements.new(pos)`非float索引
- 渲染要求：AgX色彩+位移/法线/AO三重+体积云雾，512采样+双降噪
- 水体：菲涅尔+动态波纹+泡沫

### 截屏流程
1. `caffeinate -u -t 2` 唤醒屏幕
2. 按空格键唤醒
3. 检查前台应用，如果不是Finder则激活Finder并点击桌面
4. 截屏发给用户

### 常用Git操作
```bash
cd ~/Desktop/"WX hermes workspace"/yuanmingyuan-3d
git add -A
git commit -m "描述"
git push origin main
# 回滚
git reset --hard b66f7e1
```

---

## 9. 待办/未完成

### 紧急（6/20前）
- 数字分身比赛提交

### 短期（6/30前）
- 软件杯提交（15:00截止）
- 东方之星提交（A3展板JPG或MP4≤5min≤100MB）
- 3D大赛报名（小程序"3D大赛"）

### 中期（7/20前）
- 3D大赛作品提交
- 圆明园V3高质量渲染完成
- 竞赛材料制作（演示视频、文档）

### 长期（8/28前）
- 广西AI教育大赛

### 技术债务
- 圆明园渲染GPU Metal错误未解决
- 屋顶精细化建模未达竞赛标准
- Tauri桌面应用（说关机→10min后自动关机）未实现
- OpenClaw QQ Bot配置（版本冲突导致失败后卸载）
- 6个比赛项目中的2个（圆明园NCDA、咕噜比）未做taste-skill深度重构

---

## 10. 跨Hermes协作

### 双实例管理
- **second profile（本实例）**：主力，WeChat + QQ Bot
- **default profile（老大）**：已禁用自动启动
- 两实例曾同时连接微信导致冲突，已解决
- 用户期望AI多实例协作完成复杂任务
- 用户明确表示"另一个hermes不能正常使用"时应主动排查并修复

### 文件同步
- `~/Desktop/WX hermes workspace/yuanmingyuan-3d/` ↔ `~/Desktop/学校/圆明园v3/`
- 两处必须保持同步
