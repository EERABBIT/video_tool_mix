#!/usr/bin/env python3
"""
视频生成工具Web服务
"""

import os
import json
import asyncio
import time
import platform
from pathlib import Path

# Windows上的asyncio兼容性设置
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import uuid

from qwen_t2i_flash import QwenAPITester  # 文生图API
from qwen_i2v_flash import QwenI2VFlashAPI  # 图生视频API
from qwen_t2v_plus import QwenT2VPlusAPI  # 文生视频API
from qwen_keyframe_plus import QwenKeyframePlusAPI  # 首尾帧视频API
from qwen_image_edit import QwenImageEditAPI  # 图片编辑API
from qwen_local_t2v import QwenLocalT2VAPI  # 本地文生视频API

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 配置路径
UPLOAD_FOLDER = Path('./uploads')
OUTPUT_FOLDER = Path('./output')
ASSETS_FOLDER = Path('./assets')

# 创建必要的目录
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, ASSETS_FOLDER]:
    folder.mkdir(exist_ok=True)
    
# 创建assets子目录
(ASSETS_FOLDER / 'images').mkdir(exist_ok=True)
(ASSETS_FOLDER / 'videos').mkdir(exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def copy_to_assets(source_path, file_type='image'):
    """将生成的文件复制到assets目录"""
    import shutil
    
    source = Path(source_path)
    if not source.exists():
        print(f"源文件不存在: {source}")
        return None
    
    # 生成新的文件名
    timestamp = int(time.time())
    source_filename = source.name
    filename = f"generated_{timestamp}_{source_filename}"
    
    # 确定目标路径
    if file_type == 'image':
        target_path = ASSETS_FOLDER / 'images' / filename
    else:
        target_path = ASSETS_FOLDER / 'videos' / filename
    
    try:
        # 复制文件
        shutil.copy2(source, target_path)
        print(f"文件已复制到assets: {target_path}")
        return str(target_path)
    except Exception as e:
        print(f"复制文件到assets失败: {e}")
        return None

# 初始化API
text_to_image_api = QwenAPITester()
image_to_video_api = QwenI2VFlashAPI()
text_to_video_api = QwenT2VPlusAPI()
keyframe_video_api = QwenKeyframePlusAPI()
image_edit_api = QwenImageEditAPI()
local_t2v_api = QwenLocalT2VAPI()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/assets')
def list_assets():
    """获取素材列表"""
    assets = []
    
    for file_path in ASSETS_FOLDER.rglob('*'):
        if file_path.is_file() and allowed_file(file_path.name):
            relative_path = file_path.relative_to(ASSETS_FOLDER)
            file_info = {
                'name': file_path.name,
                'path': str(relative_path),
                'size': file_path.stat().st_size,
                'type': 'image' if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif'] else 'video'
            }
            assets.append(file_info)
    
    return jsonify({'assets': assets})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    save_to_assets = request.form.get('saveToAssets', 'false') == 'true'
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        if save_to_assets:
            # 根据文件类型决定保存路径
            file_ext = filename.rsplit('.', 1)[1].lower()
            if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                file_path = ASSETS_FOLDER / 'images' / unique_filename
            else:
                file_path = ASSETS_FOLDER / 'videos' / unique_filename
        else:
            file_path = UPLOAD_FOLDER / unique_filename
        
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'path': str(file_path)
        })
    
    return jsonify({'error': '不支持的文件类型'}), 400

