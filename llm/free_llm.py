#!/usr/bin/env python3
"""
免费LLM接口实现（使用Dashscope通义千问）
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
import aiohttp
import requests
from .base_llm import BaseLLM


class DashscopeLLM(BaseLLM):
    """Dashscope通义千问API接口"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # 使用提供的API key或从环境变量读取
        api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        model = model or "qwen-turbo"  # qwen-turbo, qwen-plus, qwen-max
        
        super().__init__(api_key, model)
        
        if not self.api_key:
            raise ValueError("Dashscope API key not provided. Set DASHSCOPE_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    async def generate(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      response_format: Optional[str] = None) -> str:
        """生成文本响应"""
        
        temperature = temperature or self.default_temperature
        max_tokens = max_tokens or self.default_max_tokens
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        if response_format == "json":
            if messages[0]["role"] == "system":
                messages[0]["content"] += "\n\n请以有效的JSON格式响应。"
            else:
                messages.insert(0, {"role": "system", "content": "请以有效的JSON格式响应。"})
        
        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload, headers=headers) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return result["output"]["choices"][0]["message"]["content"]
                    else:
                        raise Exception(f"Dashscope API error: {result}")
                        
        except Exception as e:
            print(f"Dashscope API error: {str(e)}")
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
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        if response_format == "json":
            if messages[0]["role"] == "system":
                messages[0]["content"] += "\n\n请以有效的JSON格式响应。"
            else:
                messages.insert(0, {"role": "system", "content": "请以有效的JSON格式响应。"})
        
        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            result = response.json()
            
            if response.status_code == 200:
                return result["output"]["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Dashscope API error: {result}")
                
        except Exception as e:
            print(f"Dashscope API error: {str(e)}")
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


class FreeLLM(BaseLLM):
    """免费LLM接口包装器，支持多个提供商"""
    
    def __init__(self, provider: str = "dashscope", api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化免费LLM
        
        Args:
            provider: LLM提供商 (dashscope, cohere, etc.)
            api_key: API密钥
            model: 模型名称
        """
        super().__init__(api_key, model)
        
        self.provider = provider
        self.llm_instance = None
        
        # 根据提供商创建实例
        if provider == "dashscope":
            self.llm_instance = DashscopeLLM(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def generate(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      response_format: Optional[str] = None) -> str:
        """生成文本响应"""
        return await self.llm_instance.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )
    
    async def generate_json(self,
                          prompt: str,
                          system_prompt: Optional[str] = None,
                          schema: Optional[Dict[str, Any]] = None,
                          temperature: Optional[float] = None,
                          max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """生成JSON格式响应"""
        return await self.llm_instance.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            schema=schema,
            temperature=temperature,
            max_tokens=max_tokens
        )