"""
Multiplayer Config
"""

MULTIPLAYER_SERVER_URL = "http://127.0.0.1:8000/"
CONNENCTION = False
CHECK_CONNECTION_INTERVAL = 5
CHECK_CONNECTION = True
CHECK_CONNECTION_ACTIVE = False



CODE: str | None = None
NAME: str | None = None
PLAYER_TOKEN: str | None = None
ROLE: str | None = None






def change_vars(code: str | None = CODE, name: str | None = NAME, player_token: str | None = PLAYER_TOKEN, role: str | None = ROLE):
    global CODE, NAME, PLAYER_TOKEN, ROLE
    CODE = code
    NAME = name
    PLAYER_TOKEN = player_token
    ROLE = role


def connection_status(status: bool):
    global CONNENCTION
    CONNENCTION = status


def check_connection(status: bool = CHECK_CONNECTION, check: bool = CHECK_CONNECTION_ACTIVE, interval: int = CHECK_CONNECTION_INTERVAL):
    global CHECK_CONNECTION, CHECK_CONNECTION_INTERVAL, CHECK_CONNECTION_ACTIVE
    CHECK_CONNECTION = status
    CHECK_CONNECTION_INTERVAL = interval
    CHECK_CONNECTION_ACTIVE = check