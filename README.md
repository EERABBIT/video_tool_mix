# 视频生成工具 Web 服务

这是一个基于通义万相模型的文生图、视频生成工具Web服务，支持多种生成模式。

## 功能特性

- 🎨 **文生图**: 使用通义万相2.2-文生图-Flash模型
- 🎬 **图生视频**: 使用通义万相2.2-图生视频-Flash模型  
- 🎥 **文生视频**: 使用通义万相2.2-文生视频-Plus模型

## 界面功能

- 📁 **左侧素材框**: 显示和管理文件夹内的素材
- 💬 **底部聊天框**: 输入文本或上传/拖入图片视频素材
- 📺 **结果显示框**: 展示模型生成的结果
- 🔄 **实时状态**: 显示生成进度和状态

## 快速开始

### 1. 环境要求

- Python 3.7+
- Flask 2.3+
- aiohttp 3.8+

### 2. 安装依赖

```bash
# 安装依赖包
pip install -r requirements.txt
```

### 3. 配置API密钥

在以下文件中配置你的API密钥：
- `qwen_t2i_flash.py` - 文生图API
- `qwen_i2v_flash.py` - 图生视频API
- `qwen_t2v_plus.py` - 文生视频API

或者设置环境变量：
```bash
export QWEN_API_KEY="your_api_key_here"
```

### 4. 启动服务

```bash
# 使用启动脚本
./start.sh

# 或者直接运行
python app.py
```

### 5. 访问服务

打开浏览器访问: http://localhost:5000

## 目录结构

```
video_tool_mix/
├── app.py                    # Flask主应用
├── config.py                 # 配置文件
├── qwen_t2i_flash.py        # 文生图模型
├── qwen_i2v_flash.py        # 图生视频模型
├── qwen_t2v_plus.py         # 文生视频模型
├── requirements.txt         # 依赖包
├── start.sh                 # 启动脚本
├── templates/
│   └── index.html          # 前端模板
├── uploads/                 # 上传文件目录
├── output/                  # 输出文件目录
├── assets/                  # 素材文件目录
└── README.md               # 说明文档
```

## API接口

### 文生图
```
POST /api/text-to-image
Content-Type: application/json

{
  "prompt": "一只可爱的小猫",
  "negative_prompt": "模糊",
  "size": "1024*1024",
  "style": "auto",
  "n": 1
}
```

### 图生视频
```
POST /api/image-to-video
Content-Type: application/json

{
  "image_path": "/path/to/image.jpg",
  "prompt": "让画面动起来",
  "duration": 5,
  "fps": 30,
  "resolution": "1280*720"
}
```

### 文生视频
```
POST /api/text-to-video
Content-Type: application/json

{
  "prompt": "一只猫在花园里奔跑",
  "duration": 5,
  "style": "realistic",
  "motion_strength": 0.7,
  "resolution": "1280*720"
}
```

## 使用说明

1. **准备素材**: 将测试图片放入 `assets/` 目录
2. **选择功能**: 点击顶部标签页选择需要的功能
3. **输入参数**: 填写提示词和相关参数
4. **选择素材**: 从左侧素材库选择需要的图片
5. **开始生成**: 点击生成按钮开始处理
6. **查看结果**: 在结果区域查看生成的内容

## 注意事项

- 确保API密钥配置正确
- 网络连接稳定，生成过程可能需要几分钟
- 支持的图片格式: PNG, JPG, JPEG, GIF
- 支持的视频格式: MP4, AVI, MOV
- 最大文件上传限制: 50MB

## 故障排除

1. **API密钥错误**: 检查密钥是否正确配置
2. **网络连接问题**: 确保能访问阿里云服务
3. **文件上传失败**: 检查文件格式和大小限制
4. **生成超时**: 某些复杂任务可能需要更长时间

## 开发说明

- 前端使用纯JavaScript，无需额外框架
- 后端使用Flask异步处理API调用
- 支持拖拽上传和实时状态显示
- 响应式设计，适配不同屏幕尺寸