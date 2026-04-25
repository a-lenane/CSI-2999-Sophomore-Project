import pygame
import sys
import random
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PokerLogic import *  
from sprite_loader import SpriteLoader
from DialogueCasino import BOSS_DIALOGUE, STORY_PAGES, GAME_OVER_TEXT, ENDING_TEXT
from Buffs import Player as PersistentPlayer

"""
TODO:
- hide dealer cards (diff card backs for diff dealers?)
- menu to adjust bet amount (mayb  buttons like, bet 1x, bet 2x, bet 5x)
- player money tracking
- using ChipsAndCode to assess hands, can mayb show optimal hand to player during play
- determine a winner (+ payout)
- where get buffs (store?)
- hide player cards untill click "deal" button
- dynamic adjustments for each turn, such as "deal" being only option, then only "check" or "bet", then "check", "bet" or fold, with game finish handling
- buff menu / info 
- dealer sprites when open table
- change back to full dynamic card positions vs using fixed pixel offset
"""

pygame.init()

PROJECT_ROOT = Path(__file__).resolve().parent
ASSET_SEARCH_ROOTS = [
    PROJECT_ROOT / "Assets",
    PROJECT_ROOT / "assets",
    PROJECT_ROOT,
]
IMAGE_CACHE = {}
WORLD_TILE_SIZE = 64
sprite_loader = SpriteLoader(tile_size=WORLD_TILE_SIZE)
world_object_surfaces = sprite_loader.load_tilesheet_objects()


def scale_surface_to_rect(surface, rect, pixel_art=True):
    target_size = (max(1, int(rect.width)), max(1, int(rect.height)))
    scaler = pygame.transform.scale if pixel_art else pygame.transform.smoothscale
    return scaler(surface, target_size)


def get_world_scale(scale_x=None, scale_y=None):
    scale_x = current_scale_x if scale_x is None else scale_x
    scale_y = current_scale_y if scale_y is None else scale_y
    return max(0.55, min(scale_x, scale_y))


def get_world_floor_tile(room_idx, tile_size):
    floor_name = {
        0: "wood_floor_warm",
        1: "office_floor",
        2: "vault_floor",
    }.get(room_idx, "wood_floor_dark")
    return scale_surface_to_rect(
        sprite_loader.get_tile(floor_name),
        pygame.Rect(0, 0, tile_size[0], tile_size[1]),
    )


def get_world_prop_surface(name, rect):
    if name in SpriteLoader.TILE_FILES:
        surface = sprite_loader.get_tile(name)
    else:
        surface = world_object_surfaces[name]
    return scale_surface_to_rect(surface, rect)


def scale_surface_contained(surface, bounds):
    source_w, source_h = surface.get_size()
    if source_w <= 0 or source_h <= 0:
        return surface
    scale = min(bounds.width / source_w, bounds.height / source_h)
    target_size = (
        max(1, int(source_w * scale)),
        max(1, int(source_h * scale)),
    )
    return pygame.transform.scale(surface, target_size)


def draw_world_prop(surface, name, bounds):
    if name in SpriteLoader.TILE_FILES:
        prop = get_world_prop_surface(name, bounds)
        surface.blit(prop, bounds.topleft)
        return

    prop = scale_surface_contained(world_object_surfaces[name], bounds)
    prop_rect = prop.get_rect(midbottom=(bounds.centerx, bounds.bottom))
    surface.blit(prop, prop_rect.topleft)


def draw_door_hint(surface, door):
    if door.rect.collidepoint(pygame.mouse.get_pos()):
        pygame.draw.rect(surface, GOLD, door.rect, 2)


