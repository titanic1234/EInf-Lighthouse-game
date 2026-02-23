"""
Computer-KI für Schiffe-Versenken
Implementiert eine intelligente Strategie mit Such- und Jagdmodus
"""

import random
from game.config import GRID_SIZE


class ComputerAI:
    """Intelligente KI für den Computer-Gegner"""

    MODE_HUNT = "hunt"      # Suchmodus: Zufällige Schüsse
    MODE_TARGET = "target"  # Zielmodus: Nach Treffer systematisch angreifen

    def __init__(self):
        """Initialisiert die KI"""
        self.mode = self.MODE_HUNT
        self.possible_targets = []  # Liste von Zellen, die nach einem Treffer angegriffen werden
        self.last_hit = None        # Letzte erfolgreiche Treffer-Position
        self.hit_sequence = []      # Sequenz von Treffern für Richtungserkennung
        self.tried_positions = set()  # Bereits beschossene Positionen

    def get_next_shot(self, board):
        """
        Bestimmt den nächsten Schuss

        Args:
            board: Board-Objekt des Spielers

        Returns:
            tuple: (row, col) Position für den nächsten Schuss
        """
        if self.mode == self.MODE_TARGET and self.possible_targets:
            # Zielmodus: Greife bekannte Ziele an
            return self._get_target_shot()
        else:
            # Suchmodus: Zufälliger Schuss
            return self._get_hunt_shot(board)

    def _get_hunt_shot(self, board):
        """
        Wählt einen zufälligen Schuss im Suchmodus

        Args:
            board: Board-Objekt

        Returns:
            tuple: (row, col)
        """
        available = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if (row, col) not in self.tried_positions:
                    cell = board.get_cell(row, col)
                    if not cell.is_shot():
                        available.append((row, col))

        if available:
            # Schachbrett-Muster für effizientere Suche
            # (Schiffe mit Länge > 1 werden so wahrscheinlicher getroffen)
            parity_targets = [pos for pos in available if (pos[0] + pos[1]) % 2 == 0]
            if parity_targets and random.random() < 0.7:  # 70% Wahrscheinlichkeit für Muster
                shot = random.choice(parity_targets)
            else:
                shot = random.choice(available)

            self.tried_positions.add(shot)
            return shot

        # Fallback falls keine verfügbaren Ziele (sollte nicht passieren)
        return random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)

    def _get_target_shot(self):
        """
        Wählt einen Schuss im Zielmodus

        Returns:
            tuple: (row, col)
        """
        if self.possible_targets:
            shot = self.possible_targets.pop(0)
            self.tried_positions.add(shot)
            return shot

        # Fallback: Zurück zum Suchmodus
        self.mode = self.MODE_HUNT
        return None

    def register_shot_result(self, row, col, hit, destroyed, ship):
        """
        Registriert das Ergebnis eines Schusses

        Args:
            row: Zeile des Schusses
            col: Spalte des Schusses
            hit: True wenn getroffen
            destroyed: True wenn Schiff versenkt
            ship: Das getroffene/versenkte Schiff (oder None)
        """
        self.tried_positions.add((row, col))

        if hit:
            self.last_hit = (row, col)
            self.hit_sequence.append((row, col))

            if destroyed:
                # Schiff versenkt: Zurück zum Suchmodus
                self._switch_to_hunt_mode()
            else:
                # Treffer aber nicht versenkt: Wechsel zum Zielmodus
                self._switch_to_target_mode(row, col)

    def _switch_to_target_mode(self, row, col):
        """
        Wechselt in den Zielmodus nach einem Treffer

        Args:
            row: Zeile des Treffers
            col: Spalte des Treffers
        """
        self.mode = self.MODE_TARGET

        if len(self.hit_sequence) == 1:
            # Erster Treffer: Alle 4 angrenzenden Zellen hinzufügen
            self._add_adjacent_targets(row, col)
        else:
            # Mehrere Treffer: Richtung erkennen und fortsetzen
            self._add_directional_targets()

    def _switch_to_hunt_mode(self):
        """Wechselt zurück in den Suchmodus"""
        self.mode = self.MODE_HUNT
        self.possible_targets = []
        self.hit_sequence = []
        self.last_hit = None

    def _add_adjacent_targets(self, row, col):
        """
        Fügt alle angrenzenden Zellen als mögliche Ziele hinzu

        Args:
            row: Zeile
            col: Spalte
        """
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Rechts, Links, Unten, Oben

        new_targets = []
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if (0 <= new_row < GRID_SIZE and 0 <= new_col < GRID_SIZE and
                (new_row, new_col) not in self.tried_positions):
                new_targets.append((new_row, new_col))

        # Zufällige Reihenfolge für Unvorhersehbarkeit
        random.shuffle(new_targets)
        self.possible_targets.extend(new_targets)

    def _add_directional_targets(self):
        """Fügt Ziele basierend auf erkannter Richtung hinzu"""
        if len(self.hit_sequence) < 2:
            return

        # Erkenne Richtung aus den letzten beiden Treffern
        last_two = self.hit_sequence[-2:]
        dr = last_two[1][0] - last_two[0][0]
        dc = last_two[1][1] - last_two[0][1]

        # Normalisiere Richtung
        if dr != 0:
            dr = dr // abs(dr)
        if dc != 0:
            dc = dc // abs(dc)

        # Füge Zellen in beide Richtungen hinzu
        for direction in [(dr, dc), (-dr, -dc)]:
            # Prüfe vom ersten und letzten Treffer aus
            for start_pos in [self.hit_sequence[0], self.hit_sequence[-1]]:
                new_row = start_pos[0] + direction[0]
                new_col = start_pos[1] + direction[1]

                if (0 <= new_row < GRID_SIZE and 0 <= new_col < GRID_SIZE and
                    (new_row, new_col) not in self.tried_positions and
                    (new_row, new_col) not in self.possible_targets):
                    self.possible_targets.append((new_row, new_col))

    def reset(self):
        """Setzt die KI zurück"""
        self.mode = self.MODE_HUNT
        self.possible_targets = []
        self.last_hit = None
        self.hit_sequence = []
        self.tried_positions = set()

    def __repr__(self):
        return f"ComputerAI(mode={self.mode}, targets={len(self.possible_targets)}, hits={len(self.hit_sequence)})"
