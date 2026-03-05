from game.ai.easy_ai import EasyComputerAI
from game.ai.normal_ai import NormalComputerAI
from game.ai.hard_ai import HardComputerAI


def create_ai(difficulty):
    #Setzt AI difficulty, default normal
    key = (difficulty or "normal").lower()
    if key == "easy":
        return EasyComputerAI()
    if key == "hard":
        return HardComputerAI()
    return NormalComputerAI()