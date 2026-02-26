"""
Schiffsplatzierungs-State
Spieler platziert seine Schiffe auf dem Board
"""

import pygame
from pygame import Rect
import game.config as config
from game.entities.board import Board
from game.entities.ship import Ship
from game.graphics import draw_gradient_background, draw_rounded_rect, draw_text, draw_grid_cell
from game.theme import theme_manager
from game.states.base_state import BaseState


class PlacementState(BaseState):
    """Schiffsplatzierungs-Phase"""

    def __init__(self, game_manager):
        """
        Initialisiert die Platzierungsphase

        Args:
            game_manager: Referenz zum GameManager
        """
        super().__init__(game_manager)
        self.player_board = Board(config.PLAYER_GRID_X, config.GRID_OFFSET_Y, "Player")

        # Schiffe die platziert werden muessen
        self.ships_to_place = []
        self._create_ships()

        self.current_ship_index = 0
        self.current_ship = self.ships_to_place[0] if self.ships_to_place else None
        self.current_orientation = config.ORIENTATION_HORIZONTAL

        self.preview_position = None  # (row, col) fuer Vorschau
        self.placement_valid = False

    def _create_ships(self):
        """Erstellt alle Schiffe die platziert werden muessen"""
        for ship_type in config.SHIP_TYPES:
            ship_name, ship_length, ship_count = ship_type[:3]
            ship_shape = ship_type[3] if len(ship_type) > 3 else None
            for i in range(ship_count):
                name = f"{ship_name} #{i+1}" if ship_count > 1 else ship_name
                self.ships_to_place.append(Ship(name, ship_length, shape=ship_shape))

    def update(self, dt, mouse_pos):
        """Aktualisiert die Platzierungsphase"""
        if not self.current_ship:
            return

        # Berechne Vorschau-Position
        cell_pos = self.player_board.get_cell_at_pos(mouse_pos[0], mouse_pos[1])

        if cell_pos:
            self.preview_position = cell_pos
            # Pruefe ob Platzierung gueltig ist
            self.placement_valid = self.player_board.can_place_ship(
                self.current_ship, cell_pos[0], cell_pos[1], self.current_orientation
            )
        else:
            self.preview_position = None
            self.placement_valid = False

    def on_mouse_down(self, pos, button):
        """Behandelt Mausklicks"""
        if button == 1 and self.current_ship and self.preview_position and self.placement_valid:
            # Platziere Schiff
            row, col = self.preview_position
            success = self.player_board.place_ship(
                self.current_ship, row, col, self.current_orientation
            )

            if success:
                # Naechstes Schiff
                self.current_ship_index += 1
                if self.current_ship_index < len(self.ships_to_place):
                    self.current_ship = self.ships_to_place[self.current_ship_index]
                    self.current_orientation = config.ORIENTATION_HORIZONTAL
                else:
                    # Alle Schiffe platziert -> Starte Kampfphase
                    self.player_board.all_ships_placed = True
                    self._start_battle()

    def on_key_down(self, key):
        """Behandelt Tasteneingaben"""
        # R-Taste: Rotation
        if key == pygame.K_r and self.current_ship:
            self.current_orientation = (
                   self.current_orientation + 1
            ) % self.current_ship.get_rotation_count()

    def _start_battle(self):
        """Startet die Kampfphase"""
        self.game_manager.player_board = self.player_board
        self.game_manager.change_state(config.STATE_BATTLE)

    def draw(self, screen):
        """Zeichnet die Platzierungsphase"""
        theme = theme_manager.current
        # Tactical Background
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

        # Titel Menu bar glow
        panel_rect = Rect(
            config.WINDOW_WIDTH // 2 - config.PLACEMENT_PANEL_WIDTH // 2,
            config.PLACEMENT_PANEL_Y,
            config.PLACEMENT_PANEL_WIDTH,
            config.PLACEMENT_PANEL_HEIGHT,
        )
        draw_rounded_rect(screen, (0, 0, 0), panel_rect, radius=20, alpha=150)
        draw_rounded_rect(screen, theme.color_ship_border, panel_rect, radius=20, width=3, alpha=100)

        draw_text(
            screen,
            theme.text_placement_title,
            config.WINDOW_WIDTH // 2,
            panel_rect.centery,
            config.PLACEMENT_TITLE_FONT_SIZE,
            theme.color_text_primary,
            center=True,
        )

        # Anleitung
        if self.current_ship:
            display_name = theme_manager.get_ship_display_name(self.current_ship.name)
            instruction = f"AUSGEWÄHLTES SCHIFF: {display_name.upper()} (LÄNGE: {self.current_ship.get_size()})"
            draw_text(
                screen,
                instruction,
                config.WINDOW_WIDTH // 2,
                panel_rect.bottom + 50,
                config.PLACEMENT_INSTRUCTION_FONT_SIZE,
                theme.color_text_secondary,
                center=True,
            )
            draw_text(
                screen,
                theme.text_placement_instruction,
                config.WINDOW_WIDTH // 2,
                config.WINDOW_HEIGHT - config.PLACEMENT_INSTRUCTION_MARGIN_BOTTOM,
                config.PLACEMENT_INSTRUCTION_FONT_SIZE,
                theme.color_text_secondary,
                center=True,
            )

        # Zeichne Spielfeld
        self._draw_board(screen)

        # Fortschrittsanzeige Panel
        prog_rect = Rect(
            config.WINDOW_WIDTH - config.PLACEMENT_PROGRESS_PANEL_WIDTH - config.PLACEMENT_PROGRESS_PANEL_MARGIN_RIGHT,
            config.PLACEMENT_PROGRESS_PANEL_Y,
            config.PLACEMENT_PROGRESS_PANEL_WIDTH,
            config.PLACEMENT_PROGRESS_PANEL_HEIGHT,
        )
        draw_rounded_rect(screen, (0, 0, 0), prog_rect, radius=15, alpha=150)

        progress = f"SCHIFF {self.current_ship_index + 1} VON {len(self.ships_to_place)}"
        draw_text(
            screen,
            progress,
            prog_rect.centerx,
            prog_rect.centery,
            config.PLACEMENT_PROGRESS_FONT_SIZE,
            (255, 200, 100),
            center=True,
        )

        # Bereits platzierte Schiffe auflisten
        self._draw_placed_ships_list(screen)

    def _draw_board(self, screen):
        """Zeichnet das Spielfeld mit Vorschau"""
        board = self.player_board
        theme = theme_manager.current

        # Draw board background glow
        bg_rect = Rect(
            board.x_offset - 10,
            board.y_offset - 10,
            config.GRID_SIZE * config.CELL_SIZE + 20,
            config.GRID_SIZE * config.CELL_SIZE + 20,
        )
        draw_rounded_rect(screen, theme.color_panel_bg, bg_rect, radius=10, alpha=180)
        draw_rounded_rect(screen, theme.color_ship_border, bg_rect, radius=10, width=2, alpha=80)

        # Zeichne Grid
        for row in range(config.GRID_SIZE):
            for col in range(config.GRID_SIZE):
                x = board.x_offset + col * config.CELL_SIZE
                y = board.y_offset + row * config.CELL_SIZE
                cell = board.get_cell(row, col)

                draw_grid_cell(screen, x, y, cell, is_enemy=False, show_ships=True)

        # Zeichne Vorschau
        if self.preview_position and self.current_ship:
            self._draw_ship_preview(screen)

    def _draw_ship_preview(self, screen):
        """Zeichnet die Schiffs-Vorschau"""
        if not self.preview_position:
            return

        row, col = self.preview_position
        ship = self.current_ship
        color = (50, 255, 100) if self.placement_valid else (255, 50, 50)

        # Zeichne alle Zellen die das Schiff belegen wuerde
        for preview_row, preview_col in ship.get_coordinates_at(row, col, self.current_orientation):

            if 0 <= preview_row < config.GRID_SIZE and 0 <= preview_col < config.GRID_SIZE:
                x = self.player_board.x_offset + preview_col * config.CELL_SIZE
                y = self.player_board.y_offset + preview_row * config.CELL_SIZE

                rect = Rect(
                    x + config.PLACEMENT_PREVIEW_INSET,
                    y + config.PLACEMENT_PREVIEW_INSET,
                    config.CELL_SIZE - config.PLACEMENT_PREVIEW_INSET * 2,
                    config.CELL_SIZE - config.PLACEMENT_PREVIEW_INSET * 2,
                )
                draw_rounded_rect(screen, color, rect, radius=4, alpha=150)
                draw_rounded_rect(screen, color, rect, radius=4, width=2, alpha=255)

    def _draw_placed_ships_list(self, screen):
        """Zeichnet eine Liste der bereits platzierten Schiffe"""
        x = config.PLACEMENT_SHIP_LIST_X
        y = config.WINDOW_HEIGHT - config.PLACEMENT_SHIP_LIST_MARGIN_BOTTOM

        panel_rect = Rect(
            x - 20,
            y - 20,
            config.PLACEMENT_SHIP_LIST_WIDTH,
            config.PLACEMENT_SHIP_LIST_HEIGHT,
        )
        draw_rounded_rect(screen, (0, 0, 0), panel_rect, radius=15, alpha=150)
        draw_rounded_rect(screen, (50, 100, 150), panel_rect, radius=15, width=2, alpha=80)

        draw_text(screen, "PLATZIERTE SCHIFFE", x, y, config.PLACEMENT_SHIP_LIST_TITLE_FONT_SIZE, (150, 200, 255))

        for i, ship in enumerate(self.player_board.ships):
            y_offset = y + 50 + i * config.PLACEMENT_SHIP_LIST_ITEM_SPACING
            display_name = theme_manager.get_ship_display_name(ship.name)
            text = f"{display_name.upper()} hat den Hafen verlassen"
            draw_text(screen, text, x, y_offset, config.PLACEMENT_SHIP_LIST_ITEM_FONT_SIZE, (100, 255, 150))

    def on_resize(self, width, height):
        self.player_board.x_offset = config.PLAYER_GRID_X
        self.player_board.y_offset = config.GRID_OFFSET_Y