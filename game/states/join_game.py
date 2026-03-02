# join_game.py

import pygame
from pgzero.keyboard import keys
from pgzero.builtins import keymods
import game.config as config
from game.graphics import draw_gradient_background, GlowButton, draw_title_art
from game.states.base_state import BaseState

import game.multiplayer.multiplayer_config as mconfig


from game.multiplayer.communication import join_game as join_game_request


class JoinGameState(BaseState):
    """Multiplayer: Join Game Screen (Name + RoomCode + Join/Back)"""

    def __init__(self, game_manager):
        super().__init__(game_manager)


        # ---- Field State ----
        self.name_text = mconfig.NAME if mconfig.NAME else ""
        self.name_placeholder = "Spieler"
        self.name_max_len = 16

        self.room_text = mconfig.CODE if mconfig.CODE else ""
        self.room_placeholder = "z.B. 123456"
        self.room_max_len = 6
        self.room_locked = False

        # Fokus: "name" | "room" | None
        self.focus = "name"
        self.cursor_t = 0.0

        # ---- Layout (JOIN GAME über dem Schiff) ----
        center_x = config.WINDOW_WIDTH // 2
        self.field_w = config.MENU_BUTTON_WIDTH
        self.field_h = 70

        ship_center_y = config.MENU_SUBTITLE_Y + 220
        self.heading_y = ship_center_y - 120

        fields_top = ship_center_y + 150
        self.name_rect = pygame.Rect(center_x - self.field_w // 2, fields_top, self.field_w, self.field_h)
        self.room_rect = pygame.Rect(center_x - self.field_w // 2, fields_top + 120, self.field_w, self.field_h)

        self.toast_text = ""
        self.toast_timer = 0.0

        # Buttons
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):
        center_x = config.WINDOW_WIDTH // 2
        start_y = config.MENU_BUTTON_Y

        self.btn_join = GlowButton(
            center_x,
            start_y + config.MENU_BUTTON_SPACING * 2,
            config.MENU_BUTTON_WIDTH,
            config.MENU_BUTTON_HEIGHT,
            "Join Game",
            self._start_game,
        )
        self.btn_back = GlowButton(
            center_x,
            start_y + config.MENU_BUTTON_SPACING * 3,
            config.MENU_BUTTON_WIDTH,
            config.MENU_BUTTON_HEIGHT,
            "Back",
            self._back_menu,
        )

        self.buttons = [self.btn_join, self.btn_back]


    def _show_toast(self, text: str, duration: float = 2.0):
        self.toast_text = text
        self.toast_timer = duration

    def _back_menu(self):
        self.game_manager.change_state(config.STATE_MULTIPLAYER_MENU)

    def _start_game(self):
        fehler = join_game_request(code=self.room_text, name=self.name_text)
        if not fehler:
            self.game_manager.change_state(config.STATE_MULTIPLAYER_PLACEMENT)

        else:
            # TODO: Fehlermeldung anzeigen
            text = f"Fehler beim Join: {fehler}"
            self._show_toast(text)
            #self.game_manager.change_state(config.STATE_MULTIPLAYER_MENU)


    # ---------------- Update / Input ----------------
    def update(self, dt, mouse_pos):
        self.cursor_t += dt

        # Join nur aktiv, wenn Code 6-stellig ist
        code_ok = (len(self.room_text) == self.room_max_len)
        self.btn_join.enabled = code_ok  # GlowButton muss enabled unterstützen; falls nicht, siehe Hinweis unten.

        mx, my = mouse_pos
        for button in self.buttons:
            button.update(dt, mx, my)

    def on_mouse_down(self, pos, button):
        if button != 1:
            return

        if self.name_rect.collidepoint(pos):
            self.focus = "name"
            self.cursor_t = 0.0
            return

        if self.room_rect.collidepoint(pos):
            if not self.room_locked:
                self.focus = "room"
                self.cursor_t = 0.0
            return

        for btn in self.buttons:
            if btn.hovered:
                # falls disabled: nicht klicken
                if hasattr(btn, "enabled") and not btn.enabled:
                    return
                btn.click()
                return

        self.focus = None

    def on_key_down(self, key, mod=0):
        if key == keys.ESCAPE:
            self._back_menu()
            return

        if key in (keys.RETURN, keys.KP_ENTER):
            if len(self.room_text) == self.room_max_len:
                self._start_game()
            return

        if key == keys.TAB:
            if self.room_locked:
                self.focus = "name"
            else:
                self.focus = "room" if self.focus == "name" else "name"
            self.cursor_t = 0.0
            return

        if key == keys.BACKSPACE:
            if self.focus == "name" and self.name_text:
                self.name_text = self.name_text[:-1]
            elif self.focus == "room" and (not self.room_locked) and self.room_text:
                self.room_text = self.room_text[:-1]
            return

        # -------- Texteingabe über KEYDOWN (funktioniert immer) --------
        mods = mod
        if mods & (keymods.CTRL | keymods.ALT | keymods.META):
            return

        # Name: Buchstaben/Zahlen/Space usw.
        if self.focus == "name":
            ch = None

            if keys.A <= key <= keys.Z:
                ch = chr(key)
                if mods & keymods.SHIFT:
                    ch = ch.upper()

            elif keys.K_0 <= key <= keys.K_9:
                ch = chr(key)

            elif key == keys.SPACE:
                ch = " "

            elif key in (keys.MINUS, keys.PERIOD, keys.COMMA, keys.UNDERSCORE):
                mapping = {
                    keys.MINUS: "-",
                    keys.PERIOD: ".",
                    keys.COMMA: ",",
                    keys.UNDERSCORE: "_",
                }
                ch = mapping.get(key)

            if ch and len(self.name_text) < self.name_max_len:
                self.name_text += ch

        # Room Code
        elif self.focus == "room" and not self.room_locked:
            if len(self.room_text) >= self.room_max_len:
                return

            # A-Z
            if keys.A <= key <= keys.Z:
                self.room_text += chr(key).upper()
                return

            # 0-9
            if keys.K_0 <= key <= keys.K_9:
                self.room_text += chr(key)
                return

    def on_text_input(self, text: str):
        """Optional: falls dein GameManager pygame.TEXTINPUT weiterreicht (z.B. für Umlaute)."""
        if not text:
            return
        ch = text[0]
        if ch in "\r\n\t":
            return
        if ord(ch) < 32:
            return

        if self.focus == "name":
            if len(self.name_text) < self.name_max_len:
                self.name_text += ch
        elif self.focus == "room" and not self.room_locked:
            if ch.isdigit() and len(self.room_text) < self.room_max_len:
                self.room_text += ch

    # ---------------- Drawing ----------------
    def _draw_textbox(self, screen, rect, value, placeholder, focused):
        bg = getattr(config, "COLOR_INPUT_BG", (15, 25, 45))
        border = getattr(config, "COLOR_INPUT_BORDER", (70, 110, 170))
        border_focus = getattr(config, "COLOR_INPUT_FOCUS", (120, 180, 255))

        text_col = getattr(config, "COLOR_TEXT_PRIMARY", config.COLOR_WHITE)
        hint_col = getattr(config, "COLOR_TEXT_SECONDARY", (150, 165, 190))

        pygame.draw.rect(screen, bg, rect, border_radius=14)
        pygame.draw.rect(screen, border_focus if focused else border, rect, width=3, border_radius=14)

        font = pygame.font.Font(None, getattr(config, "INPUT_FONT_SIZE", config.FONT_SIZE_SMALL))

        shown = value if value else placeholder
        col = text_col if value else hint_col
        surf = font.render(shown, True, col)
        screen.blit(surf, (rect.x + 16, rect.centery - surf.get_height() // 2))

        if focused and (int(self.cursor_t * 2) % 2 == 0):
            cx = rect.x + 16 + min(rect.w - 32, 12 * len(value))
            pygame.draw.line(screen, text_col, (cx, rect.y + 10), (cx, rect.bottom - 10), 2)

    def draw(self, screen):
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)
        draw_title_art(screen)

        # Titel
        title_font = pygame.font.Font(None, config.MENU_TITLE_FONT_SIZE)

        shadow_surf = title_font.render("Schiffe Versenken", True, config.COLOR_BLACK)
        shadow_rect = shadow_surf.get_rect(center=(config.WINDOW_WIDTH // 2, config.MENU_TITLE_Y + 5))
        screen.blit(shadow_surf, shadow_rect)

        title_surf = title_font.render("Schiffe Versenken", True, config.COLOR_WHITE)
        title_rect = title_surf.get_rect(center=(config.WINDOW_WIDTH // 2, config.MENU_TITLE_Y))
        screen.blit(title_surf, title_rect)

        # Untertitel
        sub_font = pygame.font.Font(None, config.MENU_SUBTITLE_FONT_SIZE)
        sub_surf = sub_font.render("Operation Lighthouse", True, config.COLOR_LIGHT_GRAY)
        sub_rect = sub_surf.get_rect(center=(config.WINDOW_WIDTH // 2, config.MENU_SUBTITLE_Y))
        screen.blit(sub_surf, sub_rect)

        # Heading
        heading_font = pygame.font.Font(None, config.FONT_SIZE_LARGE)
        heading = heading_font.render("JOIN GAME", True, config.COLOR_WHITE)
        heading_rect = heading.get_rect(center=(config.WINDOW_WIDTH // 2, self.heading_y - 30))
        screen.blit(heading, heading_rect)

        # Labels
        label_font = pygame.font.Font(None, config.FONT_SIZE_SMALL)
        host_lbl = label_font.render("Your Name:", True, config.COLOR_LIGHT_GRAY)
        screen.blit(host_lbl, host_lbl.get_rect(center=(config.WINDOW_WIDTH // 2, self.name_rect.y - 22)))

        room_lbl = label_font.render("Room Code:", True, config.COLOR_LIGHT_GRAY)
        screen.blit(room_lbl, room_lbl.get_rect(center=(config.WINDOW_WIDTH // 2, self.room_rect.y - 22)))

        # Textfelder
        self._draw_textbox(screen, self.name_rect, self.name_text, self.name_placeholder, self.focus == "name")
        self._draw_textbox(screen, self.room_rect, self.room_text, self.room_placeholder, self.focus == "room")

        # Buttons
        for button in self.buttons:
            button.draw(screen)

        # Footer
        info_font = pygame.font.Font(None, config.MENU_INFO_FONT_SIZE)
        info_surf = info_font.render("Steuerung: Maus", True, config.COLOR_GRAY)
        info_rect = info_surf.get_rect(
            center=(config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT - config.MENU_INFO_MARGIN_BOTTOM)
        )
        screen.blit(info_surf, info_rect)