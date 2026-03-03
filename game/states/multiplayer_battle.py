"""
Multiplayer Kampf-State
Spieler vs Spieler über WebSocket (Server ist "Source of Truth")
"""

from pgzero.rect import Rect

import game.config as config
from game.entities.board import Board
from game.graphics import draw_rounded_rect, draw_text,draw_grid_cell
from game.theme import theme_manager
import game.multiplayer.multiplayer_config as mconfig

from game.config import CELL_HIT, CELL_MISS  # CELL_DESTROYED ist in Cell.mark_destroyed()
from game.states.shared_battle import SharedBattleState


class MultiplayerBattleState(SharedBattleState):
    """Kampf-Phase: Multiplayer"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.ws = self.game_manager.ws

        self.host = (mconfig.ROLE == "host")
        self.role = "host" if self.host else "guest"

        # eigener Board kommt aus Placement (GameManager.player_board)
        # Gegnerboard ist Fog-of-war Board
        self.opponent_board = Board(config.COMPUTER_GRID_X, config.GRID_OFFSET_Y, "Opponent")

        self.player_turn: bool = False
        self.game_over: bool = False
        self.winner = None
        self.message = "WAITING FOR GAME START..."

        # Start-turn aus Placement (damit Battle nicht "hängt")
        initial_turn = getattr(self.game_manager, "mp_turn", None)
        if isinstance(initial_turn, str) and initial_turn in ("host", "guest"):
            self._set_turn(initial_turn)
        else:
            self.message = "WAITING FOR GAME START... (no turn)"

    # ---------------- Turn / Marking helpers ----------------

    def _set_turn(self, turn: str):
        self.player_turn = (turn == self.role)
        self.message = "YOUR TURN - SELECT TARGET" if self.player_turn else "OPPONENT TURN..."

    def _mark_opponent_cell(self, row: int, col: int, hit: bool, keep_napalm: bool = True):
        """
        Wichtig für Napalm:
        - napalm_marked darf NICHT bei jedem hit/miss zurückgesetzt werden,
          sonst sieht man im Multiplayer nie "Feuer", sondern nur Shot-States.
        """
        cell = self.opponent_board.get_cell(row, col)
        if not cell or cell.is_shot():
            return

        cell.scan_marked = False
        cell.scan_found_ship = False
        cell.player_marker = False

        if not keep_napalm:
            cell.napalm_marked = False

        cell.status = CELL_HIT if hit else CELL_MISS

    def _apply_destroyed_cells_on_opponent(self, destroyed_cells):
        # destroyed_cells erwartet: [[row,col], ...]
        if not isinstance(destroyed_cells, list):
            return
        for rc in destroyed_cells:
            if not isinstance(rc, list) or len(rc) != 2:
                continue
            r, c = rc
            if not isinstance(r, int) or not isinstance(c, int):
                continue
            cell = self.opponent_board.get_cell(r, c)
            if cell:
                cell.mark_destroyed()

    def _apply_incoming_strike_on_player(self, row: int, col: int, hit: bool, napalm: bool = False):
        """Wendet serverbestätigten Treffer auf das eigene Board an.

        Für Napalm gilt: `hit=False` kann auch auf Schiffszellen auftreten
        (z. B. U-Boot-Immunität). In diesem Fall darf die Zelle NICHT als
        normaler Schuss verarbeitet werden.
        """
        cell = self.player_board.get_cell(row, col)
        if not cell:
            return

        if napalm and not hit:
            cell.napalm_marked = True
            self._spawn_effects(self.player_board, row, col, False)
            return

        hit2, _, _ = self.player_board.shoot(row, col)
        if napalm:
            cell.napalm_marked = True
        self._spawn_effects(self.player_board, row, col, hit2)

    # ------------------------------
    # websocket processing
    # ------------------------------

    def _apply_shot_result(self, msg: dict):
        by = msg.get("by")
        x = msg.get("x")  # col
        y = msg.get("y")  # row
        hit = bool(msg.get("hit"))
        destroyed = bool(msg.get("destroyed"))
        destroyed_cells = msg.get("destroyed_cells", [])
        next_turn = msg.get("next_turn")

        if not isinstance(x, int) or not isinstance(y, int):
            return

        row, col = y, x

        if by == self.role:
            # du hast geschossen -> Gegnerboard markieren
            self._mark_opponent_cell(row, col, hit, keep_napalm=True)
            self._spawn_effects(self.opponent_board, row, col, hit)
            self.game_manager.shots_fired += 1
            self.game_manager.shots_hit += 1 if (hit or destroyed) else 0
            if destroyed:
                self._apply_destroyed_cells_on_opponent(destroyed_cells)
                self.message = "SHIP DESTROYED!"
            else:
                self.message = "HIT!" if hit else "MISS!"

        else:
            # Gegner hat auf dich geschossen -> echtes Board schießen
            hit2, _, _ = self.player_board.shoot(row, col)
            self._spawn_effects(self.player_board, row, col, hit2)
            self.message = "YOU WERE HIT!" if hit2 else "OPPONENT MISSED!"

        if isinstance(next_turn, str) and next_turn in ("host", "guest"):
            self._set_turn(next_turn)

    def _apply_ability_result(self, msg: dict):
        ability = msg.get("ability")
        by = msg.get("by")
        results = msg.get("results", [])
        next_turn = msg.get("next_turn")

        # Ergebnisse markieren
        if isinstance(results, list):
            for r in results:
                if not isinstance(r, dict):
                    continue
                row = r.get("row")
                col = r.get("col")
                hit = bool(r.get("hit"))
                destroyed = bool(r.get("destroyed"))
                destroyed_cells = r.get("destroyed_cells", [])

                if not isinstance(row, int) or not isinstance(col, int):
                    continue

                if by == self.role:
                    self._mark_opponent_cell(row, col, hit, keep_napalm=True)
                    self._spawn_effects(self.opponent_board, row, col, hit)
                    if destroyed:
                        self._apply_destroyed_cells_on_opponent(destroyed_cells)
                else:
                    # Gegner-Ability trifft dich
                    self._apply_incoming_strike_on_player(row, col, hit, napalm=(ability == "napalm"))

        self.message = f"{str(ability).upper()} RESOLVED"

        if isinstance(next_turn, str) and next_turn in ("host", "guest"):
            self._set_turn(next_turn)

        # Napalm Start-Zelle optisch markieren (kommt vom Server)
        fire_started = bool(msg.get("fire_started"))
        origin = msg.get("fire_origin")

        if fire_started and isinstance(origin, dict):
            r0 = origin.get("row")
            c0 = origin.get("col")
            target_role = origin.get("target_role")
            if isinstance(r0, int) and isinstance(c0, int):
                if target_role != self.role:
                    cell = self.opponent_board.get_cell(r0, c0)
                    if cell:
                        cell.napalm_marked = True
                else:
                    cell = self.player_board.get_cell(r0, c0)
                    if cell:
                        cell.napalm_marked = True

    def _apply_sonar_result(self, msg: dict):
        # {"type":"sonar_result","cells":[[r,c],...],"found":[[r,c],...]}
        cells = msg.get("cells", [])
        found = set()
        for rc in msg.get("found", []) if isinstance(msg.get("found", []), list) else []:
            if isinstance(rc, list) and len(rc) == 2 and isinstance(rc[0], int) and isinstance(rc[1], int):
                found.add((rc[0], rc[1]))

        # Markieren auf Gegnerboard (scan_marked / scan_found_ship)
        if isinstance(cells, list):
            for rc in cells:
                if not isinstance(rc, list) or len(rc) != 2:
                    continue
                r, c = rc
                if not isinstance(r, int) or not isinstance(c, int):
                    continue
                cell = self.opponent_board.get_cell(r, c)
                if cell and not cell.is_shot():
                    cell.scan_marked = True
                    cell.scan_found_ship = (r, c) in found

        self.message = "SONAR COMPLETE"

    def _apply_fire_tick(self, msg: dict):
        """
        Server:
          {"type":"fire_tick","results":[{"target_role":"guest","row":..,"col":..,"hit":..,"destroyed":..,"destroyed_cells":[...]}]}
        """
        results = msg.get("results", [])
        if not isinstance(results, list):
            return

        # Optional: message setzen (kurz)
        self.message = "FIRE SPREADING..."

        for r in results:
            if not isinstance(r, dict):
                continue

            target_role = r.get("target_role")  # "host" oder "guest"
            row = r.get("row")
            col = r.get("col")
            hit = bool(r.get("hit"))
            destroyed = bool(r.get("destroyed"))
            destroyed_cells = r.get("destroyed_cells", [])

            if not isinstance(row, int) or not isinstance(col, int):
                continue

            # Wenn das Feuer den Gegner trifft, ist target_role der Gegner.
            if target_role != self.role:
                # Gegnerboard (fog) markieren + Napalm Overlay setzen (auch wenn bereits HIT/MISS)
                self._mark_opponent_cell(row, col, hit, keep_napalm=True)
                cell = self.opponent_board.get_cell(row, col)
                if cell:
                    cell.napalm_marked = True  # <-- Feuer sichtbar halten
                self._spawn_effects(self.opponent_board, row, col, hit)

                if destroyed:
                    self._apply_destroyed_cells_on_opponent(destroyed_cells)

            else:
                # Feuer trifft dich -> echtes Board schießen + Napalm markieren
                self._apply_incoming_strike_on_player(row, col, hit, napalm=True)

    def _game_over(self, winner):
        if isinstance(winner, str) and winner in ("host", "guest"):
            if winner == self.role:
                self.game_manager.winner = "Player"
            else:
                self.game_manager.winner = "Opponent"
            mconfig.set_game(winner=winner)
        self.game_manager.change_state(config.STATE_GAME_OVER)

    def _process_ws_messages(self):
        while True:
            msg = self.ws.poll()
            if msg is None:
                break

            t = msg.get("type")

            match t:
                case "game_started":
                    turn = msg.get("turn")
                    if isinstance(turn, str) and turn in ("host", "guest"):
                        self.game_manager.mp_turn = turn
                        self._set_turn(turn)

                case "shot_result":
                    self._apply_shot_result(msg)

                case "ability_result":
                    self._apply_ability_result(msg)

                case "sonar_result":
                    self._apply_sonar_result(msg)

                case "fire_tick":
                    self._apply_fire_tick(msg)

                case "turn_update":
                    turn = msg.get("turn")
                    if isinstance(turn, str) and turn in ("host", "guest"):
                        self._set_turn(turn)

                case "destroyed_update":
                    self._apply_destroyed_cells_on_opponent(msg.get("cells", []))

                case "game_over":
                    winner = msg.get("winner")
                    self._game_over(winner)
                    return

                case "error":
                    self.message = msg.get("detail", "SERVER ERROR")

    # ------------------------------
    # Input / Update
    # ------------------------------

    def _update_pipeline(self, dt, mouse_pos):
        self.particles.update(dt)
        self._process_ws_messages()

    def _send_ability(self, ability: str, row: int | None = None, col: int | None = None):
        if ability == "guided":
            self.ws.send_json({"type": "ability", "ability": "guided"})
            return
        if row is None or col is None:
            return
        # server expects x=col, y=row
        self.ws.send_json({"type": "ability", "ability": ability, "x": col, "y": row})

    def _use_guided_missile(self):
        if self.abilities["guided"]["charges"] <= 0:
            return
        self.abilities["guided"]["charges"] = 0
        self._send_ability("guided")
        self.selected_ability = None
        self.message = f"{self._ability_display_name('guided')} SENT..."

    def _player_shoot(self, row, col):
        # normal shot
        cell = self.opponent_board.get_cell(row, col)
        if not cell or cell.is_shot():
            return
        self.ws.send_json({"type": "shot", "x": col, "y": row})
        self.message = "SHOT FIRED..."

    def _player_airstrike(self, row, col):
        self.abilities["airstrike"]["charges"] = 0
        self.selected_ability = None
        self._send_ability("airstrike", row=row, col=col)
        self.message = f"{self._ability_display_name('airstrike')} SENT..."

    def _player_sonar(self, row, col):
        self.abilities["sonar"]["charges"] = 0
        self.selected_ability = None
        self._send_ability("sonar", row=row, col=col)
        self.message = f"{self._ability_display_name('sonar')} SENT..."

    def _player_napalm(self, row, col):
        self.abilities["napalm"]["charges"] = 0
        self.selected_ability = None
        self._send_ability("napalm", row=row, col=col)
        self.message = f"{self._ability_display_name('napalm')} SENT..."

    # ------------------------------
    # Draw
    # ------------------------------

    def _draw_board(self, screen, board, show_ships=True, is_enemy=False):
        theme = theme_manager.current

        bg_rect = Rect(
            board.x_offset - 10,
            board.y_offset - 10,
            config.GRID_SIZE * config.CELL_SIZE + 20,
            config.GRID_SIZE * config.CELL_SIZE + 20,
        )
        border_color = theme.color_text_enemy if is_enemy else theme.color_ship_border
        bg_color = (40, 10, 10) if is_enemy else theme.color_panel_bg
        draw_rounded_rect(screen, bg_color, bg_rect, radius=10, alpha=180)
        draw_rounded_rect(screen, border_color, bg_rect, radius=10, width=2, alpha=80)

        for row in range(config.GRID_SIZE):
            for col in range(config.GRID_SIZE):
                x = board.x_offset + col * config.CELL_SIZE
                y = board.y_offset + row * config.CELL_SIZE
                cell = board.get_cell(row, col)
                draw_grid_cell(screen, x, y, cell, is_enemy=is_enemy, show_ships=show_ships, ws_connected=self.ws.is_connected())

        label_color = (150, 200, 255) if not is_enemy else (255, 150, 150)
        for i in range(config.GRID_SIZE):
            draw_text(
                screen,
                str(i + 1),
                board.x_offset - 35,
                board.y_offset + i * config.CELL_SIZE + config.CELL_SIZE // 2 - 12,
                config.BATTLE_LABEL_FONT_SIZE,
                label_color,
            )
            draw_text(
                screen,
                chr(65 + i),
                board.x_offset + i * config.CELL_SIZE + config.CELL_SIZE // 2,
                board.y_offset - 30,
                config.BATTLE_LABEL_FONT_SIZE,
                label_color,
                center=True,
            )

    def draw(self, screen):
        super().draw(screen)