class BaseState:
    """Parent class für states"""

    def __init__(self, game_manager):
        self.game_manager = game_manager

    def update(self, dt, mouse_pos):
        pass

    def draw(self, screen):
        raise NotImplementedError("draw() muss in State-Klassen implementiert werden")

    def on_mouse_down(self, pos, button):
        pass

    def on_key_down(self, key, mod=0):
        pass