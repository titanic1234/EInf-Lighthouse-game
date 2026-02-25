"""
Game-Over-State
Zeigt Gewinner und Optionen an
"""

from pygame import Rect
import game.config as config
from game.states.base_state import BaseState
from game.graphics import draw_text, draw_gradient_background, GlowButton
from game.theme import theme_manager


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
        center_x = config.WINDOW_WIDTH // 2
        start_y = config.WINDOW_HEIGHT // 2 + 50

        # "Neues Spiel" Button
        self.buttons.append(
            GlowButton(
                center_x,
                start_y,
                config.GAME_OVER_BUTTON_WIDTH,
                config.GAME_OVER_BUTTON_HEIGHT,
                "NEUES SPIEL",
                self._new_game,
            )
        )

        # "Hauptmenue" Button
        self.buttons.append(
            GlowButton(
                center_x,
                start_y + config.GAME_OVER_BUTTON_SPACING,
                config.GAME_OVER_BUTTON_WIDTH,
                config.GAME_OVER_BUTTON_HEIGHT,
                "ZUM MENÜ",
                self._main_menu,
            )
        )

        # "Beenden" Button
        self.buttons.append(
            GlowButton(
                center_x,
                start_y + config.GAME_OVER_BUTTON_SPACING * 2,
                config.GAME_OVER_BUTTON_WIDTH,
                config.GAME_OVER_BUTTON_HEIGHT,
                "BEENDEN",
                self._quit_game,
            )
        )

    def _new_game(self):
        """Startet ein neues Spiel"""
        self.game_manager.reset_game()
        self.game_manager.change_state(config.STATE_PLACEMENT)

    def _main_menu(self):
        """Zurueck zum Hauptmenue"""
        self.game_manager.reset_game()
        self.game_manager.change_state(config.STATE_MENU)

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
            button.update(dt, mouse_x, mouse_y)

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
        """
        theme = theme_manager.current
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

        # Titel
        title = "VICTORY!" if self.winner == "Player" else "DEFEAT!"
        title_color = theme.color_text_primary if self.winner == "Player" else theme.color_text_enemy

        draw_text(
            screen,
            title,
            config.WINDOW_WIDTH // 2,
            config.GAME_OVER_TITLE_Y,
            config.GAME_OVER_TITLE_FONT_SIZE,
            title_color,
            center=True,
        )

        # Untertitel
        if self.winner == "Player":
            subtitle = theme.text_game_over_win
            subtitle_color = theme.color_text_secondary
        else:
            subtitle = theme.text_game_over_lose
            subtitle_color = theme.color_text_enemy

        draw_text(
            screen,
            subtitle,
            config.WINDOW_WIDTH // 2,
            config.GAME_OVER_SUBTITLE_Y,
            config.GAME_OVER_SUBTITLE_FONT_SIZE,
            subtitle_color,
            center=True,
        )

        accuracy = 0
        if self.game_manager.shots_fired > 0:
            accuracy = int((self.game_manager.shots_hit / self.game_manager.shots_fired) * 100)

        stats_text = f"Accuracy: {accuracy}% ({self.game_manager.shots_hit}/{self.game_manager.shots_fired} hits)"
        draw_text(
            screen,
            stats_text,
            config.WINDOW_WIDTH // 2,
            config.GAME_OVER_STATS_Y,
            config.GAME_OVER_STATS_FONT_SIZE,
            theme.color_text_primary,
            center=True,
        )

        # Buttons
        for button in self.buttons:
            button.draw(screen)

        # Dekorative Elemente
        if self.winner == "Player":
            draw_text(
                screen,
                "OK",
                config.WINDOW_WIDTH // 2,
                config.WINDOW_HEIGHT - config.GAME_OVER_ICON_MARGIN_BOTTOM,
                config.GAME_OVER_ICON_FONT_SIZE,
                theme.color_text_secondary,
                center=True,
            )
        else:
            draw_text(
                screen,
                "SKULL",
                config.WINDOW_WIDTH // 2,
                config.WINDOW_HEIGHT - config.GAME_OVER_ICON_MARGIN_BOTTOM,
                config.GAME_OVER_ICON_FONT_SIZE,
                theme.color_text_enemy,
                center=True,
            )

    def on_resize(self, width, height):
        self.buttons = []
        self._create_buttons()