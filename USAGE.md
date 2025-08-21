# 🎬 AI视频生成平台 - 使用指南

## 系统特性

### ✅ 已完成的改进

1. **Agent独立执行** - 每个Agent可以单独调用和调试
2. **结果自动保存** - Agent结果保存到`projects/{project_id}/prompts/`目录
3. **模型选择功能** - 支持选择不同的生成模型（如文生视频有2个模型可选）
4. **项目结构可视化** - 实时显示项目的素材、prompts和输出
5. **完整的API集成** - 所有图像/视频生成API都已集成

## 快速开始

### 1. 启动服务
```bash
python run.py
```
访问: http://localhost:30001

### 2. 创建项目
点击左侧"+ 创建新项目"按钮

### 3. Agent工作流

#### 独立执行模式
1. **故事分析** → 输入故事 → 执行 → 结果保存到`prompts/story/`
2. **分镜脚本** → 选择已有故事分析 → 执行 → 结果保存到`prompts/storyboard/`
3. **角色设计** → 选择已有故事分析 → 执行 → 结果保存到`prompts/characters/`

每个Agent的结果都会：
- 自动保存到项目目录
- 在Prompts管理面板中显示
- 可供后续Agent使用

### 4. 模型生成

#### 文生图
- 模型：通义万相 v1
- 输入：文本描述
- 输出：保存到`outputs/references/`

#### 图生视频
- 模型：通义万相 Flash
- 输入：选择项目中的图像 + 动态描述
- 输出：保存到`outputs/videos/`

#### 文生视频（2个模型可选）
- 模型1：通义万相 Plus
- 模型2：本地模型
- 输入：文本描述
- 输出：保存到`outputs/videos/`

#### 首尾帧视频
- 模型：通义万相 KF2V Plus
- 输入：首帧图像 + 尾帧图像 + 过渡描述
- 输出：保存到`outputs/videos/`

#### 图片编辑
- 模型：Qwen Image Edit
- 输入：选择图像 + 编辑指令
- 输出：保存到`outputs/references/`

## 界面布局

```
┌─────────────────────────────────────────────┐
│                  顶部导航栏                   │
├────────────┬─────────────────────────────────┤
│            │  ┌──────────┬──────────┐        │
│   项目列表  │  │Agent控制 │模型生成   │        │
│            │  ├──────────┼──────────┤        │
│            │  │项目结构   │Prompts   │        │
│            │  └──────────┴──────────┘        │
└────────────┴─────────────────────────────────┘
```

## 项目文件结构

```
projects/{project_id}/
├── metadata.json          # 项目元数据
├── assets/               # 素材文件
│   ├── images/          # 图片素材
│   └── videos/          # 视频素材
├── prompts/             # Agent生成的prompts
│   ├── story/           # 故事分析结果
│   ├── storyboard/      # 分镜脚本
│   ├── characters/      # 角色设计
│   └── scenes/          # 场景设计
└── outputs/             # 生成结果
    ├── references/      # 参考图像
    └── videos/          # 生成的视频
```

## API接口

### Agent执行
```bash
POST /api/agents/{agent_type}/execute
{
    "project_id": "xxx",
    "input_data": {...},
    "save_result": true  # 是否保存结果
}
```

### 模型生成（带模型选择）
```bash
POST /api/generate/{task_type}
{
    "project_id": "xxx",
    "model": "model_name",  # 指定模型
    "prompt": "...",
    ...
}
```

### 获取项目结构
```bash
GET /api/projects/{project_id}/structure
```

### 获取项目Prompts
```bash
GET /api/projects/{project_id}/prompts/{prompt_type}
```

## 工作流示例

### 完整创作流程
1. 创建项目 "科幻短片"
2. 执行故事分析Agent → 生成故事结构
3. 执行分镜脚本Agent → 生成镜头序列
4. 执行角色设计Agent → 生成角色设计
5. 使用角色的reference_image_prompt → 文生图生成角色参考图
6. 使用分镜的complete_prompt → 文生图生成分镜图
7. 使用分镜图 → 图生视频生成动态镜头
8. 组合所有视频片段完成作品

### 独立调试模式
- 可以单独测试每个Agent
- 可以手动编辑保存的prompts
- 可以选择不同的模型进行对比
- 可以重复执行直到满意

## 注意事项

1. **API密钥配置**：确保`.env`文件中配置了`DASHSCOPE_API_KEY`
2. **文件路径**：图像路径使用相对于项目根目录的路径
3. **模型选择**：不同模型可能有不同的参数要求
4. **结果保存**：所有Agent结果和生成内容都自动保存到项目目录

## 常见问题

**Q: Agent执行失败？**
A: 检查LLM API密钥是否配置正确

**Q: 找不到生成的文件？**
A: 查看项目结构面板，所有文件都在对应目录中

**Q: 如何使用不同的模型？**
A: 在模型生成面板中选择对应的模型选项

**Q: 如何查看保存的Prompts？**
A: 点击Prompts管理面板的对应标签