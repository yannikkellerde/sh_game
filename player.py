from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

from sh_game.types.event_types import Event

if TYPE_CHECKING:
    from sh_game.board import Board


class Player(ABC):
    def __init__(self, pid, name, game_id=None, num_players=None, role=None):
        self.name: str = name
        self.pid: int = pid
        self.role: str = role
        self.board: Board = None
        self.num_players: int = num_players
        self.game_id: str = game_id
        self.is_dead: bool = False
        self.known_roles: dict[int, str] = {}
        self.history: list[Event] = []
        self.game_counter = 0

    def reset(self, pid, role=None):
        self.pid: int = pid
        self.role: str = role
        self.is_dead = False
        self.known_roles: dict[int, str] = {}
        self.history = []

        # Game counter is for versioning scheme
        self.game_counter += 1

    def __hash__(self):
        return hash(f"{self.name}_{self.pid}")

    @property
    def party_membership(self):
        return "liberal" if self.role == "liberal" else "fascist"

    @property
    def is_fascist_team(self):
        return self.role in ("fascist", "hitler")

    def __repr__(self):
        return f"Player(id:{self.pid}, role:{self.role})"

    @abstractmethod
    def inform_event(self, event: Event, **kwargs):
        """
        Get information on a game event that happened
        """

    @abstractmethod
    def personal_event(self, event: Event, **kwargs):
        """
        Get some personal event
        """

    @abstractmethod
    def perform_action(self, event_type: Event, **kwargs) -> tuple[Any, dict]:
        pass
