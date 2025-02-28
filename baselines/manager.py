import random
from typing import Tuple

from sh_game.manager import Manager
from sh_game.player import Player
from sh_game.types.event_types import Event


class BaselineManager(Manager):
    def personal_event(self, event: Event, player: Player = None, **kwargs):
        self.history.append(
            f"Player {player.pid} got message {event._name_} with arguments {kwargs}"
        )
        print(self.history[-1])

    def inform_event(self, event: Event, **kwargs):
        self.history.append(f"Action {event._name_} happened with arguments {kwargs}")
        print(self.history[-1])

    def get_next_action(self) -> Tuple[Event, int]:
        legals = self.board.get_legal_actions()
        action_type = random.choice(list(legals.keys()))
        pid = random.choice(legals[action_type])
        return action_type, pid
