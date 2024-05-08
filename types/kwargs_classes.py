from dataclasses import dataclass
from typing import Literal, NamedTuple, Optional

from sh_game.player import Player
from sh_game.types.event_types import Event
from sh_game.types.game_end_types import GameEnd

YN = Literal["yes", "no"]
JN = Literal["ja", "nein"]


KWARGS_CLASSES = {
    Event.PERSONAL_ROLE_CALL: NamedTuple("PersonalRoleCall", []),
    Event.ALL_ROLE_CALLS: NamedTuple(
        "AllRoleCalls", [("all_roles", dict[Player, str])]
    ),
    Event.PERSONAL_VOTE: NamedTuple("PersonalVote", [("vote", JN)]),
    Event.DRAW: NamedTuple("Draw", [("hand", list[str])]),
    Event.DISCARD: NamedTuple("Discard", [("dropped_card", str)]),
    Event.GET_CARD: NamedTuple("GetCard", [("hand", list[str]), ("pres", Player)]),
    Event.PLAY_CARD: NamedTuple("PlayCard", [("card", str)]),
    Event.PEEK_PERSONAL: NamedTuple("PeekPersonal", [("peek", str)]),
    Event.NOMINATION: NamedTuple("Nomination", [("pres", Player), ("chanc", Player)]),
    Event.VOTES: NamedTuple("Votes", [("votes", dict[Player, JN])]),
    Event.MESSAGE: NamedTuple("Message", [("player", Player), ("message", str)]),
    Event.ENACTED: NamedTuple(
        "Enacted", [("policy", str), ("num_enacted", int), ("maximum", int)]
    ),
    Event.ELECTION_FAIL: NamedTuple(
        "ElectionFail", [("num_fails", int), ("max_fails", int)]
    ),
    Event.PRESIDENT_CLAIM: NamedTuple(
        "PresidentClaim", [("hand", list[str]), ("player", Player)]
    ),
    Event.CHANCELLOR_CLAIM: NamedTuple(
        "ChancellorClaim", [("hand", list[str]), ("player", Player)]
    ),
    Event.INVESTIGATION_MESSAGE: NamedTuple("InvestigationMessage", []),
    Event.INVESTIGATION_ACTION: NamedTuple(
        "InvestigationAction", [("pres", Player), ("inved", Player)]
    ),
    Event.INVESTIGATION_CLAIM: NamedTuple(
        "InvestigationClaim", [("hand", list[str]), ("player", Player)]
    ),
    Event.INVESTIGATION_RESULT: NamedTuple(
        "InvestigationResult", [("inv_pid", int), ("inv_role", str)]
    ),
    Event.SPECIAL_ELECT_MESSAGE: NamedTuple("SpecialElectMessage", []),
    Event.SPECIAL_ELECT_ACTION: NamedTuple(
        "SpecialElectAction", [("old_pres", Player), ("new_pres", Player)]
    ),
    Event.CHAOS_POLICY: NamedTuple("ChaosPolicy", []),
    Event.CHANCELLOR_VETO: NamedTuple(
        "ChancellorVeto", [("veto", bool), ("player", Player)]
    ),
    Event.PRESIDENT_VETO: NamedTuple(
        "PresidentVeto", [("veto", bool), ("player", Player)]
    ),
    Event.PEEK_MESSAGE: NamedTuple("PeekMessage", []),
    Event.PEEK_CLAIM: NamedTuple(
        "PeekClaim", [("hand", list[str]), ("player", Player)]
    ),
    Event.EXECUTE_MESSAGE: NamedTuple("ExecuteMessage", []),
    Event.EXECUTE_ACTION: NamedTuple(
        "ExecuteAction", [("pres", Player), ("targ", Player)]
    ),
    Event.DECK_SHUFFLE: NamedTuple(
        "DeckShuffle", [("num_lib", int), ("num_fasc", int)]
    ),
    Event.START: NamedTuple("Start", []),
    Event.GAME_SETTINGS: NamedTuple(
        "GameSettings",
        [("num_players", int), ("disable_rebalance", YN), ("remake", YN)],
    ),
    Event.FASCIST_WIN: NamedTuple("FascistWin", [("how", GameEnd)]),
    Event.LIBERAL_WIN: NamedTuple("LiberalWin", [("how", GameEnd)]),
}


@dataclass
class KwargsDc:
    all_roles: Optional[dict[Player, str]]
    vote: Optional[JN]
    hand: Optional[list[str]]
    dropped_card: Optional[str]
    pres: Optional[Player]
    chanc: Optional[Player]
    card: Optional[str]
    peek: Optional[str]
    votes: Optional[dict[Player, JN]]
    player: Optional[Player]
    message: Optional[str]
    policy: Optional[str]
    num_enacted: Optional[int]
    maximum: Optional[int]
    num_fails: Optional[int]
    max_fails: Optional[int]
    inved: Optional[Player]
    inv_pid: Optional[int]
    inv_role: Optional[str]
    old_pres: Optional[Player]
    new_pres: Optional[Player]
    veto: Optional[bool]
    targ: Optional[Player]
    num_lib: Optional[int]
    num_fasc: Optional[int]
    num_players: Optional[int]
    disable_rebalance: Optional[YN]
    remake: Optional[YN]
    how: Optional[GameEnd]
