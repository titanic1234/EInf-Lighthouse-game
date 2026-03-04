# multiplayer_placement.py
"""Schiffsplatzierung (Multiplayer)"""

from pgzero.rect import Rect

import game.config as config
import game.multiplayer.multiplayer_config as mconfig
from game.multiplayer.ws import WSClient
from game.graphics import draw_rounded_rect, draw_text
from game.states.shared_placement import SharedPlacementState
from game.theme import theme_manager


NAPALM_IMMUNE_BASE_NAMES = {"U-Boot", "Schaluppe"}


def _base_ship_name(name: str) -> str:
    # "U-Boot #1" -> "U-Boot"
    return (name or "").split(" #", 1)[0].strip()


class MultiplayerPlacementState(SharedPlacementState):

    title_text = "MULTIPLAYER - SCHIFFE PLATZIEREN"
    instruction_hint = "Linksklick: wählen/platzieren | R: rotieren"

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # WS starten und im GameManager speichern
        self.ws = WSClient()
        self.ws.start()
        self.game_manager.ws = self.ws

        # Multiplayer UI / State
        self.local_ready_sent = False
        self.toast_text = ""
        self.toast_timer = 0.0
        self.host = (mconfig.ROLE == "host")

        # Board-Upload state
        self.board_sent = False  # set_board schon gesendet?

        # Buttons
        self.ready_button = self.build_primary_action_button("BEREIT", self._on_ready_clicked, 30)

        # Optional: nur sinnvoll, wenn Server diese Nachricht auch verarbeitet
        if self.host:
            self.ws.send_json({"type": "host_name", "name": mconfig.NAME})

    # ------------------------------
    # Button clicked
    # ------------------------------
    def _send_board_to_server_once(self):
        """
        Sendet die eigenen Schiffszellen an den Server.
        """
        if self.board_sent:
            return
        if not self._all_ships_placed():
            return

        ships_payload = []
        for ship in self.player_board.ships:
            base_name = _base_ship_name(ship.name)
            ships_payload.append({
                "name": base_name,
                "immune_to_napalm": base_name in NAPALM_IMMUNE_BASE_NAMES,
                "cells": [[cell.row, cell.col] for cell in ship.cells],
            })

        self.ws.send_json({"type": "set_board", "ships": ships_payload})
        self.board_sent = True

    def _can_send_ready(self):
        return self._all_ships_placed() and (not self.local_ready_sent)

    def _send_ready_to_server(self):
        self.ws.send_json({"type": "ready"})

    def _on_ready_clicked(self):
        if not self._all_ships_placed():
            self._show_toast("Platziere zuerst alle Schiffe!")
            return
        if not self.ws.is_connected():
            self._show_toast("Keine Verbindung zum Server.")
            return

        # ✅ wichtig: erst Board senden, dann ready
        self._send_board_to_server_once()

        self.local_ready_sent = True
        self._send_ready_to_server()
        self._show_toast("Bereit gesendet. Warte auf Gegner...")

    def _handle_action_button_click(self, pos):
        if self.ready_button.is_hovered(pos[0], pos[1]):
            self.ready_button.click()

    # ------------------------------
    # Graphics
    # ------------------------------
    def _show_toast(self, text: str, duration: float = 2.0):
        self.toast_text = text
        self.toast_timer = duration

    # ------------------------------
    # websocket
    # ------------------------------
    def _process_ws_messages(self):
        while True:
            msg = self.ws.poll()
            if msg is None:
                break

            t = msg.get("type")

            if t == "presence":
                opponent = (msg.get("guest_name") if self.host else msg.get("host_name")) or None
                if opponent:
                    mconfig.set_game(opponent_name=opponent)

            elif t == "ready_update":
                ready = bool(msg.get("guest_ready")) and bool(msg.get("host_ready"))
                opponent = (msg.get("guest_name") if self.host else msg.get("host_name")) or None
                mconfig.set_game(opponent_name=opponent, ready=ready)

            elif t == "game_started":
                turn = msg.get("turn")  # "host"/"guest"
                self.game_manager.mp_turn = turn

                # Board + WS in GameManager speichern
                self.game_manager.player_board = self.player_board
                self.game_manager.ws = self.ws

                self.game_manager.change_state(config.STATE_MULTIPLAYER_GAME)
                return

            elif t == "host_name":
                pass

            elif t == "error":
                self._show_toast(msg.get("detail", "Server error"))

    # ------------------------------
    # Update
    # ------------------------------
    def update(self, dt, mouse_pos):
        self._process_ws_messages()
        if self.toast_timer > 0:
            self.toast_timer -= dt
            if self.toast_timer <= 0:
                self.toast_text = ""
        super().update(dt, mouse_pos)

    # ------------------------------
    # Draw
    # ------------------------------
    def draw(self, screen):
        super().draw(screen)
        if self.toast_text:
            self._draw_toast(screen, self.toast_text)

    def _draw_status_panels(self, screen):
        self._draw_multiplayer_status(screen)

    def _draw_action_buttons(self, screen):
        if self._can_send_ready():
            self.ready_button.draw(screen, default_color=(30, 110, 70), hover_color=(50, 170, 100))

    def _draw_multiplayer_status(self, screen):
        theme = theme_manager.current

        status_rect = Rect(1300, 240, 520, 220)
        draw_rounded_rect(screen, (0, 0, 0), status_rect, radius=16, alpha=160)
        draw_rounded_rect(screen, theme.color_ship_border, status_rect, radius=16, width=2, alpha=100)

        y = status_rect.y + 22
        line_h = 32

        code = mconfig.CODE or "-"
        you = mconfig.NAME or "-"
        opp = mconfig.OPPONENT_NAME or "Warte auf Gegner..."
        conn = "ONLINE" if self.ws.is_connected() else "OFFLINE"

        local_ready = "JA" if self.local_ready_sent else "NEIN"
        board_sent = "JA" if self.board_sent else "NEIN"

        draw_text(screen, f"ROOM: {code}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"DU: {you}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"GEGNER: {opp}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"STATUS: {conn}", status_rect.x + 20, y, 26, theme.color_text_secondary); y += line_h
        draw_text(screen, f"BOARD GESENDET: {board_sent}", status_rect.x + 20, y, 26, theme.color_text_secondary); y += line_h
        draw_text(screen, f"DU BEREIT: {local_ready}", status_rect.x + 20, y, 26, theme.color_text_secondary); y += line_h