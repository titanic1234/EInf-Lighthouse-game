# communication.py

import threading
import time
import requests
from game.theme import theme_manager
import game.multiplayer.multiplayer_config as mconfig



def _check_connection_loop():
    """Im Thread laufende Loop zum testen der Serververbindung. Kann teils abgeschaltet werden mit mconfig.CHECK_CONNECTION = False."""
    while True:
        if mconfig.CHECK_CONNECTION:
            try:
                response = requests.get(mconfig.MULTIPLAYER_SERVER_URL)
                mconfig.connection_status(status=True)
            except requests.exceptions.ConnectionError:
                mconfig.connection_status(status=False)

        time.sleep(mconfig.CHECK_CONNECTION_INTERVAL)


def _start_check_connection_thread():
    """Startet einen Thread zum testen der Serververbindung."""
    if mconfig.CHECK_CONNECTION_ACTIVE:
        return
    mconfig.check_connection(check=True)
    print("Starting connection check thread...")
    thread = threading.Thread(target=_check_connection_loop, daemon=True)
    thread.start()


def create_game():
    """Schicke eine create game request an den multiplayer Server und speichert den Gamecode und den Player-Token in mconfig."""
    response = requests.post(mconfig.MULTIPLAYER_SERVER_URL + "games", json={"theme": theme_manager.get_theme()})
    response = response.json()
    mconfig.change_vars(code=response["code"], player_token=response["player_token"], role=response["role"])


def join_game(code: str, name: str):
    """Schickt eine join game request an den multiplayer Server mit dem Gamecode aus mconfig und speichert den Player-Token in mconfig. Setzt außerdem das Theme = theme vom host."""
    response = requests.post(mconfig.MULTIPLAYER_SERVER_URL + "games/join", json={"code": code, "name": name})
    if 400 <= response.status_code <= 404:
        return response.status_code
    response = response.json()
    theme_manager.set_theme(response["theme"])
    mconfig.change_vars(code=code, player_token=response["player_token"], role=response["role"], name=name)
    return None