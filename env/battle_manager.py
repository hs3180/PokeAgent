from poke_env.player import Player, RandomPlayer
from poke_env.battle import Battle
from typing import List, Dict, Any, Optional, Callable
import asyncio
import logging
from datetime import datetime
import json
import os

class BattleManager:
    """
    对战管理器，用于协调Agent之间的对战
    """
    
    def __init__(self, 
                 battle_format: str = "gen8randombattle",
                 max_concurrent_battles: int = 10,
                 log_battles: bool = True,
                 log_dir: str = "battle_logs"):
        self.battle_format = battle_format
        self.max_concurrent_battles = max_concurrent_battles
        self.log_battles = log_battles
        self.log_dir = log_dir
        
        # 创建日志目录
        if log_battles and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 对战统计
        self.battle_stats = {
            'total_battles': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'avg_turns': 0.0
        }
        
        # 回调函数
        self.on_battle_start: Optional[Callable] = None
        self.on_battle_end: Optional[Callable] = None
        self.on_turn_end: Optional[Callable] = None
        
    async def run_battle(self, 
                        player1: Player, 
                        player2: Player,
                        battle_id: Optional[str] = None) -> Dict[str, Any]:
        """
        运行单场对战
        """
        if battle_id is None:
            battle_id = f"battle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logging.info(f"开始对战 {battle_id}: {player1.username} vs {player2.username}")
        
        # 设置回调
        if self.on_battle_start:
            self.on_battle_start(battle_id, player1, player2)
        
        try:
            # 创建对战
            battle = await player1.send_challenges(
                opponent=player2.username,
                n_challenges=1,
                to_wait=True
            )
            
            if not battle:
                raise Exception("无法创建对战")
            
            battle = battle[0]  # 获取第一个对战
            
            # 等待对战结束
            await battle.finished
            
            # 记录结果
            result = self._record_battle_result(battle, battle_id)
            
            # 调用结束回调
            if self.on_battle_end:
                self.on_battle_end(battle_id, result)
            
            return result
            
        except Exception as e:
            logging.error(f"对战 {battle_id} 出错: {e}")
            return {
                'battle_id': battle_id,
                'error': str(e),
                'winner': None,
                'loser': None,
                'turns': 0,
                'finished': False
            }
    
    async def run_tournament(self, 
                           players: List[Player],
                           rounds: int = 1,
                           tournament_id: Optional[str] = None) -> Dict[str, Any]:
        """
        运行锦标赛
        """
        if tournament_id is None:
            tournament_id = f"tournament_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logging.info(f"开始锦标赛 {tournament_id}，参与者: {len(players)}，轮数: {rounds}")
        
        tournament_results = {
            'tournament_id': tournament_id,
            'players': [p.username for p in players],
            'rounds': rounds,
            'matches': [],
            'standings': {},
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        # 初始化积分
        for player in players:
            tournament_results['standings'][player.username] = {
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'points': 0
            }
        
        # 运行对战
        for round_num in range(rounds):
            logging.info(f"锦标赛 {tournament_id} 第 {round_num + 1} 轮")
            
            # 生成对战配对
            matches = self._generate_matches(players)
            
            # 并发运行对战
            tasks = []
            for i, (player1, player2) in enumerate(matches):
                battle_id = f"{tournament_id}_round{round_num + 1}_match{i + 1}"
                task = self.run_battle(player1, player2, battle_id)
                tasks.append(task)
            
            # 等待所有对战完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 记录结果
            for result in results:
                if isinstance(result, dict) and 'error' not in result:
                    tournament_results['matches'].append(result)
                    self._update_standings(tournament_results['standings'], result)
        
        tournament_results['end_time'] = datetime.now().isoformat()
        
        # 保存锦标赛结果
        if self.log_battles:
            self._save_tournament_results(tournament_results)
        
        return tournament_results
    
    async def run_self_play_training(self, 
                                   agent: Player,
                                   opponent: Player,
                                   num_battles: int = 100,
                                   training_id: Optional[str] = None) -> Dict[str, Any]:
        """
        运行自我对弈训练
        """
        if training_id is None:
            training_id = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logging.info(f"开始自我对弈训练 {training_id}，对战数: {num_battles}")
        
        training_results = {
            'training_id': training_id,
            'agent': agent.username,
            'opponent': opponent.username,
            'num_battles': num_battles,
            'battles': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        # 运行对战
        for i in range(num_battles):
            battle_id = f"{training_id}_battle_{i + 1}"
            result = await self.run_battle(agent, opponent, battle_id)
            training_results['battles'].append(result)
            
            # 每10场对战输出一次进度
            if (i + 1) % 10 == 0:
                wins = sum(1 for r in training_results['battles'] if r.get('winner') == agent.username)
                win_rate = wins / (i + 1) * 100
                logging.info(f"训练进度: {i + 1}/{num_battles}, 胜率: {win_rate:.1f}%")
        
        training_results['end_time'] = datetime.now().isoformat()
        
        # 计算训练统计
        wins = sum(1 for r in training_results['battles'] if r.get('winner') == agent.username)
        losses = sum(1 for r in training_results['battles'] if r.get('loser') == agent.username)
        draws = num_battles - wins - losses
        
        training_results['stats'] = {
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': wins / num_battles * 100,
            'avg_turns': sum(r.get('turns', 0) for r in training_results['battles']) / num_battles
        }
        
        # 保存训练结果
        if self.log_battles:
            self._save_training_results(training_results)
        
        return training_results
    
    def _record_battle_result(self, battle: Battle, battle_id: str) -> Dict[str, Any]:
        """
        记录对战结果
        """
        result = {
            'battle_id': battle_id,
            'player1': battle.player_username,
            'player2': battle.opponent_username,
            'turns': battle.turn,
            'finished': battle.finished,
            'winner': None,
            'loser': None,
            'timestamp': datetime.now().isoformat()
        }
        
        if battle.won:
            result['winner'] = battle.player_username
            result['loser'] = battle.opponent_username
            self.battle_stats['wins'] += 1
        elif battle.lost:
            result['winner'] = battle.opponent_username
            result['loser'] = battle.player_username
            self.battle_stats['losses'] += 1
        else:
            result['winner'] = 'draw'
            result['loser'] = 'draw'
            self.battle_stats['draws'] += 1
        
        self.battle_stats['total_battles'] += 1
        self.battle_stats['avg_turns'] = (
            (self.battle_stats['avg_turns'] * (self.battle_stats['total_battles'] - 1) + battle.turn) 
            / self.battle_stats['total_battles']
        )
        
        # 保存对战日志
        if self.log_battles:
            self._save_battle_log(battle, result)
        
        logging.info(f"对战 {battle_id} 结束: {result['winner']} 获胜，回合数: {battle.turn}")
        
        return result
    
    def _generate_matches(self, players: List[Player]) -> List[tuple]:
        """
        生成对战配对
        """
        import random
        matches = []
        players_copy = players.copy()
        random.shuffle(players_copy)
        
        # 简单的轮转配对
        for i in range(0, len(players_copy) - 1, 2):
            if i + 1 < len(players_copy):
                matches.append((players_copy[i], players_copy[i + 1]))
        
        return matches
    
    def _update_standings(self, standings: Dict[str, Dict], result: Dict[str, Any]):
        """
        更新积分榜
        """
        winner = result.get('winner')
        loser = result.get('loser')
        
        if winner and winner != 'draw':
            standings[winner]['wins'] += 1
            standings[winner]['points'] += 3
            standings[loser]['losses'] += 1
        else:
            # 平局
            standings[result['player1']]['draws'] += 1
            standings[result['player1']]['points'] += 1
            standings[result['player2']]['draws'] += 1
            standings[result['player2']]['points'] += 1
    
    def _save_battle_log(self, battle: Battle, result: Dict[str, Any]):
        """
        保存对战日志
        """
        log_file = os.path.join(self.log_dir, f"{result['battle_id']}.json")
        
        battle_log = {
            'result': result,
            'battle_log': battle.battle_log if hasattr(battle, 'battle_log') else [],
            'team': [pokemon.species for pokemon in battle.team.values()],
            'opponent_team': [pokemon.species for pokemon in battle.opponent_team.values()]
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(battle_log, f, ensure_ascii=False, indent=2)
    
    def _save_tournament_results(self, results: Dict[str, Any]):
        """
        保存锦标赛结果
        """
        log_file = os.path.join(self.log_dir, f"{results['tournament_id']}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def _save_training_results(self, results: Dict[str, Any]):
        """
        保存训练结果
        """
        log_file = os.path.join(self.log_dir, f"{results['training_id']}.json")
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取对战统计
        """
        return self.battle_stats.copy()
    
    def reset_stats(self):
        """
        重置统计
        """
        self.battle_stats = {
            'total_battles': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'avg_turns': 0.0
        }