def draw_shadow(surface, anchor_rect, width_ratio=0.7, height_ratio=0.22, alpha=75):
    shadow_w = max(12, int(anchor_rect.width * width_ratio))
    shadow_h = max(6, int(anchor_rect.height * height_ratio))
    shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, alpha), shadow.get_rect())
    shadow_rect = shadow.get_rect(center=(anchor_rect.centerx, anchor_rect.bottom - shadow_h // 3))
    surface.blit(shadow, shadow_rect)


def draw_table(surface, table_rect):
    rug_rect = table_rect.inflate(int(table_rect.width * 0.18), int(table_rect.height * 0.08))
    rug_rect.centery += int(table_rect.height * 0.14)
    rug = get_world_prop_surface("green_rug", rug_rect).copy()
    rug.set_alpha(38)
    surface.blit(rug, rug_rect.topleft)

    draw_shadow(surface, table_rect, width_ratio=0.82, height_ratio=0.2, alpha=110)

    sprite_bounds = table_rect.inflate(int(table_rect.width * 0.06), int(table_rect.height * 0.18))
    table_surface = scale_surface_contained(world_object_surfaces["poker_table"], sprite_bounds)
    table_surface_rect = table_surface.get_rect(
        midbottom=(table_rect.centerx, table_rect.bottom + max(2, table_rect.height // 18))
    )
    surface.blit(table_surface, table_surface_rect.topleft)


def draw_depth_sorted_world_objects(surface):
    draw_items = []
    for table in tables:
        draw_items.append((table.bottom, lambda target, rect=table: draw_table(target, rect)))
    for npc in npcs:
        draw_items.append((npc.rect.bottom, lambda target, actor=npc: actor.draw(target)))
    for guard in guards:
        draw_items.append((guard.rect.bottom, lambda target, actor=guard: actor.draw(target)))
    draw_items.append((player.rect.bottom, lambda target: player.draw(target)))

    for _, draw_item in sorted(draw_items, key=lambda item: item[0]):
        draw_item(surface)

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
# Default to 16:9 aspect ratio (1280x720)
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Texas Hold'em: High Stakes")

clock = pygame.time.Clock()

# COLORS
TABLE_GREEN = (6, 71, 42)
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
LIGHT_GOLD = (255, 215, 0)
FLOOR = (40, 40, 40)          # kept for compatibility but not used in world
WALL = (20, 20, 20)
PLAYER_COLOR = (200, 50, 50)
NPC_COLOR = (200, 200, 50)
GUARD_COLOR = (50, 120, 220)
CARD_BACK_COLOR = (100, 50, 0)
BOSS_MSG_BG = (0, 0, 0, 180)  # semi-transparent black
MENU_BG = (0, 0, 0, 200)

# Tile floor settings
TILE_COLS = 16
TILE_ROWS = 9
TILE_GAP = 0

# Room colour sets (light, dark) – made darker
ROOM_COLORS = [
    ((40, 90, 40), (10, 40, 10)),     # room 0: dark green
    ((30, 30, 90), (0, 0, 40)),       # room 1: dark blue
    ((120, 40, 40), (60, 0, 0))       # room 2: dark rose/red
]

# Door settings
DOOR_SIZE = 80               # base door gap size (at 1280x720)
DOOR_COLOR = (100, 50, 20)   # darker wood brown
DOOR_HIGHLIGHT = (160, 100, 40)
BASE_WALL_THICK = 40

# Base sizes (at reference resolution 1280x720)
BASE_PLAYER_SIZE = 72
BASE_NPC_SIZE = 72
BASE_GUARD_SIZE = 72
BASE_TABLE_W = 132
BASE_TABLE_H = 88
PLAYER_VISUAL_SCALE = 1.5
NPC_VISUAL_SCALE = 0.88
NPC_VISUAL_WIDTH_SCALE = 1.12
BASE_CARD_W = 35   # based on min(1280,720)/20 = 720/20 = 36, approximate
BASE_CARD_H = 49   # 2.5:3.5 ratio

# FONTS
class PILFontAdapter:
    def __init__(self, size, bold=False):
        self.size = size
        self.bold = bold
        self._font = self._load_font(size, bold)

    @staticmethod
    def _load_font(size, bold):
        candidates = [
            "Arial Black.ttf" if bold else "Arial.ttf",
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        ]
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def render(self, text, antialias, color, background=None):
        if text is None:
            text = ""
        dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        draw = ImageDraw.Draw(dummy)
        bbox = draw.textbbox((0, 0), text, font=self._font)
        width = max(1, bbox[2] - bbox[0])
        height = max(1, bbox[3] - bbox[1])
        bg = (background[0], background[1], background[2], 255) if background else (0, 0, 0, 0)
        image = Image.new("RGBA", (width, height), bg)
        draw = ImageDraw.Draw(image)
        draw.text((-bbox[0], -bbox[1]), text, font=self._font, fill=(color[0], color[1], color[2], 255))
        return pygame.image.fromstring(image.tobytes(), image.size, image.mode)


title_font = PILFontAdapter(80, bold=True)
font = PILFontAdapter(32)
boss_font = PILFontAdapter(28, bold=True)

# --------------------------------------------------
# UI & OBJECT CLASSES
# --------------------------------------------------
class Button:
    def __init__(self, text, x_ratio, y_ratio, w_ratio=0.18, h_ratio=0.07):
        self.text = text
        self.x_ratio = x_ratio
        self.y_ratio = y_ratio
        self.w_ratio = w_ratio
        self.h_ratio = h_ratio
        self.rect = pygame.Rect(0, 0, 0, 0)

    def draw(self, surface):
        btn_w = WIDTH * self.w_ratio
        btn_h = HEIGHT * self.h_ratio
        self.rect.size = (btn_w, btn_h)
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)
        
        dynamic_font = PILFontAdapter(int(btn_h * 0.5))
        color = GOLD if not self.rect.collidepoint(pygame.mouse.get_pos()) else LIGHT_GOLD

        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        text_surf = dynamic_font.render(self.text, True, TABLE_GREEN)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

class WorldPlayer:
    def __init__(self):
        self.rect = pygame.Rect(100, 100, BASE_PLAYER_SIZE, BASE_PLAYER_SIZE)
        self.base_speed = 5
        self.x_ratio = 0.1
        self.y_ratio = 0.1
        self.direction = "down"
        self.moving = False
        self.frame_index = 0.0
        self.sprite_frames = sprite_loader.load_player_frames(tile_size=BASE_PLAYER_SIZE)

    def resize(self, scale_x, scale_y):
        """Update player size without stretching the sprite on non-16:9 windows."""
        scale = get_world_scale(scale_x, scale_y)
        size = int(BASE_PLAYER_SIZE * scale)
        self.rect.size = (size, size)
        self.reposition()

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def move(self, dx, dy, colliders):
        """Move with collision detection and resolution (separate axes)."""
        self.moving = dx != 0 or dy != 0
        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
        elif dy != 0:
            self.direction = "down" if dy > 0 else "up"

        # Move horizontally
        self.rect.x += dx
        for collider in colliders:
            if self.rect.colliderect(collider):
                if dx > 0:
                    self.rect.right = collider.left
                elif dx < 0:
                    self.rect.left = collider.right
        # Move vertically
        self.rect.y += dy
        for collider in colliders:
            if self.rect.colliderect(collider):
                if dy > 0:
                    self.rect.bottom = collider.top
                elif dy < 0:
                    self.rect.top = collider.bottom
        
        # Update ratios
        self.x_ratio = self.rect.centerx / WIDTH
        self.y_ratio = self.rect.centery / HEIGHT

    def update_animation(self, dt_ms, scale_x):
        frame_size = max(24, int(self.rect.width * PLAYER_VISUAL_SCALE))
        if frame_size not in sprite_loader._player_cache:
            self.sprite_frames = sprite_loader.load_player_frames(tile_size=frame_size)
        else:
            self.sprite_frames = sprite_loader._player_cache[frame_size]

        if self.moving:
            frame_count = len(self.sprite_frames[f"walk_{self.direction}"])
            self.frame_index = (self.frame_index + 0.012 * dt_ms) % frame_count
        else:
            self.frame_index = 0.0

    def current_frame(self):
        key = f"walk_{self.direction}" if self.moving else f"idle_{self.direction}"
        frames = self.sprite_frames[key]
        return frames[int(self.frame_index) % len(frames)]

    def draw(self, surface):
        frame = self.current_frame()
        draw_shadow(surface, self.rect, width_ratio=0.5, height_ratio=0.16, alpha=55)
        sprite_rect = frame.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 4))
        surface.blit(frame, sprite_rect)

class NPC:
    def __init__(self, x_ratio, y_ratio, facing="down", use_sprite_sheet=True):
        self.x_ratio, self.y_ratio = x_ratio, y_ratio
        self.rect = pygame.Rect(0, 0, BASE_NPC_SIZE, BASE_NPC_SIZE)
        self.facing = facing
        self.use_sprite_sheet = use_sprite_sheet
        self.sprite_name = "gambler.png"
        self.sprite_frames = sprite_loader.load_player_frames(tile_size=BASE_NPC_SIZE)

    def resize(self, scale_x, scale_y):
        scale = get_world_scale(scale_x, scale_y)
        size = int(BASE_NPC_SIZE * scale)
        self.rect.size = (size, size)
        frame_size = max(20, int(size * NPC_VISUAL_SCALE))
        if frame_size not in sprite_loader._player_cache:
            self.sprite_frames = sprite_loader.load_player_frames(tile_size=frame_size)
        else:
            self.sprite_frames = sprite_loader._player_cache[frame_size]
        self.reposition()

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def update(self, colliders, speed_scale_x, speed_scale_y):
        self.reposition()

    def draw(self, surface):
        if self.use_sprite_sheet:
            sprite = self.sprite_frames[f"idle_{self.facing}"][0]
        else:
            sprite_size = (
                int(self.rect.width * NPC_VISUAL_WIDTH_SCALE),
                int(self.rect.height * NPC_VISUAL_SCALE),
            )
            sprite = load_sprite_sheet_frame(self.sprite_name, sprite_size)
        draw_shadow(surface, self.rect, width_ratio=0.55, height_ratio=0.18, alpha=55)
        surface.blit(sprite, sprite.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 2)))

class Guard:
    def __init__(self, x_ratio, y_ratio):
        self.x_ratio, self.y_ratio = x_ratio, y_ratio
        self.rect = pygame.Rect(0, 0, BASE_GUARD_SIZE, BASE_GUARD_SIZE)
        self.sprite_name = "dealer.png"

    def resize(self, scale_x, scale_y):
        scale = get_world_scale(scale_x, scale_y)
        size = int(BASE_GUARD_SIZE * scale)
        self.rect.size = (size, size)
        self.reposition()

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def draw(self, surface):
        sprite_size = (
            int(self.rect.width * NPC_VISUAL_WIDTH_SCALE),
            int(self.rect.height * NPC_VISUAL_SCALE),
        )
        sprite = load_sprite_sheet_frame(self.sprite_name, sprite_size)
        draw_shadow(surface, self.rect, width_ratio=0.58, height_ratio=0.18, alpha=60)
        surface.blit(sprite, sprite.get_rect(midbottom=(self.rect.centerx, self.rect.bottom + 2)))

class Door:
    def __init__(self, rect, target_room, spawn_pos):
        self.rect = rect
        self.target_room = target_room
        self.spawn_pos = spawn_pos


def resolve_asset_path(*path_parts):
    relative_path = Path(*path_parts)
    candidates = [relative_path]

    # Support callers that still pass "ui/..." while the files live in Assets/ui/.
    if relative_path.parts and relative_path.parts[0].lower() == "ui":
        candidates.append(Path("Assets") / relative_path)
        candidates.append(Path("assets") / relative_path)

    for root in ASSET_SEARCH_ROOTS:
        for candidate in candidates:
            asset_path = root / candidate
            if asset_path.exists():
                return asset_path

    raise FileNotFoundError(f"Unable to find asset: {relative_path}")


def load_image_asset(*path_parts, size=None, pixel_art=False):
    asset_path = resolve_asset_path(*path_parts)
    cache_key = (str(asset_path), size)

    if cache_key in IMAGE_CACHE:
        return IMAGE_CACHE[cache_key]

    try:
        image = pygame.image.load(str(asset_path))
    except pygame.error:
        with Image.open(asset_path) as pil_image:
            converted = pil_image.convert("RGBA")
            image = pygame.image.fromstring(
                converted.tobytes(),
                converted.size,
                converted.mode,
            )
    if pygame.display.get_init() and pygame.display.get_surface() is not None:
        image = image.convert_alpha()

    if size is not None:
        scaler = pygame.transform.scale if pixel_art else pygame.transform.smoothscale
        image = scaler(image, size)

    IMAGE_CACHE[cache_key] = image
    return image


