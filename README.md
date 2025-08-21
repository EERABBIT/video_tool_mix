# AI视频生成工作室

一个基于Agent架构的智能视频生成平台，支持从故事创意到视频产出的完整工作流。

## 功能特性

### 📖 智能Agent系统
- **故事分析Agent**: 分析故事创意，提取关键元素
- **分镜脚本Agent**: 基于故事分析生成详细分镜脚本
- **角色设计Agent**: 自动设计角色形象和特征

### 🎬 多模型视频生成
- **文生图**: 通义万相文生图模型 (wanx-v1)
- **图生视频**: 通义万相图生视频Flash模型
- **文生视频**: 
  - 通义万相文生视频Plus模型
  - 本地部署T2V模型支持
- **首尾帧视频**: 通义万相首尾帧插值视频生成
- **图片编辑**: AI图片编辑和优化

### 🗂️ 项目管理
- 完整的项目文件组织结构
- 素材管理（图片、视频、音频）
- 生成历史记录和版本控制
- 文件预览和管理功能

### 🎨 现代化Web界面
- 响应式三栏布局设计
- 拖拽上传文件支持
- 实时预览功能
- 右键菜单文件操作

## 项目架构

```
video_tool_mix/
├── agents/           # AI Agent模块
│   ├── story_agent.py        # 故事分析
│   ├── storyboard_agent.py   # 分镜脚本
│   └── character_agent.py    # 角色设计
├── api/             # 视频生成API
│   ├── qwen_t2i_flash.py     # 文生图API
│   ├── qwen_i2v_flash.py     # 图生视频API
│   ├── qwen_t2v_plus.py      # 文生视频API
│   ├── qwen_local_t2v.py     # 本地T2V API
│   ├── qwen_keyframe_plus.py # 首尾帧API
│   └── qwen_image_edit.py    # 图片编辑API
├── llm/             # LLM提供商
│   ├── claude_llm.py         # Claude接口
│   └── free_llm.py           # 免费LLM接口
├── services/        # 核心服务
│   └── project_manager.py    # 项目管理
├── web/             # Web界面
│   ├── app.py               # Flask主应用
│   └── templates/           # HTML模板
└── projects/        # 项目数据存储
```

## 快速开始

### 一键设置（推荐）
```bash
# 克隆项目
git clone https://github.com/ramaalpaca/video_tool_mix.git
cd video_tool_mix

# 安装依赖
pip install -r requirements.txt

# 运行设置脚本
python setup.py
```

设置脚本会自动：
- 创建.env配置文件
- 创建必要目录
- 检查依赖和配置
- 提供API密钥获取指引

### 手动设置

### 环境要求
- Python 3.8+
- Flask
- asyncio
- aiohttp
- 通义千问API密钥

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API密钥（重要！）

**⚠️ 必须配置API密钥才能使用Agent功能**

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，添加你的API密钥：
```env
# 必需：Dashscope API密钥（免费）
DASHSCOPE_API_KEY=sk-your_dashscope_api_key_here

# 可选：Claude API密钥（优先使用）
ANTHROPIC_API_KEY=your_claude_api_key_here

# 可选：OpenAI API密钥
OPENAI_API_KEY=your_openai_api_key_here
```

#### 获取API密钥：

**Dashscope（推荐，免费）：**
1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 注册并登录阿里云账号
3. 进入"API-KEY管理"创建新的API Key
4. 复制API Key到 `.env` 文件中

**Claude（可选，性能更好）：**
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建账号并获取API Key
3. 复制到 `.env` 文件中

### 启动应用
```bash
python web/app.py
```

应用将在 `http://localhost:30001` 启动。

## 使用指南

### 1. 创建项目
- 在左侧面板点击"创建新项目"
- 输入项目名称和描述

### 2. 上传素材
- 拖拽文件到上传区域
- 或点击上传区域选择文件
- 支持图片和视频格式

### 3. 使用Agent
- **故事分析**: 输入故事创意，AI自动分析关键要素
- **分镜脚本**: 基于故事分析生成详细分镜
- **角色设计**: 自动设计角色形象

### 4. 生成视频内容
- **文生图**: 根据提示词生成图片
- **图生视频**: 将图片转换为视频
- **文生视频**: 直接从文本生成视频
- **图片编辑**: AI编辑和优化图片

### 5. 文件管理
- 右键点击文件进行重命名或删除
- 在右侧预览面板查看内容
- 所有生成内容自动保存到项目中

## 本地模型支持

平台支持本地部署的T2V模型，默认连接到 `http://192.168.3.4:8888`。

本地模型特点：
- 支持64倍数分辨率（自动调整）
- 可配置帧数和帧率
- 支持自定义分辨率

## API接口

### Agent执行
```bash
POST /api/agents/{agent_type}/execute
{
    "project_id": "项目ID",
    "input_data": {...},
    "save_result": true
}
```

### 内容生成
```bash
POST /api/generate/{task_type}
{
    "model": "模型名称",
    "project_id": "项目ID",
    "prompt": "提示词",
    ...
}
```

## 技术栈

- **后端**: Python Flask + AsyncIO
- **前端**: HTML5 + CSS3 + JavaScript
- **AI集成**: 通义千问系列模型
- **LLM**: Claude/通义千问大语言模型
- **文件存储**: 本地文件系统

## 常见问题

### ❌ "story agent is not available" 错误
**原因**: 没有配置LLM API密钥，导致Agent无法初始化

**解决方案**:
1. 确保已配置 `DASHSCOPE_API_KEY` 在 `.env` 文件中
2. 重启应用 `python web/app.py`
3. 检查控制台是否显示 "Using Dashscope LLM" 或 "Using Claude LLM"

### ❌ API请求失败
**原因**: API密钥无效或网络连接问题

**解决方案**:
1. 验证API密钥是否正确
2. 检查网络连接
3. 确认API密钥有足够的配额

### ❌ 本地T2V模型连接失败
**原因**: 本地模型服务未启动或地址错误

**解决方案**:
1. 确认本地T2V服务已启动（默认 `http://192.168.3.4:8888`）
2. 修改 `api/qwen_local_t2v.py` 中的 `base_url` 参数

### 📱 启动检查清单
启动应用时，控制台应显示：
```
Using Dashscope LLM  # 或 Using Claude LLM
 * Running on http://127.0.0.1:30001
```

如果看到 "Warning: No LLM provider available"，说明API密钥配置有问题。

## 开发计划

- [ ] 场景设计Agent
- [ ] 视频后处理功能  
- [ ] 音频生成和编辑
- [ ] 批量处理支持
- [ ] Docker部署支持
- [ ] 更多模型集成

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

MIT License