#!/usr/bin/env python3
"""
Agent测试文件
"""

import unittest
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.rl_agent import RLAgent
from agents.llm_agent import LLMAgent
from poke_env.player import RandomPlayer

class TestBaseAgent(unittest.TestCase):
    """测试基础Agent类"""
    
    def setUp(self):
        self.agent = BaseAgent()
    
    def test_agent_creation(self):
        """测试Agent创建"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.battle_format, "gen8randombattle")
    
    def test_get_battle_state(self):
        """测试获取战斗状态"""
        # 这里需要模拟一个battle对象
        # 由于poke-env的复杂性，这里只是基本测试
        self.assertIsNotNone(self.agent.get_battle_state)

class TestRLAgent(unittest.TestCase):
    """测试RL Agent类"""
    
    def setUp(self):
        self.agent = RLAgent()
    
    def test_rl_agent_creation(self):
        """测试RL Agent创建"""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.q_network)
        self.assertIsNotNone(self.agent.target_network)
    
    def test_state_representation(self):
        """测试状态表示"""
        # 这里需要模拟一个battle对象
        # 由于poke-env的复杂性，这里只是基本测试
        self.assertIsNotNone(self.agent.get_state_representation)
    
    def test_model_save_load(self):
        """测试模型保存和加载"""
        # 创建临时文件路径
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pth', delete=False) as tmp:
            model_path = tmp.name
        
        try:
            # 保存模型
            self.agent.save_model(model_path)
            self.assertTrue(os.path.exists(model_path))
            
            # 加载模型
            new_agent = RLAgent()
            new_agent.load_model(model_path)
            
            # 验证模型参数是否相同
            for param1, param2 in zip(self.agent.q_network.parameters(), 
                                     new_agent.q_network.parameters()):
                self.assertTrue((param1 == param2).all())
                
        finally:
            # 清理临时文件
            if os.path.exists(model_path):
                os.unlink(model_path)

class TestLLMAgent(unittest.TestCase):
    """测试LLM Agent类"""
    
    def setUp(self):
        self.agent = LLMAgent()
    
    def test_llm_agent_creation(self):
        """测试LLM Agent创建"""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.model_name)
    
    def test_model_info(self):
        """测试模型信息获取"""
        info = self.agent.get_model_info()
        self.assertIsInstance(info, dict)
        self.assertIn('model_name', info)
        self.assertIn('temperature', info)
        self.assertIn('model_loaded', info)
    
    def test_temperature_setting(self):
        """测试温度设置"""
        original_temp = self.agent.temperature
        self.agent.set_temperature(0.5)
        self.assertEqual(self.agent.temperature, 0.5)
        
        # 测试边界值
        self.agent.set_temperature(3.0)  # 应该被限制到2.0
        self.assertEqual(self.agent.temperature, 2.0)
        
        self.agent.set_temperature(0.0)  # 应该被限制到0.1
        self.assertEqual(self.agent.temperature, 0.1)

class TestAgentIntegration(unittest.TestCase):
    """测试Agent集成"""
    
    def test_agent_compatibility(self):
        """测试Agent兼容性"""
        agents = [
            BaseAgent(),
            RLAgent(),
            LLMAgent(),
            RandomPlayer()
        ]
        
        for agent in agents:
            self.assertIsNotNone(agent)
            self.assertTrue(hasattr(agent, 'choose_move'))

if __name__ == '__main__':
    unittest.main()