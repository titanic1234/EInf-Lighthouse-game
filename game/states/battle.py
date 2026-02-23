"""
Kampf-State
Spieler vs Computer
"""

import pygame
from pygame import Rect
from game.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, GRID_SIZE, CELL_SIZE,
    COLOR_WHITE, COLOR_BLACK, COLOR_BLUE, COLOR_RED, COLOR_GREEN, COLOR_GRAY,
    PLAYER_GRID_X, COMPUTER_GRID_X, GRID_OFFSET_Y,
    CELL_SHIP, CELL_HIT, CELL_MISS, CELL_DESTROYED,
    STATE_GAME_OVER
)
from game.entities.board import Board
from game.ai.computer_ai import ComputerAI
from game.graphics import draw_gradient_background, draw_rounded_rect, ParticleSystem
from game.states.base_state import BaseState


class BattleState(BaseState):
    """Kampf-Phase: Spieler gegen Computer"""

    def __init__(self, game_manager):
        """Initialisiert die Kampfphase"""
        super().__init__(game_manager)
        self.player_board = game_manager.player_board

        self.computer_board = Board(COMPUTER_GRID_X, GRID_OFFSET_Y, "Computer")
        self.computer_board.place_ships_randomly()

        self.ai = ComputerAI()

        self.player_turn = True
        self.game_over = False
        self.winner = None

        self.message = "AWAITING ORDERS - SELECT TARGET"
        self.last_shot_result = None

        self.computer_delay = 0
        self.computer_delay_time = 1.0  # Sekunden
        
        # Effekte
        self.particles = ParticleSystem()

    def update(self, dt, mouse_pos):
        """Aktualisiert die Kampfphase"""
        self.particles.update(dt)
        
        if self.game_over:
            return

        # Computer-Zug mit Verzögerung
        if not self.player_turn:
            self.computer_delay += dt
            if self.computer_delay >= self.computer_delay_time:
                self._computer_turn()
                self.computer_delay = 0

    def on_mouse_down(self, pos, button):
        """Behandelt Mausklicks"""
        if button == 1 and self.player_turn and not self.game_over:
            cell_pos = self.computer_board.get_cell_at_pos(pos[0], pos[1])
            if cell_pos:
                self._player_shoot(cell_pos[0], cell_pos[1])

    def _spawn_effects(self, board, row, col, hit):
        """Spawnt Partikel an der getroffenen Zelle"""
        x = board.x_offset + col * CELL_SIZE + CELL_SIZE // 2
        y = board.y_offset + row * CELL_SIZE + CELL_SIZE // 2
        if hit:
            self.particles.add_explosion(x, y, count=40, color=(255, 60, 20))
        else:
            self.particles.add_splash(x, y, count=25)

    def _player_shoot(self, row, col):
        """Spieler schießt"""
        cell = self.computer_board.get_cell(row, col)

        if cell.is_shot():
            self.message = "SECTOR ALREADY COMPROMISED!"
            return

        hit, destroyed, ship = self.computer_board.shoot(row, col)
        
        self._spawn_effects(self.computer_board, row, col, hit)

        if hit:
            if destroyed:
                self.message = f"CRITICAL HIT! ENEMY {ship.name.upper()} DESTROYED!"
            else:
                self.message = "TARGET HIT!"
        else:
            self.message = "MISSED TARGET."

        if self.computer_board.all_ships_destroyed():
            self.game_over = True
            self.winner = "Player"
            self.computer_delay_time = 2.0 # Wait before ending
            self._end_game()
        else:
            if not hit:
                self.player_turn = False
                self.message = "ENEMY TURN IN PROGRESS..."

    def _computer_turn(self):
        """Computer macht seinen Zug"""
        row, col = self.ai.get_next_shot(self.player_board)
        hit, destroyed, ship = self.player_board.shoot(row, col)

        self.ai.register_shot_result(row, col, hit, destroyed, ship)
        
        self._spawn_effects(self.player_board, row, col, hit)

        if hit:
            if destroyed:
                self.message = f"ALERT: ALLY {ship.name.upper()} SUNK!"
            else:
                self.message = f"WARNING: HULL BREACH AT ({row}, {col})!"
        else:
            self.message = f"ENEMY MISSED AT ({row}, {col})."

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
        # Im Idealfall wäre hier noch ein kleiner Timer für die letzten Partikel,
        # aber wir halten es einfach.
        self.game_manager.change_state(STATE_GAME_OVER)

    def draw(self, screen):
        """Zeichnet die Kampfphase"""
        # Tactical Background
        draw_gradient_background(screen.surface, (15, 20, 35), (10, 5, 20))

        # Title Menu Bar / Status
        panel_rect = Rect(WINDOW_WIDTH//2 - 400, 10, 800, 60)
        draw_rounded_rect(screen.surface, (0, 0, 0), panel_rect, radius=15, alpha=150)
        draw_rounded_rect(screen.surface, (100, 150, 255), panel_rect, radius=15, width=2, alpha=100)

        # Status Message (Glowing)
        msg_color = (100, 255, 100) if self.player_turn else (255, 100, 100)
        screen.draw.text(self.message, center=(WINDOW_WIDTH // 2, 40),
                        fontsize=32, color=msg_color)

        # Board Headers
        screen.draw.text("ALLIED FLEET RADAR", (PLAYER_GRID_X, GRID_OFFSET_Y - 30),
                        fontsize=24, color=(150, 200, 255))
        screen.draw.text("ENEMY FLEET RADAR", (COMPUTER_GRID_X, GRID_OFFSET_Y - 30),
                        fontsize=24, color=(255, 150, 150))

        # Zeichne Boards
        self._draw_board(screen, self.player_board, show_ships=True, is_enemy=False)
        self._draw_board(screen, self.computer_board, show_ships=False, is_enemy=True)

        # Draw particles
        self.particles.draw(screen.surface)

        # Statistiken
        self._draw_statistics(screen)

    def _draw_board(self, screen, board, show_ships=True, is_enemy=False):
        """Zeichnet ein Spielfeld"""
        
        # Draw board background glow (Blue for player, Red for enemy)
        bg_rect = Rect(board.x_offset - 10, board.y_offset - 10, GRID_SIZE * CELL_SIZE + 20, GRID_SIZE * CELL_SIZE + 20)
        border_color = (200, 50, 50) if is_enemy else (50, 150, 255)
        bg_color = (40, 10, 10) if is_enemy else (10, 20, 40)
        draw_rounded_rect(screen.surface, bg_color, bg_rect, radius=10, alpha=180)
        draw_rounded_rect(screen.surface, border_color, bg_rect, radius=10, width=2, alpha=80)

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = board.x_offset + col * CELL_SIZE
                y = board.y_offset + row * CELL_SIZE
                cell = board.get_cell(row, col)
                cell_rect = Rect(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)
                
                # Base Water Cell
                draw_rounded_rect(screen.surface, (20, 40, 80), cell_rect, radius=4, alpha=100)

                # Schiff
                if show_ships and cell.has_ship() and not cell.is_shot():
                     draw_rounded_rect(screen.surface, (100, 200, 255), cell_rect, radius=4, alpha=200)

                # Treffer/Fehlschuss prozedural zeichnen
                if cell.status == CELL_HIT:
                    draw_rounded_rect(screen.surface, (255, 50, 50), cell_rect, radius=4, alpha=180)
                    pygame.draw.line(screen.surface, (255, 255, 255), (x + 8, y + 8), (x + CELL_SIZE - 8, y + CELL_SIZE - 8), 3)
                    pygame.draw.line(screen.surface, (255, 255, 255), (x + CELL_SIZE - 8, y + 8), (x + 8, y + CELL_SIZE - 8), 3)
                elif cell.status == CELL_MISS:
                    pygame.draw.circle(screen.surface, (150, 200, 255), (x + CELL_SIZE//2, y + CELL_SIZE//2), 6)
                elif cell.status == CELL_DESTROYED:
                    draw_rounded_rect(screen.surface, (150, 0, 0), cell_rect, radius=4, alpha=220)
                    pygame.draw.line(screen.surface, (255, 100, 100), (x + 8, y + 8), (x + CELL_SIZE - 8, y + CELL_SIZE - 8), 4)
                    pygame.draw.line(screen.surface, (255, 100, 100), (x + CELL_SIZE - 8, y + 8), (x + 8, y + CELL_SIZE - 8), 4)

                # Grid-Linien (Subtle)
                screen.draw.rect(Rect(x, y, CELL_SIZE, CELL_SIZE), (40, 60, 100) if not is_enemy else (100, 40, 40))

        # Koordinaten-Labels
        label_color = (150, 200, 255) if not is_enemy else (255, 150, 150)
        for i in range(GRID_SIZE):
            screen.draw.text(str(i), (board.x_offset - 25, board.y_offset + i * CELL_SIZE + CELL_SIZE // 2 - 8), fontsize=18, color=label_color)
            screen.draw.text(chr(65 + i), center=(board.x_offset + i * CELL_SIZE + CELL_SIZE // 2, board.y_offset - 20), fontsize=18, color=label_color)

    def _draw_statistics(self, screen):
        """Zeichnet Statistiken in modernen Panels"""
        y = GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 30

        # Player Panel
        p_rect = Rect(PLAYER_GRID_X, y, 300, 60)
        draw_rounded_rect(screen.surface, (0, 0, 0), p_rect, radius=10, alpha=150)
        draw_rounded_rect(screen.surface, (50, 150, 255), p_rect, radius=10, width=2, alpha=100)
        
        player_ships_alive = sum(1 for ship in self.player_board.ships if not ship.is_destroyed())
        player_ships_total = len(self.player_board.ships)

        screen.draw.text(f"ALLIED UNITS ACTIVE: {player_ships_alive}/{player_ships_total}",
                        (PLAYER_GRID_X + 15, y + 20), fontsize=22, color=(100, 255, 100))

        # Computer Panel
        c_rect = Rect(COMPUTER_GRID_X, y, 300, 60)
        draw_rounded_rect(screen.surface, (0, 0, 0), c_rect, radius=10, alpha=150)
        draw_rounded_rect(screen.surface, (255, 50, 50), c_rect, radius=10, width=2, alpha=100)
        
        computer_ships_alive = sum(1 for ship in self.computer_board.ships if not ship.is_destroyed())
        computer_ships_total = len(self.computer_board.ships)

        screen.draw.text(f"ENEMY UNITS ACTIVE: {computer_ships_alive}/{computer_ships_total}",
                        (COMPUTER_GRID_X + 15, y + 20), fontsize=22, color=(255, 100, 100))


