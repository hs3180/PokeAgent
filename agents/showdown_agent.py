import asyncio
import logging
from typing import Optional, Dict, Any
from poke_env.player import Player
from poke_env.ps_client import PSClient
from poke_env.battle import Battle
from .base_agent import BaseAgent

class ShowdownAgent(BaseAgent):
    """
    Pokemon Showdown Agent，可以连接到Showdown服务器进行在线对战
    """
    
    def __init__(self, 
                 username: str,
                 password: Optional[str] = None,
                 server_url: str = "sim.smogon.com",
                 server_port: int = 8000,
                 battle_format: str = "gen8randombattle",
                 log_level: int = logging.INFO,
                 **kwargs):
        """
        初始化Showdown Agent
        
        Args:
            username: Showdown用户名
            password: Showdown密码（可选）
            server_url: Showdown服务器地址
            server_port: 服务器端口
            battle_format: 对战格式
            log_level: 日志级别
        """
        super().__init__(battle_format=battle_format, log_level=log_level, **kwargs)
        self.username = username
        self.password = password
        self.server_url = server_url
        self.server_port = server_port
        self.client: Optional[PSClient] = None
        self.is_connected = False
        
    async def connect(self):
        """
        连接到Showdown服务器
        """
        try:
            self.client = PSClient(
                username=self.username,
                password=self.password,
                server_url=self.server_url,
                server_port=self.server_port,
                log_level=self.log_level
            )
            
            # 连接到服务器
            await self.client.connect()
            self.is_connected = True
            logging.info(f"成功连接到Showdown服务器: {self.server_url}:{self.server_port}")
            
        except Exception as e:
            logging.error(f"连接Showdown服务器失败: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """
        断开与Showdown服务器的连接
        """
        if self.client and self.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            logging.info("已断开与Showdown服务器的连接")
    
    async def challenge_user(self, opponent: str, battle_format: Optional[str] = None):
        """
        挑战指定用户
        
        Args:
            opponent: 对手用户名
            battle_format: 对战格式（可选，默认使用初始化时的格式）
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        format_to_use = battle_format or self.battle_format
        await self.client.challenge_user(opponent, format_to_use)
        logging.info(f"已向 {opponent} 发起 {format_to_use} 格式的挑战")
    
    async def accept_challenge(self, battle_format: Optional[str] = None):
        """
        接受挑战
        
        Args:
            battle_format: 对战格式（可选，默认使用初始化时的格式）
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        format_to_use = battle_format or self.battle_format
        await self.client.accept_challenge(format_to_use)
        logging.info(f"已接受 {format_to_use} 格式的挑战")
    
    async def join_ladder(self, battle_format: Optional[str] = None):
        """
        加入天梯对战
        
        Args:
            battle_format: 对战格式（可选，默认使用初始化时的格式）
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        format_to_use = battle_format or self.battle_format
        await self.client.join_ladder(format_to_use)
        logging.info(f"已加入 {format_to_use} 天梯对战")
    
    async def leave_ladder(self):
        """
        离开天梯对战
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        await self.client.leave_ladder()
        logging.info("已离开天梯对战")
    
    async def run_battles(self, num_battles: int = 1, battle_format: Optional[str] = None):
        """
        运行指定数量的对战
        
        Args:
            num_battles: 对战数量
            battle_format: 对战格式（可选，默认使用初始化时的格式）
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        format_to_use = battle_format or self.battle_format
        battles_completed = 0
        
        try:
            while battles_completed < num_battles:
                # 加入天梯等待对战
                await self.join_ladder(format_to_use)
                
                # 等待对战开始
                while not self.client.battles:
                    await asyncio.sleep(1)
                
                # 处理所有对战
                for battle in self.client.battles.values():
                    if not battle.finished:
                        await battle.wait_until_finished()
                        battles_completed += 1
                        logging.info(f"完成对战 {battles_completed}/{num_battles}")
                        
                        if battles_completed >= num_battles:
                            break
                
                # 短暂等待避免过于频繁的请求
                await asyncio.sleep(2)
                
        except Exception as e:
            logging.error(f"运行对战时发生错误: {e}")
            raise
        finally:
            # 离开天梯
            await self.leave_ladder()
    
    def get_battle_stats(self) -> Dict[str, Any]:
        """
        获取对战统计信息
        """
        if not self.client:
            return {}
        
        stats = {
            'total_battles': len(self.client.battles),
            'wins': 0,
            'losses': 0,
            'current_rating': None
        }
        
        for battle in self.client.battles.values():
            if battle.finished:
                if battle.won:
                    stats['wins'] += 1
                else:
                    stats['losses'] += 1
        
        return stats
    
    async def __aenter__(self):
        """
        异步上下文管理器入口
        """
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口
        """
        await self.disconnect()