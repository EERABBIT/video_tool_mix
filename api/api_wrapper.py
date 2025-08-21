#!/usr/bin/env python3
"""
API包装器 - 为所有API提供统一的接口
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

class APIWrapper:
    """API包装器基类"""
    
    def __init__(self, api_instance):
        self.api = api_instance
    
    async def generate(self, **kwargs) -> str:
        """统一的生成接口"""
        raise NotImplementedError

class TextToImageWrapper(APIWrapper):
    """文生图API包装器"""
    
    async def generate(self, prompt: str, negative_prompt: str = "", **kwargs) -> str:
        """生成图片"""
        # 调用_submit_generation_task方法
        request_body = {
            "model": self.api.model,
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "size": kwargs.get("size", "1920*1080"),
                "n": kwargs.get("n", 1),
                "style": kwargs.get("style", "auto")
            }
        }
        
        # 提交任务
        async with aiohttp.session.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api.api_key}",
                "Content-Type": "application/json"
            }
            
            async with session.post(
                f"{self.api.base_url}/services/aigc/text2image/wan2-text2image",
                headers=headers,
                json=request_body
            ) as response:
                result = await response.json()
                
                if response.status != 200:
                    raise Exception(f"API请求失败: {result}")
                
                task_id = result.get("request_id")
                if not task_id:
                    raise Exception(f"未获取到任务ID: {result}")
        
        # 轮询结果
        while True:
            await asyncio.sleep(2)
            
            async with session.get(
                f"{self.api.base_url}/tasks/{task_id}",
                headers=headers
            ) as response:
                task_info = await response.json()
                
                status = task_info.get("task_status")
                
                if status == "SUCCEEDED":
                    # 获取图片URL
                    images = task_info.get("output", {}).get("images", [])
                    if images:
                        image_url = images[0].get("url")
                        
                        # 下载并保存图片
                        output_path = self.api.output_dir / f"t2i_{task_id}.png"
                        await self.api._download_image(image_url, output_path)
                        
                        return str(output_path)
                    else:
                        raise Exception("生成成功但没有图片")
                
                elif status == "FAILED":
                    raise Exception(f"任务失败: {task_info.get('task_metrics', {}).get('FAILED', 'Unknown error')}")
                
                elif status in ["PENDING", "RUNNING"]:
                    continue
                else:
                    raise Exception(f"未知任务状态: {status}")

class ImageToVideoWrapper(APIWrapper):
    """图生视频API包装器"""
    
    async def generate(self, image_path: str, prompt: str = "", **kwargs) -> str:
        """生成视频"""
        return await self.api.generate_video(image_path, prompt)

class TextToVideoWrapper(APIWrapper):
    """文生视频API包装器"""
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成视频"""
        return await self.api.generate_text_to_video(prompt)

class KeyframeVideoWrapper(APIWrapper):
    """首尾帧视频API包装器"""
    
    async def generate(self, first_frame: str, last_frame: str, prompt: str = "", **kwargs) -> str:
        """生成视频"""
        return await self.api.generate_keyframe_video(first_frame, last_frame, prompt)

class ImageEditWrapper(APIWrapper):
    """图片编辑API包装器"""
    
    async def generate(self, image_path: str, instruction: str, **kwargs) -> str:
        """编辑图片"""
        return await self.api.edit_image(image_path, instruction)