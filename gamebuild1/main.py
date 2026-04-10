import os
import random
import sys
from dataclasses import dataclass, field

import pygame


WIDTH, HEIGHT = 960, 720
TILE_SIZE = 64
WORLD_COLS = 15
WORLD_ROWS = 11
PLAYER_SIZE = 34
PLAYER_SPRITE_BOX = (58, 84)
NPC_SPRITE_BOX = (60, 88)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ASSET_FILENAMES = {
    "player": "player.jpeg",
    "gambler": "gambler.jpeg",
    "dealer": "dealer.jpeg",
    "boss": "Boss.jpeg",
    "tiles": "tiles.png",
}
DOOR_ASSET_FILENAMES = {
    "door_blue": "door_blue.png",
    "door_service": "door_service.png",
    "stairs_gold": "stairs_gold.png",
}
EXTRA_ASSET_FILENAMES = {
    "wood_floor_warm": "wood_floor_warm.png",
    "wood_floor_dark": "wood_floor_dark.png",
    "lounge_bar_full": "lounge_bar_full.png",
    "alley_floor": "alley_floor.png",
    "vault_floor": "vault_floor.png",
    "office_floor": "office_floor.png",
}
CARD_UI_DIRS = [
    "/Users/alexmatovski/Downloads/CSI-2999-Sophomore-Project-test-engine-1/ui",
    os.path.join(SCRIPT_DIR, "ui"),
    os.path.join(SCRIPT_DIR, "Assets", "ui"),
]
FALLBACK_ASSET_DIRS = [
    os.environ.get("POKER_ROGUELIKE_ASSET_DIR"),
    os.path.join(SCRIPT_DIR, "Assets"),
    os.path.join(SCRIPT_DIR, "assets"),
    "/Users/alexmatovski/PyCharmMiscProject/Gametest2/Assets",
]

SCENE_MENU = 0
SCENE_INTRO = 1
SCENE_WORLD = 2
SCENE_COMBAT = 3
SCENE_GAME_OVER = 4

TILE_FLOOR = 0
TILE_WALL = 1
TILE_EXIT = 2

PROP_SLOT = "slot"
PROP_RUG = "rug"
PROP_TABLE = "table"
PROP_CRATES = "crates"
PROP_BAR = "bar"
PROP_WALL = "wall"
PROP_LOUNGE_BAR = "lounge_bar"

PROP_LAYOUTS = {
    PROP_SLOT: {"size": (96, 140), "anchor": "floor"},
    PROP_RUG: {"size": (150, 110), "anchor": "center"},
    PROP_TABLE: {"size": (150, 108), "anchor": "floor"},
    PROP_CRATES: {"size": (132, 120), "anchor": "floor"},
    PROP_BAR: {"size": (220, 132), "anchor": "floor"},
    PROP_LOUNGE_BAR: {"size": (256, 160), "anchor": "floor"},
    PROP_WALL: {"size": (64, 64), "anchor": "tile"},
}

CARD_SUITS = ["hearts", "diamonds", "spades", "clubs"]
CARD_RANK_NAMES = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "jack", 12: "queen", 13: "king", 14: "ace"}
BUFF_POOL = ["Lucky Draw", "High Roller", "Bluff Master", "Second Chance", "Chip Shield", "All-In Fury", "Intimidation"]


def resolve_asset_paths():
    for asset_dir in FALLBACK_ASSET_DIRS:
        if not asset_dir:
            continue
        asset_paths = {
            name: os.path.join(asset_dir, filename)
            for name, filename in DEFAULT_ASSET_FILENAMES.items()
        }
        if all(os.path.exists(path) for path in asset_paths.values()):
            return asset_dir, asset_paths

    asset_dir = next((path for path in FALLBACK_ASSET_DIRS if path), SCRIPT_DIR)
    return asset_dir, {
        name: os.path.join(asset_dir, filename)
        for name, filename in DEFAULT_ASSET_FILENAMES.items()
    }


def load_image(path):
    if not os.path.exists(path):
        return None
    try:
        return pygame.image.load(path)
    except pygame.error:
        return None


def crop_surface(surface, rect):
    out = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    out.blit(surface, (0, 0), rect)
    return out


def scale_to_fit(surface, width, height):
    if surface is None:
        return None
    source_w, source_h = surface.get_size()
    if source_w == 0 or source_h == 0:
        return surface
    ratio = min(width / source_w, height / source_h)
    size = (max(1, int(source_w * ratio)), max(1, int(source_h * ratio)))
    return pygame.transform.smoothscale(surface, size)


def card_asset_name(rank, suit):
    return f"{CARD_RANK_NAMES[rank]}_of_{suit}.png"


def generate_poker_hand(bonus=0):
    display_cards = []
    values = []
    for _ in range(5):
        rank = random.randint(2, 14)
        suit = random.choice(CARD_SUITS)
        display_cards.append((rank, suit))
        values.append(rank + bonus)
    return display_cards, values


def card_label(value):
    if value == 14:
        return "A"
    if value == 13:
        return "K"
    if value == 12:
        return "Q"
    if value == 11:
        return "J"
    return str(value)


def roll_hand(bonus=0):
    return [random.randint(2, 14) + bonus for _ in range(5)]


def classify_hand(cards):
    counts = {}
    for card in cards:
        counts[card] = counts.get(card, 0) + 1
    ordered = sorted(counts.values(), reverse=True)
    values = sorted(cards, reverse=True)
    unique = sorted(set(cards))
    straight = len(unique) == 5 and unique[-1] - unique[0] == 4

    if ordered[0] == 4:
        return 7, "Four of a Kind"
    if ordered[0] == 3 and ordered[1] == 2:
        return 6, "Full House"
    if straight:
        return 5, "Straight"
    if ordered[0] == 3:
        return 4, "Three of a Kind"
    if ordered[0] == 2 and ordered[1] == 2:
        return 3, "Two Pair"
    if ordered[0] == 2:
        return 2, "Pair"
    return 1, "High Card"


def compare_hands(player_cards, enemy_cards):
    player_rank, player_name = classify_hand(player_cards)
    enemy_rank, enemy_name = classify_hand(enemy_cards)
    if player_rank > enemy_rank:
        return 1, player_name, enemy_name
    if player_rank < enemy_rank:
        return -1, player_name, enemy_name

    player_sorted = sorted(player_cards, reverse=True)
    enemy_sorted = sorted(enemy_cards, reverse=True)
    if player_sorted > enemy_sorted:
        return 1, player_name, enemy_name
    if player_sorted < enemy_sorted:
        return -1, player_name, enemy_name
    return 0, player_name, enemy_name


class SpriteSheet:
    def __init__(self, path, target_size, columns=4, rows=4):
        self.path = path
        self.target_size = target_size
        self.columns = columns
        self.rows = rows
        self.frames = {"down": [], "right": [], "up": []}
        self.ready = False
        self._load()

    def _remove_background(self, surface, tolerance=26):
        surface = surface.convert_alpha()
        bg = surface.get_at((0, 0))
        width, height = surface.get_size()
        for y in range(height):
            for x in range(width):
                color = surface.get_at((x, y))
                if (
                    abs(color.r - bg.r) <= tolerance
                    and abs(color.g - bg.g) <= tolerance
                    and abs(color.b - bg.b) <= tolerance
                ):
                    surface.set_at((x, y), (0, 0, 0, 0))
        return surface

    def _prepare_frame(self, frame):
        frame = self._remove_background(frame)
        bounds = frame.get_bounding_rect()
        if bounds.width == 0 or bounds.height == 0:
            return {"surface": frame, "offset_x": 0, "offset_y": 0}

        trimmed = crop_surface(frame, (bounds.x, bounds.y, bounds.width, bounds.height))
        source_w, source_h = trimmed.get_size()
        target_w, target_h = self.target_size
        ratio = min(target_w / source_w, target_h / source_h)
        trimmed = pygame.transform.smoothscale(
            trimmed,
            (
                max(1, int(source_w * ratio)),
                max(1, int(source_h * ratio)),
            ),
        )

        return {
            "surface": trimmed,
            "offset_x": 0,
            "offset_y": 0,
        }

    def _load(self):
        image = load_image(self.path)
        if image is None:
            return
        image = image.convert()
        frame_w = image.get_width() // self.columns
        frame_h = image.get_height() // self.rows

        rows = []
        for row in range(self.rows):
            row_frames = []
            for col in range(self.columns):
                frame = crop_surface(image, (col * frame_w, row * frame_h, frame_w, frame_h))
                row_frames.append(self._prepare_frame(frame))
            rows.append(row_frames)

        self.frames["down"] = rows[0]
        self.frames["right"] = rows[1] if len(rows) > 1 else rows[0]
        self.frames["up"] = rows[2] if len(rows) > 2 else rows[0]
        self.ready = True

    def get_frame(self, direction, frame_index):
        if not self.ready:
            return None
        if direction == "left":
            source = self.frames["right"][frame_index % len(self.frames["right"])]
            return {
                "surface": pygame.transform.flip(source["surface"], True, False),
                "offset_x": source["offset_x"],
                "offset_y": source["offset_y"],
            }
        return self.frames.get(direction, self.frames["down"])[frame_index % 4]

    def portrait(self, size):
        frame = self.get_frame("down", 0)
        if frame is None:
            return None
        return scale_to_fit(frame["surface"], size, size)


