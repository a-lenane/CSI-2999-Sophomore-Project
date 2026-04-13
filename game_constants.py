import os

WIDTH, HEIGHT = 960, 720
TILE_SIZE = 64
WORLD_COLS = 15
WORLD_ROWS = 11
PLAYER_SIZE = 34
PLAYER_SPRITE_BOX = (58, 84)
NPC_SPRITE_BOX = (60, 88)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(SCRIPT_DIR, "Assets")
CARD_UI_DIR = os.path.join(ASSET_DIR, "ui")
SAVE_PATH = os.path.join(SCRIPT_DIR, "save_data.json")

SCENE_MENU = 0
SCENE_INTRO = 1
SCENE_WORLD = 2
SCENE_POKER = 3
SCENE_GAME_OVER = 4
