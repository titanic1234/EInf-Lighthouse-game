"""
Multiplayer Config
"""

MULTIPLAYER_SERVER_URL = "http://127.0.0.1:8000/" #"http://46.224.135.187:8000/"
MULTIPLAYER_WS_URL = "ws://127.0.0.1:8000/ws/" #"ws://46.224.135.187:8000/ws/"
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




def change_vars(code=None, name=None, player_token=None, role=None):
    global CODE, NAME, PLAYER_TOKEN, ROLE
    if code is not None:
        CODE = code
    if name is not None:
        NAME = name
    if player_token is not None:
        PLAYER_TOKEN = player_token
    if role is not None:
        ROLE = role


def connection_status(status: bool):
    global CONNECTION
    CONNECTION = status


def check_connection(status=None, check=None, interval=None):
    global CHECK_CONNECTION, CHECK_CONNECTION_INTERVAL, CHECK_CONNECTION_ACTIVE
    if status is not None:
        CHECK_CONNECTION = status
    if interval is not None:
        CHECK_CONNECTION_INTERVAL = interval
    if check is not None:
        CHECK_CONNECTION_ACTIVE = check


def set_game(state=None, opponent_name=None, ready=None, winner=None):
    global GAME_STATE, OPPONENT_NAME, READY, WINNER
    if state is not None:
        GAME_STATE = state
    if opponent_name is not None:
        OPPONENT_NAME = opponent_name
    if ready is not None:
        READY = ready
    if winner is not None:
        WINNER = winner


def reset():
    global CODE, PLAYER_TOKEN, ROLE, OPPONENT_NAME, READY, WINNER, GAME_STATE
    CODE = None
    PLAYER_TOKEN = None
    ROLE = None
    OPPONENT_NAME = None
    READY = False
    WINNER = None
    GAME_STATE = None
