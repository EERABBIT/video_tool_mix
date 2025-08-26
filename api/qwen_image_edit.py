#!/usr/bin/env python3
"""
通义千问图片编辑模型调用脚本
支持基于文本指令编辑图片
"""

import os
import time
import base64
import requests
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

class QwenImageEditAPI:
    """通义千问图片编辑API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required. Please set DASHSCOPE_API_KEY in .env file")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.model = "qwen-image-edit"
        self.output_dir = Path("./output/image_edit")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _encode_image_to_url(self, image_path: str) -> str:
        """将本地图片转换为base64 data URL"""
        import mimetypes
        
        file_path = Path(image_path)
        if not file_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 检测MIME类型
        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        
        with open(image_path, 'rb') as f:
            content = f.read()
            base64_str = base64.b64encode(content).decode('utf-8')
            return f"data:{mime_type};base64,{base64_str}"
    
    async def edit_image(
        self,
        image_path: str,
        edit_instruction: str,
        negative_prompt: Optional[str] = None,
        watermark: bool = False
    ) -> Dict[str, Any]:
        """
        编辑图片
        
        Args:
            image_path: 原始图片路径
            edit_instruction: 编辑指令文本
            negative_prompt: 负向提示词
            watermark: 是否添加水印
        """
        print(f"\n{'='*60}")
        print(f"🎨 开始图片编辑任务")
        print(f"{'='*60}")
        print(f"📷 原图: {image_path}")
        print(f"📝 编辑指令: {edit_instruction}")
        print(f"🚫 负向提示: {negative_prompt or '无'}")
        print(f"🖼️ 水印: {'是' if watermark else '否'}")
        
        try:
            # 1. 编码图片
            print(f"\n🔧 步骤1: 处理输入图片...")
            if image_path.startswith(('http://', 'https://')):
                image_url = image_path
                print(f"  ✅ 使用网络图片: {image_url}")
            else:
                image_url = self._encode_image_to_url(image_path)
                print(f"  ✅ 转换本地图片为base64格式")
            
            # 2. 构建请求
            print(f"\n🔧 步骤2: 构建API请求...")
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            request_body = {
                "model": self.model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"image": image_url},
                                {"text": edit_instruction}
                            ]
                        }
                    ]
                },
                "parameters": {
                    "watermark": watermark
                }
            }
            
            if negative_prompt:
                request_body["parameters"]["negative_prompt"] = negative_prompt
            
            print(f"  📦 模型: {self.model}")
            print(f"  🌐 API端点: {self.base_url}/services/aigc/multimodal-generation/generation")
            
            # 3. 提交请求
            print(f"\n🔧 步骤3: 提交编辑请求...")
            url = f"{self.base_url}/services/aigc/multimodal-generation/generation"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=120)  # 2分钟超时
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        print(f"  ❌ 请求失败: HTTP {response.status}")
                        print(f"  错误响应: {response_text}")
                        return {"status": "error", "error": f"API错误 {response.status}: {response_text}"}
                    
                    import json
                    data = json.loads(response_text)
                    
                    print(f"  ✅ 请求成功")
                    
                    # 4. 解析响应
                    if "output" in data and "choices" in data["output"]:
                        choices = data["output"]["choices"]
                        if choices and "message" in choices[0]:
                            content = choices[0]["message"]["content"]
                            
                            # 查找图片URL
                            image_url = None
                            for item in content:
                                if "image" in item:
                                    image_url = item["image"]
                                    break
                            
                            if image_url:
                                print(f"\n🔧 步骤4: 下载编辑后的图片...")
                                
                                # 生成输出文件名
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                output_filename = f"edited_{timestamp}.png"
                                output_path = self.output_dir / output_filename
                                
                                # 下载图片
                                success = await self._download_image(image_url, output_path)
                                
                                if success:
                                    # 获取图片信息
                                    usage = data.get("usage", {})
                                    width = usage.get("width", 0)
                                    height = usage.get("height", 0)
                                    
                                    print(f"\n{'='*60}")
                                    print(f"🎉 图片编辑成功!")
                                    print(f"  📁 本地文件: {output_path}")
                                    print(f"  📐 分辨率: {width}×{height}")
                                    print(f"  🆔 请求ID: {data.get('request_id')}")
                                    print(f"{'='*60}")
                                    
                                    return {
                                        "status": "success",
                                        "image_url": image_url,
                                        "local_path": str(output_path),
                                        "width": width,
                                        "height": height,
                                        "request_id": data.get("request_id")
                                    }
                                else:
                                    return {"status": "error", "error": "图片下载失败"}
                            else:
                                print(f"  ❌ 响应中未找到图片URL")
                                return {"status": "error", "error": "响应中未找到图片"}
                    
                    print(f"  ❌ 响应格式异常: {data}")
                    return {"status": "error", "error": f"响应格式异常: {data}"}
                    
        except asyncio.TimeoutError:
            print(f"\n  ❌ 请求超时")
            return {"status": "error", "error": "请求超时"}
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            import traceback
            print(f"📍 错误详情: {traceback.format_exc()}")
            return {"status": "error", "error": str(e)}
    
    async def _download_image(self, image_url: str, output_path: Path) -> bool:
        """下载生成的图片"""
        try:
            print(f"  📥 下载URL: {image_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    image_url,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        print(f"  ❌ 下载失败: HTTP {response.status}")
                        return False
                    
                    content = await response.read()
                    
                    async with aiofiles.open(output_path, 'wb') as f:
                        await f.write(content)
                    
                    file_size = len(content) / 1024 / 1024
                    print(f"  ✅ 下载完成: {file_size:.2f} MB")
                    return True
                    
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return False


if __name__ == "__main__":
    # 简单的测试示例
    async def simple_test():
        api = QwenImageEditAPI()
        print("通义千问图片编辑API已准备就绪")
        print("使用方法:")
        print("  result = await api.edit_image(")
        print("      image_path='your_image.jpg',")
        print("      edit_instruction='编辑指令',")
        print("      negative_prompt='负向提示词（可选）',")
        print("      watermark=False")
        print("  )")
    
    asyncio.run(simple_test())