#!/usr/bin/env python3
"""
项目管理服务
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class ProjectManager:
    """项目管理器"""
    
    def __init__(self, base_path: str = "./projects"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """创建新项目"""
        project_id = str(uuid.uuid4())
        project_path = self.base_path / project_id
        
        # 创建项目目录结构
        project_path.mkdir(exist_ok=True)
        (project_path / "assets").mkdir(exist_ok=True)
        (project_path / "assets" / "images").mkdir(exist_ok=True)
        (project_path / "assets" / "videos").mkdir(exist_ok=True)
        (project_path / "assets" / "audios").mkdir(exist_ok=True)
        
        # 创建prompts目录
        (project_path / "prompts").mkdir(exist_ok=True)
        (project_path / "prompts" / "story").mkdir(exist_ok=True)
        (project_path / "prompts" / "storyboard").mkdir(exist_ok=True)
        (project_path / "prompts" / "characters").mkdir(exist_ok=True)
        (project_path / "prompts" / "scenes").mkdir(exist_ok=True)
        (project_path / "prompts" / "shots").mkdir(exist_ok=True)
        (project_path / "prompts" / "videos").mkdir(exist_ok=True)
        
        # 创建outputs目录
        (project_path / "outputs").mkdir(exist_ok=True)
        (project_path / "outputs" / "references").mkdir(exist_ok=True)
        (project_path / "outputs" / "storyboards").mkdir(exist_ok=True)
        (project_path / "outputs" / "videos").mkdir(exist_ok=True)
        
        # 创建项目元数据
        metadata = {
            "id": project_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "stage": "initial",  # initial, story_analysis, storyboard, production, post_production
            "settings": {
                "llm_provider": "claude",  # claude, openai, free
                "target_duration": 60,  # 目标视频时长（秒）
                "style": "realistic",  # realistic, cartoon, anime, etc.
                "quality": "high"  # low, medium, high
            },
            "history": []
        }
        
        # 保存元数据
        with open(project_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return metadata
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        project_path = self.base_path / project_id
        metadata_path = project_path / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # 添加项目统计信息
        metadata["stats"] = self._get_project_stats(project_path)
        
        return metadata
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目"""
        projects = []
        
        for project_dir in self.base_path.iterdir():
            if project_dir.is_dir():
                metadata = self.get_project(project_dir.name)
                if metadata:
                    projects.append(metadata)
        
        # 按更新时间排序
        projects.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return projects
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新项目信息"""
        project_path = self.base_path / project_id
        metadata_path = project_path / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        # 更新字段
        for key, value in updates.items():
            if key not in ["id", "created_at"]:  # 不允许更新这些字段
                metadata[key] = value
        
        metadata["updated_at"] = datetime.now().isoformat()
        
        # 保存更新
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return metadata
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        project_path = self.base_path / project_id
        
        if project_path.exists():
            shutil.rmtree(project_path)
            return True
        
        return False
    
    def add_asset(self, project_id: str, file_path: str, asset_type: str) -> Optional[str]:
        """添加素材到项目"""
        project_path = self.base_path / project_id
        
        if not project_path.exists():
            return None
        
        source = Path(file_path)
        if not source.exists():
            return None
        
        # 确定目标路径
        if asset_type == "image":
            target_dir = project_path / "assets" / "images"
        elif asset_type == "video":
            target_dir = project_path / "assets" / "videos"
        elif asset_type == "audio":
            target_dir = project_path / "assets" / "audios"
        else:
            return None
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{source.name}"
        target_path = target_dir / filename
        
        # 复制文件
        shutil.copy2(source, target_path)
        
        # 记录到历史
        self._add_history(project_id, "asset_added", {
            "type": asset_type,
            "filename": filename,
            "path": str(target_path.relative_to(project_path))
        })
        
        return str(target_path)
    
    def save_prompt(self, project_id: str, prompt_type: str, filename: str, content: Dict[str, Any]) -> Optional[str]:
        """保存生成的prompt"""
        project_path = self.base_path / project_id
        
        if not project_path.exists():
            return None
        
        # 确定保存路径
        prompt_dir = project_path / "prompts" / prompt_type
        if not prompt_dir.exists():
            return None
        
        # 保存文件
        file_path = prompt_dir / f"{filename}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        # 记录到历史
        self._add_history(project_id, "prompt_generated", {
            "type": prompt_type,
            "filename": filename,
            "path": str(file_path.relative_to(project_path))
        })
        
        return str(file_path)
    
    def save_output(self, project_id: str, output_type: str, file_path: str) -> Optional[str]:
        """保存生成的输出"""
        project_path = self.base_path / project_id
        
        if not project_path.exists():
            return None
        
        source = Path(file_path)
        if not source.exists():
            return None
        
        # 确定目标路径
        output_dir = project_path / "outputs" / output_type
        if not output_dir.exists():
            return None
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{source.name}"
        target_path = output_dir / filename
        
        # 移动文件
        shutil.move(str(source), str(target_path))
        
        # 记录到历史
        self._add_history(project_id, "output_generated", {
            "type": output_type,
            "filename": filename,
            "path": str(target_path.relative_to(project_path))
        })
        
        return str(target_path)
    
    def get_project_prompts(self, project_id: str, prompt_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取项目的prompts"""
        project_path = self.base_path / project_id
        
        if not project_path.exists():
            return []
        
        prompts = []
        prompts_dir = project_path / "prompts"
        
        if prompt_type:
            # 获取特定类型的prompts
            type_dir = prompts_dir / prompt_type
            if type_dir.exists():
                for file_path in type_dir.glob("*.json"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                        prompts.append({
                            "type": prompt_type,
                            "filename": file_path.stem,
                            "content": content,
                            "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
        else:
            # 获取所有prompts
            for type_dir in prompts_dir.iterdir():
                if type_dir.is_dir():
                    for file_path in type_dir.glob("*.json"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = json.load(f)
                            prompts.append({
                                "type": type_dir.name,
                                "filename": file_path.stem,
                                "content": content,
                                "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
        
        return prompts
    
    def _get_project_stats(self, project_path: Path) -> Dict[str, int]:
        """获取项目统计信息"""
        stats = {
            "images": 0,
            "videos": 0,
            "audios": 0,
            "prompts": 0,
            "outputs": 0
        }
        
        # 统计素材
        stats["images"] = len(list((project_path / "assets" / "images").glob("*")))
        stats["videos"] = len(list((project_path / "assets" / "videos").glob("*")))
        stats["audios"] = len(list((project_path / "assets" / "audios").glob("*")))
        
        # 统计prompts
        for prompt_dir in (project_path / "prompts").iterdir():
            if prompt_dir.is_dir():
                stats["prompts"] += len(list(prompt_dir.glob("*.json")))
        
        # 统计输出
        for output_dir in (project_path / "outputs").iterdir():
            if output_dir.is_dir():
                stats["outputs"] += len(list(output_dir.glob("*")))
        
        return stats
    
    def _add_history(self, project_id: str, action: str, details: Dict[str, Any]) -> None:
        """添加历史记录"""
        metadata = self.get_project(project_id)
        if not metadata:
            return
        
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        
        metadata["history"].append(history_entry)
        
        # 限制历史记录数量
        if len(metadata["history"]) > 100:
            metadata["history"] = metadata["history"][-100:]
        
        self.update_project(project_id, {"history": metadata["history"]})