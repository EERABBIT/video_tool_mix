#!/usr/bin/env python3
"""
视频生成平台主应用 - 改进版
支持Agent独立执行和模型选择
"""

import os
import json
import asyncio
import platform
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import uuid

# Windows兼容性设置
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 添加项目根目录到Python路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入服务
from services.project_manager import ProjectManager

# 导入LLM
from llm.free_llm import FreeLLM
try:
    from llm.claude_llm import ClaudeLLM
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("Claude LLM not available (anthropic not installed)")

# 导入Agents
from agents.story_agent import StoryAnalysisAgent
from agents.storyboard_agent import StoryboardAgent
from agents.character_agent import CharacterDesignAgent

# 导入所有图像/视频生成API
from api.qwen_t2i_flash import QwenAPITester  # 文生图
from api.qwen_i2v_flash import QwenI2VFlashAPI  # 图生视频
from api.qwen_t2v_plus import QwenT2VPlusAPI  # 文生视频Plus
from api.qwen_keyframe_plus import QwenKeyframePlusAPI  # 首尾帧视频
from api.qwen_image_edit import QwenImageEditAPI  # 图片编辑
from api.qwen_local_t2v import QwenLocalT2VAPI  # 本地文生视频

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# 初始化项目管理器
project_manager = ProjectManager()

# 初始化LLM（默认使用免费的Dashscope）
llm_provider = None
if CLAUDE_AVAILABLE:
    try:
        llm_provider = ClaudeLLM()
        print("Using Claude LLM")
    except:
        pass

if not llm_provider:
    try:
        llm_provider = FreeLLM(provider="dashscope")
        print("Using Dashscope LLM")
    except Exception as e:
        print(f"Warning: No LLM provider available - {e}")
        llm_provider = None

# 初始化Agents
agents = {}
if llm_provider:
    agents["story"] = StoryAnalysisAgent(llm_provider, project_manager)
    agents["storyboard"] = StoryboardAgent(llm_provider, project_manager)
    agents["character"] = CharacterDesignAgent(llm_provider, project_manager)

# 初始化所有图像/视频API
apis = {
    "text-to-image": {
        "wanx-v1": QwenAPITester(),  # 通义万相文生图
    },
    "image-to-video": {
        "wanx-i2v-flash": QwenI2VFlashAPI(),  # 通义万相图生视频
    },
    "text-to-video": {
        "wanx-t2v-plus": QwenT2VPlusAPI(),  # 通义万相文生视频Plus
        "local-t2v": QwenLocalT2VAPI(),  # 本地文生视频
    },
    "keyframe-video": {
        "wanx-kf2v-plus": QwenKeyframePlusAPI(),  # 首尾帧视频
    },
    "image-edit": {
        "qwen-image-edit": QwenImageEditAPI(),  # 图片编辑
    }
}

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    return render_template('index_v2.html')

# ==================== 项目管理API ====================

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """获取项目列表"""
    projects = project_manager.list_projects()
    return jsonify({"success": True, "projects": projects})

@app.route('/api/projects', methods=['POST'])
def create_project():
    """创建新项目"""
    data = request.json
    name = data.get('name', 'Untitled Project')
    description = data.get('description', '')
    
    project = project_manager.create_project(name, description)
    return jsonify({"success": True, "project": project})

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """获取项目详情"""
    project = project_manager.get_project(project_id)
    
    if project:
        return jsonify({"success": True, "project": project})
    else:
        return jsonify({"success": False, "error": "Project not found"}), 404

