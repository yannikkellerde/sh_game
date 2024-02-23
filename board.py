from random import shuffle
from typing import Dict, List

from typeguard import typechecked

from sh_game.game_settings import GameSettings
from sh_game.player import Player
from sh_game.types.event_types import Event


class Board:
    def __init__(self, settings: GameSettings, players: List[Player]):
        self.settings = settings
        self.shuffle_callback = None

        self.players: List[Player] = players
        for player in self.players:
            player.board = self
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
        self.fascist_track = self.settings.fascist_pre_enact
        self.failed_election_tracker = 0
        self.discards = []

        self.term_blocked: List[Player] = []
        self.president: Player = self.players[0]
        self.chancellor: Player = None
        self.ex_president: Player = None
        self.ex_chancellor: Player = None

        self.special_elect_return_president: Player = None
        self.special_elect_choice: Player = None

        self.discard_claimed = False
        self.play_card_claimed = False
        self.action_claimed: bool = False

        self.action_type: Event = None
        self.action_done: bool = False
        self.phase: int = 0

    @property
    def tracks(self):
        return {"liberal": self.liberal_track, "fascist": self.fascist_track}

    @property
    def can_veto(self):
        return self.settings.fascist_track_length - self.fascist_track == 1

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
            if self.liberal_track == self.settings.liberal_track_length:
                return Event.LIBERAL_WIN
        else:
            assert policy == "fascist"
            self.fascist_track += 1
            if self.fascist_track == self.settings.fascist_track_length:
                return Event.FASCIST_WIN
        return None

    def nomination(self, chancellor: Player):
        self.ex_chancellor = self.chancellor
        self.chancellor = chancellor
        self.phase = 1

    def on_vote(self):
        self.action_type = None
        self.action_done = False
        self.phase = 2

    def vote_failed(self):
        # Nothing to claim if vote failed
        self.discard_claimed = True
        self.action_claimed = True
        self.play_card_claimed = True

        self.failed_election_tracker += 1
        if self.failed_election_tracker == self.settings.election_tracker_size:
            self.failed_election_tracker = 0
            self.term_blocked = []
            return True
        return False

    def vote_success(self):
        self.failed_election_tracker = 0
        self.discard_claimed = False
        self.action_claimed = False
        self.play_card_claimed = False

        self.term_blocked = [self.chancellor]
        if self.alive_players > 5:
            self.term_blocked.append(self.president)

    def compute_next_president(self) -> Player:
        assert self.president is not None
        if self.special_elect_choice is not None:
            return self.special_elect_choice
        if self.special_elect_return_president is not None:
            next_president = self.special_elect_return_president
        else:
            next_president = self.president
        old_pres = next_president
        while next_president is old_pres or next_president.is_dead:
            next_president = self.players[(next_president.id + 1) % len(self.players)]
        return next_president

    def set_next_president(self):
        if self.special_elect_choice is not None:
            return_pres = self.president
        self.ex_president = self.president
        self.president = self.compute_next_president()
        self.special_elect_return_president = None
        if self.special_elect_choice is not None:
            self.special_elect_return_president = return_pres
        self.special_elect_choice = None

    def get_legal_nominations(self):
        return [
            x
            for x in self.players
            if (
                not x.is_dead and not x in self.term_blocked and not x is self.president
            )
        ]

    def get_legal_to_act_on(self):
        return [x for x in self.players if (not x.is_dead and not x is self.president)]

    @typechecked
    def get_legal_actions(self) -> Dict[Event, List[int]]:
        if self.phase == 1:
            legals = {
                Event.VOTES: [0],
                Event.MESSAGE: [i for i, x in enumerate(self.players) if not x.is_dead],
            }
            if (
                not self.discard_claimed
                and self.ex_president is not None
                and not self.ex_president.is_dead
            ):
                legals[Event.PRESIDENT_CLAIM] = [self.ex_president.id]
            if (
                not self.play_card_claimed
                and self.ex_chancellor is not None
                and not self.ex_chancellor.is_dead
            ):
                legals[Event.CHANCELLOR_CLAIM] = [self.ex_chancellor.id]
        elif self.phase == 2:
            legals = {
                Event.MESSAGE: [i for i, x in enumerate(self.players) if not x.is_dead],
            }
            # if self.can_veto:
            #    assert self.action_type is None
            #    legals[Event.PRESIDENT_VETO] = [self.president.id]
            #    legals[Event.CHANCELLOR_VETO] = [self.chancellor.id]
            # else:
            if self.action_type is None or self.action_done:
                legals[Event.NOMINATION] = [self.compute_next_president().id]
            if not self.discard_claimed:
                legals[Event.PRESIDENT_CLAIM] = [self.president.id]
            if not self.play_card_claimed and not self.chancellor.is_dead:
                legals[Event.CHANCELLOR_CLAIM] = [self.chancellor.id]
            if self.action_type is not None and not self.action_done:
                legals[self.action_type] = [self.president.id]
            if self.action_done and not self.action_claimed:
                if self.action_type == Event.PEEK_MESSAGE:
                    legals[Event.PEEK_CLAIM] = [self.president.id]
                elif self.action_type == Event.INVESTIGATION_ACTION:
                    legals[Event.INVESTIGATION_CLAIM] = [self.president.id]
        return legals
