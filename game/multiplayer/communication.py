import threading
import time
import requests
import websocket  # pip install websocket-client
import json
from queue import Queue, Empty

from game.multiplayer.schemas import *
from game.multiplayer.multiplayer_config import MULTIPLAYER_SERVER_URL
import game.multiplayer.multiplayer_config as mconfig
import game.config as config


def _check_connection_loop():
    """Connects to the multiplayer server and returns True if successful, False otherwise."""
    while True:
        if mconfig.CHECK_CONNECTION:
            try:
                response = requests.get(mconfig.MULTIPLAYER_SERVER_URL)
                mconfig.connection_status(status=True)
            except requests.exceptions.ConnectionError:
                mconfig.connection_status(status=False)

        time.sleep(mconfig.CHECK_CONNECTION_INTERVAL)


def _start_check_connection_thread():
    """Starts a thread to check the connection status with the multiplayer server."""
    if mconfig.CHECK_CONNECTION_ACTIVE:
        return
    mconfig.check_connection(check=True)
    print("Starting connection check thread...")
    thread = threading.Thread(target=_check_connection_loop, daemon=True)
    thread.start()


def create_game():
    """Creates a new game on the multiplayer server."""
    response = requests.post(mconfig.MULTIPLAYER_SERVER_URL + "games")
    response = response.json()
    mconfig.change_vars(code=response["code"], player_token=response["player_token"], role=response["role"])


def join_game(code: str, name: str):
    """Joins an existing game on the multiplayer server."""
    response = requests.post(mconfig.MULTIPLAYER_SERVER_URL + "games/join/", json={"code": code, "name": name})
    if 400 <= response.status_code <= 404:
        return response.status_code
    response = response.json()
    print(response)
    print(response["player_token"])
    mconfig.change_vars(code=code, player_token=response["player_token"], role=response["role"])
    return None