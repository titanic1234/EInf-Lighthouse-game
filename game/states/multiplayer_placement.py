"""
Schiffsplatzierungs-State (Multiplayer)
Spieler platziert seine Schiffe, wartet auf Gegner, Ready/Start Logik
"""

from pgzero.keyboard import keys
from pygame import Rect

import game.config as config
from game.entities.board import Board
from game.entities.ship import Ship
from game.graphics import (
    draw_gradient_background,
    draw_rounded_rect,
    draw_text,
    draw_grid_cell,
    GlowButton,
    _get_transformed_ship_surface,
)
from game.theme import theme_manager
from game.states.base_state import BaseState

import game.multiplayer.multiplayer_config as mconfig
from game.multiplayer.ws import WSClient


class MultiplayerPlacementState(BaseState):
    """Schiffsplatzierungs-Phase (Multiplayer)"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # WS starten und im GameManager speichern (Battle nutzt denselben Client)
        self.ws = WSClient()
        self.ws.start()
        self.game_manager.ws = self.ws

        self.player_board = Board(config.PLAYER_GRID_X, config.GRID_OFFSET_Y, "Player")

        self.ships_to_place = []
        self._create_ships()

        self.selected_ship = None
        self.current_orientation = config.ORIENTATION_HORIZONTAL

        self.preview_position = None
        self.placement_valid = False

        self.ship_list_item_rects = []
        self.mouse_pos = (0, 0)

        # Multiplayer UI / State
        self.local_ready_sent = False
        self.toast_text = ""
        self.toast_timer = 0.0
        self.host = (mconfig.ROLE == "host")

        # Board-Upload state
        self.board_sent = False  # set_board schon gesendet?

        # Buttons
        self.ready_button = self._build_ready_button()
        # optional (Server startet automatisch bei beiden ready; Button bleibt als UI)
        self.start_button = self._build_start_button()

    # ------------------------------
    # Ship / Placement helpers
    # ------------------------------
    def _get_ship_bounds(self, ship, row, col, orientation):
        coords = ship.get_coordinates_at(row, col, orientation)
        min_row = min(r for r, _ in coords)
        min_col = min(c for _, c in coords)
        max_row = max(r for r, _ in coords)
        max_col = max(c for _, c in coords)
        return min_row, min_col, max_row, max_col

    def _create_ships(self):
        for ship_type in config.SHIP_TYPES:
            ship_name, ship_length, ship_count = ship_type[:3]
            ship_shape = ship_type[3] if len(ship_type) > 3 else None
            for i in range(ship_count):
                name = f"{ship_name} #{i+1}" if ship_count > 1 else ship_name
                self.ships_to_place.append(Ship(name, ship_length, shape=ship_shape))

    def _is_ship_placed(self, ship):
        return ship in self.player_board.ships

    def _all_ships_placed(self):
        return len(self.player_board.ships) == len(self.ships_to_place)

    def _get_preview_bounds(self, ship, row, col, orientation):
        min_row, min_col, max_row, max_col = self._get_ship_bounds(ship, row, col, orientation)
        x = self.player_board.x_offset + min_col * config.CELL_SIZE
        y = self.player_board.y_offset + min_row * config.CELL_SIZE
        width = (max_col - min_col + 1) * config.CELL_SIZE
        height = (max_row - min_row + 1) * config.CELL_SIZE
        return x, y, width, height

    def _draw_ship_sprite_preview(self, screen):
        if not self.selected_ship:
            return

        if self.preview_position:
            row, col = self.preview_position
            min_row, min_col, max_row, max_col = self._get_ship_bounds(
                self.selected_ship, row, col, self.current_orientation
            )
            grid_width = max_col - min_col + 1
            grid_height = max_row - min_row + 1
            x, y, _, _ = self._get_preview_bounds(self.selected_ship, row, col, self.current_orientation)
            ship_coords = self.selected_ship.get_coordinates_at(row, col, self.current_orientation)
        else:
            min_row, min_col, max_row, max_col = self._get_ship_bounds(
                self.selected_ship, 0, 0, self.current_orientation
            )
            grid_width = max_col - min_col + 1
            grid_height = max_row - min_row + 1
            width = grid_width * config.CELL_SIZE
            height = grid_height * config.CELL_SIZE
            x = self.mouse_pos[0] - width // 2
            y = self.mouse_pos[1] - height // 2
            ship_coords = self.selected_ship.get_coordinates_at(0, 0, self.current_orientation)

        transformed = _get_transformed_ship_surface(
            self.selected_ship,
            grid_width,
            grid_height,
            self.current_orientation,
            ship_coords=ship_coords,
        )
        if transformed is None:
            return

        preview_surface = transformed.copy()
        preview_surface.set_alpha(210 if self.placement_valid else 130)
        screen.blit(preview_surface, (x, y))

    def _pick_ship_from_board(self, pos):
        cell_pos = self.player_board.get_cell_at_pos(pos[0], pos[1])
        if not cell_pos:
            return False

        cell = self.player_board.get_cell(cell_pos[0], cell_pos[1])
        if not cell or not cell.has_ship():
            return False

        picked_ship = cell.ship
        self.player_board.remove_ship(picked_ship)
        self.selected_ship = picked_ship
        self.current_orientation = picked_ship.orientation
        self.preview_position = cell_pos
        return True

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

    # ------------------------------
    # Multiplayer UI logic
    # ------------------------------
    def _build_ready_button(self):
        return GlowButton(
            config.WINDOW_WIDTH - config.BATTLE_AIRSTRIKE_BUTTON_WIDTH // 2 - 30,
            config.WINDOW_HEIGHT - config.BATTLE_AIRSTRIKE_BUTTON_HEIGHT // 2 - 30,
            config.BATTLE_AIRSTRIKE_BUTTON_WIDTH,
            config.BATTLE_AIRSTRIKE_BUTTON_HEIGHT,
            "BEREIT",
            self._on_ready_clicked,
        )

    def _build_start_button(self):
        return GlowButton(
            config.WINDOW_WIDTH - config.BATTLE_AIRSTRIKE_BUTTON_WIDTH // 2 - 30,
            config.WINDOW_HEIGHT - (config.BATTLE_AIRSTRIKE_BUTTON_HEIGHT * 3) // 2 - 40,
            config.BATTLE_AIRSTRIKE_BUTTON_WIDTH,
            config.BATTLE_AIRSTRIKE_BUTTON_HEIGHT,
            "START",
            self._on_start_clicked,
        )

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

        if self.selected_ship:
            cell_pos = self.player_board.get_cell_at_pos(mouse_pos[0], mouse_pos[1])
            if cell_pos:
                self.preview_position = cell_pos
                self.placement_valid = self.player_board.can_place_ship(
                    self.selected_ship, cell_pos[0], cell_pos[1], self.current_orientation
                )
            else:
                self.preview_position = None
                self.placement_valid = False
        else:
            self.preview_position = None
            self.placement_valid = False

        self.ready_button.update(dt, mouse_pos[0], mouse_pos[1])
        self.start_button.update(dt, mouse_pos[0], mouse_pos[1])

    def on_mouse_down(self, pos, button):
        if button != 1:
            return

        # Ready / Start Buttons
        if self._can_send_ready() and self.ready_button.is_hovered(pos[0], pos[1]):
            self.ready_button.click()
            return

        if self.host and self._can_start_game() and self.start_button.is_hovered(pos[0], pos[1]):
            self.start_button.click()
            return

        # Ship list selection
        for ship, item_rect in self.ship_list_item_rects:
            if item_rect.collidepoint(pos):
                if self._is_ship_placed(ship):
                    self.player_board.remove_ship(ship)
                self.selected_ship = ship
                self.current_orientation = ship.orientation
                return

        # Pick already placed ship
        if not self.selected_ship and self._pick_ship_from_board(pos):
            return

        # Place ship
        if self.selected_ship and self.preview_position and self.placement_valid:
            row, col = self.preview_position
            if self.player_board.place_ship(self.selected_ship, row, col, self.current_orientation):
                self.selected_ship = None
                self.preview_position = None
                self.placement_valid = False

    def on_key_down(self, key, mod=0):
        if key == keys.R and self.selected_ship:
            self.current_orientation = (self.current_orientation + 1) % self.selected_ship.get_rotation_count()

    # ------------------------------
    # Draw
    # ------------------------------
    def draw(self, screen):
        theme = theme_manager.current
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

        # Top panel
        panel_rect = Rect(
            config.WINDOW_WIDTH // 2 - config.PLACEMENT_PANEL_WIDTH // 2,
            config.PLACEMENT_PANEL_Y,
            config.PLACEMENT_PANEL_WIDTH,
            config.PLACEMENT_PANEL_HEIGHT,
        )
        draw_rounded_rect(screen, (0, 0, 0), panel_rect, radius=20, alpha=150)
        draw_rounded_rect(screen, theme.color_ship_border, panel_rect, radius=20, width=3, alpha=100)

        draw_text(
            screen,
            "MULTIPLAYER - SCHIFFE PLATZIEREN",
            config.WINDOW_WIDTH // 2,
            panel_rect.centery,
            config.PLACEMENT_TITLE_FONT_SIZE,
            theme.color_text_primary,
            center=True,
        )

        # Multiplayer status panel (links oben)
        self._draw_multiplayer_status(screen)

        # Anleitung
        if self.selected_ship:
            display_name = theme_manager.get_ship_display_name(self.selected_ship.name)
            instruction = f"AUSGEWÄHLTES SCHIFF: {display_name.upper()} (LÄNGE: {self.selected_ship.get_size()})"
        else:
            instruction = "WÄHLE EIN SCHIFF AUS DER LISTE ODER KLICKE EIN SCHIFF AUF DEM FELD"

        draw_text(
            screen,
            instruction,
            config.WINDOW_WIDTH // 2,
            panel_rect.bottom + 50,
            config.PLACEMENT_INSTRUCTION_FONT_SIZE,
            theme.color_text_secondary,
            center=True,
        )
        draw_text(
            screen,
            "Linksklick: wählen/platzieren | R: rotieren",
            config.WINDOW_WIDTH // 2,
            config.WINDOW_HEIGHT - config.PLACEMENT_INSTRUCTION_MARGIN_BOTTOM,
            config.PLACEMENT_INSTRUCTION_FONT_SIZE,
            theme.color_text_secondary,
            center=True,
        )

        # Board
        self._draw_board(screen)

        # Progress panel
        prog_rect = Rect(
            config.WINDOW_WIDTH - config.PLACEMENT_PROGRESS_PANEL_WIDTH - config.PLACEMENT_PROGRESS_PANEL_MARGIN_RIGHT,
            config.PLACEMENT_PROGRESS_PANEL_Y,
            config.PLACEMENT_PROGRESS_PANEL_WIDTH,
            config.PLACEMENT_PROGRESS_PANEL_HEIGHT,
        )
        draw_rounded_rect(screen, (0, 0, 0), prog_rect, radius=15, alpha=150)

        progress = f"PLATZIERT: {len(self.player_board.ships)} VON {len(self.ships_to_place)}"
        draw_text(
            screen,
            progress,
            prog_rect.centerx,
            prog_rect.centery,
            config.PLACEMENT_PROGRESS_FONT_SIZE,
            (255, 200, 100),
            center=True,
        )

        # Ship list
        self._draw_ship_list(screen)

        # Buttons
        if self._can_send_ready():
            self.ready_button.draw(screen, default_color=(30, 110, 70), hover_color=(50, 170, 100))

        if self.host and self._can_start_game():
            self.start_button.draw(screen, default_color=(30, 80, 140), hover_color=(60, 120, 220))
        elif self.host and self.local_ready_sent:
            draw_text(
                screen,
                "WARTEN AUF GEGNER...",
                self.start_button.x,
                self.start_button.y,
                config.BATTLE_STAT_FONT_SIZE,
                theme.color_text_secondary,
                center=True,
            )

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

    def _draw_board(self, screen):
        board = self.player_board
        theme = theme_manager.current

        bg_rect = Rect(
            board.x_offset - 10,
            board.y_offset - 10,
            config.GRID_SIZE * config.CELL_SIZE + 20,
            config.GRID_SIZE * config.CELL_SIZE + 20,
        )
        draw_rounded_rect(screen, theme.color_panel_bg, bg_rect, radius=10, alpha=180)
        draw_rounded_rect(screen, theme.color_ship_border, bg_rect, radius=10, width=2, alpha=80)

        for row in range(config.GRID_SIZE):
            for col in range(config.GRID_SIZE):
                x = board.x_offset + col * config.CELL_SIZE
                y = board.y_offset + row * config.CELL_SIZE
                cell = board.get_cell(row, col)
                draw_grid_cell(screen, x, y, cell, is_enemy=False, show_ships=True)

        if self.selected_ship:
            self._draw_ship_sprite_preview(screen)

    def _draw_ship_list(self, screen):
        x = self.player_board.x_offset + config.GRID_SIZE * config.CELL_SIZE + 50
        y = self.player_board.y_offset + 10

        draw_text(screen, "SCHIFFE", x, y - 36, config.PLACEMENT_SHIP_LIST_TITLE_FONT_SIZE, (150, 200, 255))

        self.ship_list_item_rects = []
        available_ships = [ship for ship in self.ships_to_place if not self._is_ship_placed(ship)]
        cursor_y = y
        for ship in available_ships:
            coords = ship.get_coordinates_at(0, 0, ship.orientation)
            min_row, min_col, max_row, max_col = self._get_ship_bounds(ship, 0, 0, ship.orientation)
            grid_width = max_col - min_col + 1
            grid_height = max_row - min_row + 1
            sprite = _get_transformed_ship_surface(
                ship,
                grid_width,
                grid_height,
                ship.orientation,
                ship_coords=coords,
            )
            if sprite is None:
                continue

            sprite_width = sprite.get_width()
            sprite_height = sprite.get_height()
            sprite_x = x
            sprite_y = cursor_y

            if ship == self.selected_ship:
                highlight_rect = Rect(sprite_x - 6, sprite_y - 6, sprite_width + 12, sprite_height + 12)
                draw_rounded_rect(screen, (80, 180, 255), highlight_rect, radius=8, width=2, alpha=160)

            screen.blit(sprite, (sprite_x, sprite_y))

            item_rect = Rect(sprite_x, sprite_y, sprite_width, sprite_height)
            self.ship_list_item_rects.append((ship, item_rect))
            cursor_y += sprite_height + 24