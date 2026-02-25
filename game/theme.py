from game.entities import ship


class Theme:
    def __init__(self, name):
        self.name = name

        # Colors
        self.color_bg_top = (0, 0, 0)
        self.color_bg_bottom = (0, 0, 0)
        self.color_water = (0, 0, 0)
        self.color_ship = (0, 0, 0)
        self.color_ship_border = (0, 0, 0)
        self.color_hit = (0, 0, 0)
        self.color_miss = (0, 0, 0)
        self.color_destroyed = (0, 0, 0)
        self.color_grid_player = (0, 0, 0)
        self.color_grid_enemy = (0, 0, 0)
        self.color_text_primary = (0, 0, 0)
        self.color_text_secondary = (0, 0, 0)
        self.color_panel_bg = (0, 0, 0)
        self.color_particle_explosion = (0, 0, 0)
        self.color_particle_splash = (0, 0, 0)

        # Strings
        self.text_title = ""
        self.text_subtitle = ""
        self.text_start_btn = ""
        self.text_quit_btn = ""
        self.text_placement_title = ""
        self.text_placement_instruction = ""
        self.text_battle_player_radar = ""
        self.text_battle_enemy_radar = ""
        self.text_airstrike_btn = ""
        self.text_airstrike_active = ""
        self.text_airstrike_critical = ""
        self.text_airstrike_success = ""
        self.text_airstrike_miss = ""
        self.text_target_hit = ""
        self.text_target_miss = ""
        self.text_target_destroyed = ""
        self.text_already_compromised = ""
        self.text_computer_turn = ""
        self.ship_name_overrides = {}


class ModernTheme(Theme):
    def __init__(self):
        super().__init__("MODERN")
        self.color_bg_top = (15, 20, 35)
        self.color_bg_bottom = (5, 10, 20)
        self.color_water = (20, 40, 80)
        self.color_ship = (100, 200, 255)
        self.color_ship_border = (200, 230, 255)
        self.color_hit = (255, 50, 50)
        self.color_miss = (150, 200, 255)
        self.color_destroyed = (150, 0, 0)
        self.color_grid_player = (40, 60, 100)
        self.color_grid_enemy = (100, 40, 40)
        self.color_text_primary = (255, 255, 255)
        self.color_text_secondary = (150, 200, 255)
        self.color_text_enemy = (255, 150, 150)
        self.color_panel_bg = (10, 20, 40)
        self.color_particle_explosion = (255, 200, 50)
        self.color_particle_splash = (150, 200, 255)

        self.text_title = "SCHIFFE VERSENKEN"
        self.text_subtitle = "TACTICAL NAVAL COMBAT"
        self.text_start_btn = "START BATTLE"
        self.text_quit_btn = "ABORT"
        self.text_placement_title = "COMMANDER, DEPLOY YOUR FLEET"
        self.text_placement_instruction = "PRESS R TO ROTATE | LEFT CLICK TO DEPLOY"
        self.text_battle_player_radar = "ALLIED FLEET RADAR"
        self.text_battle_enemy_radar = "ENEMY FLEET RADAR"
        self.text_airstrike_btn = "AIRSTRIKE"
        self.text_airstrike_active = "AIRSTRIKE TARGETING ACTIVE (3x3)"
        self.text_airstrike_critical = "AIRSTRIKE CRITICAL! ENEMY SUNK!"
        self.text_airstrike_success = "AIRSTRIKE SUCCESSFUL! TARGET HIT!"
        self.text_airstrike_miss = "AIRSTRIKE MISSED."
        self.text_target_hit = "TARGET HIT!"
        self.text_target_miss = "MISSED TARGET."
        self.text_target_destroyed = "CRITICAL HIT! ENEMY DESTROYED!"
        self.text_already_compromised = "SECTOR ALREADY COMPROMISED!"
        self.text_computer_turn = "ENEMY IS CALCULATING TRACTORY..."
        self.text_game_over_win = "ALLE GEGNERISCHEN SCHIFFE ZERSTÖRT!"
        self.text_game_over_lose = "ALLE EIGENEN SCHIFFE SIND GESUNKEN!"


