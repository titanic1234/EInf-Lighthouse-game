"""Schwere KI. Logik für abilities, angepasstes Suchraster, Placement logik"""

import random
from game.config import GRID_SIZE
from game.ai.normal_ai import NormalComputerAI


class HardComputerAI(NormalComputerAI):
    def __init__(self):
        super().__init__()
        self.hide_small_ship_remaining = 0

    def place_ships(self, board):
        # Nicht jedes Spiel gleich: kleines Schiff nur manchmal bewusst verstecken.
        self.hide_small_ship_remaining = 1 if random.random() < 0.35 else 0
        super().place_ships(board)

    def _choose_ship_placement(self, board, ship):
        placements = self._collect_possible_placements(board, ship)
        if not placements:
            return None

        occupied_cells = self._occupied_ship_cells(board)
        if not occupied_cells:
            return random.choice(placements)

        spread_weight = random.uniform(2.2, 3.4)
        edge_weight = random.uniform(2.8, 4.2)
        noise = random.uniform(1.0, 2.0)
        hide_weight = random.uniform(1.1, 1.9)

        scored = []
        for row, col, orientation in placements:
            coordinates = ship.get_coordinates_at(row, col, orientation)
            score = spread_weight * self._distance_to_other_ships(coordinates, occupied_cells)
            score += edge_weight * self._distance_to_edge(coordinates)

            if self.hide_small_ship_remaining > 0 and ship.get_size() <= 3:
                score += hide_weight * self._small_ship_hide_bonus(coordinates, occupied_cells)

            score += random.uniform(-noise, noise)
            scored.append((score, row, col, orientation))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_pool_size = min(max(4, len(scored) // 5), len(scored))
        top_pool = scored[:top_pool_size]
        chosen = random.choice(top_pool)
        chosen_coords = ship.get_coordinates_at(chosen[1], chosen[2], chosen[3])

        if self.hide_small_ship_remaining > 0 and ship.get_size() <= 3:
            if self._small_ship_hide_bonus(chosen_coords, occupied_cells) > 0.2:
                self.hide_small_ship_remaining -= 1

        return chosen[1], chosen[2], chosen[3]

    def _distance_to_edge(self, coordinates):
        edge_distances = [
            min(row, col, GRID_SIZE - 1 - row, GRID_SIZE - 1 - col)
            for row, col in coordinates
        ]
        return sum(edge_distances) / max(1, len(edge_distances))

    def _small_ship_hide_bonus(self, coordinates, occupied_cells):
        if not occupied_cells:
            return 0.0

        near_edge_cells = sum(
            1
            for row, col in coordinates
            if min(row, col, GRID_SIZE - 1 - row, GRID_SIZE - 1 - col) <= 1
        )
        nearest = min(
            abs(row - other_row) + abs(col - other_col)
            for row, col in coordinates
            for other_row, other_col in occupied_cells
        )

        edge_factor = near_edge_cells / max(1, len(coordinates))
        near_ship_factor = max(0.0, 4.0 - nearest) / 4.0
        return edge_factor + near_ship_factor

    def choose_action(self, board):
        # Guided missile zum finden neuer targets einsetzen
        if self.abilities["guided"] > 0 and self._should_use_guided(board):
            self.abilities["guided"] -= 1
            row, col = self._random_untried(board)
            return {"type": "guided", "row": row, "col": col}

        # Sonar früh einsetzen, um schnell Zielzellen zu markieren
        if self.abilities["sonar"] > 0:
            self.abilities["sonar"] -= 1
            row, col = self._best_sonar_center(board)
            return {"type": "sonar", "row": row, "col": col}

        # Airstrike auf unbeschossenes Gebiet
        if self.abilities["airstrike"] > 0:
            self.abilities["airstrike"] -= 1
            row, col = self._best_airstrike_center(board)
            return {"type": "airstrike", "row": row, "col": col}

        # Napalm optional in der Suche; danach nicht auf markierte Felder schießen
        if self.abilities["napalm"] > 0 and self.mode == self.MODE_HUNT and random.random() < 0.3:
            self.abilities["napalm"] -= 1
            row, col = self._best_hunt_cell(board)
            return {"type": "napalm", "row": row, "col": col}

        row, col = self.get_next_shot(board)
        return {"type": "shoot", "row": row, "col": col}

    def _should_use_guided(self, board):
        """Nutze guided missile nur für 2x1 oder um neues ship zu finden"""
        remaining = [ship for ship in board.ships if not ship.is_destroyed()]
        two_cell_remaining = [ship for ship in remaining if ship.get_size() == 2]
        all_except_two_destroyed = len(remaining) == 1 and len(two_cell_remaining) == 1

        if all_except_two_destroyed:
            return True

        two_cell_destroyed = any(
            ship.get_size() == 2 and ship.is_destroyed() for ship in board.ships
        )
        if two_cell_destroyed and not self._has_open_targets(board):
            return True

        return False

    def _has_open_targets(self, board):
        if self.known_ship_cells:
            return True

        for hit_row, hit_col in self.unresolved_hits:
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nr, nc = hit_row + dr, hit_col + dc
                cell = board.get_cell(nr, nc)
                if not cell or cell.is_shot():
                    continue
                if (nr, nc) in self.tried_positions or (nr, nc) in self.sonar_miss_positions:
                    continue
                return True

        return False

    def _best_sonar_center(self, board):
        best_cells = []
        best_score = -1
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                score = 0
                for r in range(row - 1, row + 2):
                    for c in range(col - 1, col + 2):
                        cell = board.get_cell(r, c)
                        if cell and not cell.is_shot() and (r, c) not in self.tried_positions and (r, c) not in self.sonar_miss_positions:
                            score += 1
                if score > best_score:
                    best_cells = [(row, col)]
                    best_score = score
                elif score == best_score:
                    best_cells.append((row, col))
        if best_cells:
            return random.choice(best_cells)
        return random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)

    def _best_airstrike_center(self, board):
        best = None
        best_score = -1
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                score = 0
                for r, c in ((row, col), (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                    cell = board.get_cell(r, c)
                    if cell and not cell.is_shot() and not cell.napalm_marked:
                        score += 1
                if score > best_score:
                    best = (row, col)
                    best_score = score
        return best if best else (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))

    def _best_hunt_cell(self, board):
        candidates = [
            (r, c)
            for r, c in self._available_positions(board)
            if not board.get_cell(r, c).napalm_marked
        ]
        return random.choice(candidates) if candidates else self._random_untried(board)

    def _get_hunt_shot(self, board):
        if not self.hunt_queue:
            self._rebuild_hunt_queue(board)

        while self.hunt_queue:
            shot = self.hunt_queue.pop(0)
            if shot in self.tried_positions:
                continue
            cell = board.get_cell(*shot)
            if cell and not cell.is_shot() and not cell.napalm_marked:
                self.tried_positions.add(shot)
                return shot

        return self._best_hunt_cell(board)

    def _rebuild_hunt_queue(self, board):
        # Raster mit Abstand 2 (mod 3), um größere Fläche abzudecken
        offset = random.randint(0, 2)
        candidates = []
        for row, col in self._available_positions(board):
            if board.get_cell(row, col).napalm_marked:
                continue
            if (row + col + offset) % 3 == 0:
                candidates.append((row, col))

        random.shuffle(candidates)
        fallback = [
            pos for pos in self._available_positions(board)
            if pos not in candidates and not board.get_cell(*pos).napalm_marked
        ]
        random.shuffle(fallback)
        self.hunt_queue = candidates + fallback