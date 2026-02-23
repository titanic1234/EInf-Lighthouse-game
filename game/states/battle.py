"""
Kampf-State
Spieler vs Computer
"""

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
import time


class BattleState:
    """Kampf-Phase: Spieler gegen Computer"""

    def __init__(self, game_manager):
        """
        Initialisiert die Kampfphase

        Args:
            game_manager: Referenz zum GameManager
        """
        self.game_manager = game_manager

        # Spieler-Board wurde bereits in PlacementState erstellt
        self.player_board = game_manager.player_board

        # Computer-Board erstellen und Schiffe zufällig platzieren
        self.computer_board = Board(COMPUTER_GRID_X, GRID_OFFSET_Y, "Computer")
        self.computer_board.place_ships_randomly()

        # KI
        self.ai = ComputerAI()

        # Spielzustand
        self.player_turn = True
        self.game_over = False
        self.winner = None

        # Feedback-Nachrichten
        self.message = "Dein Zug! Klicke auf das Computer-Feld."
        self.last_shot_result = None

        # Verzögerung für Computer-Zug
        self.computer_delay = 0
        self.computer_delay_time = 1.0  # Sekunden

    def update(self, dt, mouse_pos):
        """
        Aktualisiert die Kampfphase

        Args:
            dt: Delta-Zeit
            mouse_pos: Tuple (x, y) der Mausposition
        """
        if self.game_over:
            return

        # Computer-Zug mit Verzögerung
        if not self.player_turn:
            self.computer_delay += dt
            if self.computer_delay >= self.computer_delay_time:
                self._computer_turn()
                self.computer_delay = 0

    def on_mouse_down(self, pos, button):
        """
        Behandelt Mausklicks

        Args:
            pos: Tuple (x, y)
            button: Maustaste
        """
        if button == 1 and self.player_turn and not self.game_over:
            # Spieler schießt auf Computer-Board
            cell_pos = self.computer_board.get_cell_at_pos(pos[0], pos[1])

            if cell_pos:
                self._player_shoot(cell_pos[0], cell_pos[1])

    def _player_shoot(self, row, col):
        """
        Spieler schießt

        Args:
            row, col: Zielposition
        """
        cell = self.computer_board.get_cell(row, col)

        if cell.is_shot():
            self.message = "Diese Zelle wurde bereits beschossen!"
            return

        hit, destroyed, ship = self.computer_board.shoot(row, col)

        if hit:
            if destroyed:
                self.message = f"Treffer und versenkt! {ship.name} wurde versenkt!"
            else:
                self.message = "Treffer!"
        else:
            self.message = "Fehlschuss!"

        # Prüfe Gewinnbedingung
        if self.computer_board.all_ships_destroyed():
            self.game_over = True
            self.winner = "Player"
            self._end_game()
        else:
            # Computer ist dran
            if not hit:  # Nur wenn Fehlschuss, sonst nochmal Spieler
                self.player_turn = False
                self.message = "Computer ist am Zug..."

    def _computer_turn(self):
        """Computer macht seinen Zug"""
        row, col = self.ai.get_next_shot(self.player_board)
        hit, destroyed, ship = self.player_board.shoot(row, col)

        # Registriere Ergebnis bei KI
        self.ai.register_shot_result(row, col, hit, destroyed, ship)

        # Feedback
        if hit:
            if destroyed:
                self.message = f"Computer trifft und versenkt dein {ship.name}!"
            else:
                self.message = f"Computer trifft bei ({row}, {col})!"
        else:
            self.message = f"Computer verfehlt bei ({row}, {col})!"

        # Prüfe Gewinnbedingung
        if self.player_board.all_ships_destroyed():
            self.game_over = True
            self.winner = "Computer"
            self._end_game()
        else:
            # Spieler ist wieder dran
            if not hit:  # Nur wenn Fehlschuss
                self.player_turn = True
                self.message += " - Dein Zug!"

    def _end_game(self):
        """Beendet das Spiel"""
        self.game_manager.winner = self.winner
        self.game_manager.change_state(STATE_GAME_OVER)

    def draw(self, screen):
        """
        Zeichnet die Kampfphase

        Args:
            screen: pgzero Screen-Objekt
        """
        screen.clear()
        screen.fill(COLOR_BLACK)

        # Titel
        screen.draw.text("Schlacht", center=(WINDOW_WIDTH // 2, 30),
                        fontsize=40, color=COLOR_WHITE)

        # Status-Nachricht
        msg_color = COLOR_GREEN if self.player_turn else COLOR_RED
        screen.draw.text(self.message, center=(WINDOW_WIDTH // 2, 70),
                        fontsize=22, color=msg_color)

        # Board-Labels
        screen.draw.text("Deine Flotte", (PLAYER_GRID_X, GRID_OFFSET_Y - 30),
                        fontsize=24, color=COLOR_WHITE)
        screen.draw.text("Gegner-Flotte", (COMPUTER_GRID_X, GRID_OFFSET_Y - 30),
                        fontsize=24, color=COLOR_WHITE)

        # Zeichne Boards
        self._draw_board(screen, self.player_board, show_ships=True)
        self._draw_board(screen, self.computer_board, show_ships=False)

        # Statistiken
        self._draw_statistics(screen)

    def _draw_board(self, screen, board, show_ships=True):
        """
        Zeichnet ein Spielfeld

        Args:
            screen: pgzero Screen
            board: Board-Objekt
            show_ships: Ob Schiffe angezeigt werden sollen
        """
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = board.x_offset + col * CELL_SIZE
                y = board.y_offset + row * CELL_SIZE

                cell = board.get_cell(row, col)

                # Hintergrund
                screen.blit('water', (x, y))

                # Schiff (nur wenn show_ships=True und nicht getroffen)
                if show_ships and cell.has_ship() and not cell.is_shot():
                    orientation = cell.ship.orientation
                    ship_sprite = 'ship_h' if orientation == 0 else 'ship_v'
                    screen.blit(ship_sprite, (x, y))

                # Treffer/Fehlschuss
                if cell.status == CELL_HIT:
                    screen.blit('hit', (x, y))
                elif cell.status == CELL_MISS:
                    screen.blit('miss', (x, y))
                elif cell.status == CELL_DESTROYED:
                    screen.blit('destroyed', (x, y))

                # Grid-Linien
                rect = Rect(x, y, CELL_SIZE, CELL_SIZE)
                screen.draw.rect(rect, COLOR_GRAY)

        # Koordinaten-Labels
        for i in range(GRID_SIZE):
            # Zahlen (Zeilen)
            x = board.x_offset - 25
            y = board.y_offset + i * CELL_SIZE + CELL_SIZE // 2
            screen.draw.text(str(i), (x, y), fontsize=18, color=COLOR_WHITE)

            # Buchstaben (Spalten)
            x = board.x_offset + i * CELL_SIZE + CELL_SIZE // 2
            y = board.y_offset - 20
            screen.draw.text(chr(65 + i), center=(x, y), fontsize=18, color=COLOR_WHITE)

    def _draw_statistics(self, screen):
        """Zeichnet Statistiken"""
        x = 50
        y = GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 40

        # Spieler-Statistik
        player_ships_alive = sum(1 for ship in self.player_board.ships if not ship.is_destroyed())
        player_ships_total = len(self.player_board.ships)

        screen.draw.text(f"Deine Schiffe: {player_ships_alive}/{player_ships_total}",
                        (x, y), fontsize=20, color=COLOR_GREEN)

        # Computer-Statistik
        computer_ships_alive = sum(1 for ship in self.computer_board.ships if not ship.is_destroyed())
        computer_ships_total = len(self.computer_board.ships)

        screen.draw.text(f"Gegner-Schiffe: {computer_ships_alive}/{computer_ships_total}",
                        (COMPUTER_GRID_X, y), fontsize=20, color=COLOR_RED)
