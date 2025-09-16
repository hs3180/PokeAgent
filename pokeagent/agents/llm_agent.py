import json
import logging
from typing import Any, Dict

import torch
from poke_env.environment.battle import Battle
from transformers import AutoModelWithLMHead, AutoTokenizer

from .base_agent import BaseAgent


class LLMAgent(BaseAgent):
    """
    基于大语言模型的Agent
    """

    def __init__(
        self,
        battle_format: str = "gen1ou",
        model_name: str = "microsoft/DialoGPT-medium",
        max_length: int = 100,
        temperature: float = 0.7,
        **kwargs,
    ):
        super().__init__(battle_format=battle_format, **kwargs)

        # LLM参数
        self.model_name = model_name
        self.max_length = max_length
        self.temperature = temperature

        # 初始化模型和tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelWithLMHead.from_pretrained(model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
        except Exception as e:
            logging.warning(f"Failed to load model {model_name}: {e}")
            self.tokenizer = None
            self.model = None

        # 系统提示词
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """
        获取系统提示词
        """
        return """你是一个Pokemon对战AI助手。你需要根据当前战斗状态选择最佳的行动。

战斗规则：
1. 你可以选择使用技能或切换宝可梦
2. 每个宝可梦有4个技能槽
3. 宝可梦有HP、攻击、防御、特攻、特防、速度等属性
4. 技能有威力、命中率、PP等属性
5. 需要考虑属性相克关系

请根据以下信息选择最佳行动：
- 当前宝可梦和对手宝可梦的信息
- 可用技能和切换选项
- 当前战斗状态

请只回复行动选择，格式如下：
{
    "action_type": "move" or "switch",
    "action": "技能名称或宝可梦名称",
    "reasoning": "选择理由"
}"""

    def choose_move(self, battle: Battle):
        """
        使用LLM选择移动
        """
        if battle.finished:
            return None

        # 如果模型未加载，使用随机策略
        if self.model is None or self.tokenizer is None:
            return self.choose_random_move(battle)

        try:
            # 构建提示词
            prompt = self._build_prompt(battle)

            # 生成回复
            response = self._generate_response(prompt)

            # 解析回复
            action = self._parse_response(response, battle)

            return action

        except Exception as e:
            logging.error(f"LLM选择移动时出错: {e}")
            return self.choose_random_move(battle)

    def _build_prompt(self, battle: Battle) -> str:
        """
        构建LLM提示词
        """
        battle_state = self.get_battle_state(battle)

        prompt = f"{self.system_prompt}\n\n"
        prompt += "当前战斗状态：\n"
        prompt += f"- 回合: {battle_state['turn']}\n"
        prompt += f"- 我方宝可梦: {battle_state['active_pokemon']}\n"
        prompt += f"- 对手宝可梦: {battle_state['opponent_active_pokemon']}\n"
        prompt += f"- 可用技能: {', '.join(battle_state['available_moves'])}\n"
        prompt += f"- 可切换宝可梦: {', '.join(battle_state['available_switches'])}\n"
        prompt += f"- 我方队伍: {', '.join(battle_state['team'])}\n"
        prompt += f"- 对手队伍: {', '.join(battle_state['opponent_team'])}\n\n"

        # 添加宝可梦详细信息
        if battle.active_pokemon:
            prompt += "我方宝可梦详情:\n"
            prompt += f"- 物种: {battle.active_pokemon.species}\n"
            if hasattr(battle.active_pokemon, "current_hp"):
                prompt += f"- 当前HP: {battle.active_pokemon.current_hp}\n"
            if hasattr(battle.active_pokemon, "max_hp"):
                prompt += f"- 最大HP: {battle.active_pokemon.max_hp}\n"
            prompt += f"- 状态: {battle.active_pokemon.status}\n"

        if battle.opponent_active_pokemon:
            prompt += "对手宝可梦详情:\n"
            prompt += f"- 物种: {battle.opponent_active_pokemon.species}\n"
            if hasattr(battle.opponent_active_pokemon, "current_hp"):
                prompt += f"- 当前HP: {battle.opponent_active_pokemon.current_hp}\n"
            if hasattr(battle.opponent_active_pokemon, "max_hp"):
                prompt += f"- 最大HP: {battle.opponent_active_pokemon.max_hp}\n"
            prompt += f"- 状态: {battle.opponent_active_pokemon.status}\n"

        prompt += "\n请选择最佳行动："

        return prompt

    def _generate_response(self, prompt: str) -> str:
        """
        使用LLM生成回复
        """
        if self.tokenizer is None or self.model is None:
            # Fallback to random move if model is not available
            return "random"

        inputs = self.tokenizer.encode(
            prompt, return_tensors="pt", truncation=True, max_length=512
        )

        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=inputs.shape[1] + self.max_length,
                temperature=self.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 提取生成的回复部分
        if prompt in response:
            response = response[len(prompt) :].strip()

        return response

    def _parse_response(self, response: str, battle: Battle):
        """
        解析LLM回复并转换为动作
        """
        try:
            # 尝试解析JSON格式的回复
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
                parsed = json.loads(json_str)

                action_type = parsed.get("action_type", "move")
                action_name = parsed.get("action", "")

                if action_type == "move":
                    # 查找匹配的技能
                    for move in battle.available_moves:
                        if action_name.lower() in move.id.lower():
                            return self.create_order(move)
                elif action_type == "switch":
                    # 查找匹配的宝可梦
                    for pokemon in battle.available_switches:
                        if action_name.lower() in pokemon.species.lower():
                            return self.create_order(pokemon)

            # 如果JSON解析失败，尝试直接匹配
            available_moves = self.get_available_moves(battle)
            available_switches = self.get_available_switches(battle)

            # 在回复中查找可用的技能或宝可梦
            response_lower = response.lower()

            for move in available_moves:
                if move.lower() in response_lower:
                    for battle_move in battle.available_moves:
                        if battle_move.id == move:
                            return self.create_order(battle_move)

            for switch in available_switches:
                if switch.lower() in response_lower:
                    for pokemon in battle.available_switches:
                        if pokemon.species == switch:
                            return self.create_order(pokemon)

        except Exception as e:
            logging.error(f"解析LLM回复时出错: {e}")

        # 如果解析失败，使用随机策略
        return self.choose_random_move(battle)

    def update_model(self, model_name: str):
        """
        更新模型
        """
        try:
            self.model_name = model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelWithLMHead.from_pretrained(model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
            logging.info(f"成功更新模型为: {model_name}")
        except Exception as e:
            logging.error(f"更新模型失败: {e}")

    def set_temperature(self, temperature: float):
        """
        设置生成温度
        """
        self.temperature = max(0.1, min(2.0, temperature))

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        """
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_length": self.max_length,
            "model_loaded": self.model is not None,
        }

    def get_battle_state(self, battle: Battle):
        """
        Get battle state with LLM-specific information
        """
        state = super().get_battle_state(battle)
        state["agent_type"] = "llm"
        state["model_name"] = self.model_name
        state["model_loaded"] = self.model is not None
        return state
