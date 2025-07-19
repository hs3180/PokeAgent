#!/usr/bin/env python3
"""
强化学习Agent训练脚本
"""

import asyncio
import logging
import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from agents.rl_agent import RLAgent
from agents.base_agent import BaseAgent
from env.battle_manager import BattleManager
from poke_env.player import RandomPlayer
import torch
import numpy as np
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class RLTrainer:
    """
    强化学习训练器
    """
    
    def __init__(self, 
                 model_save_dir: str = "models",
                 log_dir: str = "logs",
                 battle_format: str = "gen8randombattle"):
        self.model_save_dir = model_save_dir
        self.log_dir = log_dir
        self.battle_format = battle_format
        
        # 创建目录
        os.makedirs(model_save_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        
        # 初始化对战管理器
        self.battle_manager = BattleManager(
            battle_format=battle_format,
            log_battles=True,
            log_dir=log_dir
        )
        
        # 训练参数
        self.training_params = {
            'episodes': 1000,
            'episodes_per_eval': 50,
            'epsilon_start': 1.0,
            'epsilon_end': 0.01,
            'epsilon_decay': 0.995,
            'target_update_freq': 100,
            'save_freq': 200
        }
        
        # 训练统计
        self.training_stats = {
            'episode': 0,
            'total_reward': 0.0,
            'wins': 0,
            'losses': 0,
            'epsilon': 1.0,
            'loss_history': []
        }
    
    async def train(self, 
                   agent: RLAgent,
                   opponent: BaseAgent,
                   episodes: int = None,
                   **kwargs):
        """
        训练RL Agent
        """
        # 更新训练参数
        if episodes:
            self.training_params['episodes'] = episodes
        self.training_params.update(kwargs)
        
        logging.info(f"开始训练RL Agent，总回合数: {self.training_params['episodes']}")
        logging.info(f"训练参数: {self.training_params}")
        
        # 设置回调
        self.battle_manager.on_battle_end = self._on_battle_end
        
        # 训练循环
        for episode in range(self.training_params['episodes']):
            self.training_stats['episode'] = episode + 1
            
            # 更新epsilon
            self._update_epsilon()
            
            # 运行一场对战
            result = await self.battle_manager.run_battle(agent, opponent)
            
            # 处理对战结果
            self._process_battle_result(result, agent)
            
            # 训练神经网络
            if len(agent.memory) >= agent.batch_size:
                loss = agent.train_step()
                if loss is not None:
                    self.training_stats['loss_history'].append(loss)
            
            # 定期更新目标网络
            if episode % self.training_params['target_update_freq'] == 0:
                agent.update_target_network()
                logging.info(f"Episode {episode + 1}: 更新目标网络")
            
            # 定期评估
            if (episode + 1) % self.training_params['episodes_per_eval'] == 0:
                await self._evaluate_agent(agent, opponent)
            
            # 定期保存模型
            if (episode + 1) % self.training_params['save_freq'] == 0:
                self._save_model(agent, episode + 1)
            
            # 输出进度
            if (episode + 1) % 10 == 0:
                self._log_progress(episode + 1)
        
        # 训练结束
        logging.info("训练完成！")
        self._save_final_model(agent)
        self._save_training_stats()
    
    def _update_epsilon(self):
        """
        更新探索率
        """
        episode = self.training_stats['episode']
        self.training_stats['epsilon'] = max(
            self.training_params['epsilon_end'],
            self.training_params['epsilon_start'] * 
            (self.training_params['epsilon_decay'] ** episode)
        )
    
    def _on_battle_end(self, battle_id: str, result: dict):
        """
        对战结束回调
        """
        # 这里可以添加额外的处理逻辑
        pass
    
    def _process_battle_result(self, result: dict, agent: RLAgent):
        """
        处理对战结果
        """
        if 'error' in result:
            logging.warning(f"对战出错: {result['error']}")
            return
        
        # 更新统计
        if result.get('winner') == agent.username:
            self.training_stats['wins'] += 1
        elif result.get('loser') == agent.username:
            self.training_stats['losses'] += 1
        
        # 计算奖励
        reward = self._calculate_reward(result)
        self.training_stats['total_reward'] += reward
        
        # 存储经验（这里需要根据实际的战斗状态来实现）
        # 在实际应用中，需要在战斗过程中收集状态和动作
        # 这里只是示例
        if hasattr(agent, 'store_experience'):
            # 简化的经验存储
            state = np.zeros(agent.state_size)
            next_state = np.zeros(agent.state_size)
            action = 0
            done = result.get('finished', False)
            
            agent.store_experience(state, action, reward, next_state, done)
    
    def _calculate_reward(self, result: dict) -> float:
        """
        计算奖励
        """
        reward = 0.0
        
        if result.get('winner') == result.get('player1'):
            reward += 100.0  # 胜利奖励
        elif result.get('loser') == result.get('player1'):
            reward -= 100.0  # 失败惩罚
        
        # 回合惩罚（鼓励快速结束）
        turns = result.get('turns', 0)
        reward -= turns * 0.1
        
        return reward
    
    async def _evaluate_agent(self, agent: RLAgent, opponent: BaseAgent):
        """
        评估Agent性能
        """
        logging.info(f"开始评估Agent (Episode {self.training_stats['episode']})")
        
        # 临时设置epsilon为0（纯利用）
        original_epsilon = agent.epsilon
        agent.epsilon = 0.0
        
        # 运行评估对战
        eval_results = await self.battle_manager.run_self_play_training(
            agent, opponent, num_battles=10
        )
        
        # 恢复epsilon
        agent.epsilon = original_epsilon
        
        # 输出评估结果
        stats = eval_results.get('stats', {})
        win_rate = stats.get('win_rate', 0.0)
        avg_turns = stats.get('avg_turns', 0.0)
        
        logging.info(f"评估结果 - 胜率: {win_rate:.1f}%, 平均回合: {avg_turns:.1f}")
        
        # 保存评估结果
        eval_file = os.path.join(self.log_dir, f"eval_episode_{self.training_stats['episode']}.json")
        with open(eval_file, 'w') as f:
            import json
            json.dump(eval_results, f, indent=2)
    
    def _save_model(self, agent: RLAgent, episode: int):
        """
        保存模型
        """
        model_path = os.path.join(self.model_save_dir, f"rl_agent_episode_{episode}.pth")
        agent.save_model(model_path)
        logging.info(f"模型已保存: {model_path}")
    
    def _save_final_model(self, agent: RLAgent):
        """
        保存最终模型
        """
        model_path = os.path.join(self.model_save_dir, "rl_agent_final.pth")
        agent.save_model(model_path)
        logging.info(f"最终模型已保存: {model_path}")
    
    def _save_training_stats(self):
        """
        保存训练统计
        """
        stats_file = os.path.join(self.log_dir, "training_stats.json")
        with open(stats_file, 'w') as f:
            import json
            json.dump(self.training_stats, f, indent=2)
        logging.info(f"训练统计已保存: {stats_file}")
    
    def _log_progress(self, episode: int):
        """
        输出训练进度
        """
        total_episodes = self.training_params['episodes']
        progress = episode / total_episodes * 100
        
        wins = self.training_stats['wins']
        losses = self.training_stats['losses']
        total_battles = wins + losses
        win_rate = wins / total_battles * 100 if total_battles > 0 else 0.0
        
        avg_reward = self.training_stats['total_reward'] / episode
        epsilon = self.training_stats['epsilon']
        
        logging.info(
            f"进度: {episode}/{total_episodes} ({progress:.1f}%) | "
            f"胜率: {win_rate:.1f}% | "
            f"平均奖励: {avg_reward:.2f} | "
            f"Epsilon: {epsilon:.3f}"
        )

async def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='训练RL Agent')
    parser.add_argument('--episodes', type=int, default=1000, help='训练回合数')
    parser.add_argument('--epsilon-start', type=float, default=1.0, help='初始探索率')
    parser.add_argument('--epsilon-end', type=float, default=0.01, help='最终探索率')
    parser.add_argument('--epsilon-decay', type=float, default=0.995, help='探索率衰减')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='学习率')
    parser.add_argument('--battle-format', type=str, default='gen8randombattle', help='对战格式')
    parser.add_argument('--model-dir', type=str, default='models', help='模型保存目录')
    parser.add_argument('--log-dir', type=str, default='logs', help='日志目录')
    
    args = parser.parse_args()
    
    # 创建训练器
    trainer = RLTrainer(
        model_save_dir=args.model_dir,
        log_dir=args.log_dir,
        battle_format=args.battle_format
    )
    
    # 创建Agent
    agent = RLAgent(
        battle_format=args.battle_format,
        learning_rate=args.learning_rate,
        epsilon=args.epsilon_start
    )
    
    # 创建对手
    opponent = RandomPlayer(battle_format=args.battle_format)
    
    # 开始训练
    await trainer.train(
        agent=agent,
        opponent=opponent,
        episodes=args.episodes,
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_decay=args.epsilon_decay
    )

if __name__ == "__main__":
    asyncio.run(main())