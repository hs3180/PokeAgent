import logging
import os
from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn
from poke_env.battle import Battle

from .base_agent import BaseAgent


class MetamonPretrainAgent(BaseAgent):
    """
    Metamon预训练Agent，加载SmallRL模型进行对战
    """

    def __init__(
        self,
        battle_format: str = "gen1ou",
        model_path: Optional[str] = None,
        model_name: str = "SmallRL",
        **kwargs,
    ):
        super().__init__(battle_format=battle_format, **kwargs)

        self.model_name = model_name
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 加载模型
        self._load_model()

    def _get_default_model_path(self) -> str:
        """
        获取默认模型路径
        """
        # 检查多个可能的模型路径
        possible_paths = [
            "models/SmallRL.pt",
            "models/smallrl.pt",
            "metamon/models/SmallRL.pt",
            "checkpoints/SmallRL.pt",
            os.path.expanduser("~/.metamon/models/SmallRL.pt"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果找不到模型，记录警告
        logging.warning(f"Could not find SmallRL model at any of these paths: {possible_paths}")
        return "models/SmallRL.pt"

    def _load_model(self):
        """
        加载SmallRL模型
        """
        try:
            if os.path.exists(self.model_path):
                logging.info(f"Loading SmallRL model from {self.model_path}")
                
                # 根据文件扩展名选择加载方式
                if self.model_path.endswith('.pt') or self.model_path.endswith('.pth'):
                    self.model = torch.load(self.model_path, map_location=self.device)
                elif self.model_path.endswith('.pkl'):
                    import pickle
                    with open(self.model_path, 'rb') as f:
                        self.model = pickle.load(f)
                
                # 将模型移到正确设备并设置为评估模式
                if hasattr(self.model, 'to'):
                    self.model.to(self.device)
                if hasattr(self.model, 'eval'):
                    self.model.eval()
                
                logging.info(f"Successfully loaded {self.model_name} model")
            else:
                logging.error(f"Model file not found: {self.model_path}")
                self.model = None

        except Exception as e:
            logging.error(f"Failed to load {self.model_name} model: {e}")
            self.model = None

    def choose_move(self, battle: Battle):
        """
        使用SmallRL模型选择移动
        """
        if battle.finished:
            return None

        # 如果模型未加载，使用随机策略
        if self.model is None:
            logging.warning(f"{self.model_name} model not loaded, using random strategy")
            return self.choose_random_move(battle)

        try:
            # 构建状态表示
            state = self._build_state_representation(battle)
            
            # 使用模型预测动作
            action = self._predict_action(state, battle)
            
            return action

        except Exception as e:
            logging.error(f"Error in {self.model_name} agent: {e}")
            return self.choose_random_move(battle)

    def _build_state_representation(self, battle: Battle) -> Dict[str, Any]:
        """
        构建状态表示，兼容metamon的输入格式
        """
        state = {
            "battle_format": self._battle_format,
            "turn": battle.turn,
            "active_pokemon": None,
            "opponent_active_pokemon": None,
            "team": [],
            "opponent_team": [],
            "available_moves": [],
            "available_switches": [],
            "weather": None,
            "field": None,
        }

        # 获取我方活跃宝可梦信息
        if battle.active_pokemon:
            state["active_pokemon"] = {
                "species": battle.active_pokemon.species,
                "current_hp": getattr(battle.active_pokemon, "current_hp", 100),
                "max_hp": getattr(battle.active_pokemon, "max_hp", 100),
                "status": getattr(battle.active_pokemon, "status", None),
                "level": getattr(battle.active_pokemon, "level", 50),
                "ability": getattr(battle.active_pokemon, "ability", None),
                "item": getattr(battle.active_pokemon, "item", None),
                "stats": self._get_pokemon_stats(battle.active_pokemon),
                "moves": [
                    {
                        "id": move.id,
                        "current_pp": getattr(move, "current_pp", move.max_pp),
                        "max_pp": move.max_pp,
                        "type": move.type,
                        "power": getattr(move, "base_power", 0),
                        "accuracy": getattr(move, "accuracy", 100),
                        "category": getattr(move, "category", "Physical"),
                    }
                    for move in getattr(battle.active_pokemon, "moves", [])
                ],
            }

        # 获取对手活跃宝可梦信息
        if battle.opponent_active_pokemon:
            state["opponent_active_pokemon"] = {
                "species": battle.opponent_active_pokemon.species,
                "current_hp": getattr(battle.opponent_active_pokemon, "current_hp", 100),
                "max_hp": getattr(battle.opponent_active_pokemon, "max_hp", 100),
                "status": getattr(battle.opponent_active_pokemon, "status", None),
                "level": getattr(battle.opponent_active_pokemon, "level", 50),
                "ability": getattr(battle.opponent_active_pokemon, "ability", None),
                "item": getattr(battle.opponent_active_pokemon, "item", None),
                "stats": self._get_pokemon_stats(battle.opponent_active_pokemon),
            }

        # 获取队伍信息
        state["team"] = [
            {
                "species": pokemon.species,
                "current_hp": getattr(pokemon, "current_hp", 100),
                "max_hp": getattr(pokemon, "max_hp", 100),
                "status": getattr(pokemon, "status", None),
                "level": getattr(pokemon, "level", 50),
                "ability": getattr(pokemon, "ability", None),
                "item": getattr(pokemon, "item", None),
                "fainted": getattr(pokemon, "fainted", False),
                "active": pokemon == battle.active_pokemon,
            }
            for pokemon in battle.team.values()
        ]

        state["opponent_team"] = [
            {
                "species": pokemon.species,
                "current_hp": getattr(pokemon, "current_hp", 100),
                "max_hp": getattr(pokemon, "max_hp", 100),
                "status": getattr(pokemon, "status", None),
                "level": getattr(pokemon, "level", 50),
                "ability": getattr(pokemon, "ability", None),
                "item": getattr(pokemon, "item", None),
                "fainted": getattr(pokemon, "fainted", False),
                "active": pokemon == battle.opponent_active_pokemon,
            }
            for pokemon in battle.opponent_team.values()
        ]

        # 获取可用动作
        state["available_moves"] = [
            {
                "id": move.id,
                "current_pp": getattr(move, "current_pp", move.max_pp),
                "max_pp": move.max_pp,
                "type": move.type,
                "power": getattr(move, "base_power", 0),
                "accuracy": getattr(move, "accuracy", 100),
                "category": getattr(move, "category", "Physical"),
                "priority": getattr(move, "priority", 0),
            }
            for move in battle.available_moves
        ]

        state["available_switches"] = [
            pokemon.species for pokemon in battle.available_switches
        ]

        # 获取战场状态
        state["weather"] = getattr(battle, "weather", None)
        state["field"] = getattr(battle, "field", None)

        return state

    def _get_pokemon_stats(self, pokemon) -> Dict[str, int]:
        """
        获取宝可梦 stats
        """
        return {
            "hp": getattr(pokemon, "hp", 100),
            "atk": getattr(pokemon, "atk", 100),
            "def": getattr(pokemon, "def", 100),
            "spa": getattr(pokemon, "spa", 100),
            "spd": getattr(pokemon, "spd", 100),
            "spe": getattr(pokemon, "spe", 100),
        }

    def _predict_action(self, state: Dict[str, Any], battle: Battle):
        """
        使用模型预测动作
        """
        try:
            # 将状态转换为模型输入格式
            # 这里需要根据实际的SmallRL模型架构进行调整
            input_tensor = self._state_to_tensor(state)
            
            # 模型预测
            with torch.no_grad():
                if hasattr(self.model, 'forward'):
                    if hasattr(self.model, 'act'):  # RL模型通常有act方法
                        action_logits = self.model.act(input_tensor)
                    else:
                        action_logits = self.model(input_tensor)
                    
                    # 获取最佳动作
                    if isinstance(action_logits, torch.Tensor):
                        if action_logits.dim() > 1:
                            action_idx = torch.argmax(action_logits, dim=-1).item()
                        else:
                            action_idx = torch.argmax(action_logits).item()
                    else:
                        # 如果返回的是直接动作索引
                        action_idx = int(action_logits)
                else:
                    # 如果模型没有forward方法，假设它是一个动作选择函数
                    action_idx = self.model(state)

            # 将动作索引转换为实际动作
            return self._action_idx_to_order(action_idx, battle)

        except Exception as e:
            logging.error(f"Error predicting action: {e}")
            return self.choose_random_move(battle)

    def _state_to_tensor(self, state: Dict[str, Any]) -> torch.Tensor:
        """
        将状态转换为张量
        这是一个简化的实现，实际实现需要根据SmallRL模型的具体输入格式调整
        """
        # 这里创建一个简化的状态表示
        # 实际实现需要根据SmallRL模型的具体要求
        
        # 基本状态特征
        features = []
        
        # 回合数
        features.append(state["turn"] / 100.0)  # 归一化
        
        # 我方宝可梦特征
        if state["active_pokemon"]:
            ap = state["active_pokemon"]
            features.extend([
                ap["current_hp"] / max(ap["max_hp"], 1),
                len([m for m in ap["moves"] if m["current_pp"] > 0]) / 4.0,
            ])
        else:
            features.extend([0.0, 0.0])
        
        # 对手宝可梦特征
        if state["opponent_active_pokemon"]:
            op = state["opponent_active_pokemon"]
            features.append(op["current_hp"] / max(op["max_hp"], 1))
        else:
            features.append(0.0)
        
        # 可用动作数量
        features.append(len(state["available_moves"]) / 4.0)
        features.append(len(state["available_switches"]) / 6.0)
        
        # 队伍大小
        features.append(len([p for p in state["team"] if not p["fainted"]]) / 6.0)
        features.append(len([p for p in state["opponent_team"] if not p["fainted"]]) / 6.0)
        
        # 填充到固定长度（根据模型要求调整）
        target_length = 64  # 假设模型需要64维输入
        while len(features) < target_length:
            features.append(0.0)
        
        features = features[:target_length]
        
        return torch.tensor(features, dtype=torch.float32).to(self.device)

    def _action_idx_to_order(self, action_idx: int, battle: Battle):
        """
        将动作索引转换为poke-env订单
        """
        # 简化的动作映射
        # 前4个索引对应技能，后续对应切换
        available_moves = list(battle.available_moves)
        available_switches = list(battle.available_switches)
        
        total_actions = len(available_moves) + len(available_switches)
        
        if total_actions == 0:
            return self.choose_random_move(battle)
        
        # 确保动作索引在有效范围内
        action_idx = action_idx % total_actions
        
        if action_idx < len(available_moves):
            return self.create_order(available_moves[action_idx])
        else:
            switch_idx = action_idx - len(available_moves)
            if switch_idx < len(available_switches):
                return self.create_order(available_switches[switch_idx])
        
        return self.choose_random_move(battle)

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        """
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "model_loaded": self.model is not None,
            "device": str(self.device),
            "model_type": "RL" if "RL" in self.model_name else "IL",
        }

    def get_battle_state(self, battle: Battle) -> Dict[str, Any]:
        """
        获取战斗状态，包含模型特定信息
        """
        state = super().get_battle_state(battle)
        state.update({
            "agent_type": "metamon_pretrain",
            "model_name": self.model_name,
            "model_path": self.model_path,
            "model_loaded": self.model is not None,
            "device": str(self.device),
        })
        return state