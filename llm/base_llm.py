#!/usr/bin/env python3
"""
LLM基类定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json


class BaseLLM(ABC):
    """LLM基类"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.default_temperature = 0.7
        self.default_max_tokens = 2000
    
    @abstractmethod
    async def generate(self, 
                       prompt: str, 
                       system_prompt: Optional[str] = None,
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None,
                       response_format: Optional[str] = None) -> str:
        """生成文本响应"""
        pass
    
    @abstractmethod
    async def generate_json(self,
                           prompt: str,
                           system_prompt: Optional[str] = None,
                           schema: Optional[Dict[str, Any]] = None,
                           temperature: Optional[float] = None,
                           max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """生成JSON格式响应"""
        pass
    
    def format_agent_prompt(self, agent_name: str, agent_description: str, 
                           input_data: Dict[str, Any], output_format: str) -> str:
        """格式化Agent prompt"""
        prompt = f"""你是{agent_name}，{agent_description}

**输入数据**:
{json.dumps(input_data, indent=2, ensure_ascii=False)}

**任务要求**:
请根据输入数据完成你的任务。

**输出格式**:
{output_format}

请严格按照输出格式要求生成结果。
"""
        return prompt
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON块
        import re
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # 尝试提取大括号内容
        brace_pattern = r'\{.*\}'
        matches = re.findall(brace_pattern, response, re.DOTALL)
        
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # 如果都失败了，返回原始文本包装
        return {"raw_response": response}
    
    def estimate_tokens(self, text: str) -> int:
        """估算token数量"""
        # 简单估算：中文约1.5字符/token，英文约4字符/token
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len(text) - chinese_chars
        
        return int(chinese_chars / 1.5 + english_chars / 4)
    
    def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """截断文本到token限制"""
        estimated_tokens = self.estimate_tokens(text)
        
        if estimated_tokens <= max_tokens:
            return text
        
        # 按比例截断
        ratio = max_tokens / estimated_tokens
        target_length = int(len(text) * ratio * 0.9)  # 留10%余量
        
        return text[:target_length] + "..."