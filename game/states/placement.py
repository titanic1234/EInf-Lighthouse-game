"""Schiffsplatzierung (Single Player)"""

import game.config as config
from game.states.shared_placement import SharedPlacementState


class PlacementState(SharedPlacementState):
    """Schiffsplatzierungs-Phase"""

    title_text = "SCHIFFE PLATZIEREN"

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.start_button = self.build_primary_action_button("GEFECHT STARTEN", self._start_battle, y_offset=30)

    def _start_battle(self):
        """Startet die Kampfphase"""
        if not self._all_ships_placed():
            return

        self.player_board.all_ships_placed = True
        self.game_manager.player_board = self.player_board
        self.game_manager.change_state(config.STATE_BATTLE)

    def _update_action_buttons(self, dt, mouse_pos):
        self.start_button.update(dt, mouse_pos[0], mouse_pos[1])

    def _handle_action_button_click(self, pos):
        if self._all_ships_placed() and self.start_button.is_hovered(pos[0], pos[1]):
            self.start_button.click()
            return True
        return False


    def _draw_action_buttons(self, screen):
        if self._all_ships_placed():
            self.start_button.draw(screen, default_color=(30, 110, 70), hover_color=(50, 170, 100))

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.start_button = self.build_primary_action_button("GEFECHT STARTEN", self._start_battle, y_offset=30)