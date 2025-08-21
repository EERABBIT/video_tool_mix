#!/usr/bin/env python3
"""
启动脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量
os.environ['PYTHONPATH'] = str(Path(__file__).parent)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 导入并启动应用
from web.app import app
from config.settings import WEB_CONFIG

if __name__ == '__main__':
    print(f"Starting AI Video Generation Platform...")
    print(f"Server running at http://{WEB_CONFIG['host']}:{WEB_CONFIG['port']}")
    print(f"Press Ctrl+C to stop")
    
    app.run(
        host=WEB_CONFIG['host'],
        port=WEB_CONFIG['port'],
        debug=WEB_CONFIG['debug']
    )