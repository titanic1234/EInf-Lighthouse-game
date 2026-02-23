"""
Ship-Klasse für Schiffe
"""

from game.config import ORIENTATION_HORIZONTAL, ORIENTATION_VERTICAL


class Ship:
    """Repräsentiert ein Schiff"""

    def __init__(self, name, length):
        """
        Initialisiert ein Schiff

        Args:
            name: Name des Schiffs (z.B. "Schlachtschiff")
            length: Länge des Schiffs (Anzahl Zellen)
        """
        self.name = name
        self.length = length
        self.orientation = ORIENTATION_HORIZONTAL
        self.row = 0
        self.col = 0
        self.hits = 0
        self.cells = []  # Liste der Zellen, die dieses Schiff belegt

    def place(self, row, col, orientation):
        """
        Platziert das Schiff an einer Position

        Args:
            row: Startzeile
            col: Startspalte
            orientation: ORIENTATION_HORIZONTAL oder ORIENTATION_VERTICAL
        """
        self.row = row
        self.col = col
        self.orientation = orientation

    def add_cell(self, cell):
        """
        Fügt eine Zelle zu diesem Schiff hinzu

        Args:
            cell: Cell-Objekt
        """
        self.cells.append(cell)

    def hit(self):
        """Registriert einen Treffer auf diesem Schiff"""
        self.hits += 1

    def is_destroyed(self):
        """
        Prüft, ob das Schiff versenkt wurde

        Returns:
            bool: True wenn versenkt, sonst False
        """
        return self.hits >= self.length

    def get_coordinates(self):
        """
        Gibt alle Koordinaten zurück, die das Schiff belegt

        Returns:
            list: Liste von (row, col) Tupeln
        """
        coords = []
        for i in range(self.length):
            if self.orientation == ORIENTATION_HORIZONTAL:
                coords.append((self.row, self.col + i))
            else:  # ORIENTATION_VERTICAL
                coords.append((self.row + i, self.col))
        return coords

    def reset(self):
        """Setzt das Schiff zurück"""
        self.hits = 0
        self.cells = []
        self.row = 0
        self.col = 0
        self.orientation = ORIENTATION_HORIZONTAL

    def __repr__(self):
        orientation_str = "H" if self.orientation == ORIENTATION_HORIZONTAL else "V"
        status = "VERSENKT" if self.is_destroyed() else f"{self.hits}/{self.length}"
        return f"{self.name} [{orientation_str}] @ ({self.row},{self.col}) - {status}"
