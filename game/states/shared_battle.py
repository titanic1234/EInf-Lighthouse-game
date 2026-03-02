# shared_battle.py
"""Gemeinsame Battle-Logik für Singleplayer und Multiplayer."""


import os
import random
import pygame
from pygame import Rect

import game.config as config
import game.multiplayer.multiplayer_config as mconfig
from game.config import CELL_HIT, CELL_MISS  # CELL_DESTROYED ist in Cell.mark_destroyed()

from game.entities.board import Board

from game.ai import create_ai

from game.theme import theme_manager

from game.states.base_state import BaseState

from game.graphics import (
    draw_gradient_background,
    draw_rounded_rect,
    ParticleSystem,
    draw_text,
    draw_grid_cell,
)



class SharedBattleState(BaseState):
    """Gemeinsame UI/Input-Logik für Battle."""


    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.player_board = self.game_manager.player_board

        # Effekte
        self.particles = ParticleSystem()

        # Specials UI
        self.abilities = {
            "airstrike": {"charges": 1, "targeted": True},
            "guided": {"charges": 1, "targeted": False},
            "sonar": {"charges": 1, "targeted": True},
            "napalm": {"charges": 1, "targeted": True},
        }

        self.selected_ability = None
        self.active_fires = []
        self.ability_buttons = []
        self._load_ability_icons()
        self._rebuild_ability_buttons()



    def _load_icon(self, filename):
        path = os.path.join("images", filename)
        if not os.path.exists(path):
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None


    def _load_ability_icons(self):
        is_modern = theme_manager.current.name == "MODERN"
        self.ability_icons = {
            "airstrike": self._load_icon("airstrike.png" if is_modern else "breitseite.png"),
            "guided": self._load_icon("lenkrakete.png" if is_modern else "enterhaken.png"),
            "sonar": self._load_icon("sonar.png" if is_modern else "Kraehennest.png"),
            "napalm": self._load_icon("napalm.png" if is_modern else "griechisches_feuer.png"),
        }

    def _rebuild_ability_buttons(self):
        size = 64
        spacing = 20
        total_width = size * 4 + spacing * 3
        start_x = config.WINDOW_WIDTH // 2 - total_width // 2
        y = config.WINDOW_HEIGHT - 90

        names = ["airstrike", "guided", "sonar", "napalm"]
        self.ability_buttons = []
        for idx, name in enumerate(names):
            rect = pygame.Rect(start_x + idx * (size + spacing), y, size, size)
            self.ability_buttons.append((name, rect))