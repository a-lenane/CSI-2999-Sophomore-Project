import pygame
import sys
import random
import json
import os
from PokerLogic import *
from DialogueCasino import BOSS_DIALOGUE, STORY_PAGES, GAME_OVER_TEXT, ENDING_TEXT

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Texas Hold'em: High Stakes")
clock = pygame.time.Clock()

# Colors
TABLE_GREEN = (6, 71, 42)
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
LIGHT_GOLD = (255, 215, 0)
FLOOR = (40, 40, 40)
WALL = (20, 20, 20)
PLAYER_COLOR = (200, 50, 50)
NPC_COLOR = (200, 200, 50)
CARD_BACK_COLOR = (100, 50, 0)
BOSS_MSG_BG = (0, 0, 0, 180)
MENU_BG = (0, 0, 0, 200)

TILE_COLS = 16
TILE_ROWS = 9
TILE_GAP = 2
TILE_BORDER_COLOR = (30, 30, 30)

ROOM_COLORS = [
    ((40, 90, 40), (10, 40, 10)),
    ((30, 30, 90), (0, 0, 40)),
    ((120, 40, 40), (60, 0, 0))
]

DOOR_SIZE = 80
DOOR_COLOR = (100, 50, 20)
DOOR_HIGHLIGHT = (160, 100, 40)
BASE_WALL_THICK = 40

BASE_PLAYER_SIZE = 40
BASE_NPC_SIZE = 35
BASE_TABLE_W = 120
BASE_TABLE_H = 80
BASE_CARD_W = 80
BASE_CARD_H = 112

title_font = pygame.font.SysFont("arialblack", 80)
font = pygame.font.SysFont(None, 32)
boss_font = pygame.font.SysFont("arialblack", 28)

#event log
event_log = []
MAX_LOG_LINES = 6

# Persistent player
human_player = Player("You")
human_player.chips = 500

# Progression tracking (boss chip stacks & defeat status)
#boss_chips = {"easy": 1000, "medium": 2000, "hard": 4000}
bosses_defeated = {"easy": False, "medium": False, "hard": False}

SAVE_FILE = "savegame.json"

def save_game():
    data = {
        "chips": human_player.chips,
        "boss_chips": boss_chips,
        "bosses_defeated": bosses_defeated,
        "player_buffs": human_player.buffs,
        "table_intro_shown": table_intro_shown,
        "current_room": current_room,
        "player_x_ratio": player.x_ratio,
        "player_y_ratio": player.y_ratio
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_game():
    global human_player, table_intro_shown, current_room, player, boss_chips, bosses_defeated
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        human_player.chips = data["chips"]
        boss_chips = data.get("boss_chips", {"easy": 1000, "medium": 2000, "hard": 4000})
        bosses_defeated = data.get("bosses_defeated", {"easy": False, "medium": False, "hard": False})
        human_player.buffs.update(data.get("player_buffs", {}))
        table_intro_shown = data["table_intro_shown"]
        current_room = data["current_room"]
        player.x_ratio = data["player_x_ratio"]
        player.y_ratio = data["player_y_ratio"]
        recalculate_elements()
        return True
    return False

# UI Classes
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
        dynamic_font = pygame.font.SysFont("arial", int(btn_h * 0.5))
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

    def resize(self, scale_x, scale_y):
        width = int(BASE_PLAYER_SIZE * scale_x)
        height = int(BASE_PLAYER_SIZE * scale_y)
        self.rect.size = (width, height)
        self.reposition()

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def move(self, dx, dy, colliders):
        self.rect.x += dx
        for collider in colliders:
            if self.rect.colliderect(collider):
                if dx > 0:
                    self.rect.right = collider.left
                elif dx < 0:
                    self.rect.left = collider.right
        self.rect.y += dy
        for collider in colliders:
            if self.rect.colliderect(collider):
                if dy > 0:
                    self.rect.bottom = collider.top
                elif dy < 0:
                    self.rect.top = collider.bottom
        self.x_ratio = self.rect.centerx / WIDTH
        self.y_ratio = self.rect.centery / HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)

class NPC:
    def __init__(self, x_ratio, y_ratio):
        self.x_ratio, self.y_ratio = x_ratio, y_ratio
        self.rect = pygame.Rect(0, 0, BASE_NPC_SIZE, BASE_NPC_SIZE)
        self.timer = 0
        self.direction = (0, 0)
        self.base_speed = 2

    def resize(self, scale_x, scale_y):
        width = int(BASE_NPC_SIZE * scale_x)
        height = int(BASE_NPC_SIZE * scale_y)
        self.rect.size = (width, height)
        self.reposition()

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def update(self, colliders, speed_scale_x, speed_scale_y):
        self.timer -= 1
        if self.timer <= 0:
            if random.random() < 0.7:
                self.direction = (0, 0)
            else:
                self.direction = random.choice([(1,0), (-1,0), (0,1), (0,-1)])
            self.timer = random.randint(30, 90)
        dx = self.direction[0] * self.base_speed * speed_scale_x
        dy = self.direction[1] * self.base_speed * speed_scale_y
        self.rect.x += dx
        for collider in colliders:
            if self.rect.colliderect(collider):
                if dx > 0:
                    self.rect.right = collider.left
                elif dx < 0:
                    self.rect.left = collider.right
        self.rect.y += dy
        for collider in colliders:
            if self.rect.colliderect(collider):
                if dy > 0:
                    self.rect.bottom = collider.top
                elif dy < 0:
                    self.rect.top = collider.bottom
        self.x_ratio = self.rect.centerx / WIDTH
        self.y_ratio = self.rect.centery / HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, NPC_COLOR, self.rect)

