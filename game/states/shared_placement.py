"""Gemeinsame Placement-Logik für Singleplayer und Multiplayer."""

from pgzero.keyboard import keys
from pgzero.rect import Rect

import game.config as config
from game.entities.board import Board
from game.entities.ship import Ship
from game.graphics import (
    GlowButton,
    _get_transformed_ship_surface,
    draw_gradient_background,
    draw_grid_cell,
    draw_rounded_rect,
    draw_text,
)
from game.states.base_state import BaseState
from game.theme import theme_manager


class SharedPlacementState(BaseState):
    """Gemeinsame UI/Input-Logik für Schiffsplatzierung."""

    title_text = "SCHIFFE PLATZIEREN"
    instruction_hint = "Linksklick: Schiff wählen/platzieren | R: rotieren"

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.player_board = Board(config.PLAYER_GRID_X, config.GRID_OFFSET_Y, "Player")
        self.ships_to_place = []
        self._create_ships()

        self.selected_ship = None
        self.current_orientation = config.ORIENTATION_HORIZONTAL
        self.preview_position = None
        self.placement_valid = False
        self.ship_list_item_rects = []
        self.mouse_pos = (0, 0)

    def _create_ships(self):
        for ship_type in config.SHIP_TYPES:
            ship_name, ship_length, ship_count = ship_type[:3]
            ship_shape = ship_type[3] if len(ship_type) > 3 else None
            for i in range(ship_count):
                name = f"{ship_name} #{i + 1}" if ship_count > 1 else ship_name
                self.ships_to_place.append(Ship(name, ship_length, shape=ship_shape))

    def _is_ship_placed(self, ship):
        return ship in self.player_board.ships

    def _all_ships_placed(self):
        return len(self.player_board.ships) == len(self.ships_to_place)

    def _get_ship_bounds(self, ship, row, col, orientation):
        coords = ship.get_coordinates_at(row, col, orientation)
        min_row = min(r for r, _ in coords)
        min_col = min(c for _, c in coords)
        max_row = max(r for r, _ in coords)
        max_col = max(c for _, c in coords)
        return min_row, min_col, max_row, max_col

    def _get_preview_bounds(self, ship, row, col, orientation):
        min_row, min_col, max_row, max_col = self._get_ship_bounds(ship, row, col, orientation)
        x = self.player_board.x_offset + min_col * config.CELL_SIZE
        y = self.player_board.y_offset + min_row * config.CELL_SIZE
        width = (max_col - min_col + 1) * config.CELL_SIZE
        height = (max_row - min_row + 1) * config.CELL_SIZE
        return x, y, width, height

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
            min_row, min_col, max_row, max_col = self._get_ship_bounds(self.selected_ship, 0, 0, self.current_orientation)
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

    def update(self, dt, mouse_pos):
        self.player_board.all_ships_placed = self._all_ships_placed()
        self.mouse_pos = mouse_pos

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

        self._update_action_buttons(dt, mouse_pos)

    def on_mouse_down(self, pos, button):
        if button != 1:
            return

        if self._handle_action_button_click(pos):
            return

        for ship, item_rect in self.ship_list_item_rects:
            if item_rect.collidepoint(pos):
                if self._is_ship_placed(ship):
                    self.player_board.remove_ship(ship)
                self.selected_ship = ship
                self.current_orientation = ship.orientation
                return

        if not self.selected_ship and self._pick_ship_from_board(pos):
            return

        if self.selected_ship and self.preview_position and self.placement_valid:
            row, col = self.preview_position
            if self.player_board.place_ship(self.selected_ship, row, col, self.current_orientation):
                self.selected_ship = None
                self.preview_position = None
                self.placement_valid = False

    def on_key_down(self, key, mod=0):
        if key == keys.R and self.selected_ship:
            self.current_orientation = (self.current_orientation + 1) % self.selected_ship.get_rotation_count()

    def draw(self, screen):
        theme = theme_manager.current
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

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
            self.title_text,
            config.WINDOW_WIDTH // 2,
            panel_rect.centery,
            config.PLACEMENT_TITLE_FONT_SIZE,
            theme.color_text_primary,
            center=True,
        )

        self._draw_status_panels(screen)

        instruction = self._get_instruction_text()
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
            self.instruction_hint,
            config.WINDOW_WIDTH // 2,
            config.WINDOW_HEIGHT - config.PLACEMENT_INSTRUCTION_MARGIN_BOTTOM,
            config.PLACEMENT_INSTRUCTION_FONT_SIZE,
            theme.color_text_secondary,
            center=True,
        )

        self._draw_board(screen)
        self._draw_progress(screen)
        self._draw_ship_list(screen)
        self._draw_action_buttons(screen)

    def _draw_status_panels(self, screen):
        """Hook for subclasses."""

    def _get_instruction_text(self):
        if self.selected_ship:
            display_name = theme_manager.get_ship_display_name(self.selected_ship.name)
            return f"AUSGEWÄHLTES SCHIFF: {display_name.upper()} (LÄNGE: {self.selected_ship.get_size()})"
        return "WÄHLE EIN SCHIFF AUS DER LISTE ODER KLICKE EIN SCHIFF AUF DEM FELD"

    def _draw_progress(self, screen):
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
            self.ship_list_item_rects.append((ship, Rect(sprite_x, sprite_y, sprite_width, sprite_height)))
            cursor_y += sprite_height + 24

    def _update_action_buttons(self, dt, mouse_pos):
        """Hook for subclasses."""

    def _handle_action_button_click(self, pos):
        """Hook for subclasses."""
        return False

    def _draw_action_buttons(self, screen):
        """Hook for subclasses."""

    def on_resize(self, width, height):
        self.player_board.x_offset = config.PLAYER_GRID_X
        self.player_board.y_offset = config.GRID_OFFSET_Y

    @staticmethod
    def build_primary_action_button(text, action, y_offset):
        return GlowButton(
            config.WINDOW_WIDTH - config.BATTLE_AIRSTRIKE_BUTTON_WIDTH // 2 - 30,
            config.WINDOW_HEIGHT - config.BATTLE_AIRSTRIKE_BUTTON_HEIGHT // 2 - y_offset,
            config.BATTLE_AIRSTRIKE_BUTTON_WIDTH,
            config.BATTLE_AIRSTRIKE_BUTTON_HEIGHT,
            text,
            action,
        )