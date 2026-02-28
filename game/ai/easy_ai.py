"""Easy KI, keine Abilities und random shots"""

import random
from game.ai.base_ai import BaseComputerAI


class EasyComputerAI(BaseComputerAI):
    def _get_hunt_shot(self, board):
        available = self._available_positions(board)
        if not available:
            return random.randint(0, 11), random.randint(0, 11)

        shot = random.choice(available)
        self.tried_positions.add(shot)
        return shot