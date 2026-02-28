# create_game.py

import pygame
import random
import string

import game.config as config
from game.graphics import draw_gradient_background, GlowButton, draw_title_art
from game.states.base_state import BaseState

import game.multiplayer.multiplayer_config as mconfig

from game.multiplayer.communication import create_game as create_game_request
from game.multiplayer.schemas import CreateGame as CreateGameSchema


class JoinGame(BaseState):
    """Multiplayer: Create Game Screen (Name + RoomCode + Start/Back)"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ---- Field State ----
        self.name_text = ""
        self.name_placeholder = "Spieler"
        self.name_max_len = 16

        self.room_text = "Waiting..."
        self.room_placeholder = "z.B. 123456"
        self.room_max_len = 6
        self.room_locked = True

        if mconfig.CODE is not None:
            self.room_text = mconfig.CODE

        # Fokus: "name" | "room" | None
        self.focus = "name"
        self.cursor_t = 0.0

        # ---- Layout (CREATE GAME über dem Schiff) ----
        center_x = config.WINDOW_WIDTH // 2
        self.field_w = config.MENU_BUTTON_WIDTH
        self.field_h = 70

        # Orientierung an Subtitle/Artwork, stabil bei 1920x1080
        # Titelblock endet ca. bei MENU_SUBTITLE_Y -> darunter sitzt das Schiff
        ship_center_y = config.MENU_SUBTITLE_Y + 220

        # Heading sitzt ÜBER dem Schiff
        self.heading_y = ship_center_y - 120

        # Felder unter dem Schiff
        fields_top = ship_center_y + 150

        self.name_rect = pygame.Rect(center_x - self.field_w // 2, fields_top, self.field_w, self.field_h)
        self.room_rect = pygame.Rect(center_x - self.field_w // 2, fields_top + 120, self.field_w, self.field_h)

        # Buttons unter die Felder setzen
        self.buttons = []
        self._create_buttons()


    def _create_buttons(self):
        center_x = config.WINDOW_WIDTH // 2
        start_y = config.MENU_BUTTON_Y

        self.buttons = [
            GlowButton(
                center_x,
                start_y + config.MENU_BUTTON_SPACING * 2,
                config.MENU_BUTTON_WIDTH,
                config.MENU_BUTTON_HEIGHT,
                "Start Game",
                self._start_game,
            ),
            GlowButton(
                center_x,
                start_y + config.MENU_BUTTON_SPACING * 3,
                config.MENU_BUTTON_WIDTH,
                config.MENU_BUTTON_HEIGHT,
                "Back",
                self._back_menu,
            ),
        ]

    def _back_menu(self):
        self.game_manager.change_state(config.STATE_MULTIPLAYER_MENU)

    def _start_game(self):
        pass

        # optional:
        # self.game_manager.change_state(config.STATE_MULTIPLAYER_WAITING)

    # ---------------- Update / Input ----------------
    def update(self, dt, mouse_pos):
        self.cursor_t += dt

        mx, my = mouse_pos
        for button in self.buttons:
            button.update(dt, mx, my)

    def on_mouse_down(self, pos, button):
        if button != 1:
            return

        # Fokus auf Textfelder
        if self.name_rect.collidepoint(pos):
            self.focus = "name"
            self.cursor_t = 0.0
            return

        if self.room_rect.collidepoint(pos):
            if not self.room_locked:
                self.focus = "room"
                self.cursor_t = 0.0
            return

        # Buttons
        for btn in self.buttons:
            if btn.hovered:
                btn.click()
                return

        # Klick außerhalb -> Fokus weg
        self.focus = None

    def on_key_down(self, key):
        if key == pygame.K_ESCAPE:
            self._back_menu()
            return

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._start_game()
            return

        if key == pygame.K_TAB:
            if self.room_locked:
                self.focus = "name"
            else:
                self.focus = "room" if self.focus == "name" else "name"
            self.cursor_t = 0.0
            return

        if key == pygame.K_BACKSPACE:
            if self.focus == "name" and self.name_text:
                self.name_text = self.name_text[:-1]
            elif self.focus == "room" and self.room_text:
                self.room_text = self.room_text[:-1]
            return

    def on_text_input(self, text: str):
        """Nutze pygame.TEXTINPUT, falls dein GameManager das weiterreicht."""
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
        elif self.focus == "room":
            if ch.isdigit() and len(self.room_text) < self.room_max_len:
                self.room_text += ch

    # ---------------- Drawing ----------------
    def _draw_textbox(self, screen, rect, value, placeholder, focused):
        # Farben aus config (optional erweiterbar)
        bg = getattr(config, "COLOR_INPUT_BG", (15, 25, 45))
        border = getattr(config, "COLOR_INPUT_BORDER", (70, 110, 170))
        border_focus = getattr(config, "COLOR_INPUT_FOCUS", (120, 180, 255))

        text_col = getattr(config, "COLOR_TEXT_PRIMARY", config.COLOR_WHITE)
        hint_col = getattr(config, "COLOR_TEXT_SECONDARY", (150, 165, 190))

        pygame.draw.rect(screen, bg, rect, border_radius=14)
        pygame.draw.rect(screen, border_focus if focused else border, rect, width=3, border_radius=14)

        font = pygame.font.Font(None, config.FONT_SIZE_SMALL)
        shown = value if value else placeholder
        col = text_col if value else hint_col
        surf = font.render(shown, True, col)
        screen.blit(surf, (rect.x + 16, rect.centery - surf.get_height() // 2))

        # Cursor blink
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

        # Heading: ÜBER dem Schiff
        heading_font = pygame.font.Font(None, config.FONT_SIZE_LARGE)
        heading = heading_font.render("CREATE GAME", True, config.COLOR_WHITE)
        heading_rect = heading.get_rect(center=(config.WINDOW_WIDTH // 2, self.heading_y - 30))
        screen.blit(heading, heading_rect)

        # Labels
        label_font = pygame.font.Font(None, config.FONT_SIZE_SMALL)
        host_lbl = label_font.render("Host's Name:", True, config.COLOR_LIGHT_GRAY)
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