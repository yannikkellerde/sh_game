from typing import Tuple
from sh_game.manager import Manager
from sh_game.types.event_types import Event
from sh_game.player import Player
import random


class BaselineManager(Manager):
    def personal_event(self, event_type: Event, player: Player = None, **kwargs):
        self.history.append(
            f"Player {player.id} performed action {event_type._name_} with arguments {kwargs}"
        )

    def inform_event(self, event_type: Event, **kwargs):
        self.history.append(
            f"Action {event_type._name_} happened with arguments {kwargs}"
        )

    def get_next_action(self) -> Tuple[Event, int]:
        legals = self.board.get_legal_actions()
        action_type = random.choice(legals.keys())
        pid = random.choice(legals[action_type])
        return action_type, pid
