#!/usr/bin/env python3
"""
千问API测试脚本
独立测试千问文生图API的完整流程：提交任务、轮询状态、获取结果
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import aiohttp

class QwenAPITester:
    """千问API测试器"""
    
    def __init__(self):
        # 从环境变量获取API密钥
        self.api_key = os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required. Please set DASHSCOPE_API_KEY in .env file")
        
        # API配置
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.model = "wan2.2-t2i-flash"  # 通义万象模型
        
        # 测试输出目录
        self.output_dir = Path("./qwen_test_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # 支持的分辨率列表
        self.supported_sizes = [
            "1080*1920",    # 9:16 竖屏
            "1920*1080",    # 16:9 横屏
            "1440*1440",    # 1:1 正方形
            "1632*1248",    # 4:3 横屏
            "1248*1632",    # 3:4 竖屏
            "480*832",      # 9:16 小尺寸竖屏
            "832*480",      # 16:9 小尺寸横屏
            "624*624"       # 1:1 小尺寸正方形
        ]
    
    def _validate_size(self, size: str) -> str:
        """验证并修正分辨率格式"""
        if not size:
            return "1920*1080"  # 默认分辨率
        
        # 检查是否是支持的分辨率
        if size in self.supported_sizes:
            return size
        
        # 如果传入的是1024*1024这种旧格式，转换为最接近的支持格式
        if size == "1024*1024":
            return "1440*1440"  # 转换为支持的正方形格式
        
        # 其他不支持的格式，返回默认值
        print(f"⚠️ 分辨率 {size} 不被支持，使用默认分辨率 1920*1080")
        print(f"💡 支持的分辨率: {', '.join(self.supported_sizes)}")
        return "1920*1080"
    
    async def test_full_workflow(self):
        """测试完整的API工作流程"""
        print("🚀 开始测试千问文生图API...")
        print(f"📁 输出目录: {self.output_dir.absolute()}")
        print(f"🔑 使用API密钥: {self.api_key[:10]}...")
        print("-" * 50)
        
        # 测试参数
        test_params = {
            "prompt": "一只可爱的小猫咪，坐在阳光明媚的窗台上，卡通风格",
            "negative_prompt": "模糊、低质量、变形",
            "size": "1920*1080",  # 使用支持的分辨率
            "n": 1,
            "style": "auto",
            "seed": None
        }
        
        print(f"📝 测试参数:")
        for key, value in test_params.items():
            print(f"  {key}: {value}")
        print("-" * 50)
        
        try:
            # 步骤1: 提交任务
            print("1️⃣ 提交生成任务...")
            task_id = await self._submit_generation_task(**test_params)
            print(f"✅ 任务提交成功，任务ID: {task_id}")
            
            # 步骤2: 轮询状态
            print("2️⃣ 轮询任务状态...")
            result = await self._poll_task_status(task_id)
            print(f"✅ 任务完成，生成了 {len(result['images'])} 张图像")
            
            # 步骤3: 下载图像
            print("3️⃣ 下载生成的图像...")
            downloaded_files = []
            for idx, image_url in enumerate(result['images']):
                output_path = self.output_dir / f"test_image_{int(time.time())}_{idx+1}.png"
                await self._download_image(image_url, output_path)
                downloaded_files.append(output_path)
                print(f"  📸 图像 {idx+1} 已保存: {output_path.name}")
            
            print("-" * 50)
            print("🎉 测试完成!")
            print(f"📊 结果统计:")
            print(f"  任务ID: {task_id}")
            print(f"  生成图像数: {len(downloaded_files)}")
            print(f"  下载文件:")
            for file in downloaded_files:
                size_mb = file.stat().st_size / 1024 / 1024
                print(f"    - {file.name} ({size_mb:.2f} MB)")
            
            return {
                "success": True,
                "task_id": task_id,
                "images": [str(f) for f in downloaded_files],
                "result": result
            }
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _submit_generation_task(
        self,
        prompt: str,
        negative_prompt: str = "",
        size: str = "1920*1080",
        n: int = 1,
        style: str = "auto",
        seed: Optional[int] = None
    ) -> str:
        """提交图像生成任务"""
        
        # 验证分辨率格式
        size = self._validate_size(size)
        
        # 构建请求体
        request_body = {
            "model": self.model,
            "input": {
                "prompt": prompt,
                "n": n,
                "size": size,
                "style": f"<{style}>" if style != "auto" else "<auto>"
            },
            "parameters": {}
        }
        
        # 添加可选参数
        if negative_prompt:
            request_body["input"]["negative_prompt"] = negative_prompt
        
        if seed is not None:
            request_body["parameters"]["seed"] = seed
        
        # 设置请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"  # 启用异步模式
        }
        
        print(f"  📤 发送请求到: {self.base_url}/services/aigc/text2image/image-synthesis")
        print(f"  📋 请求体: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/services/aigc/text2image/image-synthesis"
            
            async with session.post(url, headers=headers, json=request_body) as response:
                response_text = await response.text()
                
                print(f"  📥 响应状态: {response.status}")
                print(f"  📄 响应内容: {response_text}")
                
                if response.status != 200:
                    raise RuntimeError(f"API请求失败 ({response.status}): {response_text}")
                
                data = json.loads(response_text)
                
                # 检查响应
                if data.get("code") and data["code"] != "200":
                    raise RuntimeError(f"API错误: {data.get('message', 'Unknown error')}")
                
                # 返回任务ID
                task_id = data["output"]["task_id"]
                return task_id
    
    async def _poll_task_status(self, task_id: str) -> Dict[str, Any]:
        """轮询任务状态直到完成"""
        
        max_polls = 120  # 最多轮询120次
        poll_interval = 2  # 每2秒轮询一次
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        url = f"{self.base_url}/tasks/{task_id}"
        print(f"  🔄 轮询URL: {url}")
        
        async with aiohttp.ClientSession() as session:
            for i in range(max_polls):
                print(f"  ⏱️  轮询 {i+1}/{max_polls}...")
                
                # 查询任务状态
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        print(f"  ⚠️  状态查询失败: {response_text}")
                        await asyncio.sleep(poll_interval)
                        continue
                    
                    data = json.loads(response_text)
                    print(f"  📊 轮询响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    # 获取任务状态
                    status = data["output"]["task_status"]
                    print(f"  📈 任务状态: {status}")
                    
                    if status == "SUCCEEDED":
                        # 任务成功完成
                        results = data["output"]["results"]
                        image_urls = [result["url"] for result in results]
                        
                        print(f"  ✅ 任务成功完成，生成 {len(image_urls)} 张图像")
                        for idx, url in enumerate(image_urls):
                            print(f"    🖼️  图像 {idx+1}: {url}")
                        
                        return {
                            "status": "success",
                            "images": image_urls,
                            "task_metrics": data["output"].get("task_metrics", {})
                        }
                    
                    elif status == "FAILED":
                        # 任务失败
                        error_msg = data["output"].get("message", "Unknown error")
                        raise RuntimeError(f"生成任务失败: {error_msg}")
                    
                    elif status == "RUNNING" or status == "PENDING":
                        # 任务进行中
                        progress = min(100, (i + 1) * 100 // 30)  # 估算进度
                        print(f"  🔄 生成进度: {progress}% (状态: {status})")
                    
                    else:
                        print(f"  ❓ 未知状态: {status}")
                
                await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"图像生成超时 (任务ID: {task_id})")
    
    async def _download_image(self, image_url: str, output_path: Path):
        """下载生成的图像"""
        
        print(f"  📥 下载图像: {image_url}")
        print(f"  💾 保存到: {output_path}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise RuntimeError(f"图像下载失败 ({response.status})")
                
                # 保存图像
                content = await response.read()
                with open(output_path, 'wb') as f:
                    f.write(content)
                
                file_size = len(content) / 1024 / 1024  # MB
                print(f"  ✅ 图像已保存: {output_path.name} ({file_size:.2f} MB)")

async def main():
    """主函数"""
    print("=" * 60)
    print("🧪 千问文生图API测试脚本")
    print("=" * 60)
    
    tester = QwenAPITester()
    
    # 检查API密钥
    if tester.api_key == "YOUR_QWEN_API_KEY_HERE":
        print("❌ 请先修改脚本中的API密钥!")
        print("💡 在第19行修改: self.api_key = \"你的实际API密钥\"")
        return
    
    # 运行测试
    result = await tester.test_full_workflow()
    
    print("=" * 60)
    if result["success"]:
        print("🎊 所有测试通过!")
    else:
        print("💥 测试失败，请检查API密钥和网络连接")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())