"""Secret Hitler game engine. Imports are LAZY (PEP 562): ``game`` pulls in
ykutil, whose package init loads torch / transformers (~16 s), while many
users (transcripts, constants, the contest monitor) only need the event types.
``from sh_game import Game`` still works, it just resolves on first use."""

import importlib

_LAZY_EXPORTS = {
    "Board": "board",
    "Event": "types.event_types",
    "Game": "game",
    "GameEnd": "types.game_end_types",
    "GameSettings": "game_settings",
    "INVERTED_EVENTS": "types.event_types",
    "KWARGS_CLASSES": "types.kwargs_classes",
    "KwargsDc": "types.kwargs_classes",
    "Manager": "manager",
    "Player": "player",
}


def __getattr__(name):
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    module = importlib.import_module("." + module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value  # cache, so the lookup happens once
    return value


def __dir__():
    return sorted(set(globals()) | set(_LAZY_EXPORTS))


__all__ = sorted(_LAZY_EXPORTS)
