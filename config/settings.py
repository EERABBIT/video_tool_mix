#!/usr/bin/env python3
"""
全局配置文件
"""

import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent.parent

# 项目路径
PROJECTS_DIR = BASE_DIR / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

# 临时文件路径
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# API配置
API_CONFIG = {
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/api/v1/services/aigc",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "timeout": 300  # 5分钟超时
    }
}

# LLM配置
LLM_CONFIG = {
    "default_provider": os.getenv("LLM_PROVIDER", "dashscope"),  # claude, dashscope, openai
    "claude": {
        "api_key": os.getenv("CLAUDE_API_KEY"),
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 4000,
        "temperature": 0.7
    },
    "dashscope": {
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "model": "qwen-turbo",
        "max_tokens": 3000,
        "temperature": 0.7
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4-turbo-preview",
        "max_tokens": 4000,
        "temperature": 0.7
    }
}

# Agent配置
AGENT_CONFIG = {
    "story": {
        "temperature": 0.7,
        "max_tokens": 3000
    },
    "storyboard": {
        "temperature": 0.7,
        "max_tokens": 4000
    },
    "character": {
        "temperature": 0.8,
        "max_tokens": 4000
    },
    "scene": {
        "temperature": 0.8,
        "max_tokens": 4000
    },
    "shot_prompt": {
        "temperature": 0.6,
        "max_tokens": 3000
    },
    "image_optimize": {
        "temperature": 0.6,
        "max_tokens": 2000
    },
    "video_prompt": {
        "temperature": 0.6,
        "max_tokens": 3000
    }
}

# 视频生成配置
VIDEO_CONFIG = {
    "default_duration": 60,  # 默认时长60秒
    "max_duration": 300,  # 最大时长5分钟
    "default_fps": 24,  # 默认帧率
    "default_resolution": "1280x720",  # 默认分辨率
    "output_format": "mp4"  # 输出格式
}

# Web配置
WEB_CONFIG = {
    "host": "0.0.0.0",
    "port": 30001,
    "debug": True,
    "max_upload_size": 50 * 1024 * 1024,  # 50MB
    "allowed_extensions": ["png", "jpg", "jpeg", "gif", "mp4", "avi", "mov", "wav", "mp3"]
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": BASE_DIR / "logs" / "app.log"
}

# 确保日志目录存在
LOG_CONFIG["file"].parent.mkdir(exist_ok=True)