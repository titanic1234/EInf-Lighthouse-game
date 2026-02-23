"""
Schiffsplatzierungs-State
Spieler platziert seine Schiffe auf dem Board
"""

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


class PlacementState:
    """Schiffsplatzierungs-Phase"""

    def __init__(self, game_manager):
        """
        Initialisiert die Platzierungsphase

        Args:
            game_manager: Referenz zum GameManager
        """
        self.game_manager = game_manager
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
        """
        Aktualisiert die Platzierungsphase

        Args:
            dt: Delta-Zeit
            mouse_pos: Tuple (x, y) der Mausposition
        """
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
        """
        Behandelt Mausklicks

        Args:
            pos: Tuple (x, y)
            button: Maustaste
        """
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
        """
        Behandelt Tasteneingaben

        Args:
            key: Taste (pgzero key constant)
        """
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
        """
        Zeichnet die Platzierungsphase

        Args:
            screen: pgzero Screen-Objekt
        """
        screen.clear()
        screen.fill(COLOR_BLACK)

        # Titel
        screen.draw.text("Platziere deine Schiffe", center=(WINDOW_WIDTH // 2, 30),
                        fontsize=40, color=COLOR_WHITE)

        # Anleitung
        if self.current_ship:
            instruction = f"Platziere: {self.current_ship.name} (Länge: {self.current_ship.length})"
            screen.draw.text(instruction, center=(WINDOW_WIDTH // 2, 70),
                           fontsize=24, color=COLOR_GREEN)
            screen.draw.text("R = Rotieren | Linksklick = Platzieren",
                           center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30),
                           fontsize=20, color=COLOR_WHITE)

        # Zeichne Spielfeld
        self._draw_board(screen)

        # Fortschrittsanzeige
        progress = f"Schiff {self.current_ship_index + 1} / {len(self.ships_to_place)}"
        screen.draw.text(progress, (WINDOW_WIDTH - 200, 30),
                        fontsize=24, color=COLOR_WHITE)

        # Bereits platzierte Schiffe auflisten
        self._draw_placed_ships_list(screen)

    def _draw_board(self, screen):
        """Zeichnet das Spielfeld mit Vorschau"""
        board = self.player_board

        # Zeichne Grid
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = board.x_offset + col * CELL_SIZE
                y = board.y_offset + row * CELL_SIZE

                cell = board.get_cell(row, col)

                # Hintergrund
                if cell.has_ship():
                    # Bereits platziertes Schiff
                    screen.blit('ship_h', (x, y))
                else:
                    screen.blit('water', (x, y))

                # Grid-Linien
                rect = Rect(x, y, CELL_SIZE, CELL_SIZE)
                screen.draw.rect(rect, COLOR_GRAY)

        # Zeichne Vorschau
        if self.preview_position and self.current_ship:
            self._draw_ship_preview(screen)

    def _draw_ship_preview(self, screen):
        """Zeichnet die Schiffs-Vorschau"""
        if not self.preview_position:
            return

        row, col = self.preview_position
        ship = self.current_ship
        color = COLOR_GREEN if self.placement_valid else COLOR_RED

        # Zeichne alle Zellen die das Schiff belegen würde
        for i in range(ship.length):
            preview_row = row if self.current_orientation == ORIENTATION_HORIZONTAL else row + i
            preview_col = col + i if self.current_orientation == ORIENTATION_HORIZONTAL else col

            if 0 <= preview_row < GRID_SIZE and 0 <= preview_col < GRID_SIZE:
                x = self.player_board.x_offset + preview_col * CELL_SIZE
                y = self.player_board.y_offset + preview_row * CELL_SIZE

                # Halbtransparenter Overlay (simuliert durch hellere Farbe)
                rect = Rect(x + 2, y + 2, CELL_SIZE - 4, CELL_SIZE - 4)
                screen.draw.filled_rect(rect, color + (100,) if len(color) == 3 else color)
                screen.draw.rect(rect, color)

    def _draw_placed_ships_list(self, screen):
        """Zeichnet eine Liste der bereits platzierten Schiffe"""
        x = 50
        y = WINDOW_HEIGHT - 150

        screen.draw.text("Platzierte Schiffe:", (x, y),
                        fontsize=20, color=COLOR_WHITE)

        for i, ship in enumerate(self.player_board.ships):
            y_offset = y + 30 + i * 25
            text = f"✓ {ship.name}"
            screen.draw.text(text, (x, y_offset),
                           fontsize=18, color=COLOR_GREEN)
