#!/usr/bin/env python3
"""
分镜脚本Agent
负责将故事转化为具体的镜头序列
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class StoryboardAgent(BaseAgent):
    """分镜脚本Agent"""
    
    def __init__(self, llm_provider: Any, project_manager: Any = None):
        super().__init__(
            name="分镜脚本Agent",
            description="专业的分镜师，擅长将故事转化为具体的镜头序列",
            llm_provider=llm_provider,
            project_manager=project_manager
        )
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是专业的分镜师，擅长将故事转化为具体的镜头序列。
你需要根据故事分析结果，创建详细的分镜头剧本。
每个镜头都应该有明确的视觉内容、拍摄方式和叙事功能。
请确保镜头之间的连贯性和整体节奏的把控。
输出必须是严格的JSON格式。"""
    
    def get_output_format(self) -> str:
        """获取输出格式定义"""
        return """```json
{
  "storyboard": [
    {
      "shot_id": "SHOT_001",
      "sequence_name": "序列名称",
      "shot_description": {
        "shot_type": "远景/中景/近景/特写",
        "camera_angle": "平视/俯视/仰视",
        "camera_movement": "静止/推拉/摇移/跟随",
        "duration": "预估时长（秒）"
      },
      "visual_content": {
        "main_subject": "画面主体描述",
        "subject_action": "主体动作/状态",
        "environment": "环境背景描述",
        "lighting": "光照情况",
        "mood": "情绪氛围"
      },
      "narrative_purpose": "这个镜头的叙事作用",
      "emotional_beat": "情感节拍",
      "transition_to_next": "与下一镜头的过渡方式"
    }
  ],
  "overall_pacing": "整体节奏描述",
  "key_moments": ["关键情感节点1", "关键情感节点2"],
  "total_shots": "总镜头数",
  "estimated_duration": "预估总时长（秒）"
}
```"""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据并返回结果"""
        # 验证输入
        self.validate_input(input_data, ["story_analysis"])
        
        # 构建输入数据
        story_analysis = input_data["story_analysis"]
        
        process_input = {
            "story_analysis": story_analysis,
            "target_duration": story_analysis.get("story_analysis", {}).get("target_duration", 60),
            "narrative_structure": story_analysis.get("narrative_structure", {}),
            "visual_requirements": story_analysis.get("visual_requirements", {}),
            "style_direction": story_analysis.get("style_direction", {})
        }
        
        # 生成响应
        result = await self.generate_response(
            input_data=process_input,
            temperature=0.7,
            max_tokens=4000  # 分镜脚本可能需要更多tokens
        )
        
        # 后处理
        result = self.post_process(result)
        
        return result
    
    def post_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理结果"""
        # 确保storyboard是数组
        if "storyboard" not in result:
            result["storyboard"] = []
        elif not isinstance(result["storyboard"], list):
            result["storyboard"] = [result["storyboard"]]
        
        # 为每个镜头生成默认值
        for i, shot in enumerate(result["storyboard"]):
            # 确保shot_id
            if "shot_id" not in shot:
                shot["shot_id"] = f"SHOT_{str(i+1).zfill(3)}"
            
            # 确保shot_description
            if "shot_description" not in shot:
                shot["shot_description"] = {}
            
            # 设置默认值
            shot_defaults = {
                "shot_type": "中景",
                "camera_angle": "平视",
                "camera_movement": "静止",
                "duration": 3
            }
            
            for key, value in shot_defaults.items():
                if key not in shot["shot_description"]:
                    shot["shot_description"][key] = value
            
            # 确保visual_content
            if "visual_content" not in shot:
                shot["visual_content"] = {
                    "main_subject": "待定",
                    "environment": "待定",
                    "mood": "中性"
                }
        
        # 计算总镜头数和预估时长
        result["total_shots"] = len(result["storyboard"])
        
        total_duration = sum(
            int(shot.get("shot_description", {}).get("duration", 3))
            for shot in result["storyboard"]
        )
        result["estimated_duration"] = total_duration
        
        # 确保key_moments是数组
        if "key_moments" not in result:
            result["key_moments"] = []
        elif not isinstance(result["key_moments"], list):
            result["key_moments"] = [result["key_moments"]]
        
        return result
    
    def get_save_type(self) -> str:
        """获取保存类型"""
        return "storyboard"