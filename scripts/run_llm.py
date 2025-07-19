#!/usr/bin/env python3
"""
LLM Agent对战脚本
"""

import asyncio
import logging
import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from agents.llm_agent import LLMAgent
from agents.base_agent import BaseAgent
from env.battle_manager import BattleManager
from poke_env.player import RandomPlayer
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class LLMRunner:
    """
    LLM Agent运行器
    """
    
    def __init__(self, 
                 log_dir: str = "llm_logs",
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
        
        # 运行统计
        self.run_stats = {
            'total_battles': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'avg_turns': 0.0,
            'model_responses': []
        }
    
    async def run_battles(self, 
                         agent: LLMAgent,
                         opponent: BaseAgent,
                         num_battles: int = 10,
                         save_responses: bool = True):
        """
        运行多场对战
        """
        logging.info(f"开始运行LLM Agent对战，对战数: {num_battles}")
        logging.info(f"LLM模型: {agent.get_model_info()}")
        
        # 设置回调
        self.battle_manager.on_battle_end = self._on_battle_end
        
        # 运行对战
        for i in range(num_battles):
            battle_id = f"llm_battle_{i + 1}"
            logging.info(f"开始第 {i + 1}/{num_battles} 场对战")
            
            # 运行对战
            result = await self.battle_manager.run_battle(agent, opponent, battle_id)
            
            # 处理结果
            self._process_battle_result(result)
            
            # 输出进度
            if (i + 1) % 5 == 0:
                self._log_progress(i + 1, num_battles)
        
        # 输出最终统计
        self._log_final_stats()
        
        # 保存响应记录
        if save_responses:
            self._save_responses()
    
    async def run_tournament(self, 
                           agents: list,
                           rounds: int = 1,
                           tournament_id: str = None):
        """
        运行LLM Agent锦标赛
        """
        if tournament_id is None:
            tournament_id = f"llm_tournament_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logging.info(f"开始LLM Agent锦标赛: {tournament_id}")
        logging.info(f"参与者: {len(agents)} 个Agent，轮数: {rounds}")
        
        # 运行锦标赛
        results = await self.battle_manager.run_tournament(
            agents, rounds=rounds, tournament_id=tournament_id
        )
        
        # 分析结果
        self._analyze_tournament_results(results)
        
        return results
    
    async def run_interactive_battle(self, agent: LLMAgent, opponent: BaseAgent):
        """
        运行交互式对战（实时显示）
        """
        logging.info("开始交互式对战")
        
        # 设置回调来显示实时信息
        def on_battle_start(battle_id, player1, player2):
            print(f"\n=== 对战开始: {player1.username} vs {player2.username} ===")
        
        def on_battle_end(battle_id, result):
            print(f"\n=== 对战结束 ===")
            print(f"获胜者: {result.get('winner', 'Unknown')}")
            print(f"回合数: {result.get('turns', 0)}")
            print(f"持续时间: {result.get('duration', 'Unknown')}")
        
        self.battle_manager.on_battle_start = on_battle_start
        self.battle_manager.on_battle_end = on_battle_end
        
        # 运行对战
        result = await self.battle_manager.run_battle(agent, opponent)
        
        return result
    
    def _on_battle_end(self, battle_id: str, result: dict):
        """
        对战结束回调
        """
        # 记录模型响应（如果有的话）
        if hasattr(self, 'last_response'):
            self.run_stats['model_responses'].append({
                'battle_id': battle_id,
                'response': self.last_response,
                'result': result
            })
    
    def _process_battle_result(self, result: dict):
        """
        处理对战结果
        """
        if 'error' in result:
            logging.warning(f"对战出错: {result['error']}")
            return
        
        # 更新统计
        self.run_stats['total_battles'] += 1
        
        if result.get('winner') == result.get('player1'):
            self.run_stats['wins'] += 1
        elif result.get('loser') == result.get('player1'):
            self.run_stats['losses'] += 1
        else:
            self.run_stats['draws'] += 1
        
        # 更新平均回合数
        turns = result.get('turns', 0)
        total_battles = self.run_stats['total_battles']
        self.run_stats['avg_turns'] = (
            (self.run_stats['avg_turns'] * (total_battles - 1) + turns) / total_battles
        )
    
    def _log_progress(self, current: int, total: int):
        """
        输出进度
        """
        progress = current / total * 100
        wins = self.run_stats['wins']
        losses = self.run_stats['losses']
        total_battles = wins + losses
        win_rate = wins / total_battles * 100 if total_battles > 0 else 0.0
        
        logging.info(
            f"进度: {current}/{total} ({progress:.1f}%) | "
            f"胜率: {win_rate:.1f}% | "
            f"平均回合: {self.run_stats['avg_turns']:.1f}"
        )
    
    def _log_final_stats(self):
        """
        输出最终统计
        """
        total = self.run_stats['total_battles']
        wins = self.run_stats['wins']
        losses = self.run_stats['losses']
        draws = self.run_stats['draws']
        
        win_rate = wins / total * 100 if total > 0 else 0.0
        loss_rate = losses / total * 100 if total > 0 else 0.0
        draw_rate = draws / total * 100 if total > 0 else 0.0
        
        logging.info("=" * 50)
        logging.info("LLM Agent 最终统计:")
        logging.info(f"总对战数: {total}")
        logging.info(f"胜利: {wins} ({win_rate:.1f}%)")
        logging.info(f"失败: {losses} ({loss_rate:.1f}%)")
        logging.info(f"平局: {draws} ({draw_rate:.1f}%)")
        logging.info(f"平均回合数: {self.run_stats['avg_turns']:.1f}")
        logging.info("=" * 50)
    
    def _analyze_tournament_results(self, results: dict):
        """
        分析锦标赛结果
        """
        standings = results.get('standings', {})
        
        logging.info("=" * 50)
        logging.info("锦标赛结果:")
        logging.info("排名:")
        
        # 按积分排序
        sorted_standings = sorted(
            standings.items(), 
            key=lambda x: x[1]['points'], 
            reverse=True
        )
        
        for i, (player, stats) in enumerate(sorted_standings):
            logging.info(
                f"{i + 1}. {player}: "
                f"{stats['points']}分 "
                f"({stats['wins']}胜 {stats['losses']}负 {stats['draws']}平)"
            )
        
        logging.info("=" * 50)
    
    def _save_responses(self):
        """
        保存模型响应记录
        """
        if not self.run_stats['model_responses']:
            return
        
        responses_file = os.path.join(self.log_dir, "llm_responses.json")
        with open(responses_file, 'w', encoding='utf-8') as f:
            json.dump(self.run_stats['model_responses'], f, ensure_ascii=False, indent=2)
        
        logging.info(f"模型响应记录已保存: {responses_file}")

async def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='运行LLM Agent')
    parser.add_argument('--battles', type=int, default=10, help='对战数量')
    parser.add_argument('--model', type=str, default='microsoft/DialoGPT-medium', help='LLM模型名称')
    parser.add_argument('--temperature', type=float, default=0.7, help='生成温度')
    parser.add_argument('--max-length', type=int, default=100, help='最大生成长度')
    parser.add_argument('--battle-format', type=str, default='gen8randombattle', help='对战格式')
    parser.add_argument('--log-dir', type=str, default='llm_logs', help='日志目录')
    parser.add_argument('--interactive', action='store_true', help='交互式对战')
    parser.add_argument('--tournament', action='store_true', help='运行锦标赛')
    parser.add_argument('--opponent', type=str, default='random', help='对手类型 (random, rl)')
    
    args = parser.parse_args()
    
    # 创建运行器
    runner = LLMRunner(
        log_dir=args.log_dir,
        battle_format=args.battle_format
    )
    
    # 创建LLM Agent
    agent = LLMAgent(
        battle_format=args.battle_format,
        model_name=args.model,
        temperature=args.temperature,
        max_length=args.max_length
    )
    
    # 创建对手
    if args.opponent == 'random':
        opponent = RandomPlayer(battle_format=args.battle_format)
    elif args.opponent == 'rl':
        from agents.rl_agent import RLAgent
        opponent = RLAgent(battle_format=args.battle_format)
        # 如果有训练好的模型，可以加载
        # opponent.load_model("models/rl_agent_final.pth")
    else:
        opponent = RandomPlayer(battle_format=args.battle_format)
    
    # 运行对战
    if args.interactive:
        await runner.run_interactive_battle(agent, opponent)
    elif args.tournament:
        # 创建多个Agent进行锦标赛
        agents = [agent, opponent]
        if args.opponent == 'random':
            # 添加更多随机Agent
            for i in range(3):
                agents.append(RandomPlayer(battle_format=args.battle_format))
        
        await runner.run_tournament(agents, rounds=2)
    else:
        await runner.run_battles(agent, opponent, num_battles=args.battles)

if __name__ == "__main__":
    asyncio.run(main())