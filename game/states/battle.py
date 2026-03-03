"""
Kampf-State
Spieler vs Computer
"""

import random
from pgzero.rect import Rect
import game.config as config
from game.entities.board import Board
from game.ai import create_ai
from game.graphics import draw_rounded_rect, draw_text
from game.theme import theme_manager
from game.states.shared_battle import SharedBattleState


class BattleState(SharedBattleState):
    """Kampf-Phase: Spieler gegen Computer"""

    def __init__(self, game_manager):
        """Initialisiert die Kampfphase"""
        super().__init__(game_manager)

        self.computer_board = Board(config.COMPUTER_GRID_X, config.GRID_OFFSET_Y, "Computer")
        self.ai = create_ai(game_manager.ai_difficulty)
        self.ai.place_ships(self.computer_board)

        self.player_turn = True
        self.game_over = False
        self.winner = None

        self.message = "AWAITING ORDERS - SELECT TARGET"

        self.computer_delay = 0
        self.computer_delay_time = config.BATTLE_COMPUTER_DELAY_TIME

        self.game_over_delay = config.BATTLE_GAME_OVER_DELAY
        self.game_over_timer = None

        self.active_fires = []

    def _update_pipeline(self, dt, mouse_pos):
        if self.game_over_timer is not None:
            self.game_over_timer -= dt
            if self.game_over_timer <= 0:
                self.game_manager.change_state(config.STATE_GAME_OVER)

        if self.game_over:
            return

        # Computer-Zug mit Verzoegerung
        if not self.player_turn:
            self.computer_delay += dt
            if self.computer_delay >= self.computer_delay_time:
                self._computer_turn()
                self.computer_delay = 0


    def _shoot_with_napalm_rules(self, row, col):
        """U-Boot ist immun, deshalb anderer Marker statt miss"""
        cell = self.computer_board.get_cell(row, col)
        if not cell or cell.is_shot():
            return False, False

        self.game_manager.shots_fired += 1
        cell.scan_marked = False
        cell.scan_found_ship = False
        cell.player_marker = False

        if not cell.has_ship():
            cell.napalm_marked = True
            self._spawn_effects(self.computer_board, row, col, False)
            return False, False

        if cell.ship and cell.ship.name.split(" #", 1)[0] in ("U-Boot", "Schaluppe"):
            cell.napalm_marked = True
            self._spawn_effects(self.computer_board, row, col, False)
            return False, False

        hit, destroyed, _ = self.computer_board.shoot(row, col)
        self._spawn_effects(self.computer_board, row, col, hit)
        if hit:
            self.game_manager.shots_hit += 1
        return hit, destroyed

    def _player_airstrike(self, center_row, center_col):
        """Fuehrt einen Airstrike (+ muster) aus."""
        self.abilities["airstrike"]["charges"] = 0
        self.selected_ability = None

        hit_any = False
        destroyed_any = False

        # Airstrike visual effect at center
        coords = [
            (center_row, center_col),
            (center_row - 1, center_col),
            (center_row + 1, center_col),
            (center_row, center_col - 1),
            (center_row, center_col + 1),
        ]

        cx = self.computer_board.x_offset + center_col * config.CELL_SIZE + config.CELL_SIZE // 2
        cy = self.computer_board.y_offset + center_row * config.CELL_SIZE + config.CELL_SIZE // 2
        self.particles.add_explosion(cx, cy, count=100, color=(255, 200, 50))

        for r, c in coords:
            cell = self.computer_board.get_cell(r, c)
            if cell and not cell.is_shot():
                self.game_manager.shots_fired += 1
                hit, destroyed, _ = self.computer_board.shoot(r, c)
                self._spawn_effects(self.computer_board, r, c, hit)
                if hit:
                    self.game_manager.shots_hit += 1
                    hit_any = True
                if destroyed:
                    destroyed_any = True

        if destroyed_any:
            self.message = theme_manager.current.text_airstrike_critical
        elif hit_any:
            self.message = theme_manager.current.text_airstrike_success
        else:
            self.message = theme_manager.current.text_airstrike_miss

        self._check_game_over_after_player_action(hit_any)

    def _use_guided_missile(self):
        candidates = []
        for row in range(config.GRID_SIZE):
            for col in range(config.GRID_SIZE):
                cell = self.computer_board.get_cell(row, col)
                if cell and cell.has_ship() and not cell.is_shot():
                    candidates.append((row, col))

        if not candidates: # sollte nicht passieren
            self.message = f"KEIN GÜLTIGES ZIEL FÜR {self._ability_display_name('guided')}"
            return

        row, col = random.choice(candidates)
        self.abilities["guided"]["charges"] = 0

        self.game_manager.shots_fired += 1
        hit, destroyed, _ = self.computer_board.shoot(row, col)
        self._spawn_effects(self.computer_board, row, col, hit)
        if hit:
            self.game_manager.shots_hit += 1

        if destroyed:
            self.message = f"{self._ability_display_name('guided')}: ZIEL VERSENKT!"
        else:
            self.message = f"{self._ability_display_name('guided')} HAT BEI ({row + 1}, {col + 1}) GETROFFEN!"

        self._check_game_over_after_player_action(hit)

    def _player_sonar(self, center_row, center_col):
        self.abilities["sonar"]["charges"] = 0
        self.selected_ability = None

        found_positions = []

        for r in range(center_row - 1, center_row + 2):
            for c in range(center_col - 1, center_col + 2):
                cell = self.computer_board.get_cell(r, c)
                if not cell or cell.is_shot():
                    continue
                cell.scan_marked = True
                cell.scan_found_ship = cell.has_ship()
                cell.player_marker = False
                if cell.has_ship():
                    found_positions.append((r + 1, c + 1))

        if found_positions:
            coords_text = ", ".join(f"({r},{c})" for r, c in found_positions)
            self.message = f"{self._ability_display_name('sonar')} KONTAKTE: {coords_text}"
        else:
            self.message = f"{self._ability_display_name('sonar')}: KEINE SCHIFFE GESICHTET"

        self._check_game_over_after_player_action(False, force_end_turn=True, preserve_message=True)

    def _player_napalm(self, row, col):
        self.abilities["napalm"]["charges"] = 0
        self.selected_ability = None

        hit, _ = self._shoot_with_napalm_rules(row, col)
        fire = {
            "turns_left": 3,
            "burning_cells": {(row, col)},
            "expanded_to": {(row, col)},
        }
        self.active_fires.append(fire)

        if hit:
            self.message = f"{self._ability_display_name('napalm')} ENTZÜNDET - TREFFER!"
        else:
            self.message = f"{self._ability_display_name('napalm')} ENTZÜNDET"

        self._check_game_over_after_player_action(hit, force_end_turn=True, preserve_message=True)

    def _progress_fires(self):
        if not self.active_fires:
            return False

        hit_any = False
        for fire in self.active_fires:
            if fire["turns_left"] <= 0:
                continue

            candidates = set()
            for row, col in fire["burning_cells"]:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = row + dr, col + dc
                    if (nr, nc) in fire["expanded_to"]:
                        continue
                    if self.computer_board.get_cell(nr, nc):
                        candidates.add((nr, nc))

            spread_targets = random.sample(list(candidates), min(3, len(candidates))) if candidates else []
            new_burning = set()
            for tr, tc in spread_targets:
                fire["expanded_to"].add((tr, tc))
                new_burning.add((tr, tc))
                hit, _ = self._shoot_with_napalm_rules(tr, tc)
                if hit:
                    hit_any = True

            fire["burning_cells"].update(new_burning)
            fire["turns_left"] -= 1

        self.active_fires = [f for f in self.active_fires if f["turns_left"] > 0]
        return hit_any

    def _player_shoot(self, row, col):
        """Spieler schiesst"""
        theme = theme_manager.current
        cell = self.computer_board.get_cell(row, col)

        if cell.is_shot():
            self.message = theme.text_already_compromised
            return

        self.game_manager.shots_fired += 1
        hit, destroyed, _ = self.computer_board.shoot(row, col)

        self._spawn_effects(self.computer_board, row, col, hit)

        if hit:
            self.game_manager.shots_hit += 1
            self.message = theme.text_target_destroyed if destroyed else theme.text_target_hit
        else:
            self.message = theme.text_target_miss

        self._check_game_over_after_player_action(hit)

    def _check_game_over_after_player_action(self, hit, force_end_turn=False, preserve_message=False):
        fire_hit = self._progress_fires()
        any_hit = hit or fire_hit

        if self.computer_board.all_ships_destroyed():
            self.game_over = True
            self.winner = "Player"
            self._end_game()
            return

        if force_end_turn or not any_hit:
            self.player_turn = False
            if preserve_message:
                self.message = f"{self.message} - {theme_manager.current.text_computer_turn}"
            else:
                self.message = theme_manager.current.text_computer_turn

    def _computer_turn(self):
        """Computer macht seinen Zug"""
        action = self.ai.choose_action(self.player_board)
        action_type = action.get("type", "shoot")

        if action_type == "sonar":
            row, col = action["row"], action["col"]
            found = self._computer_sonar(row, col)
            if found:
                self.message = f"ENEMY SONAR DETECTED CONTACTS AT {len(found)} POSITIONS."
            else:
                self.message = "ENEMY SONAR: NO CONTACTS."
            self.player_turn = True
            self.message += " - YOUR TURN!"
            return

        if action_type == "airstrike":
            hit = self._computer_airstrike(action["row"], action["col"])
            self.message = "ENEMY AIRSTRIKE HIT!" if hit else "ENEMY AIRSTRIKE MISSED."
            if not hit:
                self.player_turn = True
                self.message += " - YOUR TURN!"
        elif action_type == "guided":
            row, col, hit, destroyed, ship = self._computer_guided_missile()
            self.message = self._computer_shot_message(row, col, hit, destroyed, ship, prefix="GUIDED")
            if not hit:
                self.player_turn = True
                self.message += " - YOUR TURN!"
        elif action_type == "napalm":
            row, col = action["row"], action["col"]
            hit, destroyed, ship = self._computer_napalm(row, col)
            self.message = self._computer_shot_message(row, col, hit, destroyed, ship, prefix="NAPALM")
            if not hit:
                self.player_turn = True
                self.message += " - YOUR TURN!"
        else:
            row, col = action["row"], action["col"]
            hit, destroyed, ship = self.player_board.shoot(row, col)
            self.ai.register_shot_result(row, col, hit, destroyed, ship)
            self._spawn_effects(self.player_board, row, col, hit)
            self.message = self._computer_shot_message(row, col, hit, destroyed, ship)
            if not hit:
                self.player_turn = True
                self.message += " - YOUR TURN!"

        if self.player_board.all_ships_destroyed():
            self.game_over = True
            self.winner = "Computer"
            self._end_game()

    def _computer_shot_message(self, row, col, hit, destroyed, ship, prefix=None):
        marker = f"{prefix} " if prefix else ""
        if hit:
            if destroyed and ship:
                ship_name = theme_manager.get_ship_display_name(ship.name)
                return f"ALERT: {marker}ALLY {ship_name.upper()} SUNK!"
            return f"WARNING: {marker}HULL BREACH AT ({row + 1}, {col + 1})!"
        return f"ENEMY {marker}MISSED AT ({row + 1}, {col + 1})."

    def _computer_sonar(self, center_row, center_col):
        found_positions = []
        miss_positions = []
        for r in range(center_row - 1, center_row + 2):
            for c in range(center_col - 1, center_col + 2):
                cell = self.player_board.get_cell(r, c)
                if not cell or cell.is_shot():
                    continue
                cell.scan_marked = True
                cell.scan_found_ship = cell.has_ship()
                if cell.has_ship():
                    found_positions.append((r, c))
                else:
                    miss_positions.append((r, c))

        self.ai.register_sonar_findings(found_positions)
        self.ai.register_sonar_misses(miss_positions)
        return found_positions

    def _computer_airstrike(self, center_row, center_col):
        hit_any = False
        coords = [
            (center_row, center_col),
            (center_row - 1, center_col),
            (center_row + 1, center_col),
            (center_row, center_col - 1),
            (center_row, center_col + 1),
        ]
        for row, col in coords:
            cell = self.player_board.get_cell(row, col)
            if not cell or cell.is_shot():
                continue
            hit, destroyed, ship = self.player_board.shoot(row, col)
            self.ai.register_shot_result(row, col, hit, destroyed, ship)
            self._spawn_effects(self.player_board, row, col, hit)
            hit_any = hit_any or hit
        return hit_any

    def _computer_guided_missile(self):
        candidates = []
        for row in range(config.GRID_SIZE):
            for col in range(config.GRID_SIZE):
                cell = self.player_board.get_cell(row, col)
                if cell and cell.has_ship() and not cell.is_shot() and not cell.napalm_marked:
                    candidates.append((row, col))

        if candidates:
            row, col = random.choice(candidates)
        else:
            row, col = self.ai.get_next_shot(self.player_board)

        hit, destroyed, ship = self.player_board.shoot(row, col)
        self.ai.register_shot_result(row, col, hit, destroyed, ship)
        self._spawn_effects(self.player_board, row, col, hit)
        return row, col, hit, destroyed, ship

    def _computer_napalm(self, row, col):
        cell = self.player_board.get_cell(row, col)
        if not cell or cell.is_shot():
            row, col = self.ai.get_next_shot(self.player_board)
            cell = self.player_board.get_cell(row, col)

        if not cell.has_ship():
            cell.napalm_marked = True
            self.ai.tried_positions.add((row, col))
            self._spawn_effects(self.player_board, row, col, False)
            return False, False, None

        hit, destroyed, ship = self.player_board.shoot(row, col)
        self.ai.register_shot_result(row, col, hit, destroyed, ship)
        self._spawn_effects(self.player_board, row, col, hit)
        return hit, destroyed, ship

    def _end_game(self):
        """Beendet das Spiel"""
        self.game_manager.winner = self.winner
        self.game_over_timer = self.game_over_delay

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