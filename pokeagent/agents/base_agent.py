# -*- coding: utf-8 -*-
import logging
import random
from typing import Any, Dict, List, Optional

from poke_env.battle import Battle
from poke_env.data import GenData
from poke_env.player import Player


class BaseAgent(Player):
    """
    Base Agent class providing common battle logic and utility methods
    """

    def __init__(
        self,
        battle_format: str = "gen1ou",
        log_level: int = logging.INFO,
        **kwargs,
    ):
        # Don't call super().__init__ initially to avoid auto-connection
        # We'll initialize Player later when we have the proper configuration
        self._battle_format = battle_format
        self._log_level = log_level
        self._initialized = False
        self.gen_data = GenData.from_format(battle_format)

    def initialize_player(self, **kwargs):
        """Initialize the Player with proper configuration"""
        if not self._initialized:
            super().__init__(
                log_level=self._log_level,
                **kwargs
            )
            self._initialized = True

    def choose_move(self, battle: Battle):
        """
        Main method to choose move, subclasses must override this method
        """
        raise NotImplementedError("Subclasses must implement choose_move")

    def get_available_moves(self, battle: Battle) -> List[str]:
        """
        Get currently available moves
        """
        if battle.available_moves:
            return [move.id for move in battle.available_moves]
        return []

    def get_available_switches(self, battle: Battle) -> List[str]:
        """
        Get currently available Pokemon switches
        """
        if battle.available_switches:
            return [pokemon.species for pokemon in battle.available_switches]
        return []

    def get_battle_state(self, battle: Battle) -> Dict[str, Any]:
        """
        Get current battle state summary information
        """
        return {
            "turn": battle.turn,
            "active_pokemon": (
                battle.active_pokemon.species if battle.active_pokemon else None
            ),
            "opponent_active_pokemon": (
                battle.opponent_active_pokemon.species
                if battle.opponent_active_pokemon
                else None
            ),
            "available_moves": self.get_available_moves(battle),
            "available_switches": self.get_available_switches(battle),
            "team": [pokemon.species for pokemon in battle.team.values()],
            "opponent_team": [
                pokemon.species for pokemon in battle.opponent_team.values()
            ],
            "won": battle.won,
            "lost": battle.lost,
        }

    def choose_random_move(self, battle: Battle):
        """
        Randomly choose move (as fallback)
        """
        if battle.available_moves:
            return self.create_order(random.choice(battle.available_moves))
        elif battle.available_switches:
            return self.create_order(random.choice(battle.available_switches))
        else:
            return self.choose_random_move(battle)

    def is_battle_finished(self, battle: Battle) -> bool:
        """
        Check if battle is finished
        """
        return battle.finished

    def get_win_probability(self, battle: Battle) -> float:
        """
        Estimate win probability (simple implementation)
        """
        if battle.finished:
            return 1.0 if battle.won else 0.0

        # Simple win probability estimation
        my_remaining = len([p for p in battle.team.values() if p.fainted is False])
        opponent_remaining = len(
            [p for p in battle.opponent_team.values() if p.fainted is False]
        )

        if my_remaining == 0:
            return 0.0
        elif opponent_remaining == 0:
            return 1.0
        else:
            return my_remaining / (my_remaining + opponent_remaining)