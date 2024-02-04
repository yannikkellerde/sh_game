from abc import ABC, abstractmethod
from .event_types import Event


class Manager(ABC):
    @abstractmethod
    def personal_event(self, event_type: Event, player=None, **kwargs):
        pass

    @abstractmethod
    def inform_event(self, event_type: Event, **kwargs):
        pass

    @abstractmethod
    def get_legal_actions(self):
        pass

    @abstractmethod
    def get_next_action(self):
        pass
