"""ez AI: keine Abilities, random shots"""

import random
from game.ai.base_ai import BaseComputerAI
from game.config import GRID_SIZE


class EasyComputerAI(BaseComputerAI):
    def _get_hunt_shot(self, board):
        #hunt random, target wie in base
        available = self._available_positions(board)
        if not available:
            return random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)

        shot = random.choice(available)
        self.tried_positions.add(shot)
        return shot
