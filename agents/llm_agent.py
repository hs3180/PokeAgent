from poke_env.player import Player

class LLMAgent(Player):
    def choose_move(self, battle):
        # TODO: Use LLM to select a move
        return self.choose_random_move(battle)