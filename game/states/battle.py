"""
Kampf-State
Spieler vs Computer
"""

import os
import random
import pygame
from pygame import Rect
import game.config as config
from game.entities.board import Board
from game.ai import create_ai
from game.graphics import draw_gradient_background, draw_rounded_rect, ParticleSystem, draw_text, draw_grid_cell
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

        self.ai = create_ai(game_manager.ai_difficulty)

        self.player_turn = True
        self.game_over = False
        self.winner = None

        self.message = "AWAITING ORDERS - SELECT TARGET"

        self.computer_delay = 0
        self.computer_delay_time = config.BATTLE_COMPUTER_DELAY_TIME

        self.game_over_delay = config.BATTLE_GAME_OVER_DELAY
        self.game_over_timer = None

        # Effekte
        self.particles = ParticleSystem()

        # Special Schüsse
        self.abilities = {
            "airstrike": {"charges": 1, "targeted": True},
            "guided": {"charges": 1, "targeted": False},
            "sonar": {"charges": 1, "targeted": True},
            "napalm": {"charges": 1, "targeted": True},
        }
        self.selected_ability = None
        self.active_fires = []

        self.ability_buttons = []
        self._load_ability_icons()
        self._rebuild_ability_buttons()

    def _load_icon(self, filename):
        path = os.path.join("images", filename)
        if not os.path.exists(path):
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

    def _load_ability_icons(self):
        is_modern = theme_manager.current.name == "MODERN"
        self.ability_icons = {
            "airstrike": self._load_icon("airstrike.png" if is_modern else "breitseite.png"),
            "guided": self._load_icon("lenkrakete.png" if is_modern else "enterhaken.png"),
            "sonar": self._load_icon("sonar.png" if is_modern else "Kraehennest.png"),
            "napalm": self._load_icon("napalm.png" if is_modern else "griechisches_feuer.png"),
        }

    def _rebuild_ability_buttons(self):
        size = 64
        spacing = 20
        total_width = size * 4 + spacing * 3
        start_x = config.WINDOW_WIDTH // 2 - total_width // 2
        y = config.WINDOW_HEIGHT - 90

        names = ["airstrike", "guided", "sonar", "napalm"]
        self.ability_buttons = []
        for idx, name in enumerate(names):
            rect = pygame.Rect(start_x + idx * (size + spacing), y, size, size)
            self.ability_buttons.append((name, rect))

    def _ability_display_name(self, ability_key):
        is_modern = theme_manager.current.name == "MODERN"
        names = {
            "airstrike": "LUFTSCHLAG" if is_modern else "BREITSEITE",
            "guided": "LENKRAKETE" if is_modern else "ENTERHAKEN",
            "sonar": "SONAR" if is_modern else "KRÄHENNEST",
            "napalm": "NAPALM" if is_modern else "GRIECHISCHES FEUER",
        }
        return names.get(ability_key, "SPEZIALFÄHIGKEIT")

    def _activate_ability(self, name):
        if not self.player_turn or self.abilities[name]["charges"] <= 0:
            return

        if name == "guided":
            self._use_guided_missile()
            return

        self.selected_ability = name
        label = {
            "airstrike": f"{self._ability_display_name('airstrike')} AKTIV (+)",
            "sonar": f"{self._ability_display_name('sonar')} AKTIV (3x3)",
            "napalm": f"{self._ability_display_name('napalm')} AKTIV",
        }
        self.message = label.get(name, "SPEZIALFÄHIGKEIT AKTIV")

    def update(self, dt, mouse_pos):
        """Aktualisiert die Kampfphase"""
        self.particles.update(dt)

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

    def on_mouse_down(self, pos, button):
        """Behandelt Mausklicks"""
        if button != 1 or not self.player_turn or self.game_over:
            return

        for name, rect in self.ability_buttons:
            if rect.collidepoint(pos):
                self._activate_ability(name)
                return

        cell_pos = self.computer_board.get_cell_at_pos(pos[0], pos[1])
        if not cell_pos:
            return

        row, col = cell_pos
        if self.selected_ability == "airstrike":
            self._player_airstrike(row, col)
        elif self.selected_ability == "sonar":
            self._player_sonar(row, col)
        elif self.selected_ability == "napalm":
            self._player_napalm(row, col)
        else:
            self._player_shoot(row, col)

    def _spawn_effects(self, board, row, col, hit):
        """Spawnt Partikel an der getroffenen Zelle"""
        x = board.x_offset + col * config.CELL_SIZE + config.CELL_SIZE // 2
        y = board.y_offset + row * config.CELL_SIZE + config.CELL_SIZE // 2
        if hit:
            self.particles.add_explosion(x, y, count=40, color=(255, 60, 20))
        else:
            self.particles.add_splash(x, y, count=25)

    def _shoot_with_napalm_rules(self, row, col):
        """U-Boot ist immun, deshalb anderer Marker statt miss"""
        cell = self.computer_board.get_cell(row, col)
        if not cell or cell.is_shot():
            return False, False

        self.game_manager.shots_fired += 1
        cell.scan_marked = False
        cell.scan_found_ship = False

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

    def _draw_ability_buttons(self, screen):
        for name, rect in self.ability_buttons:
            charges = self.abilities[name]["charges"]
            active = self.selected_ability == name
            enabled = charges > 0 and self.player_turn and not self.game_over

            base = (45, 75, 120) if enabled else (45, 45, 45)
            hover = (85, 130, 200) if enabled else (70, 70, 70)
            color = hover if rect.collidepoint(pygame.mouse.get_pos()) else base
            border = (255, 215, 0) if active else (160, 210, 255)

            draw_rounded_rect(screen, (0, 0, 0), rect.move(0, 4), radius=8, alpha=120)
            draw_rounded_rect(screen, color, rect, radius=8, alpha=230)
            draw_rounded_rect(screen, border, rect, radius=8, width=2, alpha=255)

            icon = self.ability_icons.get(name)
            if icon:
                icon_surf = pygame.transform.smoothscale(icon, (42, 42))
                icon_rect = icon_surf.get_rect(center=rect.center)
                screen.blit(icon_surf, icon_rect)

            draw_text(screen, str(charges), rect.right - 12, rect.top + 6, 24, (255, 255, 255), center=True)

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

        # Draw particles
        self._draw_ability_buttons(screen)
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
        self._rebuild_ability_buttons()
        self._load_ability_icons()