@app.route('/api/projects/<project_id>/structure', methods=['GET'])
def get_project_structure(project_id):
    """获取项目文件结构"""
    project_path = Path(project_manager.base_path) / project_id
    
    if not project_path.exists():
        return jsonify({"success": False, "error": "Project not found"}), 404
    
    structure = {
        "assets": {
            "images": [],
            "videos": [],
            "audios": []
        },
        "prompts": {
            "story": [],
            "storyboard": [],
            "characters": [],
            "scenes": [],
            "shots": [],
            "videos": []
        },
        "outputs": {
            "references": [],
            "storyboards": [],
            "videos": []
        }
    }
    
    # 扫描素材
    for asset_type in ["images", "videos", "audios"]:
        asset_dir = project_path / "assets" / asset_type
        if asset_dir.exists():
            structure["assets"][asset_type] = [f.name for f in asset_dir.iterdir() if f.is_file()]
    
    # 扫描prompts
    for prompt_type in structure["prompts"].keys():
        prompt_dir = project_path / "prompts" / prompt_type
        if prompt_dir.exists():
            structure["prompts"][prompt_type] = [f.name for f in prompt_dir.glob("*.json")]
    
    # 扫描输出
    for output_type in structure["outputs"].keys():
        output_dir = project_path / "outputs" / output_type
        if output_dir.exists():
            structure["outputs"][output_type] = [f.name for f in output_dir.iterdir() if f.is_file()]
    
    return jsonify({"success": True, "structure": structure})

@app.route('/api/projects/<project_id>/prompts/<prompt_type>', methods=['GET'])
def get_project_prompts(project_id, prompt_type):
    """获取项目的特定类型prompts"""
    prompts = project_manager.get_project_prompts(project_id, prompt_type)
    return jsonify({"success": True, "prompts": prompts})

@app.route('/api/projects/<project_id>/file', methods=['GET'])
def get_project_file(project_id):
    """获取项目文件内容（用于预览）"""
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({"success": False, "error": "File path required"}), 400
    
    project_path = Path(project_manager.base_path) / project_id / file_path
    
    if not project_path.exists():
        return jsonify({"success": False, "error": "File not found"}), 404
    
    # 判断文件类型
    file_ext = project_path.suffix.lower()
    
    # 对于JSON文件，返回内容
    if file_ext == '.json':
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return jsonify({"success": True, "type": "json", "content": content})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    # 对于图片和视频，返回URL
    elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.mp4', '.avi', '.mov']:
        # 返回可访问的URL路径
        url = f"/projects/{project_id}/{file_path}"
        return jsonify({"success": True, "type": "media", "url": url})
    
    # 对于文本文件
    elif file_ext in ['.txt', '.md', '.log']:
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({"success": True, "type": "text", "content": content})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    else:
        return jsonify({"success": False, "error": "Unsupported file type"}), 400

# ==================== Agent执行API（独立执行） ====================

@app.route('/api/agents', methods=['GET'])
def list_agents():
    """获取可用的Agents列表"""
    agent_list = []
    for name, agent in agents.items():
        agent_list.append({
            "name": name,
            "description": agent.description,
            "available": True
        })
    
    # 添加未实现的Agent信息
    unimplemented = [
        {"name": "scene", "description": "场景设计Agent", "available": False},
        {"name": "shot_prompt", "description": "分镜Prompt生成Agent", "available": False},
        {"name": "image_optimize", "description": "图像优化Agent", "available": False},
        {"name": "video_prompt", "description": "视频Prompt生成Agent", "available": False},
    ]
    agent_list.extend(unimplemented)
    
    return jsonify({"success": True, "agents": agent_list})

@app.route('/api/agents/<agent_type>/execute', methods=['POST'])
def execute_agent(agent_type):
    """独立执行单个Agent"""
    if agent_type not in agents:
        return jsonify({"success": False, "error": f"Agent '{agent_type}' not available"}), 400
    
    data = request.json
    project_id = data.get('project_id')
    input_data = data.get('input_data', {})
    save_result = data.get('save_result', True)  # 是否保存结果
    
    if not project_id:
        return jsonify({"success": False, "error": "project_id is required"}), 400
    
    try:
        agent = agents[agent_type]
        
        # 创建事件循环来运行异步代码
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(agent.execute(project_id, input_data, save_result))
        loop.close()
        
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== 模型API（支持选择） ====================

@app.route('/api/models', methods=['GET'])
def list_models():
    """获取所有可用的模型"""
    models = {}
    for task_type, task_models in apis.items():
        models[task_type] = list(task_models.keys())
    return jsonify({"success": True, "models": models})

