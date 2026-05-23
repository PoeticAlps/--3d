"""
圆明园数字重建 - FastAPI后端

API服务，提供3D模型和场景数据给前端Three.js
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import shutil
import os

# ============================================================
# 配置
# ============================================================

app = FastAPI(
    title="重生·圆明园 API",
    description="圆明园数字重建项目API服务",
    version="1.0.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
MODELS_DIR = BASE_DIR / "data" / "processed" / "models"
STATIC_DIR = BASE_DIR / "output"

# 确保目录存在
MODELS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ============================================================
# 数据模型
# ============================================================

class SceneInfo(BaseModel):
    """景区信息"""
    id: str
    name: str
    name_en: str
    description: str
    position: dict
    model_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class ProjectInfo(BaseModel):
    """项目信息"""
    title: str
    description: str
    scenes: List[SceneInfo]

class RebuildRequest(BaseModel):
    """重建请求"""
    scene_id: str
    image_url: Optional[str] = None
    prompt: Optional[str] = None


# ============================================================
# 景区数据
# ============================================================

SCENES_DATA = {
    "dashuifa": {
        "id": "dashuifa",
        "name": "大水法",
        "name_en": "Dashuifa (Grand Fountain)",
        "description": "西洋楼景区的核心建筑，建于乾隆年间，由意大利传教士郎世宁参与设计。1860年被英法联军焚毁，现仅存石柱残垣。",
        "position": {"x": 0, "y": 0, "z": 0},
        "history": "建于1747年，是圆明园中最著名的西洋建筑群",
        "tags": ["西洋楼", "巴洛克", "喷泉", "遗址"]
    },
    "jiuzhouqingyan": {
        "id": "jiuzhouqingyan",
        "name": "九州清晏",
        "name_en": "Jiuzhou Qingyan",
        "description": "圆明园四十景之一，位于后湖中心，由九个人工岛组成，象征华夏九州。是皇帝居住和理政的主要场所。",
        "position": {"x": 200, "y": 0, "z": 0},
        "history": "始建于康熙年间，后经雍正、乾隆扩建",
        "tags": ["核心景区", "岛屿", "皇家寝宫", "后湖"]
    },
    "fangpuxianjing": {
        "id": "fangpuxianjing",
        "name": "方壶胜境",
        "name_en": "Fangpu Xianjing",
        "description": "圆明园四十景之一，仿古代神仙仙境而建，建筑群矗立于水面之上，宛如传说中的蓬莱仙境。",
        "position": {"x": 0, "y": 200, "z": 0},
        "history": "建于乾隆年间，是圆明园最美的景区之一",
        "tags": ["仙境", "湖上建筑", "道家", "园林"]
    },
    "zhengdaguangming": {
        "id": "zhengdaguangming",
        "name": "正大光明",
        "name_en": "Zhengda Guangming",
        "description": "圆明园四十景之一，是圆明园的正殿，皇帝举行朝会和接见外使的场所。匾额为雍正帝亲题。",
        "position": {"x": -200, "y": 0, "z": 0},
        "history": "建于雍正年间，是圆明园的政治中心",
        "tags": ["正殿", "朝政", "雍正", "牌匾"]
    }
}


# ============================================================
# API路由
# ============================================================

@app.get("/")
async def root():
    """API根路径"""
    return {
        "title": "重生·圆明园 API",
        "version": "1.0.0",
        "description": "圆明园数字重建项目API服务"
    }


@app.get("/api/project", response_model=ProjectInfo)
async def get_project():
    """获取项目信息"""
    scenes = [SceneInfo(**data) for data in SCENES_DATA.values()]
    return ProjectInfo(
        title="重生·圆明园",
        description="AI驱动的圆明园数字重建与沉浸式体验平台",
        scenes=scenes
    )


@app.get("/api/scenes", response_model=List[SceneInfo])
async def get_scenes():
    """获取所有景区列表"""
    return [SceneInfo(**data) for data in SCENES_DATA.values()]


@app.get("/api/scenes/{scene_id}", response_model=SceneInfo)
async def get_scene(scene_id: str):
    """获取单个景区详情"""
    if scene_id not in SCENES_DATA:
        raise HTTPException(status_code=404, detail="景区不存在")
    return SceneInfo(**SCENES_DATA[scene_id])


@app.get("/api/scenes/{scene_id}/model")
async def get_scene_model(scene_id: str):
    """获取景区3D模型"""
    model_path = MODELS_DIR / f"{scene_id}.glb"
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="模型文件不存在")
    
    return {
        "scene_id": scene_id,
        "model_url": f"/static/models/{scene_id}.glb",
        "file_size": model_path.stat().st_size
    }


@app.post("/api/rebuild")
async def rebuild_scene(request: RebuildRequest):
    """
    触发AI重建
    
    支持两种方式:
    1. 上传图片重建
    2. 文字描述生成
    """
    scene_id = request.scene_id
    
    if not request.image_url and not request.prompt:
        raise HTTPException(
            status_code=400,
            detail="需要提供图片URL或文字描述"
        )
    
    # TODO: 调用Meshy API或TripoSR
    # 这里返回模拟响应
    
    return {
        "status": "processing",
        "scene_id": scene_id,
        "message": "重建任务已提交，请稍后查看结果",
        "task_id": f"task_{scene_id}_001"
    }


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """上传图片"""
    upload_dir = STATIC_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    return {
        "filename": file.filename,
        "url": f"/static/uploads/{file.filename}",
        "size": file_path.stat().st_size
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "models_dir": str(MODELS_DIR),
        "models_count": len(list(MODELS_DIR.glob("*.glb")))
    }


# ============================================================
# 启动服务
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🏛️ 圆明园数字重建 API服务")
    print("=" * 60)
    print(f"📁 模型目录: {MODELS_DIR}")
    print(f"🌐 API文档: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
