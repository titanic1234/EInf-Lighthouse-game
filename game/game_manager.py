"""
Game-Manager
Verwaltet alle Spielzustände (States) und koordiniert das Spiel
"""

from game.config import STATE_MENU, STATE_PLACEMENT, STATE_BATTLE, STATE_GAME_OVER
from game.states.menu import MenuState
from game.states.placement import PlacementState
from game.states.battle import BattleState
from game.states.game_over import GameOverState


class GameManager:
    """Zentrale Spielverwaltung mit State-Pattern"""

    def __init__(self):
        """Initialisiert den Game-Manager"""
        self.current_state_name = STATE_MENU
        self.current_state = None

        # Gemeinsame Spieldaten
        self.player_board = None
        self.winner = None

        # Initialer State
        self.change_state(STATE_MENU)

    def change_state(self, new_state_name):
        """
        Wechselt zu einem neuen Spielzustand

        Args:
            new_state_name: Name des neuen States (aus config.py)
        """
        self.current_state_name = new_state_name

        # State-Factory
        if new_state_name == STATE_MENU:
            self.current_state = MenuState(self)
        elif new_state_name == STATE_PLACEMENT:
            self.current_state = PlacementState(self)
        elif new_state_name == STATE_BATTLE:
            self.current_state = BattleState(self)
        elif new_state_name == STATE_GAME_OVER:
            self.current_state = GameOverState(self)
        else:
            raise ValueError(f"Unbekannter State: {new_state_name}")

    def reset_game(self):
        """Setzt das Spiel zurück"""
        self.player_board = None
        self.winner = None

    def update(self, dt, mouse_pos):
        """
        Aktualisiert den aktuellen State

        Args:
            dt: Delta-Zeit
            mouse_pos: Mausposition (x, y)
        """
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
        if self.current_state and hasattr(self.current_state, 'on_mouse_down'):
            self.current_state.on_mouse_down(pos, button)

    def on_key_down(self, key):
        """
        Delegiert Tasteneingaben an den aktuellen State

        Args:
            key: Taste (pgzero key)
        """
        if self.current_state and hasattr(self.current_state, 'on_key_down'):
            self.current_state.on_key_down(key)
