import uuid
from random import shuffle
from typing import Dict, List, Optional

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
        game_id = uuid.uuid4()
        for i, p in enumerate(self.players):
            p.reset(i)
            p.game_id = game_id
            p.num_players = len(self.players)

        shuffle(self.players)
        self.pid2player = {p.pid: p for p in self.players}
        self.pid2index = {p.pid: i for i, p in enumerate(self.players)}

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
        self.inv_target: Player = None

        self.term_blocked: List[Player] = []
        self.president: Player = self.pid2player[0]
        self.chancellor: Player = None
        self.ex_president: Player = None
        self.ex_chancellor: Player = None

        self.special_elect_return_president: Player = None
        self.special_elect_choice: Player = None

        self.discard_to_claim: Optional[Player] = None
        self.play_card_to_claim: Optional[Player] = None
        self.action_to_claim: Optional[Player] = None

        self.action_type: Event = None
        self.action_done: bool = False
        self.phase: int = 0
        self.round_number: int = 0

        self.chanc_veto: Optional[bool] = None
        self.pres_veto: Optional[bool] = None
        self.pending_policy: Optional[str] = None

        self.player_votes: dict[Player, bool] = {}

    @property
    def hitler(self):
        for p in self.players:
            if p.role == "hitler":
                return p

    @property
    def fascist_team_size(self):
        return sum(1 for p in self.players if p.is_fascist_team and not p.is_dead)

    @property
    def liberal_team_size(self):
        return sum(1 for p in self.players if p.role == "liberal" and not p.is_dead)

    @property
    def tracks(self):
        return {"liberal": self.liberal_track, "fascist": self.fascist_track}

    @property
    def can_veto(self):
        return self.settings.fascist_track_length - self.fascist_track == 1

    @property
    def alive_players(self):
        return sum(not x.is_dead for x in self.players)

    def draw_policy(self, num) -> str:
        drawn = self.peek_policy(num)
        self.policies = self.policies[num:]
        return drawn

    def peek_policy(self, num) -> str:
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
        self.chanc_veto = None
        self.pres_veto = None
        self.ex_chancellor = self.chancellor
        self.chancellor = chancellor
        self.phase = 1
        self.pending_policy = None

    def on_vote(self):
        self.player_votes = {p: None for p in self.players}
        self.action_type = None
        self.action_done = False

        # Too late to claim now if voting already happened
        self.discard_to_claim = None
        self.play_card_to_claim = None

        self.phase = 2

    def vote_failed(self):
        # Nothing to claim if vote failed
        self.discard_to_claim = None
        self.play_card_to_claim = None

        self.failed_election_tracker += 1
        if self.failed_election_tracker == self.settings.election_tracker_size:
            self.failed_election_tracker = 0
            self.term_blocked = []
            return True
        return False

    def vote_success(self):
        self.failed_election_tracker = 0
        self.discard_to_claim = self.president
        self.play_card_to_claim = self.chancellor

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
            next_president = self.pid2player[
                (next_president.pid + 1) % len(self.players)
            ]
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

    def get_legal_nominations(self) -> list[Player]:
        return [
            x
            for x in self.players
            if (
                not x.is_dead and not x in self.term_blocked and not x is self.president
            )
        ]

    def get_legal_to_act_on(self):
        return [x for x in self.players if (not x.is_dead and not x is self.president)]

    def get_legal_actions(self) -> Dict[Event, List[int]]:
        if self.phase == 1:
            legals = {
                Event.PERSONAL_VOTE: list(range(len(self.players))),
                Event.MESSAGE: [
                    pid for pid, player in self.pid2player.items() if not player.is_dead
                ],
            }
        elif self.phase in (0, 2):
            legals = {
                Event.MESSAGE: [
                    pid for pid, player in self.pid2player.items() if not player.is_dead
                ],
            }
            if self.action_type is None or self.action_done:
                legals[Event.NOMINATION] = [self.president.pid]
            if self.action_type is not None and not self.action_done:
                if self.action_type == Event.CHANCELLOR_VETO:
                    legals[Event.CHANCELLOR_VETO] = [self.chancellor.pid]
                else:
                    legals[self.action_type] = [self.president.pid]
        if self.discard_to_claim is not None and not self.discard_to_claim.is_dead:
            legals[Event.PRESIDENT_CLAIM] = [self.discard_to_claim.pid]
        if self.play_card_to_claim is not None and not self.play_card_to_claim.is_dead:
            legals[Event.CHANCELLOR_CLAIM] = [self.play_card_to_claim.pid]
        if (
            self.action_done
            and self.action_to_claim is not None
            and not self.action_to_claim.is_dead
        ):
            if self.action_type == Event.PEEK_MESSAGE:
                legals[Event.PEEK_CLAIM] = [self.action_to_claim.pid]
            elif self.action_type == Event.INVESTIGATION_ACTION:
                legals[Event.INVESTIGATION_CLAIM] = [self.action_to_claim.pid]
        return legals
