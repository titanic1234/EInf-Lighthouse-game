# create_game.py

import pygame
from pgzero.keyboard import keys
from pgzero.builtins import keymods

import game.config as config
import game.multiplayer.multiplayer_config as mconfig

from game.states.multiplayer_lobby import MultiplayerLobbyState

class CreateGameState(MultiplayerLobbyState):
    """Multiplayer: Create Game Screen (Name + RoomCode + Start/Back)"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ---- Field State ----
        self.room_locked = True  # gesperrt: kann nur kopiert werden, nicht bearbeitet

        # ---- Clipboard / Toast ----
        self.clipboard_ok = True
        try:
            pygame.scrap.init()
        except Exception:
            self.clipboard_ok = False

        self.toast_text = ""
        self.toast_timer = 0.0

        self.text = "Create Game"

        self._create_game_buttons(text=self.text)


    # ------------------------------
    # Button clicked
    # ------------------------------
    def _start_game(self):
        mconfig.change_vars(name=self.name_text)
        self.game_manager.change_state(config.STATE_MULTIPLAYER_PLACEMENT)


    # ------------------------------
    # Copy / Toast
    # ------------------------------
    def _show_copy_toast(self, text: str, duration: float = 2.0):
        self.toast_text = text
        self.toast_timer = duration

    def _copy_room_code(self):
        code = (self.room_text or "").strip()
        if not code or code.lower() == "waiting...":
            self._show_copy_toast("Noch kein Code verfügbar")
            return

        if not self.clipboard_ok:
            self._show_copy_toast("Clipboard nicht verfügbar")
            return

        try:
            pygame.scrap.put(pygame.SCRAP_TEXT, code.encode("utf-8"))
            self._show_copy_toast("Code kopiert!")
        except Exception:
            self._show_copy_toast("Kopieren fehlgeschlagen")


    # ------------------------------
    # Update
    # ------------------------------
    def update(self, dt, mouse_pos):
        self.cursor_t += dt
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_text = ""

        if mconfig.CODE is not None:
            self.room_text = str(mconfig.CODE)

        mx, my = mouse_pos
        for button in self.buttons:
            button.update(dt, mx, my)

        if self.room_text is None and mconfig.CODE is not None:
            self.room_text = str(mconfig.CODE)
            self.text_fields[1].text = self.room_text


    # ------------------------------
    # Draw / Toast
    # ------------------------------
    def draw(self, screen):
        super().draw(screen)

        if self.toast_text:
            toast_font = pygame.font.Font(None, config.FONT_SIZE_MEDIUM)
            toast = toast_font.render(self.toast_text, True, config.COLOR_WHITE)
            toast_rect = toast.get_rect(center=(config.WINDOW_WIDTH // 2, self.room_rect.bottom + 70))

            pad_x, pad_y = 18, 10
            bg_rect = pygame.Rect(
                toast_rect.x - pad_x,
                toast_rect.y - pad_y,
                toast_rect.w + 2 * pad_x,
                toast_rect.h + 2 * pad_y,
            )
            pygame.draw.rect(screen, (10, 16, 28), bg_rect, border_radius=12)
            pygame.draw.rect(screen, config.COLOR_BLUE, bg_rect, width=2, border_radius=12)
            screen.blit(toast, toast_rect)