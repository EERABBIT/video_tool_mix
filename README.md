# 通义千问视频生成工具集

基于阿里云通义千问API的AI视频生成工具集，支持文生图、图生视频、文生视频、首尾帧视频、图片编辑等多种生成模式。

## 🚀 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置API密钥（可选）

```bash
export DASHSCOPE_API_KEY="sk-c4af8d8ed01d43a587eda9b8c3b32058"
```

注：代码中已配置默认API密钥，可直接使用

### 3. 启动Web服务

```bash
python app.py
```

服务将在 **http://localhost:30001** 启动

## 📁 项目结构

```
video_tool_mix/
├── app.py                    # Flask Web服务主文件
├── requirements.txt          # 项目依赖
├── templates/               # HTML模板
│   └── index.html          # Web界面
├── static/                 # 静态资源
├── assets/                 # 素材文件夹
│   ├── images/            # 图片素材
│   └── videos/            # 视频素材
├── output/                 # 输出文件夹
│   ├── keyframe_plus/     # 首尾帧视频输出
│   └── image_edit/       # 图片编辑输出
├── uploads/               # 上传文件夹
└── test_output/           # 测试输出
```

## 🎯 功能模块

### 1. 文生图 (Text to Image)
- **文件:** `qwen_t2i_flash.py`
- **API端点:** `/api/text-to-image`
- **模型:** wanx-v1
- **生成时间:** 10-30秒

### 2. 图生视频 (Image to Video)
- **文件:** `qwen_i2v_flash.py`
- **API端点:** `/api/image-to-video`
- **模型:** wanx-i2v-flash
- **生成时间:** 3-5分钟

### 3. 文生视频 (Text to Video)
- **文件:** `qwen_t2v_plus.py`
- **API端点:** `/api/text-to-video`
- **模型:** wanx2.0-t2v-plus
- **生成时间:** 3-5分钟

### 4. 首尾帧视频 (Keyframe to Video)
- **文件:** `qwen_keyframe_plus.py`
- **API端点:** `/api/keyframe-to-video`
- **模型:** wanx2.1-kf2v-plus
- **生成时间:** 7-10分钟
- **特点:** 支持完整流程（提交→轮询→下载）

### 5. 图片编辑 (Image Edit) ⭐新功能
- **文件:** `qwen_image_edit.py`
- **API端点:** `/api/image-edit`
- **模型:** qwen-image-edit
- **生成时间:** 1-2分钟
- **特点:** 基于文本指令编辑图片，支持风格转换、细节修改等

## 🔧 独立测试各模块

### 测试首尾帧视频生成
```bash
python qwen_keyframe_plus.py
```

### 测试文生图
```bash
python qwen_t2i_flash.py
```

### 测试图生视频
```bash
python qwen_i2v_flash.py
```

### 测试文生视频
```bash
python qwen_t2v_plus.py
```

### 测试图片编辑
```bash
python qwen_image_edit.py
```

## 📝 API调用示例

### 首尾帧视频生成（新功能）
```python
import requests

url = "http://localhost:30001/api/keyframe-to-video"
data = {
    "first_frame_path": "assets/images/first.png",
    "last_frame_path": "assets/images/last.png",
    "prompt": "流畅的过渡动画",
    "resolution": "720P",
    "prompt_extend": True
}

response = requests.post(url, json=data)
result = response.json()
```

### 文生图
```python
url = "http://localhost:30001/api/text-to-image"
data = {
    "prompt": "一只可爱的小猫",
    "negative_prompt": "模糊",
    "size": "1024*1024",
    "style": "auto",
    "n": 1
}
```

### 图生视频
```python
url = "http://localhost:30001/api/image-to-video"
data = {
    "image_path": "assets/images/cat.png",
    "prompt": "让画面动起来",
    "duration": 5,
    "fps": 30,
    "resolution": "1280*720"
}
```

### 文生视频
```python
url = "http://localhost:30001/api/text-to-video"
data = {
    "prompt": "一只猫在花园里奔跑",
    "duration": 5,
    "style": "realistic",
    "motion_strength": 0.7,
    "resolution": "1280*720"
}
```

### 图片编辑
```python
url = "http://localhost:30001/api/image-edit"
data = {
    "image_path": "assets/images/cat.png",
    "edit_instruction": "给小猫戴一个红色圣诞帽",
    "negative_prompt": "模糊，低质量",
    "watermark": False
}
```

## ⚙️ 配置说明

### API密钥配置
- 环境变量: `DASHSCOPE_API_KEY`
- 默认值: `sk-c4af8d8ed01d43a587eda9b8c3b32058`（已配置）

### 端口配置
- 默认端口: **30001**
- 修改位置: `app.py` 第414行

### 输出目录
- 图片: `output/`
- 视频: `output/keyframe_plus/`
- 图片编辑: `output/image_edit/`
- 素材: `assets/`

## 🧪 测试工具

- `test.py` - 首尾帧视频完整测试
- `quick_test.py` - 快速API连通性测试
- `check_task.py` - 任务状态查询工具
- `test_keyframe_integration.py` - 集成测试

## 📊 任务处理流程

1. **提交任务** - 将请求发送到API
2. **获取任务ID** - API返回任务标识
3. **轮询状态** - 每30秒查询一次
4. **下载结果** - 任务完成后下载视频
5. **保存到本地** - 自动保存到output目录

## ⏱️ 生成时间参考

| 功能 | 时间 | 分辨率 |
|------|------|--------|
| 文生图 | 10-30秒 | 1024×1024 |
| 图生视频 | 3-5分钟 | 1280×720 |
| 文生视频 | 3-5分钟 | 1280×720 |
| 首尾帧视频 | 7-10分钟 | 720P/1080P |
| 图片编辑 | 1-2分钟 | 1024×1024 |

## 🔍 常见问题

### 1. API连接超时
- 检查网络连接
- 确认API密钥有效
- 可能需要代理设置

### 2. 视频生成失败
- 检查图片格式（支持PNG/JPG）
- 确保图片文件存在
- 分辨率使用720P或1080P

### 3. 端口被占用
```bash
# 查看端口占用
lsof -i:30001

# 修改端口
# 编辑 app.py 第414行
```

### 4. 依赖安装失败
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 💡 使用提示

1. **首尾帧视频生成**
   - 选择两张关联图片作为首尾帧
   - 提示词描述过渡动画效果
   - 建议使用720P分辨率
   - 启用提示词扩展获得更好效果

2. **文生图优化**
   - 详细描述场景和风格
   - 使用负向提示词排除不想要的元素
   - 可设置seed值获得可重复结果

3. **视频生成建议**
   - 图片质量影响视频效果
   - 动作幅度通过motion_strength控制
   - 复杂场景可能需要更长生成时间

4. **图片编辑技巧**
   - 使用清晰的编辑指令描述想要的效果
   - 负向提示词帮助排除不想要的结果
   - 支持颜色调整、风格转换、添加物体等
   - 编辑结果会自动保存到素材库

## 📞 支持

- API文档: https://help.aliyun.com/zh/dashscope/
- 百炼平台: https://bailian.console.aliyun.com/
- 问题反馈: 提交Issue到项目仓库

## 📄 许可

本项目仅供学习和研究使用。