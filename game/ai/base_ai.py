"""Parent class mit Basislogik für Computer-KIs."""

import random
from game.config import GRID_SIZE


class BaseComputerAI:
    MODE_HUNT = "hunt"
    MODE_TARGET = "target"

    def __init__(self):
        self.mode = self.MODE_HUNT
        self.possible_targets = []
        self.tried_positions = set()
        self.unresolved_hits = set()
        self.known_ship_cells = set()  # noch nicht beschossene Sonar-Marks
        self.sonar_miss_positions = set()

    def choose_action(self, board):
        """Wird von Unterklassen überschrieben. Rückgabe: dict(type=..., row=..., col=...)."""
        row, col = self.get_next_shot(board)
        return {"type": "shoot", "row": row, "col": col}

    def register_sonar_findings(self, found_positions):
        for pos in found_positions:
            self.sonar_miss_positions.discard(pos)
            if pos not in self.tried_positions:
                self.known_ship_cells.add(pos)

    def register_sonar_misses(self, miss_positions):
        for pos in miss_positions:
            if pos in self.tried_positions or pos in self.known_ship_cells:
                continue
            self.sonar_miss_positions.add(pos)

    def get_next_shot(self, board):
        if self.mode == self.MODE_TARGET:
            if not self.possible_targets and self._has_pending_target_info():
                self._rebuild_targets_from_hits()
            if self.possible_targets:
                return self._pop_next_target(board)

        sonar_target = self._pop_known_ship_target(board)
        if sonar_target:
            self.mode = self.MODE_TARGET
            return sonar_target

        return self._get_hunt_shot(board)

    def _has_pending_target_info(self):
        return bool(self.unresolved_hits or self.known_ship_cells)

    def _get_hunt_shot(self, board):
        raise NotImplementedError

    def _available_positions(self, board):
        available = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if (row, col) in self.tried_positions:
                    continue
                if (row, col) in self.sonar_miss_positions:
                    continue
                cell = board.get_cell(row, col)
                if cell and not cell.is_shot():
                    available.append((row, col))
        return available

    def _pop_known_ship_target(self, board):
        candidates = [
            pos for pos in self.known_ship_cells
            if pos not in self.tried_positions and board.get_cell(*pos) and not board.get_cell(*pos).is_shot()
        ]
        if not candidates:
            self.known_ship_cells = set()
            return None
        shot = random.choice(candidates)
        self.known_ship_cells.discard(shot)
        self.tried_positions.add(shot)
        return shot

    def _pop_next_target(self, board):
        while self.possible_targets:
            shot = self.possible_targets.pop(0)
            if shot in self.tried_positions:
                continue
            cell = board.get_cell(*shot)
            if cell and not cell.is_shot() and shot not in self.sonar_miss_positions:
                self.tried_positions.add(shot)
                return shot

        self.mode = self.MODE_HUNT
        return self._get_hunt_shot(board)

    def register_shot_result(self, row, col, hit, destroyed, ship):
        self.tried_positions.add((row, col))
        self.known_ship_cells.discard((row, col))
        self.sonar_miss_positions.discard((row, col))

        if hit:
            self.unresolved_hits.add((row, col))
            if destroyed and ship:
                for ship_cell in ship.cells:
                    self.unresolved_hits.discard((ship_cell.row, ship_cell.col))
                self._mark_destroyed_ship_surroundings(ship)

        self._rebuild_targets_from_hits()

    def _rebuild_targets_from_hits(self):
        self.possible_targets = []

        # Sonar-Hinweise immer zuerst priorisieren
        for sonar_pos in list(self.known_ship_cells):
            self._append_target_if_valid(*sonar_pos)

        hit_clusters = self._get_hit_clusters()
        if not hit_clusters and not self.possible_targets:
            self.mode = self.MODE_HUNT

        self.mode = self.MODE_TARGET
        for cluster in sorted(hit_clusters, key=len, reverse=True):
            same_row = len({r for r, _ in cluster}) == 1
            same_col = len({c for _, c in cluster}) == 1

            if len(cluster) >= 2 and (same_row or same_col):
                if same_row:
                    row = cluster[0][0]
                    cols = sorted(c for _, c in cluster)
                    self._append_target_if_valid(row, cols[0] - 1)
                    self._append_target_if_valid(row, cols[-1] + 1)
                else:
                    col = cluster[0][1]
                    rows = sorted(r for r, _ in cluster)
                    self._append_target_if_valid(rows[0] - 1, col)
                    self._append_target_if_valid(rows[-1] + 1, col)

            # Für L-/Carrier-Formen: um jeden bekannten Treffer herum prüfen
            neighbor_candidates = []
            for row, col in cluster:
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    neighbor_candidates.append((row + dr, col + dc))

            random.shuffle(neighbor_candidates)
            for cand_row, cand_col in neighbor_candidates:
                self._append_target_if_valid(cand_row, cand_col)

    def _get_hit_clusters(self):
        remaining_hits = set(self.unresolved_hits)
        clusters = []

        while remaining_hits:
            start = remaining_hits.pop()
            stack = [start]
            cluster = {start}

            while stack:
                row, col = stack.pop()
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    neighbor = (row + dr, col + dc)
                    if neighbor in remaining_hits:
                        remaining_hits.remove(neighbor)
                        cluster.add(neighbor)
                        stack.append(neighbor)

            clusters.append(sorted(cluster))

        return clusters

    def _append_target_if_valid(self, row, col):
        if (
            0 <= row < GRID_SIZE
            and 0 <= col < GRID_SIZE
            and (row, col) not in self.tried_positions
            and (row, col) not in self.possible_targets
            and (row, col) not in self.sonar_miss_positions
        ):
            self.possible_targets.append((row, col))

    def _mark_destroyed_ship_surroundings(self, ship):
        if not ship:
            return

        for ship_cell in ship.cells:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr = ship_cell.row + dr
                    nc = ship_cell.col + dc
                    if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                        self.tried_positions.add((nr, nc))
                        self.known_ship_cells.discard((nr, nc))
                        #self.sonar_miss_positions.discard((nr, nc))

    def reset(self):
        self.mode = self.MODE_HUNT
        self.possible_targets = []
        self.tried_positions = set()
        self.unresolved_hits = set()
        self.known_ship_cells = set()
        self.sonar_miss_positions = set()

    def __repr__(self):
        return f"{self.__class__.__name__}(mode={self.mode}, targets={len(self.possible_targets)}, unresolved={len(self.unresolved_hits)})"