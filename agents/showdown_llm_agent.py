import asyncio
import logging
from typing import Optional, Dict, Any
from .showdown_agent import ShowdownAgent
from .llm_agent import LLMAgent

class ShowdownLLMAgent(ShowdownAgent):
    """
    基于大语言模型的Showdown Agent
    """
    
    def __init__(self, 
                 username: str,
                 llm_agent: Optional[LLMAgent] = None,
                 model_name: str = "microsoft/DialoGPT-medium",
                 password: Optional[str] = None,
                 server_url: str = "sim.smogon.com",
                 server_port: int = 8000,
                 battle_format: str = "gen8randombattle",
                 log_level: int = logging.INFO,
                 **kwargs):
        """
        初始化Showdown LLM Agent
        
        Args:
            username: Showdown用户名
            llm_agent: 预配置的LLM Agent实例
            model_name: 语言模型名称（如果提供llm_agent则忽略）
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
        
        # 初始化LLM Agent
        if llm_agent is not None:
            self.llm_agent = llm_agent
        else:
            self.llm_agent = LLMAgent(model_name=model_name)
            logging.info(f"创建新的LLM Agent，使用模型: {model_name}")
    
    def choose_move(self, battle):
        """
        使用LLM Agent选择移动
        """
        try:
            # 使用LLM Agent的决策逻辑
            return self.llm_agent.choose_move(battle)
        except Exception as e:
            logging.warning(f"LLM Agent决策失败，使用随机移动: {e}")
            return self.choose_random_move(battle)
    
    def set_temperature(self, temperature: float):
        """
        设置生成温度
        """
        self.llm_agent.set_temperature(temperature)
        logging.info(f"LLM生成温度设置为: {temperature}")
    
    def set_max_length(self, max_length: int):
        """
        设置最大生成长度
        """
        self.llm_agent.set_max_length(max_length)
        logging.info(f"LLM最大生成长度设置为: {max_length}")
    
    async def run_showdown_battles(self, 
                                  num_battles: int = 10,
                                  temperature: float = 0.7,
                                  max_length: int = 100):
        """
        在Showdown上运行LLM Agent对战
        
        Args:
            num_battles: 对战数量
            temperature: 生成温度
            max_length: 最大生成长度
        """
        if not self.is_connected:
            await self.connect()
        
        # 设置LLM参数
        self.set_temperature(temperature)
        self.set_max_length(max_length)
        
        battles_completed = 0
        wins = 0
        losses = 0
        
        try:
            logging.info(f"开始Showdown LLM对战，计划对战 {num_battles} 场")
            logging.info(f"LLM参数 - 温度: {temperature}, 最大长度: {max_length}")
            
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
                        
                        if battles_completed >= num_battles:
                            break
                
                # 短暂等待
                await asyncio.sleep(2)
                
        except Exception as e:
            logging.error(f"Showdown LLM对战时发生错误: {e}")
            raise
        finally:
            await self.leave_ladder()
            
            # 输出最终统计
            final_win_rate = wins / battles_completed if battles_completed > 0 else 0
            logging.info(f"Showdown LLM对战完成 - 总对战: {battles_completed}, "
                        f"胜率: {final_win_rate:.2%} ({wins}胜{losses}负)")
    
    async def challenge_specific_user(self, 
                                     opponent: str, 
                                     num_battles: int = 1,
                                     temperature: float = 0.7):
        """
        挑战特定用户进行对战
        
        Args:
            opponent: 对手用户名
            num_battles: 对战数量
            temperature: 生成温度
        """
        if not self.is_connected:
            await self.connect()
        
        self.set_temperature(temperature)
        battles_completed = 0
        wins = 0
        losses = 0
        
        try:
            logging.info(f"开始挑战用户 {opponent}，计划对战 {num_battles} 场")
            
            while battles_completed < num_battles:
                # 发起挑战
                await self.challenge_user(opponent)
                
                # 等待对战开始
                while not self.client.battles:
                    await asyncio.sleep(1)
                
                # 处理对战
                for battle in self.client.battles.values():
                    if not battle.finished:
                        await battle.wait_until_finished()
                        battles_completed += 1
                        
                        # 更新统计
                        if battle.won:
                            wins += 1
                        else:
                            losses += 1
                        
                        logging.info(f"对战 {battles_completed}/{num_battles} 完成 - "
                                   f"结果: {'胜利' if battle.won else '失败'}")
                        
                        if battles_completed >= num_battles:
                            break
                
                # 等待一段时间再发起下一场挑战
                await asyncio.sleep(5)
                
        except Exception as e:
            logging.error(f"挑战用户 {opponent} 时发生错误: {e}")
            raise
        finally:
            # 输出最终统计
            final_win_rate = wins / battles_completed if battles_completed > 0 else 0
            logging.info(f"挑战 {opponent} 完成 - 总对战: {battles_completed}, "
                        f"胜率: {final_win_rate:.2%} ({wins}胜{losses}负)")
    
    def get_llm_stats(self) -> Dict[str, Any]:
        """
        获取LLM统计信息
        """
        stats = self.get_battle_stats()
        stats.update({
            'agent_type': 'LLM',
            'model_name': self.llm_agent.model_name,
            'temperature': getattr(self.llm_agent, 'temperature', None),
            'max_length': getattr(self.llm_agent, 'max_length', None)
        })
        return stats