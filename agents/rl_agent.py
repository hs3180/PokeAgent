from .base_agent import BaseAgent
from poke_env.battle import Battle
from poke_env.player import Player
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional
import random

class SimpleRLNetwork(nn.Module):
    """
    简单的神经网络用于强化学习
    """
    def __init__(self, input_size: int, output_size: int, hidden_size: int = 128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )
    
    def forward(self, x):
        return self.network(x)

class RLAgent(BaseAgent):
    """
    强化学习Agent
    """
    
    def __init__(self, 
                 battle_format: str = "gen8randombattle",
                 learning_rate: float = 0.001,
                 epsilon: float = 0.1,
                 **kwargs):
        super().__init__(battle_format=battle_format, **kwargs)
        
        # 强化学习参数
        self.learning_rate = learning_rate
        self.epsilon = epsilon  # 探索率
        
        # 状态和动作空间大小（需要根据实际情况调整）
        self.state_size = 100  # 状态向量大小
        self.action_size = 50   # 动作空间大小
        
        # 神经网络
        self.q_network = SimpleRLNetwork(self.state_size, self.action_size)
        self.target_network = SimpleRLNetwork(self.state_size, self.action_size)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        # 优化器
        self.optimizer = torch.optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # 经验回放缓冲区
        self.memory = []
        self.memory_size = 10000
        
        # 训练参数
        self.batch_size = 32
        self.gamma = 0.99  # 折扣因子
        
    def choose_move(self, battle: Battle):
        """
        使用强化学习策略选择移动
        """
        if battle.finished:
            return None
            
        # 获取当前状态
        state = self.get_state_representation(battle)
        
        # epsilon-greedy策略
        if random.random() < self.epsilon:
            # 探索：随机选择
            return self.choose_random_move(battle)
        else:
            # 利用：使用Q网络选择最佳动作
            return self.choose_best_move(battle, state)
    
    def get_state_representation(self, battle: Battle) -> np.ndarray:
        """
        将战斗状态转换为神经网络输入向量
        """
        # 简化的状态表示，实际应用中需要更复杂的特征工程
        state = np.zeros(self.state_size)
        
        # 编码当前宝可梦信息
        if battle.active_pokemon:
            # 使用宝可梦的species_id作为特征
            pokemon_id = getattr(battle.active_pokemon, 'species_id', 0)
            state[0] = pokemon_id / 1000.0  # 归一化
            
            # 编码HP
            if hasattr(battle.active_pokemon, 'current_hp'):
                state[1] = battle.active_pokemon.current_hp / 100.0
        
        # 编码对手宝可梦信息
        if battle.opponent_active_pokemon:
            pokemon_id = getattr(battle.opponent_active_pokemon, 'species_id', 0)
            state[2] = pokemon_id / 1000.0
            
            if hasattr(battle.opponent_active_pokemon, 'current_hp'):
                state[3] = battle.opponent_active_pokemon.current_hp / 100.0
        
        # 编码可用动作
        available_moves = self.get_available_moves(battle)
        for i, move in enumerate(available_moves[:10]):  # 最多10个动作
            state[4 + i] = 1.0
            
        available_switches = self.get_available_switches(battle)
        for i, switch in enumerate(available_switches[:10]):
            state[14 + i] = 1.0
        
        return state
    
    def choose_best_move(self, battle: Battle, state: np.ndarray):
        """
        使用Q网络选择最佳动作
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.q_network(state_tensor)
        
        # 获取可用动作的Q值
        available_actions = self.get_available_moves(battle) + self.get_available_switches(battle)
        
        if not available_actions:
            return self.choose_random_move(battle)
        
        # 简化的动作选择逻辑
        # 在实际应用中，需要将Q值映射到具体的动作
        best_action_idx = q_values.argmax().item()
        
        # 这里需要根据实际的动作空间来映射
        # 暂时使用随机选择作为占位符
        return self.choose_random_move(battle)
    
    def store_experience(self, state: np.ndarray, action: int, reward: float, 
                        next_state: np.ndarray, done: bool):
        """
        存储经验到回放缓冲区
        """
        experience = (state, action, reward, next_state, done)
        self.memory.append(experience)
        
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
    
    def train_step(self):
        """
        执行一步训练
        """
        if len(self.memory) < self.batch_size:
            return
        
        # 采样batch
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.BoolTensor(dones)
        
        # 计算当前Q值
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # 计算目标Q值
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # 计算损失
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def update_target_network(self):
        """
        更新目标网络
        """
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def save_model(self, path: str):
        """
        保存模型
        """
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, path)
    
    def load_model(self, path: str):
        """
        加载模型
        """
        checkpoint = torch.load(path)
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])