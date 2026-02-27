import pgzrun
import pygame
import game.config as config
from game.game_manager import GameManager
from game.multiplayer.communication import _start_check_connection_thread
global WIDTH, HEIGHT
WIDTH = config.WINDOW_WIDTH
HEIGHT = config.WINDOW_HEIGHT
TITLE = config.TITLE
DISPLAY_FLAGS = pygame.RESIZABLE if config.WINDOW_RESIZABLE else 0


_start_check_connection_thread()

game_manager = GameManager()

def update():
    mouse_position = pygame.mouse.get_pos()
    try:
        if not config.WINDOW_FULLSCREEN and not config.WINDOW_FULLSCREEN_CHANGED:
            screen.surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
            config.update_fullscreen(True, False)
    except pygame.error:
        print("Display was closed")
    # Simple 60fps dt
    dt = 1 / 60.0
    game_manager.update(dt, mouse_position)

def draw():
    screen.surface.fill((0, 0, 0))
    game_manager.draw(screen.surface)

def on_mouse_down(pos, button):
    game_manager.on_mouse_down(pos, button)

def on_key_down(key):
    game_manager.on_key_down(key)
    if key == pygame.K_ESCAPE:
        import sys
        sys.exit()
    elif key == pygame.K_F11:
        try:
            if not config.WINDOW_FULLSCREEN:
                screen.surface = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                config.update_fullscreen(True, True)
            else:
                screen.surface = pygame.display.set_mode((WIDTH, HEIGHT), DISPLAY_FLAGS)
                config.update_fullscreen(False, True)
        except pygame.error:
            print("Display was closed")



pgzrun.go()

