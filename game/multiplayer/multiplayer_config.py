"""
Multiplayer Config
"""

MULTIPLAYER_SERVER_URL = "http://46.224.135.187:8000/"
MULTIPLAYER_WS_URL = "ws://46.224.135.187:8000/ws/"
CONNECTION = False
CHECK_CONNECTION_INTERVAL = 5
CHECK_CONNECTION = True
CHECK_CONNECTION_ACTIVE = False


GAME_STATE = None



CODE: str | None = None
NAME: str | None = None
PLAYER_TOKEN: str | None = None
ROLE: str | None = None

OPPONENT_NAME: str | None = None
READY: bool = False

WINNER: str | None = None





def change_vars(code: str | None = CODE, name: str | None = NAME, player_token: str | None = PLAYER_TOKEN, role: str | None = ROLE):
    global CODE, NAME, PLAYER_TOKEN, ROLE
    CODE = code
    NAME = name
    PLAYER_TOKEN = player_token
    ROLE = role


def connection_status(status: bool):
    global CONNECTION
    CONNECTION = status


def check_connection(status: bool = CHECK_CONNECTION, check: bool = CHECK_CONNECTION_ACTIVE, interval: int = CHECK_CONNECTION_INTERVAL):
    global CHECK_CONNECTION, CHECK_CONNECTION_INTERVAL, CHECK_CONNECTION_ACTIVE
    CHECK_CONNECTION = status
    CHECK_CONNECTION_INTERVAL = interval
    CHECK_CONNECTION_ACTIVE = check


def set_game(state: str = GAME_STATE, opponent_name: str | None = OPPONENT_NAME, ready: bool = READY, winner: str | None = WINNER):
    global GAME_STATE, OPPONENT_NAME, READY, WINNER
    GAME_STATE = state
    OPPONENT_NAME = opponent_name
    READY = ready
    WINNER = winner