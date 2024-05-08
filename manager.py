from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Tuple

from sh_game.types.event_types import Event

if TYPE_CHECKING:
    from sh_game.board import Board


class Manager(ABC):
    def __init__(self):
        self.board: Board = None
        self.history = []
        self.game_number = 0

    def reset(self):
        self.history = []
        self.game_number += 1

    @abstractmethod
    def personal_event(self, event_type: Event, player=None, **kwargs):
        pass

    @abstractmethod
    def inform_event(self, event_type: Event, **kwargs):
        pass

    @abstractmethod
    def get_next_action(self) -> Tuple[Event, int]:
        pass
