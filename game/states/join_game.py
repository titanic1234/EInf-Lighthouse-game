# join_game.py

from pgzero.keyboard import keys
from pgzero.builtins import keymods

import game.config as config

from game.multiplayer.communication import join_game as join_game_request

from game.states.multiplayer_lobby import MultiplayerLobbyState


class JoinGameState(MultiplayerLobbyState):
    """Multiplayer: Join Game Screen (Name + RoomCode + Join/Back)"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ---- Field State ----
        self.room_locked = False

        self.toast_text = ""
        self.toast_timer = 0.0

        self.text = "Join Game"

        self._create_game_buttons(text=self.text)


    # ------------------------------
    # Button clicked
    # ------------------------------
    def _start_game(self):
        fehler = join_game_request(code=self.room_text, name=self.name_text)
        if not fehler:
            self.game_manager.change_state(config.STATE_MULTIPLAYER_PLACEMENT)

        else:
            # TODO: Fehlermeldung anzeigen
            text = f"Fehler beim Join: {fehler}"
            self._show_toast(text)
            self.game_manager.change_state(config.STATE_MULTIPLAYER_MENU)


    # ------------------------------
    # Toast
    # ------------------------------
    def _show_toast(self, text: str, duration: float = 2.0):
        self.toast_text = text
        self.toast_timer = duration


    # ------------------------------
    # Update
    # ------------------------------
    def update(self, dt, mouse_pos):
        self.cursor_t += dt

        # Join nur aktiv, wenn Code 6-stellig ist
        code_ok = (len(self.room_text) == self.room_max_len)
        self.buttons[0].enabled = code_ok  # GlowButton muss enabled unterstützen; falls nicht, siehe Hinweis unten.

        mx, my = mouse_pos
        for button in self.buttons:
            button.update(dt, mx, my)