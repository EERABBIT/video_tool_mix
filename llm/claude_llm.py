#!/usr/bin/env python3
"""
Claude API接口实现
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from .base_llm import BaseLLM

try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeLLM(BaseLLM):
    """Claude API接口"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic library is not installed. Install it with: pip install anthropic")
            
        # 使用提供的API key或从环境变量读取
        api_key = api_key or os.getenv("CLAUDE_API_KEY")
        model = model or "claude-3-sonnet-20240229"
        
        super().__init__(api_key, model)
        
        if not self.api_key:
            raise ValueError("Claude API key not provided. Set CLAUDE_API_KEY environment variable or pass api_key parameter.")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.sync_client = anthropic.Anthropic(api_key=self.api_key)
    
    async def generate(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      response_format: Optional[str] = None) -> str:
        """生成文本响应"""
        
        temperature = temperature or self.default_temperature
        max_tokens = max_tokens or self.default_max_tokens
        
        messages = [{"role": "user", "content": prompt}]
        
        if response_format == "json":
            if system_prompt:
                system_prompt += "\n\n请以有效的JSON格式响应。"
            else:
                system_prompt = "请以有效的JSON格式响应。"
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Claude API error: {str(e)}")
            raise
    
    async def generate_json(self,
                          prompt: str,
                          system_prompt: Optional[str] = None,
                          schema: Optional[Dict[str, Any]] = None,
                          temperature: Optional[float] = None,
                          max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """生成JSON格式响应"""
        
        # 添加JSON格式要求到prompt
        if schema:
            schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
            prompt += f"\n\n请严格按照以下JSON schema格式输出：\n```json\n{schema_str}\n```"
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="json"
        )
        
        return self.parse_json_response(response)
    
    def generate_sync(self, 
                     prompt: str, 
                     system_prompt: Optional[str] = None,
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     response_format: Optional[str] = None) -> str:
        """同步生成文本响应"""
        
        temperature = temperature or self.default_temperature
        max_tokens = max_tokens or self.default_max_tokens
        
        messages = [{"role": "user", "content": prompt}]
        
        if response_format == "json":
            if system_prompt:
                system_prompt += "\n\n请以有效的JSON格式响应。"
            else:
                system_prompt = "请以有效的JSON格式响应。"
        
        try:
            response = self.sync_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Claude API error: {str(e)}")
            raise
    
    def generate_json_sync(self,
                         prompt: str,
                         system_prompt: Optional[str] = None,
                         schema: Optional[Dict[str, Any]] = None,
                         temperature: Optional[float] = None,
                         max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """同步生成JSON格式响应"""
        
        # 添加JSON格式要求到prompt
        if schema:
            schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
            prompt += f"\n\n请严格按照以下JSON schema格式输出：\n```json\n{schema_str}\n```"
        
        response = self.generate_sync(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="json"
        )
        
        return self.parse_json_response(response)
    
    async def generate_agent_response(self, 
                                     agent_name: str,
                                     agent_description: str,
                                     input_data: Dict[str, Any],
                                     output_format: str,
                                     temperature: float = 0.7) -> Dict[str, Any]:
        """为Agent生成响应"""
        
        prompt = self.format_agent_prompt(
            agent_name=agent_name,
            agent_description=agent_description,
            input_data=input_data,
            output_format=output_format
        )
        
        return await self.generate_json(
            prompt=prompt,
            temperature=temperature,
            max_tokens=3000  # Agent响应通常需要更多tokens
        )