#!/usr/bin/env python3
"""
角色设计Agent
负责为故事中的角色创建详细的视觉设计方案
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class CharacterDesignAgent(BaseAgent):
    """角色设计Agent"""
    
    def __init__(self, llm_provider: Any, project_manager: Any = None):
        super().__init__(
            name="角色设计Agent",
            description="专业的角色设计师，负责为故事中的角色创建详细的视觉设计方案",
            llm_provider=llm_provider,
            project_manager=project_manager
        )
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是专业的角色设计师，负责为故事中的角色创建详细的视觉设计方案。
你需要根据故事分析中的角色信息，为每个主要角色生成详细的设计描述。
设计应该包括外观特征、服装风格、独特标识等视觉元素。
最重要的是生成可以直接用于文生图模型的reference_image_prompt。
输出必须是严格的JSON格式。"""
    
    def get_output_format(self) -> str:
        """获取输出格式定义"""
        return """```json
{
  "characters": [
    {
      "character_id": "CHAR_001",
      "character_name": "角色名称",
      "role_in_story": "在故事中的作用",
      "character_design": {
        "basic_description": "基础外观描述",
        "facial_features": {
          "face_shape": "脸型",
          "eyes": "眼部特征",
          "nose": "鼻部特征",
          "mouth": "嘴部特征",
          "skin_tone": "肤色"
        },
        "hair": {
          "color": "发色",
          "style": "发型",
          "length": "长度",
          "texture": "质感"
        },
        "body_type": {
          "height": "身高描述",
          "build": "体型",
          "posture": "姿态特点"
        },
        "clothing": {
          "style": "服装风格",
          "colors": "主要颜色",
          "details": "细节描述",
          "accessories": "配饰"
        },
        "distinctive_features": "独特识别特征"
      },
      "reference_image_prompt": "用于生成角色参考图的完整prompt（英文）",
      "consistency_keywords": ["保持一致性的关键词1", "关键词2", "关键词3"]
    }
  ],
  "total_characters": "角色总数"
}
```"""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据并返回结果"""
        # 验证输入
        self.validate_input(input_data, ["story_analysis"])
        
        # 提取角色信息
        story_analysis = input_data["story_analysis"]
        characters = story_analysis.get("visual_requirements", {}).get("main_characters", [])
        
        if not characters:
            characters = ["主角"]  # 默认至少有一个主角
        
        process_input = {
            "characters_list": characters,
            "story_genre": story_analysis.get("story_analysis", {}).get("genre", "剧情"),
            "story_mood": story_analysis.get("story_analysis", {}).get("mood", "中性"),
            "style_direction": story_analysis.get("style_direction", {}),
            "narrative_context": story_analysis.get("narrative_structure", {})
        }
        
        # 生成响应
        result = await self.generate_response(
            input_data=process_input,
            temperature=0.8,  # 角色设计需要更多创造性
            max_tokens=4000
        )
        
        # 后处理
        result = self.post_process(result)
        
        return result
    
    def post_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理结果"""
        # 确保characters是数组
        if "characters" not in result:
            result["characters"] = []
        elif not isinstance(result["characters"], list):
            result["characters"] = [result["characters"]]
        
        # 为每个角色生成默认值和ID
        for i, character in enumerate(result["characters"]):
            # 确保character_id
            if "character_id" not in character:
                character["character_id"] = f"CHAR_{str(i+1).zfill(3)}"
            
            # 确保character_design存在
            if "character_design" not in character:
                character["character_design"] = {}
            
            # 确保reference_image_prompt存在
            if "reference_image_prompt" not in character:
                # 生成默认的prompt
                name = character.get("character_name", f"Character {i+1}")
                desc = character.get("character_design", {}).get("basic_description", "a person")
                character["reference_image_prompt"] = f"Portrait of {desc}, professional photography, high quality, detailed"
            
            # 确保consistency_keywords是数组
            if "consistency_keywords" not in character:
                character["consistency_keywords"] = []
            elif not isinstance(character["consistency_keywords"], list):
                character["consistency_keywords"] = [character["consistency_keywords"]]
        
        # 添加角色总数
        result["total_characters"] = len(result["characters"])
        
        return result
    
    def get_save_type(self) -> str:
        """获取保存类型"""
        return "characters"