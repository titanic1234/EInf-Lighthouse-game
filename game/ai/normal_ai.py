"""Standard KI, Hunt raster und random abilities"""

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
        available_abilities = [name for name, charges in self.abilities.items() if charges > 0]
        if available_abilities and random.random() < 0.35:
            ability = random.choice(available_abilities)
            self.abilities[ability] -= 1
            row, col = self._random_untried(board)
            return {"type": ability, "row": row, "col": col}

        row, col = self.get_next_shot(board)
        return {"type": "shoot", "row": row, "col": col}

    def _random_untried(self, board):
        available = self._available_positions(board)
        if not available:
            return random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        return random.choice(available)

    def _get_hunt_shot(self, board):
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