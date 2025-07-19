from poke_env.battle import Battle
from poke_env.player import Player
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import gym
from gym import spaces

class PokeEnvWrapper(gym.Env):
    """
    poke-env的Gym风格包装器，提供标准化的强化学习环境接口
    """
    
    def __init__(self, player: Player, 
                 state_size: int = 100,
                 action_size: int = 50,
                 max_turns: int = 100):
        super().__init__()
        
        self.player = player
        self.state_size = state_size
        self.action_size = action_size
        self.max_turns = max_turns
        
        # 定义观察空间和动作空间
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(state_size,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(action_size)
        
        # 当前战斗状态
        self.current_battle = None
        self.current_state = None
        self.turn_count = 0
        
        # 动作映射
        self.action_mapping = {}
        self.reverse_action_mapping = {}
        
    def reset(self, seed=None):
        """
        重置环境
        """
        super().reset(seed=seed)
        
        self.current_battle = None
        self.current_state = None
        self.turn_count = 0
        
        # 返回初始状态（零向量）
        initial_state = np.zeros(self.state_size, dtype=np.float32)
        return initial_state
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        执行一步动作
        """
        if self.current_battle is None or self.current_battle.finished:
            return self.reset(), 0.0, True, {}
        
        # 将离散动作转换为实际动作
        actual_action = self._action_to_move(action)
        
        # 执行动作（这里需要与实际的poke-env集成）
        # 注意：实际的战斗逻辑需要在外部处理
        
        # 更新状态
        self.current_state = self._get_state_representation()
        
        # 计算奖励
        reward = self._calculate_reward()
        
        # 检查是否结束
        done = self._is_done()
        
        # 额外信息
        info = {
            'turn': self.turn_count,
            'battle_finished': self.current_battle.finished if self.current_battle else False,
            'action_taken': action
        }
        
        self.turn_count += 1
        
        return self.current_state, reward, done, info
    
    def _action_to_move(self, action: int):
        """
        将离散动作转换为实际的移动
        """
        if action in self.action_mapping:
            return self.action_mapping[action]
        
        # 如果没有映射，使用随机移动
        if self.current_battle:
            return self.player.choose_random_move(self.current_battle)
        
        return None
    
    def _get_state_representation(self) -> np.ndarray:
        """
        获取当前状态的向量表示
        """
        if self.current_battle is None:
            return np.zeros(self.state_size, dtype=np.float32)
        
        state = np.zeros(self.state_size, dtype=np.float32)
        
        # 编码当前宝可梦信息
        if self.current_battle.active_pokemon:
            pokemon_id = getattr(self.current_battle.active_pokemon, 'species_id', 0)
            state[0] = pokemon_id / 1000.0
            
            if hasattr(self.current_battle.active_pokemon, 'current_hp'):
                state[1] = self.current_battle.active_pokemon.current_hp / 100.0
        
        # 编码对手宝可梦信息
        if self.current_battle.opponent_active_pokemon:
            pokemon_id = getattr(self.current_battle.opponent_active_pokemon, 'species_id', 0)
            state[2] = pokemon_id / 1000.0
            
            if hasattr(self.current_battle.opponent_active_pokemon, 'current_hp'):
                state[3] = self.current_battle.opponent_active_pokemon.current_hp / 100.0
        
        # 编码可用动作
        available_moves = self.player.get_available_moves(self.current_battle)
        for i, move in enumerate(available_moves[:10]):
            state[4 + i] = 1.0
            
        available_switches = self.player.get_available_switches(self.current_battle)
        for i, switch in enumerate(available_switches[:10]):
            state[14 + i] = 1.0
        
        # 编码回合信息
        state[24] = self.current_battle.turn / self.max_turns
        
        # 编码胜负信息
        if self.current_battle.won:
            state[25] = 1.0
        elif self.current_battle.lost:
            state[26] = 1.0
        
        return state
    
    def _calculate_reward(self) -> float:
        """
        计算奖励
        """
        if self.current_battle is None:
            return 0.0
        
        reward = 0.0
        
        # 胜利奖励
        if self.current_battle.won:
            reward += 100.0
        elif self.current_battle.lost:
            reward -= 100.0
        
        # 基于HP的奖励
        if self.current_battle.active_pokemon:
            current_hp = getattr(self.current_battle.active_pokemon, 'current_hp', 0)
            max_hp = getattr(self.current_battle.active_pokemon, 'max_hp', 1)
            if max_hp > 0:
                hp_ratio = current_hp / max_hp
                reward += hp_ratio * 10.0
        
        # 对手HP减少的奖励
        if self.current_battle.opponent_active_pokemon:
            current_hp = getattr(self.current_battle.opponent_active_pokemon, 'current_hp', 0)
            max_hp = getattr(self.current_battle.opponent_active_pokemon, 'max_hp', 1)
            if max_hp > 0:
                hp_ratio = current_hp / max_hp
                reward += (1.0 - hp_ratio) * 10.0
        
        # 回合惩罚（鼓励快速结束战斗）
        reward -= 0.1
        
        return reward
    
    def _is_done(self) -> bool:
        """
        检查是否结束
        """
        if self.current_battle is None:
            return True
        
        return (self.current_battle.finished or 
                self.turn_count >= self.max_turns)
    
    def set_battle(self, battle: Battle):
        """
        设置当前战斗
        """
        self.current_battle = battle
        self.current_state = self._get_state_representation()
        self.turn_count = 0
    
    def update_action_mapping(self, available_actions: List[Any]):
        """
        更新动作映射
        """
        self.action_mapping.clear()
        self.reverse_action_mapping.clear()
        
        for i, action in enumerate(available_actions):
            if i < self.action_size:
                self.action_mapping[i] = action
                self.reverse_action_mapping[action] = i
    
    def get_battle_info(self) -> Dict[str, Any]:
        """
        获取战斗信息
        """
        if self.current_battle is None:
            return {}
        
        return {
            'turn': self.current_battle.turn,
            'finished': self.current_battle.finished,
            'won': self.current_battle.won,
            'lost': self.current_battle.lost,
            'active_pokemon': self.current_battle.active_pokemon.species if self.current_battle.active_pokemon else None,
            'opponent_active_pokemon': self.current_battle.opponent_active_pokemon.species if self.current_battle.opponent_active_pokemon else None
        }
    
    def render(self, mode='human'):
        """
        渲染环境（可选）
        """
        if self.current_battle:
            print(f"Turn {self.current_battle.turn}")
            print(f"Active: {self.current_battle.active_pokemon.species if self.current_battle.active_pokemon else 'None'}")
            print(f"Opponent: {self.current_battle.opponent_active_pokemon.species if self.current_battle.opponent_active_pokemon else 'None'}")
            print(f"Finished: {self.current_battle.finished}")
            print(f"Won: {self.current_battle.won}, Lost: {self.current_battle.lost}")
            print("-" * 50)