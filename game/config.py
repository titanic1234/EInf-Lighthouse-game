"""
Spielkonfiguration für Schiffe-Versenken
Enthält alle Konstanten, Farben und Spielregeln
"""

# Fenstergröße
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
TITLE = "Schiffe Versenken"

# Spielfeld
GRID_SIZE = 10
CELL_SIZE = 40
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 100

# Zwei Spielfelder nebeneinander (Spieler links, Computer rechts)
PLAYER_GRID_X = GRID_OFFSET_X
COMPUTER_GRID_X = WINDOW_WIDTH // 2 + 20

# Farben
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_BLUE = (65, 105, 225)
COLOR_RED = (220, 20, 60)
COLOR_GREEN = (34, 139, 34)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (64, 64, 64)
COLOR_LIGHT_GRAY = (192, 192, 192)
COLOR_YELLOW = (255, 215, 0)

# Button-Einstellungen
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_COLOR = COLOR_BLUE
BUTTON_HOVER_COLOR = (100, 140, 255)
BUTTON_TEXT_COLOR = COLOR_WHITE

# Schiffstypen: (Name, Länge, Anzahl)
SHIP_TYPES = [
    ("Schlachtschiff", 5, 1),
    ("Kreuzer", 4, 1),
    ("Zerstörer", 3, 2),
    ("U-Boot", 2, 1),
]

# Spielzustände
STATE_MENU = "menu"
STATE_PLACEMENT = "placement"
STATE_BATTLE = "battle"
STATE_GAME_OVER = "game_over"

# Zell-Status
CELL_EMPTY = 0
CELL_SHIP = 1
CELL_HIT = 2
CELL_MISS = 3
CELL_DESTROYED = 4

# Schiffs-Orientierung
ORIENTATION_HORIZONTAL = 0
ORIENTATION_VERTICAL = 1

# Text-Einstellungen
FONT_SIZE_TITLE = 48
FONT_SIZE_LARGE = 32
FONT_SIZE_MEDIUM = 24
FONT_SIZE_SMALL = 18