class Door:
    def __init__(self, rect, target_room, spawn_pos):
        self.rect = rect
        self.target_room = target_room
        self.spawn_pos = spawn_pos

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

# Room configurations (no guards)
tables = []
npcs = []
obstacles = []

def set_room_layout(room_idx, scale_x, scale_y):
    global tables, npcs, obstacles
    table_w = int(BASE_TABLE_W * scale_x)
    table_h = int(BASE_TABLE_H * scale_y)

    obstacles.clear()
    if room_idx == 0:
        tables = [pygame.Rect(WIDTH * 0.3, HEIGHT * 0.3, table_w, table_h)]
        npcs = [NPC(0.2, 0.3), NPC(0.4, 0.5), NPC(0.7, 0.2)]
        obs1 = pygame.Rect(WIDTH*0.15, HEIGHT*0.6, 30, 30)
        obs2 = pygame.Rect(WIDTH*0.7, HEIGHT*0.8, 50, 30)
        obs3 = pygame.Rect(WIDTH*0.85, HEIGHT*0.2, 40, 40)
        obstacles.extend([obs1, obs2, obs3])
    elif room_idx == 1:
        tables = [pygame.Rect(WIDTH * 0.5, HEIGHT * 0.5, table_w, table_h)]
        npcs = []
        obs1 = pygame.Rect(WIDTH*0.2, HEIGHT*0.2, 60, 60)
        obs2 = pygame.Rect(WIDTH*0.75, HEIGHT*0.7, 45, 45)
        obs3 = pygame.Rect(WIDTH*0.1, HEIGHT*0.8, 35, 60)
        obstacles.extend([obs1, obs2, obs3])
    else:
        tables = [pygame.Rect(WIDTH * 0.5, HEIGHT * 0.4, table_w, table_h)]
        npcs = []

    for n in npcs:
        n.resize(scale_x, scale_y)

# Initialization
player = WorldPlayer()
walls = []
doors = []
current_room = 0
current_scale_x = 1.0
current_scale_y = 1.0

# Buttons
checkCall_btn = Button("Check/Call", 0.2, 0.9, 0.15, 0.06)
raise_btn = Button("Raise", 0.4, 0.9, 0.15, 0.06)
fold_btn = Button("Fold", 0.6, 0.9, 0.15, 0.06)
leave_btn = Button("Leave", 0.8, 0.9, 0.15, 0.06)
play_again_btn = Button("Play Again", 0.4, 0.85, 0.2, 0.08)
leave_table_btn = Button("Leave Table", 0.6, 0.85, 0.2, 0.08)
peek_btn = Button("Peek Card", .8, .82, .15, .06)

volume_slider_btn = Button("Volume: 50%", 0.5, 0.4, 0.3, 0.07)
abandon_btn = Button("Abandon Mission", 0.5, 0.55, 0.3, 0.07)
save_exit_btn = Button("Save & Exit", 0.5, 0.7, 0.3, 0.07)
resume_btn = Button("Resume", 0.5, 0.85, 0.3, 0.07)

new_game_btn = Button("New Game", 0.5, 0.4, 0.3, 0.08)
continue_btn = Button("Continue", 0.5, 0.55, 0.3, 0.08)
quit_main_btn = Button("Quit", 0.5, 0.7, 0.3, 0.08)

deck_pos = (WIDTH * 0.1, HEIGHT * 0.5)
active_animations = []
animating = False
animating_card_keys = set()

boss_message_text = None
boss_message_timer = 0
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

def set_boss_message(msg):
    global boss_message_text, boss_message_timer
    boss_message_text = msg
    boss_message_timer = 3000

def add_event(text):
    event_log.append(text)
    if len(event_log) > MAX_LOG_LINES:
        event_log.pop(0)

def update_boss_message(dt_ms):
    global boss_message_timer, boss_message_text
    if boss_message_timer > 0:
        boss_message_timer -= dt_ms
        if boss_message_timer <= 0:
            boss_message_text = None

def draw_boss_message(surface):
    if boss_message_text:
        msg_surf = boss_font.render(boss_message_text, True, GOLD)
        padding = 15
        bg_rect = msg_surf.get_rect().inflate(padding*2, padding)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 180))
        x = WIDTH * 0.15
        y = HEIGHT * 0.05
        bg_rect.topleft = (x, y)
        surface.blit(bg_surf, bg_rect)
        surface.blit(msg_surf, msg_surf.get_rect(center=bg_rect.center))

