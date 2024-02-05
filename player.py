from abc import ABC, abstractmethod
from typing import Dict, TYPE_CHECKING
from sh_game.types.event_types import Event
from typing import List, Optional

if TYPE_CHECKING:
    from sh_game.board import Board


class Player(ABC):
    def __init__(self, id, name):
        self.name: str = name
        self.reset(id)
        self.board: Board = None

    def reset(self, id):
        self.id: int = id
        self.role: str = None
        self.is_dead = False
        self.known_roles: Dict[Player, str] = {}
        self.history = []

    def __hash__(self):
        return hash(f"{self.name}_{self.id}")

    @property
    def party_membership(self):
        return "liberal" if self.role == "liberal" else "fascist"

    @property
    def is_fascist_team(self):
        return self.role in ("fascist", "hitler")

    def __repr__(self):
        return f"Player(id:{self.id}, role:{self.role})"

    @abstractmethod
    def inform_event(self, event_type: Event, **kwargs):
        """
        Get information on a game event that happened
        """

    @abstractmethod
    def personal_event(self, event_type: Event, **kwargs):
        """
        Get some personal event
        """

    @abstractmethod
    def perform_action(self, event_type: Event, hand: Optional[List[str]]):
        pass
