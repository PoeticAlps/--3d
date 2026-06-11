"""
圆明园AI重建模块 - 下载TripoSR模型

TripoSR: Stability AI的单图→3D重建模型
GitHub: https://github.com/VAST-AI-Research/TripoSR
"""

import os
import sys
from pathlib import Path

def download_model():
    """下载TripoSR预训练模型"""
    
    print("=" * 60)
    print("🏛️ 圆明园数字重建 - 下载AI模型")
    print("=" * 60)
    
    # 模型保存路径
    model_dir = Path("models/triposr")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n模型将保存到: {model_dir.absolute()}")
    
    # 检查依赖
    try:
        import torch
        print(f"✓ PyTorch: {torch.__version__}")
    except ImportError:
        print("✗ PyTorch未安装，请先运行: pip install torch torchvision")
        sys.exit(1)
    
    # 方法1: 使用官方仓库克隆
    print("\n📦 方法1: 从GitHub克隆TripoSR")
    print("请执行以下命令:")
    print("-" * 40)
    print(f"cd {model_dir.parent.absolute()}")
    print("git clone https://github.com/VAST-AI-Research/TripoSR.git")
    print("cd TripoSR")
    print("pip install -r requirements.txt")
    print("-" * 40)
    
    # 方法2: 使用Meshy API（在线服务，无需本地GPU）
    print("\n📦 方法2: 使用Meshy AI API（推荐，无需GPU）")
    print("访问: https://www.meshy.ai")
    print("注册后可免费生成3D模型")
    
    return model_dir

if __name__ == "__main__":
    model_dir = download_model()
    print(f"\n✅ 模型目录已创建: {model_dir}")
