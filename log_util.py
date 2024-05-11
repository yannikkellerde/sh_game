import inspect
import logging
import os

from termcolor import colored

logger = logging.getLogger("log_util")
logger.setLevel(logging.INFO)
hl = logging.StreamHandler()
hl.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(hl)

level_map = {
    "WARN": logging.WARNING,
    "INFO": logging.INFO,
    "ERROR": logging.ERROR,
    "DEBUG": logging.DEBUG,
}


def log(*messages, level=logging.INFO):
    if type(level) == str:
        level = level_map[level.upper()]
    caller = inspect.stack()[1]
    msg = f'{os.path.basename(caller.filename)}:{caller.lineno} {" ".join(map(str, messages))}'
    if level == logging.ERROR:
        msg = colored(msg, "red")
    elif level == logging.WARNING:
        msg = colored(msg, "yellow")
    logger.log(level, msg)
