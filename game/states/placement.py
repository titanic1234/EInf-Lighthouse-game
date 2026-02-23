"""
Schiffsplatzierungs-State
Spieler platziert seine Schiffe auf dem Board
"""

import pygame
from pygame import Rect
from game.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, GRID_SIZE, CELL_SIZE,
    COLOR_WHITE, COLOR_BLACK, COLOR_BLUE, COLOR_GREEN, COLOR_RED, COLOR_GRAY,
    ORIENTATION_HORIZONTAL, ORIENTATION_VERTICAL,
    SHIP_TYPES, PLAYER_GRID_X, GRID_OFFSET_Y,
    STATE_BATTLE
)
from game.entities.board import Board
from game.entities.ship import Ship
from game.graphics import draw_gradient_background, draw_rounded_rect
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
        self.player_board = Board(PLAYER_GRID_X, GRID_OFFSET_Y, "Player")

        # Schiffe die platziert werden müssen
        self.ships_to_place = []
        self._create_ships()

        self.current_ship_index = 0
        self.current_ship = self.ships_to_place[0] if self.ships_to_place else None
        self.current_orientation = ORIENTATION_HORIZONTAL

        self.preview_position = None  # (row, col) für Vorschau
        self.placement_valid = False

    def _create_ships(self):
        """Erstellt alle Schiffe die platziert werden müssen"""
        for ship_name, ship_length, ship_count in SHIP_TYPES:
            for i in range(ship_count):
                name = f"{ship_name} #{i+1}" if ship_count > 1 else ship_name
                self.ships_to_place.append(Ship(name, ship_length))

    def update(self, dt, mouse_pos):
        """Aktualisiert die Platzierungsphase"""
        if not self.current_ship:
            return

        # Berechne Vorschau-Position
        cell_pos = self.player_board.get_cell_at_pos(mouse_pos[0], mouse_pos[1])

        if cell_pos:
            self.preview_position = cell_pos
            # Prüfe ob Platzierung gültig ist
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
                # Nächstes Schiff
                self.current_ship_index += 1
                if self.current_ship_index < len(self.ships_to_place):
                    self.current_ship = self.ships_to_place[self.current_ship_index]
                    self.current_orientation = ORIENTATION_HORIZONTAL
                else:
                    # Alle Schiffe platziert -> Starte Kampfphase
                    self.player_board.all_ships_placed = True
                    self._start_battle()

    def on_key_down(self, key):
        """Behandelt Tasteneingaben"""
        # R-Taste: Rotation
        if key.name == 'r' and self.current_ship:
            self.current_orientation = (
                ORIENTATION_VERTICAL if self.current_orientation == ORIENTATION_HORIZONTAL
                else ORIENTATION_HORIZONTAL
            )

    def _start_battle(self):
        """Startet die Kampfphase"""
        self.game_manager.player_board = self.player_board
        self.game_manager.change_state(STATE_BATTLE)

    def draw(self, screen):
        """Zeichnet die Platzierungsphase"""
        # Tactical Background
        draw_gradient_background(screen.surface, (15, 25, 40), (5, 10, 20))

        # Titel Menu bar glow
        panel_rect = Rect(WINDOW_WIDTH//2 - 300, 10, 600, 50)
        draw_rounded_rect(screen.surface, (0, 0, 0), panel_rect, radius=15, alpha=150)
        draw_rounded_rect(screen.surface, (100, 150, 255), panel_rect, radius=15, width=2, alpha=100)
        
        screen.draw.text("COMMANDER, DEPLOY YOUR FLEET", center=(WINDOW_WIDTH // 2, 35),
                        fontsize=36, color=(200, 230, 255))

        # Anleitung
        if self.current_ship:
            instruction = f"ACTIVE UNIT: {self.current_ship.name.upper()} (LRG: {self.current_ship.length})"
            screen.draw.text(instruction, center=(WINDOW_WIDTH // 2, 85),
                           fontsize=26, color=(100, 255, 150))
            screen.draw.text("PRESS R TO ROTATE | LEFT CLICK TO DEPLOY",
                           center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30),
                           fontsize=22, color=(150, 180, 220))

        # Zeichne Spielfeld
        self._draw_board(screen)

        # Fortschrittsanzeige Panel
        prog_rect = Rect(WINDOW_WIDTH - 280, 20, 250, 40)
        draw_rounded_rect(screen.surface, (0, 0, 0), prog_rect, radius=10, alpha=150)
        
        progress = f"UNIT {self.current_ship_index + 1} OF {len(self.ships_to_place)}"
        screen.draw.text(progress, center=(WINDOW_WIDTH - 155, 40),
                        fontsize=22, color=(255, 200, 100))

        # Bereits platzierte Schiffe auflisten
        self._draw_placed_ships_list(screen)

    def _draw_board(self, screen):
        """Zeichnet das Spielfeld mit Vorschau"""
        board = self.player_board

        # Draw board background glow
        bg_rect = Rect(board.x_offset - 10, board.y_offset - 10, GRID_SIZE * CELL_SIZE + 20, GRID_SIZE * CELL_SIZE + 20)
        draw_rounded_rect(screen.surface, (10, 20, 40), bg_rect, radius=10, alpha=180)
        draw_rounded_rect(screen.surface, (50, 100, 200), bg_rect, radius=10, width=2, alpha=80)

        # Zeichne Grid
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = board.x_offset + col * CELL_SIZE
                y = board.y_offset + row * CELL_SIZE

                cell = board.get_cell(row, col)

                # Cell Background
                cell_rect = Rect(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)
                draw_rounded_rect(screen.surface, (20, 40, 80), cell_rect, radius=4, alpha=100)

                if cell.has_ship():
                     # Platziertes Schiff (glow effect)
                     draw_rounded_rect(screen.surface, (100, 200, 255), cell_rect, radius=4, alpha=200)

                # Subtle Grid-Linien
                screen.draw.rect(Rect(x, y, CELL_SIZE, CELL_SIZE), (40, 60, 100))

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

        # Zeichne alle Zellen die das Schiff belegen würde
        for i in range(ship.length):
            preview_row = row if self.current_orientation == ORIENTATION_HORIZONTAL else row + i
            preview_col = col + i if self.current_orientation == ORIENTATION_HORIZONTAL else col

            if 0 <= preview_row < GRID_SIZE and 0 <= preview_col < GRID_SIZE:
                x = self.player_board.x_offset + preview_col * CELL_SIZE
                y = self.player_board.y_offset + preview_row * CELL_SIZE

                rect = Rect(x + 2, y + 2, CELL_SIZE - 4, CELL_SIZE - 4)
                draw_rounded_rect(screen.surface, color, rect, radius=4, alpha=150)
                draw_rounded_rect(screen.surface, color, rect, radius=4, width=2, alpha=255)

    def _draw_placed_ships_list(self, screen):
        """Zeichnet eine Liste der bereits platzierten Schiffe"""
        x = 50
        y = WINDOW_HEIGHT - 200

        panel_rect = Rect(x - 10, y - 10, 220, 180)
        draw_rounded_rect(screen.surface, (0, 0, 0), panel_rect, radius=10, alpha=150)
        draw_rounded_rect(screen.surface, (50, 100, 150), panel_rect, radius=10, width=1, alpha=80)

        screen.draw.text("DEPLOYED UNITS", (x, y),
                        fontsize=20, color=(150, 200, 255))

        for i, ship in enumerate(self.player_board.ships):
            y_offset = y + 30 + i * 25
            text = f"✓ {ship.name.upper()}"
            screen.draw.text(text, (x, y_offset),
                           fontsize=18, color=(100, 255, 150))
