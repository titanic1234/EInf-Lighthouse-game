"""
Game-Manager
Verwaltet alle Spielzustände (States) und koordiniert das Spiel
"""

from game.config import STATE_MENU, STATE_PLACEMENT, STATE_BATTLE, STATE_GAME_OVER, STATE_MULTIPLAYER_PLACEMENT
from game.config import (
    STATE_MULTIPLAYER_MENU,
    STATE_MULTIPLAYER_WAITING,
    STATE_MULTIPLAYER_GAME,
    STATE_MULTIPLAYER_CREATE,
    STATE_MULTIPLAYER_JOIN
)
from game.states.menu import MenuState
from game.states.placement import PlacementState
from game.states.battle import BattleState
from game.states.game_over import GameOverState
from game.states.multiplayer import MultiplayerState
from game.states.create_game import CreateGameState
from game.states.join_game import JoinGameState
from game.states.multiplayer_placement import MultiplayerPlacementState


class GameManager:
    """Zentrale Spielverwaltung mit State-Pattern"""

    STATE_MAP = {
        STATE_MENU: MenuState,
        STATE_PLACEMENT: PlacementState,
        STATE_BATTLE: BattleState,
        STATE_GAME_OVER: GameOverState,
        STATE_MULTIPLAYER_MENU: MultiplayerState,
        STATE_MULTIPLAYER_CREATE: CreateGameState,
        STATE_MULTIPLAYER_JOIN: JoinGameState,
        STATE_MULTIPLAYER_PLACEMENT: MultiplayerPlacementState,


    }

    def __init__(self):
        """Initialisiert den Game-Manager"""
        self.current_state_name = STATE_MENU
        self.current_state = None

        # Gemeinsame Spieldaten
        self.player_board = None
        self.winner = None
        self.shots_fired = 0
        self.shots_hit = 0
        self.time_elapsed = 0.0
        self.ai_difficulty = "normal"

        # Initialer State
        self.change_state(STATE_MENU)

    def change_state(self, new_state_name):
        """
        Wechselt zu einem neuen Spielzustand

        Args:
            new_state_name: Name des neuen States (aus config.py)
        """
        self.current_state_name = new_state_name

        state_class = self.STATE_MAP.get(new_state_name)
        if not state_class:
            raise ValueError(f"Unbekannter State: {new_state_name}")

        self.current_state = state_class(self)

    def reset_game(self):
        """Setzt das Spiel zurück"""
        self.player_board = None
        self.winner = None
        self.shots_fired = 0
        self.shots_hit = 0

    def update(self, dt, mouse_pos):
        """
        Aktualisiert den aktuellen State

        Args:
            dt: Delta-Zeit
            mouse_pos: Mausposition (x, y)
        """
        self.time_elapsed += dt
        if self.current_state:
            self.current_state.update(dt, mouse_pos)

    def draw(self, screen):
        """
        Zeichnet den aktuellen State

        Args:
            screen: pgzero Screen-Objekt
        """
        if self.current_state:
            self.current_state.draw(screen)

    def on_mouse_down(self, pos, button):
        """
        Delegiert Mausklicks an den aktuellen State

        Args:
            pos: Position (x, y)
            button: Maustaste (1=links, 2=mitte, 3=rechts)
        """
        if self.current_state:
            self.current_state.on_mouse_down(pos, button)

    def on_key_down(self, key, mod=0):
        """
        Delegiert Tasteneingaben an den aktuellen State

        Args:
            key: Taste (pgzero key)
            mod: keymod (pgzero mod)
        """
        if self.current_state:
            self.current_state.on_key_down(key, mod)
