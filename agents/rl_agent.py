from poke_env.player import Player

class RLAgent(Player):
    def choose_move(self, battle):
        # TODO: Use RL model to select a move
        return self.choose_random_move(battle)