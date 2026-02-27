import threading
import time
import requests
import websocket  # pip install websocket-client
import json
from queue import Queue, Empty

from game.multiplayer.schemas import *
from game.config import MULTIPLAYER_SERVER_URL
import game.config as config



def _check_connection_loop() -> bool:
    """Connects to the multiplayer server and returns True if successful, False otherwise."""
    while config.CHECK_CONNECTION:
        try:
            response = requests.get(MULTIPLAYER_SERVER_URL)
            print(response.json())
            config.connection_status(status=True)
        except requests.exceptions.ConnectionError:
            config.connection_status(status=False)

        time.sleep(config.CHECK_CONNECTION_INTERVAL)


def _start_check_connection_thread():
    """Starts a thread to check the connection status with the multiplayer server."""
    if config.CHECK_CONNECTION_ACTIVE:
        return
    config.check_connection(check=True)
    print("Starting connection check thread...")
    thread = threading.Thread(target=_check_connection_loop, daemon=True)
    thread.start()



def create_game(payload: CreateGame):
    """Creates a new game on the multiplayer server."""
    response = requests.post(MULTIPLAYER_SERVER_URL + "games", json=payload.model_dump())
    print(response.json())