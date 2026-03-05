# game_over.py
"""
Game-Over-State
"""

import game.config as config
from game.states.base_state import BaseState
from game.graphics import draw_text, draw_gradient_background, GlowButton
from game.theme import theme_manager


class GameOverState(BaseState):
    """Game-Over-Screen"""

    def __init__(self, game_manager):

        super().__init__(game_manager)
        self.winner = game_manager.winner
        self.buttons = []
        self._create_buttons()


    # ------------------------------
    # Create Buttons
    # ------------------------------
    def _create_buttons(self):

        center_x = config.WINDOW_WIDTH // 2
        start_y = config.WINDOW_HEIGHT // 2 + 50

        button_specs = [
            ("NEUES SPIEL", self._new_game),
            ("ZUM MENÜ", self._main_menu),
            ("BEENDEN", self._quit_game),
        ]

        for index, (label, action) in enumerate(button_specs):
            self.buttons.append(
                GlowButton(
                    center_x,
                    start_y + config.GAME_OVER_BUTTON_SPACING * index,
                    config.GAME_OVER_BUTTON_WIDTH,
                    config.GAME_OVER_BUTTON_HEIGHT,
                    label,
                    action,
                )
            )


    # ------------------------------
    # Button clicked
    # ------------------------------
    def _new_game(self):
        try:
            multiplayer = self.game_manager.ws.is_connected()
            self.game_manager.ws.stop()
            self.game_manager.reset_game()
            if multiplayer:
                self.game_manager.change_state(config.STATE_MULTIPLAYER_MENU)
        except Exception:
            self.game_manager.reset_game()
            self.game_manager.change_state(config.STATE_PLACEMENT)

    def _main_menu(self):
        try:
            self.game_manager.ws.stop()
        except Exception:
            pass
        self.game_manager.reset_game()
        self.game_manager.change_state(config.STATE_MENU)

    def _quit_game(self):
        import sys
        sys.exit()


    # ------------------------------
    # Events
    # ------------------------------
    def update(self, dt, mouse_pos):
        mouse_x, mouse_y = mouse_pos
        for button in self.buttons:
            button.update(dt, mouse_x, mouse_y)

    def on_mouse_down(self, pos, button):
        if button == 1:
            for btn in self.buttons:
                if btn.hovered:
                    btn.click()
                    break


    # ------------------------------
    # Draw
    # ------------------------------
    def draw(self, screen):
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