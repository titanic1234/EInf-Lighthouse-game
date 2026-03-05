# schemas.py

from pydantic import BaseModel # https://docs.pydantic.dev/latest/#pydantic-examples


class CreateGame(BaseModel):
    name: str


class JoinGame(BaseModel):
    name: str
    code: str
    player_token: str


class Game(BaseModel):
    name: str
    code: str
    stage: str = "waiting"
    role: str