import requests
import json

from game.multiplayer.schemas import *
from game.multiplayer.models import *
from game.config import MULTIPLAYER_SERVER_URL



def createGame(payload: CreateGame):

    response = requests.post(MULTIPLAYER_SERVER_URL + "games", json=payload.model_dump())
    print(response.json())