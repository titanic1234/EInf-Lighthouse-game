"""
Computer-KI für Schiffe-Versenken
Implementiert eine intelligente Strategie mit Such- und Jagdmodus
"""

import random
from game.config import GRID_SIZE


class ComputerAI:
    """Intelligente KI für den Computer-Gegner"""

    MODE_HUNT = "hunt"      # Suchmodus: Raster abgehen
    MODE_TARGET = "target"  # Zielmodus: Nach Treffer systematisch angreifen

    def __init__(self):
        """Initialisiert die KI"""
        self.mode = self.MODE_HUNT
        self.possible_targets = []  # Liste von Zellen, die nach einem Treffer angegriffen werden
        self.last_hit = None        # Letzte erfolgreiche Treffer-Position
        self.hit_sequence = []      # Sequenz von Treffern für Richtungserkennung
        self.tried_positions = set()  # Beschossene oder ausgeschlossene Positionen

        # Hunt-Muster: Schachbrett (nur diagonale Berührung möglich)
        self.parity_offset = random.randint(0, 1)
        self.diagonal_offset = random.randint(0, 3)
        self.hunt_queue = []

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
        # Suchmodus
        return self._get_hunt_shot(board)

    def _get_hunt_shot(self, board):
        """
        Wählt einen Schuss im Suchmodus

        Args:
            board: Board-Objekt

        Returns:
            tuple: (row, col)
        """
        if not self.hunt_queue:
            self._rebuild_hunt_queue(board)

        while self.hunt_queue:
            shot = self.hunt_queue.pop(0)
            if shot in self.tried_positions:
                continue

            cell = board.get_cell(*shot)
            if cell and not cell.is_shot():
                self.tried_positions.add(shot)
                return shot

            # Falls das aktuelle Raster vollständig ist, auf restliche Felder ausweichen
        remaining = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if (row, col) in self.tried_positions:
                    continue
                cell = board.get_cell(row, col)
                if cell and not cell.is_shot():
                    remaining.append((row, col))

        if remaining:
            shot = random.choice(remaining)
            self.tried_positions.add(shot)
            return shot

        # Fallback falls keine verfügbaren Ziele (sollte nicht passieren)
        return random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)

    def _rebuild_hunt_queue(self, board):
        """Berechnet das Hunt-Raster neu (semi-random, schwer vorhersagbar)."""
        # Muster bei jedem Neuaufbau leicht variieren,
        # aber weiterhin im Schachbrett-Raster bleiben.
        self.diagonal_offset = random.randint(0, 3)

        available = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if (row, col) in self.tried_positions:
                    continue
                cell = board.get_cell(row, col)
                if cell and not cell.is_shot():
                    available.append((row, col))

        parity_cells = [
            pos for pos in available
            if (pos[0] + pos[1] + self.parity_offset) % 2 == 0
        ]

        diagonal_cells = [
            pos for pos in parity_cells
            if (pos[0] - pos[1] - self.diagonal_offset) % 4 == 0
        ]

        # Nicht direkt neben bekannten Misses bevorzugen,
        # um "miss-clumping" im Hunt-Mode zu reduzieren.
        diagonal_not_adjacent_to_miss = [
            pos for pos in diagonal_cells
            if not self._is_adjacent_to_miss(board, pos[0], pos[1])
        ]
        parity_not_adjacent_to_miss = [
            pos for pos in parity_cells
            if not self._is_adjacent_to_miss(board, pos[0], pos[1]) and pos not in diagonal_cells
        ]

        diagonal_rest = [pos for pos in diagonal_cells if pos not in diagonal_not_adjacent_to_miss]
        parity_rest = [pos for pos in parity_cells if
                       pos not in diagonal_cells and pos not in parity_not_adjacent_to_miss]

        # Reihenfolge absichtlich zufällig, aber mit Priorität:
        # 1) Diagonalraster ohne Miss-Nachbarn
        # 2) übrige Parity-Felder ohne Miss-Nachbarn
        # 3) Diagonalraster mit Miss-Nachbarn
        # 4) übrige Parity-Felder mit Miss-Nachbarn
        random.shuffle(diagonal_not_adjacent_to_miss)
        random.shuffle(parity_not_adjacent_to_miss)
        random.shuffle(diagonal_rest)
        random.shuffle(parity_rest)

        self.hunt_queue = (
                diagonal_not_adjacent_to_miss +
                parity_not_adjacent_to_miss +
                diagonal_rest +
                parity_rest
        )

    def _is_adjacent_to_miss(self, board, row, col):
        """Prüft, ob die Zelle orthogonal an einen Fehlschuss grenzt."""
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            check_row = row + dr
            check_col = col + dc
            if 0 <= check_row < GRID_SIZE and 0 <= check_col < GRID_SIZE:
                neighbor = board.get_cell(check_row, check_col)
                if neighbor and neighbor.is_miss():
                    return True
        return False

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
            if (row, col) not in self.hit_sequence:
                self.hit_sequence.append((row, col))

            if destroyed:
                # Schiff versenkt: Zurück zum Suchmodus
                self._mark_destroyed_ship_surroundings(ship)
                self._switch_to_hunt_mode()
            else:
                # Treffer aber nicht versenkt: Wechsel zum Zielmodus
                self._switch_to_target_mode(row, col)
        elif self.mode == self.MODE_TARGET and self.hit_sequence:
            # Fehlschuss im Zielmodus: verbleibende Treffer weiter auswerten
            self._rebuild_targets_from_hits()

    def _switch_to_target_mode(self, row, col):
        """
        Wechselt in den Zielmodus nach einem Treffer

        Args:
            row: Zeile des Treffers
            col: Spalte des Treffers
        """
        self.mode = self.MODE_TARGET
        self._rebuild_targets_from_hits()

    def _switch_to_hunt_mode(self):
        """Wechselt zurück in den Suchmodus"""
        self.mode = self.MODE_HUNT
        self.possible_targets = []
        self.hit_sequence = []
        self.last_hit = None

        # Nach versenktem Schiff Hunt-Raster neu aufbauen
        self._refresh_hunt_pattern()
        self.hunt_queue = []

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

    def _rebuild_targets_from_hits(self):
        """Berechnet Ziele aus bekannten Treffern neu."""
        self.possible_targets = []

        if not self.hit_sequence:
            return

        if len(self.hit_sequence) == 1:
            hit_row, hit_col = self.hit_sequence[0]
            self._add_adjacent_targets(hit_row, hit_col)
            return

        same_row = all(hit[0] == self.hit_sequence[0][0] for hit in self.hit_sequence)
        same_col = all(hit[1] == self.hit_sequence[0][1] for hit in self.hit_sequence)

        if same_row:
            current_row = self.hit_sequence[0][0]
            cols = sorted(hit[1] for hit in self.hit_sequence)
            candidate_positions = [(current_row, cols[0] - 1), (current_row, cols[-1] + 1)]
        elif same_col:
            current_col = self.hit_sequence[0][1]
            rows = sorted(hit[0] for hit in self.hit_sequence)
            candidate_positions = [(rows[0] - 1, current_col), (rows[-1] + 1, current_col)]
        else:
            # Sicherheitsnetz: Falls eine inkonsistente Sequenz entsteht,
            # betrachten wir weiterhin alle Nachbarfelder.
            for hit_row, hit_col in self.hit_sequence:
                self._add_adjacent_targets(hit_row, hit_col)
            return

        for candidate in candidate_positions:
            self._append_target_if_valid(*candidate)

    def _append_target_if_valid(self, row, col):
        """Fügt ein Ziel hinzu, falls es im Spielfeld und noch nicht versucht ist."""
        if (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE and
                (row, col) not in self.tried_positions and
                (row, col) not in self.possible_targets):
            self.possible_targets.append((row, col))

    def _mark_destroyed_ship_surroundings(self, ship):
        """Markiert Nachbarfelder des versenkten Schiffs als irrelevant."""
        if not ship:
            return

        for ship_cell in ship.cells:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    neighbor_row = ship_cell.row + dr
                    neighbor_col = ship_cell.col + dc
                    if 0 <= neighbor_row < GRID_SIZE and 0 <= neighbor_col < GRID_SIZE:
                        self.tried_positions.add((neighbor_row, neighbor_col))

    def _refresh_hunt_pattern(self):
        """Mischt das Hunt-Muster neu für weniger Vorhersagbarkeit."""
        self.parity_offset = random.randint(0, 1)
        self.diagonal_offset = random.randint(0, 3)

    def reset(self):
        """Setzt die KI zurück"""
        self.mode = self.MODE_HUNT
        self.possible_targets = []
        self.last_hit = None
        self.hit_sequence = []
        self.tried_positions = set()
        self._refresh_hunt_pattern()
        self.hunt_queue = []

    def __repr__(self):
        return f"ComputerAI(mode={self.mode}, targets={len(self.possible_targets)}, hits={len(self.hit_sequence)})"