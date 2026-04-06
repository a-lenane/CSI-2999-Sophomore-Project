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
FALLBACK_ASSET_DIRS = [
    os.environ.get("POKER_ROGUELIKE_ASSET_DIR"),
    os.path.join(SCRIPT_DIR, "Assets"),
    os.path.join(SCRIPT_DIR, "assets"),
    "/Users/alexmatovski/PyCharmMiscProject/Gametest2/Assets",
]

SCENE_MENU = 0
SCENE_WORLD = 1
SCENE_COMBAT = 2
SCENE_GAME_OVER = 3

TILE_FLOOR = 0
TILE_WALL = 1
TILE_EXIT = 2

PROP_SLOT = "slot"
PROP_RUG = "rug"
PROP_TABLE = "table"
PROP_CRATES = "crates"
PROP_BAR = "bar"
PROP_WALL = "wall"

PROP_LAYOUTS = {
    PROP_SLOT: {"size": (96, 140), "anchor": "floor"},
    PROP_RUG: {"size": (150, 110), "anchor": "center"},
    PROP_TABLE: {"size": (150, 108), "anchor": "floor"},
    PROP_CRATES: {"size": (132, 120), "anchor": "floor"},
    PROP_BAR: {"size": (220, 132), "anchor": "floor"},
    PROP_WALL: {"size": (64, 64), "anchor": "tile"},
}


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
        self.missing = [name for name, path in self.paths.items() if not os.path.exists(path)]


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
    xp: int = 0
    level: int = 1
    quest_stage: int = 0
    has_backroom_key: bool = False
    chest_opened: bool = False
    boss_defeated: bool = False

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def damage(self, amount):
        self.hp = max(0, self.hp - amount)

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

    def handle_resize(self, size):
        width = max(640, size[0])
        height = max(480, size[1])
        self.window = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.scaler.update((width, height))

    def start_new_game(self):
        self.player_state = PlayerState()
        self.areas = self.build_areas()
        self.current_area = "lounge"
        self.player.place(*self.areas[self.current_area].spawn)
        self.scene = SCENE_WORLD
        self.dialogue = DialogueWindow(
            "Night Shift",
            "The dealer flagged you down.\nTalk to people, shake down the district, and reach the office upstairs.\nPress E to interact and 1/2/3 during combat.",
        )

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
            (PROP_BAR, TILE_SIZE * 10, TILE_SIZE * 2),
            (PROP_SLOT, TILE_SIZE * 2, TILE_SIZE * 2),
            (PROP_SLOT, TILE_SIZE * 2, TILE_SIZE * 5),
            (PROP_TABLE, TILE_SIZE * 6, TILE_SIZE * 4),
            (PROP_TABLE, TILE_SIZE * 8, TILE_SIZE * 6),
        ]
        lounge.npcs = [
            NPC("dealer", "Mara the Dealer", "dealer", TILE_SIZE * 6, TILE_SIZE * 3, "quest", "Need help? I know where the ledger is."),
            NPC("bartender", "Silas the Bartender", "dealer", TILE_SIZE * 11, TILE_SIZE * 3, "shop", "Need a top-up? I sell potions and grit."),
        ]
        lounge.warps = [
            Warp(TILE_SIZE * 13, TILE_SIZE * 5, "alley", (TILE_SIZE * 2, TILE_SIZE * 5), "To Back Alley"),
            Warp(TILE_SIZE * 7, TILE_SIZE * 1, "office", (TILE_SIZE * 7, TILE_SIZE * 8), "Stairs Up", locked_by="boss_access"),
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
            Warp(TILE_SIZE * 1, TILE_SIZE * 5, "lounge", (TILE_SIZE * 12, TILE_SIZE * 5), "Back To Lounge"),
            Warp(TILE_SIZE * 13, TILE_SIZE * 5, "vault", (TILE_SIZE * 2, TILE_SIZE * 5), "Service Door", locked_by="backroom_key"),
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
        ]
        vault.npcs = [
            NPC("safekeeper", "Old Cashier", "dealer", TILE_SIZE * 10, TILE_SIZE * 5, "treasure", "If you made it in here, maybe you earned something."),
        ]
        vault.warps = [
            Warp(TILE_SIZE * 1, TILE_SIZE * 5, "alley", (TILE_SIZE * 12, TILE_SIZE * 5), "Back To Alley"),
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
            Warp(TILE_SIZE * 7, TILE_SIZE * 9, "lounge", (TILE_SIZE * 7, TILE_SIZE * 2), "Downstairs"),
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

        if obj.role == "quest":
            self.handle_dealer(obj)
        elif obj.role == "shop":
            self.open_shop()
        elif obj.role == "enemy":
            self.start_combat(obj)
        elif obj.role == "boss":
            self.start_combat(obj)
        elif obj.role == "treasure":
            self.open_treasure(obj)
        else:
            self.dialogue = DialogueWindow(obj.name, obj.dialogue)

    def handle_dealer(self, npc):
        stage = self.player_state.quest_stage
        if stage == 0:
            self.player_state.quest_stage = 1
            self.dialogue = DialogueWindow(
                npc.name,
                "Rook stole the floor ledger and the office won’t open without it.\nFind him in the Back Alley and take it back.",
            )
        elif stage == 1:
            self.dialogue = DialogueWindow(npc.name, "The alley door is open. Beat Rook and bring me the ledger.")
        elif stage == 2:
            self.player_state.quest_stage = 3
            self.dialogue = DialogueWindow(
                npc.name,
                "Nice work. Here’s the upstairs clearance.\nThe office stairs are now open, and the service door key is yours too.",
            )
        elif stage == 3:
            self.dialogue = DialogueWindow(npc.name, "Vale is upstairs. Stock up before you head in.")
        else:
            self.dialogue = DialogueWindow(npc.name, "You did it. The district is finally quiet.")

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
        if warp.locked_by == "boss_access" and self.player_state.quest_stage < 3:
            self.dialogue = DialogueWindow("Locked", "The stairs stay shut until Mara clears you upstairs.")
            return
        if warp.locked_by == "backroom_key" and not self.player_state.has_backroom_key:
            self.dialogue = DialogueWindow("Locked", "You need the backroom key first.")
            return
        self.current_area = warp.target_area
        self.player.place(*warp.target_pos)
        self.dialogue = DialogueWindow(self.active_area().name, self.active_area().flavor)

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
        self.combat_log = [
            f"{npc.name}: {npc.combat.taunt}",
            "1 Attack  2 Poker Skill  3 Potion",
        ]
        self.scene = SCENE_COMBAT

    def finish_combat_victory(self):
        enemy_name = self.combat_enemy.name
        self.player_state.gold += self.combat_enemy.gold_reward
        self.player_state.gain_xp(self.combat_enemy.xp_reward)

        for npc in self.active_area().npcs:
            if npc.combat and npc.combat.name == enemy_name:
                npc.active = False
                if npc.npc_id == "gambler":
                    self.player_state.quest_stage = max(self.player_state.quest_stage, 2)
                    self.player_state.has_backroom_key = True
                if npc.npc_id == "boss":
                    self.player_state.boss_defeated = True
        self.dialogue = DialogueWindow(
            "Victory",
            f"You beat {enemy_name}.\nRewards: {self.combat_enemy.gold_reward} gold and {self.combat_enemy.xp_reward} XP.",
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

    def combat_turn(self, action):
        if self.combat_enemy is None:
            return

        if action == 1:
            damage = max(1, self.player_state.attack + random.randint(0, 3) - self.combat_enemy.defense)
            self.combat_enemy.hp -= damage
            self.combat_log = [f"You strike for {damage} damage."]
        elif action == 2:
            player_cards = roll_hand(self.player_state.poker_bonus)
            enemy_cards = roll_hand(self.combat_enemy.poker_bonus)
            outcome, player_name, enemy_name = compare_hands(player_cards, enemy_cards)
            if outcome > 0:
                damage = 8 + self.player_state.level
                self.combat_enemy.hp -= damage
                self.combat_log = [
                    f"Poker win: {' '.join(card_label(card) for card in player_cards)} ({player_name})",
                    f"Enemy shows {' '.join(card_label(card) for card in enemy_cards)} ({enemy_name})",
                    f"Your read lands for {damage} damage.",
                ]
            elif outcome < 0:
                damage = 5 + self.combat_enemy.poker_bonus
                self.player_state.damage(damage)
                self.combat_log = [
                    f"Poker loss: {' '.join(card_label(card) for card in player_cards)} ({player_name})",
                    f"Enemy shows {' '.join(card_label(card) for card in enemy_cards)} ({enemy_name})",
                    f"You lose your footing and take {damage} damage.",
                ]
            else:
                self.combat_log = ["Tie hand. Nobody finds an opening."]
        elif action == 3:
            if self.player_state.potions > 0:
                self.player_state.potions -= 1
                self.player_state.heal(12)
                self.combat_log = ["You drink a potion and recover 12 HP."]
            else:
                self.combat_log = ["No potions left."]
        else:
            return

        if self.combat_enemy.hp <= 0:
            self.finish_combat_victory()
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
            if self.player.rect.inflate(80, 80).colliderect(warp.rect):
                pygame.draw.rect(self.screen, (75, 130, 170), warp_rect, 3, border_radius=10)

        for npc in area.npcs:
            if npc.active:
                self.draw_character(npc.sprite_key, npc.x - cam_x, npc.y - cam_y, npc.facing)

        self.player.draw(self.screen, cam_x, cam_y)
        self.draw_hud(area)
        self.draw_interaction_hint()
        if self.dialogue:
            self.dialogue.draw(self.screen, self.big_font, self.font)

    def draw_floor(self, rect, style, tile, tile_x, tile_y):
        if tile == TILE_WALL:
            self.draw_wall_tile(rect, style, tile_x, tile_y)
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
            self.screen.blit(surf, (draw_x, draw_y))
            return
        pygame.draw.rect(self.screen, (155, 110, 70), (x, y, TILE_SIZE, TILE_SIZE), border_radius=10)

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
        hud = pygame.Rect(16, 16, 280, 150)
        pygame.draw.rect(self.screen, (22, 22, 28), hud, border_radius=12)
        pygame.draw.rect(self.screen, (225, 225, 225), hud, 2, border_radius=12)
        lines = [
            f"Area: {area.name}",
            f"HP: {self.player_state.hp}/{self.player_state.max_hp}",
            f"Level: {self.player_state.level}  XP: {self.player_state.xp}",
            f"ATK: {self.player_state.attack}  DEF: {self.player_state.defense}",
            f"Gold: {self.player_state.gold}  Potions: {self.player_state.potions}",
            f"Quest: {self.quest_text()}",
        ]
        for idx, line in enumerate(lines):
            surf = self.small_font.render(line, True, (240, 240, 240))
            self.screen.blit(surf, (hud.x + 12, hud.y + 12 + idx * 22))

    def quest_text(self):
        stage = self.player_state.quest_stage
        if self.player_state.boss_defeated:
            return "Finished"
        if stage == 0:
            return "Talk to Mara"
        if stage == 1:
            return "Beat Rook in the alley"
        if stage == 2:
            return "Report back to Mara"
        return "Confront Mr. Vale upstairs"

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
        self.dialogue = DialogueWindow(
            "Status",
            f"Level {self.player_state.level}\n"
            f"HP {self.player_state.hp}/{self.player_state.max_hp}\n"
            f"ATK {self.player_state.attack}  DEF {self.player_state.defense}\n"
            f"Gold {self.player_state.gold}  Potions {self.player_state.potions}\n"
            f"Poker Bonus +{self.player_state.poker_bonus}\n"
            f"Quest: {self.quest_text()}",
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

        player_box = self.font.render(
            f"You  HP {self.player_state.hp}/{self.player_state.max_hp}  ATK {self.player_state.attack}  DEF {self.player_state.defense}",
            True,
            (240, 240, 240),
        )
        enemy_box = self.font.render(
            f"{self.combat_enemy.name}  HP {self.combat_enemy.hp}/{self.combat_enemy.max_hp}",
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

        prompt = self.small_font.render("1 Attack   2 Poker Skill   3 Potion", True, (255, 220, 120))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 54))

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
                elif self.scene == SCENE_WORLD and event.type == pygame.KEYDOWN:
                    self.handle_world_key(event)
                elif self.scene == SCENE_COMBAT and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.combat_turn(1)
                    elif event.key == pygame.K_2:
                        self.combat_turn(2)
                    elif event.key == pygame.K_3:
                        self.combat_turn(3)
                elif self.scene == SCENE_GAME_OVER and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.scene = SCENE_MENU
                        self.dialogue = None

            if self.scene == SCENE_MENU:
                self.menu.draw(self.screen)
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
