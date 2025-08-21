#!/usr/bin/env python3
"""
本地文生视频API模块
基于局域网部署的T2V模型服务
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False


class LocalT2VAPIError(Exception):
    """本地T2V API错误"""
    pass


class QwenLocalT2VAPI:
    """本地文生视频API"""
    
    def __init__(self, base_url: str = "http://192.168.3.4:8888"):
        self.base_url = base_url
        self.model = "local-t2v"
        self.output_dir = Path("./output/local_t2v")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _calculate_frames(self, duration: int, fps: int) -> int:
        """根据时长和帧率计算帧数"""
        # 确保参数是整数
        duration = int(duration) if isinstance(duration, str) else duration
        fps = int(fps) if isinstance(fps, str) else fps
        
        frames = duration * fps
        # 限制在16-600帧范围内
        return max(16, min(600, frames))
    
    def _ensure_64_multiple(self, value: int) -> int:
        """确保尺寸是64的倍数"""
        return ((value + 63) // 64) * 64
    
    def _parse_resolution(self, resolution: str) -> tuple:
        """解析分辨率字符串，确保是64的倍数"""
        if 'x' in resolution:
            width, height = map(int, resolution.split('x'))
        elif '*' in resolution:
            width, height = map(int, resolution.split('*'))
        else:
            # 默认正方形
            width = height = int(resolution)
        
        # 确保是64的倍数
        original_width, original_height = width, height
        width = self._ensure_64_multiple(width)
        height = self._ensure_64_multiple(height)
        
        # 如果进行了调整，打印提示
        if width != original_width or height != original_height:
            print(f"  ⚠️ 分辨率调整: {original_width}x{original_height} -> {width}x{height} (64的倍数)")
        
        return width, height
    
    async def _submit_task(self, request_body: Dict) -> str:
        """提交生成任务"""
        if not HAS_AIOHTTP:
            raise LocalT2VAPIError("需要安装aiohttp库")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/generate_video_minimal"
        
        print(f"\n{'='*60}")
        print(f"🎬 开始本地T2V视频生成任务")
        print(f"{'='*60}")
        print(f"📝 提示词: {request_body['positive'][:50]}...")
        print(f"📐 分辨率: {request_body['width']}x{request_body['height']}")
        print(f"🎞️ 帧数: {request_body['length']}, 帧率: {request_body['fps']}fps")
        print(f"🌐 服务地址: {self.base_url}")
        
        # 创建会话时禁用代理，因为是局域网地址
        connector = aiohttp.TCPConnector()
        timeout = aiohttp.ClientTimeout(total=120)
        
        try:
            async with aiohttp.ClientSession(connector=connector, trust_env=False, timeout=timeout) as session:
                print(f"\n🔧 步骤1: 提交任务到本地服务...")
                async with session.post(url, headers=headers, json=request_body) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        print(f"❌ API请求失败: HTTP {response.status}")
                        print(f"错误响应: {response_text}")
                        raise LocalT2VAPIError(f"API请求失败 ({response.status}): {response_text}")
                    
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError:
                        raise LocalT2VAPIError(f"响应JSON解析失败: {response_text}")
                    
                    if data.get("detail"):
                        # 处理验证错误
                        error_msg = str(data["detail"])
                        print(f"❌ API参数错误: {error_msg}")
                        raise LocalT2VAPIError(f"API参数错误: {error_msg}")
                    
                    job_id = data.get("job_id")
                    if not job_id:
                        raise LocalT2VAPIError(f"未获取到job_id: {response_text}")
                    
                    print(f"✅ 任务提交成功")
                    print(f"🆔 任务ID: {job_id}")
                    return job_id
                    
        except aiohttp.ClientError as e:
            print(f"❌ 网络连接失败: {e}")
            raise LocalT2VAPIError(f"无法连接到本地服务 {self.base_url}: {e}")
    
    async def _poll_task_status(self, job_id: str) -> Dict[str, Any]:
        """轮询任务状态直到完成"""
        if not HAS_AIOHTTP:
            raise LocalT2VAPIError("需要安装aiohttp库")
            
        max_polls = 600  # 最多轮询20分钟
        poll_interval = 5  # 每5秒轮询一次
        
        url = f"{self.base_url}/task_status/{job_id}"
        
        print(f"\n🔧 步骤2: 轮询任务状态...")
        start_time = time.time()
        
        # 创建会话时禁用代理
        connector = aiohttp.TCPConnector()
        timeout = aiohttp.ClientTimeout(total=30)
        
        try:
            async with aiohttp.ClientSession(connector=connector, trust_env=False, timeout=timeout) as session:
                for i in range(max_polls):
                    try:
                        async with session.get(url) as response:
                            if response.status != 200:
                                await asyncio.sleep(poll_interval)
                                continue
                            
                            response_text = await response.text()
                            data = json.loads(response_text)
                            
                            status = data.get("status")
                            elapsed_time = int(time.time() - start_time)
                            
                            if status == "completed":
                                print(f"\n{'='*60}")
                                print(f"🎉 视频生成完成!")
                                print(f"⏱️ 总耗时: {elapsed_time}秒")
                                if data.get("execution_time"):
                                    print(f"🔥 实际生成时间: {data['execution_time']:.2f}秒")
                                print(f"✅ 完成时间: {data.get('completed_at', '未知')}")
                                print(f"{'='*60}")
                                
                                return {
                                    "status": "success",
                                    "job_id": job_id,
                                    "outputs": data.get("outputs", []),
                                    "execution_time": data.get("execution_time"),
                                    "completed_at": data.get("completed_at")
                                }
                            
                            elif status == "not_found":
                                print(f"\n❌ 任务未找到: {data.get('message', '')}")
                                raise LocalT2VAPIError(f"任务未找到: {job_id}")
                            
                            elif status == "pending":
                                queue_position = data.get("queue_position", "未知")
                                print(f"⏳ 排队中... 位置: {queue_position} | 已等待 {elapsed_time}秒", end='\r')
                            
                            elif status == "running":
                                progress = data.get("progress", "进行中")
                                print(f"⏳ 生成中... {progress} | 已等待 {elapsed_time}秒", end='\r')
                            
                    except Exception as e:
                        # 如果查询失败，继续重试
                        print(f"⚠️ 状态查询失败，重试中... ({str(e)})", end='\r')
                    
                    await asyncio.sleep(poll_interval)
            
            raise TimeoutError(f"视频生成超时 (任务ID: {job_id})")
            
        except aiohttp.ClientError as e:
            print(f"❌ 轮询过程中网络错误: {e}")
            raise LocalT2VAPIError(f"轮询过程中网络错误: {e}")
    
    async def _download_video(self, job_id: str, filename: str, output_path: Path,
                            file_type: str = "output", subfolder: str = "") -> None:
        """下载生成的视频文件"""
        if not HAS_AIOHTTP:
            raise LocalT2VAPIError("需要安装aiohttp库")
        
        # 构建下载URL
        params = {
            "filename": filename,
            "type": file_type
        }
        if subfolder:
            params["subfolder"] = subfolder
            
        url = f"{self.base_url}/proxy_video/{job_id}"
        
        print(f"\n🔧 步骤3: 下载视频文件...")
        print(f"📥 下载文件: {filename}")
        
        # 创建会话时禁用代理
        connector = aiohttp.TCPConnector()
        timeout = aiohttp.ClientTimeout(total=300)  # 下载可能需要更长时间
        
        try:
            async with aiohttp.ClientSession(connector=connector, trust_env=False, timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ 视频下载失败: HTTP {response.status}")
                        print(f"错误信息: {error_text}")
                        raise LocalT2VAPIError(f"视频下载失败 ({response.status}): {error_text}")
                    
                    # 获取文件大小
                    total_size = int(response.headers.get('content-length', 0))
                    if total_size:
                        print(f"📊 文件大小: {total_size / 1024 / 1024:.2f} MB")
                    
                    # 下载文件
                    content = await response.read()
                    
                    # 保存文件
                    if HAS_AIOFILES:
                        async with aiofiles.open(output_path, 'wb') as f:
                            await f.write(content)
                    else:
                        # 同步写入文件
                        with open(output_path, 'wb') as f:
                            f.write(content)
                    
                    file_size = len(content) / 1024 / 1024
                    print(f"✅ 下载完成: {file_size:.2f} MB")
                    print(f"📁 保存到: {output_path}")
                    
        except aiohttp.ClientError as e:
            print(f"❌ 下载过程中网络错误: {e}")
            raise LocalT2VAPIError(f"下载过程中网络错误: {e}")
    
    async def generate_text_to_video(self, prompt: str, negative_prompt: Optional[str] = None,
                                   duration: int = 5, fps: int = 24, resolution: str = "1920*1080",
                                   seed: Optional[int] = None, style: str = "realistic",
                                   motion_strength: float = 0.5) -> Dict[str, Any]:
        """生成文生视频
        
        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            duration: 视频时长（秒）
            fps: 帧率
            resolution: 分辨率
            seed: 随机种子
            style: 风格（本地API可能不支持）
            motion_strength: 动作强度（本地API可能不支持）
            
        Returns:
            生成结果字典
        """
        try:
            # 确保数值参数是正确的类型
            duration = int(duration) if isinstance(duration, str) else duration
            fps = int(fps) if isinstance(fps, str) else fps
            if seed is not None and isinstance(seed, str):
                seed = int(seed) if seed else None
            
            # 解析分辨率
            width, height = self._parse_resolution(resolution)
            
            # 计算帧数
            frames = self._calculate_frames(duration, fps)
            
            # 构建请求体
            request_body = {
                "positive": prompt,
                "width": width,
                "height": height,
                "length": frames,
                "fps": fps
            }
            
            if negative_prompt:
                request_body["negative"] = negative_prompt
                
            if seed is not None:
                request_body["seed"] = seed
            
            # 提交任务
            job_id = await self._submit_task(request_body)
            
            # 轮询状态
            result = await self._poll_task_status(job_id)
            
            # 下载视频文件
            if result["status"] == "success":
                outputs = result.get("outputs", [])
                if outputs:
                    # 获取第一个输出文件
                    output_file = outputs[0]
                    filename = output_file.get("filename")
                    file_type = output_file.get("type", "output")
                    subfolder = output_file.get("subfolder", "")
                    
                    if filename:
                        # 生成本地文件名
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        local_filename = f"local_t2v_{timestamp}.mp4"
                        output_path = self.output_dir / local_filename
                        
                        # 下载视频到本地
                        await self._download_video(job_id, filename, output_path, file_type, subfolder)
                        result["local_path"] = str(output_path)
                        result["filename"] = local_filename
                    else:
                        print(f"⚠️ 未找到输出文件名")
                else:
                    print(f"⚠️ 未找到输出文件信息")
            
            return result
            
        except Exception as e:
            print(f"\n❌ 生成失败: {str(e)}")
            import traceback
            print(f"📍 错误详情: {traceback.format_exc()}")
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    # 简单的测试示例
    async def simple_test():
        api = QwenLocalT2VAPI()
        print("本地T2V API已准备就绪")
        print("使用方法:")
        print("  result = await api.generate_text_to_video(")
        print("      prompt='一只猫在草地上奔跑',")
        print("      duration=5,")
        print("      fps=24,")
        print("      resolution='1920*1080'")
        print("  )")
        print(f"默认服务地址: {api.base_url}")
        print(f"输出目录: {api.output_dir}")
    
    asyncio.run(simple_test())