@app.route('/api/generate/<task_type>', methods=['POST'])
def generate_content(task_type):
    """通用生成接口，支持模型选择"""
    if task_type not in apis:
        return jsonify({"success": False, "error": f"Unknown task type: {task_type}"}), 400
    
    data = request.json
    model_name = data.get('model', None)
    project_id = data.get('project_id')
    
    # 如果没有指定模型，使用第一个可用的
    if not model_name:
        model_name = list(apis[task_type].keys())[0]
    
    if model_name not in apis[task_type]:
        return jsonify({"success": False, "error": f"Unknown model: {model_name} for task: {task_type}"}), 400
    
    api = apis[task_type][model_name]
    
    try:
        result = None
        
        # 创建事件循环来运行异步代码
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 根据不同的任务类型调用不同的方法
        if task_type == "text-to-image":
            prompt = data.get('prompt', '')
            negative_prompt = data.get('negative_prompt', '')
            size = data.get('size', '1920*1080')
            style = data.get('style', 'auto')
            
            # 使用QwenAPITester的内部方法
            async def generate_image():
                # 提交任务
                task_id = await api._submit_generation_task(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    size=size,
                    n=1,
                    style=style,
                    seed=None
                )
                # 轮询状态
                result_data = await api._poll_task_status(task_id)
                # 下载图片
                if result_data and result_data.get("images"):
                    image_url = result_data["images"][0]
                    import time
                    output_path = api.output_dir / f"gen_{int(time.time())}.png"
                    await api._download_image(image_url, output_path)
                    return str(output_path)
                return None
            
            result = loop.run_until_complete(generate_image())
            
        elif task_type == "image-to-video":
            image_path = data.get('image_path', '')
            # 如果是相对路径，转换为项目的完整路径
            if image_path and project_id and not os.path.isabs(image_path):
                project_path = Path(project_manager.base_path) / project_id
                image_path = str(project_path / image_path)
            prompt = data.get('prompt', '')
            negative_prompt = data.get('negative_prompt', '')
            duration = data.get('duration', 5)
            fps = data.get('fps', 30)
            resolution = data.get('resolution', '1280*720')
            # QwenI2VFlashAPI的generate_video方法
            api_result = loop.run_until_complete(api.generate_video(
                image_path, prompt, negative_prompt, duration, fps, resolution
            ))
            # 提取local_path作为result
            result = api_result.get('local_path') if api_result and api_result.get('status') == 'success' else None
            
        elif task_type == "text-to-video":
            prompt = data.get('prompt', '')
            negative_prompt = data.get('negative_prompt', '')
            duration = data.get('duration', 5)
            fps = data.get('fps', 30)
            resolution = data.get('resolution', '1920*1080')
            style = data.get('style', 'realistic')
            motion_strength = data.get('motion_strength', 0.5)
            seed = data.get('seed')
            # QwenT2VPlusAPI和QwenLocalT2VAPI的generate_text_to_video方法
            api_result = loop.run_until_complete(api.generate_text_to_video(
                prompt=prompt, 
                negative_prompt=negative_prompt, 
                duration=duration, 
                fps=fps, 
                resolution=resolution, 
                seed=seed,
                style=style, 
                motion_strength=motion_strength
            ))
            # 提取local_path作为result
            result = api_result.get('local_path') if api_result and api_result.get('status') == 'success' else None
                
        elif task_type == "keyframe-video":
            first_frame = data.get('first_frame_path', '')
            last_frame = data.get('last_frame_path', '')
            # 转换路径
            if project_id:
                project_path = Path(project_manager.base_path) / project_id
                if first_frame and not os.path.isabs(first_frame):
                    first_frame = str(project_path / first_frame)
                if last_frame and not os.path.isabs(last_frame):
                    last_frame = str(project_path / last_frame)
            prompt = data.get('prompt', '')
            resolution = data.get('resolution', '720P')
            prompt_extend = data.get('prompt_extend', True)
            # QwenKeyframePlusAPI的generate_keyframe_video方法
            api_result = loop.run_until_complete(api.generate_keyframe_video(
                first_frame, last_frame, prompt, resolution, prompt_extend
            ))
            # 提取local_path作为result
            result = api_result.get('local_path') if api_result and api_result.get('status') == 'success' else None
            
        elif task_type == "image-edit":
            image_path = data.get('image_path', '')
            # 转换路径
            if image_path and project_id and not os.path.isabs(image_path):
                project_path = Path(project_manager.base_path) / project_id
                image_path = str(project_path / image_path)
            instruction = data.get('edit_instruction', '')
            negative_prompt = data.get('negative_prompt', '')
            watermark = data.get('watermark', False)
            # QwenImageEditAPI的edit_image方法
            api_result = loop.run_until_complete(api.edit_image(
                image_path, instruction, negative_prompt, watermark
            ))
            # 提取local_path作为result
            result = api_result.get('local_path') if api_result and api_result.get('status') == 'success' else None
        
        loop.close()
        
        if result and project_id:
            # 根据任务类型保存到相应目录
            output_type = "references" if "image" in task_type else "videos"
            saved_path = project_manager.save_output(project_id, output_type, result)
            
            return jsonify({
                "success": True, 
                "result_path": result,
                "saved_path": saved_path,
                "model_used": model_name
            })
        
        return jsonify({"success": True, "result_path": result, "model_used": model_name})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== 素材管理API ====================