def load_sprite_sheet_frame(asset_name, size, frame_col=0, frame_row=0, cols=4, rows=4):
    cache_key = ("sheet_frame", asset_name, size, frame_col, frame_row, cols, rows)
    if cache_key in IMAGE_CACHE:
        return IMAGE_CACHE[cache_key]

    sheet = load_image_asset(asset_name)
    frame_rect = sprite_loader._grid_frame_rect(sheet, cols, rows, frame_col, frame_row)
    frame = pygame.Surface((frame_rect.width, frame_rect.height), pygame.SRCALPHA)
    frame.blit(sheet, (0, 0), frame_rect)
    frame = sprite_loader._prepare_sprite_surface(frame)
    frame = scale_surface_to_rect(frame, pygame.Rect(0, 0, size[0], size[1]))
    IMAGE_CACHE[cache_key] = frame
    return frame

# --------------------------------------------------
# ANIMATION SYSTEM FOR CARD DEALING
# --------------------------------------------------
class CardAnimation:
    def __init__(self, card_image, from_pos, to_pos, speed=0.1):
        self.image = card_image
        self.from_pos = pygame.math.Vector2(from_pos)
        self.to_pos = pygame.math.Vector2(to_pos)
        self.progress = 0.0
        self.speed = speed

    def update(self):
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            return True
        return False

    def get_current_pos(self):
        return self.from_pos.lerp(self.to_pos, self.progress)

    def draw(self, surface):
        pos = self.get_current_pos()
        rect = self.image.get_rect(center=pos)
        surface.blit(self.image, rect)

# --------------------------------------------------
# ROOM CONFIGURATIONS
# --------------------------------------------------
# Room 0 (green) – starting room with tables, NPCs, guards
# Room 1 (blue) – different table positions, no NPCs
# Room 2 (rose/red) – different table positions, no NPCs

# Current active room elements
tables = []
playable_tables = []
room_props = []
npcs = []
guards = []


def create_table_npc(
    table_rect,
    x_offset_ratio=0.0,
    y_offset_ratio=0.38,
    facing="down",
    sprite_name="dealer.png",
    use_sprite_sheet=False,
):
    npc_x = (table_rect.centerx + table_rect.width * x_offset_ratio) / WIDTH
    npc_y = (table_rect.top - table_rect.height * y_offset_ratio) / HEIGHT
    npc = NPC(npc_x, npc_y, facing=facing, use_sprite_sheet=use_sprite_sheet)
    npc.sprite_name = sprite_name
    return npc

def set_room_layout(room_idx, scale_x, scale_y):
    """Set up room objects using a uniform visual scale inside the playable floor."""
    global tables, playable_tables, room_props, npcs, guards
    visual_scale = get_world_scale(scale_x, scale_y)
    table_w = int(BASE_TABLE_W * visual_scale)
    table_h = int(BASE_TABLE_H * visual_scale)
    room_table_scale = {0: 1.0, 1: 0.82, 2: 0.78}.get(room_idx, 1.0)
    room_prop_scale = {0: 1.0, 1: 0.84, 2: 0.8}.get(room_idx, 1.0)
    table_w = int(table_w * room_table_scale)
    table_h = int(table_h * room_table_scale)
    side_table_w = table_w
    side_table_h = table_h
    prop_unit_w = max(32, int(table_w * 0.95 * room_prop_scale))
    prop_unit_h = max(32, int(table_h * 0.95 * room_prop_scale))

    floor_rect = get_room_interior_bounds(room_idx, scale_x, scale_y)

    def scaled_rect(x_ratio, y_ratio, width, height):
        return pygame.Rect(
            int(floor_rect.left + floor_rect.width * x_ratio),
            int(floor_rect.top + floor_rect.height * y_ratio),
            width,
            height,
        )

    def scaled_prop_rect(x_ratio, y_ratio, width_scale, height_scale):
        return scaled_rect(
            x_ratio,
            y_ratio,
            int(prop_unit_w * width_scale),
            int(prop_unit_h * height_scale),
        )
    
    if room_idx == 0:
        playable_tables = [
            scaled_rect(0.45, 0.40, table_w, table_h)
        ]
        tables = playable_tables + [
            scaled_rect(0.15, 0.24, side_table_w, side_table_h),
            scaled_rect(0.73, 0.52, side_table_w, side_table_h),
        ]
        room_props = []
        npcs = [
            create_table_npc(playable_tables[0], facing="down", sprite_name="dealer.png"),
        ]
        guards = []
    elif room_idx == 1:
        playable_tables = [
            scaled_rect(0.47, 0.41, table_w, table_h)
        ]
        tables = playable_tables + [
            scaled_rect(0.67, 0.26, side_table_w, side_table_h),
            scaled_rect(0.62, 0.58, side_table_w, side_table_h),
        ]
        room_props = []
        npcs = [
            create_table_npc(playable_tables[0], facing="down", sprite_name="Boss.png"),
        ]
        guards = []
    else:  # room_idx == 2
        playable_tables = [
            scaled_rect(0.52, 0.42, table_w, table_h)
        ]
        tables = playable_tables + [
            scaled_rect(0.22, 0.22, side_table_w, side_table_h),
            scaled_rect(0.25, 0.62, side_table_w, side_table_h),
        ]
        room_props = []
        npcs = [
            create_table_npc(playable_tables[0], facing="down", sprite_name="dealer.png"),
        ]
        guards = []
    
    # Apply scaling to NPCs and Guards
    for n in npcs:
        n.resize(scale_x, scale_y)
    for g in guards:
        g.resize(scale_x, scale_y)
        g.sprite_name = "Boss.png" if room_idx == 0 and g is guards[0] else "dealer.png"

# --------------------------------------------------
# INITIALIZATION & RESIZING
# --------------------------------------------------
player = WorldPlayer()
persistent_player = PersistentPlayer("You")
persistent_player.chips = 500
walls = []
doors = []
current_room = 0
current_scale_x = 1.0
current_scale_y = 1.0

# Poker Buttons 
checkCall_btn = Button("Check/Call", 0.2, 0.9, 0.15, 0.06)
raise_btn = Button("Raise (50$)", 0.4, 0.9, 0.15, 0.06)
fold_btn = Button("Fold", 0.6, 0.9, 0.15, 0.06)
leave_btn = Button("Leave", 0.8, 0.9, 0.15, 0.06)
play_again_btn = Button("Play Again", 0.4, 0.85, 0.2, 0.08)
leave_table_btn = Button("Leave Table", 0.6, 0.85, 0.2, 0.08)

# Menu buttons
volume_slider_btn = Button("Volume: 50%", 0.5, 0.4, 0.3, 0.07)
abandon_btn = Button("Abandon Mission", 0.5, 0.55, 0.3, 0.07)
save_exit_btn = Button("Save & Exit", 0.5, 0.7, 0.3, 0.07)
resume_btn = Button("Resume", 0.5, 0.85, 0.3, 0.07)

# Main menu buttons
new_game_btn = Button("New Game", 0.5, 0.4, 0.3, 0.08)
continue_btn = Button("Continue", 0.5, 0.55, 0.3, 0.08)
quit_main_btn = Button("Quit", 0.5, 0.7, 0.3, 0.08)

# Animation globals
deck_pos = (WIDTH * 0.1, HEIGHT * 0.5)
active_animations = []
animating = False
animating_card_keys = set()  # (type, index) where type = 'human', 'boss', 'community'

# Boss message system
boss_message_text = None
boss_message_timer = 0  # milliseconds remaining
boss_thinking = False
boss_think_start_time = 0
boss_think_duration = 0
current_boss_difficulty = None
table_intro_shown = {"easy": False, "medium": False, "hard": False}
show_hand_menu = False
last_hand_player_won = False
ENTRY_COST = {"easy": 50, "medium": 100, "hard": 200}
escape_menu_active = False
story_mode_active = False
current_story_page = 0
SAVE_FILE = PROJECT_ROOT / "savegame.json"


def default_boss_chips():
    return {"easy": 1000, "medium": 2000, "hard": 4000}


