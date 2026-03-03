"""
Multiplayer Kampf-State
Spieler vs Spieler über WebSocket (Server ist "Source of Truth")
"""

import pygame
from pygame import Rect

import game.config as config
from game.entities.board import Board
from game.graphics import (
    draw_gradient_background,
    draw_rounded_rect,
    draw_text,
    draw_grid_cell,
)
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

    def _spawn_effects(self, board, row, col, hit):
        x = board.x_offset + col * config.CELL_SIZE + config.CELL_SIZE // 2
        y = board.y_offset + row * config.CELL_SIZE + config.CELL_SIZE // 2
        if hit:
            self.particles.add_explosion(x, y, count=40, color=(255, 60, 20))
        else:
            self.particles.add_splash(x, y, count=25)

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
            if destroyed:
                self._apply_destroyed_cells_on_opponent(destroyed_cells)
                self.message = "SHIP DESTROYED!"
            else:
                self.message = "HIT!" if hit else "MISS!"
        else:
            # Gegner hat auf dich geschossen -> echtes Board schießen
            hit2, destroyed2, ship = self.player_board.shoot(row, col)
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
                    hit2, destroyed2, ship = self.player_board.shoot(row, col)
                    self._spawn_effects(self.player_board, row, col, hit2)

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
                hit2, destroyed2, ship = self.player_board.shoot(row, col)
                cell = self.player_board.get_cell(row, col)
                if cell:
                    cell.napalm_marked = True
                self._spawn_effects(self.player_board, row, col, hit2)

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

    def update(self, dt, mouse_pos):
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

    def on_mouse_down(self, pos, button):
        if button not in (1, 3) or self.game_over:
            return

        # Marker (rechtsklick) auf Gegnerboard
        if button == 3:
            cell_pos = self.opponent_board.get_cell_at_pos(pos[0], pos[1])
            if not cell_pos:
                return
            row, col = cell_pos
            cell = self.opponent_board.get_cell(row, col)
            if not cell:
                return
            if cell.is_shot() or cell.scan_marked or cell.napalm_marked:
                return
            cell.player_marker = not cell.player_marker
            return

        # nur wenn du dran bist
        if not self.player_turn:
            return

        # ability buttons
        for name, rect in self.ability_buttons:
            if rect.collidepoint(pos):
                if self.abilities[name]["charges"] <= 0:
                    return
                self.selected_ability = name
                return

        # click on opponent grid
        cell_pos = self.opponent_board.get_cell_at_pos(pos[0], pos[1])
        if not cell_pos:
            return
        row, col = cell_pos

        # ability handling
        if self.selected_ability:
            ability = self.selected_ability
            self.selected_ability = None
            self.abilities[ability]["charges"] = 0
            self._send_ability(ability, row=row, col=col)
            self.message = f"{ability.upper()} SENT..."
            return

        # normal shot
        cell = self.opponent_board.get_cell(row, col)
        if not cell or cell.is_shot():
            return

        self.ws.send_json({"type": "shot", "x": col, "y": row})
        self.message = "SHOT FIRED..."

    # ------------------------------
    # Draw
    # ------------------------------

    def _draw_ability_buttons(self, screen):
        for name, rect in self.ability_buttons:
            charges = self.abilities[name]["charges"]
            enabled = charges > 0 and self.player_turn and not self.game_over

            base = (45, 75, 120) if enabled else (45, 45, 45)
            hover = (85, 130, 200) if enabled else (70, 70, 70)
            color = hover if rect.collidepoint(pygame.mouse.get_pos()) else base
            border = (255, 215, 0) if self.selected_ability == name else (160, 210, 255)

            draw_rounded_rect(screen, (0, 0, 0), rect.move(0, 4), radius=8, alpha=120)
            draw_rounded_rect(screen, color, rect, radius=8, alpha=230)
            draw_rounded_rect(screen, border, rect, radius=8, width=2, alpha=255)

            icon = self.ability_icons.get(name)
            if icon:
                icon_surf = pygame.transform.smoothscale(icon, (42, 42))
                icon_rect = icon_surf.get_rect(center=rect.center)
                screen.blit(icon_surf, icon_rect)

            draw_text(screen, str(charges), rect.right - 12, rect.top + 6, 24, (255, 255, 255), center=True)

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
        theme = theme_manager.current
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

        panel_rect = Rect(
            config.WINDOW_WIDTH // 2 - config.BATTLE_PANEL_WIDTH // 2,
            config.BATTLE_PANEL_Y,
            config.BATTLE_PANEL_WIDTH,
            config.BATTLE_PANEL_HEIGHT,
        )
        draw_rounded_rect(screen, (0, 0, 0), panel_rect, radius=20, alpha=150)
        draw_rounded_rect(screen, theme.color_ship_border, panel_rect, radius=20, width=3, alpha=100)

        msg_color = theme.color_text_primary if self.player_turn else theme.color_text_enemy
        draw_text(
            screen,
            self.message,
            config.WINDOW_WIDTH // 2,
            panel_rect.centery,
            config.BATTLE_STATUS_FONT_SIZE,
            msg_color,
            center=True,
        )

        draw_text(
            screen,
            theme.text_battle_player_radar,
            config.PLAYER_GRID_X,
            config.GRID_OFFSET_Y - 80,
            config.BATTLE_HEADER_FONT_SIZE,
            theme.color_text_secondary,
        )
        draw_text(
            screen,
            theme.text_battle_enemy_radar,
            config.COMPUTER_GRID_X,
            config.GRID_OFFSET_Y - 80,
            config.BATTLE_HEADER_FONT_SIZE,
            theme.color_text_enemy,
        )

        self._draw_board(screen, self.player_board, show_ships=True, is_enemy=False)
        self._draw_board(screen, self.opponent_board, show_ships=False, is_enemy=True)

        self._draw_ability_buttons(screen)
        self.particles.draw(screen)