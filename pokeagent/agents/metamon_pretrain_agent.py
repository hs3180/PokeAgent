import logging
from typing import Any, Dict

from poke_env.environment import Battle

from .base_agent import BaseAgent


class MetamonPretrainAgent(BaseAgent):
    """
    Metamon预训练Agent，使用标准的Metamon接口和预训练模型
    """

    def __init__(
        self,
        battle_format: str = "gen1ou",
        model_name: str = "SmallRL",
        **kwargs,
    ):
        super().__init__(battle_format=battle_format, **kwargs)

        self.model_name = model_name
        self.model = None
        self._initialized = False

        # 初始化Metamon环境
        self._setup_metamon_environment()

    def _setup_metamon_environment(self):
        """设置Metamon环境和组件"""
        try:
            # 尝试导入Metamon组件
            from metamon.rl.pretrained import load_pretrained_agent

            # 加载预训练模型
            self.model = load_pretrained_agent(self.model_name)
            if self.model is None:
                raise ValueError(f"Could not load pretrained model: {self.model_name}")

            # 尝试加载其他组件（可选）
            try:
                from metamon.interface import (
                    DefaultObservationSpace,
                    DefaultActionSpace,
                )
                from metamon.env import get_metamon_teams

                self.observation_space = DefaultObservationSpace()
                self.action_space = DefaultActionSpace()
                self.team_set = get_metamon_teams(self._battle_format, "competitive")
                self._has_full_interface = True

            except ImportError:
                # 如果没有完整接口，使用简化模式
                self._has_full_interface = False
                logging.warning("Using simplified mode without full Metamon interface")

            self._initialized = True
            logging.info(
                f"Successfully initialized Metamon environment with {self.model_name}"
            )

        except ImportError as e:
            logging.error(f"Failed to import Metamon components: {e}")
            logging.error(
                "Please ensure Metamon is properly installed with: pip install -e ./metamon"
            )
            self.model = None
            self._initialized = False
        except Exception as e:
            logging.error(f"Failed to setup Metamon environment: {e}")
            self.model = None
            self._initialized = False

    def choose_move(self, battle: Battle):
        """
        使用Metamon预训练模型选择移动
        """
        if battle.finished:
            return None

        if not self._initialized:
            logging.error("Metamon environment not properly initialized")
            return self.choose_random_move(battle)

        try:
            if self._has_full_interface:
                # 使用完整Metamon接口
                observation = self.observation_space.convert_battle_to_observation(
                    battle
                )
                action = self._select_action_with_model(observation, battle)
            else:
                # 使用简化模式
                action = self._select_action_simplified(battle)

            return action

        except Exception as e:
            logging.error(f"Error in Metamon agent: {e}")
            return self.choose_random_move(battle)

    def _select_action_with_model(self, observation, battle: Battle):
        """使用模型选择动作"""
        if self.model is None:
            return None

        try:
            # 根据模型类型选择合适的推理方法
            if hasattr(self.model, "act"):
                # RL模型的标准接口
                action_logits = self.model.act(observation)
                if hasattr(action_logits, "sample"):
                    # 如果是分布对象，采样
                    action_idx = action_logits.sample().item()
                elif hasattr(action_logits, "argmax"):
                    # 如果是tensor，取最大值
                    action_idx = action_logits.argmax().item()
                else:
                    # 直接使用
                    action_idx = int(action_logits)
            elif hasattr(self.model, "forward"):
                # 神经网络模型
                import torch

                with torch.no_grad():
                    action_logits = self.model(observation)
                    if isinstance(action_logits, torch.Tensor):
                        action_idx = action_logits.argmax().item()
                    else:
                        action_idx = int(action_logits)
            else:
                # 其他类型的模型/函数
                action_idx = self.model(observation)

            # 将动作索引转换为实际的动作
            return self._convert_action_to_order(action_idx, battle)

        except Exception as e:
            logging.error(f"Error in model inference: {e}")
            return self.choose_random_move(battle)

    def _convert_action_to_order(self, action_idx: int, battle: Battle):
        """将动作索引转换为poke-env订单"""
        try:
            # 确保动作索引在有效范围内
            action_idx = action_idx % 13  # Metamon UniversalAction空间有13个动作

            available_moves = list(battle.available_moves)
            available_switches = list(battle.available_switches)

            # Metamon UniversalAction空间:
            # 0-3: 移动 (按字母顺序)
            # 4-8: 切换 (按字母顺序)
            # 9-12: 特殊动作 (如Terastallization)

            if action_idx < 4 and action_idx < len(available_moves):
                # 移动动作
                return self.create_order(available_moves[action_idx])
            elif action_idx < 9:
                # 切换动作
                switch_idx = action_idx - 4
                if switch_idx < len(available_switches):
                    return self.create_order(available_switches[switch_idx])
            else:
                # 特殊动作 - 对于不支持的功能，回退到随机移动
                # 或者可以尝试映射到普通移动
                if available_moves:
                    return self.create_order(available_moves[0])
                elif available_switches:
                    return self.create_order(available_switches[0])

            # 如果没有可用动作，使用随机策略
            return self.choose_random_move(battle)

        except Exception as e:
            logging.error(f"Error converting action to order: {e}")
            return self.choose_random_move(battle)

    def _select_action_simplified(self, battle: Battle):
        """简化模式下的动作选择"""
        try:
            # 构建简化的状态表示
            state = self._build_simplified_state(battle)

            # 使用模型预测动作
            if hasattr(self.model, "act"):
                action_logits = self.model.act(state)
                if hasattr(action_logits, "argmax"):
                    action_idx = action_logits.argmax().item()
                else:
                    action_idx = int(action_logits)
            elif hasattr(self.model, "forward"):
                import torch

                with torch.no_grad():
                    action_logits = self.model(state)
                    action_idx = torch.argmax(action_logits).item()
            else:
                action_idx = self.model(state)

            # 简化的动作映射
            return self._simplified_action_mapping(action_idx, battle)

        except Exception as e:
            logging.error(f"Error in simplified action selection: {e}")
            return self.choose_random_move(battle)

    def _build_simplified_state(self, battle: Battle):
        """构建简化的状态表示"""
        # 基本状态信息
        state_features = []

        # 回合数
        state_features.append(battle.turn / 100.0)

        # 我方宝可梦状态
        if battle.active_pokemon:
            state_features.append(
                battle.active_pokemon.current_hp / max(battle.active_pokemon.max_hp, 1)
            )
            state_features.append(
                len([m for m in battle.active_pokemon.moves if m.current_pp > 0]) / 4.0
            )
        else:
            state_features.extend([0.0, 0.0])

        # 对手宝可梦状态
        if battle.opponent_active_pokemon:
            state_features.append(
                battle.opponent_active_pokemon.current_hp
                / max(battle.opponent_active_pokemon.max_hp, 1)
            )
        else:
            state_features.append(0.0)

        # 可用动作数量
        state_features.append(len(battle.available_moves) / 4.0)
        state_features.append(len(battle.available_switches) / 6.0)

        # 队伍状态
        active_team = [p for p in battle.team.values() if not p.fainted]
        opponent_team = [p for p in battle.opponent_team.values() if not p.fainted]
        state_features.append(len(active_team) / 6.0)
        state_features.append(len(opponent_team) / 6.0)

        # 填充到固定长度
        while len(state_features) < 18:
            state_features.append(0.0)

        import torch

        return torch.tensor(state_features, dtype=torch.float32).unsqueeze(0)

    def _simplified_action_mapping(self, action_idx: int, battle: Battle):
        """简化的动作映射"""
        available_moves = list(battle.available_moves)
        available_switches = list(battle.available_switches)

        total_actions = len(available_moves) + len(available_switches)
        if total_actions == 0:
            return self.choose_random_move(battle)

        # 确保动作索引在有效范围内
        action_idx = abs(action_idx) % total_actions

        if action_idx < len(available_moves):
            return self.create_order(available_moves[action_idx])
        else:
            switch_idx = action_idx - len(available_moves)
            if switch_idx < len(available_switches):
                return self.create_order(available_switches[switch_idx])

        return self.choose_random_move(battle)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            "model_name": self.model_name,
            "model_loaded": self.model is not None,
            "initialized": self._initialized,
            "battle_format": self._battle_format,
            "has_full_interface": getattr(self, "_has_full_interface", False),
        }

        if hasattr(self, "observation_space"):
            info["observation_space"] = type(self.observation_space).__name__
        if hasattr(self, "action_space"):
            info["action_space"] = type(self.action_space).__name__

        return info

    def get_battle_state(self, battle: Battle) -> Dict[str, Any]:
        """获取战斗状态，包含模型特定信息"""
        state = super().get_battle_state(battle)
        state.update(
            {
                "agent_type": "metamon_pretrain",
                "model_name": self.model_name,
                "model_loaded": self.model is not None,
                "initialized": self._initialized,
                "using_metamon_interface": True,
            }
        )
        return state
