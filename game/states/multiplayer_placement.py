"""Schiffsplatzierung (Multiplayer)"""

from pgzero.rect import Rect

import game.config as config
import game.multiplayer.multiplayer_config as mconfig
from game.multiplayer.ws import WSClient
from game.graphics import draw_rounded_rect, draw_text
from game.states.shared_placement import SharedPlacementState
from game.theme import theme_manager


class MultiplayerPlacementState(SharedPlacementState):
    """Schiffsplatzierung mit ready/start"""

    title_text = "MULTIPLAYER - SCHIFFE PLATZIEREN"
    instruction_hint = "Linksklick: wählen/platzieren | R: rotieren"

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.ws = WSClient()
        self.ws.start()

        # Multiplayer UI
        self.local_ready_sent = False
        self.toast_text = ""
        self.toast_timer = 0.0
        self.host = mconfig.ROLE == "host"

        self.ready_button = self.build_primary_action_button("BEREIT", self._on_ready_clicked, y_offset=30)
        self.start_button = self.build_primary_action_button("START", self._on_start_clicked, y_offset=95)

    def _can_send_ready(self):
        return self._all_ships_placed() and not self.local_ready_sent

    def _can_start_game(self):
        # „bereit“ nur wenn Gegner da + server sagt READY True (oder du setzt READY wenn beide ready)

        return (
                self._all_ships_placed()
                and self.host
                and (mconfig.OPPONENT_NAME is not None)
                and (mconfig.READY is True)
        )

    def _show_toast(self, text: str, duration: float = 2.0):
        self.toast_text = text
        self.toast_timer = duration

    def _send_ready_to_server(self):
        """
        TODO: Hier deinen echten Request einbauen:
        - z.B. websocket send: {"type":"ready", "token":..., "code":...}
        - oder HTTP: POST /ready
        """
        # Placeholder: du könntest hier mconfig.READY nicht setzen, weil server das tun soll.
        # Aber für Offline-Test:
        # mconfig.READY = True

        message = {"type": "ready"}
        self.ws.send_json(message)

    def _request_start_to_server(self):
        """
        TODO: Hier deinen Start-Request einbauen (server startet game, setzt GAME_STATE etc.)
        """
        pass

    def _on_ready_clicked(self):
        print("READY CLICKED")
        if not self._all_ships_placed():
            self._show_toast("Platziere zuerst alle Schiffe!")
            return
        if not mconfig.CONNECTION:
            self._show_toast("Keine Verbindung zum Server.")
            return

        self.local_ready_sent = True
        self._send_ready_to_server()
        self._show_toast("Bereit gesendet. Warte auf Gegner...")

    def _on_start_clicked(self):
        if not self.host: return
        if not self._can_start_game():
            self._show_toast("Spiel kann noch nicht starten.")
            return

        self._request_start_to_server()

        # Wenn dein Server z.B. mconfig.GAME_STATE setzt, kannst du im update darauf reagieren.
        # Für jetzt: Wechsel direkt in Multiplayer-Game-State:
        self.game_manager.player_board = self.player_board
        self.game_manager.change_state(config.STATE_MULTIPLAYER_GAME)

    def _process_ws_messages(self):
        while True:
            msg = self.ws.poll()
            if msg is None:
                break

            # Debug:
            print("WS IN:", msg)

            if msg.get("type") == "ready":
                ready = bool(msg.get("guest_ready")) and bool(msg.get("host_ready"))
                mconfig.set_game(opponent_name=msg.get("opponent_name"), ready=ready)
            elif msg.get("type") == "opponent_joined":
                mconfig.set_game(opponent_name=msg.get("opponent_name"), ready=False)


    # ------------------------------
    # Update / Input
    # ------------------------------
    def update(self, dt, mouse_pos):
        self.player_board.all_ships_placed = self._all_ships_placed()
        self.mouse_pos = mouse_pos
        self._process_ws_messages()

        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_text = ""

        super().update(dt, mouse_pos)

    def _update_action_buttons(self, dt, mouse_pos):
        self.ready_button.update(dt, mouse_pos[0], mouse_pos[1])
        self.start_button.update(dt, mouse_pos[0], mouse_pos[1])

        # Ready / Start Buttons
    def _handle_action_button_click(self, pos):
        if self._can_send_ready() and self.ready_button.is_hovered(pos[0], pos[1]):
            self.ready_button.click()
            return True

        if self._can_start_game() and self.start_button.is_hovered(pos[0], pos[1]):
            self.start_button.click()
            return True

        return False

    def _draw_status_panels(self, screen):
        # Multiplayer status panel (links oben)
        self._draw_multiplayer_status(screen)

        # Buttons (Ready/Start abhängig)
    def _draw_action_buttons(self, screen):
        theme = theme_manager.current
        if self._can_send_ready():
            self.ready_button.draw(screen, default_color=(30, 110, 70), hover_color=(50, 170, 100))

        if self.local_ready_sent and not self._can_start_game() and self.host:
            # Wartetext statt Button
            draw_text(
                screen,
                "WARTEN AUF GEGNER...",
                self.start_button.x,
                self.start_button.y,
                config.BATTLE_STAT_FONT_SIZE,
                theme.color_text_secondary,
                center=True,
            )

        if self._can_start_game() and self.host:
            self.start_button.draw(screen, default_color=(30, 80, 140), hover_color=(60, 120, 220))

        # Toast
        if self.toast_text:
            self._draw_toast(screen, self.toast_text)

    def _draw_toast(self, screen, text: str):
        theme = theme_manager.current
        toast_rect = Rect(config.WINDOW_WIDTH // 2 - 260, config.WINDOW_HEIGHT - 140, 520, 60)
        draw_rounded_rect(screen, (0, 0, 0), toast_rect, radius=16, alpha=180)
        draw_rounded_rect(screen, theme.color_ship_border, toast_rect, radius=16, width=2, alpha=120)
        draw_text(screen, text, toast_rect.centerx, toast_rect.centery, 30, theme.color_text_primary, center=True)

    def _draw_multiplayer_status(self, screen):
        theme = theme_manager.current

        status_rect = Rect(40, 40, 520, 190)
        draw_rounded_rect(screen, (0, 0, 0), status_rect, radius=16, alpha=160)
        draw_rounded_rect(screen, theme.color_ship_border, status_rect, radius=16, width=2, alpha=100)

        # Zeilen
        y = status_rect.y + 22
        line_h = 32

        code = mconfig.CODE or "-"
        you = mconfig.NAME or "-"
        opp = mconfig.OPPONENT_NAME or "Warte auf Gegner..."
        conn = "ONLINE" if mconfig.CONNECTION else "OFFLINE"

        # READY-Text: lokales ready vs server ready
        local_ready = "JA" if self.local_ready_sent else "NEIN"
        server_ready = "JA" if mconfig.READY else "NEIN"

        draw_text(screen, f"ROOM: {code}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"DU: {you}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"GEGNER: {opp}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"STATUS: {conn}", status_rect.x + 20, y, 26, theme.color_text_secondary); y += line_h
        draw_text(screen, f"DU BEREIT: {local_ready}", status_rect.x + 20, y, 26, theme.color_text_secondary); y += line_h
        draw_text(screen, f"SPIEL STARTBAR: {server_ready}", status_rect.x + 20, y, 26, theme.color_text_secondary)

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.ready_button = self.build_primary_action_button("BEREIT", self._on_ready_clicked, y_offset=30)
        self.start_button = self.build_primary_action_button("START", self._on_start_clicked, y_offset=95)