def draw_event_log(surface):
    box_width = WIDTH * .35
    box_height = HEIGHT * .25
    x = WIDTH * .02
    y = HEIGHT * .68

    bg = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 180))
    surface.blit(bg, (x,y))

    pygame.draw.rect(surface, GOLD, (x,y, box_width, box_height), 2)

    title = font.render("Event Log", True, GOLD)
    surface.blit(title, (x + 10, y + 8))

    line_y = y + 40
    for line in event_log:
        text = font.render(line, True, WHITE)
        surface.blit(text, (x+10, line_y))
        line_y += 28


def get_card_back_image(scale_x, scale_y):
    card_w = int(BASE_CARD_W * scale_x)
    card_h = int(BASE_CARD_H * scale_y)
    back_surf = pygame.Surface((card_w, card_h))
    back_surf.fill(CARD_BACK_COLOR)
    pygame.draw.rect(back_surf, GOLD, back_surf.get_rect(), 3, border_radius=5)
    pygame.draw.line(back_surf, (200,150,100), (0,0), (card_w, card_h), 2)
    pygame.draw.line(back_surf, (200,150,100), (card_w,0), (0, card_h), 2)
    return back_surf

card_back_img = get_card_back_image(1.0, 1.0)

def draw_tiled_floor(surface, room_idx):
    light_color, dark_color = ROOM_COLORS[room_idx]
    total_gap_width = (TILE_COLS - 1) * TILE_GAP
    total_gap_height = (TILE_ROWS - 1) * TILE_GAP
    tile_width = (WIDTH - total_gap_width) // TILE_COLS
    tile_height = (HEIGHT - total_gap_height) // TILE_ROWS
    if tile_width <= 0 or tile_height <= 0:
        surface.fill(dark_color)
        return
    grid_width = TILE_COLS * tile_width + total_gap_width
    grid_height = TILE_ROWS * tile_height + total_gap_height
    start_x = (WIDTH - grid_width) // 2
    start_y = (HEIGHT - grid_height) // 2
    surface.fill(dark_color)
    for row in range(TILE_ROWS):
        for col in range(TILE_COLS):
            x = start_x + col * (tile_width + TILE_GAP)
            y = start_y + row * (tile_height + TILE_GAP)
            color = light_color if (col + row) % 2 == 0 else dark_color
            pygame.draw.rect(surface, color, (x, y, tile_width, tile_height))
            pygame.draw.rect(surface, TILE_BORDER_COLOR, (x, y, tile_width, tile_height), 1)

