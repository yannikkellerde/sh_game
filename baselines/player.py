import random
from typing import List, Optional

from sh_game.player import Player
from sh_game.types.event_types import Event


class BaselinePlayer(Player):
    def inform_event(self, event_type, **kwargs):
        pass

    def personal_event(self, event_type, **kwargs):
        pass

    def perform_action(self, event_type: Event, hand: Optional[List[str]] = None):
        if event_type == Event.NOMINATION:
            return random.choice(self.board.get_legal_nominations())
        elif event_type == Event.DISCARD:
            discard = random.choice(hand)
            hand.remove(discard)
            return hand, discard
        elif event_type == Event.PLAY_CARD:
            discard = random.choice(hand)
            hand.remove(discard)
            return hand[0], discard
        elif event_type in (Event.CHANCELLOR_VETO, Event.PRESIDENT_VETO):
            return random.choice([True, False])
        elif event_type == Event.MESSAGE:
            return "I will win"
        elif event_type in (Event.PRESIDENT_CLAIM, Event.PEEK_CLAIM):
            return [random.choice(["fascist", "liberal"]) for _ in range(3)]
        elif event_type == Event.CHANCELLOR_CLAIM:
            return [random.choice(["fascist", "liberal"]) for _ in range(2)]
        elif event_type == Event.INVESTIGATION_CLAIM:
            return random.choice(["fascist", "liberal"])
        elif event_type in (
            Event.INVESTIGATION_ACTION,
            Event.EXECUTE_ACTION,
            Event.SPECIAL_ELECT_ACTION,
        ):
            return random.choice(self.board.get_legal_to_act_on())
        elif event_type == Event.PERSONAL_VOTE:
            return random.choice(("ja", "nein"))
