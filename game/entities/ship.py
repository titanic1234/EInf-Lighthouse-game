# ship.py
"""
Ship-Klasse für Schiffe
"""

from game.config import ORIENTATION_COUNT


class Ship:
    """Repräsentiert ein Schiff"""

    def __init__(self, name, length, shape=None):
        """
        Initialisiert ein Schiff
        """
        self.name = name
        self.length = length
        self.orientation = 0
        self.shape = shape
        self.row = 0
        self.col = 0
        self.hits = 0
        self.cells = []  # Liste der Zellen, die dieses Schiff belegt

    def place(self, row, col, orientation):
        """Platziert das Schiff an einer Position"""
        self.row = row
        self.col = col
        self.orientation = orientation

    def add_cell(self, cell):
        """Ordnet ein Feld diesem Schiff zu"""
        self.cells.append(cell)

    def hit(self):
        """Registriert einen Treffer auf diesem Schiff"""
        self.hits += 1

    def is_destroyed(self):
        """
        Prüft, ob das Schiff versenkt wurde
        """
        return self.hits >= self.get_size()

    def get_coordinates(self, row=None, col=None, orientation=None):
        """
        Gibt alle Koordinaten zurück, die das Schiff belegt
        """
        if row is None:
            row = self.row
        if col is None:
            col = self.col
        if orientation is None:
            orientation = self.orientation
        return self.get_coordinates_at(row, col, orientation)

    def reset(self):
        """Setzt das Schiff zurück"""
        self.hits = 0
        self.cells = []
        self.row = 0
        self.col = 0
        self.orientation = 0

    def __repr__(self):
        orientation_labels = ["0°", "90°", "180°", "270°"]
        orientation_str = orientation_labels[self.orientation % ORIENTATION_COUNT]
        status = "VERSENKT" if self.is_destroyed() else f"{self.hits}/{self.get_size()}"
        return f"{self.name} [{orientation_str}] @ ({self.row},{self.col}) - {status}"

    def _base_offsets(self):
        """Gibt Zell-Offsets fuer horizontale Ausrichtung zurueck."""
        if self.shape == "carrier_l":
            return [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)]
        return [(0, i) for i in range(self.length)]

    def _oriented_offsets(self, orientation):
        """Richtet Offsets gemäß Orientierung aus."""
        offsets = self._base_offsets()
        rotation_steps = orientation % ORIENTATION_COUNT

        for _ in range(rotation_steps):
            # 90° Drehung im Uhrzeigersinn
            offsets = [(c, -r) for r, c in offsets]
            # auf positive Koordinaten normalisieren
            min_row = min(r for r, _ in offsets)
            min_col = min(c for _, c in offsets)
            offsets = [(r - min_row, c - min_col) for r, c in offsets]

        return offsets

    def get_coordinates_at(self, row, col, orientation):
        """Koordinaten fuer eine potenzielle Platzierung."""
        return [(row + dr, col + dc) for dr, dc in self._oriented_offsets(orientation)]

    def get_size(self):
        """Anzahl belegter Zellen."""
        return len(self._base_offsets())