# multiplayer_battle.py
"""
Multiplayer Kampf-State
Spieler vs Spieler über WebSocket
"""

from pgzero.rect import Rect

import game.config as config
from game.entities.board import Board
from game.graphics import draw_rounded_rect, draw_text, draw_grid_cell
from game.theme import theme_manager
import game.multiplayer.multiplayer_config as mconfig

from game.config import CELL_HIT, CELL_MISS
from game.states.shared_battle import SharedBattleState


class MultiplayerBattleState(SharedBattleState):
    """Kampf-Phase: Multiplayer"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # WebSocket
        self.ws = self.game_manager.ws

        self.host = (mconfig.ROLE == "host")
        self.role = "host" if self.host else "guest"

        # Gegnerboard
        self.opponent_board = Board(config.COMPUTER_GRID_X, config.GRID_OFFSET_Y, "Opponent")

        self.player_turn: bool = False
        self.game_over: bool = False
        self.winner = None
        self.message = "WARTE AUF SPIELBEGINN..."

        self.game_over_timer = None
        self.game_over_delay = config.BATTLE_GAME_OVER_DELAY

        initial_turn = getattr(self.game_manager, "mp_turn", None)
        if isinstance(initial_turn, str) and initial_turn in ("host", "guest"):
            self._set_turn(initial_turn)
        else:
            self.message = "WARTE AUF SPIELBEGINN... (kein zug)"


    # ------------------------------
    # Handle events
    # ------------------------------
    def _set_turn(self, turn: str):
        self.player_turn = (turn == self.role)
        self.message = "Du bist dran - Mache einen Zug" if self.player_turn else "Dein Gegner ist dran..."

    def _mark_opponent_cell(self, row: int, col: int, hit: bool, keep_napalm: bool = True):
        """Setzt HIT/MISS auf opponent_board"""
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
        """Markiert zerstörte Schiffe auf opponent_board"""
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

    def _apply_incoming_strike_on_player(self, row: int, col: int, hit: bool, napalm: bool = False, napalm_only: bool = False):
        cell = self.player_board.get_cell(row, col)
        if not cell:
            return

        if napalm and napalm_only:
            cell.napalm_marked = True
            self._spawn_effects(self.player_board, row, col, False)
            return

        hit2, _, _ = self.player_board.shoot(row, col)
        if napalm:
            cell.napalm_marked = True
        self._spawn_effects(self.player_board, row, col, hit2)

    def _use_guided_missile(self):
        if self.abilities["guided"]["charges"] <= 0:
            return
        self.abilities["guided"]["charges"] = 0
        self._send_ability("guided")
        self.selected_ability = None
        self.message = f"{self._ability_display_name('guided')} SENT..."


    # ------------------------------
    # apply result
    # ------------------------------
    def _apply_shot_result(self, msg: dict):
        by = msg.get("by")
        x = msg.get("x")
        y = msg.get("y")
        hit = bool(msg.get("hit"))
        destroyed = bool(msg.get("destroyed"))
        destroyed_cells = msg.get("destroyed_cells", [])
        next_turn = msg.get("next_turn")

        if not isinstance(x, int) or not isinstance(y, int):
            return

        row, col = y, x

        if by == self.role:
            self._mark_opponent_cell(row, col, hit, keep_napalm=True)
            self._spawn_effects(self.opponent_board, row, col, hit)
            self.game_manager.shots_fired += 1
            self.game_manager.shots_hit += 1 if hit else 0
            if destroyed:
                self._apply_destroyed_cells_on_opponent(destroyed_cells)
                self.message = "SCHIFF ZERSTÖRT!"
            else:
                self.message = "TREFFER!" if hit else "VERFEHLT!"
        else:
            hit2, _, _ = self.player_board.shoot(row, col)
            self._spawn_effects(self.player_board, row, col, hit2)
            self.message = "DU WURDEST GETROFFEN!" if hit2 else "GEGNER HAT VERFEHLT!"

        if isinstance(next_turn, str) and next_turn in ("host", "guest"):
            self._set_turn(next_turn)

    def _apply_ability_result(self, msg: dict):
        ability = msg.get("ability")
        by = msg.get("by")
        results = msg.get("results", [])
        next_turn = msg.get("next_turn")

        if isinstance(results, list):
            for r in results:
                if not isinstance(r, dict):
                    continue

                row = r.get("row")
                col = r.get("col")
                hit = bool(r.get("hit"))
                destroyed = bool(r.get("destroyed"))
                destroyed_cells = r.get("destroyed_cells", [])
                napalm_only = bool(r.get("napalm_only", False))

                if not isinstance(row, int) or not isinstance(col, int):
                    continue

                if by == self.role:
                    if napalm_only:
                        cell = self.opponent_board.get_cell(row, col)
                        if cell:
                            cell.napalm_marked = True
                        self._spawn_effects(self.opponent_board, row, col, False)
                    else:
                        self._mark_opponent_cell(row, col, hit, keep_napalm=True)
                        self._spawn_effects(self.opponent_board, row, col, hit)
                        if destroyed:
                            self._apply_destroyed_cells_on_opponent(destroyed_cells)
                else:
                    self._apply_incoming_strike_on_player(
                        row, col, hit,
                        napalm=(ability == "napalm"),
                        napalm_only=napalm_only
                    )

        self.message = f"{str(ability).upper()} RESOLVED"

        if isinstance(next_turn, str) and next_turn in ("host", "guest"):
            self._set_turn(next_turn)

        # Startzelle Napalm optisch markieren
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
        cells = msg.get("cells", [])
        found = set()
        for rc in msg.get("found", []) if isinstance(msg.get("found", []), list) else []:
            if isinstance(rc, list) and len(rc) == 2 and isinstance(rc[0], int) and isinstance(rc[1], int):
                found.add((rc[0], rc[1]))

        if isinstance(cells, list):
            for rc in cells:
                if not isinstance(rc, list) or len(rc) != 2:
                    continue
                r, c = rc
                if not isinstance(r, int) or not isinstance(c, int):
                    continue
                cell = self.opponent_board.get_cell(r, c) if msg.get("by") == self.role else self.player_board.get_cell(r, c)
                if cell and not cell.is_shot():
                    cell.scan_marked = True
                    cell.scan_found_ship = (r, c) in found

        self.message = "SONAR AUSGEFÜHRT"


    # ------------------------------
    # napalm fire
    # ------------------------------
    def _apply_fire_tick(self, msg: dict):
        results = msg.get("results", [])
        if not isinstance(results, list):
            return

        self.message = "FEUER BREITET SICH AUS..."

        for r in results:
            if not isinstance(r, dict):
                continue

            target_role = r.get("target_role")
            row = r.get("row")
            col = r.get("col")
            hit = bool(r.get("hit"))
            destroyed = bool(r.get("destroyed"))
            destroyed_cells = r.get("destroyed_cells", [])
            napalm_only = bool(r.get("napalm_only", False))

            if not isinstance(row, int) or not isinstance(col, int):
                continue

            if target_role != self.role:
                # Feuer trifft Gegner
                cell = self.opponent_board.get_cell(row, col)
                if cell:
                    cell.napalm_marked = True

                if not napalm_only:
                    self._mark_opponent_cell(row, col, hit, keep_napalm=True)

                self._spawn_effects(self.opponent_board, row, col, hit if not napalm_only else False)

                if destroyed:
                    self._apply_destroyed_cells_on_opponent(destroyed_cells)

            else:
                # Feuer trifft Player
                self._apply_incoming_strike_on_player(
                    row, col, hit,
                    napalm=True,
                    napalm_only=napalm_only
                )


    # ------------------------------
    # game over
    # ------------------------------
    def _game_over(self, winner):
        if isinstance(winner, str) and winner in ("host", "guest"):
            self.game_manager.winner = "Player" if winner == self.role else "Opponent"
            mconfig.set_game(winner=winner)
        self.game_over_timer = self.game_over_delay


    # ------------------------------
    # websocket processing / send
    # ------------------------------
    def _process_ws_messages(self):
        while True:
            if self.game_over_timer is not None:
                return
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
                    self._game_over(msg.get("winner"))
                    return

                case "error":
                    self.message = msg.get("detail", "SERVER ERROR")

    def _send_ability(self, ability: str, row: int | None = None, col: int | None = None):
        if ability == "guided":
            self.ws.send_json({"type": "ability", "ability": "guided"})
            return
        if row is None or col is None:
            return
        self.ws.send_json({"type": "ability", "ability": ability, "x": col, "y": row})


    # ------------------------------
    # Update
    # ------------------------------
    def _update_pipeline(self, dt, mouse_pos):
        if self.game_over_timer is not None:
            self.game_over_timer -= dt
            if self.game_over_timer <= 0:
                self.game_manager.change_state(config.STATE_GAME_OVER)
        self.particles.update(dt)
        self._process_ws_messages()


    # ------------------------------
    # player events
    # ------------------------------
    def _player_shoot(self, row, col):
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
    def draw(self, screen):
        super().draw(screen)

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
                draw_grid_cell(
                    screen, x, y, cell,
                    is_enemy=is_enemy,
                    show_ships=show_ships,
                )

        label_color = (150, 200, 255) if not is_enemy else (255, 150, 150)
        for i in range(config.GRID_SIZE):
            draw_text(screen, str(i + 1), board.x_offset - 35,
                      board.y_offset + i * config.CELL_SIZE + config.CELL_SIZE // 2 - 12,
                      config.BATTLE_LABEL_FONT_SIZE, label_color)
            draw_text(screen, chr(65 + i), board.x_offset + i * config.CELL_SIZE + config.CELL_SIZE // 2,
                      board.y_offset - 30, config.BATTLE_LABEL_FONT_SIZE, label_color, center=True)