# base_state.py

class BaseState:
    """Parent class für states"""

    def __init__(self, game_manager):
        self.game_manager = game_manager

    def update(self, dt, mouse_pos):
        """Wird pro Frame aufgerufen."""

    def draw(self, screen):
        """Zeichnet den State auf den Bildschirm."""
        raise NotImplementedError("draw() muss in State-Klassen implementiert werden")

    def on_mouse_down(self, pos, button):
        """Optionaler Mausklick-Handler."""

    def on_key_down(self, key, mod=0):
        """Optionaler Tastatur-Handler."""
