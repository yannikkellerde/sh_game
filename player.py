from abc import ABC, abstractmethod
from typing import Dict
from .event_types import Event


class Player(ABC):
    def __init__(self, id, name):
        self.name: str = name
        self.reset(id)

    def reset(self, id):
        self.id: int = id
        self.role: str = None
        self.is_dead = False
        self.known_roles: Dict[Player, str] = {}
        self.history = []

    def __hash__(self):
        return hash(f"{self.name}_{self.id}")

    @property
    def is_fascist_team(self):
        return self.role in ("fascist", "hitler")

    def __repr__(self):
        return f"Player(id:{self.id}, name:{self.name}, role:{self.role})"

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
    def perform_action(self, event_type: Event, **kwargs):
        pass
