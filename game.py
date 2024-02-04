from typing import List
from random import shuffle
from .board import Board
from .player import Player
from .manager import Manager
from .game_settings import GameSettings
from .event_types import Event


class Game:
    def __init__(self, manager: Manager, players: List[Player]):
        settings = GameSettings.get_settings(
            len(players), is_rebalanced=len(players) in (6, 7, 9)
        )
        self.board = Board(settings, players)
        self.board.shuffle_callback = self.on_shuffle
        self.manager = manager

    def run_game(self):
        self.board.setup_new_game()
        self.broadcast("start")

    def turn(self):
        self.board.set_next_president()

    def inform_fascists(self):
        fascists = [player for player in self.board.players if player.is_fascist_team]

        for fascist in fascists:
            if fascist.role != "hitler" or self.board.settings.hitler_knows_fascists:
                self.personal_event(
                    fascist,
                    event_type=Event.ALL_ROLE_CALLS,
                    all_roles={
                        player: player.role.role for player in self.state.players
                    },
                )

    def personal_event(self, player: Player, event_type: Event, **kwargs):
        player.personal_event(event_type, **kwargs)
        self.manager.personal_event(event_type, player=player, **kwargs)

    def broadcast(self, event_type: Event, **kwargs):
        for player in self.state.players:
            player.inform_event(event_type, **kwargs)
        self.manager.inform_event(event_type, **kwargs)

    def on_shuffle(self):
        self.broadcast(
            "deck_shuffle",
            num_lib=self.board.policies.count("liberal"),
            num_fasc=self.board.policies.count("fascist"),
        )

    def nominate_chancellor(self):
        chancellor: Player = self.board.president.perform_action(Event.NOMINATION)
        assert (
            chancellor != self.board.president
            and chancellor not in self.board.term_blocked
            and not chancellor.is_dead
        )
        self.broadcast(Event.NOMINATION, pres=self.board.president, chanc=chancellor)
        self.board.nomination(chancellor)

    def voting(self):
        self.board.on_vote()
        player_votes = {}
        for player in self.board.players:
            if not player.is_dead:
                vote = player.perform_action(Event.PERSONAL_VOTE)
                player_votes[player] = vote
                self.personal_event(player, Event.PERSONAL_VOTE, vote=vote)
        self.broadcast(Event.VOTES, votes=player_votes)
        vote_list = list(player_votes.values())
        return vote_list.count("ja") > vote_list.count("nein")

    def vote_failed(self):
        self.broadcast(
            Event.ELECTION_FAIL,
            num_fails=self.board.failed_election_tracker + 1,
            max_fails=self.board.settings.election_tracker_size,
        )
        if self.board.vote_failed():
            self.broadcast(Event.CHAOS_POLICY)
            enacted_policy = self.board.draw_policy(1)[0]
            self.broadcast(
                Event.ENACTED,
                policy=enacted_policy,
                num_enacted=self.board.tracks[enacted_policy] + 1,
                maximum=self.board.settings.track_len[enacted_policy],
            )
            self.board.enact_policy(enacted_policy)

    def vote_passed(self):
        self.board.vote_success()
        pres_draw = self.board.draw_policy(3)
        self.personal_event(self.board.president, Event.DRAW, hand=pres_draw)
        (take, discard) = self.board.president.perform_action(
            Event.DISCARD, hand=pres_draw
        )
        self.board.discards.append(discard)
        self.personal_event(self.board.president, Event.DISCARD, dropped_card=discard)
        self.personal_event(
            self.board.chancellor, Event.GET_CARD, hand=take, pres=self.board.president
        )
        (enact, discard) = self.board.chancellor.perform_action(
            Event.PLAY_CARD, hand=take
        )
        self.personal_event(self.board.chancellor, Event.PLAY_CARD, card=enact)
        self.board.discards.append(discard)
