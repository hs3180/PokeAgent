import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from poke_env.player import Player
from poke_env.ps_client.account_configuration import AccountConfiguration
from poke_env.ps_client.server_configuration import ServerConfiguration, ShowdownServerConfiguration
from poke_env.battle import Battle
from .base_agent import BaseAgent

class ShowdownAgent(BaseAgent):
    """
    Pokemon Showdown Agent，可以连接到Showdown服务器进行在线对战
    """
    
    def choose_move(self, battle):
        """
        基本的移动选择逻辑 - 随机选择可用移动
        """
        import random
        if battle.available_moves:
            return self.create_order(random.choice(battle.available_moves))
        elif battle.available_switches:
            return self.create_order(random.choice(battle.available_switches))
        else:
            return self.create_order(random.choice(list(battle.available_moves) + list(battle.available_switches)))
    
    def __init__(self, 
                 username: str = None,
                 password: Optional[str] = None,
                 websocket_url: str = None,
                 auth_url: str = None,
                 battle_format: str = "gen8randombattle",
                 team: Optional[str] = None,
                 log_level: int = logging.INFO,
                 load_dotenv_file: bool = True,
                 **kwargs):
        """
        初始化Showdown Agent
        
        Args:
            username: Showdown用户名（可选，可以从环境变量POKEAGENT_USERNAME读取）
            password: Showdown密码（可选，可以从环境变量POKEAGENT_PASSWORD读取）
            websocket_url: 完整的WebSocket URL（可选，可以从环境变量POKEAGENT_WEBSOCKET_URL读取）
            auth_url: 认证URL（可选，可以从环境变量POKEAGENT_AUTH_URL读取，如未提供则从websocket_url自动生成）
            battle_format: 对战格式
            team: 对战队伍（可选，可以是Showdown队伍格式或packed格式）
            log_level: 日志级别
            load_dotenv_file: 是否自动加载.env文件（默认为True）
        """
        # 自动加载.env文件（如果存在）
        if load_dotenv_file:
            env_file = Path(__file__).parent.parent.parent / '.env'
            if env_file.exists():
                load_dotenv(env_file)
            else:
                # 尝试从当前目录加载
                load_dotenv()
        
        # 从环境变量读取配置，优先使用环境变量
        username = username or os.environ.get('POKEAGENT_USERNAME')
        password = password or os.environ.get('POKEAGENT_PASSWORD')
        websocket_url = websocket_url or os.environ.get('POKEAGENT_WEBSOCKET_URL')
        auth_url = auth_url or os.environ.get('POKEAGENT_AUTH_URL')
        
        # 强制用户设置必要的认证信息
        if not username:
            raise ValueError("Username is required. Set it as parameter or environment variable POKEAGENT_USERNAME")
        
        if not websocket_url:
            raise ValueError("WebSocket URL is required. Set it as parameter or environment variable POKEAGENT_WEBSOCKET_URL")
        
        # 如果没有提供auth_url，则从websocket_url自动生成
        if not auth_url:
            auth_url = websocket_url.replace("wss://", "https://").replace("/showdown/websocket", "/action.php?")
        
        # 创建账户配置
        account_config = AccountConfiguration(username, password)
        
        # 创建服务器配置
        server_config = ServerConfiguration(
            websocket_url=websocket_url,
            authentication_url=auth_url
        )
        
        self._log_level = log_level
        self._battle_format = battle_format
        self._team = team
        self._username = username
        self._password = password
        self.websocket_url = websocket_url
        self.auth_url = auth_url
        self.is_connected = False
        
        # 使用配置初始化Player
        super().__init__(
            account_configuration=account_config,
            server_configuration=server_config,
            battle_format=battle_format,
            team=team,
            log_level=log_level,
            **kwargs
        )
    
    @property
    def username(self):
        return self._username
        
    @property 
    def password(self):
        return self._password
        
    @property
    def log_level(self):
        return self._log_level
        
    async def connect(self):
        """
        连接到Showdown服务器
        """
        try:
            # Player会自动连接，只需要设置连接状态
            self.is_connected = True
            logging.info(f"成功连接到Showdown服务器: {self.websocket_url}")
            
        except Exception as e:
            logging.error(f"连接Showdown服务器失败: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """
        断开与Showdown服务器的连接
        """
        if self.is_connected:
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
        
        format_to_use = battle_format or self._battle_format
        await super().challenge_user(opponent, format_to_use)
        logging.info(f"已向 {opponent} 发起 {format_to_use} 格式的挑战")
    
    async def accept_challenge(self, battle_format: Optional[str] = None):
        """
        接受挑战
        
        Args:
            battle_format: 对战格式（可选，默认使用初始化时的格式）
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        format_to_use = battle_format or self._battle_format
        await super().accept_challenge(format_to_use)
        logging.info(f"已接受 {format_to_use} 格式的挑战")
    
    async def join_ladder(self, battle_format: Optional[str] = None, n_games: int = 1):
        """
        加入天梯对战
        
        Args:
            battle_format: 对战格式（可选，默认使用初始化时的格式）
            n_games: 要进行的对战数量（默认为1）
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        format_to_use = battle_format or self._battle_format
        # The ladder method expects the number of games, not the format
        # The format is already set during initialization
        try:
            await self.ladder(n_games)
            logging.info(f"已开始搜索 {format_to_use} 天梯对战，计划进行 {n_games} 场对战")
        except Exception as e:
            logging.error(f"加入天梯失败: {e}")
            raise
    
    async def leave_ladder(self):
        """
        离开天梯对战
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        # 发送取消搜索的消息
        await self.send_message("/cancelsearch")
        logging.info("已取消天梯对战搜索")
    
    async def run_battles(self, num_battles: int = 1, battle_format: Optional[str] = None):
        """
        运行指定数量的对战
        
        Args:
            num_battles: 对战数量
            battle_format: 对战格式（可选，默认使用初始化时的格式）
        """
        if not self.is_connected:
            raise RuntimeError("未连接到Showdown服务器")
        
        format_to_use = battle_format or self._battle_format
        battles_completed = 0
        
        try:
            while battles_completed < num_battles:
                # 加入天梯等待对战
                await self.join_ladder(format_to_use)
                
                # 等待对战开始
                while not self.battles:
                    await asyncio.sleep(1)
                
                # 处理所有对战
                for battle in self.battles.values():
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
        if not hasattr(self, 'player') or not self.player:
            return {}
        
        stats = {
            'total_battles': len(self.battles),
            'wins': 0,
            'losses': 0,
            'current_rating': None
        }
        
        for battle in self.battles.values():
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