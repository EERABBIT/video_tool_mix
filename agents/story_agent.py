#!/usr/bin/env python3
"""
故事分析Agent
负责分析用户的故事创意，提炼可视化的核心要素
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class StoryAnalysisAgent(BaseAgent):
    """故事分析Agent"""
    
    def __init__(self, llm_provider: Any, project_manager: Any = None):
        super().__init__(
            name="故事分析Agent",
            description="资深的影视策划师，擅长从故事创意中提炼可视化的核心要素",
            llm_provider=llm_provider,
            project_manager=project_manager
        )
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一位资深的影视策划师，擅长从故事创意中提炼可视化的核心要素。
你需要深度分析用户提供的故事，为后续视觉制作提供全面的指导。
请确保你的分析涵盖故事的各个方面，包括主题、类型、情感基调、叙事结构、视觉需求和风格方向。
输出必须是严格的JSON格式。"""
    
    def get_output_format(self) -> str:
        """获取输出格式定义"""
        return """```json
{
  "story_analysis": {
    "core_theme": "故事核心主题",
    "genre": "影片类型（悬疑/爱情/科幻/动作等）",
    "mood": "整体情感基调",
    "target_duration": "建议视频时长（秒）",
    "complexity_level": "制作复杂度（简单/中等/复杂）"
  },
  "narrative_structure": {
    "opening": "开场设置描述",
    "development": "情节发展描述",
    "climax": "高潮部分描述",
    "resolution": "结尾解决描述"
  },
  "visual_requirements": {
    "main_characters": ["主要角色1", "主要角色2"],
    "key_locations": ["主要场景1", "主要场景2"],
    "required_props": ["重要道具1", "重要道具2"],
    "visual_effects_needed": ["所需视觉效果"]
  },
  "style_direction": {
    "overall_aesthetic": "整体美学风格",
    "color_palette": "建议色彩方案",
    "lighting_style": "光照风格偏好",
    "camera_style": "拍摄风格偏好"
  }
}
```"""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据并返回结果"""
        # 验证输入
        self.validate_input(input_data, ["story"])
        
        # 构建输入数据
        process_input = {
            "story": input_data["story"],
            "additional_requirements": input_data.get("requirements", ""),
            "target_audience": input_data.get("target_audience", "general"),
            "duration_preference": input_data.get("duration", 60)
        }
        
        # 生成响应
        result = await self.generate_response(
            input_data=process_input,
            temperature=0.7,
            max_tokens=3000
        )
        
        # 后处理
        result = self.post_process(result)
        
        return result
    
    def post_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理结果"""
        # 确保必要字段存在
        if "story_analysis" not in result:
            result["story_analysis"] = {}
        
        # 设置默认值
        defaults = {
            "target_duration": 60,
            "complexity_level": "中等",
            "genre": "剧情",
            "mood": "中性"
        }
        
        for key, value in defaults.items():
            if key not in result["story_analysis"]:
                result["story_analysis"][key] = value
        
        # 确保数组字段
        if "visual_requirements" not in result:
            result["visual_requirements"] = {}
        
        array_fields = ["main_characters", "key_locations", "required_props", "visual_effects_needed"]
        for field in array_fields:
            if field not in result["visual_requirements"]:
                result["visual_requirements"][field] = []
            elif not isinstance(result["visual_requirements"][field], list):
                result["visual_requirements"][field] = [result["visual_requirements"][field]]
        
        return result
    
    def get_save_type(self) -> str:
        """获取保存类型"""
        return "story"