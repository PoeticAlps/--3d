"""
Meshy AI API - 图片转3D模型

使用Meshy API将圆明园四十景图转换为3D模型
文档: https://docs.meshy.ai/api

使用前需要在 https://www.meshy.ai 注册并获取API Key
"""

import os
import time
import requests
from pathlib import Path
from typing import Optional

class MeshyAPI:
    """Meshy AI API客户端"""
    
    BASE_URL = "https://api.meshy.ai/v2"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def image_to_3d(
        self,
        image_path: str,
        prompt: str = "Chinese traditional architecture, Yuanmingyuan palace",
        ai_model: str = "meshy-4",
        topology: str = "triangle",
        target_polycount: int = 30000
    ) -> dict:
        """
        从图片生成3D模型
        
        Args:
            image_path: 输入图片路径
            prompt: 描述提示词
            ai_model: AI模型版本
            topology: 网格类型
            target_polycount: 目标面数
            
        Returns:
            任务信息
        """
        # 上传图片
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # 创建任务
        url = f"{self.BASE_URL}/image-to-3d"
        
        # 如果是本地文件，先base64编码
        import base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        payload = {
            "image": f"data:image/jpeg;base64,{image_base64}",
            "prompt": prompt,
            "ai_model": ai_model,
            "topology": topology,
            "target_polycount": target_polycount
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        task = response.json()
        print(f"✓ 任务已创建: {task.get('id')}")
        return task
    
    def text_to_3d(
        self,
        prompt: str,
        ai_model: str = "meshy-4",
        topology: str = "triangle",
        target_polycount: int = 30000
    ) -> dict:
        """
        从文字描述生成3D模型
        
        Args:
            prompt: 文字描述
            ai_model: AI模型版本
            topology: 网格类型
            target_polycount: 目标面数
        """
        url = f"{self.BASE_URL}/text-to-3d"
        
        payload = {
            "prompt": prompt,
            "ai_model": ai_model,
            "topology": topology,
            "target_polycount": target_polycount
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        task = response.json()
        print(f"✓ 任务已创建: {task.get('id')}")
        return task
    
    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        url = f"{self.BASE_URL}/image-to-3d/{task_id}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 10,
        max_wait: int = 600
    ) -> dict:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            max_wait: 最大等待时间（秒）
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            task = self.get_task_status(task_id)
            status = task.get("status")
            
            if status == "succeeded":
                print(f"✓ 任务完成!")
                return task
            elif status == "failed":
                raise Exception(f"任务失败: {task.get('error')}")
            else:
                elapsed = int(time.time() - start_time)
                print(f"⏳ 处理中... ({elapsed}s)", end="\r")
                time.sleep(poll_interval)
        
        raise TimeoutError(f"任务超时: {max_wait}秒")
    
    def download_model(self, task_id: str, output_path: str) -> str:
        """下载生成的3D模型"""
        task = self.get_task_status(task_id)
        
        model_url = task.get("model_urls", {}).get("glb")
        if not model_url:
            raise ValueError("未找到模型下载链接")
        
        response = requests.get(model_url)
        response.raise_for_status()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"✓ 模型已保存: {output_path}")
        return output_path


def rebuild_yuanmingyuan_scenes():
    """
    重建圆明园主要景区
    
    重点景区:
    1. 大水法 - 西洋楼标志性建筑
    2. 九州清晏 - 后湖核心景区
    3. 方壶胜境 - 仙境主题
    """
    
    # 从环境变量获取API Key
    api_key = os.getenv("MESHY_API_KEY", "your_meshy_api_key_here")
    
    if api_key == "your_meshy_api_key_here":
        print("⚠️ 请设置MESHY_API_KEY环境变量")
        print("   export MESHY_API_KEY=your_key")
        print("   获取地址: https://www.meshy.ai/settings/api")
        return
    
    client = MeshyAPI(api_key)
    
    # 重点景区配置
    scenes = {
        "dashuifa": {
            "name": "大水法",
            "prompt": "Qing dynasty European style fountain ruins, Yuanmingyuan Old Summer Palace, Baroque architecture columns and arches, historical Chinese imperial garden",
            "image": "data/raw/images/dashuifa.jpg"
        },
        "jiuzhouqingyan": {
            "name": "九州清晏",
            "prompt": "Traditional Chinese imperial palace complex on lake island, Yuanmingyuan Old Summer Palace, ornate roof tiles, red pillars, white marble terraces",
            "image": "data/raw/images/jiuzhouqingyan.jpg"
        },
        "fangpuxianjing": {
            "name": "方壶胜境",
            "prompt": "Chinese fairyland palace on water, Yuanmingyuan Old Summer Palace, ethereal architecture, golden roofs, misty atmosphere",
            "image": "data/raw/images/fangpuxianjing.jpg"
        },
        "zhengdaguangming": {
            "name": "正大光明",
            "prompt": "Main imperial throne hall, Qing dynasty Chinese architecture, Yuanmingyuan Old Summer Palace, grand palace with dragon motifs",
            "image": "data/raw/images/zhengdaguangming.jpg"
        }
    }
    
    output_dir = Path("data/processed/models")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🏛️ 圆明园AI重建 - Meshy API")
    print("=" * 60)
    
    for scene_id, config in scenes.items():
        print(f"\n📐 重建景区: {config['name']}")
        
        try:
            # 如果有图片，使用图生3D
            if os.path.exists(config["image"]):
                print(f"  输入图片: {config['image']}")
                task = client.image_to_3d(
                    image_path=config["image"],
                    prompt=config["prompt"]
                )
            else:
                # 否则使用文生3D
                print(f"  使用文字描述生成...")
                task = client.text_to_3d(prompt=config["prompt"])
            
            task_id = task.get("id")
            
            # 等待完成
            result = client.wait_for_completion(task_id)
            
            # 下载模型
            output_path = str(output_dir / f"{scene_id}.glb")
            client.download_model(task_id, output_path)
            
            print(f"  ✅ {config['name']} 重建完成!")
            
        except Exception as e:
            print(f"  ❌ {config['name']} 重建失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 全部景区重建完成!")
    print(f"📁 模型保存在: {output_dir.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    rebuild_yuanmingyuan_scenes()
