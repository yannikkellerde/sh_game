from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Tuple

from sh_game.types.event_types import Event

if TYPE_CHECKING:
    from sh_game.board import Board
    from sh_game.game import Game


class Manager(ABC):
    def __init__(self):
        self.game: Game = None
        self.board: Board = None
        self.history = []
        self.game_number = 0

    def set_game(self, game: "Game"):
        self.game = game
        self.board = game.board

    def reset(self):
        self.history = []
        self.game_number += 1

    @abstractmethod
    def personal_event(self, event_type: Event, player=None, **kwargs):
        pass

    @abstractmethod
    def inform_event(self, event: Event, **kwargs):
        pass

    @abstractmethod
    def get_next_action(self) -> Tuple[Event, int]:
        pass
