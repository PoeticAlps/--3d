#!/bin/bash
# ============================================================
# 圆明园数字重建 - 项目初始化脚本
# ============================================================

set -e

echo "============================================================"
echo "🏛️ 重生·圆明园 - 项目初始化"
echo "============================================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数
info() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. 检查Python
echo ""
echo "📦 检查环境..."

if command -v python3 &> /dev/null; then
    info "Python3 已安装: $(python3 --version)"
else
    echo "❌ Python3 未安装"
    exit 1
fi

# 2. 创建虚拟环境
echo ""
echo "🐍 创建Python虚拟环境..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
    info "虚拟环境已创建"
else
    info "虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate
info "虚拟环境已激活"

# 3. 安装依赖
echo ""
echo "📚 安装Python依赖..."

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
info "依赖安装完成"

# 4. 复制环境配置
echo ""
echo "⚙️ 配置环境变量..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    info "已创建 .env 文件，请填入API密钥"
    warn "需要设置 MESHY_API_KEY"
else
    info ".env 文件已存在"
fi

# 5. 初始化前端
echo ""
echo "🌐 初始化前端..."

if [ -d "src/frontend" ]; then
    cd src/frontend
    if command -v npm &> /dev/null; then
        npm install
        info "前端依赖安装完成"
    else
        warn "npm 未安装，跳过前端依赖安装"
    fi
    cd ../..
fi

# 6. 创建必要目录
echo ""
echo "📁 创建目录..."

mkdir -p data/raw/images
mkdir -p data/raw/references
mkdir -p data/processed/models
mkdir -p data/processed/textures
mkdir -p output
info "目录创建完成"

# 7. 初始化Git仓库
echo ""
echo "📝 初始化Git仓库..."

if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "init: 项目初始化" > /dev/null 2>&1
    info "Git仓库已初始化"
else
    info "Git仓库已存在"
fi

# 8. 完成
echo ""
echo "============================================================"
echo -e "${GREEN}✅ 项目初始化完成!${NC}"
echo "============================================================"
echo ""
echo "下一步:"
echo "  1. 编辑 .env 文件，设置 MESHY_API_KEY"
echo "  2. 运行: python src/ai_rebuild/meshy_api.py"
echo "  3. 运行: blender --background --python src/blender_scripts/assemble.py"
echo "  4. 运行: uvicorn src.backend.main:app --reload"
echo "  5. 运行: cd src/frontend && npm run dev"
echo ""
