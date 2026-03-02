"""Button-Klassen."""

from pgzero.rect import Rect
from game.config import BUTTON_COLOR, BUTTON_HOVER_COLOR, COLOR_WHITE


class BaseButton:
    """Basisklasse für klickbare Buttons."""

    def __init__(self, x, y, width, height, text, action):
        self.x = x
        self.y = y
        self.rect = Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.action = action
        self.hovered = False

    def is_hovered(self, mouse_x, mouse_y):
        return self.rect.collidepoint(mouse_x, mouse_y)

    def update(self, *args):
        """Unterstützt update(mouse_x, mouse_y) oder update(dt, mouse_x, mouse_y)."""
        if len(args) == 2:
            mouse_x, mouse_y = args
        elif len(args) == 3:
            _, mouse_x, mouse_y = args
        else:
            raise ValueError("update erwartet (mouse_x, mouse_y) oder (dt, mouse_x, mouse_y)")

        self.hovered = self.is_hovered(mouse_x, mouse_y)

    def click(self):
        if self.action:
            self.action()

    def draw(self, target):
        raise NotImplementedError("draw() muss in Button-Klassen implementiert werden")


class FlatButton(BaseButton):
    """Einfacher Button für klassische pgzero Screens."""

    def draw(self, screen):
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
        screen.draw.filled_rect(Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height), color)
        screen.draw.rect(Rect(self.rect.x, self.rect.y, self.rect.width, self.rect.height), COLOR_WHITE)
        screen.draw.text(self.text, center=self.rect.center, fontsize=32, color=COLOR_WHITE)