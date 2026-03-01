"""
Cell-Klasse für einzelne Spielfeld-Zellen
"""

from game.config import CELL_EMPTY, CELL_SHIP, CELL_HIT, CELL_MISS, CELL_DESTROYED


class Cell:
    """Repräsentiert eine einzelne Zelle im Spielfeld"""

    def __init__(self, row, col):
        """
        Initialisiert eine Zelle

        Args:
            row: Zeile (0-9)
            col: Spalte (0-9)
        """
        self.row = row
        self.col = col
        self.status = CELL_EMPTY
        self.ship = None  # Referenz zum Schiff, falls vorhanden
        self.scan_marked = False
        self.scan_found_ship = False
        self.napalm_marked = False
        self.player_marker = False

    def has_ship(self):
        """Prüft, ob die Zelle ein Schiff enthält"""
        return self.ship is not None

    def is_hit(self):
        """Prüft, ob die Zelle getroffen wurde"""
        return self.status == CELL_HIT

    def is_miss(self):
        """Prüft, ob die Zelle ein Fehlschuss ist"""
        return self.status == CELL_MISS

    def is_shot(self):
        """Prüft, ob auf diese Zelle bereits geschossen wurde"""
        return self.status in (CELL_HIT, CELL_MISS, CELL_DESTROYED)

    def place_ship(self, ship):
        """Platziert ein Schiff auf dieser Zelle"""
        self.ship = ship
        self.status = CELL_SHIP

    def shoot(self):
        """
        Schießt auf diese Zelle

        Returns:
            bool: True wenn getroffen, False wenn Fehlschuss
        """
        if self.is_shot():
            return False  # Bereits beschossen

        self.scan_marked = False
        self.scan_found_ship = False
        self.napalm_marked = False
        self.player_marker = False

        if self.has_ship():
            self.status = CELL_HIT
            self.ship.hit()
            return True
        else:
            self.status = CELL_MISS
            return False

    def mark_destroyed(self):
        """Markiert die Zelle als Teil eines versenkten Schiffs"""
        self.status = CELL_DESTROYED

    def reset(self):
        """Setzt die Zelle zurück"""
        self.status = CELL_EMPTY
        self.ship = None
        self.scan_marked = False
        self.scan_found_ship = False
        self.napalm_marked = False
        self.player_marker = False

    def __repr__(self):
        status_symbols = {
            CELL_EMPTY: '~',
            CELL_SHIP: 'S',
            CELL_HIT: 'X',
            CELL_MISS: 'O',
            CELL_DESTROYED: '#'
        }
        return status_symbols.get(self.status, '?')
