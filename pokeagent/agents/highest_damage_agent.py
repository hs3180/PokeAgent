"""
Highest Damage Agent - Chooses moves with highest expected damage
"""

import logging

from poke_env.environment import Battle

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class HighestDamageAgent(BaseAgent):
    """
    Agent that chooses moves with highest expected damage output
    """

    def __init__(
        self, battle_format: str = "gen1ou", log_level: int = logging.INFO, **kwargs
    ):
        super().__init__(battle_format=battle_format, log_level=log_level, **kwargs)

    def choose_move(self, battle: Battle):
        """
        Choose the move with highest expected damage
        """
        if not battle.active_pokemon:
            logger.warning("No active pokemon")
            return None

        # Get all possible actions and their scores
        actions = []

        # Add available moves with damage calculations
        if battle.available_moves:
            for move in battle.available_moves:
                damage_score = self._calculate_move_score(move, battle)
                actions.append((move, "move", damage_score))

        # Add available switches
        if battle.available_switches:
            for pokemon in battle.available_switches:
                switch_score = self._calculate_switch_score(pokemon, battle)
                actions.append((pokemon, "switch", switch_score))

        if not actions:
            logger.warning("No available actions")
            return None

        # Sort by score (descending) and choose the best
        actions.sort(key=lambda x: x[2], reverse=True)
        choice, choice_type, score = actions[0]

        if choice_type == "move":
            logger.debug(f"Chose move: {choice.id} (score: {score})")
            return self.create_order(choice)
        else:
            logger.debug(f"Chose switch: {choice.species} (score: {score})")
            return self.create_order(choice)

    def _calculate_move_score(self, move, battle: Battle) -> float:
        """
        Calculate score for a move based on expected damage and other factors
        """
        if not battle.opponent_active_pokemon:
            return 0.0

        base_power = move.base_power or 0
        accuracy = move.accuracy or 100

        # Calculate type effectiveness
        effectiveness = self._calculate_type_effectiveness(
            move, battle.opponent_active_pokemon
        )

        # Calculate expected damage (simplified)
        expected_damage = (base_power * accuracy / 100) * effectiveness

        # Add bonus for status moves
        if move.category == "status":
            expected_damage += 10  # Arbitrary bonus for status moves

        # Add STAB bonus
        if move.type and any(move.type == t.type for t in battle.active_pokemon.types):
            expected_damage *= 1.5

        # Add priority bonus
        if move.priority > 0:
            expected_damage += 5
        elif move.priority < 0:
            expected_damage -= 5

        return expected_damage

    def _calculate_switch_score(self, pokemon, battle: Battle) -> float:
        """
        Calculate score for switching to a pokemon
        """
        if not battle.opponent_active_pokemon:
            return 0.0

        # Check if current pokemon is in trouble
        current_hp_percent = (
            battle.active_pokemon.current_hp / battle.active_pokemon.max_hp
            if battle.active_pokemon.max_hp > 0
            else 0
        )
        switch_hp_percent = (
            pokemon.current_hp / pokemon.max_hp if pokemon.max_hp > 0 else 0
        )

        # Base score is HP percentage difference
        score = switch_hp_percent - current_hp_percent

        # Add type advantage bonus
        if battle.opponent_active_pokemon.types:
            type_advantage = self._calculate_type_advantage(
                pokemon, battle.opponent_active_pokemon
            )
            score += type_advantage * 0.2

        # Only consider switching if new pokemon has significantly more HP
        if switch_hp_percent <= current_hp_percent + 0.2:
            score -= 10  # Penalty for switching to pokemon with similar or less HP

        return score

    def _calculate_type_effectiveness(self, move, opponent) -> float:
        """
        Calculate type effectiveness multiplier for a move against opponent
        """
        if not move.type or not opponent.types:
            return 1.0

        effectiveness = 1.0
        move_type = move.type

        # Simple type effectiveness chart (simplified for Gen 1)
        type_chart = {
            "fire": {
                "grass": 2.0,
                "ice": 2.0,
                "bug": 2.0,
                "water": 0.5,
                "fire": 0.5,
                "rock": 0.5,
                "dragon": 0.5,
            },
            "water": {
                "fire": 2.0,
                "ground": 2.0,
                "rock": 2.0,
                "water": 0.5,
                "grass": 0.5,
                "dragon": 0.5,
            },
            "electric": {
                "water": 2.0,
                "flying": 2.0,
                "electric": 0.5,
                "grass": 0.5,
                "dragon": 0.5,
            },
            "grass": {
                "water": 2.0,
                "ground": 2.0,
                "rock": 2.0,
                "fire": 0.5,
                "grass": 0.5,
                "poison": 0.5,
                "flying": 0.5,
                "bug": 0.5,
                "dragon": 0.5,
            },
            "ice": {
                "grass": 2.0,
                "ground": 2.0,
                "flying": 2.0,
                "dragon": 2.0,
                "water": 0.5,
                "ice": 0.5,
            },
            "fighting": {
                "normal": 2.0,
                "ice": 2.0,
                "rock": 2.0,
                "dark": 2.0,
                "poison": 0.5,
                "flying": 0.5,
                "psychic": 0.5,
                "bug": 0.5,
            },
            "poison": {
                "grass": 2.0,
                "poison": 0.5,
                "ground": 0.5,
                "rock": 0.5,
                "ghost": 0.5,
            },
            "ground": {
                "fire": 2.0,
                "electric": 2.0,
                "poison": 2.0,
                "rock": 2.0,
                "grass": 0.5,
                "bug": 0.5,
            },
            "flying": {
                "grass": 2.0,
                "fighting": 2.0,
                "bug": 2.0,
                "electric": 0.5,
                "rock": 0.5,
            },
            "psychic": {"fighting": 2.0, "poison": 2.0, "psychic": 0.5, "dark": 0.0},
            "bug": {
                "grass": 2.0,
                "psychic": 2.0,
                "dark": 2.0,
                "fire": 0.5,
                "fighting": 0.5,
                "poison": 0.5,
                "flying": 0.5,
                "ghost": 0.5,
            },
            "rock": {
                "fire": 2.0,
                "ice": 2.0,
                "flying": 2.0,
                "bug": 2.0,
                "fighting": 2.0,
                "ground": 0.5,
            },
            "ghost": {"psychic": 2.0, "ghost": 2.0, "dark": 0.5, "normal": 0.0},
            "dragon": {"dragon": 2.0},
            "dark": {"psychic": 2.0, "ghost": 2.0, "fighting": 2.0, "dark": 0.5},
            "steel": {
                "ice": 2.0,
                "rock": 2.0,
                "fire": 0.5,
                "water": 0.5,
                "electric": 0.5,
                "steel": 0.5,
            },
            "fairy": {
                "fighting": 2.0,
                "dragon": 2.0,
                "dark": 2.0,
                "poison": 0.5,
                "steel": 0.5,
            },
        }

        for opponent_type in opponent.types:
            if move_type in type_chart and opponent_type.type in type_chart[move_type]:
                effectiveness *= type_chart[move_type][opponent_type.type]

        return effectiveness

    def _calculate_type_advantage(self, attacker, defender) -> float:
        """
        Calculate type advantage score for attacker vs defender
        """
        if not defender.types:
            return 0.0

        advantage = 0.0

        # Check each type of the attacker against defender's types
        for attacker_type in attacker.types:
            for defender_type in defender.types:
                # Simplified advantage calculation
                if attacker_type.type == "fire" and defender_type.type in [
                    "grass",
                    "ice",
                    "bug",
                ]:
                    advantage += 1.0
                elif attacker_type.type == "water" and defender_type.type in [
                    "fire",
                    "ground",
                    "rock",
                ]:
                    advantage += 1.0
                elif attacker_type.type == "grass" and defender_type.type in [
                    "water",
                    "ground",
                    "rock",
                ]:
                    advantage += 1.0
                elif attacker_type.type == "electric" and defender_type.type in [
                    "water",
                    "flying",
                ]:
                    advantage += 1.0
                elif attacker_type.type == "ice" and defender_type.type in [
                    "grass",
                    "ground",
                    "flying",
                    "dragon",
                ]:
                    advantage += 1.0

        return advantage

    def get_battle_state(self, battle: Battle):
        """
        Get battle state with damage analysis
        """
        state = super().get_battle_state(battle)
        state["agent_type"] = "highest_damage"

        if battle.active_pokemon and battle.opponent_active_pokemon:
            state["current_hp_percent"] = (
                battle.active_pokemon.current_hp / battle.active_pokemon.max_hp
                if battle.active_pokemon.max_hp > 0
                else 0
            )
            state["opponent_hp_percent"] = (
                battle.opponent_active_pokemon.current_hp
                / battle.opponent_active_pokemon.max_hp
                if battle.opponent_active_pokemon.max_hp > 0
                else 0
            )

        return state