@app.route('/api/text-to-image', methods=['POST'])
def text_to_image():
    """文生图"""
    data = request.json
    
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    size = data.get('size', '1024*1024')
    n = data.get('n', 1)
    style = data.get('style', 'auto')
    seed = data.get('seed')
    
    if not prompt:
        return jsonify({'error': '请输入提示词'}), 400
    
    # 异步执行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            text_to_image_api._submit_generation_task(
                prompt=prompt,
                negative_prompt=negative_prompt,
                size=size,
                n=n,
                style=style,
                seed=seed
            )
        )
        
        # 开始轮询任务状态
        poll_result = loop.run_until_complete(
            text_to_image_api._poll_task_status(result)
        )
        
        # 下载图片
        downloaded_files = []
        for idx, image_url in enumerate(poll_result['images']):
            output_path = OUTPUT_FOLDER / f"t2i_{uuid.uuid4().hex}.png"
            loop.run_until_complete(
                text_to_image_api._download_image(image_url, output_path)
            )
            
            # 复制到assets
            asset_path = copy_to_assets(output_path, 'image')
            if asset_path:
                downloaded_files.append(str(Path(asset_path).relative_to(Path.cwd())))
            else:
                downloaded_files.append(str(output_path.relative_to(Path.cwd())))
            
            print(f"图片已保存: {output_path}")
            print(f"Asset路径: {asset_path}")
        
        return jsonify({
            'success': True,
            'task_id': result,
            'images': downloaded_files
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        try:
            loop.close()
        except:
            pass  # 忽略Windows上的关闭循环错误

@app.route('/api/image-to-video', methods=['POST'])
def image_to_video():
    """图生视频"""
    data = request.json
    
    image_path = data.get('image_path', '')
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    duration = data.get('duration', 5)
    fps = data.get('fps', 30)
    resolution = data.get('resolution', '1280*720')
    
    if not image_path:
        return jsonify({'error': '请选择图片'}), 400
    
    # 转换为绝对路径
    if image_path.startswith('/'):
        image_path = image_path[1:]  # 去掉开头的斜杠
    
    full_image_path = Path(image_path).resolve()
    if not full_image_path.exists():
        return jsonify({'error': f'图片文件不存在: {image_path} (完整路径: {full_image_path})'}), 400
    
    print(f"图生视频请求:")
    print(f"  原始路径: {image_path}")
    print(f"  完整路径: {full_image_path}")
    print(f"  文件存在: {full_image_path.exists()}")
    print(f"  文件大小: {full_image_path.stat().st_size if full_image_path.exists() else 'N/A'}")
    
    # 异步执行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            image_to_video_api.generate_video(
                image_path=str(full_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                duration=duration,
                fps=fps,
                resolution=resolution
            )
        )
        
        # 如果生成成功，复制到assets
        if result.get('status') == 'success' and result.get('local_path'):
            asset_path = copy_to_assets(result['local_path'], 'video')
            if asset_path:
                result['local_path'] = str(Path(asset_path).relative_to(Path.cwd()))
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        try:
            loop.close()
        except:
            pass  # 忽略Windows上的关闭循环错误


@app.route('/api/text-to-video', methods=['POST'])
def text_to_video():
    """文生视频"""
    data = request.json
    
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    duration = int(data.get('duration', 5))
    fps = int(data.get('fps', 30))
    resolution = data.get('resolution', '1920*1080')
    style = data.get('style', 'realistic')
    motion_strength = float(data.get('motion_strength', 0.5))
    seed = data.get('seed')
    if seed:
        seed = int(seed) if seed else None
    model = data.get('model', 'qwen-t2v-plus')  # 新增模型选择参数
    
    if not prompt:
        return jsonify({'error': '请输入提示词'}), 400
    
    print(f"🎥 文生视频请求:")
    print(f"  模型: {model}")
    print(f"  提示词: {prompt}")
    print(f"  分辨率: {resolution}")
    print(f"  时长: {duration}秒, 帧率: {fps}fps")
    
    # 异步执行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 根据模型选择API
        if model == 'local-t2v':
            result = loop.run_until_complete(
                local_t2v_api.generate_text_to_video(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    duration=duration,
                    fps=fps,
                    resolution=resolution,
                    seed=seed,
                    style=style,
                    motion_strength=motion_strength
                )
            )
        else:
            # 默认使用通义万相T2V Plus
            result = loop.run_until_complete(
                text_to_video_api.generate_text_to_video(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    duration=duration,
                    fps=fps,
                    resolution=resolution,
                    style=style,
                    motion_strength=motion_strength,
                    seed=seed
                )
            )
        
        # 如果生成成功，复制到assets
        if result.get('status') == 'success' and result.get('local_path'):
            asset_path = copy_to_assets(result['local_path'], 'video')
            if asset_path:
                # 确保返回相对路径
                try:
                    result['local_path'] = str(Path(asset_path).relative_to(Path.cwd()))
                except ValueError:
                    # 如果路径转换失败，直接使用相对路径
                    result['local_path'] = str(Path(asset_path)).replace(str(Path.cwd()) + '/', '')
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        try:
            loop.close()
        except:
            pass  # 忽略Windows上的关闭循环错误

@app.route('/api/keyframe-to-video', methods=['POST'])
def keyframe_to_video():
    """首尾帧生成视频"""
    data = request.json
    
    first_frame_path = data.get('first_frame_path', '')
    last_frame_path = data.get('last_frame_path', '')
    prompt = data.get('prompt', '')
    resolution = data.get('resolution', '720P')
    prompt_extend = data.get('prompt_extend', True)
    
    if not first_frame_path or not last_frame_path:
        return jsonify({'error': '请选择首帧和尾帧图片'}), 400
    
    # 转换为绝对路径
    if first_frame_path.startswith('/'):
        first_frame_path = first_frame_path[1:]
    if last_frame_path.startswith('/'):
        last_frame_path = last_frame_path[1:]
    
    full_first_path = Path(first_frame_path).resolve()
    full_last_path = Path(last_frame_path).resolve()
    
    if not full_first_path.exists():
        return jsonify({'error': f'首帧图片不存在: {first_frame_path}'}), 400
    if not full_last_path.exists():
        return jsonify({'error': f'尾帧图片不存在: {last_frame_path}'}), 400
    
    print(f"首尾帧视频生成请求:")
    print(f"  首帧: {full_first_path}")
    print(f"  尾帧: {full_last_path}")
    print(f"  提示词: {prompt}")
    print(f"  分辨率: {resolution}")
    
    # 异步执行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            keyframe_video_api.generate_keyframe_video(
                first_frame_path=str(full_first_path),
                last_frame_path=str(full_last_path),
                prompt=prompt,
                resolution=resolution,
                prompt_extend=prompt_extend
            )
        )
        
        # 如果生成成功，复制到assets
        if result.get('status') == 'success' and result.get('local_path'):
            asset_path = copy_to_assets(result['local_path'], 'video')
            if asset_path:
                result['local_path'] = str(Path(asset_path).relative_to(Path.cwd()))
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        try:
            loop.close()
        except:
            pass  # 忽略Windows上的关闭循环错误

