"""Gemeinsame Battle-Logik für Singleplayer und Multiplayer."""

import os
import pygame
from pgzero.rect import Rect

import game.config as config
from game.graphics import (
    ParticleSystem,
    draw_gradient_background,
    draw_grid_cell,
    draw_rounded_rect,
    draw_text,
)
from game.states.base_state import BaseState
from game.theme import theme_manager


class SharedBattleState(BaseState):
    """Gemeinsame UI/Input-Logik für Battle."""

    enemy_board_title = None

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.player_board = self.game_manager.player_board
        self.particles = ParticleSystem()

        self.abilities = {
            "airstrike": {"charges": 1, "targeted": True},
            "guided": {"charges": 1, "targeted": False},
            "sonar": {"charges": 1, "targeted": True},
            "napalm": {"charges": 1, "targeted": True},
        }

        self.selected_ability = None
        self.active_fires = []
        self.ability_buttons = []
        self._load_ability_icons()
        self._rebuild_ability_buttons()

    def _get_enemy_board(self):
        if hasattr(self, "computer_board"):
            return self.computer_board
        if hasattr(self, "opponent_board"):
            return self.opponent_board
        return None

    def _load_icon(self, filename):
        path = os.path.join("images", filename)
        if not os.path.exists(path):
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

    def _load_ability_icons(self):
        is_modern = theme_manager.current.name == "MODERN"
        self.ability_icons = {
            "airstrike": self._load_icon("airstrike.png" if is_modern else "breitseite.png"),
            "guided": self._load_icon("lenkrakete.png" if is_modern else "enterhaken.png"),
            "sonar": self._load_icon("sonar.png" if is_modern else "Kraehennest.png"),
            "napalm": self._load_icon("napalm.png" if is_modern else "griechisches_feuer.png"),
        }

    def _rebuild_ability_buttons(self):
        size = 64
        spacing = 20
        total_width = size * 4 + spacing * 3
        start_x = config.WINDOW_WIDTH // 2 - total_width // 2
        y = config.WINDOW_HEIGHT - 90

        names = ["airstrike", "guided", "sonar", "napalm"]
        self.ability_buttons = []
        for idx, name in enumerate(names):
            rect = pygame.Rect(start_x + idx * (size + spacing), y, size, size)
            self.ability_buttons.append((name, rect))

    def _ability_display_name(self, ability_key):
        is_modern = theme_manager.current.name == "MODERN"
        names = {
            "airstrike": "LUFTSCHLAG" if is_modern else "BREITSEITE",
            "guided": "LENKRAKETE" if is_modern else "ENTERHAKEN",
            "sonar": "SONAR" if is_modern else "KRÄHENNEST",
            "napalm": "NAPALM" if is_modern else "GRIECHISCHES FEUER",
        }
        return names.get(ability_key, "SPEZIALFÄHIGKEIT")

    def _activate_ability(self, name):
        if not self.player_turn or self.abilities[name]["charges"] <= 0:
            return

        if name == "guided":
            self._use_guided_missile()
            return

        self.selected_ability = name
        label = {
            "airstrike": f"{self._ability_display_name('airstrike')} AKTIV (+)",
            "sonar": f"{self._ability_display_name('sonar')} AKTIV (3x3)",
            "napalm": f"{self._ability_display_name('napalm')} AKTIV",
        }
        self.message = label.get(name, "SPEZIALFÄHIGKEIT AKTIV")

    def _toggle_player_marker(self, pos):
        board = self._get_enemy_board()
        if not board:
            return
        cell_pos = board.get_cell_at_pos(pos[0], pos[1])
        if not cell_pos:
            return

        row, col = cell_pos
        cell = board.get_cell(row, col)
        if not cell:
            return

        if cell.is_shot() or cell.scan_marked or cell.napalm_marked:
            return

        cell.player_marker = not cell.player_marker

    def _spawn_effects(self, board, row, col, hit):
        x = board.x_offset + col * config.CELL_SIZE + config.CELL_SIZE // 2
        y = board.y_offset + row * config.CELL_SIZE + config.CELL_SIZE // 2
        if hit:
            self.particles.add_explosion(x, y, count=40, color=(255, 60, 20))
        else:
            self.particles.add_splash(x, y, count=25)

    def _update_pipeline(self, dt, mouse_pos):
        """Hook for subclasses (AI turn, WS polling, timers, ...)."""

    def update(self, dt, mouse_pos):
        self.particles.update(dt)
        self._update_pipeline(dt, mouse_pos)

    def on_mouse_down(self, pos, button):
        if button not in (1, 3) or self.game_over:
            return

        if button == 3:
            self._toggle_player_marker(pos)
            return

        if not self.player_turn:
            return

        for name, rect in self.ability_buttons:
            if rect.collidepoint(pos):
                self._activate_ability(name)
                return

        board = self._get_enemy_board()
        if not board:
            return
        cell_pos = board.get_cell_at_pos(pos[0], pos[1])
        if not cell_pos:
            return

        row, col = cell_pos
        if self.selected_ability == "airstrike":
            self._player_airstrike(row, col)
        elif self.selected_ability == "sonar":
            self._player_sonar(row, col)
        elif self.selected_ability == "napalm":
            self._player_napalm(row, col)
        else:
            self._player_shoot(row, col)

    def _enemy_board_header(self):
        if self.enemy_board_title:
            return self.enemy_board_title
        return theme_manager.current.text_battle_enemy_radar

    def _draw_ability_buttons(self, screen):
        for name, rect in self.ability_buttons:
            charges = self.abilities[name]["charges"]
            active = self.selected_ability == name
            enabled = charges > 0 and self.player_turn and not self.game_over

            base = (45, 75, 120) if enabled else (45, 45, 45)
            hover = (85, 130, 200) if enabled else (70, 70, 70)
            color = hover if rect.collidepoint(pygame.mouse.get_pos()) else base
            border = (255, 215, 0) if active else (160, 210, 255)

            draw_rounded_rect(screen, (0, 0, 0), rect.move(0, 4), radius=8, alpha=120)
            draw_rounded_rect(screen, color, rect, radius=8, alpha=230)
            draw_rounded_rect(screen, border, rect, radius=8, width=2, alpha=255)

            icon = self.ability_icons.get(name)
            if icon:
                icon_surf = pygame.transform.smoothscale(icon, (42, 42))
                icon_rect = icon_surf.get_rect(center=rect.center)
                screen.blit(icon_surf, icon_rect)

            draw_text(screen, str(charges), rect.right - 12, rect.top + 6, 24, (255, 255, 255), center=True)

    def _draw_board(self, screen, board, show_ships=True, is_enemy=False):
        theme = theme_manager.current
        bg_rect = Rect(
            board.x_offset - 10,
            board.y_offset - 10,
            config.GRID_SIZE * config.CELL_SIZE + 20,
            config.GRID_SIZE * config.CELL_SIZE + 20,
        )
        border_color = theme.color_text_enemy if is_enemy else theme.color_ship_border
        bg_color = (40, 10, 10) if is_enemy else theme.color_panel_bg
        draw_rounded_rect(screen, bg_color, bg_rect, radius=10, alpha=180)
        draw_rounded_rect(screen, border_color, bg_rect, radius=10, width=2, alpha=80)

        for row in range(config.GRID_SIZE):
            for col in range(config.GRID_SIZE):
                x = board.x_offset + col * config.CELL_SIZE
                y = board.y_offset + row * config.CELL_SIZE
                cell = board.get_cell(row, col)
                draw_grid_cell(screen, x, y, cell, is_enemy=is_enemy, show_ships=show_ships)

        label_color = (150, 200, 255) if not is_enemy else (255, 150, 150)
        for i in range(config.GRID_SIZE):
            draw_text(screen, str(i + 1), board.x_offset - 35,
                      board.y_offset + i * config.CELL_SIZE + config.CELL_SIZE // 2 - 12, config.BATTLE_LABEL_FONT_SIZE,
                      label_color)
            draw_text(screen, chr(65 + i), board.x_offset + i * config.CELL_SIZE + config.CELL_SIZE // 2,
                      board.y_offset - 30, config.BATTLE_LABEL_FONT_SIZE, label_color, center=True)

    def _draw_statistics(self, screen):
        """Optional hook."""

    def draw(self, screen):
        theme = theme_manager.current
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

        panel_rect = Rect(
            config.WINDOW_WIDTH // 2 - config.BATTLE_PANEL_WIDTH // 2,
            config.BATTLE_PANEL_Y,
            config.BATTLE_PANEL_WIDTH,
            config.BATTLE_PANEL_HEIGHT,
        )
        draw_rounded_rect(screen, (0, 0, 0), panel_rect, radius=20, alpha=150)
        draw_rounded_rect(screen, theme.color_ship_border, panel_rect, radius=20, width=3, alpha=100)

        msg_color = theme.color_text_primary if self.player_turn else theme.color_text_enemy
        draw_text(screen, self.message, config.WINDOW_WIDTH // 2, panel_rect.centery, config.BATTLE_STATUS_FONT_SIZE,
                  msg_color, center=True)

        draw_text(screen, theme.text_battle_player_radar, config.PLAYER_GRID_X, config.GRID_OFFSET_Y - 80,
                  config.BATTLE_HEADER_FONT_SIZE, theme.color_text_secondary)
        draw_text(screen, self._enemy_board_header(), config.COMPUTER_GRID_X, config.GRID_OFFSET_Y - 80,
                  config.BATTLE_HEADER_FONT_SIZE, theme.color_text_enemy)

        self._draw_board(screen, self.player_board, show_ships=True, is_enemy=False)
        enemy_board = self._get_enemy_board()
        if enemy_board:
            self._draw_board(screen, enemy_board, show_ships=False, is_enemy=True)

        self._draw_ability_buttons(screen)
        self.particles.draw(screen)
        self._draw_statistics(screen)