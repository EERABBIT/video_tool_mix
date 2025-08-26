#!/usr/bin/env python3
"""
通义万相2.1-首尾帧-Plus模型调用脚本
完整实现：提交任务 -> 轮询状态 -> 下载视频
"""

import asyncio
import json
import time
import base64
import os
from pathlib import Path
from typing import Optional, Dict, Any
import aiohttp
import aiofiles
from datetime import datetime

class QwenKeyframePlusAPI:
    """通义万相2.1-首尾帧-Plus模型API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required. Please set DASHSCOPE_API_KEY in .env file")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.model = "wanx2.1-kf2v-plus"
        self.output_dir = Path("./output/keyframe_plus")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_keyframe_video(
        self,
        first_frame_path: str,
        last_frame_path: str,
        prompt: Optional[str] = None,
        resolution: str = "720P",
        prompt_extend: bool = True
    ) -> Dict[str, Any]:
        """
        首尾帧生成视频 - 完整流程
        
        Args:
            first_frame_path: 首帧图片路径
            last_frame_path: 尾帧图片路径
            prompt: 生成提示词
            resolution: 分辨率 (720P, 1080P)
            prompt_extend: 是否启用提示词扩展
        """
        print(f"\n{'='*60}")
        print(f"🎬 开始首尾帧视频生成任务")
        print(f"{'='*60}")
        print(f"📷 首帧: {first_frame_path}")
        print(f"📷 尾帧: {last_frame_path}")
        print(f"📝 提示词: {prompt or '默认提示词'}")
        print(f"📐 分辨率: {resolution}")
        
        try:
            # 1. 编码图片
            print(f"\n🔧 步骤1: 编码图片为base64...")
            first_frame_base64 = await self._encode_image(first_frame_path)
            last_frame_base64 = await self._encode_image(last_frame_path)
            print(f"  ✅ 首帧大小: {len(first_frame_base64) / 1024:.1f} KB")
            print(f"  ✅ 尾帧大小: {len(last_frame_base64) / 1024:.1f} KB")
            
            # 2. 提交任务
            print(f"\n🔧 步骤2: 提交生成任务...")
            task_id = await self._submit_task(
                first_frame_base64, 
                last_frame_base64, 
                prompt, 
                resolution,
                prompt_extend
            )
            
            if not task_id:
                return {"status": "error", "error": "任务提交失败"}
            
            print(f"  ✅ 任务ID: {task_id}")
            
            # 3. 轮询任务状态
            print(f"\n🔧 步骤3: 轮询任务状态...")
            result = await self._poll_task_status(task_id)
            
            if result["status"] != "success":
                return result
            
            # 4. 下载视频
            if result.get("video_url"):
                print(f"\n🔧 步骤4: 下载生成的视频...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.output_dir / f"keyframe_{timestamp}.mp4"
                
                success = await self._download_video(result["video_url"], output_path)
                if success:
                    result["local_path"] = str(output_path)
                    print(f"\n{'='*60}")
                    print(f"🎉 视频生成成功!")
                    print(f"  📁 本地文件: {output_path}")
                    print(f"  ⏱️ 视频时长: {result.get('duration', 5)}秒")
                    print(f"{'='*60}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            import traceback
            print(f"📍 错误详情: {traceback.format_exc()}")
            return {"status": "error", "error": str(e)}
    
    async def _encode_image(self, image_path: str) -> str:
        """将图片编码为base64 data URI"""
        file_path = Path(image_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 检测MIME类型
        import mimetypes
        mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
        
        async with aiofiles.open(image_path, 'rb') as f:
            content = await f.read()
            base64_str = base64.b64encode(content).decode('utf-8')
            # 返回完整的data URI格式
            return f"data:{mime_type};base64,{base64_str}"
    
    async def _submit_task(
        self, 
        first_frame: str, 
        last_frame: str, 
        prompt: Optional[str],
        resolution: str,
        prompt_extend: bool
    ) -> Optional[str]:
        """提交视频生成任务"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }
        
        # 使用正确的API端点
        url = f"{self.base_url}/services/aigc/image2video/video-synthesis"
        
        request_body = {
            "model": self.model,
            "input": {
                "first_frame_url": first_frame,
                "last_frame_url": last_frame,
                "prompt": prompt or "创建流畅的过渡动画，自然的运动轨迹"
            },
            "parameters": {
                "resolution": resolution,
                "prompt_extend": prompt_extend
            }
        }
        
        print(f"  📦 模型: {self.model}")
        print(f"  📡 API端点: {url}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url, 
                    headers=headers, 
                    json=request_body,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        print(f"  ❌ 请求失败: HTTP {response.status}")
                        print(f"  错误响应: {response_text}")
                        return None
                    
                    data = json.loads(response_text)
                    
                    # 检查响应格式
                    if "output" in data and "task_id" in data["output"]:
                        return data["output"]["task_id"]
                    else:
                        print(f"  ❌ 响应格式异常: {data}")
                        return None
                        
            except asyncio.TimeoutError:
                print(f"  ❌ 请求超时(30秒)")
                return None
            except Exception as e:
                print(f"  ❌ 请求异常: {e}")
                return None
    
    async def _poll_task_status(self, task_id: str, max_wait: int = 900) -> Dict[str, Any]:
        """
        轮询任务状态
        
        Args:
            task_id: 任务ID
            max_wait: 最大等待时间(秒)，默认15分钟
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        url = f"{self.base_url}/tasks/{task_id}"
        poll_interval = 30  # 每30秒查询一次
        max_polls = max_wait // poll_interval
        
        print(f"  ⏳ 最多等待 {max_wait} 秒，每 {poll_interval} 秒查询一次")
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            last_status = None
            
            for i in range(max_polls):
                try:
                    async with session.get(
                        url, 
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status != 200:
                            print(f"  ⚠️ 查询失败: HTTP {response.status}")
                            await asyncio.sleep(poll_interval)
                            continue
                        
                        data = json.loads(await response.text())
                        output = data.get("output", {})
                        status = output.get("task_status", "UNKNOWN")
                        
                        # 只在状态变化时打印
                        if status != last_status:
                            elapsed = int(time.time() - start_time)
                            print(f"  [{elapsed}秒] 任务状态: {status}")
                            last_status = status
                        
                        if status == "SUCCEEDED":
                            print(f"\n  ✅ 视频生成成功!")
                            
                            # 获取视频信息
                            video_url = output.get("video_url")
                            usage = data.get("usage", {})
                            
                            if output.get("orig_prompt"):
                                print(f"  原始提示词: {output.get('orig_prompt')}")
                            if output.get("actual_prompt"):
                                print(f"  扩展提示词: {output.get('actual_prompt')}")
                            
                            return {
                                "status": "success",
                                "video_url": video_url,
                                "duration": usage.get("video_duration", 5),
                                "ratio": usage.get("video_ratio"),
                                "task_id": task_id,
                                "orig_prompt": output.get("orig_prompt"),
                                "actual_prompt": output.get("actual_prompt")
                            }
                        
                        elif status == "FAILED":
                            error_msg = output.get("message", "未知错误")
                            print(f"\n  ❌ 任务失败: {error_msg}")
                            return {"status": "error", "error": error_msg}
                        
                        elif status == "UNKNOWN":
                            print(f"\n  ⚠️ 任务不存在或已过期")
                            return {"status": "error", "error": "任务不存在或已过期"}
                        
                except asyncio.TimeoutError:
                    print(f"  ⚠️ 查询超时，继续重试...")
                except Exception as e:
                    print(f"  ⚠️ 查询出错: {e}")
                
                # 等待下次轮询
                await asyncio.sleep(poll_interval)
        
        print(f"\n  ⏱️ 等待超时(超过 {max_wait} 秒)")
        return {"status": "error", "error": f"生成超时(超过{max_wait}秒)"}
    
    async def _download_video(self, video_url: str, output_path: Path) -> bool:
        """下载生成的视频"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    video_url,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5分钟超时
                ) as response:
                    if response.status != 200:
                        print(f"  ❌ 下载失败: HTTP {response.status}")
                        return False
                    
                    # 获取文件大小
                    total_size = int(response.headers.get('content-length', 0))
                    if total_size > 0:
                        print(f"  📊 文件大小: {total_size / 1024 / 1024:.2f} MB")
                    
                    # 下载并保存
                    content = await response.read()
                    
                    async with aiofiles.open(output_path, 'wb') as f:
                        await f.write(content)
                    
                    actual_size = len(content) / 1024 / 1024
                    print(f"  ✅ 下载完成: {actual_size:.2f} MB")
                    return True
                    
        except asyncio.TimeoutError:
            print(f"  ❌ 下载超时")
            return False
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return False


