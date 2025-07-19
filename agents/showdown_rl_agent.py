import asyncio
import logging
from typing import Optional, Dict, Any
from .showdown_agent import ShowdownAgent
from .rl_agent import RLAgent

class ShowdownRLAgent(ShowdownAgent):
    """
    基于强化学习的Showdown Agent
    """
    
    def __init__(self, 
                 username: str,
                 rl_agent: Optional[RLAgent] = None,
                 model_path: Optional[str] = None,
                 password: Optional[str] = None,
                 server_url: str = "sim.smogon.com",
                 server_port: int = 8000,
                 battle_format: str = "gen8randombattle",
                 log_level: int = logging.INFO,
                 **kwargs):
        """
        初始化Showdown RL Agent
        
        Args:
            username: Showdown用户名
            rl_agent: 预训练的RL Agent实例
            model_path: 模型文件路径（如果提供rl_agent则忽略）
            password: Showdown密码（可选）
            server_url: Showdown服务器地址
            server_port: 服务器端口
            battle_format: 对战格式
            log_level: 日志级别
        """
        super().__init__(
            username=username,
            password=password,
            server_url=server_url,
            server_port=server_port,
            battle_format=battle_format,
            log_level=log_level,
            **kwargs
        )
        
        # 初始化RL Agent
        if rl_agent is not None:
            self.rl_agent = rl_agent
        elif model_path is not None:
            self.rl_agent = RLAgent()
            self.rl_agent.load_model(model_path)
            logging.info(f"从 {model_path} 加载RL模型")
        else:
            # 创建新的RL Agent
            self.rl_agent = RLAgent()
            logging.info("创建新的RL Agent")
    
    def choose_move(self, battle):
        """
        使用RL Agent选择移动
        """
        try:
            # 使用RL Agent的决策逻辑
            return self.rl_agent.choose_move(battle)
        except Exception as e:
            logging.warning(f"RL Agent决策失败，使用随机移动: {e}")
            return self.choose_random_move(battle)
    
    def save_model(self, path: str):
        """
        保存RL模型
        """
        self.rl_agent.save_model(path)
        logging.info(f"RL模型已保存到: {path}")
    
    def load_model(self, path: str):
        """
        加载RL模型
        """
        self.rl_agent.load_model(path)
        logging.info(f"RL模型已从 {path} 加载")
    
    async def train_on_showdown(self, 
                               num_battles: int = 100,
                               save_interval: int = 10,
                               model_save_path: str = "showdown_rl_model.pth"):
        """
        在Showdown上进行在线训练
        
        Args:
            num_battles: 训练对战数量
            save_interval: 保存间隔（每多少场对战保存一次）
            model_save_path: 模型保存路径
        """
        if not self.is_connected:
            await self.connect()
        
        battles_completed = 0
        wins = 0
        losses = 0
        
        try:
            logging.info(f"开始Showdown在线训练，计划对战 {num_battles} 场")
            
            while battles_completed < num_battles:
                # 加入天梯等待对战
                await self.join_ladder()
                
                # 等待对战开始
                while not self.client.battles:
                    await asyncio.sleep(1)
                
                # 处理所有对战
                for battle in self.client.battles.values():
                    if not battle.finished:
                        await battle.wait_until_finished()
                        battles_completed += 1
                        
                        # 更新统计
                        if battle.won:
                            wins += 1
                        else:
                            losses += 1
                        
                        # 计算胜率
                        win_rate = wins / battles_completed if battles_completed > 0 else 0
                        
                        logging.info(f"对战 {battles_completed}/{num_battles} 完成 - "
                                   f"胜率: {win_rate:.2%} ({wins}胜{losses}负)")
                        
                        # 定期保存模型
                        if battles_completed % save_interval == 0:
                            self.save_model(model_save_path)
                            logging.info(f"模型已保存到 {model_save_path}")
                        
                        if battles_completed >= num_battles:
                            break
                
                # 短暂等待
                await asyncio.sleep(2)
                
        except Exception as e:
            logging.error(f"Showdown训练过程中发生错误: {e}")
            raise
        finally:
            # 保存最终模型
            self.save_model(model_save_path)
            await self.leave_ladder()
            
            # 输出最终统计
            final_win_rate = wins / battles_completed if battles_completed > 0 else 0
            logging.info(f"Showdown训练完成 - 总对战: {battles_completed}, "
                        f"胜率: {final_win_rate:.2%} ({wins}胜{losses}负)")
    
    def get_training_stats(self) -> Dict[str, Any]:
        """
        获取训练统计信息
        """
        stats = self.get_battle_stats()
        stats.update({
            'agent_type': 'RL',
            'model_loaded': hasattr(self.rl_agent, 'model') and self.rl_agent.model is not None
        })
        return stats