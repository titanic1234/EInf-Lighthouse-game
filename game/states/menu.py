"""
Hauptmenue-State mit aufgewerteter UI
"""

import pygame
import game.config as config
from game.graphics import draw_gradient_background, GlowButton, draw_title_art
from game.theme import theme_manager
from game.states.base_state import BaseState
import game.multiplayer.multiplayer_config as mconfig


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
        current_theme = theme_manager.current
        self.toggle_text = ""
        self.difficulty_text = ""

        if current_theme.name == "MODERN":
            self.toggle_text = "PIRATEN MODUS"
        else:
            self.toggle_text = "CLASSIC MODUS"
        self._refresh_difficulty_text()

        main_button_width = 360
        secondary_button_width = 540
        column_gap = 30
        row_gap = 30
        row_one_y = start_y
        row_two_y = start_y + config.MENU_BUTTON_HEIGHT + row_gap

        total_main_width = main_button_width * 3 + column_gap * 2
        row_one_start = center_x - total_main_width // 2

        multiplayer_text, multiplayer_action = self._multiplayer_button_state()

        row_one_buttons = [
            (current_theme.text_start_btn, self._start_game),
            (multiplayer_text, multiplayer_action),
            (current_theme.text_quit_btn, self._quit_game),
        ]

        self.buttons = []
        self.button_map = {}

        for idx, (label, action) in enumerate(row_one_buttons):
            x = row_one_start + idx * (main_button_width + column_gap) + main_button_width // 2
            btn = GlowButton(
                x,
                row_one_y,
                main_button_width,
                config.MENU_BUTTON_HEIGHT,
                label,
                action,
            )
            self.buttons.append(btn)

        total_secondary_width = secondary_button_width * 2 + column_gap
        row_two_start = center_x - total_secondary_width // 2

        secondary_buttons = [
            ("theme", self.toggle_text, self._toggle_theme),
            ("difficulty", self.difficulty_text, self._cycle_difficulty),
        ]

        for idx, (key, label, action) in enumerate(secondary_buttons):
            x = row_two_start + idx * (secondary_button_width + column_gap) + secondary_button_width // 2
            btn = GlowButton(
                x,
                row_two_y,
                secondary_button_width,
                config.MENU_BUTTON_HEIGHT,
                label,
                action,
            )
            self.buttons.append(btn)
            self.button_map[key] = btn

    def _toggle_theme(self):
        theme_manager.toggle()
        # Rekonstruiere Buttons
        self.buttons = []
        self._create_buttons()

    def _multiplayer_button_state(self):
        if mconfig.CONNECTION:
            return "Multiplayer", self._start_multiplayer
        return "Multiplayer (Offline)", self._do_nothing

    def _update_multiplayer_button(self):
        multiplayer_button = self.buttons[1]
        label, action = self._multiplayer_button_state()
        multiplayer_button.text = label
        multiplayer_button.action = action

    def _start_game(self):
        """Startet ein neues Spiel"""
        self.game_manager.change_state(config.STATE_PLACEMENT)

    def _refresh_difficulty_text(self):
        difficulty_names = {
            "easy": "EINFACH",
            "normal": "NORMAL",
            "hard": "SCHWER",
        }
        current = self.game_manager.ai_difficulty
        self.difficulty_text = f"KI SCHWIERIGKEIT: {difficulty_names.get(current, 'NORMAL')}"

    def _cycle_difficulty(self):
        levels = ["easy", "normal", "hard"]
        current = self.game_manager.ai_difficulty
        idx = levels.index(current) if current in levels else 1
        self.game_manager.ai_difficulty = levels[(idx + 1) % len(levels)]
        self._refresh_difficulty_text()
        self.button_map["difficulty"].text = self.difficulty_text

    def _start_multiplayer(self):
        """Gehe ins Multiplayer-Menu"""
        self.game_manager.change_state(config.STATE_MULTIPLAYER_MENU)

    def _do_nothing(self):
        pass

    def _quit_game(self):
        """Beendet das Spiel"""
        import sys
        sys.exit()

    def update(self, dt, mouse_pos):
        """Aktualisiert das Menue"""
        mouse_x, mouse_y = mouse_pos
        for button in self.buttons:
            button.update(dt, mouse_x, mouse_y)

        self._update_multiplayer_button()


    def on_mouse_down(self, pos, button):
        """Behandelt Mausklicks"""
        if button == 1:  # Linke Maustaste
            for btn in self.buttons:
                if btn.hovered:
                    btn.click()
                    break

    def draw(self, screen):
        """Zeichnet das Menue"""
        current_theme = theme_manager.current
        # Premium Gradient Background
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

        # Schiff Artwork
        draw_title_art(screen)

        # Titel (Schatten + Glowing Text)
        title_font = pygame.font.Font(None, config.MENU_TITLE_FONT_SIZE)

        # Shadow
        shadow_surf = title_font.render(current_theme.text_title, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(config.WINDOW_WIDTH // 2, config.MENU_TITLE_Y + 4))
        screen.blit(shadow_surf, shadow_rect)

        # Main Title (Glowing)
        title_surf = title_font.render(current_theme.text_title, True, current_theme.color_text_primary)
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