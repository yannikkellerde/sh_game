from dataclasses import dataclass
import json


@dataclass
class GameSettings:
    num_players: int
    num_liberals: int
    num_fascists: int
    fascist_track: list
    num_fascist_cards: int
    num_liberal_cards: int
    hitler_knows_fascists: bool
    election_tracker_size: int = 3
    liberal_track_length: int = 5
    fascist_track_length: int = 6

    @property
    def track_len(self):
        return {
            "liberal": self.liberal_track_length,
            "fascist": self.fascist_track_length,
        }

    @classmethod
    def get_settings(
        cls,
        num_players: int,
        is_rebalanced: bool,
        config_path: str = "configs/game/shio_default.json",
    ):
        with open(config_path, "r") as f:
            config = json.load(f)

        return cls(
            num_players=num_players,
            **config[str(num_players)]["rebalanced" if is_rebalanced else "default"]
        )