class TileArt:
    def __init__(self, path):
        self.props = {}
        self.ready = False
        self._load(path)

    def _remove_background(self, surface, tolerance=10):
        surface = surface.convert_alpha()
        bg = surface.get_at((0, 0))
        width, height = surface.get_size()
        for y in range(height):
            for x in range(width):
                color = surface.get_at((x, y))
                if (
                    abs(color.r - bg.r) <= tolerance
                    and abs(color.g - bg.g) <= tolerance
                    and abs(color.b - bg.b) <= tolerance
                ):
                    surface.set_at((x, y), (0, 0, 0, 0))
        return surface

    def _trim(self, surface):
        rect = surface.get_bounding_rect()
        if rect.width == 0 or rect.height == 0:
            return surface
        return crop_surface(surface, rect)

    def _load(self, path):
        image = load_image(path)
        if image is None:
            return
        image = image.convert_alpha()
        section_w = image.get_width() // 6
        section_h = image.get_height()
        names = [PROP_WALL, PROP_SLOT, PROP_RUG, PROP_TABLE, PROP_CRATES, PROP_BAR]
        for idx, name in enumerate(names):
            section = crop_surface(image, (idx * section_w, 0, section_w, section_h))
            if name == PROP_WALL:
                self.props[name] = section
            else:
                section = self._remove_background(section)
                self.props[name] = self._trim(section)
        self.ready = True

    def get(self, name, width, height):
        return scale_to_fit(self.props.get(name), width, height)


class Assets:
    def __init__(self):
        self.asset_dir, self.paths = resolve_asset_paths()
        self.player_sheet = SpriteSheet(self.paths["player"], target_size=PLAYER_SPRITE_BOX)
        self.gambler_sheet = SpriteSheet(self.paths["gambler"], target_size=NPC_SPRITE_BOX)
        self.dealer_sheet = SpriteSheet(self.paths["dealer"], target_size=NPC_SPRITE_BOX)
        self.boss_sheet = SpriteSheet(self.paths["boss"], target_size=NPC_SPRITE_BOX)
        self.tile_art = TileArt(self.paths["tiles"])
        self.door_icons = self._load_door_icons()
        self.extra_art = self._load_extra_art()
        self.card_faces = self._load_card_faces()
        self.missing = [name for name, path in self.paths.items() if not os.path.exists(path)]

    def _asset_search_dirs(self):
        search_dirs = []
        override = os.environ.get("POKER_ROGUELIKE_ASSET_DIR")
        if override:
            search_dirs.append(override)
        search_dirs.extend(
            [
                os.path.join(SCRIPT_DIR, "Assets"),
                os.path.join(SCRIPT_DIR, "assets"),
                self.asset_dir,
            ]
        )
        return search_dirs

    def _load_door_icons(self):
        icons = {}
        search_dirs = self._asset_search_dirs()
        for key, filename in DOOR_ASSET_FILENAMES.items():
            for directory in search_dirs:
                path = os.path.join(directory, filename)
                if os.path.exists(path):
                    icons[key] = load_image(path)
                    break
        return icons

    def _load_extra_art(self):
        art = {}
        search_dirs = self._asset_search_dirs()
        for key, filename in EXTRA_ASSET_FILENAMES.items():
            for directory in search_dirs:
                path = os.path.join(directory, filename)
                if os.path.exists(path):
                    art[key] = load_image(path)
                    break
        return art

    def _load_card_faces(self):
        faces = {}
        for directory in CARD_UI_DIRS:
            if not os.path.isdir(directory):
                continue
            for rank in CARD_RANK_NAMES:
                for suit in CARD_SUITS:
                    path = os.path.join(directory, card_asset_name(rank, suit))
                    if os.path.exists(path):
                        image = load_image(path)
                        if image is not None:
                            faces[(rank, suit)] = image.convert_alpha()
            if faces:
                break
        return faces



class ScreenScaler:
    def __init__(self, window_size):
        self.window_width, self.window_height = window_size
        self.dest_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        self.update(window_size)

    def update(self, window_size):
        self.window_width, self.window_height = window_size
        scale = min(self.window_width / WIDTH, self.window_height / HEIGHT)
        render_width = max(1, int(WIDTH * scale))
        render_height = max(1, int(HEIGHT * scale))
        self.dest_rect = pygame.Rect(
            (self.window_width - render_width) // 2,
            (self.window_height - render_height) // 2,
            render_width,
            render_height,
        )

    def present(self, window, frame_surface):
        window.fill((8, 8, 10))
        scaled = pygame.transform.smoothscale(frame_surface, self.dest_rect.size)
        window.blit(scaled, self.dest_rect.topleft)


@dataclass
class DialogueWindow:
    title: str
    text: str
    visible: bool = True
    width: int = 600
    height: int = 220

    def draw(self, screen, title_font, body_font):
        if not self.visible:
            return
        rect = pygame.Rect(WIDTH // 2 - self.width // 2, HEIGHT - self.height - 24, self.width, self.height)
        pygame.draw.rect(screen, (24, 24, 30), rect, border_radius=12)
        pygame.draw.rect(screen, (225, 225, 225), rect, 2, border_radius=12)
        title = title_font.render(self.title, True, (255, 228, 150))
        screen.blit(title, (rect.x + 16, rect.y + 14))
        y = rect.y + 58
        for line in self.text.split("\n"):
            surf = body_font.render(line, True, (238, 238, 238))
            screen.blit(surf, (rect.x + 16, y))
            y += 28


@dataclass
class Combatant:
    name: str
    sprite_key: str
    max_hp: int
    hp: int
    attack: int
    defense: int
    gold_reward: int
    xp_reward: int
    poker_bonus: int = 0
    taunt: str = ""


@dataclass
class NPC:
    npc_id: str
    name: str
    sprite_key: str
    x: int
    y: int
    role: str
    dialogue: str
    facing: str = "down"
    combat: Combatant | None = None
    active: bool = True

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)


@dataclass
class Warp:
    x: int
    y: int
    target_area: str
    target_pos: tuple[int, int]
    label: str
    locked_by: str | None = None
    icon: str = "door_blue"

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)


@dataclass
class Area:
    area_id: str
    name: str
    palette: tuple[int, int, int]
    floor_style: str
    spawn: tuple[int, int]
    tiles: list[list[int]]
    props: list[tuple[str, int, int]] = field(default_factory=list)
    warps: list[Warp] = field(default_factory=list)
    npcs: list[NPC] = field(default_factory=list)
    flavor: str = ""


@dataclass
class PlayerState:
    max_hp: int = 36
    hp: int = 36
    attack: int = 6
    defense: int = 2
    poker_bonus: int = 0
    potions: int = 2
    gold: int = 18
    chips: int = 60
    xp: int = 0
    level: int = 1
    buffs: list[str] = field(default_factory=lambda: ["Lucky Draw"])
    second_chance_used: bool = False
    chest_opened: bool = False
    boss_defeated: bool = False

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def add_buff(self, buff_name):
        if buff_name not in self.buffs:
            self.buffs.append(buff_name)
            return True
        return False

    def reduce_poker_damage(self, amount):
        if "Chip Shield" in self.buffs:
            return max(1, int(amount * 0.7))
        return amount

    def gain_xp(self, amount):
        self.xp += amount
        threshold = self.level * 20
        while self.xp >= threshold:
            self.xp -= threshold
            self.level += 1
            self.max_hp += 6
            self.hp = self.max_hp
            self.attack += 2
            self.defense += 1
            threshold = self.level * 20


