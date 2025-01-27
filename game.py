import json
from typing import List
from uuid import uuid4

from ykutil import Statlogger

from sh_game.board import Board
from sh_game.game_settings import GameSettings
from sh_game.log_util import log
from sh_game.manager import Manager
from sh_game.player import Player
from sh_game.types.event_types import PRESIDENT_POWERS, Event
from sh_game.types.game_end_types import GameEnd


class Game:
    def __init__(
        self,
        manager: Manager,
        players: List[Player],
        time_logging_file=None,
        verbose=False,
    ):
        settings = GameSettings.get_settings(
            len(players), is_rebalanced=len(players) in (6, 7, 9)
        )
        self.board = Board(settings, players)
        self.board.shuffle_callback = self.on_shuffle
        self.manager = manager
        self.manager.set_game(self)
        self.game_result: Event = None
        self.game_end_type: GameEnd = None
        self.max_repeated_chat_messages = 40
        self.chat_streak = 0
        self.game_id = None
        self.statlogger = Statlogger()
        self.time_logging_file = time_logging_file
        self.verbose = verbose

    def run_game(self):
        self.statlogger.start_timer("run_game")
        self.statlogger.start_timer("setup")
        self.game_id = str(uuid4())
        self.chat_streak = 0
        self.game_result = None
        self.game_end_type = None
        self.board.setup_new_game()
        self.manager.reset()
        self.broadcast(
            Event.GAME_SETTINGS,
            num_players=len(self.board.players),
            disable_rebalance="No",
            remake="No",
        )
        self.inform_roles()
        self.broadcast(Event.START)

        self.statlogger.stop_timer("setup")
        self.chat_phase()  # TODO: Make this work
        self.nominate_chancellor()
        self.board.phase = 1
        while 1:
            self.chat_phase()
            vote_success = self.voting()
            if vote_success:
                self.vote_passed()
            else:
                self.vote_failed()
            if self.game_result is not None:
                break
            self.chat_phase()
            if self.game_result is not None:
                break
            self.board.set_next_president()
            self.board.round_number += 1
            self.nominate_chancellor()

        self.broadcast(self.game_result, how=self.game_end_type)
        self.statlogger.stop_timer("run_game", average=True, summed=True)
        if self.verbose:
            print(self.statlogger.stats)
        if self.time_logging_file is not None:
            with open(self.time_logging_file, "w") as f:
                json.dump(self.statlogger.stats, f)

    def chat_phase(self):
        self.statlogger.start_timer("chat_phase")
        last_p = (
            self.board.ex_president if self.board.phase == 1 else self.board.president
        )
        last_c = (
            self.board.ex_chancellor if self.board.phase == 1 else self.board.chancellor
        )
        move_on_event = Event.VOTES if self.board.phase == 1 else Event.NOMINATION
        while 1:
            self.statlogger.start_timer("get_next_action")
            event, pid = self.manager.get_next_action()
            self.statlogger.stop_timer("get_next_action", average=True, summed=True)
            self.statlogger.start_timer("chat_phase_act")
            player = self.board.players[pid]
            if event == move_on_event or (
                event == Event.MESSAGE
                and self.chat_streak >= self.max_repeated_chat_messages
            ):
                self.chat_streak = 0
                break
            elif event == Event.MESSAGE:
                self.chat_streak += 1
                msg, hint = player.perform_action(Event.MESSAGE)
                if msg is None:
                    log(f"Player {player.pid} refused to send a message", level="info")
                else:
                    self.broadcast(Event.MESSAGE, player=player, message=msg, hint=hint)
            elif self.board.phase > 0:
                if event == Event.CHANCELLOR_CLAIM:
                    assert last_c is player
                    assert not self.board.play_card_claimed
                    claim, _hint = player.perform_action(Event.CHANCELLOR_CLAIM)
                    self.broadcast(Event.CHANCELLOR_CLAIM, hand=claim, player=player)
                    self.board.play_card_claimed = True
                elif event == Event.PRESIDENT_CLAIM:
                    assert last_p is player
                    assert not self.board.discard_claimed
                    claim, _hint = player.perform_action(Event.PRESIDENT_CLAIM)
                    self.broadcast(Event.PRESIDENT_CLAIM, hand=claim, player=player)
                    self.board.discard_claimed = True
                elif event in (Event.INVESTIGATION_CLAIM, Event.PEEK_CLAIM):
                    assert last_p is player
                    assert not self.board.action_claimed
                    assert self.board.action_done
                    claim, _hint = player.perform_action(
                        event, inved=self.board.inv_target
                    )
                    if event == Event.INVESTIGATION_CLAIM:
                        assert self.board.action_type == Event.INVESTIGATION_ACTION
                        self.broadcast(
                            event,
                            pres=player,
                            inved=self.board.inv_target,
                            role=claim,
                        )
                    else:
                        assert self.board.action_type == Event.PEEK_MESSAGE
                        self.broadcast(event, hand=claim, player=player)
                    self.board.action_claimed = True
                elif (
                    self.board.phase == 2
                    and not self.board.action_done
                    and self.board.action_type in PRESIDENT_POWERS
                ):
                    assert self.board.action_type == event
                    assert last_p is player
                    if event == Event.INVESTIGATION_ACTION:
                        inv: Player
                        inv, _hint = player.perform_action(Event.INVESTIGATION_ACTION)
                        assert not inv.is_dead and inv is not player
                        self.board.inv_target = inv
                        self.broadcast(
                            Event.INVESTIGATION_ACTION, pres=player, inved=inv
                        )
                        self.personal_event(
                            player,
                            Event.INVESTIGATION_RESULT,
                            inv_pid=inv.pid,
                            inv_role=inv.party_membership,
                        )
                    elif event == Event.EXECUTE_ACTION:
                        kill: Player
                        kill, _hint = player.perform_action(Event.EXECUTE_ACTION)
                        assert not kill.is_dead and kill is not player
                        self.broadcast(Event.EXECUTE_ACTION, pres=player, targ=kill)
                        kill.is_dead = True
                        if kill.role == "hitler":
                            self.game_result = Event.LIBERAL_WIN
                            self.game_end_type = GameEnd.HITLER_DEAD
                            return
                    elif event == Event.SPECIAL_ELECT_ACTION:
                        chosen: Player
                        chosen, _hint = player.perform_action(
                            Event.SPECIAL_ELECT_ACTION
                        )
                        assert not chosen.is_dead and chosen is not player
                        self.broadcast(
                            Event.SPECIAL_ELECT_ACTION, old_pres=player, new_pres=chosen
                        )
                        self.board.special_elect_choice = chosen
                    self.board.action_done = True
            else:
                raise ValueError(
                    f"Manager Error: Cannot perform {event} in message phase {self.board.phase}"
                )

            self.statlogger.stop_timer("chat_phase_act", average=True, summed=True)
        self.statlogger.stop_timer("chat_phase", average=True, summed=True)

    def inform_roles(self):
        for player in self.board.players:
            self.personal_event(player, Event.PERSONAL_ROLE_CALL)
        fascists = [player for player in self.board.players if player.is_fascist_team]

        for fascist in fascists:
            if fascist.role != "hitler" or self.board.settings.hitler_knows_fascists:
                self.personal_event(
                    fascist,
                    event_type=Event.ALL_ROLE_CALLS,
                    all_roles={
                        player.pid: player.role for player in self.board.players
                    },
                )

    def personal_event(self, player: Player, event_type: Event, **kwargs):
        player.personal_event(event_type, **kwargs)
        self.manager.personal_event(event_type, player=player, **kwargs)

    def broadcast(self, event_type: Event, **kwargs):
        for player in self.board.players:
            player.inform_event(event_type, **kwargs)
        self.manager.inform_event(event_type, **kwargs)

    def on_shuffle(self):
        self.broadcast(
            Event.DECK_SHUFFLE,
            num_lib=self.board.policies.count("liberal"),
            num_fasc=self.board.policies.count("fascist"),
        )

    def nominate_chancellor(self):
        self.statlogger.start_timer("nominate_chancellor")
        chancellor: Player
        chancellor, _hint = self.board.president.perform_action(Event.NOMINATION)
        assert (
            chancellor != self.board.president
            and chancellor not in self.board.term_blocked
            and not chancellor.is_dead
        )
        self.broadcast(Event.NOMINATION, pres=self.board.president, chanc=chancellor)
        self.board.nomination(chancellor)
        self.statlogger.stop_timer("nominate_chancellor", average=True, summed=True)

    def voting(self):
        self.statlogger.start_timer("voting")
        self.board.on_vote()
        player_votes = {}
        for player in self.board.players:
            if not player.is_dead:
                vote, _hint = player.perform_action(Event.PERSONAL_VOTE)
                assert vote in ("ja", "nein")
                player_votes[player] = vote
                self.personal_event(player, Event.PERSONAL_VOTE, vote=vote)
        self.broadcast(Event.VOTES, votes=player_votes)
        vote_list = list(player_votes.values())
        self.statlogger.stop_timer("voting", average=True, summed=True)
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
            self.game_result = self.board.enact_policy(enacted_policy)
            if self.game_result is not None:
                self.game_end_type = (
                    GameEnd.LIBERAL_CARDS
                    if self.game_result is Event.LIBERAL_WIN
                    else GameEnd.FASCIST_CARDS
                )

    def vote_passed(self):
        self.statlogger.start_timer("government")
        if self.board.chancellor.role == "hitler" and self.board.fascist_track >= 3:
            self.game_end_type = GameEnd.HITLER_CHANCELLOR
            self.game_result = Event.FASCIST_WIN
            return
        self.board.vote_success()
        pres_draw = self.board.draw_policy(3)
        self.personal_event(self.board.president, Event.DRAW, hand=pres_draw)
        (take, discard), _hint = self.board.president.perform_action(
            Event.DISCARD, hand=pres_draw
        )
        self.board.discards.append(discard)
        self.personal_event(self.board.president, Event.DISCARD, dropped_card=discard)
        self.personal_event(
            self.board.chancellor, Event.GET_CARD, hand=take, pres=self.board.president
        )
        (enact, discard), _hint = self.board.chancellor.perform_action(
            Event.PLAY_CARD, hand=take
        )
        self.personal_event(self.board.chancellor, Event.PLAY_CARD, card=enact)
        self.board.discards.append(discard)

        if self.board.can_veto:
            chanc_veto, _hint = self.board.chancellor.perform_action(
                Event.CHANCELLOR_VETO
            )
            self.broadcast(
                Event.CHANCELLOR_VETO, veto=chanc_veto, player=self.board.chancellor
            )
            if chanc_veto:
                pres_veto, _hint = self.board.president.perform_action(
                    Event.PRESIDENT_VETO
                )
                self.broadcast(
                    Event.PRESIDENT_VETO, veto=pres_veto, player=self.board.president
                )
                if pres_veto:
                    self.board.discards.append(enact)
                    self.vote_failed()
                    return

        self.broadcast(
            Event.ENACTED,
            policy=enact,
            num_enacted=self.board.tracks[enact] + 1,
            maximum=self.board.settings.track_len[enact],
        )
        self.game_result = self.board.enact_policy(enact)
        self.statlogger.stop_timer("government", average=True, summed=True)
        if self.game_result is not None:
            if self.game_result is Event.FASCIST_WIN:
                self.game_end_type = GameEnd.FASCIST_CARDS
            else:
                self.game_end_type = GameEnd.LIBERAL_CARDS
            return
        if enact == "fascist":
            self.introduce_presidential_power()

    def introduce_presidential_power(self):
        self.statlogger.start_timer("pres_power")
        pres_power = self.board.settings.fascist_track[self.board.fascist_track - 1]
        assert self.board.action_type is None
        assert not self.board.action_done
        assert not self.board.action_claimed

        if pres_power is not None:
            if pres_power == "inv":
                self.broadcast(Event.INVESTIGATION_MESSAGE)
                self.board.action_type = Event.INVESTIGATION_ACTION
            elif pres_power == "peek":
                self.broadcast(Event.PEEK_MESSAGE)
                peeked = self.board.peek_policy(3)
                self.personal_event(
                    self.board.president, Event.PEEK_PERSONAL, peek=peeked
                )
                self.board.action_type = Event.PEEK_MESSAGE
                self.board.action_done = True
            elif pres_power == "execute":
                self.broadcast(Event.EXECUTE_MESSAGE)
                self.board.action_type = Event.EXECUTE_ACTION
            elif pres_power == "special_elect":
                self.broadcast(Event.SPECIAL_ELECT_MESSAGE)
                self.board.action_type = Event.SPECIAL_ELECT_ACTION
            else:
                raise ValueError("Invalid president power", pres_power)
        self.statlogger.stop_timer("pres_power", average=True, summed=True)
