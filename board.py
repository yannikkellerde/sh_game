from .game_settings import GameSettings
from .player import Player
from random import shuffle
from typing import List


class Board:
    def __init__(self, settings: GameSettings, players: List[Player]):
        self.settings = settings
        self.shuffle_callback = None

        self.players: List[Player] = players
        self.setup_new_game()

    def setup_new_game(self):
        self.policies = ["liberal"] * self.settings.num_liberal_cards + [
            "fascist"
        ] * self.settings.num_fascist_cards
        shuffle(self.policies)
        shuffle(self.players)
        for i, p in enumerate(self.players):
            p.reset(i)
        roles = (
            ["liberal"] * self.settings.num_liberals
            + ["fascist"] * (self.settings.num_fascists - 1)
            + ["hitler"]
        )
        assert len(roles) == len(self.players)
        shuffle(roles)
        for p, r in zip(self.players, roles):
            p.role = r

        self.liberal_track = 0
        self.fascist_track = 0
        self.failed_election_tracker = 0
        self.discards = []

        self.term_blocked: List[Player] = []
        self.president: Player = self.players[0]
        self.chancellor: Player = None

        self.special_elect_return_president: Player = None
        self.special_elect_choice: Player = None

        self.discard_claimed = False
        self.play_card_claimed = False
        self.action_claimed = False

        self.action_type = None
        self.action_done = False

    @property
    def tracks(self):
        return {"liberal": self.liberal_track, "fascist": self.fascist_track}

    @property
    def alive_players(self):
        return sum(not x.is_dead for x in self.players)

    def draw_policy(self, num):
        drawn = self.peek_policy(num)
        self.policies = self.policies[num:]
        return drawn

    def peek_policy(self, num):
        if len(self.policies) >= num:
            return self.policies[:num]
        else:
            # The discarded policies and the remaining policies are shuffled together
            self.policies = self.policies + self.discards
            shuffle(self.policies)
            if self.shuffle_callback is not None:
                self.shuffle_callback()
            self.discards = []
            assert len(self.policies) > num
            return self.peek_policy(num)

    def enact_policy(self, policy):
        if policy == "liberal":
            self.liberal_track += 1
        else:
            assert policy == "fascist"
            self.fascist_track += 1

    def nomination(self, chancellor: Player):
        self.chancellor = chancellor
        self.action_type = None
        self.action_done = False

    def on_vote(self):
        self.discard_claimed = False
        self.action_claimed = False
        self.play_card_claimed = False

    def vote_failed(self):
        self.failed_election_tracker += 1
        if self.failed_election_tracker == self.settings.election_tracker_size:
            self.failed_election_tracker = 0
            self.term_blocked = []
            return True
        return False

    def vote_success(self):
        self.term_blocked = [self.chancellor]
        if self.alive_players > 5:
            self.term_blocked.append(self.president)

    def compute_next_president(self):
        if self.special_elect_president is not None:
            return self.special_elect_president
        if self.special_elect_return_president is None:
            next_president = self.special_elect_return_president
        else:
            next_president = self.president
        old_pres = next_president
        while next_president is old_pres or next_president.is_dead:
            next_president = self.players[(next_president.id + 1) % len(self.players)]
        return next_president

    def set_next_president(self):
        if self.special_elect_president is not None:
            return_pres = self.president
        self.president = self.compute_next_president()
        self.special_elect_return_president = None
        if self.special_elect_president is not None:
            self.special_elect_return_president = return_pres
        self.special_elect_president = None
