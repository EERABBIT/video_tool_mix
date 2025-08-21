#!/usr/bin/env python3
"""
快速设置脚本
"""

import os
import shutil
from pathlib import Path

def setup_project():
    """设置项目环境"""
    print("🚀 开始设置AI视频生成工作室...")
    
    # 1. 检查.env文件
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 创建.env文件...")
        shutil.copy(env_example, env_file)
        print("✅ .env文件已创建，请编辑并添加您的API密钥")
        
        # 打开.env文件让用户编辑
        print("\n🔑 请在.env文件中配置以下API密钥:")
        print("   DASHSCOPE_API_KEY=sk-your_key_here")
        print("   (可选) ANTHROPIC_API_KEY=your_claude_key_here")
        print("\n📖 获取Dashscope API密钥:")
        print("   1. 访问: https://bailian.console.aliyun.com/")
        print("   2. 注册阿里云账号")
        print("   3. 进入'API-KEY管理'创建密钥")
        
        # 在macOS上自动打开文件编辑
        if os.system("which open > /dev/null 2>&1") == 0:
            os.system(f"open {env_file}")
        
    elif env_file.exists():
        print("✅ .env文件已存在")
    else:
        print("⚠️ 没有找到.env.example文件")
    
    # 2. 创建必要目录
    dirs_to_create = [
        "projects",
        "logs"
    ]
    
    for dir_name in dirs_to_create:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 创建目录: {dir_name}")
    
    # 3. 检查Python依赖
    print("\n📦 检查Python依赖...")
    try:
        import flask
        import aiohttp
        print("✅ 核心依赖已安装")
    except ImportError:
        print("❌ 缺少依赖，请运行: pip install -r requirements.txt")
        return False
    
    # 4. 检查API密钥配置
    print("\n🔍 检查配置...")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    claude_key = os.getenv("ANTHROPIC_API_KEY")
    
    if dashscope_key and dashscope_key.startswith("sk-"):
        print("✅ Dashscope API密钥已配置")
    else:
        print("⚠️ Dashscope API密钥未配置或格式错误")
        print("   请在.env文件中设置: DASHSCOPE_API_KEY=sk-your_key_here")
    
    if claude_key:
        print("✅ Claude API密钥已配置（可选）")
    
    print("\n🎉 设置完成！")
    print("\n🚀 启动应用:")
    print("   python web/app.py")
    print("\n🌐 访问地址:")
    print("   http://localhost:30001")
    
    return True

if __name__ == "__main__":
    setup_project()