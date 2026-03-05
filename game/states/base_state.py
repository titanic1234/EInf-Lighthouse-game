class BaseState:
    """Parent class für states"""

    def __init__(self, game_manager):
        self.game_manager = game_manager

    def draw(self, screen):
        raise NotImplementedError("draw() muss in State-Klassen implementiert werden")