@app.route('/api/image-edit', methods=['POST'])
def image_edit():
    """图片编辑"""
    data = request.json
    
    image_path = data.get('image_path', '')
    edit_instruction = data.get('edit_instruction', '')
    negative_prompt = data.get('negative_prompt', '')
    watermark = data.get('watermark', False)
    
    if not image_path:
        return jsonify({'error': '请选择要编辑的图片'}), 400
    
    if not edit_instruction:
        return jsonify({'error': '请输入编辑指令'}), 400
    
    # 转换为绝对路径
    if image_path.startswith('/'):
        image_path = image_path[1:]
    
    full_image_path = Path(image_path).resolve()
    if not full_image_path.exists():
        return jsonify({'error': f'图片文件不存在: {image_path}'}), 400
    
    print(f"图片编辑请求:")
    print(f"  图片: {full_image_path}")
    print(f"  编辑指令: {edit_instruction}")
    print(f"  负向提示: {negative_prompt}")
    print(f"  水印: {watermark}")
    
    # 异步执行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            image_edit_api.edit_image(
                image_path=str(full_image_path),
                edit_instruction=edit_instruction,
                negative_prompt=negative_prompt if negative_prompt else None,
                watermark=watermark
            )
        )
        
        # 如果编辑成功，复制到assets
        if result.get('status') == 'success' and result.get('local_path'):
            asset_path = copy_to_assets(result['local_path'], 'image')
            if asset_path:
                # 确保返回相对路径
                try:
                    result['local_path'] = str(Path(asset_path).relative_to(Path.cwd()))
                except ValueError:
                    # 如果路径转换失败，直接使用相对路径
                    result['local_path'] = str(Path(asset_path)).replace(str(Path.cwd()) + '/', '')
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        try:
            loop.close()
        except:
            pass  # 忽略Windows上的关闭循环错误

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """提供素材文件"""
    return send_from_directory(ASSETS_FOLDER, filename)

@app.route('/output/<path:filename>')
def serve_output(filename):
    """提供输出文件"""
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """提供上传文件"""
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    print("🚀 启动视频生成工具Web服务...")
    print("📁 上传目录:", UPLOAD_FOLDER.absolute())
    print("📁 输出目录:", OUTPUT_FOLDER.absolute())
    print("📁 素材目录:", ASSETS_FOLDER.absolute())
    print("🌐 访问地址: http://localhost:30001")
    
    app.run(debug=True, host='0.0.0.0', port=30001)