class PirateTheme(Theme):
    def __init__(self):
        super().__init__("PIRATE")
        self.color_bg_top = (80, 120, 140)
        self.color_bg_bottom = (30, 60, 80)
        self.color_water = (50, 100, 130)
        self.color_ship = (139, 69, 19)  # SaddleBrown
        self.color_ship_border = (160, 82, 45)  # Sienna
        self.color_hit = (255, 140, 0)  # DarkOrange
        self.color_miss = (200, 220, 240)  # Light splash
        self.color_destroyed = (100, 0, 0)  # Dark ruby red
        self.color_grid_player = (180, 160, 120)  # Parchment/Rope color
        self.color_grid_enemy = (140, 80, 80)
        self.color_text_primary = (255, 235, 180)  # Goldish white
        self.color_text_secondary = (220, 190, 130)  # Sandy
        self.color_text_enemy = (255, 100, 100)
        self.color_panel_bg = (60, 40, 20)  # Dark wood
        self.color_particle_explosion = (255, 160, 0)
        self.color_particle_splash = (220, 240, 255)

        self.text_title = "PIRATEN SCHLACHT"
        self.text_subtitle = "KAMPF UM DIE SIEBEN WELTMEERE"
        self.text_start_btn = "SEGEL SETZEN"
        self.text_quit_btn = "KAPITULIEREN"
        self.text_placement_title = "KAPITÄN, POSITIONIERT DIE FLOTTE"
        self.text_placement_instruction = "R DRÜCKEN ZUM DREHEN | LINKSKLICK ZUM ANKERN"
        self.text_battle_player_radar = "UNSERE GEWÄSSER"
        self.text_battle_enemy_radar = "FEINDLICHE STRÖMUNGEN"
        self.text_airstrike_btn = "BREITSEITE"
        self.text_airstrike_active = "KANONIERE BEREIT (3x3 SPERRFEUER)"
        self.text_airstrike_critical = "VOLLE BREITSEITE! SCHIFF VERSENKT!"
        self.text_airstrike_success = "TREFFER DRÜBEN!"
        self.text_airstrike_miss = "NUR WASSER GETROFFEN, IHR LANDRATTEN!"
        self.text_target_hit = "TREFFER BEIM KLABAUTERMANN!"
        self.text_target_miss = "DANEBEN GESCHOSSEN!"
        self.text_target_destroyed = "SCHIFF AUF DEN GRUND GESCHICKT!"
        self.text_already_compromised = "DA LIEGT SCHON HOLZ IM WASSER!"
        self.text_computer_turn = "DIE SPANIER LADEN IHRE KANONEN..."
        self.text_game_over_win = "DIE FEINDLICHE FLOTTE IST GESUNKEN! ARRR!"
        self.text_game_over_lose = "WIR GEHEN UNTER, KÄPT'N!"
        self.ship_name_overrides = {
            "Schlachtschiff": "Flaggschiff",
            "Kreuzer": "Galeone",
            "Zerstoerer": "Fregatte",
            "U-Boot": "Schaluppe",
            "Flugzeugträger": "Mörser Brigg",
        }


class ThemeManager:
    def __init__(self):
        self.modern = ModernTheme()
        self.pirate = PirateTheme()
        self.current = self.modern

    def toggle(self):
        if self.current.name == "MODERN":
            self.current = self.pirate
        else:
            self.current = self.modern

    def get_ship_display_name(self, ship_name):
        """Liefert Schiffnamen für aktives Theme"""
        suffix = ""
        base_name = ship_name

        if "#" in ship_name:
            base_name, suffix = ship_name.split(" #", 1)
            suffix = f" #{suffix}"

        display_name = self.current.ship_name_overrides.get(base_name, base_name)
        return f"{display_name}{suffix}"


# Globale Instanz
theme_manager = ThemeManager()