"""
Random Move Agent - Chooses moves randomly
"""

import logging
import random

from poke_env.environment.battle import Battle

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RandomMoveAgent(BaseAgent):
    """
    Agent that chooses moves randomly
    """

    def __init__(
        self, battle_format: str = "gen1ou", log_level: int = logging.INFO, **kwargs
    ):
        super().__init__(battle_format=battle_format, log_level=log_level, **kwargs)

    def choose_move(self, battle: Battle):
        """
        Choose a move randomly from available options
        """
        available_moves = []

        # Add available moves
        if battle.available_moves:
            available_moves.extend([(move, "move") for move in battle.available_moves])

        # Add available switches
        if battle.available_switches:
            available_moves.extend(
                [(pokemon, "switch") for pokemon in battle.available_switches]
            )

        if not available_moves:
            logger.warning("No available moves or switches")
            return None

        # Choose randomly
        choice, choice_type = random.choice(available_moves)

        if choice_type == "move":
            logger.debug(f"Chose move: {choice.id}")
            return self.create_order(choice)
        else:
            logger.debug(f"Chose switch: {choice.species}")
            return self.create_order(choice)

    def get_battle_state(self, battle: Battle):
        """
        Get battle state with additional information for random agent
        """
        state = super().get_battle_state(battle)
        state["agent_type"] = "random"
        state["available_move_count"] = len(battle.available_moves)
        state["available_switch_count"] = len(battle.available_switches)
        return state
