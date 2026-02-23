"""
Game-Over-State
Zeigt Gewinner und Optionen an
"""

from pygame import Rect
from game.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_BLACK, COLOR_BLUE, COLOR_GREEN, COLOR_RED,
    BUTTON_WIDTH, BUTTON_HEIGHT,
    STATE_MENU, STATE_PLACEMENT
)
from game.states.base_state import BaseState
from game.ui.buttons import FlatButton


class GameOverState(BaseState):
    """Game-Over-Screen"""

    def __init__(self, game_manager):
        """
        Initialisiert den Game-Over-Screen

        Args:
            game_manager: Referenz zum GameManager
        """
        super().__init__(game_manager)
        self.winner = game_manager.winner
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):
        """Erstellt die Buttons"""
        center_x = WINDOW_WIDTH // 2
        start_y = WINDOW_HEIGHT // 2 + 50

        # "Neues Spiel" Button
        self.buttons.append(
            FlatButton(center_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT,
                  "Neues Spiel", self._new_game)
        )

        # "Hauptmenü" Button
        self.buttons.append(
            FlatButton(center_x, start_y + 80, BUTTON_WIDTH, BUTTON_HEIGHT,
                  "Hauptmenü", self._main_menu)
        )

        # "Beenden" Button
        self.buttons.append(
            FlatButton(center_x, start_y + 160, BUTTON_WIDTH, BUTTON_HEIGHT,
                  "Beenden", self._quit_game)
        )

    def _new_game(self):
        """Startet ein neues Spiel"""
        self.game_manager.reset_game()
        self.game_manager.change_state(STATE_PLACEMENT)

    def _main_menu(self):
        """Zurück zum Hauptmenü"""
        self.game_manager.reset_game()
        self.game_manager.change_state(STATE_MENU)

    def _quit_game(self):
        """Beendet das Spiel"""
        import sys
        sys.exit()

    def update(self, dt, mouse_pos):
        """
        Aktualisiert den Game-Over-Screen

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
        if button == 1:
            for btn in self.buttons:
                if btn.hovered:
                    btn.click()
                    break

    def draw(self, screen):
        """
        Zeichnet den Game-Over-Screen

        Args:
            screen: pgzero Screen-Objekt
        """
        screen.clear()
        screen.fill(COLOR_BLACK)

        # Titel
        title = "Du hast gewonnen!" if self.winner == "Player" else "Du hast verloren!"
        title_color = COLOR_GREEN if self.winner == "Player" else COLOR_RED

        screen.draw.text(title, center=(WINDOW_WIDTH // 2, 150),
                        fontsize=56, color=title_color)

        # Untertitel
        if self.winner == "Player":
            subtitle = "Alle gegnerischen Schiffe wurden versenkt!"
            subtitle_color = COLOR_GREEN
        else:
            subtitle = "Alle deine Schiffe wurden versenkt!"
            subtitle_color = COLOR_RED

        screen.draw.text(subtitle, center=(WINDOW_WIDTH // 2, 220),
                        fontsize=28, color=subtitle_color)

        # Buttons
        for button in self.buttons:
            button.draw(screen)

        # Dekorative Elemente
        if self.winner == "Player":
            # Sieges-Nachricht
            screen.draw.text("⚓ SIEG! ⚓", center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50),
                           fontsize=32, color=COLOR_BLUE)
        else:
            # Niederlagen-Nachricht
            screen.draw.text("☠ NIEDERLAGE ☠", center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50),
                           fontsize=32, color=COLOR_RED)