class Player:
    def __init__(self, sprite_sheet):
        self.sprite_sheet = sprite_sheet
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.speed = 4
        self.direction = "down"
        self.anim_timer = 0
        self.anim_frame = 0
        self.is_moving = False

    def place(self, x, y):
        self.rect.topleft = (x, y)

    def move(self, keys, area, blockers):
        dx = 0
        dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed

        if dx < 0:
            self.direction = "left"
        elif dx > 0:
            self.direction = "right"
        elif dy < 0:
            self.direction = "up"
        elif dy > 0:
            self.direction = "down"

        self._move_axis(dx, 0, area, blockers)
        self._move_axis(0, dy, area, blockers)
        self._update_anim(dx, dy)

    def _update_anim(self, dx, dy):
        if dx == 0 and dy == 0:
            self.anim_frame = 0
            self.anim_timer = 0
            self.is_moving = False
            return
        self.is_moving = True
        self.anim_timer += 1
        if self.anim_timer >= 10:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4

    def _move_axis(self, dx, dy, area, blockers):
        if dx == 0 and dy == 0:
            return
        self.rect.x += dx
        self.rect.y += dy

        for tile_y in range(self.rect.top // TILE_SIZE, self.rect.bottom // TILE_SIZE + 1):
            for tile_x in range(self.rect.left // TILE_SIZE, self.rect.right // TILE_SIZE + 1):
                if tile_x < 0 or tile_y < 0 or tile_x >= WORLD_COLS or tile_y >= WORLD_ROWS:
                    self._snap_back(dx, dy)
                    return
                if area.tiles[tile_y][tile_x] == TILE_WALL:
                    self._resolve_wall(tile_x, tile_y, dx, dy)

        for blocker in blockers:
            if self.rect.colliderect(blocker):
                self._snap_back(dx, dy)
                return

    def _resolve_wall(self, tile_x, tile_y, dx, dy):
        wall_rect = pygame.Rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        if self.rect.colliderect(wall_rect):
            if dx > 0:
                self.rect.right = wall_rect.left
            elif dx < 0:
                self.rect.left = wall_rect.right
            elif dy > 0:
                self.rect.bottom = wall_rect.top
            elif dy < 0:
                self.rect.top = wall_rect.bottom

    def _snap_back(self, dx, dy):
        self.rect.x -= dx
        self.rect.y -= dy

    def draw(self, screen, cam_x, cam_y):
        center_x = self.rect.centerx - cam_x
        feet_y = self.rect.bottom - cam_y

        shadow_width = 20 if self.is_moving else 16
        shadow_rect = pygame.Rect(0, 0, shadow_width, 8)
        shadow_rect.center = (center_x, feet_y - 2)
        pygame.draw.ellipse(screen, (0, 0, 0, 110), shadow_rect)

        ring_color = (90, 200, 255) if self.is_moving else (255, 215, 110)
        pygame.draw.ellipse(
            screen,
            ring_color,
            (center_x - 14, feet_y - 8, 28, 10),
            2,
        )

        sprite = self.sprite_sheet.get_frame(self.direction, self.anim_frame) if self.sprite_sheet else None
        if sprite:
            surface = sprite["surface"]
            bob = -2 if self.is_moving and self.anim_frame % 2 == 1 else 0
            screen.blit(
                surface,
                (
                    center_x - surface.get_width() // 2,
                    feet_y - surface.get_height() + bob,
                ),
            )
            return
        pygame.draw.rect(screen, (255, 210, 90), (self.rect.x - cam_x, self.rect.y - cam_y, PLAYER_SIZE, PLAYER_SIZE))


class Menu:
    def __init__(self, game):
        self.game = game
        self.options = ["Start Story", "Quit"]
        self.selected = 0
        self.font = pygame.font.SysFont(None, 52)
        self.small = pygame.font.SysFont(None, 28)

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % len(self.options)
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % len(self.options)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.selected == 0:
                self.game.start_new_game()
            else:
                pygame.quit()
                sys.exit()

    def draw(self, screen):
        screen.fill((12, 14, 18))
        title = self.font.render("Casino District RPG", True, (255, 235, 170))
        subtitle = self.small.render("Explore rooms, talk to NPCs, complete the job, beat the boss.", True, (220, 220, 220))
        asset_line = self.small.render(f"Assets: {self.game.assets.asset_dir}", True, (165, 165, 165))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 220))
        screen.blit(asset_line, (WIDTH // 2 - asset_line.get_width() // 2, 255))
        if self.game.assets.missing:
            warning = self.small.render("Missing some assets, so fallback placeholders may appear.", True, (220, 155, 120))
            screen.blit(warning, (WIDTH // 2 - warning.get_width() // 2, 286))
        for idx, option in enumerate(self.options):
            color = (255, 215, 90) if idx == self.selected else (215, 215, 215)
            surf = self.font.render(option, True, color)
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 360 + idx * 74))


class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH, HEIGHT)).convert()
        pygame.display.set_caption("Casino District RPG")
        self.clock = pygame.time.Clock()
        self.scaler = ScreenScaler((WIDTH, HEIGHT))
        self.assets = Assets()
        self.font = pygame.font.SysFont(None, 26)
        self.small_font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 34)
        self.title_font = pygame.font.SysFont(None, 42)
        self.menu = Menu(self)

        self.scene = SCENE_MENU
        self.player = Player(self.assets.player_sheet)
        self.player_state = PlayerState()
        self.areas = {}
        self.current_area = None
        self.dialogue = None
        self.pending_levelup = False
        self.combat_enemy = None
        self.combat_log = []
        self.game_over_reason = ""
        self.last_player_cards = []
        self.last_enemy_cards = []
        self.last_poker_labels = None
        self.last_enemy_reaction = ""
        self.current_enemy_profile = "medium"
        self.poker_round = None
        self.intro_pages = [
            ["The city stays awake", "long after its luck runs out."],
            ["Tonight, the Casino District", "feels quieter than it should."],
            ["Doors are open.", "Tables are live.", "Everybody wants something."],
            ["Walk in.", "Talk when you want.", "See what the night gives back."],
        ]
        self.intro_index = 0

    def handle_resize(self, size):
        width = max(640, size[0])
        height = max(480, size[1])
        self.window = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.scaler.update((width, height))

    def advance_intro(self):
        self.intro_index += 1
        if self.intro_index >= len(self.intro_pages):
            self.scene = SCENE_WORLD
            self.intro_index = 0

    def draw_intro(self):
        self.screen.fill((0, 0, 0))
        lines = self.intro_pages[self.intro_index]
        total_height = len(lines) * 52
        start_y = HEIGHT // 2 - total_height // 2
        for index, line in enumerate(lines):
            surf = self.title_font.render(line, True, (245, 245, 245))
            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, start_y + index * 52))

        prompt = self.small_font.render("Press Enter, Space, or click to continue", True, (200, 200, 200))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 90))

    def start_new_game(self):
        self.player_state = PlayerState()
        self.areas = self.build_areas()
        self.current_area = "lounge"
        self.player.place(*self.areas[self.current_area].spawn)
        self.scene = SCENE_INTRO
        self.poker_round = None
        self.dialogue = None
        self.intro_index = 0

    def build_areas(self):
        def empty_tiles():
            tiles = [[TILE_FLOOR for _ in range(WORLD_COLS)] for _ in range(WORLD_ROWS)]
            for y in range(WORLD_ROWS):
                for x in range(WORLD_COLS):
                    if x in (0, WORLD_COLS - 1) or y in (0, WORLD_ROWS - 1):
                        tiles[y][x] = TILE_WALL
            return tiles

        lounge_tiles = empty_tiles()
        alley_tiles = empty_tiles()
        vault_tiles = empty_tiles()
        office_tiles = empty_tiles()

        for x in range(4, 11):
            office_tiles[4][x] = TILE_WALL

        lounge = Area(
            area_id="lounge",
            name="Velvet Lounge",
            palette=(72, 56, 40),
            floor_style="warm",
            spawn=(TILE_SIZE * 2, TILE_SIZE * 7),
            tiles=lounge_tiles,
            flavor="The front room hums with chips, gossip, and bad decisions.",
        )
        lounge.props = [
            (PROP_LOUNGE_BAR, TILE_SIZE * 9, TILE_SIZE * 2),
            (PROP_SLOT, TILE_SIZE * 2, TILE_SIZE * 2),
            (PROP_SLOT, TILE_SIZE * 2, TILE_SIZE * 5),
            (PROP_TABLE, TILE_SIZE * 6, TILE_SIZE * 4),
            (PROP_TABLE, TILE_SIZE * 8, TILE_SIZE * 6),
        ]
        lounge.npcs = [
            NPC("dealer", "Mara the Dealer", "dealer", TILE_SIZE * 6, TILE_SIZE * 3, "hint", "House rule: if a door opens, take it. If a shark smiles, don't sit down."),
            NPC("bartender", "Silas the Bartender", "dealer", TILE_SIZE * 11, TILE_SIZE * 3, "shop", "Need a top-up? I sell potions and grit."),
        ]
        lounge.warps = [
            Warp(TILE_SIZE * 13, TILE_SIZE * 5, "alley", (TILE_SIZE * 2, TILE_SIZE * 5), "To Back Alley", icon="door_blue"),
            Warp(TILE_SIZE * 7, TILE_SIZE * 1, "office", (TILE_SIZE * 7, TILE_SIZE * 8), "Stairs Up", icon="stairs_gold"),
        ]

        alley = Area(
            area_id="alley",
            name="Back Alley",
            palette=(50, 58, 66),
            floor_style="cold",
            spawn=(TILE_SIZE * 2, TILE_SIZE * 5),
            tiles=alley_tiles,
            flavor="Rainwater, stacked crates, and people who would rather not be remembered.",
        )
        alley.props = [
            (PROP_CRATES, TILE_SIZE * 9, TILE_SIZE * 3),
            (PROP_CRATES, TILE_SIZE * 10, TILE_SIZE * 6),
            (PROP_CRATES, TILE_SIZE * 3, TILE_SIZE * 7),
            (PROP_SLOT, TILE_SIZE * 3, TILE_SIZE * 2),
            (PROP_TABLE, TILE_SIZE * 7, TILE_SIZE * 5),
        ]
        alley.npcs = [
            NPC(
                "gambler",
                "Rook the Gambler",
                "gambler",
                TILE_SIZE * 7,
                TILE_SIZE * 4,
                "enemy",
                "You here for the ledger? Win it from me.",
                combat=Combatant("Rook the Gambler", "gambler", 24, 24, 6, 1, 16, 12, 1, "Let's see if your luck is real."),
            ),
            NPC("lookout", "Lookout", "gambler", TILE_SIZE * 10, TILE_SIZE * 6, "hint", "The upstairs office stays locked until the lounge clears your name."),
        ]
        alley.warps = [
            Warp(TILE_SIZE * 1, TILE_SIZE * 5, "lounge", (TILE_SIZE * 12, TILE_SIZE * 5), "Back To Lounge", icon="door_blue"),
            Warp(TILE_SIZE * 13, TILE_SIZE * 5, "vault", (TILE_SIZE * 2, TILE_SIZE * 5), "Service Door", icon="door_service"),
        ]

        vault = Area(
            area_id="vault",
            name="Cash Room",
            palette=(56, 72, 60),
            floor_style="vault",
            spawn=(TILE_SIZE * 2, TILE_SIZE * 5),
            tiles=vault_tiles,
            flavor="A quiet service room full of ledgers, keys, and the smell of old bills.",
        )
        vault.props = [
            (PROP_CRATES, TILE_SIZE * 4, TILE_SIZE * 3),
            (PROP_CRATES, TILE_SIZE * 6, TILE_SIZE * 5),
            (PROP_CRATES, TILE_SIZE * 10, TILE_SIZE * 4),
            (PROP_BAR, TILE_SIZE * 9, TILE_SIZE * 2),
            (PROP_TABLE, TILE_SIZE * 8, TILE_SIZE * 6),
            (PROP_CRATES, TILE_SIZE * 2, TILE_SIZE * 2),
        ]
        vault.npcs = [
            NPC("safekeeper", "Old Cashier", "dealer", TILE_SIZE * 10, TILE_SIZE * 5, "treasure", "If you made it in here, maybe you earned something."),
        ]
        vault.warps = [
            Warp(TILE_SIZE * 1, TILE_SIZE * 5, "alley", (TILE_SIZE * 12, TILE_SIZE * 5), "Back To Alley", icon="door_service"),
        ]

        office = Area(
            area_id="office",
            name="High Roller Office",
            palette=(78, 44, 44),
            floor_style="boss",
            spawn=(TILE_SIZE * 7, TILE_SIZE * 8),
            tiles=office_tiles,
            flavor="This room was built for people who think rules are decorative.",
        )
        office.props = [
            (PROP_BAR, TILE_SIZE * 5, TILE_SIZE * 2),
            (PROP_TABLE, TILE_SIZE * 7, TILE_SIZE * 6),
            (PROP_CRATES, TILE_SIZE * 11, TILE_SIZE * 2),
            (PROP_SLOT, TILE_SIZE * 2, TILE_SIZE * 2),
            (PROP_CRATES, TILE_SIZE * 10, TILE_SIZE * 7),
        ]
        office.npcs = [
            NPC(
                "boss",
                "Mr. Vale",
                "boss",
                TILE_SIZE * 7,
                TILE_SIZE * 3,
                "boss",
                "So you climbed the whole ladder. Let's see if you belong here.",
                combat=Combatant("Mr. Vale", "boss", 38, 38, 9, 3, 40, 28, 2, "The house always wins. Unless you don't."),
            )
        ]
        office.warps = [
            Warp(TILE_SIZE * 7, TILE_SIZE * 9, "lounge", (TILE_SIZE * 7, TILE_SIZE * 2), "Downstairs", icon="stairs_gold"),
        ]
        return {
            "lounge": lounge,
            "alley": alley,
            "vault": vault,
            "office": office,
        }

    def active_area(self):
        return self.areas[self.current_area]

    def blocker_rects(self):
        blockers = []
        for npc in self.active_area().npcs:
            if npc.active:
                blockers.append(npc.rect)
        return blockers

    def nearest_interaction(self):
        interaction_rect = self.player.rect.inflate(40, 40)
        area = self.active_area()
        for npc in area.npcs:
            if npc.active and interaction_rect.colliderect(npc.rect):
                return ("npc", npc)
        for warp in area.warps:
            if interaction_rect.colliderect(warp.rect):
                return ("warp", warp)
        return None

    def interact(self):
        found = self.nearest_interaction()
        if not found:
            self.dialogue = DialogueWindow("Quiet", "Nobody answers. Try talking to someone closer.")
            return

        kind, obj = found
        if kind == "warp":
            self.use_warp(obj)
            return

        if obj.role == "shop":
            self.open_shop()
        elif obj.role == "enemy":
            self.start_combat(obj)
        elif obj.role == "boss":
            self.start_combat(obj)
        elif obj.role == "treasure":
            self.open_treasure(obj)
        else:
            self.dialogue = DialogueWindow(obj.name, obj.dialogue)

    def open_shop(self):
        self.dialogue = DialogueWindow(
            "Bartender",
            f"Gold: {self.player_state.gold}\n1 Heal 10 HP for 8 gold\n2 Buy potion for 10 gold\n3 Improve poker bonus for 14 gold",
        )

    def handle_shop_buy(self, key):
        if not self.dialogue or self.dialogue.title != "Bartender":
            return
        if key == pygame.K_1 and self.player_state.gold >= 8:
            self.player_state.gold -= 8
            self.player_state.heal(10)
            self.dialogue = DialogueWindow("Bartender", "You look less like a cautionary tale now.")
        elif key == pygame.K_2 and self.player_state.gold >= 10:
            self.player_state.gold -= 10
            self.player_state.potions += 1
            self.dialogue = DialogueWindow("Bartender", "One fresh potion. Try not to waste it.")
        elif key == pygame.K_3 and self.player_state.gold >= 14:
            self.player_state.gold -= 14
            self.player_state.poker_bonus += 1
            self.dialogue = DialogueWindow("Bartender", "Your poker face just got expensive.")
        else:
            self.dialogue = DialogueWindow("Bartender", "Come back with enough gold.")

    def open_treasure(self, npc):
        if self.player_state.chest_opened:
            self.dialogue = DialogueWindow(npc.name, "The room is picked clean.")
            return
        self.player_state.chest_opened = True
        self.player_state.gold += 25
        self.player_state.potions += 1
        self.player_state.attack += 1
        self.dialogue = DialogueWindow(
            npc.name,
            "Inside the lockbox: 25 gold, a potion, and a weighted chip.\nYour attack increases by 1.",
        )

    def use_warp(self, warp):
        self.current_area = warp.target_area
        self.player.place(*warp.target_pos)
        self.dialogue = None

    def warp_is_locked(self, warp):
        return False

    def enemy_poker_reaction(self, hand_strength, pot_odds, player_aggressive):
        if self.current_enemy_profile == "easy":
            if hand_strength > 0.7:
                return "raise", "Rookie Gambler: big grin, bigger bet."
            if hand_strength > 0.4:
                return random.choice(["call", "fold"]), "Rookie Gambler: playing it safe."
            return "fold", "Rookie Gambler: terrible hand. Folding."
        if self.current_enemy_profile == "hard":
            if hand_strength > 0.8:
                return "raise", "Casino Boss: 'This round is mine. I raise.'"
            if player_aggressive and hand_strength > 0.6:
                return "raise", "Casino Boss: 'I see through your aggression.'"
            if hand_strength > pot_odds:
                return "call", "Casino Boss: 'I call.'"
            if random.random() < 0.15:
                return "raise", "Casino Boss bluffs with total confidence."
            return "fold", "Casino Boss: 'Know when to walk away.'"
        if hand_strength > 0.75:
            return "raise", "Card Shark: 'I like my odds. I raise.'"
        if hand_strength > pot_odds:
            return "call", "Card Shark: 'The numbers favor me. I call.'"
        return "fold", "Card Shark backs off the hand."

    def apply_player_buffs_to_poker(self, player_bonus, enemy_bonus):
        notes = []
        resistance = {"easy": 1.0, "medium": 0.75, "hard": 0.5}[self.current_enemy_profile]
        for buff in self.player_state.buffs:
            if buff == "Lucky Draw":
                player_bonus += 1
                notes.append("Lucky Draw adds +1.")
            elif buff == "High Roller":
                player_bonus += 1
                notes.append("High Roller steadies your hand.")
            elif buff == "Bluff Master" and random.random() < 0.25 * resistance:
                player_bonus += 2
                notes.append("Bluff Master lands.")
            elif buff == "Intimidation":
                enemy_bonus = max(0, enemy_bonus - max(1, round(resistance)))
                notes.append("Intimidation rattles the enemy.")
        return player_bonus, enemy_bonus, notes

    def maybe_award_buff(self):
        available = [buff for buff in BUFF_POOL if buff not in self.player_state.buffs]
        if available and random.random() < 0.45:
            buff = random.choice(available)
            self.player_state.add_buff(buff)
            return buff
        return None

    def start_combat(self, npc):
        if npc.combat is None:
            return
        enemy = npc.combat
        self.combat_enemy = Combatant(
            enemy.name,
            enemy.sprite_key,
            enemy.max_hp,
            enemy.max_hp,
            enemy.attack,
            enemy.defense,
            enemy.gold_reward,
            enemy.xp_reward,
            enemy.poker_bonus,
            enemy.taunt,
        )
        self.current_enemy_profile = "hard" if npc.npc_id == "boss" else "easy" if npc.npc_id == "gambler" else "medium"
        self.last_player_cards = []
        self.last_enemy_cards = []
        self.last_poker_labels = None
        self.last_enemy_reaction = ""
        self.player_state.second_chance_used = False
        self.poker_round = None
        self.combat_log = [
            f"{npc.name}: {npc.combat.taunt}",
            "1 Attack  2 Poker Skill  3 Potion",
        ]
        self.scene = SCENE_COMBAT

    def begin_poker_round(self):
        if self.combat_enemy is None:
            return
        if self.poker_round:
            self.combat_log = [
                "The hand is already live.",
                "Play it out with 4, 5, or 6.",
            ]
            return
        if self.player_state.chips < 2:
            self.combat_log = ["You are out of chips.", "Win with attacks or earn more before gambling."]
            return

        player_bonus, enemy_bonus, buff_notes = self.apply_player_buffs_to_poker(
            self.player_state.poker_bonus,
            self.combat_enemy.poker_bonus,
        )
        player_cards, player_values = generate_poker_hand(player_bonus)
        enemy_cards, enemy_values = generate_poker_hand(enemy_bonus)
        enemy_strength = classify_hand(enemy_values)[0] / 8
        enemy_action, enemy_quote = self.enemy_poker_reaction(
            enemy_strength,
            max(0.2, self.combat_enemy.hp / max(1, self.combat_enemy.max_hp)),
            player_bonus > self.player_state.poker_bonus,
        )
        enemy_stack = max(12, 18 + self.combat_enemy.gold_reward)
        ante = min(2, self.player_state.chips, enemy_stack)
        self.player_state.chips -= ante
        enemy_stack -= ante
        self.last_player_cards = player_cards
        self.last_enemy_cards = enemy_cards
        self.last_poker_labels = ("Your hand", "Dealer hand")
        self.last_enemy_reaction = enemy_quote
        self.poker_round = {
            "player_cards": player_cards,
            "player_values": player_values,
            "enemy_cards": enemy_cards,
            "enemy_values": enemy_values,
            "enemy_action": enemy_action,
            "enemy_quote": enemy_quote,
            "buff_notes": buff_notes,
            "pot": ante * 2,
            "ante": ante,
            "player_commit": ante,
            "enemy_commit": ante,
            "enemy_stack": enemy_stack,
            "stage": "player_open",
            "to_call": 0,
        }
        self.combat_log = [
            f"Antes are in. Pot: {ante * 2} chips.",
            enemy_quote,
            "Choose 4 to bet, 5 to check, or 6 to fold.",
        ] + buff_notes[:1]

    def resolve_poker_round(self, choice):
        if self.combat_enemy is None:
            return
        if not self.poker_round:
            self.combat_log = ["No poker hand is active.", "Press 2 to deal a new hand."]
            return

        round_state = self.poker_round
        player_cards = round_state["player_cards"]
        player_values = round_state["player_values"]
        enemy_cards = round_state["enemy_cards"]
        enemy_values = round_state["enemy_values"]
        enemy_action = round_state["enemy_action"]
        enemy_quote = round_state["enemy_quote"]
        buff_notes = list(round_state["buff_notes"])
        pot = round_state["pot"]
        enemy_stack = round_state["enemy_stack"]
        stage = round_state["stage"]

        def award_player_pot():
            self.player_state.chips += pot

        def showdown(extra_damage=0):
            nonlocal pot
            outcome, player_name, enemy_name = compare_hands(player_values, enemy_values)
            self.last_player_cards = player_cards
            self.last_enemy_cards = enemy_cards
            self.last_poker_labels = (player_name, enemy_name)
            if outcome < 0 and "Second Chance" in self.player_state.buffs and not self.player_state.second_chance_used:
                self.player_state.second_chance_used = True
                reroll_bonus = self.player_state.poker_bonus + (1 if "Lucky Draw" in self.player_state.buffs else 0)
                new_cards, new_values = generate_poker_hand(reroll_bonus + 1)
                player_cards[:] = new_cards
                player_values[:] = new_values
                outcome2, player_name2, enemy_name2 = compare_hands(player_values, enemy_values)
                self.last_player_cards = player_cards
                self.last_poker_labels = (player_name2, enemy_name2)
                self.last_enemy_reaction = f"{enemy_quote} Second Chance flips one more card your way."
                buff_notes.append("Second Chance rerolls your hand.")
                outcome, player_name, enemy_name = outcome2, player_name2, enemy_name2
            else:
                self.last_enemy_reaction = enemy_quote

            damage_base = max(2, pot // 2) + extra_damage
            if outcome > 0:
                award_player_pot()
                damage = damage_base
                if "All-In Fury" in self.player_state.buffs and self.player_state.hp <= self.player_state.max_hp // 2:
                    damage += 2
                    buff_notes.append("All-In Fury adds extra damage.")
                self.combat_enemy.hp -= damage
                self.combat_log = [
                    f"You show {player_name} against {enemy_name}.",
                    enemy_quote,
                    f"You drag a {pot}-chip pot and deal {damage} damage.",
                ] + buff_notes[:2]
            elif outcome < 0:
                damage = self.player_state.reduce_poker_damage(max(2, damage_base - 1))
                self.player_state.damage(damage)
                self.combat_log = [
                    f"Their {enemy_name} beats your {player_name}.",
                    enemy_quote,
                    f"You lose the {pot}-chip pot and take {damage} damage.",
                ] + buff_notes[:2]
            else:
                split = pot // 2
                self.player_state.chips += split
                self.combat_log = [
                    f"Both sides show {player_name}.",
                    f"Split pot. You recover {split} chips.",
                ] + buff_notes[:2]

        if choice == "fold":
            damage = self.player_state.reduce_poker_damage(max(2, pot // 3))
            self.player_state.damage(damage)
            self.last_player_cards = player_cards
            self.last_enemy_cards = enemy_cards
            self.last_poker_labels = ("Folded hand", "Dealer hand")
            self.last_enemy_reaction = f"{enemy_quote} You fold before the reveal."
            self.combat_log = [
                f"You surrender a {pot}-chip pot.",
                f"You lose tempo and take {damage} damage.",
            ]
            self.poker_round = None
            if self.player_state.hp <= 0:
                self.finish_combat_defeat()
            return

        if stage == "player_open":
            if choice == "raise":
                bet = min(self.player_state.chips, max(4, 4 + self.player_state.level + self.player_state.poker_bonus))
                if bet <= 0:
                    self.combat_log = ["No chips left to bet.", "Try a different action."]
                    return
                self.player_state.chips -= bet
                pot += bet
                round_state["player_commit"] += bet
                if enemy_action == "fold":
                    award_player_pot()
                    damage = max(3, pot // 3)
                    self.combat_enemy.hp -= damage
                    self.last_enemy_reaction = f"{enemy_quote} The pressure gets to them and they fold."
                    self.combat_log = [
                        f"You fire {bet} chips into the pot and force a fold.",
                        f"You pocket the {pot}-chip pot and deal {damage} damage.",
                    ] + buff_notes[:2]
                    self.poker_round = None
                    return
                enemy_match = min(enemy_stack, bet)
                enemy_stack -= enemy_match
                pot += enemy_match
                round_state["enemy_commit"] += enemy_match
                if enemy_action == "raise" and enemy_stack > 0:
                    reraise = min(enemy_stack, max(3, 2 + self.combat_enemy.poker_bonus))
                    enemy_stack -= reraise
                    pot += reraise
                    round_state["enemy_commit"] += reraise
                    round_state["enemy_stack"] = enemy_stack
                    round_state["pot"] = pot
                    round_state["to_call"] = reraise
                    round_state["stage"] = "player_response"
                    self.combat_log = [
                        f"You open for {bet} chips.",
                        f"{self.combat_enemy.name} reraises {reraise} chips.",
                        f"Pot: {pot}. Press 5 to call or 6 to fold.",
                    ]
                    self.last_enemy_reaction = f"{enemy_quote} They come back over the top."
                    return
                round_state["pot"] = pot
                round_state["enemy_stack"] = enemy_stack
                showdown(extra_damage=1)
                self.poker_round = None
                return
            if choice == "call":
                if enemy_action == "raise" and enemy_stack > 0:
                    bet = min(enemy_stack, max(3, 2 + self.combat_enemy.poker_bonus))
                    enemy_stack -= bet
                    pot += bet
                    round_state["enemy_commit"] += bet
                    round_state["enemy_stack"] = enemy_stack
                    round_state["pot"] = pot
                    round_state["to_call"] = bet
                    round_state["stage"] = "player_response"
                    self.last_enemy_reaction = f"{enemy_quote} They push {bet} more chips forward."
                    self.combat_log = [
                        "You check the action.",
                        f"{self.combat_enemy.name} bets {bet} chips.",
                        f"Pot: {pot}. Press 5 to call or 6 to fold.",
                    ]
                    return
                if enemy_action == "fold":
                    award_player_pot()
                    self.combat_log = [
                        "You tap the table.",
                        f"{self.combat_enemy.name} won't continue. You win {pot} chips.",
                    ]
                    self.last_enemy_reaction = enemy_quote
                    self.poker_round = None
                    return
                round_state["pot"] = pot
                showdown()
                self.poker_round = None
                return

        if stage == "player_response" and choice == "call":
            to_call = round_state["to_call"]
            call_amount = min(self.player_state.chips, to_call)
            self.player_state.chips -= call_amount
            pot += call_amount
            round_state["player_commit"] += call_amount
            round_state["pot"] = pot
            showdown(extra_damage=1)
            self.poker_round = None
            return

        self.combat_log = ["That move doesn't fit the current bet.", "Use the shown prompt to continue the hand."]

    def finish_combat_victory(self):
        enemy_name = self.combat_enemy.name
        self.player_state.gold += self.combat_enemy.gold_reward
        self.player_state.gain_xp(self.combat_enemy.xp_reward)

        for npc in self.active_area().npcs:
            if npc.combat and npc.combat.name == enemy_name:
                npc.active = False
                if npc.npc_id == "boss":
                    self.player_state.boss_defeated = True
        new_buff = self.maybe_award_buff()
        victory_text = (
            f"You beat {enemy_name}.\n"
            f"Rewards: {self.combat_enemy.gold_reward} gold and {self.combat_enemy.xp_reward} XP."
        )
        if new_buff:
            victory_text += f"\nNew buff unlocked: {new_buff}."
        self.dialogue = DialogueWindow(
            "Victory",
            victory_text,
        )
        self.combat_enemy = None
        if self.player_state.boss_defeated:
            self.scene = SCENE_GAME_OVER
            self.game_over_reason = "Mr. Vale is down, the district is yours, and the night is finally over."
        else:
            self.scene = SCENE_WORLD

    def finish_combat_defeat(self):
        self.scene = SCENE_GAME_OVER
        self.game_over_reason = "You were thrown out of the district before you could finish the job."
        self.poker_round = None

    def combat_turn(self, action):
        if self.combat_enemy is None:
            return

        enemy_gets_counter = True

        if action == 1:
            damage = max(1, self.player_state.attack + random.randint(0, 3) - self.combat_enemy.defense)
            self.combat_enemy.hp -= damage
            self.combat_log = [f"You strike for {damage} damage."]
        elif action == 2:
            self.begin_poker_round()
            enemy_gets_counter = False
        elif action == 3:
            if self.player_state.potions > 0:
                self.player_state.potions -= 1
                self.player_state.heal(12)
                self.combat_log = ["You drink a potion and recover 12 HP."]
            else:
                self.combat_log = ["No potions left."]
                enemy_gets_counter = False
        elif action == 4:
            self.resolve_poker_round("raise")
        elif action == 5:
            self.resolve_poker_round("call")
        elif action == 6:
            self.resolve_poker_round("fold")
            enemy_gets_counter = False
        else:
            return

        if self.combat_enemy is None:
            return
        if self.combat_enemy.hp <= 0:
            self.finish_combat_victory()
            return
        if self.player_state.hp <= 0:
            self.finish_combat_defeat()
            return
        if not enemy_gets_counter:
            return

        enemy_damage = max(1, self.combat_enemy.attack + random.randint(0, 3) - self.player_state.defense)
        self.player_state.damage(enemy_damage)
        self.combat_log.append(f"{self.combat_enemy.name} hits back for {enemy_damage} damage.")
        if self.player_state.hp <= 0:
            self.finish_combat_defeat()

    def draw_area(self):
        area = self.active_area()
        self.screen.fill(area.palette)
        cam_x = max(0, min(self.player.rect.centerx - WIDTH // 2, WORLD_COLS * TILE_SIZE - WIDTH))
        cam_y = max(0, min(self.player.rect.centery - HEIGHT // 2, WORLD_ROWS * TILE_SIZE - HEIGHT))

        for y, row in enumerate(area.tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * TILE_SIZE - cam_x, y * TILE_SIZE - cam_y, TILE_SIZE, TILE_SIZE)
                self.draw_floor(rect, area.floor_style, tile, x, y)

        for prop_name, x, y in area.props:
            self.draw_prop(prop_name, x - cam_x, y - cam_y)

        for warp in area.warps:
            warp_rect = pygame.Rect(warp.x - cam_x, warp.y - cam_y, TILE_SIZE, TILE_SIZE)
            self.draw_warp_icon(warp, warp_rect)
            if self.player.rect.inflate(80, 80).colliderect(warp.rect):
                pygame.draw.rect(self.screen, (75, 130, 170), warp_rect, 3, border_radius=10)

        for npc in area.npcs:
            if npc.active:
                self.draw_character(npc.sprite_key, npc.x - cam_x, npc.y - cam_y, npc.facing)

        self.draw_area_lighting(area)
        self.player.draw(self.screen, cam_x, cam_y)
        self.draw_hud(area)
        self.draw_interaction_hint()
        if self.dialogue:
            self.dialogue.draw(self.screen, self.big_font, self.font)

    def draw_floor(self, rect, style, tile, tile_x, tile_y):
        if tile == TILE_WALL:
            self.draw_wall_tile(rect, style, tile_x, tile_y)
            return

        if style == "warm":
            warm_tile = self.assets.extra_art.get("wood_floor_warm")
            dark_tile = self.assets.extra_art.get("wood_floor_dark")
            tile_surface = warm_tile if (tile_x + tile_y) % 2 == 0 else dark_tile or warm_tile
            if tile_surface:
                self.screen.blit(tile_surface, rect.topleft)
                pygame.draw.rect(self.screen, (24, 18, 14), rect, 1)
                return
        if style == "cold":
            alley_tile = self.assets.extra_art.get("alley_floor")
            if alley_tile:
                self.screen.blit(alley_tile, rect.topleft)
                if (tile_x + tile_y) % 5 == 0:
                    pygame.draw.ellipse(self.screen, (96, 116, 138), (rect.x + 8, rect.y + 38, 24, 10))
                pygame.draw.rect(self.screen, (22, 24, 28), rect, 1)
                return
        if style == "vault":
            vault_tile = self.assets.extra_art.get("vault_floor")
            if vault_tile:
                self.screen.blit(vault_tile, rect.topleft)
                if tile_x % 4 == 0:
                    pygame.draw.line(self.screen, (136, 154, 118), (rect.x, rect.y + 10), (rect.right, rect.y + 10), 1)
                pygame.draw.rect(self.screen, (26, 36, 28), rect, 1)
                return
        if style == "boss":
            office_tile = self.assets.extra_art.get("office_floor")
            if office_tile:
                self.screen.blit(office_tile, rect.topleft)
                pygame.draw.rect(self.screen, (44, 18, 18), rect, 1)
                return

        base_color = {
            "warm": (76, 60, 42),
            "cold": (52, 58, 66),
            "vault": (56, 72, 60),
            "boss": (82, 48, 48),
        }.get(style, (60, 60, 60))
        alt_color = {
            "warm": (88, 70, 48),
            "cold": (62, 68, 78),
            "vault": (68, 86, 70),
            "boss": (94, 56, 56),
        }.get(style, (72, 72, 72))
        stripe_color = {
            "warm": (95, 98, 108),
            "cold": (90, 96, 108),
            "vault": (86, 104, 92),
            "boss": (108, 82, 82),
        }.get(style, (92, 92, 92))

        if style == "warm":
            fill = alt_color if tile_x % 2 == 0 else base_color
        elif style == "cold":
            fill = alt_color if (tile_x + tile_y) % 4 == 0 else base_color
        elif style == "vault":
            fill = alt_color if tile_y % 2 == 0 else base_color
        elif style == "boss":
            fill = alt_color if (tile_x - tile_y) % 3 == 0 else base_color
        else:
            fill = alt_color if (tile_x + tile_y) % 2 == 0 else base_color
        pygame.draw.rect(self.screen, fill, rect)

        if style == "warm":
            inset = TILE_SIZE // 6
            pygame.draw.rect(
                self.screen,
                stripe_color,
                (rect.x + inset, rect.y, max(3, TILE_SIZE // 14), TILE_SIZE),
            )
        elif style == "cold":
            stripe_width = max(2, TILE_SIZE // 18)
            stripe_gap = max(18, TILE_SIZE // 2)
            stripe_x = rect.x + ((tile_x + tile_y) % 2) * (stripe_gap // 2)
            while stripe_x < rect.right:
                pygame.draw.rect(self.screen, stripe_color, (stripe_x, rect.y, stripe_width, TILE_SIZE))
                stripe_x += stripe_gap
        elif style == "vault":
            pygame.draw.rect(
                self.screen,
                stripe_color,
                (rect.x, rect.y + TILE_SIZE // 2 - 2, TILE_SIZE, 4),
            )
        elif style == "boss":
            pygame.draw.line(
                self.screen,
                stripe_color,
                (rect.x, rect.y + TILE_SIZE),
                (rect.x + TILE_SIZE, rect.y),
                2,
            )
            pygame.draw.line(
                self.screen,
                (52, 34, 34),
                (rect.x, rect.y),
                (rect.x + TILE_SIZE, rect.y + TILE_SIZE),
                1,
            )

        pygame.draw.rect(self.screen, (140, 140, 140), rect, 1)
        pygame.draw.rect(self.screen, (18, 18, 18), rect, 1)

    def draw_wall_tile(self, rect, style, tile_x, tile_y):
        palette = {
            "warm": ((71, 57, 46), (93, 73, 56), (48, 37, 30)),
            "cold": ((54, 60, 70), (74, 82, 94), (36, 42, 50)),
            "vault": ((52, 68, 56), (74, 96, 78), (34, 46, 38)),
            "boss": ((72, 42, 42), (104, 58, 58), (46, 24, 24)),
        }
        base, panel, trim = palette.get(style, ((64, 64, 70), (88, 88, 96), (40, 40, 46)))
        pygame.draw.rect(self.screen, base, rect)
        is_top = tile_y == 0
        is_bottom = tile_y == WORLD_ROWS - 1
        is_left = tile_x == 0
        is_right = tile_x == WORLD_COLS - 1

        if is_top:
            crown_h = 16
            pygame.draw.rect(self.screen, trim, (rect.x, rect.y, TILE_SIZE, crown_h))
            if style == "warm":
                for offset in range(8, TILE_SIZE, 16):
                    pygame.draw.rect(self.screen, panel, (rect.x + offset, rect.y + 3, 8, crown_h - 6), border_radius=2)
            elif style == "cold":
                for offset in range(0, TILE_SIZE, 12):
                    pygame.draw.line(self.screen, panel, (rect.x + offset, rect.y + crown_h - 2), (rect.x + offset + 6, rect.y + 2), 2)
            elif style == "vault":
                pygame.draw.rect(self.screen, panel, (rect.x + 6, rect.y + 3, TILE_SIZE - 12, crown_h - 6), border_radius=3)
                pygame.draw.line(self.screen, trim, (rect.x + TILE_SIZE // 2, rect.y + 3), (rect.x + TILE_SIZE // 2, rect.y + crown_h - 3), 2)
            elif style == "boss":
                pygame.draw.line(self.screen, panel, (rect.x + 4, rect.y + crown_h - 3), (rect.x + TILE_SIZE // 2, rect.y + 3), 3)
                pygame.draw.line(self.screen, panel, (rect.x + TILE_SIZE - 4, rect.y + crown_h - 3), (rect.x + TILE_SIZE // 2, rect.y + 3), 3)
        else:
            inner = pygame.Rect(rect.x + 4, rect.y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
            pygame.draw.rect(self.screen, panel, inner, border_radius=3)

        if is_left:
            pygame.draw.rect(self.screen, trim, (rect.x, rect.y, 8, TILE_SIZE))
        if is_right:
            pygame.draw.rect(self.screen, trim, (rect.right - 8, rect.y, 8, TILE_SIZE))
        if is_bottom:
            pygame.draw.rect(self.screen, trim, (rect.x, rect.bottom - 8, TILE_SIZE, 8))

        if not is_top:
            seam_x = rect.x + TILE_SIZE // 2
            pygame.draw.line(self.screen, trim, (seam_x, rect.y + 10), (seam_x, rect.bottom - 8), 1)

        corner_size = 10
        if is_top and is_left:
            pygame.draw.rect(self.screen, trim, (rect.x, rect.y, corner_size, corner_size))
        if is_top and is_right:
            pygame.draw.rect(self.screen, trim, (rect.right - corner_size, rect.y, corner_size, corner_size))
        if is_bottom and is_left:
            pygame.draw.rect(self.screen, trim, (rect.x, rect.bottom - corner_size, corner_size, corner_size))
        if is_bottom and is_right:
            pygame.draw.rect(self.screen, trim, (rect.right - corner_size, rect.bottom - corner_size, corner_size, corner_size))

        highlight = pygame.Rect(rect.x + 2, rect.y + 2, TILE_SIZE - 4, 2)
        pygame.draw.rect(
            self.screen,
            (min(255, base[0] + 20), min(255, base[1] + 20), min(255, base[2] + 20)),
            highlight,
        )
        pygame.draw.rect(self.screen, (18, 18, 18), rect, 2 if (is_top or is_left or is_right or is_bottom) else 1)

    def draw_prop(self, prop_name, x, y):
        layout = PROP_LAYOUTS.get(prop_name, {"size": (TILE_SIZE, TILE_SIZE), "anchor": "tile"})
        width, height = layout["size"]
        if prop_name == PROP_LOUNGE_BAR:
            surf = self.assets.extra_art.get("lounge_bar_full")
            surf = scale_to_fit(surf, width, height) if surf else None
        else:
            surf = self.assets.tile_art.get(prop_name, width, height)
        if surf:
            if layout["anchor"] == "center":
                draw_x = x + (TILE_SIZE - surf.get_width()) // 2
                draw_y = y + (TILE_SIZE - surf.get_height()) // 2
            elif layout["anchor"] == "floor":
                draw_x = x + (TILE_SIZE - surf.get_width()) // 2
                draw_y = y + TILE_SIZE - surf.get_height()
            else:
                draw_x = x
                draw_y = y
            shadow = pygame.Surface((surf.get_width() + 12, 18), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
            self.screen.blit(shadow, (draw_x - 6, draw_y + surf.get_height() - 10))
            self.screen.blit(surf, (draw_x, draw_y))
            return
        pygame.draw.rect(self.screen, (155, 110, 70), (x, y, TILE_SIZE, TILE_SIZE), border_radius=10)

    def draw_area_lighting(self, area):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        if area.floor_style == "warm":
            overlay.fill((255, 170, 90, 20))
            for center in ((190, 120), (WIDTH - 180, 130), (WIDTH // 2, 180)):
                pygame.draw.circle(overlay, (255, 210, 140, 32), center, 110)
        elif area.floor_style == "cold":
            overlay.fill((70, 100, 140, 28))
            for center in ((140, 110), (WIDTH - 160, 180)):
                pygame.draw.circle(overlay, (120, 170, 220, 26), center, 120)
            for center in ((220, HEIGHT - 120), (WIDTH - 260, HEIGHT - 140)):
                pygame.draw.ellipse(overlay, (90, 120, 160, 24), (center[0], center[1], 120, 40))
        elif area.floor_style == "vault":
            overlay.fill((140, 185, 120, 18))
            for y in (96, 224, 352):
                pygame.draw.rect(overlay, (210, 255, 190, 22), (80, y, WIDTH - 160, 18), border_radius=8)
        elif area.floor_style == "boss":
            overlay.fill((120, 40, 40, 24))
            pygame.draw.circle(overlay, (210, 110, 90, 34), (WIDTH // 2, 160), 180)
            pygame.draw.circle(overlay, (80, 10, 10, 40), (WIDTH // 2, HEIGHT // 2 + 80), 260)

        vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 0), (70, 50, WIDTH - 140, HEIGHT - 100))
        pygame.draw.rect(vignette, (0, 0, 0, 70), (0, 0, WIDTH, HEIGHT), 80)

        self.screen.blit(overlay, (0, 0))
        self.screen.blit(vignette, (0, 0))

    def draw_warp_icon(self, warp, rect):
        locked = self.warp_is_locked(warp)
        nearby = self.player.rect.inflate(96, 96).colliderect(warp.rect)
        pulse = (pygame.time.get_ticks() // 16) % 20
        glow_alpha = 70 + pulse if nearby and not locked else 35
        glow_color = (95, 195, 255, glow_alpha) if not locked else (180, 90, 90, 50)

        glow_surface = pygame.Surface((TILE_SIZE + 28, TILE_SIZE + 28), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surface, glow_color, glow_surface.get_rect())
        self.screen.blit(glow_surface, (rect.x - 14, rect.y - 8))

        base_plate = pygame.Rect(rect.x + 6, rect.bottom - 12, TILE_SIZE - 12, 8)
        pygame.draw.ellipse(self.screen, (16, 18, 24), base_plate)
        pygame.draw.ellipse(
            self.screen,
            (110, 180, 230) if not locked else (150, 88, 88),
            base_plate.inflate(6, 4),
            2,
        )

        icon = self.assets.door_icons.get(warp.icon)
        if icon:
            icon = scale_to_fit(icon, TILE_SIZE - 4, TILE_SIZE - 4)
            draw_x = rect.x + (TILE_SIZE - icon.get_width()) // 2
            draw_y = rect.y + TILE_SIZE - icon.get_height()
            self.screen.blit(icon, (draw_x, draw_y))
        else:
            pygame.draw.rect(self.screen, (75, 130, 170), rect.inflate(-12, -12), border_radius=10)

        if locked:
            lock_rect = pygame.Rect(rect.centerx - 10, rect.y + 6, 20, 20)
            pygame.draw.rect(self.screen, (120, 36, 36), lock_rect, border_radius=4)
            pygame.draw.rect(self.screen, (255, 205, 150), lock_rect, 2, border_radius=4)
            pygame.draw.arc(self.screen, (255, 205, 150), (rect.centerx - 8, rect.y + 0, 16, 14), 3.14, 6.28, 2)

        if nearby:
            label_text = warp.label if not locked else f"{warp.label} (Locked)"
            label = self.small_font.render(label_text, True, (245, 238, 220))
            plate = pygame.Rect(
                rect.centerx - label.get_width() // 2 - 8,
                rect.y - 26,
                label.get_width() + 16,
                22,
            )
            pygame.draw.rect(self.screen, (20, 20, 24), plate, border_radius=8)
            pygame.draw.rect(
                self.screen,
                (110, 180, 230) if not locked else (160, 90, 90),
                plate,
                2,
                border_radius=8,
            )
            self.screen.blit(label, (plate.x + 8, plate.y + 3))

    def draw_character(self, sprite_key, x, y, direction):
        sheet = {
            "dealer": self.assets.dealer_sheet,
            "gambler": self.assets.gambler_sheet,
            "boss": self.assets.boss_sheet,
            "player": self.assets.player_sheet,
        }.get(sprite_key)
        sprite = sheet.get_frame(direction, 0) if sheet else None
        if sprite:
            surface = sprite["surface"]
            draw_x = x + PLAYER_SIZE // 2 - surface.get_width() // 2
            draw_y = y + PLAYER_SIZE - surface.get_height()
            self.screen.blit(surface, (draw_x, draw_y))
            return
        pygame.draw.rect(self.screen, (215, 215, 215), (x, y, PLAYER_SIZE, PLAYER_SIZE))

    def draw_hud(self, area):
        hud = pygame.Rect(16, 16, 320, 172)
        pygame.draw.rect(self.screen, (22, 22, 28), hud, border_radius=12)
        pygame.draw.rect(self.screen, (225, 225, 225), hud, 2, border_radius=12)
        buff_text = ", ".join(self.player_state.buffs[:2]) if self.player_state.buffs else "None"
        lines = [
            f"Area: {area.name}",
            f"HP: {self.player_state.hp}/{self.player_state.max_hp}",
            f"Level: {self.player_state.level}  XP: {self.player_state.xp}",
            f"ATK: {self.player_state.attack}  DEF: {self.player_state.defense}",
            f"Gold: {self.player_state.gold}  Chips: {self.player_state.chips}",
            f"Potions: {self.player_state.potions}",
            f"Buffs: {buff_text}",
        ]
        for idx, line in enumerate(lines):
            surf = self.small_font.render(line, True, (240, 240, 240))
            self.screen.blit(surf, (hud.x + 12, hud.y + 12 + idx * 22))

    def draw_interaction_hint(self):
        found = self.nearest_interaction()
        text = "E / Enter / Space interact   Q potion   I status   H help   Esc close"
        if found:
            kind, obj = found
            if kind == "npc":
                text = f"E / Enter / Space: {obj.name}"
                if obj.role in ("enemy", "boss"):
                    text = f"E / Enter / Space: challenge {obj.name}"
            else:
                text = f"E / Enter / Space: travel {obj.label}"
        surf = self.font.render(text, True, (255, 230, 150))
        y = 18 if self.dialogue else HEIGHT - 32
        self.screen.blit(surf, (18, y))

    def open_status_panel(self):
        buffs = ", ".join(self.player_state.buffs) if self.player_state.buffs else "None"
        self.dialogue = DialogueWindow(
            "Status",
            f"Level {self.player_state.level}\n"
            f"HP {self.player_state.hp}/{self.player_state.max_hp}\n"
            f"ATK {self.player_state.attack}  DEF {self.player_state.defense}\n"
            f"Gold {self.player_state.gold}  Chips {self.player_state.chips}\n"
            f"Potions {self.player_state.potions}\n"
            f"Poker Bonus +{self.player_state.poker_bonus}\n"
            f"Buffs: {buffs}\n"
            "Explore, fight, and use any open door.",
        )

    def open_help_panel(self):
        self.dialogue = DialogueWindow(
            "Controls",
            "Move: WASD or Arrow Keys\n"
            "Interact: E, Enter, or Space\n"
            "Potion: Q\n"
            "Status: I\n"
            "Help: H\n"
            "Close window: Esc\n"
            "Combat: 1 attack, 2 poker skill, 3 potion",
        )

    def draw_combat(self):
        self.screen.fill((18, 18, 22))
        arena = pygame.Rect(50, 70, WIDTH - 100, HEIGHT - 180)
        pygame.draw.rect(self.screen, (28, 28, 34), arena, border_radius=14)
        pygame.draw.rect(self.screen, (225, 225, 225), arena, 2, border_radius=14)

        self.draw_character("player", 170, 360, "right")
        self.draw_character(self.combat_enemy.sprite_key, WIDTH - 250, 220, "left")
        self.draw_poker_showdown()

        player_box = self.font.render(
            f"You  HP {self.player_state.hp}/{self.player_state.max_hp}  Chips {self.player_state.chips}  ATK {self.player_state.attack}  DEF {self.player_state.defense}",
            True,
            (240, 240, 240),
        )
        enemy_chip_text = ""
        if self.poker_round:
            enemy_chip_text = f"  Pot {self.poker_round['pot']}  Enemy Chips {self.poker_round['enemy_stack']}"
        enemy_box = self.font.render(
            f"{self.combat_enemy.name}  HP {self.combat_enemy.hp}/{self.combat_enemy.max_hp}{enemy_chip_text}",
            True,
            (240, 240, 240),
        )
        self.screen.blit(player_box, (80, 110))
        self.screen.blit(enemy_box, (WIDTH - enemy_box.get_width() - 80, 110))

        title = self.title_font.render("Combat", True, (255, 232, 160))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 84))

        log_panel = pygame.Rect(80, HEIGHT - 210, WIDTH - 160, 130)
        pygame.draw.rect(self.screen, (20, 20, 24), log_panel, border_radius=12)
        pygame.draw.rect(self.screen, (180, 180, 180), log_panel, 2, border_radius=12)
        for idx, line in enumerate(self.combat_log[-4:]):
            surf = self.font.render(line, True, (235, 235, 235))
            self.screen.blit(surf, (log_panel.x + 14, log_panel.y + 14 + idx * 24))

        prompt_text = "1 Attack   2 Deal Hand   3 Potion"
        if self.poker_round:
            if self.poker_round.get("stage") == "player_response":
                prompt_text = "5 Call   6 Fold"
            else:
                prompt_text = "4 Bet/Raise   5 Check/Call   6 Fold"
        prompt = self.small_font.render(prompt_text, True, (255, 220, 120))
        if self.last_enemy_reaction:
            reaction = self.small_font.render(self.last_enemy_reaction, True, (190, 190, 190))
            self.screen.blit(reaction, (WIDTH // 2 - reaction.get_width() // 2, HEIGHT - 76))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 54))

    def draw_card_back(self, x, y):
        rect = pygame.Rect(x, y, 66, 96)
        pygame.draw.rect(self.screen, (36, 46, 74), rect, border_radius=8)
        pygame.draw.rect(self.screen, (214, 224, 245), rect, 2, border_radius=8)
        inner = rect.inflate(-14, -14)
        pygame.draw.rect(self.screen, (68, 86, 122), inner, border_radius=6)
        pygame.draw.line(self.screen, (214, 224, 245), (inner.x + 6, inner.y + 6), (inner.right - 6, inner.bottom - 6), 2)
        pygame.draw.line(self.screen, (214, 224, 245), (inner.right - 6, inner.y + 6), (inner.x + 6, inner.bottom - 6), 2)

    def draw_card_visual(self, card, x, y):
        face = self.assets.card_faces.get(card)
        if face:
            face = scale_to_fit(face, 66, 96)
            self.screen.blit(face, (x, y))
            return
        rank, suit = card
        rect = pygame.Rect(x, y, 66, 96)
        pygame.draw.rect(self.screen, (245, 245, 245), rect, border_radius=8)
        pygame.draw.rect(self.screen, (30, 30, 36), rect, 2, border_radius=8)
        color = (180, 40, 40) if suit in ("hearts", "diamonds") else (30, 30, 36)
        text = self.small_font.render(f"{card_label(rank)} {suit[0].upper()}", True, color)
        self.screen.blit(text, (x + 8, y + 10))

    def draw_poker_showdown(self):
        if not self.last_player_cards or not self.last_enemy_cards:
            return
        hide_enemy = self.poker_round is not None
        for idx, card in enumerate(self.last_enemy_cards):
            if hide_enemy:
                self.draw_card_back(270 + idx * 74, 140)
            else:
                self.draw_card_visual(card, 270 + idx * 74, 140)
        for idx, card in enumerate(self.last_player_cards):
            self.draw_card_visual(card, 270 + idx * 74, 360)
        if self.last_poker_labels:
            enemy_title = "Dealer hand" if hide_enemy else self.last_poker_labels[1]
            enemy_label = self.small_font.render(enemy_title, True, (235, 235, 235))
            player_label = self.small_font.render(self.last_poker_labels[0], True, (235, 235, 235))
            self.screen.blit(enemy_label, (440 - enemy_label.get_width() // 2, 112))
            self.screen.blit(player_label, (440 - player_label.get_width() // 2, 460))

    def draw_game_over(self):
        self.screen.fill((14, 14, 18))
        title = "Victory" if self.player_state.boss_defeated else "Game Over"
        title_surf = self.title_font.render(title, True, (255, 230, 160))
        reason = self.font.render(self.game_over_reason, True, (225, 225, 225))
        prompt = self.small_font.render("Press Enter to return to the menu.", True, (210, 210, 210))
        self.screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 230))
        self.screen.blit(reason, (WIDTH // 2 - reason.get_width() // 2, 300))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 350))

    def update_world(self):
        self.player.move(pygame.key.get_pressed(), self.active_area(), self.blocker_rects())

    def handle_world_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.dialogue = None
        elif event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            self.interact()
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            self.handle_shop_buy(event.key)
        elif event.key == pygame.K_q:
            if self.player_state.potions > 0:
                self.player_state.potions -= 1
                self.player_state.heal(10)
                self.dialogue = DialogueWindow("Potion", "You recover 10 HP.")
            else:
                self.dialogue = DialogueWindow("Potion", "No potions left.")
        elif event.key == pygame.K_i:
            self.open_status_panel()
        elif event.key == pygame.K_h:
            self.open_help_panel()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event.size)
                    continue

                if self.scene == SCENE_MENU:
                    self.menu.handle_input(event)
                elif self.scene == SCENE_INTRO:
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                        self.advance_intro()
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.advance_intro()
                elif self.scene == SCENE_WORLD and event.type == pygame.KEYDOWN:
                    self.handle_world_key(event)
                elif self.scene == SCENE_COMBAT and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.combat_turn(1)
                    elif event.key == pygame.K_2:
                        self.combat_turn(2)
                    elif event.key == pygame.K_3:
                        self.combat_turn(3)
                    elif event.key == pygame.K_4:
                        self.combat_turn(4)
                    elif event.key == pygame.K_5:
                        self.combat_turn(5)
                    elif event.key == pygame.K_6:
                        self.combat_turn(6)
                elif self.scene == SCENE_GAME_OVER and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.scene = SCENE_MENU
                        self.dialogue = None

            if self.scene == SCENE_MENU:
                self.menu.draw(self.screen)
            elif self.scene == SCENE_INTRO:
                self.draw_intro()
            elif self.scene == SCENE_WORLD:
                self.update_world()
                self.draw_area()
            elif self.scene == SCENE_COMBAT:
                self.draw_combat()
            else:
                self.draw_game_over()

            self.scaler.present(self.window, self.screen)
            pygame.display.flip()
            self.clock.tick(60)


if __name__ == "__main__":
    Game().run()
