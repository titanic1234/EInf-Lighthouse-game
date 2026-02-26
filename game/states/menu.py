"""
Hauptmenue-State mit aufgewerteter UI
"""

import pygame
import game.config as config
from game.graphics import draw_gradient_background, GlowButton, draw_title_art
from game.theme import theme_manager
from game.states.base_state import BaseState
import game.theme as theme


class MenuState(BaseState):
    """Hauptmenue-State"""

    def __init__(self, game_manager):
        """
        Initialisiert das Menue

        Args:
            game_manager: Referenz zum GameManager
        """
        super().__init__(game_manager)
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):
        """Erstellt die Menue-Buttons"""
        center_x = config.WINDOW_WIDTH // 2
        start_y = config.MENU_BUTTON_Y
        theme = theme_manager.current
        self.toggle_text = ""
        if theme.name == "MODERN":
            self.toggle_text = "PIRATEN MODUS"
        else:
            self.toggle_text = "CLASSIC MODUS"

        # "Neues Spiel" Button
        self.buttons.append(
            GlowButton(
                center_x,
                start_y,
                config.MENU_BUTTON_WIDTH,
                config.MENU_BUTTON_HEIGHT,
                theme.text_start_btn,
                self._start_game,
            )
        )

        # "Theme" Button
        self.buttons.append(
            GlowButton(
                center_x,
                start_y + config.MENU_BUTTON_SPACING,
                config.MENU_BUTTON_WIDTH,
                config.MENU_BUTTON_HEIGHT,
                self.toggle_text, #Button Text
                self._toggle_theme,
            )
        )

        # "Beenden" Button
        self.buttons.append(
            GlowButton(
                center_x,
                start_y + config.MENU_BUTTON_SPACING * 2,
                config.MENU_BUTTON_WIDTH,
                config.MENU_BUTTON_HEIGHT,
                theme.text_quit_btn,
                self._quit_game,
            )
        )

    def _toggle_theme(self):
        theme_manager.toggle()
        # Rekonstruiere Buttons
        self.buttons = []
        self._create_buttons()

    def _start_game(self):
        """Startet ein neues Spiel"""
        self.game_manager.change_state(config.STATE_PLACEMENT)

    def _quit_game(self):
        """Beendet das Spiel"""
        import sys
        sys.exit()

    def update(self, dt, mouse_pos):
        """Aktualisiert das Menue"""
        mouse_x, mouse_y = mouse_pos
        for button in self.buttons:
            button.update(dt, mouse_x, mouse_y)

    def on_mouse_down(self, pos, button):
        """Behandelt Mausklicks"""
        if button == 1:  # Linke Maustaste
            for btn in self.buttons:
                if btn.hovered:
                    btn.click()
                    break

    def draw(self, screen):
        """Zeichnet das Menue"""
        theme = theme_manager.current
        # Premium Gradient Background
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

        # Schiff Artwork
        draw_title_art(screen)

        # Titel (Schatten + Glowing Text)
        title_font = pygame.font.Font(None, config.MENU_TITLE_FONT_SIZE)

        # Shadow
        shadow_surf = title_font.render(theme.text_title, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(config.WINDOW_WIDTH // 2, config.MENU_TITLE_Y + 4))
        screen.blit(shadow_surf, shadow_rect)

        # Main Title (Glowing)
        title_surf = title_font.render(theme.text_title, True, theme.color_text_primary)
        title_rect = title_surf.get_rect(center=(config.WINDOW_WIDTH // 2, config.MENU_TITLE_Y))
        screen.blit(title_surf, title_rect)

        # Untertitel
        sub_font = pygame.font.Font(None, config.MENU_SUBTITLE_FONT_SIZE)
        sub_surf = sub_font.render(theme.text_subtitle, True, theme.color_text_secondary)
        sub_rect = sub_surf.get_rect(center=(config.WINDOW_WIDTH // 2, config.MENU_SUBTITLE_Y))
        screen.blit(sub_surf, sub_rect)


        # Buttons
        for button in self.buttons:
            button.draw(screen)

        # Steuerungshinweise am unteren Rand
        info_font = pygame.font.Font(None, config.MENU_INFO_FONT_SIZE)
        info_surf = info_font.render("Steuerung: Maus", True, (100, 100, 120))
        info_rect = info_surf.get_rect(
            center=(config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT - config.MENU_INFO_MARGIN_BOTTOM)
        )
        screen.blit(info_surf, info_rect)