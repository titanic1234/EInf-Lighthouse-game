# main.py

import sys

import pgzrun
import pygame
from pgzero.keyboard import keys

import game.config as config
from game.game_manager import GameManager
from game.multiplayer.communication import _start_check_connection_thread

WIDTH = config.WINDOW_WIDTH
HEIGHT = config.WINDOW_HEIGHT
TITLE = config.TITLE
DISPLAY_FLAGS = pygame.RESIZABLE if config.WINDOW_RESIZABLE else 0

_start_check_connection_thread()
game_manager = GameManager()
mouse_position = (0, 0)



# Wechsel Fullscree - Resizable
def _set_window_mode(windowed: bool):
    flags = pygame.FULLSCREEN if not windowed else DISPLAY_FLAGS
    screen.surface = pygame.display.set_mode((WIDTH, HEIGHT), flags)


# ------------------------------
# Update
# ------------------------------
def update():
    global mouse_position
    try:
        if not config.WINDOW_FULLSCREEN and not config.WINDOW_FULLSCREEN_CHANGED:
            _set_window_mode(False)
            config.update_fullscreen(True, False)
    except pygame.error:
        print("Display was closed")
    # Simple 60fps dt
    dt = 1 / 60.0
    game_manager.update(dt, mouse_position)

# ------------------------------
# Draw
# ------------------------------
def draw():
    screen.surface.fill((0, 0, 0))
    game_manager.draw(screen.surface)


# ------------------------------
# Events
# ------------------------------
def on_mouse_move(pos, rel, buttons):
    del rel, buttons
    global mouse_position
    mouse_position = pos


def on_mouse_down(pos, button):
    global mouse_position
    game_manager.on_mouse_down(pos, button)


def on_key_down(key, mod=0):
    game_manager.on_key_down(key, mod)
    if key == keys.ESCAPE:
        sys.exit()
    if key == keys.F11:
        try:
            if not config.WINDOW_FULLSCREEN:
                _set_window_mode(False)
                config.update_fullscreen(True, True)
            else:
                _set_window_mode(True)
                config.update_fullscreen(False, True)
        except pygame.error:
            print("Display was closed")


# Start
pgzrun.go()