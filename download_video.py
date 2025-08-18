#!/usr/bin/env python3
"""
视频下载脚本
用于下载成功生成的视频文件
"""

import asyncio
import aiohttp
import aiofiles
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
import time

class VideoDownloader:
    """视频下载器"""
    
    def __init__(self, output_dir: str = "./downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    async def download_video(self, video_url: str, filename: str = None) -> str:
        """
        下载视频文件
        
        Args:
            video_url: 视频URL
            filename: 自定义文件名（可选）
        
        Returns:
            str: 下载后的本地文件路径
        """
        if not filename:
            # 从URL解析文件名
            parsed_url = urlparse(video_url)
            url_filename = Path(parsed_url.path).name
            if url_filename and url_filename.endswith('.mp4'):
                filename = url_filename
            else:
                # 生成时间戳文件名
                timestamp = int(time.time())
                filename = f"video_{timestamp}.mp4"
        
        # 确保文件名以.mp4结尾
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        
        output_path = self.output_dir / filename
        
        print(f"🔽 开始下载视频...")
        print(f"📂 URL: {video_url}")
        print(f"💾 保存到: {output_path}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status != 200:
                        raise RuntimeError(f"下载失败 (HTTP {response.status})")
                    
                    # 获取文件大小
                    content_length = response.headers.get('content-length')
                    if content_length:
                        total_size = int(content_length)
                        print(f"📊 文件大小: {total_size / 1024 / 1024:.2f} MB")
                    
                    # 下载文件
                    content = await response.read()
                    
                    async with aiofiles.open(output_path, 'wb') as f:
                        await f.write(content)
                    
                    file_size = len(content) / 1024 / 1024
                    print(f"✅ 下载完成: {output_path.name} ({file_size:.2f} MB)")
                    
                    return str(output_path)
        
        except Exception as e:
            print(f"❌ 下载失败: {str(e)}")
            raise
    
    async def download_from_response(self, response_data: dict) -> str:
        """
        从API响应数据下载视频
        
        Args:
            response_data: API响应的字典数据
        
        Returns:
            str: 下载后的本地文件路径
        """
        # 解析响应数据
        if isinstance(response_data, str):
            response_data = json.loads(response_data)
        
        # 获取视频URL
        video_url = None
        task_id = None
        orig_prompt = None
        
        # 从output字段获取
        output = response_data.get('output', {})
        video_url = output.get('video_url')
        task_id = output.get('task_id')
        orig_prompt = output.get('orig_prompt', '')
        
        if not video_url:
            raise ValueError("响应数据中未找到 video_url 字段")
        
        # 生成文件名
        if task_id:
            filename = f"{task_id}.mp4"
        else:
            timestamp = int(time.time())
            filename = f"video_{timestamp}.mp4"
        
        print(f"📝 任务ID: {task_id}")
        if orig_prompt:
            print(f"📋 原始提示词: {orig_prompt}")
        
        return await self.download_video(video_url, filename)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='视频下载工具')
    parser.add_argument('--url', type=str, help='视频URL')
    parser.add_argument('--response', type=str, help='API响应JSON字符串')
    parser.add_argument('--response-file', type=str, help='API响应JSON文件路径')
    parser.add_argument('--output-dir', type=str, default='./downloads', help='输出目录')
    parser.add_argument('--filename', type=str, help='自定义文件名')
    
    args = parser.parse_args()
    
    if not any([args.url, args.response, args.response_file]):
        print("❌ 请提供以下参数之一:")
        print("  --url: 直接提供视频URL")
        print("  --response: 提供API响应JSON字符串")
        print("  --response-file: 提供API响应JSON文件路径")
        return
    
    downloader = VideoDownloader(args.output_dir)
    
    try:
        if args.url:
            # 直接下载URL
            await downloader.download_video(args.url, args.filename)
        
        elif args.response:
            # 从响应字符串下载
            response_data = json.loads(args.response)
            await downloader.download_from_response(response_data)
        
        elif args.response_file:
            # 从响应文件下载
            response_file = Path(args.response_file)
            if not response_file.exists():
                print(f"❌ 响应文件不存在: {response_file}")
                return
            
            with open(response_file, 'r', encoding='utf-8') as f:
                response_data = json.load(f)
            
            await downloader.download_from_response(response_data)
    
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")

# 示例响应数据，你可以基于这个格式使用脚本
EXAMPLE_RESPONSE = '''
{
  "request_id": "995978ff-9b74-902b-a3c3-0407ede7f7eb",
  "output": {
    "task_id": "fa447355-33c2-4264-ba5f-07e47b541488",
    "task_status": "SUCCEEDED",
    "submit_time": "2025-08-18 16:27:32.244",
    "scheduled_time": "2025-08-18 16:27:32.275",
    "end_time": "2025-08-18 16:29:23.053",
    "video_url": "https://dashscope-result-wlcb-acdr-1.oss-cn-wulanchabu-acdr-1.aliyuncs.com/1d/30/20250818/dff48b3c/fa447355-33c2-4264-ba5f-07e47b541488.mp4?Expires=1755592162&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=a5COwrtmoxQOM1mXPKp%2F9mwHTpI%3D",
    "orig_prompt": "可爱小猫跳舞",
    "actual_prompt": "日系治愈系插画风格，一只毛茸茸的橘色小猫正开心地在草地上跳舞。小猫圆脸大眼，耳朵抖动，尾巴翘起，前爪微微抬起，身体略微前倾，神态活泼可爱。背景是阳光明媚的春日庭院，樱花随风飘落，远处有模糊的竹篱和盛开的花朵。画面色彩明亮柔和，线条细腻清新，展现出温馨可爱的氛围。中景，平视视角。"
  },
  "usage": {
    "video_duration": 5,
    "video_ratio": "1280*720",
    "video_count": 1
  }
}
'''

if __name__ == "__main__":
    print("🎬 视频下载工具")
    print("=" * 50)
    print("使用示例:")
    print("1. 直接下载URL:")
    print("   python download_video.py --url 'https://example.com/video.mp4'")
    print()
    print("2. 从API响应下载:")
    print("   python download_video.py --response '{\"output\":{\"video_url\":\"https://...\"}}'")
    print()
    print("3. 从响应文件下载:")
    print("   python download_video.py --response-file response.json")
    print()
    print("4. 基于你提供的成功响应:")
    example_data = json.loads(EXAMPLE_RESPONSE)
    video_url = example_data['output']['video_url']
    print(f"   python download_video.py --url '{video_url}'")
    print("=" * 50)
    
    asyncio.run(main())