# AI视频生成平台

一个基于Agent架构的智能视频生成系统，支持文生图、图生视频等多种AI生成功能。

## 快速开始

### 环境要求
- Python 3.8+
- 阿里云账号（获取API密钥）

### 安装步骤

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 配置API密钥
```bash
cp .env.example .env
# 编辑.env文件，填入你的DASHSCOPE_API_KEY
```

3. 启动应用
```bash
python web/app.py
```

访问 http://localhost:30001 开始使用。

## 核心功能

### Agent系统
- 故事分析Agent
- 分镜脚本Agent  
- 角色设计Agent

### 生成能力
- 文生图（Text to Image）
- 图生视频（Image to Video）
- 文生视频（Text to Video）
- 图片编辑

## 项目结构

```
├── agents/          # AI Agent模块
├── api/            # 视频生成API接口
├── llm/            # 大语言模型接口
├── services/       # 核心服务
├── web/            # Web应用
└── projects/       # 项目数据存储
```

## 使用提示

1. 首次使用需要配置API密钥，否则Agent功能无法使用
2. 生成的内容会自动保存在projects目录下
3. 支持拖拽上传文件到Web界面

## API密钥获取

访问[阿里云百炼平台](https://bailian.console.aliyun.com/)注册并创建API Key。

## 问题排查

如果遇到"agent is not available"错误，请检查：
1. .env文件中的DASHSCOPE_API_KEY是否正确配置
2. 重启应用后查看控制台是否显示"Using Dashscope LLM"

---
*更多细节请自行探索代码和文档*