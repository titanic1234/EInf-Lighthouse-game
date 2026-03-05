# models.py

from dataclasses import dataclass, field # https://docs.python.org/3/library/dataclasses.html
from typing import Optional


BOARD_SIZE = 12


@dataclass
class PlayerState:
    token: str
    name: str
    ships: list[list[tuple[int, int]]] = field(default_factory=list)
    shots_received: set[tuple[int, int]] = field(default_factory=set)
    ready: bool = False


@dataclass
class GameRoom:
    code: str
    host: PlayerState
    guest: Optional[PlayerState] = None # So wie PlayerState | None = None
    phase: str = "waiting"   # waiting, setup, playing, finished
    turn: str = "host"       # host oder guest
    winner: Optional[str] = None