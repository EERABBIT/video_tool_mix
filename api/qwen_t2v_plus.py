#!/usr/bin/env python3
"""
通义万相2.2-文生视频-Plus模型调用脚本
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import aiohttp
import aiofiles

class QwenT2VPlusAPI:
    """通义万相2.2-文生视频-Plus模型API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required. Please set DASHSCOPE_API_KEY in .env file")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.model = "wan2.2-t2v-plus"
        self.output_dir = Path("./output/t2v_plus")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _format_resolution(self, resolution: str) -> str:
        """格式化分辨率为API支持的格式"""
        # 支持的分辨率列表（根据API错误信息精确更新）
        supported_resolutions = [
            "1080*1920",   # 9:16 竖屏
            "1920*1080",   # 16:9 横屏 (默认)
            "1440*1440",   # 1:1 正方形
            "1632*1248",   # 4:3 横屏
            "1248*1632",   # 3:4 竖屏
            "480*832",     # 9:16 小尺寸竖屏
            "832*480",     # 16:9 小尺寸横屏
            "624*624"      # 1:1 小尺寸正方形
        ]
        
        if not resolution:
            return "1920*1080"  # 默认分辨率
        
        # 如果传入的是x格式，转换为*格式
        if 'x' in resolution:
            resolution = resolution.replace('x', '*')
        
        # 检查是否是支持的分辨率
        if resolution in supported_resolutions:
            return resolution
        
        # 如果不是支持的分辨率，返回最接近的
        print(f"⚠️ 分辨率 {resolution} 不被支持，使用默认分辨率 1920*1080")
        print(f"💡 支持的分辨率: {', '.join(supported_resolutions)}")
        return "1920*1080"
    
    async def generate_text_to_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: int = 5,
        fps: int = 30,
        resolution: str = "1920*1080",
        style: str = "realistic",
        motion_strength: float = 0.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        文生视频
        
        Args:
            prompt: 生成提示词
            negative_prompt: 负向提示词
            duration: 视频时长(秒)，支持 3-10 秒
            fps: 帧率，支持 24/30 fps
            resolution: 分辨率，支持 1280*720, 1920*1080
            style: 风格，realistic/anime/cartoon
            motion_strength: 动作强度 0.1-1.0
            seed: 随机种子
        """
        print(f"🎬 开始文生视频任务...")
        print(f"📝 提示词: {prompt}")
        print(f"🚫 负向提示词: {negative_prompt}")
        print(f"⏱️ 视频时长: {duration}秒")
        print(f"🎞️ 帧率: {fps}fps")
        print(f"📐 原始分辨率: {resolution}")
        print(f"🎨 风格: {style}")
        print(f"🏃 动作强度: {motion_strength}")
        print(f"🎯 随机种子: {seed}")
        
        try:
            print(f"🔧 开始构建请求体...")
            
            # 格式化分辨率
            formatted_resolution = self._format_resolution(resolution)
            print(f"📐 格式化后分辨率: {formatted_resolution}")
            
            # 构建请求体 - 使用正确的参数结构
            request_body = {
                "model": self.model,
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "size": formatted_resolution,
                    "style": f"<{style}>" if style else "<auto>"
                }
            }
            
            if negative_prompt:
                request_body["input"]["negative_prompt"] = negative_prompt
                print(f"➕ 已添加负向提示词")
            
            if seed is not None:
                request_body["parameters"]["seed"] = seed
                print(f"🎯 已设置随机种子: {seed}")
            
            print(f"📋 完整请求体结构:")
            print(f"  模型: {request_body['model']}")
            print(f"  提示词: {request_body['input']['prompt']}")
            print(f"  分辨率: {request_body['parameters']['size']}")
            print(f"  风格: {request_body['parameters']['style']}")
            
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
                output_path = self.output_dir / f"t2v_plus_{timestamp}.mp4"
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
        print(f"📋 请求体: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        
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
        max_polls = 300  # 最多轮询10分钟（文生视频较复杂）
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
                        print(f"⚠️ 状态查询失败，继续重试...")
                        await asyncio.sleep(poll_interval)
                        continue
                    
                    response_text = await response.text()
                    data = json.loads(response_text)
                    
                    print(f"📊 轮询响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    status = data["output"]["task_status"]
                    print(f"📈 任务状态: {status}")
                    
                    if status == "SUCCEEDED":
                        # 处理成功结果 - 检查是否有 video_url 字段
                        video_url = data["output"].get("video_url")
                        if video_url:
                            print(f"✅ 任务成功完成，视频URL: {video_url}")
                            
                            return {
                                "status": "success",
                                "video_url": video_url,
                                "task_metrics": data["output"].get("task_metrics", {}),
                                "usage": data["output"].get("usage", {})
                            }
                        else:
                            # 兼容旧格式：检查是否有 results 数组
                            results = data["output"].get("results")
                            if results and len(results) > 0:
                                video_url = results[0]["url"]
                                print(f"✅ 任务成功完成，视频URL: {video_url}")
                                
                                return {
                                    "status": "success",
                                    "video_url": video_url,
                                    "task_metrics": data["output"].get("task_metrics", {}),
                                    "usage": data["output"].get("usage", {})
                                }
                            else:
                                raise RuntimeError(f"任务成功但未找到视频URL，响应: {json.dumps(data, ensure_ascii=False)}")
                    
                    elif status == "FAILED":
                        error_msg = data["output"].get("message", "Unknown error")
                        raise RuntimeError(f"生成任务失败: {error_msg}")
                    
                    elif status in ["RUNNING", "PENDING"]:
                        progress = min(100, (i + 1) * 100 // 120)  # 估算进度
                        print(f"  🔄 生成进度: {progress}% (状态: {status})")
                    
                    else:
                        print(f"  ❓ 未知状态: {status}")
                
                await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"视频生成超时 (任务ID: {task_id})")
    
    async def _download_video(self, video_url: str, output_path: Path):
        """下载生成的视频"""
        print(f"📥 开始下载视频...")
        print(f"🔗 视频URL: {video_url}")
        print(f"💾 保存路径: {output_path}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                print(f"📥 下载响应状态: {response.status}")
                
                if response.status != 200:
                    print(f"❌ 视频下载失败，HTTP状态: {response.status}")
                    raise RuntimeError(f"视频下载失败 ({response.status})")
                
                # 获取文件大小
                content_length = response.headers.get('content-length')
                if content_length:
                    total_size = int(content_length)
                    print(f"📊 视频文件大小: {total_size / 1024 / 1024:.2f} MB")
                
                print(f"📥 开始读取视频内容...")
                content = await response.read()
                print(f"📥 视频内容读取完成，实际大小: {len(content)} 字节")
                
                print(f"💾 开始保存到文件...")
                async with aiofiles.open(output_path, 'wb') as f:
                    await f.write(content)
                
                file_size = len(content) / 1024 / 1024
                print(f"✅ 视频已成功保存: {output_path.name} ({file_size:.2f} MB)")

async def test():
    """测试函数"""
    api = QwenT2VPlusAPI()
    
    # 测试文生视频
    result = await api.generate_text_to_video(
        prompt="一只可爱的小猫在花园里奔跑，阳光明媚，花朵随风摇摆",
        negative_prompt="模糊，低质量，变形",
        duration=5,
        fps=30,
        resolution="1920*1080",
        style="realistic",
        motion_strength=0.7
    )
    
    print(f"生成结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(test())