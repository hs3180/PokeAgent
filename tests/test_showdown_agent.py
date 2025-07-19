#!/usr/bin/env python3
"""
Showdown Agent 测试脚本

这个脚本用于测试Showdown Agent的基本功能，不进行实际的网络连接。
"""

import unittest
import asyncio
import tempfile
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.showdown_agent import ShowdownAgent
from agents.showdown_rl_agent import ShowdownRLAgent
from agents.showdown_llm_agent import ShowdownLLMAgent
from env.showdown_manager import ShowdownManager

class TestShowdownAgent(unittest.TestCase):
    """测试Showdown Agent的基本功能"""
    
    def setUp(self):
        """测试前的设置"""
        self.username = "TestAgent"
        self.server_url = "sim.smogon.com"
        self.server_port = 8000
        self.battle_format = "gen8randombattle"
    
    def test_showdown_agent_creation(self):
        """测试Showdown Agent的创建"""
        agent = ShowdownAgent(
            username=self.username,
            server_url=self.server_url,
            server_port=self.server_port,
            battle_format=self.battle_format
        )
        
        self.assertEqual(agent.username, self.username)
        self.assertEqual(agent.server_url, self.server_url)
        self.assertEqual(agent.server_port, self.server_port)
        self.assertEqual(agent.battle_format, self.battle_format)
        self.assertFalse(agent.is_connected)
    
    def test_showdown_rl_agent_creation(self):
        """测试Showdown RL Agent的创建"""
        agent = ShowdownRLAgent(
            username=self.username,
            server_url=self.server_url,
            server_port=self.server_port,
            battle_format=self.battle_format
        )
        
        self.assertEqual(agent.username, self.username)
        self.assertIsNotNone(agent.rl_agent)
        self.assertFalse(agent.is_connected)
    
    def test_showdown_llm_agent_creation(self):
        """测试Showdown LLM Agent的创建"""
        agent = ShowdownLLMAgent(
            username=self.username,
            model_name="microsoft/DialoGPT-medium",
            server_url=self.server_url,
            server_port=self.server_port,
            battle_format=self.battle_format
        )
        
        self.assertEqual(agent.username, self.username)
        self.assertIsNotNone(agent.llm_agent)
        self.assertFalse(agent.is_connected)
    
    def test_showdown_manager_creation(self):
        """测试Showdown管理器的创建"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "showdown": {
                    "server": {
                        "url": self.server_url,
                        "port": self.server_port,
                        "secure": False
                    },
                    "credentials": {
                        "username": self.username,
                        "password": None
                    },
                    "battle_format": self.battle_format,
                    "log_level": "INFO"
                }
            }
            import json
            json.dump(config, f)
            config_path = f.name
        
        try:
            manager = ShowdownManager(config_path)
            self.assertIsNotNone(manager.config)
            self.assertEqual(manager.config["showdown"]["credentials"]["username"], self.username)
        finally:
            os.unlink(config_path)
    
    def test_showdown_manager_agent_creation(self):
        """测试Showdown管理器的Agent创建功能"""
        manager = ShowdownManager()
        
        # 测试创建RL Agent
        rl_agent = manager.create_rl_agent(username="TestRL")
        self.assertIsInstance(rl_agent, ShowdownRLAgent)
        self.assertEqual(rl_agent.username, "TestRL")
        
        # 测试创建LLM Agent
        llm_agent = manager.create_llm_agent(username="TestLLM")
        self.assertIsInstance(llm_agent, ShowdownLLMAgent)
        self.assertEqual(llm_agent.username, "TestLLM")
    
    def test_agent_stats(self):
        """测试Agent统计信息"""
        agent = ShowdownRLAgent(username=self.username)
        stats = agent.get_training_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('agent_type', stats)
        self.assertEqual(stats['agent_type'], 'RL')
    
    def test_llm_agent_stats(self):
        """测试LLM Agent统计信息"""
        agent = ShowdownLLMAgent(username=self.username)
        stats = agent.get_llm_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('agent_type', stats)
        self.assertEqual(stats['agent_type'], 'LLM')
        self.assertIn('model_name', stats)

class TestShowdownAgentAsync(unittest.IsolatedAsyncioTestCase):
    """测试Showdown Agent的异步功能"""
    
    async def test_async_context_manager(self):
        """测试异步上下文管理器"""
        agent = ShowdownRLAgent(username="TestAgent")
        
        # 测试异步上下文管理器（不实际连接）
        async with agent:
            self.assertTrue(hasattr(agent, 'is_connected'))
    
    async def test_showdown_manager_async_context(self):
        """测试Showdown管理器的异步上下文管理器"""
        manager = ShowdownManager()
        
        async with manager:
            # 创建Agent
            agent = manager.create_rl_agent(username="TestAgent")
            self.assertIsNotNone(agent)
            
            # 测试获取统计信息
            stats = manager.get_agent_stats("TestAgent")
            self.assertIsInstance(stats, dict)

def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestShowdownAgent))
    test_suite.addTest(unittest.makeSuite(TestShowdownAgentAsync))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)