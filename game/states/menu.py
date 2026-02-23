"""
Hauptmenü-State mit aufgewerteter UI
"""

import pygame
from pygame import Rect
from game.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, TITLE,
    COLOR_WHITE, COLOR_BLACK, COLOR_BLUE,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_COLOR, BUTTON_HOVER_COLOR,
    STATE_PLACEMENT
)
from game.graphics import draw_gradient_background, GlowButton
from game.states.base_state import BaseState

class MenuState(BaseState):
    """Hauptmenü-State"""

    def __init__(self, game_manager):
        """
        Initialisiert das Menü

        Args:
            game_manager: Referenz zum GameManager
        """
        super().__init__(game_manager)
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):
        """Erstellt die Menü-Buttons"""
        center_x = WINDOW_WIDTH // 2
        start_y = WINDOW_HEIGHT // 2 + 50

        # "Neues Spiel" Button
        self.buttons.append(
            GlowButton(center_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT,
                  "Neues Spiel", self._start_game)
        )

        # "Beenden" Button
        self.buttons.append(
            GlowButton(center_x, start_y + 80, BUTTON_WIDTH, BUTTON_HEIGHT,
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
        """Aktualisiert das Menü"""
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
        """Zeichnet das Menü"""
        # Premium Gradient Background
        draw_gradient_background(screen.surface, (20, 30, 60), (5, 10, 20))

        # Titel (Schatten + Glowing Text)
        title_font = pygame.font.Font(None, 80)
        
        # Shadow
        shadow_surf = title_font.render(TITLE.upper(), True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(WINDOW_WIDTH // 2, 134))
        screen.surface.blit(shadow_surf, shadow_rect)
        
        # Main Title (Glowing Blue/White)
        title_surf = title_font.render(TITLE.upper(), True, (200, 230, 255))
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 130))
        screen.surface.blit(title_surf, title_rect)

        # Untertitel
        sub_font = pygame.font.Font(None, 40)
        sub_surf = sub_font.render("TACTICAL NAVAL COMBAT", True, (100, 150, 255))
        sub_rect = sub_surf.get_rect(center=(WINDOW_WIDTH // 2, 190))
        screen.surface.blit(sub_surf, sub_rect)

        # Buttons
        for button in self.buttons:
            button.draw(screen.surface)

        # Steuerungshinweise am unteren Rand
        info_font = pygame.font.Font(None, 24)
        info_surf = info_font.render("Steuerung: Maus", True, (100, 100, 120))
        info_rect = info_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30))
        screen.surface.blit(info_surf, info_rect)

