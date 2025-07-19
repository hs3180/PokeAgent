#!/usr/bin/env python3
"""
Agent评估脚本
"""

import asyncio
import logging
import argparse
import os
import sys
from pathlib import Path
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from agents.rl_agent import RLAgent
from agents.llm_agent import LLMAgent
from agents.base_agent import BaseAgent
from env.battle_manager import BattleManager
from poke_env.player import RandomPlayer
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AgentEvaluator:
    """
    Agent评估器
    """
    
    def __init__(self, 
                 log_dir: str = "evaluation_logs",
                 battle_format: str = "gen8randombattle"):
        self.log_dir = log_dir
        self.battle_format = battle_format
        
        # 创建目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 初始化对战管理器
        self.battle_manager = BattleManager(
            battle_format=battle_format,
            log_battles=True,
            log_dir=log_dir
        )
        
        # 评估结果
        self.evaluation_results = {}
    
    async def evaluate_agent(self, 
                           agent: BaseAgent,
                           opponents: list,
                           num_battles: int = 50,
                           evaluation_id: str = None) -> dict:
        """
        评估单个Agent
        """
        if evaluation_id is None:
            evaluation_id = f"eval_{agent.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logging.info(f"开始评估Agent: {agent.username}")
        logging.info(f"对手数量: {len(opponents)}, 每对手对战数: {num_battles}")
        
        evaluation_result = {
            'evaluation_id': evaluation_id,
            'agent': agent.username,
            'agent_type': type(agent).__name__,
            'battle_format': self.battle_format,
            'num_battles': num_battles,
            'opponents': [opp.username for opp in opponents],
            'results': {},
            'overall_stats': {},
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        # 对每个对手进行评估
        for opponent in opponents:
            logging.info(f"评估对 {opponent.username} 的性能")
            
            opponent_results = await self.battle_manager.run_self_play_training(
                agent, opponent, num_battles=num_battles
            )
            
            evaluation_result['results'][opponent.username] = opponent_results
        
        # 计算总体统计
        evaluation_result['overall_stats'] = self._calculate_overall_stats(evaluation_result['results'])
        evaluation_result['end_time'] = datetime.now().isoformat()
        
        # 保存评估结果
        self._save_evaluation_result(evaluation_result)
        
        # 输出评估结果
        self._log_evaluation_results(evaluation_result)
        
        return evaluation_result
    
    async def compare_agents(self, 
                           agents: list,
                           opponents: list,
                           num_battles: int = 30) -> dict:
        """
        比较多个Agent的性能
        """
        logging.info(f"开始比较 {len(agents)} 个Agent的性能")
        
        comparison_result = {
            'comparison_id': f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'agents': [agent.username for agent in agents],
            'agent_types': [type(agent).__name__ for agent in agents],
            'opponents': [opp.username for opp in opponents],
            'num_battles': num_battles,
            'results': {},
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        # 评估每个Agent
        for agent in agents:
            agent_result = await self.evaluate_agent(
                agent, opponents, num_battles
            )
            comparison_result['results'][agent.username] = agent_result
        
        comparison_result['end_time'] = datetime.now().isoformat()
        
        # 分析比较结果
        comparison_result['analysis'] = self._analyze_comparison(comparison_result)
        
        # 保存比较结果
        self._save_comparison_result(comparison_result)
        
        # 输出比较结果
        self._log_comparison_results(comparison_result)
        
        return comparison_result
    
    async def benchmark_agents(self, 
                             agents: list,
                             benchmark_opponents: list = None) -> dict:
        """
        对Agent进行基准测试
        """
        if benchmark_opponents is None:
            # 创建标准基准对手
            benchmark_opponents = [
                RandomPlayer(battle_format=self.battle_format),
                # 可以添加其他基准对手
            ]
        
        logging.info(f"开始基准测试，Agent数量: {len(agents)}")
        
        benchmark_result = {
            'benchmark_id': f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'agents': [agent.username for agent in agents],
            'benchmark_opponents': [opp.username for opp in benchmark_opponents],
            'results': {},
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        # 对每个Agent进行基准测试
        for agent in agents:
            agent_benchmark = await self.evaluate_agent(
                agent, benchmark_opponents, num_battles=100
            )
            benchmark_result['results'][agent.username] = agent_benchmark
        
        benchmark_result['end_time'] = datetime.now().isoformat()
        
        # 生成基准报告
        benchmark_result['report'] = self._generate_benchmark_report(benchmark_result)
        
        # 保存基准测试结果
        self._save_benchmark_result(benchmark_result)
        
        return benchmark_result
    
    def _calculate_overall_stats(self, results: dict) -> dict:
        """
        计算总体统计
        """
        total_wins = 0
        total_losses = 0
        total_draws = 0
        total_turns = 0
        total_battles = 0
        
        for opponent_result in results.values():
            stats = opponent_result.get('stats', {})
            total_wins += stats.get('wins', 0)
            total_losses += stats.get('losses', 0)
            total_draws += stats.get('draws', 0)
            total_turns += stats.get('avg_turns', 0) * stats.get('num_battles', 0)
            total_battles += stats.get('num_battles', 0)
        
        if total_battles == 0:
            return {}
        
        return {
            'total_battles': total_battles,
            'wins': total_wins,
            'losses': total_losses,
            'draws': total_draws,
            'win_rate': total_wins / total_battles * 100,
            'loss_rate': total_losses / total_battles * 100,
            'draw_rate': total_draws / total_battles * 100,
            'avg_turns': total_turns / total_battles
        }
    
    def _analyze_comparison(self, comparison_result: dict) -> dict:
        """
        分析比较结果
        """
        analysis = {
            'rankings': {},
            'performance_matrix': {},
            'statistical_significance': {}
        }
        
        # 计算排名
        agent_performances = {}
        for agent_name, agent_result in comparison_result['results'].items():
            overall_stats = agent_result.get('overall_stats', {})
            win_rate = overall_stats.get('win_rate', 0.0)
            agent_performances[agent_name] = win_rate
        
        # 按胜率排序
        sorted_agents = sorted(agent_performances.items(), key=lambda x: x[1], reverse=True)
        analysis['rankings'] = {agent: rank + 1 for rank, (agent, _) in enumerate(sorted_agents)}
        
        # 性能矩阵
        for agent_name in comparison_result['agents']:
            analysis['performance_matrix'][agent_name] = {}
            for opponent_name in comparison_result['opponents']:
                agent_result = comparison_result['results'][agent_name]
                opponent_result = agent_result.get('results', {}).get(opponent_name, {})
                stats = opponent_result.get('stats', {})
                analysis['performance_matrix'][agent_name][opponent_name] = {
                    'win_rate': stats.get('win_rate', 0.0),
                    'avg_turns': stats.get('avg_turns', 0.0)
                }
        
        return analysis
    
    def _generate_benchmark_report(self, benchmark_result: dict) -> dict:
        """
        生成基准测试报告
        """
        report = {
            'summary': {},
            'detailed_analysis': {},
            'recommendations': []
        }
        
        # 总体摘要
        agent_count = len(benchmark_result['agents'])
        total_battles = sum(
            result.get('overall_stats', {}).get('total_battles', 0)
            for result in benchmark_result['results'].values()
        )
        
        report['summary'] = {
            'agent_count': agent_count,
            'total_battles': total_battles,
            'benchmark_date': benchmark_result['start_time']
        }
        
        # 详细分析
        for agent_name, agent_result in benchmark_result['results'].items():
            overall_stats = agent_result.get('overall_stats', {})
            report['detailed_analysis'][agent_name] = {
                'win_rate': overall_stats.get('win_rate', 0.0),
                'avg_turns': overall_stats.get('avg_turns', 0.0),
                'total_battles': overall_stats.get('total_battles', 0)
            }
        
        # 生成建议
        best_agent = max(
            report['detailed_analysis'].items(),
            key=lambda x: x[1]['win_rate']
        )
        
        report['recommendations'].append(f"最佳Agent: {best_agent[0]} (胜率: {best_agent[1]['win_rate']:.1f}%)")
        
        return report
    
    def _save_evaluation_result(self, result: dict):
        """
        保存评估结果
        """
        file_path = os.path.join(self.log_dir, f"{result['evaluation_id']}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logging.info(f"评估结果已保存: {file_path}")
    
    def _save_comparison_result(self, result: dict):
        """
        保存比较结果
        """
        file_path = os.path.join(self.log_dir, f"{result['comparison_id']}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logging.info(f"比较结果已保存: {file_path}")
    
    def _save_benchmark_result(self, result: dict):
        """
        保存基准测试结果
        """
        file_path = os.path.join(self.log_dir, f"{result['benchmark_id']}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logging.info(f"基准测试结果已保存: {file_path}")
    
    def _log_evaluation_results(self, result: dict):
        """
        输出评估结果
        """
        overall_stats = result.get('overall_stats', {})
        
        logging.info("=" * 60)
        logging.info(f"Agent评估结果: {result['agent']}")
        logging.info(f"总对战数: {overall_stats.get('total_battles', 0)}")
        logging.info(f"胜率: {overall_stats.get('win_rate', 0.0):.1f}%")
        logging.info(f"败率: {overall_stats.get('loss_rate', 0.0):.1f}%")
        logging.info(f"平局率: {overall_stats.get('draw_rate', 0.0):.1f}%")
        logging.info(f"平均回合数: {overall_stats.get('avg_turns', 0.0):.1f}")
        logging.info("=" * 60)
    
    def _log_comparison_results(self, result: dict):
        """
        输出比较结果
        """
        analysis = result.get('analysis', {})
        rankings = analysis.get('rankings', {})
        
        logging.info("=" * 60)
        logging.info("Agent性能比较结果:")
        logging.info("排名:")
        
        for agent, rank in sorted(rankings.items(), key=lambda x: x[1]):
            agent_result = result['results'][agent]
            overall_stats = agent_result.get('overall_stats', {})
            win_rate = overall_stats.get('win_rate', 0.0)
            logging.info(f"{rank}. {agent}: {win_rate:.1f}% 胜率")
        
        logging.info("=" * 60)
    
    def generate_plots(self, comparison_result: dict, save_dir: str = None):
        """
        生成性能图表
        """
        if save_dir is None:
            save_dir = self.log_dir
        
        os.makedirs(save_dir, exist_ok=True)
        
        # 胜率对比图
        agents = comparison_result['agents']
        win_rates = []
        
        for agent in agents:
            agent_result = comparison_result['results'][agent]
            overall_stats = agent_result.get('overall_stats', {})
            win_rates.append(overall_stats.get('win_rate', 0.0))
        
        plt.figure(figsize=(10, 6))
        plt.bar(agents, win_rates)
        plt.title('Agent胜率对比')
        plt.xlabel('Agent')
        plt.ylabel('胜率 (%)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, 'win_rates_comparison.png'))
        plt.close()
        
        # 平均回合数对比图
        avg_turns = []
        for agent in agents:
            agent_result = comparison_result['results'][agent]
            overall_stats = agent_result.get('overall_stats', {})
            avg_turns.append(overall_stats.get('avg_turns', 0.0))
        
        plt.figure(figsize=(10, 6))
        plt.bar(agents, avg_turns)
        plt.title('Agent平均回合数对比')
        plt.xlabel('Agent')
        plt.ylabel('平均回合数')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, 'avg_turns_comparison.png'))
        plt.close()

async def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='评估Agent性能')
    parser.add_argument('--mode', type=str, default='evaluate', 
                       choices=['evaluate', 'compare', 'benchmark'], 
                       help='评估模式')
    parser.add_argument('--agent-type', type=str, default='rl', 
                       choices=['rl', 'llm', 'random'], 
                       help='Agent类型')
    parser.add_argument('--model-path', type=str, help='模型路径（用于RL Agent）')
    parser.add_argument('--llm-model', type=str, default='microsoft/DialoGPT-medium', 
                       help='LLM模型名称')
    parser.add_argument('--battles', type=int, default=50, help='对战数量')
    parser.add_argument('--battle-format', type=str, default='gen8randombattle', 
                       help='对战格式')
    parser.add_argument('--log-dir', type=str, default='evaluation_logs', 
                       help='日志目录')
    parser.add_argument('--generate-plots', action='store_true', 
                       help='生成性能图表')
    
    args = parser.parse_args()
    
    # 创建评估器
    evaluator = AgentEvaluator(
        log_dir=args.log_dir,
        battle_format=args.battle_format
    )
    
    # 创建Agent
    if args.agent_type == 'rl':
        agent = RLAgent(battle_format=args.battle_format)
        if args.model_path and os.path.exists(args.model_path):
            agent.load_model(args.model_path)
            logging.info(f"已加载RL模型: {args.model_path}")
    elif args.agent_type == 'llm':
        agent = LLMAgent(
            battle_format=args.battle_format,
            model_name=args.llm_model
        )
    else:
        agent = RandomPlayer(battle_format=args.battle_format)
    
    # 创建对手
    opponents = [
        RandomPlayer(battle_format=args.battle_format),
        # 可以添加更多对手
    ]
    
    # 执行评估
    if args.mode == 'evaluate':
        result = await evaluator.evaluate_agent(
            agent, opponents, num_battles=args.battles
        )
    elif args.mode == 'compare':
        # 创建多个Agent进行比较
        agents = [agent]
        if args.agent_type == 'rl':
            agents.append(RLAgent(battle_format=args.battle_format))
        if args.agent_type == 'llm':
            agents.append(LLMAgent(battle_format=args.battle_format))
        agents.append(RandomPlayer(battle_format=args.battle_format))
        
        result = await evaluator.compare_agents(
            agents, opponents, num_battles=args.battles
        )
        
        if args.generate_plots:
            evaluator.generate_plots(result)
    elif args.mode == 'benchmark':
        result = await evaluator.benchmark_agents([agent])
    
    logging.info("评估完成！")

if __name__ == "__main__":
    asyncio.run(main())