def save_game():
    data = {
        "chips": persistent_player.chips,
        "boss_chips": persistent_player.boss_chips,
        "beaten_bosses": persistent_player.beaten_bosses,
        "buffs": persistent_player.buffs,
        "second_chance_used": persistent_player.second_chance_used,
        "table_intro_shown": table_intro_shown,
        "current_room": current_room,
        "player_x_ratio": player.x_ratio,
        "player_y_ratio": player.y_ratio,
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_game():
    global table_intro_shown, current_room
    if not SAVE_FILE.exists():
        return False

    with open(SAVE_FILE, "r") as f:
        data = json.load(f)

    persistent_player.chips = data.get("chips", 500)
    persistent_player.buffs = data.get("buffs", [])
    persistent_player.beaten_bosses = data.get("beaten_bosses", [])
    persistent_player.second_chance_used = data.get("second_chance_used", False)
    persistent_player.boss_chips = data.get("boss_chips", default_boss_chips())
    if "boss_chips" not in data:
        for defeated in persistent_player.beaten_bosses:
            if defeated in persistent_player.boss_chips:
                persistent_player.boss_chips[defeated] = 0

    table_intro_shown = data.get("table_intro_shown", {"easy": False, "medium": False, "hard": False})
    current_room = data.get("current_room", 0)
    player.x_ratio = data.get("player_x_ratio", 0.1)
    player.y_ratio = data.get("player_y_ratio", 0.1)
    recalculate_elements()
    return True


def reset_new_game():
    global table_intro_shown, current_room, story_mode_active, current_story_page
    persistent_player.chips = 500
    persistent_player.beaten_bosses = []
    persistent_player.buffs = []
    persistent_player.second_chance_used = False
    persistent_player.boss_chips = default_boss_chips()
    table_intro_shown = {"easy": False, "medium": False, "hard": False}
    current_room = 0
    player.x_ratio = 0.1
    player.y_ratio = 0.1
    recalculate_elements()
    story_mode_active = True
    current_story_page = 0

def set_boss_message(msg):
    global boss_message_text, boss_message_timer
    boss_message_text = msg
    # want to implement a delay for this to make boss have to "think" about its decisions
    boss_message_timer = 3000

def update_boss_message(dt_ms):
    global boss_message_timer, boss_message_text
    if boss_message_timer > 0:
        boss_message_timer -= dt_ms
        if boss_message_timer <= 0:
            boss_message_text = None

def draw_boss_message(surface):
    if boss_message_text:
        # Create a semi-transparent background surface
        msg_surf = boss_font.render(boss_message_text, True, GOLD)
        padding = 15
        bg_rect = msg_surf.get_rect().inflate(padding*2, padding)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        # Position above dealer's hand
        x = WIDTH * 0.15
        y = HEIGHT * 0.05
        bg_rect.topleft = (x, y)
        screen.blit(bg_surf, bg_rect)
        screen.blit(msg_surf, msg_surf.get_rect(center=bg_rect.center))

# Card back image (scaled independently)
def get_card_back_image(scale_x, scale_y):
    card_w = int(BASE_CARD_W * scale_x)
    card_h = int(BASE_CARD_H * scale_y)
    back_surf = pygame.Surface((card_w, card_h))
    back_surf.fill(CARD_BACK_COLOR)
    pygame.draw.rect(back_surf, GOLD, back_surf.get_rect(), 3, border_radius=5)
    pygame.draw.line(back_surf, (200,150,100), (0,0), (card_w, card_h), 2)
    pygame.draw.line(back_surf, (200,150,100), (card_w,0), (0, card_h), 2)
    return back_surf

# Global card_back_img, will be updated on resize
card_back_img = get_card_back_image(1.0, 1.0)

def get_room_bounds(room_idx, scale_x=None, scale_y=None):
    scale_x = current_scale_x if scale_x is None else scale_x
    scale_y = current_scale_y if scale_y is None else scale_y

    insets = {
        0: (max(18, int(24 * scale_x)), max(16, int(20 * scale_y))),
        1: (max(74, int(102 * scale_x)), max(46, int(68 * scale_y))),
        2: (max(54, int(78 * scale_x)), max(38, int(56 * scale_y))),
    }
    inset_x, inset_y = insets.get(room_idx, insets[0])
    width = max(220, WIDTH - inset_x * 2)
    height = max(180, HEIGHT - inset_y * 2)
    return pygame.Rect(inset_x, inset_y, width, height)

def get_wall_thickness(room_idx=None, scale_x=None, scale_y=None):
    room_idx = current_room if room_idx is None else room_idx
    scale_x = current_scale_x if scale_x is None else scale_x
    scale_y = current_scale_y if scale_y is None else scale_y
    wall_scale = {0: 1.0, 1: 2.45, 2: 2.1}.get(room_idx, 1.0)
    return (
        int(BASE_WALL_THICK * scale_x * wall_scale),
        int(BASE_WALL_THICK * scale_y * wall_scale),
    )

def get_room_interior_bounds(room_idx, scale_x=None, scale_y=None):
    scale_x = current_scale_x if scale_x is None else scale_x
    scale_y = current_scale_y if scale_y is None else scale_y
    room_bounds = get_room_bounds(room_idx, scale_x, scale_y)
    wall_thick_x, wall_thick_y = get_wall_thickness(room_idx, scale_x, scale_y)
    return room_bounds.inflate(-wall_thick_x * 2, -wall_thick_y * 2)

def clamp_player_to_current_room():
    interior = get_room_interior_bounds(current_room)
    player.rect.clamp_ip(interior)
    player.x_ratio = player.rect.centerx / WIDTH
    player.y_ratio = player.rect.centery / HEIGHT

def draw_tiled_floor(surface, room_idx):
    """Draw a centered tiled floor with less visual noise than the placeholder grid."""
    room_bounds = get_room_bounds(room_idx)

    # Available space for tiles (excluding gaps)
    total_gap_width = (TILE_COLS - 1) * TILE_GAP
    total_gap_height = (TILE_ROWS - 1) * TILE_GAP
    
    tile_width = room_bounds.width // TILE_COLS
    tile_height = room_bounds.height // TILE_ROWS
    
    # If tile dimensions are zero or negative, fallback to simple fill
    if tile_width <= 0 or tile_height <= 0:
        surface.fill(ROOM_COLORS[room_idx][1])
        return
    
    # Total size of the drawn grid
    grid_width = TILE_COLS * tile_width + total_gap_width
    grid_height = TILE_ROWS * tile_height + total_gap_height
    start_x = room_bounds.x + (room_bounds.width - grid_width) // 2
    start_y = room_bounds.y + (room_bounds.height - grid_height) // 2
    
    # Keep the non-playable area subdued so smaller rooms still fill the screen visually.
    surface.fill((14, 12, 12))
    tile_surface = get_world_floor_tile(room_idx, (tile_width, tile_height))
    
    # Draw tiles
    for row in range(TILE_ROWS):
        for col in range(TILE_COLS):
            x = start_x + col * (tile_width + TILE_GAP)
            y = start_y + row * (tile_height + TILE_GAP)
            surface.blit(tile_surface, (x, y))

    # Subtle vignette keeps the edges from feeling flat without reintroducing a harsh grid.
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(vignette, (0, 0, 0, 24), room_bounds.inflate(20, 20), border_radius=24)
    inner_rect = room_bounds.inflate(-max(40, room_bounds.width // 7), -max(30, room_bounds.height // 7))
    pygame.draw.rect(vignette, (0, 0, 0, 0), inner_rect, border_radius=20)
    surface.blit(vignette, (0, 0))


def draw_poker_background(surface, room_idx):
    bg_color = ROOM_COLORS[room_idx][1]
    bg_color_light = tuple(min(255, c + 20) for c in bg_color)
    surface.fill(bg_color_light)
    light_color, dark_color = ROOM_COLORS[room_idx]
    table_rect = pygame.Rect(WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(surface, dark_color, table_rect, border_radius=20)
    pygame.draw.rect(surface, light_color, table_rect.inflate(-10, -10), border_radius=15)
    pygame.draw.rect(surface, GOLD, table_rect, 3, border_radius=20)

def create_walls_and_doors(scale_x, scale_y):
    """
    Create wall segments with gaps only on the walls that should have doors,
    based on the current room. Sizes scale independently per axis.
    """
    global walls, doors
    door_gap_x = int(DOOR_SIZE * scale_x)   # width of horizontal door gaps
    door_gap_y = int(DOOR_SIZE * scale_y)   # height of vertical door gaps
    wall_thick_x, wall_thick_y = get_wall_thickness(current_room, scale_x, scale_y)
    room_bounds = get_room_bounds(current_room, scale_x, scale_y)
    doors = []

    # Top wall: horizontal, thickness uses scale_y, width uses scale_x
    if current_room == 0:
        top_left = pygame.Rect(room_bounds.left, room_bounds.top, (room_bounds.width - door_gap_x) // 2, wall_thick_y)
        top_right = pygame.Rect(room_bounds.centerx + door_gap_x // 2, room_bounds.top, (room_bounds.width - door_gap_x) // 2, wall_thick_y)
        top_door_rect = pygame.Rect(room_bounds.centerx - door_gap_x // 2, room_bounds.top, door_gap_x, wall_thick_y)
    else:
        top_left = pygame.Rect(room_bounds.left, room_bounds.top, room_bounds.width, wall_thick_y)
        top_right = None
        top_door_rect = None

    # Bottom wall
    if current_room == 1:
        bottom_left = pygame.Rect(room_bounds.left, room_bounds.bottom - wall_thick_y, (room_bounds.width - door_gap_x) // 2, wall_thick_y)
        bottom_right = pygame.Rect(room_bounds.centerx + door_gap_x // 2, room_bounds.bottom - wall_thick_y, (room_bounds.width - door_gap_x) // 2, wall_thick_y)
        bottom_door_rect = pygame.Rect(room_bounds.centerx - door_gap_x // 2, room_bounds.bottom - wall_thick_y, door_gap_x, wall_thick_y)
    else:
        bottom_left = pygame.Rect(room_bounds.left, room_bounds.bottom - wall_thick_y, room_bounds.width, wall_thick_y)
        bottom_right = None
        bottom_door_rect = None

    # Left wall: vertical, thickness uses scale_x, height uses scale_y
    if current_room == 2:
        left_top = pygame.Rect(room_bounds.left, room_bounds.top, wall_thick_x, (room_bounds.height - door_gap_y) // 2)
        left_bottom = pygame.Rect(room_bounds.left, room_bounds.centery + door_gap_y // 2, wall_thick_x, (room_bounds.height - door_gap_y) // 2)
        left_door_rect = pygame.Rect(room_bounds.left, room_bounds.centery - door_gap_y // 2, wall_thick_x, door_gap_y)
    else:
        left_top = pygame.Rect(room_bounds.left, room_bounds.top, wall_thick_x, room_bounds.height)
        left_bottom = None
        left_door_rect = None

    # Right wall
    if current_room == 0:
        right_top = pygame.Rect(room_bounds.right - wall_thick_x, room_bounds.top, wall_thick_x, (room_bounds.height - door_gap_y) // 2)
        right_bottom = pygame.Rect(room_bounds.right - wall_thick_x, room_bounds.centery + door_gap_y // 2, wall_thick_x, (room_bounds.height - door_gap_y) // 2)
        right_door_rect = pygame.Rect(room_bounds.right - wall_thick_x, room_bounds.centery - door_gap_y // 2, wall_thick_x, door_gap_y)
    else:
        right_top = pygame.Rect(room_bounds.right - wall_thick_x, room_bounds.top, wall_thick_x, room_bounds.height)
        right_bottom = None
        right_door_rect = None

    # Collect wall pieces
    walls = []
    if top_left: walls.append(top_left)
    if top_right: walls.append(top_right)
    if bottom_left: walls.append(bottom_left)
    if bottom_right: walls.append(bottom_right)
    if left_top: walls.append(left_top)
    if left_bottom: walls.append(left_bottom)
    if right_top: walls.append(right_top)
    if right_bottom: walls.append(right_bottom)

    # Create door objects (spawn positions not used here)
    if top_door_rect and current_room == 0:
        doors.append(Door(top_door_rect, 1, None))
    if bottom_door_rect and current_room == 1:
        doors.append(Door(bottom_door_rect, 0, None))
    if left_door_rect and current_room == 2:
        doors.append(Door(left_door_rect, 0, None))
    if right_door_rect and current_room == 0:
        doors.append(Door(right_door_rect, 2, None))

def recalculate_elements():
    global walls, deck_pos, card_back_img, doors, tables, playable_tables, room_props, npcs, guards, current_scale_x, current_scale_y
    # Compute independent axis scales based on reference 1280x720
    current_scale_x = WIDTH / 1280.0
    current_scale_y = HEIGHT / 720.0
    
    # Scale player size
    player.resize(current_scale_x, current_scale_y)
    # Recreate walls and doors with new scales
    create_walls_and_doors(current_scale_x, current_scale_y)
    # Reload the current room's layout with scaled tables and entities
    set_room_layout(current_room, current_scale_x, current_scale_y)
    
    # Ensure player is not stuck inside any collider after resize
    all_colliders = walls + tables + [g.rect for g in guards] + [door.rect for door in doors]
    for collider in all_colliders:
        if player.rect.colliderect(collider):
            # Push player out of collider
            overlap_left = player.rect.right - collider.left
            overlap_right = collider.right - player.rect.left
            overlap_top = player.rect.bottom - collider.top
            overlap_bottom = collider.bottom - player.rect.top
            # Move by smallest overlap
            if overlap_left < overlap_right and overlap_left < overlap_top and overlap_left < overlap_bottom:
                player.rect.right = collider.left
            elif overlap_right < overlap_left and overlap_right < overlap_top and overlap_right < overlap_bottom:
                player.rect.left = collider.right
            elif overlap_top < overlap_left and overlap_top < overlap_right and overlap_top < overlap_bottom:
                player.rect.bottom = collider.top
            else:
                player.rect.top = collider.bottom
    player.x_ratio = player.rect.centerx / WIDTH
    player.y_ratio = player.rect.centery / HEIGHT
    clamp_player_to_current_room()
    deck_pos = (WIDTH * 0.1, HEIGHT * 0.5)
    card_back_img = get_card_back_image(current_scale_x, current_scale_y)

# Initial setup (default 1280x720)
recalculate_elements()
game_state, poker_game = "main_menu", None

def near_table():
    for table in playable_tables:
        if player.rect.colliderect(table.inflate(40, 40)): return True
    return False

def near_any_door():
    for door in doors:
        if player.rect.colliderect(door.rect.inflate(30, 30)):
            return door
    return None

def get_door_direction(door_rect, wall_thick_x, wall_thick_y):
    """Return 'top', 'bottom', 'left', or 'right' based on door position."""
    room_bounds = get_room_bounds(current_room)
    if door_rect.y == room_bounds.top:
        return 'top'
    if door_rect.y == room_bounds.bottom - wall_thick_y:
        return 'bottom'
    if door_rect.x == room_bounds.left:
        return 'left'
    if door_rect.x == room_bounds.right - wall_thick_x:
        return 'right'
    return None

def teleport_player_through_door(exit_direction):
    """
    Place the player just inside the new room, on the opposite side from which they exited.
    """
    entry_side = {
        'top': 'bottom',
        'bottom': 'top',
        'left': 'right',
        'right': 'left'
    }.get(exit_direction, None)
    
    # Use player's own size to compute offset
    offset_x = player.rect.width // 2 + 10
    offset_y = player.rect.height // 2 + 10
    room_bounds = get_room_bounds(current_room)
    wall_thick_x, wall_thick_y = get_wall_thickness(current_room)
    
    if entry_side == 'top':
        player.rect.centerx = room_bounds.centerx
        player.rect.centery = room_bounds.top + wall_thick_y + offset_y
    elif entry_side == 'bottom':
        player.rect.centerx = room_bounds.centerx
        player.rect.centery = room_bounds.bottom - wall_thick_y - offset_y
    elif entry_side == 'left':
        player.rect.centerx = room_bounds.left + wall_thick_x + offset_x
        player.rect.centery = room_bounds.centery
    elif entry_side == 'right':
        player.rect.centerx = room_bounds.right - wall_thick_x - offset_x
        player.rect.centery = room_bounds.centery
    else:
        player.rect.center = room_bounds.center
    clamp_player_to_current_room()

def load_card_image(card):
    try:
        card_w = int(BASE_CARD_W * current_scale_x)
        card_h = int(BASE_CARD_H * current_scale_y)
        return load_image_asset("ui", f"{card.rank}_of_{card.suit}.png", size=(card_w, card_h))
    except:
        return None

def get_target_position_for_card(card, card_index, card_type):
    card_w = int(BASE_CARD_W * current_scale_x)
    card_h = int(BASE_CARD_H * current_scale_y)
    spacing = card_w + 10

    if card_type == 'human':
        x_hand = WIDTH/2 - (2 * spacing) / 2
        return (x_hand + card_index * spacing + card_w/2, HEIGHT * 0.65 + card_h/2)
    elif card_type == 'boss':
        dealer_x = 60
        dealer_y = HEIGHT * 0.12
        return (dealer_x + card_index * spacing + card_w/2, dealer_y + card_h/2)
    elif card_type == 'community':
        total_community = len(poker_game.table.communityCards) if poker_game else 0
        x_comm = WIDTH/2 - (total_community * spacing) / 2
        return (x_comm + card_index * spacing + card_w/2, HEIGHT/2)
    return (WIDTH//2, HEIGHT//2)

# Store previous card states
prev_human_cards = []
prev_boss_cards = []
prev_community_cards = []

def create_animation_for_card(card, idx, ctype):
    global active_animations, animating_card_keys, animating
    if ctype == 'boss':
        img = card_back_img
    else:
        img = load_card_image(card)
        if img is None:
            return
    to_pos = get_target_position_for_card(card, idx, ctype)
    anim = CardAnimation(img, deck_pos, to_pos, speed=0.08)
    active_animations.append(anim)
    animating_card_keys.add((ctype, idx))
    animating = True

def detect_and_animate_new_cards():
    global prev_human_cards, prev_boss_cards, prev_community_cards
    if poker_game is None:
        return

    # Human
    current_human = poker_game.human.hand[:]
    if len(current_human) > len(prev_human_cards):
        for i in range(len(prev_human_cards), len(current_human)):
            create_animation_for_card(current_human[i], i, 'human')
    prev_human_cards = current_human[:]

    # Boss
    current_boss = poker_game.boss.hand[:]
    if len(current_boss) > len(prev_boss_cards):
        for i in range(len(prev_boss_cards), len(current_boss)):
            create_animation_for_card(current_boss[i], i, 'boss')
    prev_boss_cards = current_boss[:]

    # Community
    current_community = poker_game.table.communityCards[:]
    if len(current_community) > len(prev_community_cards):
        for i in range(len(prev_community_cards), len(current_community)):
            create_animation_for_card(current_community[i], i, 'community')
    prev_community_cards = current_community[:]

def update_animations():
    global active_animations, animating, animating_card_keys
    if not active_animations:
        animating = False
        animating_card_keys.clear()
        return
    remaining = []
    for anim in active_animations:
        if not anim.update():
            remaining.append(anim)
    active_animations = remaining
    if not active_animations:
        animating = False
        animating_card_keys.clear()

def draw_deck(surface):
    card_w = int(BASE_CARD_W * current_scale_x)
    card_h = int(BASE_CARD_H * current_scale_y)
    deck_rect = pygame.Rect(0, 0, card_w, card_h)
    deck_rect.center = deck_pos
    pygame.draw.rect(surface, (100, 50, 0), deck_rect, border_radius=5)
    pygame.draw.rect(surface, GOLD, deck_rect, 3, border_radius=5)
    deck_text = font.render("DECK", True, WHITE)
    surface.blit(deck_text, deck_text.get_rect(center=deck_rect.center))


def room_difficulty(room):
    if room == 0:
        return "easy", 1
    if room == 1:
        return "medium", 2
    return "hard", 3


def start_poker_game(room, intro_dialogue=True):
    """Create a poker game using the persistent player and boss chip stacks."""
    global poker_game, current_boss_difficulty, boss_thinking, boss_think_start_time, boss_think_duration
    global show_hand_menu, prev_human_cards, prev_boss_cards, prev_community_cards
    global animating, boss_message_text

    diff_str, diff_num = room_difficulty(room)
    actual_cost = min(ENTRY_COST[diff_str], persistent_player.boss_chips[diff_str])
    allowed, msg = persistent_player.can_play_table(diff_str, actual_cost)
    if not allowed:
        set_boss_message(msg)
        return False

    if intro_dialogue and not table_intro_shown.get(diff_str, False):
        boss_name = BOSS_DIALOGUE[diff_str]["name"]
        lines = [
            f"You approach {boss_name}'s table.",
            f"{boss_name}: 'Buy-in is ${actual_cost}. Let's see what you have.'",
        ]
        if diff_str == "easy":
            lines.insert(1, "The worn green felt has seen better nights.")
        elif diff_str == "medium":
            lines.insert(1, "The blue room goes quiet as the Sharp Lady smiles.")
        else:
            lines.insert(1, "The red room feels colder than the hallway behind you.")
        show_dialogue_screen(lines)
        table_intro_shown[diff_str] = True

    persistent_player.chips -= actual_cost

    human_player = Player("You")
    human_player.chips = persistent_player.chips

    boss_name = BOSS_DIALOGUE[diff_str]["name"]
    boss_player = Boss(boss_name, "serious", diff_num)
    boss_player.chips = persistent_player.boss_chips[diff_str] - actual_cost

    poker_game = ActiveGame(human_player, boss_player)
    current_boss_difficulty = diff_str
    poker_game.newHand()
    poker_game.table.pot = actual_cost * 2

    prev_human_cards = []
    prev_boss_cards = []
    prev_community_cards = []
    active_animations.clear()
    animating = False
    animating_card_keys.clear()
    detect_and_animate_new_cards()

    boss_message_text = None
    boss_thinking = False
    boss_think_start_time = 0
    boss_think_duration = 0
    show_hand_menu = False
    return True


def start_table_dialogue(room):
    global game_state
    if start_poker_game(room, intro_dialogue=True):
        game_state = "poker"


def restart_poker_game():
    global game_state
    if poker_game:
        persistent_player.chips = poker_game.human.chips
        persistent_player.boss_chips[current_boss_difficulty] = poker_game.boss.chips
    cleanup_poker_state()
    game_state = "poker" if start_poker_game(current_room, intro_dialogue=False) else "world"


def cleanup_poker_state():
    global active_animations, animating, animating_card_keys, prev_human_cards, prev_boss_cards, prev_community_cards
    global boss_message_text, boss_message_timer, boss_thinking, poker_game, show_hand_menu
    active_animations.clear()
    animating = False
    animating_card_keys.clear()
    prev_human_cards = []
    prev_boss_cards = []
    prev_community_cards = []
    boss_message_text = None
    boss_message_timer = 0
    boss_thinking = False
    poker_game = None
    show_hand_menu = False


def check_and_exit_poker_if_defeated():
    global game_state
    if poker_game is None:
        return
    if poker_game.human.chips <= 0:
        show_dialogue_screen(["You're out of chips! Your cover is blown.", "The Syndicate vanishes into the night."])
        game_state = "game_over"
        cleanup_poker_state()
    elif poker_game.boss.chips <= 0:
        persistent_player.chips = poker_game.human.chips
        persistent_player.boss_chips[current_boss_difficulty] = 0
        show_dialogue_screen(BOSS_DIALOGUE[current_boss_difficulty]["defeat"])
        persistent_player.add_buff(BOSS_DIALOGUE[current_boss_difficulty]["buff"])

        if current_boss_difficulty not in persistent_player.beaten_bosses:
            persistent_player.beaten_bosses.append(current_boss_difficulty)

        defeated = current_boss_difficulty
        cleanup_poker_state()
        game_state = "ending" if defeated == "hard" else "world"


def show_dialogue_screen(lines):
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
        screen.fill((0, 0, 0))
        y_offset = HEIGHT // 2 - (len(lines) * 30) // 2
        for line in lines:
            text_surf = font.render(line, True, WHITE)
            screen.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, y_offset))
            y_offset += 40
        pygame.display.flip()
        clock.tick(30)

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------
running = True
last_time = pygame.time.get_ticks()

while running:
    current_time = pygame.time.get_ticks()
    dt = current_time - last_time
    last_time = current_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.size
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            recalculate_elements()

        if game_state == "main_menu":
            if new_game_btn.clicked(event):
                reset_new_game()
                game_state = "story"
            if continue_btn.clicked(event):
                if load_game():
                    game_state = "world"
                else:
                    set_boss_message("No saved game found.")
            if quit_main_btn.clicked(event):
                running = False

        if game_state == "story":
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if current_story_page + 1 < len(STORY_PAGES):
                    current_story_page += 1
                else:
                    story_mode_active = False
                    game_state = "world"
                    current_room = 0
                    recalculate_elements()
                    player.rect.center = (WIDTH * 0.3, HEIGHT * 0.5)
                    player.x_ratio = player.rect.centerx / WIDTH
                    player.y_ratio = player.rect.centery / HEIGHT
            continue

        if game_state == "world" and escape_menu_active:
            if resume_btn.clicked(event):
                escape_menu_active = False
            if abandon_btn.clicked(event):
                game_state = "game_over"
                escape_menu_active = False
            if save_exit_btn.clicked(event):
                save_game()
                running = False
            if volume_slider_btn.clicked(event):
                if "50%" in volume_slider_btn.text:
                    volume_slider_btn.text = "Volume: 75%"
                elif "75%" in volume_slider_btn.text:
                    volume_slider_btn.text = "Volume: 100%"
                else:
                    volume_slider_btn.text = "Volume: 50%"

        if game_state == "world" and not escape_menu_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                escape_menu_active = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if near_table():
                    diff_str, _ = room_difficulty(current_room)
                    actual_cost = min(ENTRY_COST[diff_str], persistent_player.boss_chips[diff_str])
                    allowed, msg = persistent_player.can_play_table(diff_str, actual_cost)
                    if not allowed:
                        set_boss_message(msg)
                    else:
                        start_table_dialogue(current_room)
                else:
                    door = near_any_door()
                    if door:
                        if door.target_room == 2 and not persistent_player.has_buff("High Roller"):
                            set_boss_message(BOSS_DIALOGUE["medium"]["door_lock"])
                            continue
                        if door.target_room == 1 and not persistent_player.has_buff("Lucky Draw"):
                            set_boss_message(BOSS_DIALOGUE["easy"]["door_lock"])
                            continue
                        wall_thick_x, wall_thick_y = get_wall_thickness(current_room)
                        direction = get_door_direction(door.rect, wall_thick_x, wall_thick_y)
                        current_room = door.target_room
                        recalculate_elements()
                        if direction:
                            teleport_player_through_door(direction)

        elif game_state == "poker":
            if not animating and not boss_thinking and not show_hand_menu:
                if checkCall_btn.clicked(event):
                    callAmount = poker_game.getCallAmount(poker_game.currentPlayer)
                    if callAmount > poker_game.human.chips:
                        set_boss_message("Not enough chips to call!")
                        continue
                    action = Action("check") if callAmount <= 0 else Action("call")
                    action.processAction(poker_game.currentPlayer, poker_game)
                    poker_game.playerActed = True
                    boss_thinking = True
                    boss_think_start_time = current_time
                    boss_think_duration = random.randint(500, 2000)
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["think"])
                    set_boss_message(f"{BOSS_DIALOGUE[current_boss_difficulty]['name']}: '{dialogue_option}'")

                if raise_btn.clicked(event):
                    callAmount = poker_game.getCallAmount(poker_game.currentPlayer)
                    total_needed = callAmount + 50
                    if total_needed > poker_game.human.chips:
                        set_boss_message(f"Not enough chips to raise! Need ${total_needed}.")
                        continue
                    action = Action("raise", 50)
                    action.processAction(poker_game.currentPlayer, poker_game)
                    poker_game.playerActed = True
                    boss_thinking = True
                    boss_think_start_time = current_time
                    boss_think_duration = random.randint(500, 2000)
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["think"])
                    set_boss_message(f"{BOSS_DIALOGUE[current_boss_difficulty]['name']}: '{dialogue_option}'")

                if fold_btn.clicked(event):
                    action = Action("fold")
                    action.processAction(poker_game.currentPlayer, poker_game)
                    poker_game.handWinner = poker_game.boss
                    poker_game.phase = "handCheck"
                    poker_game.phaseIndex = GAMEPHASE.index("handCheck")
                    poker_game.playerActed = False
                    poker_game.bossActed = False

                if leave_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    persistent_player.chips = poker_game.human.chips
                    persistent_player.boss_chips[current_boss_difficulty] = poker_game.boss.chips
                    cleanup_poker_state()
                    game_state = "world"

            if show_hand_menu and not animating:
                if play_again_btn.clicked(event):
                    restart_poker_game()
                if leave_table_btn.clicked(event):
                    persistent_player.chips = poker_game.human.chips
                    persistent_player.boss_chips[current_boss_difficulty] = poker_game.boss.chips
                    cleanup_poker_state()
                    game_state = "world"

        if event.type == pygame.KEYDOWN:
            if game_state in ("game_over", "ending") and event.key == pygame.K_ESCAPE:
                game_state = "main_menu"

    # UPDATE
    # Compute speed scales for player and NPCs based on window dimensions
    speed_scale_x = WIDTH / 1280.0
    speed_scale_y = HEIGHT / 720.0
    player_speed_x = player.base_speed * speed_scale_x
    player_speed_y = player.base_speed * speed_scale_y
    
    all_colliders = walls + tables + [g.rect for g in guards] + [door.rect for door in doors]
    if game_state != "poker":
        update_boss_message(dt)

    if game_state == "world" and not escape_menu_active:
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * player_speed_x
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * player_speed_y
        player.move(dx, dy, all_colliders)
        clamp_player_to_current_room()
        player.update_animation(dt, min(current_scale_x, current_scale_y))
        for npc in npcs: 
            npc.update(all_colliders, speed_scale_x, speed_scale_y)

    if game_state == "poker" and poker_game is not None:
        # Update boss message timer
        update_boss_message(dt)

        # Update animations (movement)
        update_animations()

        if boss_thinking and not animating:
            if current_time - boss_think_start_time >= boss_think_duration:
                callAmount = poker_game.getCallAmount(poker_game.boss)
                if callAmount > poker_game.boss.chips:
                    boss_action = Action("fold")
                else:
                    boss_action = poker_game.boss.chooseAction(poker_game, poker_game.table, callAmount)

                boss_action.processAction(poker_game.boss, poker_game)
                poker_game.bossActed = True
                boss_name = BOSS_DIALOGUE[current_boss_difficulty]["name"]

                if boss_action.type == "fold":
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["fold"])
                    set_boss_message(f"{boss_name}: '{dialogue_option}'")
                    poker_game.handWinner = poker_game.human
                    poker_game.phase = "handCheck"
                    poker_game.phaseIndex = GAMEPHASE.index("handCheck")
                    poker_game.playerActed = False
                    poker_game.bossActed = False
                elif boss_action.type == "call":
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["call"])
                    set_boss_message(f"{boss_name}: '{dialogue_option}' (${callAmount})")
                elif boss_action.type == "raise":
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["raise"])
                    set_boss_message(f"{boss_name}: '{dialogue_option}' (Raise to ${poker_game.currentBet})")
                elif boss_action.type == "check":
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["check"])
                    set_boss_message(f"{boss_name}: '{dialogue_option}'")

                boss_thinking = False

        if not animating and not boss_thinking:
            if poker_game.phase != "handCheck" and poker_game.playerActed and poker_game.bossActed:
                poker_game.changePhase()
                poker_game.playerActed = False
                poker_game.bossActed = False

            if poker_game.phase == "flop":
                poker_game.dealCommunityCards()
                poker_game.changePhase()
                detect_and_animate_new_cards()
            elif poker_game.phase == "turn":
                poker_game.dealCommunityCards()
                poker_game.changePhase()
                detect_and_animate_new_cards()
            elif poker_game.phase == "river":
                poker_game.dealCommunityCards()
                poker_game.changePhase()
                detect_and_animate_new_cards()
            elif poker_game.phase == "handCheck" and not poker_game.showdownDone:
                # if player folded
                if poker_game.handWinner is not None:
                    poker_game.awardPot(poker_game.handWinner)
                    winner = poker_game.handWinner
                    rank = None
                # if player did not fold
                else:
                    winner, rank = poker_game.showDown()
                poker_game.showdownDone = True
                persistent_player.chips = poker_game.human.chips
                persistent_player.boss_chips[current_boss_difficulty] = poker_game.boss.chips
                last_hand_player_won = (winner == poker_game.human)
                show_hand_menu = True
                check_and_exit_poker_if_defeated()
                if game_state != "poker":
                    continue

    # DRAW
    if game_state == "main_menu":
        screen.fill((0, 0, 0))
        title = title_font.render("TEXAS HOLD'EM", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH/2, HEIGHT*0.2)))
        new_game_btn.draw(screen)
        continue_btn.draw(screen)
        quit_main_btn.draw(screen)
        draw_boss_message(screen)

    elif game_state == "story":
        screen.fill((0, 0, 0))
        page_lines = STORY_PAGES[current_story_page]
        y_offset = HEIGHT // 2 - (len(page_lines) * 30) // 2
        for line in page_lines:
            text = font.render(line, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 40
        prompt = "Press any key to begin" if current_story_page + 1 >= len(STORY_PAGES) else "Press any key to continue..."
        prompt_surf = font.render(prompt, True, LIGHT_GOLD)
        screen.blit(prompt_surf, (WIDTH//2 - prompt_surf.get_width()//2, HEIGHT*0.85))

    elif game_state == "world":
        draw_tiled_floor(screen, current_room)
        for wall in walls:
            wall_surface = get_world_prop_surface("brick_wall", wall)
            screen.blit(wall_surface, wall.topleft)
        for door in doors:
            draw_door_hint(screen, door)
        for prop_name, prop_rect in room_props:
            draw_world_prop(screen, prop_name, prop_rect)
        draw_depth_sorted_world_objects(screen)

        chips_text = font.render(f"Chips: ${persistent_player.chips}", True, WHITE)
        screen.blit(chips_text, (WIDTH - 180, 20))
        
        # Show interaction prompts
        if near_table():
            diff_str, _ = room_difficulty(current_room)
            if persistent_player.boss_chips[diff_str] <= 0:
                prompt_text = "The table is empty. The boss has left."
            else:
                actual_cost = min(ENTRY_COST[diff_str], persistent_player.boss_chips[diff_str])
                if diff_str == "easy":
                    prompt_text = f"Press E to Play Poker (Easy) - Buy-in ${actual_cost}"
                elif diff_str == "medium":
                    prompt_text = (
                        f"Press E to Play Poker (Medium) - Buy-in ${actual_cost}"
                        if persistent_player.has_buff("Lucky Draw")
                        else "The Sharp Lady is ignoring you."
                    )
                else:
                    prompt_text = (
                        f"Press E to Play Poker (Hard) - Buy-in ${actual_cost}"
                        if persistent_player.has_buff("High Roller")
                        else "The Enforcer refuses to play you."
                    )
            prompt = font.render(prompt_text, True, WHITE)
            screen.blit(prompt, prompt.get_rect(center=(WIDTH/2, HEIGHT*0.9)))
        else:
            door = near_any_door()
            if door:
                if door.target_room == 2 and not persistent_player.has_buff("High Roller"):
                    prompt_text = "Door locked! Face the Sharp Lady first."
                elif door.target_room == 1 and not persistent_player.has_buff("Lucky Draw"):
                    prompt_text = "Door locked! The Old Guard blockades your path."
                else:
                    prompt_text = "Press E to go through door"
                prompt = font.render(prompt_text, True, WHITE)
                screen.blit(prompt, prompt.get_rect(center=(WIDTH/2, HEIGHT*0.9)))

        draw_boss_message(screen)

        if escape_menu_active:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill(MENU_BG)
            screen.blit(overlay, (0, 0))
            menu_title = font.render("MENU", True, GOLD)
            screen.blit(menu_title, (WIDTH//2 - menu_title.get_width()//2, HEIGHT*0.2))
            volume_slider_btn.draw(screen)
            abandon_btn.draw(screen)
            save_exit_btn.draw(screen)
            resume_btn.draw(screen)
    
    elif game_state == "poker":
        draw_poker_background(screen, current_room)
        pot_txt = font.render(f"Pot: ${poker_game.table.pot}", True, WHITE); screen.blit(pot_txt, pot_txt.get_rect(center=(WIDTH/2, HEIGHT/10)))

        card_w = int(BASE_CARD_W * current_scale_x)
        card_h = int(BASE_CARD_H * current_scale_y)
        
        draw_deck(screen)

        # --- DEALER HAND ---
        dealer_x = 60
        dealer_y = HEIGHT * 0.12
        boss_name = BOSS_DIALOGUE[current_boss_difficulty]["name"]
        dealer_label = font.render(f"{boss_name} Chips: ${poker_game.boss.chips}", True, GOLD)
        screen.blit(dealer_label, (dealer_x, dealer_y - 30))

        # --- Update Button Text ----
        if not animating and not boss_thinking and not show_hand_menu:
            callAmount = poker_game.getCallAmount(poker_game.currentPlayer)

            if callAmount <= 0:
                checkCall_btn.text = "Check"
            else:
                checkCall_btn.text = f"Call (${callAmount})"

            raise_btn.text = "Raise (50$)"
        
        # Draw dealer cards (skip animating ones)
        for i, card in enumerate(poker_game.boss.hand):
            if ('boss', i) in animating_card_keys:
                continue
            if poker_game.phase == "handCheck":
                try:
                    img = load_image_asset("ui", f"{card.rank}_of_{card.suit}.png", size=(card_w, card_h))
                    screen.blit(img, (dealer_x + i*(card_w + 5), dealer_y))
                except: 
                    pygame.draw.rect(screen, WHITE, (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), border_radius=5)
            else:
                # card backs
                pygame.draw.rect(screen, (150, 0, 0), (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), border_radius=5)
                pygame.draw.rect(screen, GOLD, (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), 2, border_radius=5)

        # Community Cards (skip animating ones)
        total_community = len(poker_game.table.communityCards)
        x_comm = WIDTH/2 - (total_community * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.table.communityCards):
            if ('community', i) in animating_card_keys:
                continue
            try:
                img = load_image_asset("ui", f"{card.rank}_of_{card.suit}.png", size=(card_w, card_h))
                screen.blit(img, (x_comm + i*(card_w + 10), HEIGHT/2 - card_h/2))
            except: 
                pygame.draw.rect(screen, WHITE, (x_comm + i*(card_w+10), HEIGHT/2 - card_h/2, card_w, card_h))

        # Human Player Hand (skip animating ones)
        x_hand = WIDTH/2 - (2 * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.human.hand):
            if ('human', i) in animating_card_keys:
                continue
            try:
                img = load_image_asset("ui", f"{card.rank}_of_{card.suit}.png", size=(card_w, card_h))
                screen.blit(img, (x_hand + i*(card_w + 10), HEIGHT*0.65))
            except: 
                pygame.draw.rect(screen, WHITE, (x_hand + i*(card_w+10), HEIGHT*0.65, card_w, card_h))

        # Draw flying animations
        for anim in active_animations:
            anim.draw(screen)

        # Draw boss action message
        draw_boss_message(screen)
        chips_text = font.render(f"Your Chips: ${poker_game.human.chips}", True, WHITE)
        screen.blit(chips_text, (20, HEIGHT - 40))

        if show_hand_menu and not animating:
            if persistent_player.boss_chips[current_boss_difficulty] > 0:
                play_again_btn.draw(screen)
            leave_table_btn.draw(screen)
            result_text = "You won the hand!" if last_hand_player_won else "You lost the hand."
            text_surf = font.render(result_text, True, GOLD)
            screen.blit(text_surf, text_surf.get_rect(center=(WIDTH/2, HEIGHT*0.75)))
        elif poker_game.phase != "handCheck" and not animating and not boss_thinking:
            for btn in [checkCall_btn, raise_btn, fold_btn, leave_btn]:
                btn.draw(screen)
        elif boss_thinking:
            thinking_text = font.render("Boss is thinking...", True, LIGHT_GOLD)
            screen.blit(thinking_text, thinking_text.get_rect(center=(WIDTH/2, HEIGHT * 0.95)))
                
        if animating:
            dealing_txt = font.render("Dealing cards...", True, LIGHT_GOLD)
            screen.blit(dealing_txt, dealing_txt.get_rect(center=(WIDTH/2, HEIGHT * 0.95)))

    elif game_state == "game_over":
        screen.fill((0, 0, 0))
        y_offset = HEIGHT // 2 - 100
        for line in GAME_OVER_TEXT:
            text = font.render(line, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 40
        prompt = "Press ESC to return to main menu"
        prompt_surf = font.render(prompt, True, LIGHT_GOLD)
        screen.blit(prompt_surf, (WIDTH//2 - prompt_surf.get_width()//2, HEIGHT*0.8))

    elif game_state == "ending":
        screen.fill((0, 0, 0))
        y_offset = HEIGHT // 2 - 120
        for line in ENDING_TEXT:
            text = font.render(line, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 40

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
