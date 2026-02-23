"""
Hauptmenü-State
"""

from pygame import Rect
from game.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, TITLE,
    COLOR_WHITE, COLOR_BLACK, COLOR_BLUE,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_COLOR, BUTTON_HOVER_COLOR,
    STATE_PLACEMENT
)


class Button:
    """Einfache Button-Klasse"""

    def __init__(self, x, y, width, height, text, action):
        """
        Initialisiert einen Button

        Args:
            x, y: Position (zentriert)
            width, height: Größe
            text: Button-Text
            action: Callback-Funktion
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.action = action
        self.hovered = False

    def is_hovered(self, mouse_x, mouse_y):
        """Prüft ob Maus über Button ist"""
        return (self.x - self.width // 2 <= mouse_x <= self.x + self.width // 2 and
                self.y - self.height // 2 <= mouse_y <= self.y + self.height // 2)

    def update(self, mouse_x, mouse_y):
        """Aktualisiert Hover-Status"""
        self.hovered = self.is_hovered(mouse_x, mouse_y)

    def draw(self, screen):
        """Zeichnet den Button"""
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR

        # Button-Rechteck
        rect = Rect(self.x - self.width // 2, self.y - self.height // 2,
                    self.width, self.height)
        screen.draw.filled_rect(rect, color)
        screen.draw.rect(rect, COLOR_WHITE)

        # Text
        screen.draw.text(self.text, center=(self.x, self.y),
                        fontsize=32, color=COLOR_WHITE)

    def click(self):
        """Führt die Button-Aktion aus"""
        if self.action:
            self.action()


class MenuState:
    """Hauptmenü-State"""

    def __init__(self, game_manager):
        """
        Initialisiert das Menü

        Args:
            game_manager: Referenz zum GameManager
        """
        self.game_manager = game_manager
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):
        """Erstellt die Menü-Buttons"""
        center_x = WINDOW_WIDTH // 2
        start_y = WINDOW_HEIGHT // 2

        # "Neues Spiel" Button
        self.buttons.append(
            Button(center_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT,
                  "Neues Spiel", self._start_game)
        )

        # "Beenden" Button
        self.buttons.append(
            Button(center_x, start_y + 80, BUTTON_WIDTH, BUTTON_HEIGHT,
                  "Beenden", self._quit_game)
        )

    def _start_game(self):
        """Startet ein neues Spiel"""
        self.game_manager.change_state(STATE_PLACEMENT)

    def _quit_game(self):
        """Beendet das Spiel"""
        import sys
        sys.exit()

    def update(self, dt, mouse_pos):
        """
        Aktualisiert das Menü

        Args:
            dt: Delta-Zeit
            mouse_pos: Tuple (x, y) der Mausposition
        """
        mouse_x, mouse_y = mouse_pos
        for button in self.buttons:
            button.update(mouse_x, mouse_y)

    def on_mouse_down(self, pos, button):
        """
        Behandelt Mausklicks

        Args:
            pos: Tuple (x, y)
            button: Maustaste
        """
        if button == 1:  # Linke Maustaste
            for btn in self.buttons:
                if btn.hovered:
                    btn.click()
                    break

    def draw(self, screen):
        """
        Zeichnet das Menü

        Args:
            screen: pgzero Screen-Objekt
        """
        screen.clear()
        screen.fill(COLOR_BLACK)

        # Titel
        screen.draw.text(TITLE, center=(WINDOW_WIDTH // 2, 150),
                        fontsize=64, color=COLOR_BLUE)

        # Untertitel
        screen.draw.text("Battleship", center=(WINDOW_WIDTH // 2, 220),
                        fontsize=32, color=COLOR_WHITE)

        # Buttons
        for button in self.buttons:
            button.draw(screen)

        # Steuerungshinweise
        screen.draw.text("Steuerung: Maus", center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50),
                        fontsize=20, color=COLOR_WHITE)
