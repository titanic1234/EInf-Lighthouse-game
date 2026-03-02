"""Schiffsplatzierung (Multiplayer)"""

from pgzero.rect import Rect

import game.config as config
import game.multiplayer.multiplayer_config as mconfig
from game.multiplayer.ws import WSClient
from game.graphics import draw_rounded_rect, draw_text
from game.states.shared_placement import SharedPlacementState
from game.theme import theme_manager
from game.graphics import GlowButton


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



    # ------------------------------
    # Multiplayer: Board Upload + Ready
    # ------------------------------
    def _send_board_to_server_once(self):
        """
        Sendet die eigenen Schiffszellen an den Server:
        {"type":"set_board","ships":[ [[row,col],...], ... ]}
        """
        if self.board_sent:
            return
        if not self._all_ships_placed():
            return

        ships_payload = []
        for ship in self.player_board.ships:
            ships_payload.append([[cell.row, cell.col] for cell in ship.cells])

        self.ws.send_json({"type": "set_board", "ships": ships_payload})
        self.board_sent = True

    def _can_send_ready(self):
        return self._all_ships_placed() and (not self.local_ready_sent)

    def _can_start_game(self):
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
        self.ws.send_json({"type": "ready"})

    def _on_ready_clicked(self):
        print("READY CLICKED")
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

    def _on_start_clicked(self):
        # Server startet automatisch sobald beide ready und boards gesetzt sind.
        if not self.host:
            return
        if not self._can_start_game():
            self._show_toast("Spiel kann noch nicht starten.")
            return

    def _process_ws_messages(self):
        while True:
            msg = self.ws.poll()
            if msg is None:
                break

            t = msg.get("type")
            # Debug:
            # print("WS IN:", msg)

            if t == "presence":
                # Gegnername aus host_name/guest_name
                opponent = (msg.get("guest_name") if self.host else msg.get("host_name")) or None
                if opponent:
                    mconfig.set_game(opponent_name=opponent)

            elif t == "board_set":
                # optional feedback
                # msg: {"type":"board_set","role":"host/guest","host_board_set":bool,"guest_board_set":bool}
                pass

            elif t == "ready_update":
                ready = bool(msg.get("guest_ready")) and bool(msg.get("host_ready"))
                opponent = (msg.get("guest_name") if self.host else msg.get("host_name")) or None
                mconfig.set_game(opponent_name=opponent, ready=ready)

            elif t == "game_started":
                # turn speichern, damit Battle sofort Turn kennt
                turn = msg.get("turn")  # "host"/"guest"
                self.game_manager.mp_turn = turn

                # Board + WS in GameManager speichern
                self.game_manager.player_board = self.player_board
                self.game_manager.ws = self.ws

                self.game_manager.change_state(config.STATE_MULTIPLAYER_GAME)
                return

            elif t == "error":
                self._show_toast(msg.get("detail", "Server error"))

    def _handle_action_button_click(self, pos):
        if self.ready_button.is_hovered(pos[0], pos[1]):
            self.ready_button.click()
    # ------------------------------
    # Update / Input
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

        status_rect = Rect(40, 40, 520, 190)
        draw_rounded_rect(screen, (0, 0, 0), status_rect, radius=16, alpha=160)
        draw_rounded_rect(screen, theme.color_ship_border, status_rect, radius=16, width=2, alpha=100)

        y = status_rect.y + 22
        line_h = 32

        code = mconfig.CODE or "-"
        you = mconfig.NAME or "-"
        opp = mconfig.OPPONENT_NAME or "Warte auf Gegner..."
        conn = "ONLINE" if self.ws.is_connected() else "OFFLINE"

        local_ready = "JA" if self.local_ready_sent else "NEIN"
        server_ready = "JA" if mconfig.READY else "NEIN"
        board_sent = "JA" if self.board_sent else "NEIN"

        draw_text(screen, f"ROOM: {code}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"DU: {you}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"GEGNER: {opp}", status_rect.x + 20, y, 26, theme.color_text_primary); y += line_h
        draw_text(screen, f"STATUS: {conn}", status_rect.x + 20, y, 26, theme.color_text_secondary); y += line_h
        draw_text(screen, f"BOARD GESENDET: {board_sent}", status_rect.x + 20, y, 26, theme.color_text_secondary); y += line_h
        draw_text(screen, f"DU BEREIT: {local_ready}", status_rect.x + 20, y, 26, theme.color_text_secondary); y += line_h
        draw_text(screen, f"SPIEL STARTBAR: {server_ready}", status_rect.x + 20, y, 26, theme.color_text_secondary)

