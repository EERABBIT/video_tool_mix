#!/usr/bin/env python3
"""
Agent基类定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import asyncio
from pathlib import Path


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, 
                 name: str, 
                 description: str,
                 llm_provider: Any,
                 project_manager: Any = None):
        """
        初始化Agent
        
        Args:
            name: Agent名称
            description: Agent描述
            llm_provider: LLM提供商实例
            project_manager: 项目管理器实例
        """
        self.name = name
        self.description = description
        self.llm = llm_provider
        self.project_manager = project_manager
        self.output_format = None
        self.system_prompt = None
    
    @abstractmethod
    def get_output_format(self) -> str:
        """获取输出格式定义"""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        pass
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入数据并返回结果"""
        pass
    
    async def execute(self, 
                     project_id: str,
                     input_data: Dict[str, Any],
                     save_result: bool = True) -> Dict[str, Any]:
        """
        执行Agent任务
        
        Args:
            project_id: 项目ID
            input_data: 输入数据
            save_result: 是否保存结果
        
        Returns:
            Agent处理结果
        """
        try:
            # 记录开始时间
            start_time = datetime.now()
            
            # 处理数据
            result = await self.process(input_data)
            
            # 添加元数据
            result["_metadata"] = {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "project_id": project_id
            }
            
            # 保存结果
            if save_result and self.project_manager:
                await self.save_result(project_id, result)
            
            return result
            
        except Exception as e:
            print(f"Agent {self.name} execution error: {str(e)}")
            raise
    
    async def save_result(self, project_id: str, result: Dict[str, Any]) -> None:
        """保存Agent处理结果"""
        if not self.project_manager:
            return
        
        # 确定保存类型
        save_type = self.get_save_type()
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.name}_{timestamp}"
        
        # 保存到项目
        self.project_manager.save_prompt(
            project_id=project_id,
            prompt_type=save_type,
            filename=filename,
            content=result
        )
    
    def get_save_type(self) -> str:
        """获取保存类型（子类可覆盖）"""
        # 默认根据Agent名称推断
        type_mapping = {
            "story": "story",
            "storyboard": "storyboard",
            "character": "characters",
            "scene": "scenes",
            "shot": "shots",
            "video": "videos"
        }
        
        for key, value in type_mapping.items():
            if key in self.name.lower():
                return value
        
        return "general"
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """验证输入数据"""
        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")
        return True
    
    def format_prompt(self, input_data: Dict[str, Any]) -> str:
        """格式化prompt"""
        return self.llm.format_agent_prompt(
            agent_name=self.name,
            agent_description=self.description,
            input_data=input_data,
            output_format=self.get_output_format()
        )
    
    async def generate_response(self, 
                               input_data: Dict[str, Any],
                               temperature: float = 0.7,
                               max_tokens: int = 3000) -> Dict[str, Any]:
        """生成LLM响应"""
        prompt = self.format_prompt(input_data)
        system_prompt = self.get_system_prompt()
        
        return await self.llm.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def sync_generate_response(self, 
                              input_data: Dict[str, Any],
                              temperature: float = 0.7,
                              max_tokens: int = 3000) -> Dict[str, Any]:
        """同步生成LLM响应"""
        prompt = self.format_prompt(input_data)
        system_prompt = self.get_system_prompt()
        
        if hasattr(self.llm, 'generate_json_sync'):
            return self.llm.generate_json_sync(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            # 如果没有同步方法，运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.llm.generate_json(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            )
            loop.close()
            return result