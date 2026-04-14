import pygame
import sys
import random
from PokerLogic import *  

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

# Tile floor settings – fixed 16x9 tiles with a 2px gap
TILE_COLS = 16
TILE_ROWS = 9
TILE_GAP = 2                     # fixed gap between tiles
TILE_BORDER_COLOR = (30, 30, 30) # dark grey border (gap color)

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
BASE_PLAYER_SIZE = 40
BASE_NPC_SIZE = 35
BASE_GUARD_SIZE = 40
BASE_TABLE_W = 120
BASE_TABLE_H = 80
BASE_CARD_W = 35   # based on min(1280,720)/20 = 720/20 = 36, approximate
BASE_CARD_H = 49   # 2.5:3.5 ratio

# FONTS
title_font = pygame.font.SysFont("arialblack", 80)
font = pygame.font.SysFont(None, 32)
boss_font = pygame.font.SysFont("arialblack", 28)

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
        """Update player size based on independent axis scaling."""
        width = int(BASE_PLAYER_SIZE * scale_x)
        height = int(BASE_PLAYER_SIZE * scale_y)
        self.rect.size = (width, height)
        self.reposition()

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def move(self, dx, dy, colliders):
        """Move with collision detection and resolution (separate axes)."""
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
            self.direction = random.choice([(1,0),(-1,0),(0,1),(0,-1),(0,0)])
            self.timer = random.randint(30, 120)
        
        dx = self.direction[0] * self.base_speed * speed_scale_x
        dy = self.direction[1] * self.base_speed * speed_scale_y
        
        # Horizontal movement
        self.rect.x += dx
        for collider in colliders:
            if self.rect.colliderect(collider):
                if dx > 0:
                    self.rect.right = collider.left
                elif dx < 0:
                    self.rect.left = collider.right
        
        # Vertical movement
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

class Guard:
    def __init__(self, x_ratio, y_ratio):
        self.x_ratio, self.y_ratio = x_ratio, y_ratio
        self.rect = pygame.Rect(0, 0, BASE_GUARD_SIZE, BASE_GUARD_SIZE)

    def resize(self, scale_x, scale_y):
        width = int(BASE_GUARD_SIZE * scale_x)
        height = int(BASE_GUARD_SIZE * scale_y)
        self.rect.size = (width, height)
        self.reposition()

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def draw(self, surface):
        pygame.draw.rect(surface, GUARD_COLOR, self.rect)

class Door:
    def __init__(self, rect, target_room, spawn_pos):
        self.rect = rect
        self.target_room = target_room
        self.spawn_pos = spawn_pos

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
npcs = []
guards = []

def set_room_layout(room_idx, scale_x, scale_y):
    """Set up tables, npcs, guards for the given room with independent axis scaling."""
    global tables, npcs, guards
    table_w = int(BASE_TABLE_W * scale_x)
    table_h = int(BASE_TABLE_H * scale_y)
    
    if room_idx == 0:
        tables = [
            pygame.Rect(WIDTH*0.3, HEIGHT*0.3, table_w, table_h),
            pygame.Rect(WIDTH*0.6, HEIGHT*0.5, table_w, table_h)
        ]
        npcs = [NPC(0.2, 0.3), NPC(0.4, 0.5), NPC(0.7, 0.2)]
        guards = [Guard(0.8, 0.3), Guard(0.84, 0.3)]
    elif room_idx == 1:
        tables = [
            pygame.Rect(WIDTH*0.2, HEIGHT*0.6, table_w, table_h),
            pygame.Rect(WIDTH*0.7, HEIGHT*0.2, table_w, table_h)
        ]
        npcs = []
        guards = []
    else:  # room_idx == 2
        tables = [
            pygame.Rect(WIDTH*0.5, HEIGHT*0.4, table_w, table_h),
            pygame.Rect(WIDTH*0.8, HEIGHT*0.7, table_w, table_h)
        ]
        npcs = []
        guards = []
    
    # Apply scaling to NPCs and Guards
    for n in npcs:
        n.resize(scale_x, scale_y)
    for g in guards:
        g.resize(scale_x, scale_y)