@app.route('/api/projects/<project_id>/assets', methods=['POST'])
def upload_asset(project_id):
    """上传素材"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    
    file = request.files['file']
    asset_type = request.form.get('type', 'image')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        # 保存临时文件
        filename = secure_filename(file.filename)
        temp_path = Path(f"/tmp/{filename}")
        file.save(str(temp_path))
        
        # 添加到项目
        result = project_manager.add_asset(project_id, str(temp_path), asset_type)
        
        # 删除临时文件
        temp_path.unlink()
        
        if result:
            return jsonify({"success": True, "path": result})
        else:
            return jsonify({"success": False, "error": "Failed to add asset"}), 500
    
    return jsonify({"success": False, "error": "Invalid file type"}), 400

@app.route('/api/projects/<project_id>/rename', methods=['POST'])
def rename_file(project_id):
    """重命名文件"""
    data = request.json
    old_path = data.get('old_path')
    new_name = data.get('new_name')
    
    if not old_path or not new_name:
        return jsonify({"success": False, "error": "Missing parameters"}), 400
    
    try:
        project_path = Path(project_manager.base_path) / project_id
        old_file = project_path / old_path
        
        if not old_file.exists():
            return jsonify({"success": False, "error": "File not found"}), 404
        
        # 构建新路径
        new_file = old_file.parent / new_name
        
        # 检查新文件名是否已存在
        if new_file.exists():
            return jsonify({"success": False, "error": "File name already exists"}), 400
        
        # 重命名文件
        old_file.rename(new_file)
        
        # 记录到历史
        project_manager._add_history(project_id, "file_renamed", {
            "old_path": old_path,
            "new_path": str(new_file.relative_to(project_path)),
            "old_name": old_file.name,
            "new_name": new_name
        })
        
        return jsonify({"success": True, "new_path": str(new_file.relative_to(project_path))})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/projects/<project_id>/delete', methods=['POST'])
def delete_file(project_id):
    """删除文件"""
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({"success": False, "error": "Missing file path"}), 400
    
    try:
        project_path = Path(project_manager.base_path) / project_id
        target_file = project_path / file_path
        
        if not target_file.exists():
            return jsonify({"success": False, "error": "File not found"}), 404
        
        # 删除文件
        target_file.unlink()
        
        # 记录到历史
        project_manager._add_history(project_id, "file_deleted", {
            "file_path": file_path,
            "file_name": target_file.name,
            "file_type": "image" if file_path.startswith("assets/images") or file_path.startswith("outputs/references") else "video"
        })
        
        return jsonify({"success": True, "message": "File deleted successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== 静态文件服务 ====================

@app.route('/projects/<path:filename>')
def serve_project_file(filename):
    """提供项目文件访问"""
    # 使用绝对路径
    base_path = Path(__file__).parent.parent / "projects"
    return send_from_directory(str(base_path), filename)

@app.route('/assets/<path:filename>')
def serve_asset_file(filename):
    """提供素材文件访问"""
    return send_from_directory('assets', filename)

if __name__ == '__main__':
    app.run(debug=True, port=30001)