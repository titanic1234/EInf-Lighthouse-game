"""
Kampf-State
Spieler vs Computer
"""

import pygame
from pygame import Rect
import game.config as config
from game.entities.board import Board
from game.ai.computer_ai import ComputerAI
from game.graphics import draw_gradient_background, draw_rounded_rect, ParticleSystem, draw_text, GlowButton, draw_grid_cell
from game.theme import theme_manager
from game.states.base_state import BaseState


class BattleState(BaseState):
    """Kampf-Phase: Spieler gegen Computer"""

    def __init__(self, game_manager):
        """Initialisiert die Kampfphase"""
        super().__init__(game_manager)
        self.player_board = game_manager.player_board

        self.computer_board = Board(config.COMPUTER_GRID_X, config.GRID_OFFSET_Y, "Computer")
        self.computer_board.place_ships_randomly()

        self.ai = ComputerAI()

        self.player_turn = True
        self.game_over = False
        self.winner = None

        self.message = "AWAITING ORDERS - SELECT TARGET"
        self.last_shot_result = None

        self.computer_delay = 0
        self.computer_delay_time = config.BATTLE_COMPUTER_DELAY_TIME

        # Effekte
        self.particles = ParticleSystem()

        # Special Weapon
        theme = theme_manager.current
        self.airstrike_available = True
        self.airstrike_active = False
        self.airstrike_button = GlowButton(
            config.WINDOW_WIDTH // 2,
            config.WINDOW_HEIGHT - config.BATTLE_AIRSTRIKE_BUTTON_MARGIN_BOTTOM,
            config.BATTLE_AIRSTRIKE_BUTTON_WIDTH,
            config.BATTLE_AIRSTRIKE_BUTTON_HEIGHT,
            theme.text_airstrike_btn,
            self._activate_airstrike,
        )

    def _activate_airstrike(self):
        if self.airstrike_available and self.player_turn:
            self.airstrike_active = True
            self.message = theme_manager.current.text_airstrike_active

    def update(self, dt, mouse_pos):
        """Aktualisiert die Kampfphase"""
        self.particles.update(dt)

        if self.game_over:
            return

        # Computer-Zug mit Verzoegerung
        if not self.player_turn:
            self.computer_delay += dt
            if self.computer_delay >= self.computer_delay_time:
                self._computer_turn()
                self.computer_delay = 0

        if self.airstrike_available:
            self.airstrike_button.update(dt, mouse_pos[0], mouse_pos[1])

    def on_mouse_down(self, pos, button):
        """Behandelt Mausklicks"""
        if button == 1 and self.player_turn and not self.game_over:
            if self.airstrike_available and self.airstrike_button.hovered:
                self.airstrike_button.click()
                return

            cell_pos = self.computer_board.get_cell_at_pos(pos[0], pos[1])
            if cell_pos:
                if self.airstrike_active:
                    self._player_airstrike(cell_pos[0], cell_pos[1])
                else:
                    self._player_shoot(cell_pos[0], cell_pos[1])

    def _spawn_effects(self, board, row, col, hit):
        """Spawnt Partikel an der getroffenen Zelle"""
        x = board.x_offset + col * config.CELL_SIZE + config.CELL_SIZE // 2
        y = board.y_offset + row * config.CELL_SIZE + config.CELL_SIZE // 2
        if hit:
            self.particles.add_explosion(x, y, count=40, color=(255, 60, 20))
        else:
            self.particles.add_splash(x, y, count=25)

    def _player_airstrike(self, center_row, center_col):
        """Fuehrt einen Airstrike (3x3) aus."""
        theme = theme_manager.current
        self.airstrike_available = False
        self.airstrike_active = False

        hit_any = False
        destroyed_any = False

        # Airstrike visual effect at center
        cx = self.computer_board.x_offset + center_col * config.CELL_SIZE + config.CELL_SIZE // 2
        cy = self.computer_board.y_offset + center_row * config.CELL_SIZE + config.CELL_SIZE // 2
        self.particles.add_explosion(cx, cy, count=100, color=(255, 200, 50))

        for r in range(center_row - 1, center_row + 2):
            for c in range(center_col - 1, center_col + 2):
                cell = self.computer_board.get_cell(r, c)
                if cell and not cell.is_shot():
                    self.game_manager.shots_fired += 1
                    hit, destroyed, ship = self.computer_board.shoot(r, c)
                    self._spawn_effects(self.computer_board, r, c, hit)
                    if hit:
                        self.game_manager.shots_hit += 1
                        hit_any = True
                    if destroyed:
                        destroyed_any = True

        if destroyed_any:
            self.message = theme.text_airstrike_critical
        elif hit_any:
            self.message = theme.text_airstrike_success
        else:
            self.message = theme.text_airstrike_miss

        self._check_game_over_after_player_action(hit_any)

    def _player_shoot(self, row, col):
        """Spieler schiesst"""
        theme = theme_manager.current
        cell = self.computer_board.get_cell(row, col)

        if cell.is_shot():
            self.message = theme.text_already_compromised
            return

        self.game_manager.shots_fired += 1
        hit, destroyed, ship = self.computer_board.shoot(row, col)

        self._spawn_effects(self.computer_board, row, col, hit)

        if hit:
            self.game_manager.shots_hit += 1
            if destroyed:
                self.message = theme.text_target_destroyed
            else:
                self.message = theme.text_target_hit
        else:
            self.message = theme.text_target_miss

        self._check_game_over_after_player_action(hit)

    def _check_game_over_after_player_action(self, hit):
        if self.computer_board.all_ships_destroyed():
            self.game_over = True
            self.winner = "Player"
            self.computer_delay_time = 2.0  # Wait before ending
            self._end_game()
        else:
            if not hit:
                self.player_turn = False
                self.message = theme_manager.current.text_computer_turn

    def _computer_turn(self):
        """Computer macht seinen Zug"""
        row, col = self.ai.get_next_shot(self.player_board)
        hit, destroyed, ship = self.player_board.shoot(row, col)

        self.ai.register_shot_result(row, col, hit, destroyed, ship)

        self._spawn_effects(self.player_board, row, col, hit)

        if hit:
            if destroyed:
                ship_name = theme_manager.get_ship_display_name(ship.name)
                self.message = f"ALERT: ALLY {ship_name.upper()} SUNK!"
            else:
                self.message = f"WARNING: HULL BREACH AT ({row +1}, {col +1})!"
        else:
            self.message = f"ENEMY MISSED AT ({row + 1}, {col + 1})."

        if self.player_board.all_ships_destroyed():
            self.game_over = True
            self.winner = "Computer"
            self._end_game()
        else:
            if not hit:
                self.player_turn = True
                self.message += " - YOUR TURN!"

    def _end_game(self):
        """Beendet das Spiel"""
        self.game_manager.winner = self.winner
        # Der State-Wechsel wird hier sofort gemacht.
        # Im Idealfall waere hier noch ein kleiner Timer fuer die letzten Partikel,
        # aber wir halten es einfach.
        self.game_manager.change_state(config.STATE_GAME_OVER)

    def draw(self, screen):
        """Zeichnet die Kampfphase"""
        theme = theme_manager.current
        # Tactical Background
        draw_gradient_background(screen, time_value=self.game_manager.time_elapsed)

        # Title Menu Bar / Status
        panel_rect = Rect(
            config.WINDOW_WIDTH // 2 - config.BATTLE_PANEL_WIDTH // 2,
            config.BATTLE_PANEL_Y,
            config.BATTLE_PANEL_WIDTH,
            config.BATTLE_PANEL_HEIGHT,
        )
        draw_rounded_rect(screen, (0, 0, 0), panel_rect, radius=20, alpha=150)
        draw_rounded_rect(screen, theme.color_ship_border, panel_rect, radius=20, width=3, alpha=100)

        # Status Message (Glowing)
        msg_color = theme.color_text_primary if self.player_turn else theme.color_text_enemy
        draw_text(screen, self.message, config.WINDOW_WIDTH // 2, panel_rect.centery, config.BATTLE_STATUS_FONT_SIZE, msg_color, center=True)

        # Board Headers
        draw_text(screen, theme.text_battle_player_radar, config.PLAYER_GRID_X, config.GRID_OFFSET_Y - 80, config.BATTLE_HEADER_FONT_SIZE, theme.color_text_secondary)
        draw_text(screen, theme.text_battle_enemy_radar, config.COMPUTER_GRID_X, config.GRID_OFFSET_Y - 80, config.BATTLE_HEADER_FONT_SIZE, theme.color_text_enemy)

        # Zeichne Boards
        self._draw_board(screen, self.player_board, show_ships=True, is_enemy=False)
        self._draw_board(screen, self.computer_board, show_ships=False, is_enemy=True)

        if self.airstrike_available:
            self.airstrike_button.draw(screen)

        # Draw particles
        self.particles.draw(screen)

        # Statistiken
        self._draw_statistics(screen)

    def _draw_board(self, screen, board, show_ships=True, is_enemy=False):
        """Zeichnet ein Spielfeld"""
        theme = theme_manager.current

        # Draw board background glow (Blue for player, Red for enemy)
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

                draw_grid_cell(screen, x, y, cell, is_enemy=is_enemy, show_ships=show_ships)

        # Koordinaten-Labels
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

    def _draw_statistics(self, screen):
        """Zeichnet Statistiken in modernen Panels"""
        y = config.GRID_OFFSET_Y + config.GRID_SIZE * config.CELL_SIZE + config.BATTLE_STAT_PANEL_OFFSET_Y

        # Player Panel
        p_rect = Rect(config.PLAYER_GRID_X, y, config.BATTLE_STAT_PANEL_WIDTH, config.BATTLE_STAT_PANEL_HEIGHT)
        draw_rounded_rect(screen, (0, 0, 0), p_rect, radius=15, alpha=150)
        draw_rounded_rect(screen, (50, 150, 255), p_rect, radius=15, width=3, alpha=100)

        player_ships_alive = sum(1 for ship in self.player_board.ships if not ship.is_destroyed())
        player_ships_total = len(self.player_board.ships)

        draw_text(
            screen,
            f"EIGENE SCHIFFE EINSATZBEREIT: {player_ships_alive}/{player_ships_total}",
            config.PLAYER_GRID_X + 25,
            y + 25,
            config.BATTLE_STAT_FONT_SIZE,
            (100, 255, 100),
        )

        # Computer Panel
        c_rect = Rect(config.COMPUTER_GRID_X, y, config.BATTLE_STAT_PANEL_WIDTH, config.BATTLE_STAT_PANEL_HEIGHT)
        draw_rounded_rect(screen, (0, 0, 0), c_rect, radius=15, alpha=150)
        draw_rounded_rect(screen, (255, 50, 50), c_rect, radius=15, width=3, alpha=100)

        computer_ships_alive = sum(1 for ship in self.computer_board.ships if not ship.is_destroyed())
        computer_ships_total = len(self.computer_board.ships)

        draw_text(
            screen,
            f"GEGNERISCHE SCHIFFE AKTIV: {computer_ships_alive}/{computer_ships_total}",
            config.COMPUTER_GRID_X + 25,
            y + 25,
            config.BATTLE_STAT_FONT_SIZE,
            (255, 100, 100),
        )

    def on_resize(self, width, height):
        self.player_board.x_offset = config.PLAYER_GRID_X
        self.player_board.y_offset = config.GRID_OFFSET_Y
        self.computer_board.x_offset = config.COMPUTER_GRID_X
        self.computer_board.y_offset = config.GRID_OFFSET_Y
        self.airstrike_button = GlowButton(
            config.WINDOW_WIDTH // 2,
            config.WINDOW_HEIGHT - config.BATTLE_AIRSTRIKE_BUTTON_MARGIN_BOTTOM,
            config.BATTLE_AIRSTRIKE_BUTTON_WIDTH,
            config.BATTLE_AIRSTRIKE_BUTTON_HEIGHT,
            theme_manager.current.text_airstrike_btn,
            self._activate_airstrike,
        )