# --------------------------------------------------
# INITIALIZATION & RESIZING
# --------------------------------------------------
player = WorldPlayer()
walls = []
doors = []
current_room = 0
current_scale_x = 1.0
current_scale_y = 1.0

# Main Buttons
start_story = Button("Start Story", 0.5, 0.4, 0.3, 0.08)
free_play = Button("Free Play", 0.5, 0.55, 0.3, 0.08)
quit_button = Button("Quit", 0.5, 0.7, 0.3, 0.08)

# Poker Buttons 
checkCall_btn = Button("Check/Call", 0.2, 0.9, 0.15, 0.06)
raise_btn = Button("Raise (50$)", 0.4, 0.9, 0.15, 0.06)
fold_btn = Button("Fold", 0.6, 0.9, 0.15, 0.06)
leave_btn = Button("Leave", 0.8, 0.9, 0.15, 0.06)

# Animation globals
deck_pos = (WIDTH * 0.1, HEIGHT * 0.5)
active_animations = []
animating = False
animating_card_keys = set()  # (type, index) where type = 'human', 'boss', 'community'

# Boss message system
boss_message_text = None
boss_message_timer = 0  # milliseconds remaining

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

def draw_tiled_floor(surface, room_idx):
    """
    Draw a 16x9 tile grid with a fixed 2px gap between tiles.
    Tile sizes are computed as integers, and the whole grid is centered.
    Any leftover area is filled with the dark tile color (hidden by walls).
    """
    light_color, dark_color = ROOM_COLORS[room_idx]
    
    # Available space for tiles (excluding gaps)
    total_gap_width = (TILE_COLS - 1) * TILE_GAP
    total_gap_height = (TILE_ROWS - 1) * TILE_GAP
    
    tile_width = (WIDTH - total_gap_width) // TILE_COLS
    tile_height = (HEIGHT - total_gap_height) // TILE_ROWS
    
    # If tile dimensions are zero or negative, fallback to simple fill
    if tile_width <= 0 or tile_height <= 0:
        surface.fill(dark_color)
        return
    
    # Total size of the drawn grid
    grid_width = TILE_COLS * tile_width + total_gap_width
    grid_height = TILE_ROWS * tile_height + total_gap_height
    
    # Center the grid
    start_x = (WIDTH - grid_width) // 2
    start_y = (HEIGHT - grid_height) // 2
    
    # Fill background with the dark tile color (edges will be covered by walls)
    surface.fill(dark_color)
    
    # Draw tiles
    for row in range(TILE_ROWS):
        for col in range(TILE_COLS):
            x = start_x + col * (tile_width + TILE_GAP)
            y = start_y + row * (tile_height + TILE_GAP)
            # Chessboard pattern
            color = light_color if (col + row) % 2 == 0 else dark_color
            pygame.draw.rect(surface, color, (x, y, tile_width, tile_height))
            # Draw a thin dark line around each tile to ensure crispness
            pygame.draw.rect(surface, TILE_BORDER_COLOR, (x, y, tile_width, tile_height), 1)

