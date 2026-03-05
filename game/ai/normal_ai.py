"""Standard AI: Hunt raster, random abilities, smarteres placement"""

import random
from game.config import GRID_SIZE
from game.ai.base_ai import BaseComputerAI


class NormalComputerAI(BaseComputerAI):
    DEFAULT_ABILITIES = {"airstrike": 1, "guided": 1, "sonar": 1, "napalm": 1,}

    def __init__(self):
        super().__init__()
        self.parity_offset = random.randint(0, 1)
        self.diagonal_offset = random.randint(0, 3)
        self.hunt_queue = []
        self.abilities = dict(self.DEFAULT_ABILITIES)

    def choose_action(self, board):
        # random ability oder standard hunt/target
        available_abilities = [name for name, charges in self.abilities.items() if charges > 0]
        if available_abilities and random.random() < 0.35:
            ability = random.choice(available_abilities)
            self.abilities[ability] -= 1
            row, col = self._random_untried(board)
            return {"type": ability, "row": row, "col": col}

        row, col = self.get_next_shot(board)
        return {"type": "shoot", "row": row, "col": col}

    def _choose_ship_placement(self, board, ship):
        # priorisiert Abstand um double-hits gegn. abilities zu vermindern
        placements = self._collect_possible_placements(board, ship)
        if not placements:
            return None

        occupied_cells = self._occupied_ship_cells(board)
        if not occupied_cells:
            return random.choice(placements)

        # weights so nach Gefühl weil kein bock zu testen xD
        spread_weight = random.uniform(1.7, 3.4)
        noise = random.uniform(1.5, 2.5)

        # grade placement möglichkeiten nach distanz zu anderen
        scored = []
        for row, col, orientation in placements:
            coordinates = ship.get_coordinates_at(row, col, orientation)
            score = spread_weight * self._distance_to_other_ships(coordinates, occupied_cells)
            score += random.uniform(-noise, noise)
            scored.append((score, row, col, orientation))

        scored.sort(key=lambda item: item[0], reverse=True)
        top_pool_size = min(max(4, len(scored) // 5), len(scored))
        top_pool = scored[:top_pool_size]
        chosen = random.choice(top_pool)
        return chosen[1], chosen[2], chosen[3]

    def _distance_to_other_ships(self, coordinates, occupied_cells):
        total = 0
        for row, col in coordinates:
            nearest = min(abs(row - other_row) + abs(col - other_col) for other_row, other_col in occupied_cells)
            total += nearest
        return total / max(1, len(coordinates))

    def _random_untried(self, board):
        # fallback auf random shot
        available = self._available_positions(board)
        if not available:
            return random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        return random.choice(available)

    def _get_hunt_shot(self, board):
        #folgt hunt-muster aus hunt queue, random wenn nicht möglich
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

        available = self._available_positions(board)
        shot = random.choice(available)
        self.tried_positions.add(shot)
        return shot

    def _rebuild_hunt_queue(self, board):
        #Schachbrettraster mit prio einer diagonalen für flächendeckung
        self.diagonal_offset = random.randint(0, 3)

        available = self._available_positions(board)
        parity_cells = [pos for pos in available if (pos[0] + pos[1] + self.parity_offset) % 2 == 0]
        diagonal_cells = [pos for pos in parity_cells if (pos[0] - pos[1] - self.diagonal_offset) % 4 == 0]

        random.shuffle(diagonal_cells)
        remainder = [pos for pos in parity_cells if pos not in diagonal_cells]
        random.shuffle(remainder)

        self.hunt_queue = diagonal_cells + remainder

    def reset(self):
        super().reset()
        self.hunt_queue = []
        self.parity_offset = random.randint(0, 1)
        self.diagonal_offset = random.randint(0, 3)
        self.abilities = dict(self.DEFAULT_ABILITIES)