"""
Schiffe Versenken - Main Entry Point
Pygame Zero Game

Starte mit: pgzrun main.py
"""

import pgzrun
from game.game_manager import GameManager
from game.config import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE

# Fensterkonfiguration
WIDTH = WINDOW_WIDTH
HEIGHT = WINDOW_HEIGHT
TITLE = TITLE

# Game-Manager initialisieren
game_manager = GameManager()


def update(dt):
    """
    Pygame Zero Update-Funktion
    Wird jeden Frame aufgerufen

    Args:
        dt: Delta-Zeit seit letztem Frame
    """
    mouse_pos = (0, 0)
    try:
        import pygame
        mouse_pos = pygame.mouse.get_pos()
    except:
        pass

    game_manager.update(dt, mouse_pos)


def draw():
    """
    Pygame Zero Draw-Funktion
    Zeichnet den aktuellen Frame
    """
    game_manager.draw(screen)


def on_mouse_down(pos, button):
    """
    Pygame Zero Mouse-Event
    Wird bei Mausklick aufgerufen

    Args:
        pos: Position (x, y)
        button: Maustaste (mouse.LEFT, mouse.MIDDLE, mouse.RIGHT)
    """
    button_num = 1 if button == 1 else (2 if button == 2 else 3)
    game_manager.on_mouse_down(pos, button_num)


def on_key_down(key):
    """
    Pygame Zero Keyboard-Event
    Wird bei Tastendruck aufgerufen

    Args:
        key: Gedrueckte Taste
    """
    game_manager.on_key_down(key)


# Starte das Spiel
pgzrun.go()
