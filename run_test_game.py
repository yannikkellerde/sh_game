from sh_game.game import Game
from sh_game.baselines.player import BaselinePlayer
from sh_game.baselines.manager import BaselineManager

if __name__ == "__main__":
    manager = BaselineManager()
    players = [BaselinePlayer(i, "baseline_player") for i in range(7)]
    game = Game(manager=manager, players=players)
    game.run_game()
