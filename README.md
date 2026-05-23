# 🏛️ 重生·圆明园 — AI驱动的数字文化遗产3D重建

> 2026第19届全国3D大赛 参赛作品

## 项目简介

利用AI技术从《圆明园四十景图》等历史资料中重建圆明园三维数字模型，通过Web3D技术实现沉浸式浏览体验。

## 核心功能

- 🤖 AI图像→3D重建（TripoSR / Meshy）
- 🎨 AI纹理修复与增强
- 🌐 Web3D交互式展示（Three.js）
- 🥽 VR沉浸式漫游
- ⏰ 新旧对比时间轴

## 技术栈

| 模块 | 技术 |
|------|------|
| AI重建 | TripoSR / Meshy API |
| 3D建模 | Blender + Python |
| 后端 | FastAPI |
| 前端 | React + Three.js |
| 部署 | Docker |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载AI模型（TripoSR）
python src/ai_rebuild/download_model.py

# 3. 运行AI重建
python src/ai_rebuild/rebuild.py --input data/raw/images/ --output data/processed/models/

# 4. Blender场景组装
blender --background --python src/blender_scripts/assemble.py

# 5. 启动后端
uvicorn src.backend.main:app --reload

# 6. 启动前端
cd src/frontend && npm run dev
```

## 项目结构

```
yuanmingyuan-3d/
├── data/                    # 数据目录
│   ├── raw/images/         # 原始图片
│   ├── raw/references/     # 参考资料
│   └── processed/          # 处理后的模型
├── src/                     # 源代码
│   ├── ai_rebuild/         # AI重建模块
│   ├── blender_scripts/    # Blender脚本
│   ├── backend/            # FastAPI后端
│   └── frontend/           # React前端
├── configs/                 # 配置文件
├── docs/                    # 文档
└── output/                  # 输出文件
```

## 团队

- 项目负责人
- 3D建模师
- AI算法工程师
- 前端开发

## 许可

MIT License
