import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from agents.showdown_rl_agent import ShowdownRLAgent
from agents.showdown_llm_agent import ShowdownLLMAgent
from agents.rl_agent import RLAgent
from agents.llm_agent import LLMAgent

class ShowdownManager:
    """
    Pokemon Showdown 管理器
    
    提供高级接口来管理Showdown Agent，包括配置管理、Agent创建、对战监控等
    """
    
    def __init__(self, config_path: str = "config/showdown_config.json"):
        """
        初始化Showdown管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.agents: Dict[str, Any] = {}
        self.active_battles: List[str] = []
        
        # 设置日志
        self._setup_logging()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.info(f"成功加载配置文件: {self.config_path}")
            return config
        except FileNotFoundError:
            logging.warning(f"配置文件 {self.config_path} 不存在，使用默认配置")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logging.error(f"配置文件格式错误: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        """
        return {
            "showdown": {
                "server": {
                    "url": "sim.smogon.com",
                    "port": 8000,
                    "secure": False
                },
                "credentials": {
                    "username": "DefaultAgent",
                    "password": None
                },
                "battle_format": "gen8randombattle",
                "log_level": "INFO"
            },
            "rl_agent": {
                "model_path": "models/showdown_rl_model.pth",
                "save_interval": 10,
                "training": {
                    "num_battles": 100,
                    "epsilon_start": 1.0,
                    "epsilon_end": 0.01,
                    "epsilon_decay": 0.995,
                    "learning_rate": 0.001
                }
            },
            "llm_agent": {
                "model_name": "microsoft/DialoGPT-medium",
                "temperature": 0.7,
                "max_length": 100,
                "top_p": 0.9,
                "do_sample": True
            },
            "battle_settings": {
                "default_battles": 5,
                "challenge_cooldown": 5,
                "ladder_wait_time": 2,
                "max_concurrent_battles": 1
            }
        }
    
    def _setup_logging(self):
        """
        设置日志配置
        """
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # 创建日志目录
        log_file = log_config.get("file", "logs/showdown.log")
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def create_rl_agent(self, 
                       username: Optional[str] = None,
                       model_path: Optional[str] = None,
                       **kwargs) -> ShowdownRLAgent:
        """
        创建RL Agent
        
        Args:
            username: Showdown用户名
            model_path: 模型路径
            **kwargs: 其他参数
        
        Returns:
            ShowdownRLAgent实例
        """
        showdown_config = self.config["showdown"]
        rl_config = self.config["rl_agent"]
        
        # 使用配置中的参数，允许覆盖
        agent_username = username or showdown_config["credentials"]["username"]
        agent_model_path = model_path or rl_config["model_path"]
        
        agent = ShowdownRLAgent(
            username=agent_username,
            model_path=agent_model_path,
            password=showdown_config["credentials"]["password"],
            server_url=showdown_config["server"]["url"],
            server_port=showdown_config["server"]["port"],
            battle_format=showdown_config["battle_format"],
            log_level=getattr(logging, showdown_config["log_level"]),
            **kwargs
        )
        
        self.agents[agent_username] = agent
        logging.info(f"创建RL Agent: {agent_username}")
        return agent
    
    def create_llm_agent(self,
                        username: Optional[str] = None,
                        model_name: Optional[str] = None,
                        **kwargs) -> ShowdownLLMAgent:
        """
        创建LLM Agent
        
        Args:
            username: Showdown用户名
            model_name: 模型名称
            **kwargs: 其他参数
        
        Returns:
            ShowdownLLMAgent实例
        """
        showdown_config = self.config["showdown"]
        llm_config = self.config["llm_agent"]
        
        # 使用配置中的参数，允许覆盖
        agent_username = username or showdown_config["credentials"]["username"]
        agent_model_name = model_name or llm_config["model_name"]
        
        agent = ShowdownLLMAgent(
            username=agent_username,
            model_name=agent_model_name,
            password=showdown_config["credentials"]["password"],
            server_url=showdown_config["server"]["url"],
            server_port=showdown_config["server"]["port"],
            battle_format=showdown_config["battle_format"],
            log_level=getattr(logging, showdown_config["log_level"]),
            **kwargs
        )
        
        # 设置LLM参数
        agent.set_temperature(llm_config["temperature"])
        agent.set_max_length(llm_config["max_length"])
        
        self.agents[agent_username] = agent
        logging.info(f"创建LLM Agent: {agent_username}")
        return agent
    
    async def run_rl_training(self,
                            agent: Optional[ShowdownRLAgent] = None,
                            num_battles: Optional[int] = None,
                            save_interval: Optional[int] = None,
                            model_save_path: Optional[str] = None):
        """
        运行RL训练
        
        Args:
            agent: RL Agent实例
            num_battles: 训练对战数量
            save_interval: 保存间隔
            model_save_path: 模型保存路径
        """
        if agent is None:
            agent = self.create_rl_agent()
        
        rl_config = self.config["rl_agent"]
        battle_config = self.config["battle_settings"]
        
        # 使用配置中的参数，允许覆盖
        battles = num_battles or rl_config["training"]["num_battles"]
        interval = save_interval or rl_config["save_interval"]
        save_path = model_save_path or rl_config["model_path"]
        
        logging.info(f"开始RL训练: {battles}场对战")
        
        try:
            await agent.train_on_showdown(
                num_battles=battles,
                save_interval=interval,
                model_save_path=save_path
            )
        except Exception as e:
            logging.error(f"RL训练失败: {e}")
            raise
    
    async def run_llm_battles(self,
                            agent: Optional[ShowdownLLMAgent] = None,
                            num_battles: Optional[int] = None,
                            temperature: Optional[float] = None,
                            max_length: Optional[int] = None):
        """
        运行LLM对战
        
        Args:
            agent: LLM Agent实例
            num_battles: 对战数量
            temperature: 生成温度
            max_length: 最大生成长度
        """
        if agent is None:
            agent = self.create_llm_agent()
        
        llm_config = self.config["llm_agent"]
        battle_config = self.config["battle_settings"]
        
        # 使用配置中的参数，允许覆盖
        battles = num_battles or battle_config["default_battles"]
        temp = temperature or llm_config["temperature"]
        length = max_length or llm_config["max_length"]
        
        logging.info(f"开始LLM对战: {battles}场对战")
        
        try:
            await agent.run_showdown_battles(
                num_battles=battles,
                temperature=temp,
                max_length=length
            )
        except Exception as e:
            logging.error(f"LLM对战失败: {e}")
            raise
    
    async def challenge_user(self,
                           opponent: str,
                           agent: Optional[Any] = None,
                           num_battles: int = 1,
                           **kwargs):
        """
        挑战特定用户
        
        Args:
            opponent: 对手用户名
            agent: Agent实例
            num_battles: 对战数量
            **kwargs: 其他参数
        """
        if agent is None:
            agent = self.create_llm_agent()
        
        logging.info(f"挑战用户: {opponent}")
        
        try:
            if isinstance(agent, ShowdownLLMAgent):
                await agent.challenge_specific_user(
                    opponent=opponent,
                    num_battles=num_battles,
                    **kwargs
                )
            else:
                # 对于其他类型的Agent，使用通用方法
                await agent.connect()
                for i in range(num_battles):
                    await agent.challenge_user(opponent)
                    await asyncio.sleep(self.config["battle_settings"]["challenge_cooldown"])
        except Exception as e:
            logging.error(f"挑战用户失败: {e}")
            raise
    
    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """
        获取Agent统计信息
        
        Args:
            agent_name: Agent名称
        
        Returns:
            统计信息字典
        """
        if agent_name not in self.agents:
            return {}
        
        agent = self.agents[agent_name]
        
        if isinstance(agent, ShowdownRLAgent):
            return agent.get_training_stats()
        elif isinstance(agent, ShowdownLLMAgent):
            return agent.get_llm_stats()
        else:
            return agent.get_battle_stats()
    
    async def disconnect_all_agents(self):
        """
        断开所有Agent的连接
        """
        for agent_name, agent in self.agents.items():
            try:
                if hasattr(agent, 'disconnect'):
                    await agent.disconnect()
                logging.info(f"断开Agent连接: {agent_name}")
            except Exception as e:
                logging.error(f"断开Agent {agent_name} 连接时发生错误: {e}")
    
    def save_config(self, config_path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径
        """
        path = config_path or self.config_path
        
        # 确保目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        logging.info(f"配置已保存到: {path}")
    
    async def __aenter__(self):
        """
        异步上下文管理器入口
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口
        """
        await self.disconnect_all_agents()