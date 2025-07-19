#!/usr/bin/env python3
"""
Pokemon对战AI主程序
"""

import asyncio
import argparse
import logging
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from agents.rl_agent import RLAgent
from agents.llm_agent import LLMAgent
from agents.base_agent import BaseAgent
from env.battle_manager import BattleManager
from poke_env.player import RandomPlayer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PokemonBattleAI:
    """
    Pokemon对战AI主类
    """
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.battle_manager = BattleManager(
            battle_format=self.config.get('battle_format', 'gen8randombattle'),
            log_battles=self.config.get('logging', {}).get('save_battles', True),
            log_dir=self.config.get('logging', {}).get('log_dir', 'logs')
        )
    
    def _load_config(self, config_path: str) -> dict:
        """
        加载配置文件
        """
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认配置
            return {
                'battle_format': 'gen8randombattle',
                'agents': {
                    'rl_agent': {
                        'learning_rate': 0.001,
                        'epsilon': 0.1
                    },
                    'llm_agent': {
                        'model_name': 'microsoft/DialoGPT-medium',
                        'temperature': 0.7
                    }
                }
            }
    
    def create_agent(self, agent_type: str, **kwargs) -> BaseAgent:
        """
        创建Agent
        """
        config = self.config.get('agents', {}).get(f'{agent_type}_agent', {})
        config.update(kwargs)
        
        if agent_type == 'rl':
            return RLAgent(
                battle_format=self.config.get('battle_format', 'gen8randombattle'),
                **config
            )
        elif agent_type == 'llm':
            return LLMAgent(
                battle_format=self.config.get('battle_format', 'gen8randombattle'),
                **config
            )
        elif agent_type == 'random':
            return RandomPlayer(
                battle_format=self.config.get('battle_format', 'gen8randombattle')
            )
        else:
            raise ValueError(f"不支持的Agent类型: {agent_type}")
    
    async def train_rl_agent(self, 
                           episodes: int = None,
                           opponent_type: str = 'random',
                           **kwargs):
        """
        训练RL Agent
        """
        logging.info("开始训练RL Agent")
        
        # 创建Agent
        agent = self.create_agent('rl')
        opponent = self.create_agent(opponent_type)
        
        # 训练参数
        training_config = self.config.get('training', {})
        if episodes:
            training_config['episodes'] = episodes
        training_config.update(kwargs)
        
        # 运行训练
        from scripts.train_rl import RLTrainer
        trainer = RLTrainer(
            model_save_dir='models',
            log_dir='logs',
            battle_format=self.config.get('battle_format', 'gen8randombattle')
        )
        
        await trainer.train(agent, opponent, **training_config)
    
    async def run_llm_agent(self, 
                          battles: int = 10,
                          opponent_type: str = 'random',
                          **kwargs):
        """
        运行LLM Agent
        """
        logging.info("开始运行LLM Agent")
        
        # 创建Agent
        agent = self.create_agent('llm')
        opponent = self.create_agent(opponent_type)
        
        # 运行对战
        from scripts.run_llm import LLMRunner
        runner = LLMRunner(
            log_dir='llm_logs',
            battle_format=self.config.get('battle_format', 'gen8randombattle')
        )
        
        await runner.run_battles(agent, opponent, num_battles=battles)
    
    async def evaluate_agents(self, 
                            agent_types: list = None,
                            battles: int = 50,
                            **kwargs):
        """
        评估Agent性能
        """
        if agent_types is None:
            agent_types = ['rl', 'llm', 'random']
        
        logging.info(f"开始评估Agent: {agent_types}")
        
        # 创建Agent
        agents = [self.create_agent(agent_type) for agent_type in agent_types]
        opponents = [self.create_agent('random')]
        
        # 运行评估
        from scripts.evaluate import AgentEvaluator
        evaluator = AgentEvaluator(
            log_dir='evaluation_logs',
            battle_format=self.config.get('battle_format', 'gen8randombattle')
        )
        
        result = await evaluator.compare_agents(agents, opponents, num_battles=battles)
        
        # 生成图表
        if self.config.get('evaluation', {}).get('generate_plots', False):
            evaluator.generate_plots(result)
        
        return result
    
    async def run_tournament(self, 
                           agent_types: list = None,
                           rounds: int = 2,
                           **kwargs):
        """
        运行锦标赛
        """
        if agent_types is None:
            agent_types = ['rl', 'llm', 'random']
        
        logging.info(f"开始锦标赛: {agent_types}")
        
        # 创建Agent
        agents = [self.create_agent(agent_type) for agent_type in agent_types]
        
        # 运行锦标赛
        result = await self.battle_manager.run_tournament(agents, rounds=rounds)
        
        return result
    
    async def interactive_battle(self, 
                               agent_type: str = 'llm',
                               opponent_type: str = 'random'):
        """
        交互式对战
        """
        logging.info("开始交互式对战")
        
        # 创建Agent
        agent = self.create_agent(agent_type)
        opponent = self.create_agent(opponent_type)
        
        # 运行交互式对战
        from scripts.run_llm import LLMRunner
        runner = LLMRunner(
            log_dir='interactive_logs',
            battle_format=self.config.get('battle_format', 'gen8randombattle')
        )
        
        result = await runner.run_interactive_battle(agent, opponent)
        
        return result

async def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='Pokemon对战AI')
    parser.add_argument('--mode', type=str, required=True,
                       choices=['train', 'run', 'evaluate', 'tournament', 'interactive'],
                       help='运行模式')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--agent-type', type=str, default='rl',
                       choices=['rl', 'llm', 'random'],
                       help='Agent类型')
    parser.add_argument('--opponent-type', type=str, default='random',
                       choices=['rl', 'llm', 'random'],
                       help='对手类型')
    parser.add_argument('--episodes', type=int, default=1000, help='训练回合数')
    parser.add_argument('--battles', type=int, default=10, help='对战数量')
    parser.add_argument('--rounds', type=int, default=2, help='锦标赛轮数')
    parser.add_argument('--model-path', type=str, help='模型路径')
    
    args = parser.parse_args()
    
    # 创建主程序实例
    ai = PokemonBattleAI(args.config)
    
    try:
        if args.mode == 'train':
            await ai.train_rl_agent(
                episodes=args.episodes,
                opponent_type=args.opponent_type
            )
        
        elif args.mode == 'run':
            await ai.run_llm_agent(
                battles=args.battles,
                opponent_type=args.opponent_type
            )
        
        elif args.mode == 'evaluate':
            await ai.evaluate_agents(
                agent_types=[args.agent_type, 'random'],
                battles=args.battles
            )
        
        elif args.mode == 'tournament':
            await ai.run_tournament(
                agent_types=[args.agent_type, 'random'],
                rounds=args.rounds
            )
        
        elif args.mode == 'interactive':
            await ai.interactive_battle(
                agent_type=args.agent_type,
                opponent_type=args.opponent_type
            )
        
        logging.info("程序执行完成！")
        
    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.error(f"程序执行出错: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())