def draw_poker_background(surface, room_idx):
    bg_color = ROOM_COLORS[room_idx][1]
    bg_color_light = tuple(min(255, c + 20) for c in bg_color)
    surface.fill(bg_color_light)
    light_color, dark_color = ROOM_COLORS[room_idx]
    table_rect = pygame.Rect(WIDTH//4, HEIGHT//4, WIDTH//2, HEIGHT//2)
    pygame.draw.rect(surface, dark_color, table_rect, border_radius=20)
    pygame.draw.rect(surface, light_color, table_rect.inflate(-10, -10), border_radius=15)
    pygame.draw.rect(surface, GOLD, table_rect, 3, border_radius=20)

def create_walls_and_doors(scale_x, scale_y):
    global walls, doors
    door_gap_x = int(DOOR_SIZE * scale_x)
    door_gap_y = int(DOOR_SIZE * scale_y)
    wall_thick_x = int(BASE_WALL_THICK * scale_x)
    wall_thick_y = int(BASE_WALL_THICK * scale_y)
    doors = []

    if current_room == 0:
        top_left = pygame.Rect(0, 0, (WIDTH - door_gap_x) // 2, wall_thick_y)
        top_right = pygame.Rect((WIDTH + door_gap_x) // 2, 0, (WIDTH - door_gap_x) // 2, wall_thick_y)
        top_door_rect = pygame.Rect((WIDTH - door_gap_x) // 2, 0, door_gap_x, wall_thick_y)
    else:
        top_left = pygame.Rect(0, 0, WIDTH, wall_thick_y)
        top_right = None
        top_door_rect = None

    if current_room == 1:
        bottom_left = pygame.Rect(0, HEIGHT - wall_thick_y, (WIDTH - door_gap_x) // 2, wall_thick_y)
        bottom_right = pygame.Rect((WIDTH + door_gap_x) // 2, HEIGHT - wall_thick_y, (WIDTH - door_gap_x) // 2, wall_thick_y)
        bottom_door_rect = pygame.Rect((WIDTH - door_gap_x) // 2, HEIGHT - wall_thick_y, door_gap_x, wall_thick_y)
    else:
        bottom_left = pygame.Rect(0, HEIGHT - wall_thick_y, WIDTH, wall_thick_y)
        bottom_right = None
        bottom_door_rect = None

    if current_room == 2:
        left_top = pygame.Rect(0, 0, wall_thick_x, (HEIGHT - door_gap_y) // 2)
        left_bottom = pygame.Rect(0, (HEIGHT + door_gap_y) // 2, wall_thick_x, (HEIGHT - door_gap_y) // 2)
        left_door_rect = pygame.Rect(0, (HEIGHT - door_gap_y) // 2, wall_thick_x, door_gap_y)
    else:
        left_top = pygame.Rect(0, 0, wall_thick_x, HEIGHT)
        left_bottom = None
        left_door_rect = None

    if current_room == 0:
        right_top = pygame.Rect(WIDTH - wall_thick_x, 0, wall_thick_x, (HEIGHT - door_gap_y) // 2)
        right_bottom = pygame.Rect(WIDTH - wall_thick_x, (HEIGHT + door_gap_y) // 2, wall_thick_x, (HEIGHT - door_gap_y) // 2)
        right_door_rect = pygame.Rect(WIDTH - wall_thick_x, (HEIGHT - door_gap_y) // 2, wall_thick_x, door_gap_y)
    else:
        right_top = pygame.Rect(WIDTH - wall_thick_x, 0, wall_thick_x, HEIGHT)
        right_bottom = None
        right_door_rect = None

    walls = []
    if top_left: walls.append(top_left)
    if top_right: walls.append(top_right)
    if bottom_left: walls.append(bottom_left)
    if bottom_right: walls.append(bottom_right)
    if left_top: walls.append(left_top)
    if left_bottom: walls.append(left_bottom)
    if right_top: walls.append(right_top)
    if right_bottom: walls.append(right_bottom)

    if top_door_rect and current_room == 0:
        doors.append(Door(top_door_rect, 1, None))
    if bottom_door_rect and current_room == 1:
        doors.append(Door(bottom_door_rect, 0, None))
    if left_door_rect and current_room == 2:
        doors.append(Door(left_door_rect, 0, None))
    if right_door_rect and current_room == 0:
        doors.append(Door(right_door_rect, 2, None))

def recalculate_elements():
    global walls, deck_pos, card_back_img, doors, tables, npcs, obstacles, current_scale_x, current_scale_y
    current_scale_x = WIDTH / 1280.0
    current_scale_y = HEIGHT / 720.0
    player.resize(current_scale_x, current_scale_y)
    create_walls_and_doors(current_scale_x, current_scale_y)
    set_room_layout(current_room, current_scale_x, current_scale_y)
    all_colliders = walls + tables + [door.rect for door in doors] + obstacles
    for collider in all_colliders:
        if player.rect.colliderect(collider):
            overlap_left = player.rect.right - collider.left
            overlap_right = collider.right - player.rect.left
            overlap_top = player.rect.bottom - collider.top
            overlap_bottom = collider.bottom - player.rect.top
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
    player.reposition()
    deck_pos = (WIDTH * 0.1, HEIGHT * 0.5)
    card_back_img = get_card_back_image(current_scale_x, current_scale_y)

recalculate_elements()
game_state, poker_game = "main_menu", None

def near_table():
    for table in tables:
        if player.rect.colliderect(table.inflate(40, 40)):
            return True
    return False

def near_any_door():
    for door in doors:
        if player.rect.colliderect(door.rect.inflate(30, 30)):
            return door
    return None

def get_door_direction(door_rect, wall_thick_x, wall_thick_y):
    if door_rect.y == 0:
        return 'top'
    if door_rect.y == HEIGHT - wall_thick_y:
        return 'bottom'
    if door_rect.x == 0:
        return 'left'
    if door_rect.x == WIDTH - wall_thick_x:
        return 'right'
    return None

def teleport_player_through_door(exit_direction, wall_thick_x, wall_thick_y):
    entry_side = {
        'top': 'bottom', 'bottom': 'top', 'left': 'right', 'right': 'left'
    }.get(exit_direction, None)
    offset_x = player.rect.width // 2 + 10
    offset_y = player.rect.height // 2 + 10
    if entry_side == 'top':
        player.rect.centerx = WIDTH // 2
        player.rect.centery = wall_thick_y + offset_y
    elif entry_side == 'bottom':
        player.rect.centerx = WIDTH // 2
        player.rect.centery = HEIGHT - wall_thick_y - offset_y
    elif entry_side == 'left':
        player.rect.centerx = wall_thick_x + offset_x
        player.rect.centery = HEIGHT // 2
    elif entry_side == 'right':
        player.rect.centerx = WIDTH - wall_thick_x - offset_x
        player.rect.centery = HEIGHT // 2
    else:
        player.rect.center = (WIDTH // 2, HEIGHT // 2)
    player.x_ratio = player.rect.centerx / WIDTH
    player.y_ratio = player.rect.centery / HEIGHT

def load_card_image(card):
    try:
        img = pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png")
        card_w = int(BASE_CARD_W * current_scale_x)
        card_h = int(BASE_CARD_H * current_scale_y)
        return pygame.transform.smoothscale(img, (card_w, card_h))
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
    current_human = poker_game.human.hand[:]
    if len(current_human) > len(prev_human_cards):
        for i in range(len(prev_human_cards), len(current_human)):
            create_animation_for_card(current_human[i], i, 'human')
    prev_human_cards = current_human[:]
    current_boss = poker_game.boss.hand[:]
    if len(current_boss) > len(prev_boss_cards):
        for i in range(len(prev_boss_cards), len(current_boss)):
            create_animation_for_card(current_boss[i], i, 'boss')
    prev_boss_cards = current_boss[:]
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

def can_play_table(difficulty):
    """Check using global progression data."""
    if bosses_defeated[difficulty]:
        return False, "This boss has already been cleaned out!"
    if human_player.chips < ENTRY_COST[difficulty]:
        return False, f"Need ${ENTRY_COST[difficulty]} to play at this table! (You have ${human_player.chips})"
    if boss_chips[difficulty] <= 0:
        return False, "This boss has no chips left!"
    # Progression: need previous boss defeated
    if difficulty == "medium" and not bosses_defeated["easy"]:
        return False, "Old Guard: 'Beat me first before you face the Lady.'"
    if difficulty == "hard" and not bosses_defeated["medium"]:
        return False, "Sharp Lady: 'You're not ready for him yet, darling.'"
    return True, "Ready to play!"

def start_poker_game(room, intro_dialogue=True):
    global poker_game, current_boss_difficulty, boss_thinking, boss_think_start_time, boss_think_duration, show_hand_menu
    global prev_human_cards, prev_boss_cards, prev_community_cards, active_animations, animating, animating_card_keys

    if room == 0:
        diff_str = "easy"
    elif room == 1:
        diff_str = "medium"
    else:
        diff_str = "hard"

    allowed, msg = can_play_table(diff_str)
    if not allowed:
        set_boss_message(msg)
        return False

    if intro_dialogue and not table_intro_shown.get(diff_str, False):
        if room == 0:
            lines = ["You approach the worn green felt table.",
                     "The Old Guard looks up: 'So the Agency sent you, huh?'",
                     f"Cash game for your life. Let's see if you're for real.'"]
        elif room == 1:
            lines = ["The blue velvet table gleams under the dim light.",
                     "The Sharp Lady smiles: 'Impressive, you beat the Old Guard.'",
                     f"Come put your life on the line. My superiors will be watching.'"]
        else:
            lines = ["The red felt table sits ominously in the corner.",
                     "The Enforcer leans forward: 'You've made it this far, agent.'",
                     f"'You's a man or a mouse? The leader wants to meet you.'"]
        show_dialogue_screen(lines)
        table_intro_shown[diff_str] = True

    

    boss_name = BOSS_DIALOGUE[diff_str]["name"]
    boss_player = Boss(boss_name, "serious", ["easy","medium","hard"].index(diff_str)+1)
    boss_player.chips = boss_chips[diff_str]

    poker_game = ActiveGame(human_player, boss_player)
    event_log.clear()
    current_boss_difficulty = diff_str
    human_player.buffs["peekBossCardUsed"] = False

    poker_game.newHand()
    

    prev_human_cards = []
    prev_boss_cards = []
    prev_community_cards = []
    active_animations.clear()
    animating = False
    animating_card_keys.clear()
    detect_and_animate_new_cards()

    boss_message_text = None
    boss_thinking = False
    show_hand_menu = False
    return True

def start_table_dialogue(room):
    global game_state
    if start_poker_game(room, intro_dialogue=True):
        game_state = "poker"

def restart_poker_game():
    global game_state, poker_game
    if poker_game:
        human_player.chips = poker_game.human.chips
        boss_chips[current_boss_difficulty] = poker_game.boss.chips
    cleanup_poker_state()
    if start_poker_game(current_room, intro_dialogue=False):
        game_state = "poker"
    else:
        game_state = "world"

def cleanup_poker_state():
    global active_animations, animating, animating_card_keys, prev_human_cards, prev_boss_cards, prev_community_cards, boss_message_text, boss_message_timer, boss_thinking, poker_game, show_hand_menu
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
    global game_state, poker_game, boss_chips, bosses_defeated
    if poker_game is None:
        return
    if poker_game.human.chips <= 0:
        show_dialogue_screen(["You're out of chips! Your cover is blown...", "The Syndicate vanishes into the night."])
        game_state = "game_over"
        cleanup_poker_state()
    elif poker_game.boss.chips <= 0:
        human_player.chips = poker_game.human.chips
        boss_chips[current_boss_difficulty] = 0
        bosses_defeated[current_boss_difficulty] = True

        # Award poker buffs
        if current_boss_difficulty == "easy":
            human_player.buffs["fourCardStraight"] = True
        elif current_boss_difficulty == "medium":
            human_player.buffs["fourCardFlush"] = True

        show_dialogue_screen(BOSS_DIALOGUE[current_boss_difficulty]["defeat"])
        cleanup_poker_state()

        if current_boss_difficulty == "hard":
            game_state = "ending"
        else:
            game_state = "world"

def show_dialogue_screen(lines):
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
        screen.fill((0, 0, 0))
        y_offset = HEIGHT // 2 - (len(lines) * 30) // 2
        for line in lines:
            text_surf = font.render(line, True, WHITE)
            screen.blit(text_surf, (WIDTH//2 - text_surf.get_width()//2, y_offset))
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
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.size
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            recalculate_elements()

        if game_state == "main_menu":
            if new_game_btn.clicked(event):
                human_player = Player("You")
                human_player.chips = 500
                human_player.buffs = {
                    "fourCardStraight": False,
                    "fourCardFlush": False,
                    "peekBossCard": True,
                    "peekBossCardUsed": False
                }
                boss_chips = {"easy": 1000, "medium": 2000, "hard": 4000}
                bosses_defeated = {"easy": False, "medium": False, "hard": False}
                table_intro_shown = {"easy": False, "medium": False, "hard": False}
                current_room = 0
                player.x_ratio = 0.1
                player.y_ratio = 0.1
                recalculate_elements()
                story_mode_active = True
                current_story_page = 0
                game_state = "story"
            if continue_btn.clicked(event):
                if load_game():
                    game_state = "world"
                else:
                    set_boss_message("No saved game found.")
            if quit_main_btn.clicked(event):
                running = False

        if game_state == "story":
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
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
                    if current_room == 0:
                        diff_str = "easy"
                    elif current_room == 1:
                        diff_str = "medium"
                    else:
                        diff_str = "hard"
                    allowed, msg = can_play_table(diff_str)
                    if not allowed:
                        set_boss_message(msg)
                    else:
                        start_table_dialogue(current_room)
                else:
                    door = near_any_door()
                    if door:
                        # Progression checks using bosses_defeated
                        if door.target_room == 2 and not bosses_defeated["medium"]:
                            set_boss_message("Door locked! Face the Sharp Lady first.")
                            continue
                        if door.target_room == 1 and not bosses_defeated["easy"]:
                            set_boss_message("Door locked! The Old Guard blockades your path.")
                            continue

                        wall_thick_x = int(BASE_WALL_THICK * current_scale_x)
                        wall_thick_y = int(BASE_WALL_THICK * current_scale_y)
                        direction = get_door_direction(door.rect, wall_thick_x, wall_thick_y)
                        current_room = door.target_room
                        recalculate_elements()
                        if direction:
                            wall_thick_x = int(BASE_WALL_THICK * current_scale_x)
                            wall_thick_y = int(BASE_WALL_THICK * current_scale_y)
                            teleport_player_through_door(direction, wall_thick_x, wall_thick_y)

        elif game_state == "poker":
            if not animating and not boss_thinking and not show_hand_menu:
                if checkCall_btn.clicked(event):
                    callAmount = poker_game.getCallAmount(poker_game.currentPlayer)
                    if callAmount > poker_game.human.chips:
                        set_boss_message("Not enough chips to call!")
                        continue
                    if callAmount <= 0:
                        action = Action("check")
                        add_event("You Checked")
                    else:
                        action = Action("call")
                        add_event(f"You called ${callAmount}")
                    action.processAction(poker_game.currentPlayer, poker_game)
                    poker_game.playerActed = True
                    boss_thinking = True
                    boss_think_start_time = current_time
                    boss_think_duration = random.randint(500, 2000)
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["think"])
                    set_boss_message(f"{BOSS_DIALOGUE[current_boss_difficulty]['name']}: '{dialogue_option}'")
                if peek_btn.clicked(event):
                    if not human_player.buffs.get("peekBossCard", False):
                        set_boss_message("You don't have the peek buff!")
                    elif human_player.buffs.get("peekBossCardUsed", False):
                        set_boss_message("You already Used Peek this game!")
                    else:
                        human_player.buffs["peekBossCardUsed"] = True
                if raise_btn.clicked(event):
                    callAmount = poker_game.getCallAmount(poker_game.currentPlayer)
                    total_needed = callAmount + 50
                    if total_needed > poker_game.human.chips:
                        set_boss_message(f"Not enough chips to raise! Need ${total_needed}.")
                        continue
                    action = Action("raise", 50)
                    action.processAction(poker_game.currentPlayer, poker_game)
                    add_event(f"You raised to ${poker_game.currentBet}")
                    poker_game.playerActed = True
                    boss_thinking = True
                    boss_think_start_time = current_time
                    boss_think_duration = random.randint(500, 2000)
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["think"])
                    set_boss_message(f"{BOSS_DIALOGUE[current_boss_difficulty]['name']}: '{dialogue_option}'")
                if fold_btn.clicked(event):
                    action = Action("fold")
                    action.processAction(poker_game.currentPlayer, poker_game)
                    add_event("You folded")
                    poker_game.handWinner = poker_game.boss
                    poker_game.phase = "handCheck"
                    poker_game.phaseIndex = GAMEPHASE.index("handCheck")
                    poker_game.playerActed = False
                    poker_game.bossActed = False
                if leave_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    human_player.chips = poker_game.human.chips
                    boss_chips[current_boss_difficulty] = poker_game.boss.chips
                    cleanup_poker_state()
                    game_state = "world"

            if show_hand_menu and not animating:
                if play_again_btn.clicked(event):
                    restart_poker_game()
                if leave_table_btn.clicked(event):
                    human_player.chips = poker_game.human.chips
                    boss_chips[current_boss_difficulty] = poker_game.boss.chips
                    cleanup_poker_state()
                    game_state = "world"

        if event.type == pygame.KEYDOWN:
            if game_state == "poker" and poker_game is not None and poker_game.phase == "handCheck" and not animating and not boss_thinking and not show_hand_menu:
                pass

    # UPDATE
    speed_scale_x = WIDTH / 1280.0
    speed_scale_y = HEIGHT / 720.0
    player_speed_x = player.base_speed * speed_scale_x
    player_speed_y = player.base_speed * speed_scale_y
    all_colliders = walls + tables + [door.rect for door in doors] + obstacles

    if game_state == "world" and not escape_menu_active:
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * player_speed_x
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * player_speed_y
        player.move(dx, dy, all_colliders)
        for npc in npcs:
            npc.update(all_colliders, speed_scale_x, speed_scale_y)

    if game_state == "poker" and poker_game is not None:
        update_boss_message(dt)
        update_animations()

        if boss_thinking and not animating:
            if current_time - boss_think_start_time >= boss_think_duration:
                boss_name = BOSS_DIALOGUE[current_boss_difficulty]["name"]
                callAmount = poker_game.getCallAmount(poker_game.boss)
                if callAmount > poker_game.boss.chips:
                    boss_action = Action("fold")
                else:
                    boss_action = poker_game.boss.chooseAction(poker_game, poker_game.table, callAmount)

                boss_action.processAction(poker_game.boss, poker_game)
                poker_game.bossActed = True

                if boss_action.type == "fold":
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["fold"])
                    set_boss_message(f"{boss_name}: '{dialogue_option}'")
                    add_event(f"{boss_name} folded")
                    poker_game.handWinner = poker_game.human
                    poker_game.phase = "handCheck"
                    poker_game.phaseIndex = GAMEPHASE.index("handCheck")
                    poker_game.playerActed = False
                    poker_game.bossActed = False
                elif boss_action.type == "call":
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["call"])
                    set_boss_message(f"{boss_name}: '{dialogue_option}' (${callAmount})")
                    add_event(f"{boss_name} called ${callAmount}")
                elif boss_action.type == "raise":
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["raise"])
                    set_boss_message(f"{boss_name}: '{dialogue_option}' (Raise to ${poker_game.currentBet})")
                    add_event(f"{boss_name} raised to ${poker_game.currentBet}")
                elif boss_action.type == "check":
                    dialogue_option = random.choice(BOSS_DIALOGUE[current_boss_difficulty]["check"])
                    add_event(f"{boss_name} checked")
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
                if poker_game.handWinner is not None:
                    poker_game.awardPot(poker_game.handWinner)
                    winner = poker_game.handWinner
                else:
                    winner, rank = poker_game.showDown()
                poker_game.showdownDone = True
                human_player.chips = poker_game.human.chips
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

    elif game_state == "story":
        screen.fill((0, 0, 0))
        page_lines = STORY_PAGES[current_story_page]
        y_offset = HEIGHT // 2 - (len(page_lines) * 30) // 2
        for line in page_lines:
            text = font.render(line, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 40
        if current_story_page + 1 >= len(STORY_PAGES):
            prompt = "Press any key to begin"
        else:
            prompt = "Press any key to continue..."
        prompt_surf = font.render(prompt, True, LIGHT_GOLD)
        screen.blit(prompt_surf, (WIDTH//2 - prompt_surf.get_width()//2, HEIGHT*0.85))

    elif game_state == "world":
        draw_tiled_floor(screen, current_room)
        for wall in walls:
            pygame.draw.rect(screen, WALL, wall)
        for door in doors:
            mouse_over = door.rect.collidepoint(pygame.mouse.get_pos())
            color = DOOR_HIGHLIGHT if mouse_over else DOOR_COLOR
            pygame.draw.rect(screen, color, door.rect)
            pygame.draw.rect(screen, GOLD, door.rect, 2)
            if door.rect.width > door.rect.height:
                knob_pos = (door.rect.right - 10, door.rect.centery)
            else:
                knob_pos = (door.rect.centerx, door.rect.bottom - 10)
            pygame.draw.circle(screen, GOLD, knob_pos, 4)
        for table in tables:
            table_color = ROOM_COLORS[current_room][0]
            pygame.draw.rect(screen, table_color, table, border_radius=15)
            pygame.draw.rect(screen, GOLD, table, 2, border_radius=15)
        for obs in obstacles:
            pygame.draw.rect(screen, (100, 70, 40), obs)
        for npc in npcs:
            npc.draw(screen)
        player.draw(screen)

        chips_text = font.render(f"Chips: ${human_player.chips}", True, WHITE)
        screen.blit(chips_text, (WIDTH - 150, 20))

        if near_table():
            diff_str = "easy" if current_room == 0 else ("medium" if current_room == 1 else "hard")
            if bosses_defeated[diff_str]:
                prompt = "The table is empty. The boss has left."
            else:
                actual_cost = min(ENTRY_COST[diff_str], boss_chips[diff_str])
                if current_room == 0:
                    prompt = f"Press E to Play Poker (Easy)"
                elif current_room == 1:
                    if bosses_defeated["easy"]:
                        prompt = f"Press E to Play Poker (Medium)"
                    else:
                        prompt = "The Sharp Lady is ignoring you."
                else:
                    if bosses_defeated["medium"]:
                        prompt = f"Press E to Play Poker (Hard)"
                    else:
                        prompt = "The Enforcer refuses to play you."
            screen.blit(font.render(prompt, True, WHITE), (WIDTH/2 - font.size(prompt)[0]//2, HEIGHT*0.9))
        else:
            door = near_any_door()
            if door:
                if door.target_room == 2 and not bosses_defeated["medium"]:
                    prompt = "Door locked! Face the Sharp Lady first."
                elif door.target_room == 1 and not bosses_defeated["easy"]:
                    prompt = "Door locked! The Old Guard blockades your path."
                else:
                    prompt = "Press E to go through door"
                screen.blit(font.render(prompt, True, WHITE), (WIDTH/2 - font.size(prompt)[0]//2, HEIGHT*0.9))

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
        pot_txt = font.render(f"Pot: ${poker_game.table.pot}", True, WHITE)
        screen.blit(pot_txt, pot_txt.get_rect(center=(WIDTH/2, HEIGHT/10)))
        card_w = int(BASE_CARD_W * current_scale_x)
        card_h = int(BASE_CARD_H * current_scale_y)
        draw_deck(screen)
        dealer_x = 60
        dealer_y = HEIGHT * 0.12
        boss_name = BOSS_DIALOGUE[current_boss_difficulty]["name"]
        dealer_label = font.render(f"{boss_name} Chips: ${poker_game.boss.chips}", True, GOLD)
        screen.blit(dealer_label, (dealer_x, dealer_y - 30))
        if not animating and not boss_thinking and not show_hand_menu:
            callAmount = poker_game.getCallAmount(poker_game.currentPlayer)
            if callAmount <= 0:
                checkCall_btn.text = "Check"
            else:
                checkCall_btn.text = f"Call (${callAmount})"
            raise_btn.text = "Raise"
        # Draw dealer cards
        peek_revealed = human_player.buffs.get("peekBossCardUsed", False)

        for i, card in enumerate(poker_game.boss.hand):
            if ('boss', i) in animating_card_keys:
                continue
            
            if poker_game.phase == "handCheck" or (peek_revealed and i == 0):
                try:
                    img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                    screen.blit(img, (dealer_x + i*(card_w + 5), dealer_y))
                except:
                    pygame.draw.rect(screen, WHITE, (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), border_radius=5)
            else:
                pygame.draw.rect(screen, (150, 0, 0), (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), border_radius=5)
                pygame.draw.rect(screen, GOLD, (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), 2, border_radius=5)
        # Community cards
        total_community = len(poker_game.table.communityCards)
        x_comm = WIDTH/2 - (total_community * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.table.communityCards):
            if ('community', i) in animating_card_keys:
                continue
            try:
                img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                screen.blit(img, (x_comm + i*(card_w + 10), HEIGHT/2 - card_h/2))
            except:
                pygame.draw.rect(screen, WHITE, (x_comm + i*(card_w+10), HEIGHT/2 - card_h/2, card_w, card_h))
        # Human hand
        x_hand = WIDTH/2 - (2 * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.human.hand):
            if ('human', i) in animating_card_keys:
                continue
            try:
                img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                screen.blit(img, (x_hand + i*(card_w + 10), HEIGHT*0.65))
            except:
                pygame.draw.rect(screen, WHITE, (x_hand + i*(card_w+10), HEIGHT*0.65, card_w, card_h))
        for anim in active_animations:
            anim.draw(screen)
        draw_boss_message(screen)
        draw_event_log(screen)
        chips_text = font.render(f"Your Chips: ${poker_game.human.chips}", True, WHITE)
        screen.blit(chips_text, (20, HEIGHT - 40))

        if show_hand_menu and not animating:
            if boss_chips[current_boss_difficulty] > 0:
                play_again_btn.draw(screen)
            leave_table_btn.draw(screen)
            result_text = "You won the hand!" if last_hand_player_won else "You lost the hand."
            text_surf = font.render(result_text, True, GOLD)
            screen.blit(text_surf, text_surf.get_rect(center=(WIDTH/2, HEIGHT*0.75)))
        elif poker_game.phase != "handCheck" and not animating and not boss_thinking:
            buttons = [checkCall_btn, raise_btn, fold_btn, leave_btn]

            if human_player.buffs.get("peekBossCard", False) and not human_player.buffs.get("peekBossCardUsed", False):
                buttons.append(peek_btn)

            for btn in buttons:
                btn.draw(screen)
        elif boss_thinking:
            thinking_text = font.render("Boss is thinking...", True, LIGHT_GOLD)
            screen.blit(thinking_text, thinking_text.get_rect(center=(WIDTH/2, HEIGHT * 0.95)))
        if animating:
            dealing_txt = font.render("Dealing cards...", True, LIGHT_GOLD)
            screen.blit(dealing_txt, dealing_txt.get_rect(center=(WIDTH/2, HEIGHT * 0.95)))

    elif game_state == "game_over":
        screen.fill((0, 0, 0))
        lines = GAME_OVER_TEXT
        y_offset = HEIGHT // 2 - 100
        for line in lines:
            text = font.render(line, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 40
        prompt = "Press ESC to return to main menu"
        prompt_surf = font.render(prompt, True, LIGHT_GOLD)
        screen.blit(prompt_surf, (WIDTH//2 - prompt_surf.get_width()//2, HEIGHT*0.8))

    elif game_state == "ending":
        screen.fill((0, 0, 0))
        lines = ENDING_TEXT
        y_offset = HEIGHT // 2 - 120
        for line in lines:
            text = font.render(line, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 40

    pygame.display.flip()
    clock.tick(60)

pygame.quit()