# main.spec
from PyInstaller.utils.hooks import collect_all

datas = [('images', 'images')]
binaries = []
hiddenimports = []

# Alle Abhängigkeiten automatisch einsammeln
for pkg in ['pgzero', 'pygame', 'PIL', 'pydantic', 'websocket', 'requests']:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ['main.py'],
    pathex=['.'],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports + [
        # game (root)
        'game',
        'game.config',
        'game.game_manager',
        'game.graphics',
        'game.theme',

        # game.ai
        'game.ai',
        'game.ai.base_ai',
        'game.ai.easy_ai',
        'game.ai.hard_ai',
        'game.ai.normal_ai',

        # game.entities
        'game.entities',
        'game.entities.board',
        'game.entities.cell',
        'game.entities.ship',

        # game.multiplayer
        'game.multiplayer',
        'game.multiplayer.communication',
        'game.multiplayer.models',
        'game.multiplayer.multiplayer_config',
        'game.multiplayer.schemas',
        'game.multiplayer.ws',

        # game.states
        'game.states',
        'game.states.base_state',
        'game.states.battle',
        'game.states.create_game',
        'game.states.game_over',
        'game.states.join_game',
        'game.states.menu',
        'game.states.multiplayer',
        'game.states.multiplayer_battle',
        'game.states.multiplayer_lobby',
        'game.states.multiplayer_placement',
        'game.states.placement',
        'game.states.shared_battle',
        'game.states.shared_placement',

        # game.ui
        'game.ui',
        'game.ui.buttons',
    ],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EInf-Lighthouse-game',
    windowed=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='EInf-Lighthouse-game',
)
