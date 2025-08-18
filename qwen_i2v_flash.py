#!/usr/bin/env python3
"""
通义万相2.2-图生视频-Flash模型调用脚本
"""

import asyncio
import json
import time
import base64
from pathlib import Path
from typing import Optional, Dict, Any
import aiohttp
import aiofiles

class QwenI2VFlashAPI:
    """通义万相2.2-图生视频-Flash模型API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "sk-c4af8d8ed01d43a587eda9b8c3b32058"
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.model = "wan2.2-i2v-flash"
        self.output_dir = Path("./output/i2v_flash")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _format_resolution(self, resolution: str) -> str:
        """格式化分辨率为API支持的格式"""
        # 支持的分辨率列表（根据错误信息更新，图生视频使用*格式）
        supported_resolutions = [
            "1280*720",    # 16:9 横屏 (默认)
            "1920*1080",   # 16:9 高清横屏
            "1440*1440",   # 1:1 正方形
            "1632*1248",   # 4:3 横屏
            "1248*1632",   # 3:4 竖屏
            "480*832",     # 9:16 小尺寸竖屏
            "832*480",     # 16:9 小尺寸横屏
            "624*624"      # 1:1 小尺寸正方形
        ]
        
        if not resolution:
            return "1280*720"  # 默认分辨率
        
        # 如果传入的是x格式，转换为*格式
        if 'x' in resolution:
            resolution = resolution.replace('x', '*')
        
        # 检查是否是支持的分辨率
        if resolution in supported_resolutions:
            return resolution
        
        # 如果不是支持的分辨率，返回最接近的
        print(f"⚠️ 分辨率 {resolution} 不被支持，使用默认分辨率 1280*720")
        print(f"💡 支持的分辨率: {', '.join(supported_resolutions)}")
        return "1280*720"
    
    async def generate_video(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        duration: int = 5,
        fps: int = 30,
        resolution: str = "1280*720"
    ) -> Dict[str, Any]:
        """
        图生视频
        
        Args:
            image_path: 输入图片路径
            prompt: 生成提示词
            negative_prompt: 负向提示词
            duration: 视频时长(秒)
            fps: 帧率
            resolution: 分辨率
        """
        print(f"🎬 开始图生视频任务...")
        print(f"📷 输入图片: {image_path}")
        print(f"⏱️ 视频时长: {duration}秒")
        print(f"📐 分辨率: {resolution}")
        
        try:
            print(f"🎬 开始图生视频任务...")
            print(f"📷 输入图片路径: {image_path}")
            print(f"📝 提示词: {prompt}")
            print(f"🚫 负向提示词: {negative_prompt}")
            print(f"⏱️ 视频时长: {duration}秒")
            print(f"📐 原始分辨率: {resolution}")
            
            print(f"🔍 开始编码图片: {image_path}")
            # 读取并编码图片
            image_base64 = await self._encode_image(image_path)
            print(f"✅ 图片编码完成，base64长度: {len(image_base64)}")
            
            # 检测图片格式
            import mimetypes
            from pathlib import Path
            
            file_ext = Path(image_path).suffix.lower()
            mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
            
            print(f"📄 图片文件扩展名: {file_ext}")
            print(f"🔍 检测到的MIME类型: {mime_type}")
            
            # 格式化分辨率
            formatted_resolution = self._format_resolution(resolution)
            print(f"📐 格式化后分辨率: {formatted_resolution}")
            
            # 构建请求体 - 使用正确的API参数结构
            request_body = {
                "model": self.model,
                "input": {
                    "prompt": prompt or "",
                    "img_url": f"data:{mime_type};base64,{image_base64}"
                },
                "parameters": {
                    "size": formatted_resolution
                }
            }
            
            if negative_prompt:
                request_body["input"]["negative_prompt"] = negative_prompt
                print(f"➕ 已添加负向提示词")
            
            print(f"📋 完整请求体结构:")
            print(f"  模型: {request_body['model']}")
            print(f"  提示词: {request_body['input']['prompt']}")
            print(f"  图片URL长度: {len(request_body['input']['img_url'])}")
            print(f"  分辨率: {request_body['parameters']['size']}")
            
            # 提交任务
            print(f"📤 开始提交任务...")
            task_id = await self._submit_task(request_body)
            print(f"✅ 任务提交成功，任务ID: {task_id}")
            
            # 轮询状态
            print(f"🔄 开始轮询任务状态...")
            result = await self._poll_task_status(task_id)
            print(f"📊 轮询结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 下载视频
            if result["status"] == "success" and result.get("video_url"):
                print(f"📥 开始下载视频...")
                timestamp = int(time.time())
                output_path = self.output_dir / f"i2v_flash_{timestamp}.mp4"
                await self._download_video(result["video_url"], output_path)
                result["local_path"] = str(output_path)
                print(f"✅ 视频已保存: {output_path}")
            else:
                print(f"⚠️ 未能获取视频URL或任务失败")
            
            return result
            
        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")
            print(f"🔍 异常类型: {type(e).__name__}")
            import traceback
            print(f"📍 完整错误堆栈: {traceback.format_exc()}")
            return {"status": "error", "error": str(e)}
    
    async def _encode_image(self, image_path: str) -> str:
        """将图片编码为base64"""
        from pathlib import Path
        
        file_path = Path(image_path)
        print(f"读取图片文件: {file_path}")
        print(f"文件存在: {file_path.exists()}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
        async with aiofiles.open(image_path, 'rb') as f:
            content = await f.read()
            print(f"读取文件内容，大小: {len(content)} 字节")
            return base64.b64encode(content).decode('utf-8')
    
    async def _submit_task(self, request_body: Dict) -> str:
        """提交生成任务"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }
        
        url = f"{self.base_url}/services/aigc/video-generation/video-synthesis"
        
        print(f"📤 发送请求到: {url}")
        print(f"📋 请求体大小: {len(json.dumps(request_body))} 字符")
        print(f"🔑 Authorization头: Bearer {self.api_key[:10]}...")
        print(f"📦 模型名称: {request_body['model']}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=request_body) as response:
                response_text = await response.text()
                
                print(f"📥 HTTP响应状态: {response.status}")
                print(f"📄 响应头: {dict(response.headers)}")
                print(f"📄 响应内容: {response_text}")
                
                if response.status != 200:
                    print(f"❌ API请求失败，状态码: {response.status}")
                    raise RuntimeError(f"API请求失败 ({response.status}): {response_text}")
                
                try:
                    data = json.loads(response_text)
                    print(f"✅ JSON解析成功")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    raise RuntimeError(f"响应JSON解析失败: {response_text}")
                
                if data.get("code") and data["code"] != "200":
                    print(f"❌ API返回错误代码: {data.get('code')}")
                    print(f"❌ 错误消息: {data.get('message', 'Unknown error')}")
                    raise RuntimeError(f"API错误: {data.get('message', 'Unknown error')}")
                
                task_id = data["output"]["task_id"]
                print(f"✅ 成功获取任务ID: {task_id}")
                return task_id
    
    async def _poll_task_status(self, task_id: str) -> Dict[str, Any]:
        """轮询任务状态"""
        max_polls = 180  # 最多轮询3分钟
        poll_interval = 2
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        url = f"{self.base_url}/tasks/{task_id}"
        print(f"🔄 轮询URL: {url}")
        
        async with aiohttp.ClientSession() as session:
            for i in range(max_polls):
                print(f"⏳ 轮询进度: {i+1}/{max_polls}...")
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        print(f"⚠️ 状态查询失败，HTTP状态: {response.status}")
                        await asyncio.sleep(poll_interval)
                        continue
                    
                    response_text = await response.text()
                    print(f"📊 轮询响应: {response_text}")
                    
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析失败: {e}")
                        await asyncio.sleep(poll_interval)
                        continue
                    
                    status = data["output"]["task_status"]
                    print(f"📈 任务状态: {status}")
                    
                    if status == "SUCCEEDED":
                        print("✅ 任务成功完成，解析结果...")
                        
                        # 优先检查 video_url 字段（新格式）
                        video_url = data["output"].get("video_url")
                        if video_url:
                            print(f"🎬 找到视频URL (直接格式): {video_url}")
                            return {
                                "status": "success",
                                "video_url": video_url,
                                "task_metrics": data["output"].get("task_metrics", {}),
                                "usage": data["output"].get("usage", {})
                            }
                        
                        # 兼容旧格式：检查 results 数组
                        results = data["output"].get("results")
                        if results and len(results) > 0:
                            video_url = results[0]["url"]
                            print(f"🎬 找到视频URL (results格式): {video_url}")
                            return {
                                "status": "success",
                                "video_url": video_url,
                                "task_metrics": data["output"].get("task_metrics", {}),
                                "usage": data["output"].get("usage", {})
                            }
                        
                        # 都没找到，输出详细调试信息
                        print(f"❌ 任务成功但未找到视频URL")
                        print(f"🔍 完整响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        raise RuntimeError(f"任务成功但未找到视频URL，响应: {json.dumps(data, ensure_ascii=False)}")
                    
                    elif status == "FAILED":
                        error_msg = data["output"].get("message", "Unknown error")
                        print(f"❌ 任务失败: {error_msg}")
                        raise RuntimeError(f"生成任务失败: {error_msg}")
                    
                    elif status in ["RUNNING", "PENDING"]:
                        progress = min(100, (i + 1) * 100 // 60)
                        print(f"  🔄 生成进度: {progress}% (状态: {status})")
                    
                    else:
                        print(f"  ❓ 未知状态: {status}")
                
                await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"视频生成超时 (任务ID: {task_id})")
    
    async def _download_video(self, video_url: str, output_path: Path):
        """下载生成的视频"""
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status != 200:
                    raise RuntimeError(f"视频下载失败 ({response.status})")
                
                content = await response.read()
                async with aiofiles.open(output_path, 'wb') as f:
                    await f.write(content)
                
                file_size = len(content) / 1024 / 1024
                print(f"  💾 视频大小: {file_size:.2f} MB")

async def test():
    """测试函数"""
    api = QwenI2VFlashAPI()
    
    # 测试图生视频
    result = await api.generate_video(
        image_path="./assets/images/卡通小猫.png",  # 需要准备测试图片
        prompt="让画面动起来，增加自然的动态效果",
        duration=5,
        fps=30,
        resolution="1280*720"
    )
    
    print(f"生成结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(test())