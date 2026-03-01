"""
Board-Klasse für das Spielfeld
"""

from game.config import GRID_SIZE, CELL_SIZE, SHIP_TYPES
from game.entities.cell import Cell
from game.entities.ship import Ship
import random


class Board:
    """Repräsentiert ein Spielfeld (10x10)"""

    def __init__(self, x_offset, y_offset, owner="Player"):
        """
        Initialisiert ein Spielfeld

        Args:
            x_offset: X-Position des Spielfelds
            y_offset: Y-Position des Spielfelds
            owner: Name des Besitzers ("Player" oder "Computer")
        """
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.owner = owner
        self.grid = [[Cell(row, col) for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]
        self.ships = []
        self.all_ships_placed = False

    def get_cell(self, row, col):
        """
        Gibt die Zelle an der Position zurück

        Args:
            row: Zeile (0-9)
            col: Spalte (0-9)

        Returns:
            Cell oder None wenn außerhalb
        """
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return self.grid[row][col]
        return None

    def can_place_ship(self, ship, row, col, orientation):
        """
        Prüft, ob ein Schiff platziert werden kann

        Args:
            ship: Ship-Objekt
            row: Startzeile
            col: Startspalte
            orientation: ORIENTATION_HORIZONTAL oder ORIENTATION_VERTICAL

        Returns:
            bool: True wenn platzierbar, sonst False
        """
        coordinates = ship.get_coordinates(row, col, orientation)

        # Prüfe ob innerhalb der Grenzen
        for check_row, check_col in coordinates:
            if not (0 <= check_row < GRID_SIZE and 0 <= check_col < GRID_SIZE):
                return False

        # Prüfe alle Zellen + angrenzende Zellen (Schiffe dürfen sich nicht berühren)
        for check_row, check_col in coordinates:
            # Prüfe die Zelle selbst und alle 8 Nachbarn
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    cell = self.get_cell(check_row + dr, check_col + dc)
                    if cell and cell.has_ship():
                        return False

        return True

    def place_ship(self, ship, row, col, orientation):
        """
        Platziert ein Schiff auf dem Board

        Args:
            ship: Ship-Objekt
            row: Startzeile
            col: Startspalte
            orientation: ORIENTATION_HORIZONTAL oder ORIENTATION_VERTICAL

        Returns:
            bool: True wenn erfolgreich platziert, sonst False
        """
        if not self.can_place_ship(ship, row, col, orientation):
            return False

        ship.place(row, col, orientation)

        # Platziere Schiff auf allen Zellen
        for cell_row, cell_col in ship.get_coordinates_at(row, col, orientation):
            cell = self.get_cell(cell_row, cell_col)
            if cell is None:
                return False
            cell.place_ship(ship)
            ship.add_cell(cell)

        self.ships.append(ship)
        return True


    def remove_ship(self, ship):
        """Entfernt plaziertes Ship für neues placement"""
        if ship not in self.ships:
            return False

        for cell in list(ship.cells):
            cell.reset()
        ship.reset()
        self.ships.remove(ship)
        self.all_ships_placed = False
        return True


    def place_ships_randomly(self):
        """Platziert alle Schiffe zufällig auf dem Board (für Computer)"""
        for ship_type in SHIP_TYPES:
            ship_name, ship_length, ship_count = ship_type[:3]
            ship_shape = ship_type[3] if len(ship_type) > 3 else None
            for _ in range(ship_count):
                placed = False
                attempts = 0
                while not placed and attempts < 1000:
                    row = random.randint(0, GRID_SIZE - 1)
                    col = random.randint(0, GRID_SIZE - 1)
                    ship = Ship(ship_name, ship_length, shape=ship_shape)
                    orientation = random.randint(0, ship.get_rotation_count() - 1)

                    if self.place_ship(ship, row, col, orientation):
                        placed = True
                    attempts += 1

        self.all_ships_placed = True

    def shoot(self, row, col):
        """
        Schießt auf eine Zelle

        Args:
            row: Zeile
            col: Spalte

        Returns:
            tuple: (hit: bool, destroyed: bool, ship: Ship oder None)
                   hit: True wenn getroffen
                   destroyed: True wenn Schiff versenkt wurde
                   ship: Das getroffene/versenkte Schiff (oder None)
        """
        cell = self.get_cell(row, col)
        if not cell or cell.is_shot():
            return False, False, None

        hit = cell.shoot()
        destroyed = False
        ship = None

        if hit and cell.ship:
            ship = cell.ship
            if ship.is_destroyed():
                destroyed = True
                # Markiere alle Zellen des versenkten Schiffs
                for ship_cell in ship.cells:
                    ship_cell.mark_destroyed()

        return hit, destroyed, ship

    def all_ships_destroyed(self):
        """
        Prüft, ob alle Schiffe versenkt wurden

        Returns:
            bool: True wenn alle Schiffe versenkt
        """
        return all(ship.is_destroyed() for ship in self.ships)

    def get_cell_at_pos(self, mouse_x, mouse_y):
        """
        Gibt die Zelle an der Mausposition zurück

        Args:
            mouse_x: X-Position der Maus
            mouse_y: Y-Position der Maus

        Returns:
            tuple: (row, col) oder None
        """
        # Prüfe ob innerhalb des Boards
        if (self.x_offset <= mouse_x < self.x_offset + GRID_SIZE * CELL_SIZE and
            self.y_offset <= mouse_y < self.y_offset + GRID_SIZE * CELL_SIZE):

            col = (mouse_x - self.x_offset) // CELL_SIZE
            row = (mouse_y - self.y_offset) // CELL_SIZE

            if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                return row, col

        return None

    def reset(self):
        """Setzt das Board zurück"""
        self.grid = [[Cell(row, col) for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]
        self.ships = []
        self.all_ships_placed = False

    def __repr__(self):
        """String-Repräsentation für Debugging"""
        result = [f"Board ({self.owner}):"]
        result.append("  " + " ".join(str(i) for i in range(GRID_SIZE)))
        for row_idx, row in enumerate(self.grid):
            result.append(f"{row_idx} " + " ".join(str(cell) for cell in row))
        return "\n".join(result)