async def test():
    """测试函数"""
    print("🚀 通义千问首尾帧视频生成测试")
    print("="*60)
    
    api = QwenKeyframePlusAPI()
    
    # 检查测试图片是否存在
    test_images = [
        "./assets/images/generated_1755503705_t2i_4653711ba93d4d63a6f2b7008ea28ca0.png",
        "./assets/images/generated_1755505349_t2i_8d3f7fbb7b1a4263b84519ac42c08cb6.png"
    ]
    
    # 如果测试图片不存在，使用其他可用图片
    first_frame = None
    last_frame = None
    
    for img in test_images:
        if Path(img).exists():
            if not first_frame:
                first_frame = img
            elif not last_frame:
                last_frame = img
                break
    
    if not first_frame or not last_frame:
        print("❌ 未找到测试图片")
        print("请确保存在至少两张图片用于测试")
        return False
    
    print(f"✅ 找到测试图片:")
    print(f"  首帧: {first_frame}")
    print(f"  尾帧: {last_frame}")
    
    # 执行测试
    result = await api.generate_keyframe_video(
        first_frame_path=first_frame,
        last_frame_path=last_frame,
        prompt="写实风格，一只黑色小猫好奇地看向天空，镜头从平视逐渐上升，最后俯拍小猫好奇的眼神。",
        resolution="720P",
        prompt_extend=True
    )
    
    print(f"\n📊 测试结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result["status"] == "success":
        print(f"\n✅ 测试成功! 视频已保存到: {result.get('local_path')}")
        return True
    else:
        print(f"\n❌ 测试失败: {result.get('error', 'Unknown error')}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test())
    exit(0 if success else 1)