def create_walls_and_doors(scale_x, scale_y):
    """
    Create wall segments with gaps only on the walls that should have doors,
    based on the current room. Sizes scale independently per axis.
    """
    global walls, doors
    door_gap_x = int(DOOR_SIZE * scale_x)   # width of horizontal door gaps
    door_gap_y = int(DOOR_SIZE * scale_y)   # height of vertical door gaps
    wall_thick_x = int(BASE_WALL_THICK * scale_x)
    wall_thick_y = int(BASE_WALL_THICK * scale_y)
    doors = []

    # Top wall: horizontal, thickness uses scale_y, width uses scale_x
    if current_room == 0:
        top_left = pygame.Rect(0, 0, (WIDTH - door_gap_x) // 2, wall_thick_y)
        top_right = pygame.Rect((WIDTH + door_gap_x) // 2, 0, (WIDTH - door_gap_x) // 2, wall_thick_y)
        top_door_rect = pygame.Rect((WIDTH - door_gap_x) // 2, 0, door_gap_x, wall_thick_y)
    else:
        top_left = pygame.Rect(0, 0, WIDTH, wall_thick_y)
        top_right = None
        top_door_rect = None

    # Bottom wall
    if current_room == 1:
        bottom_left = pygame.Rect(0, HEIGHT - wall_thick_y, (WIDTH - door_gap_x) // 2, wall_thick_y)
        bottom_right = pygame.Rect((WIDTH + door_gap_x) // 2, HEIGHT - wall_thick_y, (WIDTH - door_gap_x) // 2, wall_thick_y)
        bottom_door_rect = pygame.Rect((WIDTH - door_gap_x) // 2, HEIGHT - wall_thick_y, door_gap_x, wall_thick_y)
    else:
        bottom_left = pygame.Rect(0, HEIGHT - wall_thick_y, WIDTH, wall_thick_y)
        bottom_right = None
        bottom_door_rect = None

    # Left wall: vertical, thickness uses scale_x, height uses scale_y
    if current_room == 2:
        left_top = pygame.Rect(0, 0, wall_thick_x, (HEIGHT - door_gap_y) // 2)
        left_bottom = pygame.Rect(0, (HEIGHT + door_gap_y) // 2, wall_thick_x, (HEIGHT - door_gap_y) // 2)
        left_door_rect = pygame.Rect(0, (HEIGHT - door_gap_y) // 2, wall_thick_x, door_gap_y)
    else:
        left_top = pygame.Rect(0, 0, wall_thick_x, HEIGHT)
        left_bottom = None
        left_door_rect = None

    # Right wall
    if current_room == 0:
        right_top = pygame.Rect(WIDTH - wall_thick_x, 0, wall_thick_x, (HEIGHT - door_gap_y) // 2)
        right_bottom = pygame.Rect(WIDTH - wall_thick_x, (HEIGHT + door_gap_y) // 2, wall_thick_x, (HEIGHT - door_gap_y) // 2)
        right_door_rect = pygame.Rect(WIDTH - wall_thick_x, (HEIGHT - door_gap_y) // 2, wall_thick_x, door_gap_y)
    else:
        right_top = pygame.Rect(WIDTH - wall_thick_x, 0, wall_thick_x, HEIGHT)
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
    global walls, deck_pos, card_back_img, doors, tables, npcs, guards, current_scale_x, current_scale_y
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
    
    player.reposition()
    deck_pos = (WIDTH * 0.1, HEIGHT * 0.5)
    card_back_img = get_card_back_image(current_scale_x, current_scale_y)

# Initial setup (default 1280x720)
recalculate_elements()
game_state, poker_game = "menu", None

def near_table():
    for table in tables:
        if player.rect.colliderect(table.inflate(40, 40)): return True
    return False

def near_any_door():
    for door in doors:
        if player.rect.colliderect(door.rect.inflate(30, 30)):
            return door
    return None

def get_door_direction(door_rect, wall_thick_x, wall_thick_y):
    """Return 'top', 'bottom', 'left', or 'right' based on door position."""
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
        # Scale independently using current_scale_x, current_scale_y
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

        if game_state == "menu":
            if start_story.clicked(event): game_state = "story"
            if free_play.clicked(event): game_state = "world"
            if quit_button.clicked(event): running = False

        elif game_state == "poker":
            # Allow player actions only if not animating (boss message doesn't block)
            if not animating:
                if checkCall_btn.clicked(event):
                    # finds the amount that the player needs to call
                    callAmount = poker_game.getCallAmount(poker_game.currentPlayer)

                    if callAmount <= 0:
                        action = Action("check")
                    else:
                        action = Action("call")

                    action.processAction(poker_game.currentPlayer, poker_game)
                    poker_game.playerActed = True

                    # temporary boss check/call logic
                    bossCallAmount = poker_game.getCallAmount(poker_game.boss)

                    if bossCallAmount <= 0:
                        bossAction = Action("check")
                        set_boss_message("Boss: Check")
                    else:
                        bossAction = Action("call")
                        set_boss_message(f"Boss: Call ${bossCallAmount}")

                    bossAction.processAction(poker_game.boss, poker_game)
                    poker_game.bossActed = True

                if raise_btn.clicked(event):
                    action = Action("raise", 50)
                    action.processAction(poker_game.currentPlayer, poker_game)
                    poker_game.playerActed = True

                    # temporary boss logic
                    bossAction = Action("call")
                    set_boss_message("Boss: Call $50")
                    bossAction.processAction(poker_game.boss, poker_game)
                    poker_game.bossActed = True

                if fold_btn.clicked(event):
                    action = Action("fold")
                    action.processAction(poker_game.currentPlayer, poker_game)                

                    poker_game.handWinner = poker_game.boss
                    poker_game.phase = "handCheck"
                    poker_game.phaseIndex = GAMEPHASE.index("handCheck")
                    poker_game.playerActed = False
                    poker_game.bossActed = False
                    set_boss_message("Boss: Wins (Player folded)")
                    
                if leave_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    game_state = "world"
                    active_animations.clear()
                    animating = False
                    animating_card_keys.clear()
                    prev_human_cards = []
                    prev_boss_cards = []
                    prev_community_cards = []
                    boss_message_text = None
                    boss_message_timer = 0

        if event.type == pygame.KEYDOWN:
            # starts a new hand after handCheck
            if game_state == "poker" and poker_game is not None and poker_game.phase == "handCheck" and not animating:
                poker_game.newHand()
                prev_human_cards = []
                prev_boss_cards = []
                prev_community_cards = []
                active_animations.clear()
                animating_card_keys.clear()
                detect_and_animate_new_cards()
                boss_message_text = None

            if event.key == pygame.K_ESCAPE and game_state != "poker": 
                game_state = "menu"

            if event.key == pygame.K_e and game_state == "world":
                # Check for table interaction first (higher priority)
                if near_table():
                    human_player = Player("You")
                    boss_player = Boss("Boss", "easy", 2)
                    poker_game = ActiveGame(human_player, boss_player)
                    poker_game.newHand()
                    prev_human_cards = []
                    prev_boss_cards = []
                    prev_community_cards = []
                    active_animations.clear()
                    animating = False
                    animating_card_keys.clear()
                    detect_and_animate_new_cards()
                    boss_message_text = None
                    game_state = "poker"
                else:
                    # Door interaction
                    door = near_any_door()
                    if door:
                        # Get scaled wall thickness
                        wall_thick_x = int(BASE_WALL_THICK * current_scale_x)
                        wall_thick_y = int(BASE_WALL_THICK * current_scale_y)
                        direction = get_door_direction(door.rect, wall_thick_x, wall_thick_y)
                        # Teleport to other room
                        current_room = door.target_room
                        # Recalculate walls and doors for new room
                        recalculate_elements()
                        # Now place the player just inside the new room, on the opposite side
                        if direction:
                            wall_thick_x = int(BASE_WALL_THICK * current_scale_x)
                            wall_thick_y = int(BASE_WALL_THICK * current_scale_y)
                            teleport_player_through_door(direction, wall_thick_x, wall_thick_y)

    # UPDATE
    # Compute speed scales for player and NPCs based on window dimensions
    speed_scale_x = WIDTH / 1280.0
    speed_scale_y = HEIGHT / 720.0
    player_speed_x = player.base_speed * speed_scale_x
    player_speed_y = player.base_speed * speed_scale_y
    
    all_colliders = walls + tables + [g.rect for g in guards] + [door.rect for door in doors]
    if game_state == "world":
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * player_speed_x
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * player_speed_y
        player.move(dx, dy, all_colliders)
        for npc in npcs: 
            npc.update(all_colliders, speed_scale_x, speed_scale_y)

    if game_state == "poker" and poker_game is not None:
        # Update boss message timer
        update_boss_message(dt)

        # Update animations (movement)
        update_animations()

        # Only advance game logic when not animating (boss message does not block game logic)
        if not animating:
            # betting round completeness check
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

    # DRAW
    if game_state == "menu":
        screen.fill(TABLE_GREEN)
        title = title_font.render("TEXAS HOLD'EM", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH/2, HEIGHT*0.2)))
        for btn in [start_story, free_play, quit_button]: btn.draw(screen)

    elif game_state == "story":
        screen.fill((0, 0, 0))
        lines = ["Rain hits the pavement.", "Someone tipped you about a poker game.", "Not a casino.", "A basement poker den.", "", "Press ESC to return."]
        for i, line in enumerate(lines):
            text = font.render(line, True, WHITE); screen.blit(text, text.get_rect(center=(WIDTH/2, HEIGHT*0.2 + i*(HEIGHT/10))))

    elif game_state == "world":
        draw_tiled_floor(screen, current_room)
        for wall in walls:
            pygame.draw.rect(screen, WALL, wall)
        for door in doors:
            # Draw door as a button-like object (but collidable)
            mouse_over = door.rect.collidepoint(pygame.mouse.get_pos())
            color = DOOR_HIGHLIGHT if mouse_over else DOOR_COLOR
            pygame.draw.rect(screen, color, door.rect)
            pygame.draw.rect(screen, GOLD, door.rect, 2)
            # Add a simple door knob
            if door.rect.width > door.rect.height:  # top or bottom door (horizontal)
                knob_pos = (door.rect.right - 10, door.rect.centery)
            else:  # left or right door (vertical)
                knob_pos = (door.rect.centerx, door.rect.bottom - 10)
            pygame.draw.circle(screen, GOLD, knob_pos, 4)
        for table in tables:
            pygame.draw.rect(screen, TABLE_GREEN, table, border_radius=15)
        for npc in npcs:
            npc.draw(screen)
        for guard in guards:
            guard.draw(screen)
        player.draw(screen)
        
        # Show interaction prompts
        if near_table():
            prompt = font.render("Press E to Play Poker", True, WHITE)
            screen.blit(prompt, prompt.get_rect(center=(WIDTH/2, HEIGHT*0.9)))
        else:
            door = near_any_door()
            if door:
                prompt = font.render("Press E to go through door", True, WHITE)
                screen.blit(prompt, prompt.get_rect(center=(WIDTH/2, HEIGHT*0.9)))
    
    elif game_state == "poker":
        screen.fill(TABLE_GREEN)
        pot_txt = font.render(f"Pot: ${poker_game.table.pot}", True, WHITE); screen.blit(pot_txt, pot_txt.get_rect(center=(WIDTH/2, HEIGHT/10)))

        card_w = int(BASE_CARD_W * current_scale_x)
        card_h = int(BASE_CARD_H * current_scale_y)
        
        draw_deck(screen)

        # --- DEALER HAND ---
        dealer_x = 60
        dealer_y = HEIGHT * 0.12
        dealer_label = font.render("Boss:", True, GOLD)
        screen.blit(dealer_label, (dealer_x, dealer_y - 30))

        # --- Update Button Text ----
        if not animating:
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
                    img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
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
                img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                screen.blit(img, (x_comm + i*(card_w + 10), HEIGHT/2 - card_h/2))
            except: 
                pygame.draw.rect(screen, WHITE, (x_comm + i*(card_w+10), HEIGHT/2 - card_h/2, card_w, card_h))

        # Human Player Hand (skip animating ones)
        x_hand = WIDTH/2 - (2 * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.human.hand):
            if ('human', i) in animating_card_keys:
                continue
            try:
                img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                screen.blit(img, (x_hand + i*(card_w + 10), HEIGHT*0.65))
            except: 
                pygame.draw.rect(screen, WHITE, (x_hand + i*(card_w+10), HEIGHT*0.65, card_w, card_h))

        # Draw flying animations
        for anim in active_animations:
            anim.draw(screen)

        # Draw boss action message
        draw_boss_message(screen)

        # Only draw poker buttons if not in handCheck and not animating
        if poker_game.phase != "handCheck" and not animating:
            for btn in [checkCall_btn, raise_btn, fold_btn, leave_btn]:
                btn.draw(screen)

        # display the message telling player to press any button to continue at the end of a hand
        if poker_game.phase == "handCheck" and not animating:
            displayTxt = font.render("Press any key for next hand", True, WHITE)
            screen.blit(displayTxt, displayTxt.get_rect(center = (WIDTH/2, HEIGHT * 0.85)))
                
        if animating:
            dealing_txt = font.render("Dealing cards...", True, LIGHT_GOLD)
            screen.blit(dealing_txt, dealing_txt.get_rect(center=(WIDTH/2, HEIGHT * 0.95)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()