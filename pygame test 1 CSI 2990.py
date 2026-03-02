import sys

import pygame

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Texas Hold'em: High Stakes")

clock = pygame.time.Clock()

# Colors
TABLE_GREEN = (6, 71, 42)
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
LIGHT_GOLD = (255, 215, 0)

# Fonts
title_font = pygame.font.SysFont("arialblack", 80)
button_font = pygame.font.SysFont("arial", 40)

# Game state
game_state = "menu"

class Button:
    def __init__(self, text, y):
        self.text = text
        self.rect = pygame.Rect(WIDTH//2 - 150, y, 300, 60)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()

        color = GOLD
        if self.rect.collidepoint(mouse_pos):
            color = LIGHT_GOLD

        pygame.draw.rect(surface, color, self.rect, border_radius=10)

        text_surf = button_font.render(self.text, True, TABLE_GREEN)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


start_story = Button("Start Story", 250)
free_play = Button("Free Play", 330)
quit_button = Button("Quit", 410)

running = True
while running:
    screen.fill(TABLE_GREEN)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "menu":
            if start_story.clicked(event):
                game_state = "story"
            if free_play.clicked(event):
                game_state = "game"
            if quit_button.clicked(event):
                running = False

    if game_state == "menu":
        # Title
        title = title_font.render("TEXAS HOLD'EM", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH//2, 150)))

        start_story.draw(screen)
        free_play.draw(screen)
        quit_button.draw(screen)

    elif game_state == "story":
        text = button_font.render("Story Mode Coming Soon...", True, WHITE)
        screen.blit(text, (250, 300))

    elif game_state == "game":
        text = button_font.render("Free Play Mode", True, WHITE)
        screen.blit(text, (320, 300))

    pygame.display.flip()
    clock.tick(60)

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Casino World")

clock = pygame.time.Clock()

# Colors
FLOOR = (40, 40, 40)
WALL = (20, 20, 20)
TABLE = (6, 71, 42)
PLAYER_COLOR = (200, 50, 50)
WHITE = (255, 255, 255)

font = pygame.font.SysFont(None, 32)

# Player
player_size = 40
player = pygame.Rect(100, 100, player_size, player_size)
player_speed = 5

# Walls
walls = [
    pygame.Rect(0, 0, WIDTH, 40),                # Top wall
    pygame.Rect(0, 0, 40, HEIGHT),               # Left wall
    pygame.Rect(0, HEIGHT-40, WIDTH, 40),       # Bottom
    pygame.Rect(WIDTH-40, 0, 40, HEIGHT),       # Right
]

# Poker Tables
tables = [
    pygame.Rect(300, 200, 120, 80),
    pygame.Rect(600, 400, 120, 80),
]

def move_player(dx, dy):
    player.x += dx
    for wall in walls:
        if player.colliderect(wall):
            player.x -= dx

    player.y += dy
    for wall in walls:
        if player.colliderect(wall):
            player.y -= dy

def near_table():
    for table in tables:
        if player.colliderect(table.inflate(40, 40)):
            return table
    return None

running = True
game_state = "world"

while running:
    screen.fill(FLOOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e and game_state == "world":
                if near_table():
                    game_state = "poker"

            if event.key == pygame.K_ESCAPE:
                game_state = "world"

    keys = pygame.key.get_pressed()

    if game_state == "world":
        dx = dy = 0
        if keys[pygame.K_w]: dy = -player_speed
        if keys[pygame.K_s]: dy = player_speed
        if keys[pygame.K_a]: dx = -player_speed
        if keys[pygame.K_d]: dx = player_speed

        move_player(dx, dy)

    # Draw walls
    for wall in walls:
        pygame.draw.rect(screen, WALL, wall)

    # Draw tables
    for table in tables:
        pygame.draw.rect(screen, TABLE, table, border_radius=20)

    # Draw player
    pygame.draw.rect(screen, PLAYER_COLOR, player)

    # Interaction prompt
    if game_state == "world" and near_table():
        text = font.render("Press E to Play Poker", True, WHITE)
        screen.blit(text, (player.x - 20, player.y - 30))

    if game_state == "poker":
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        text = font.render("Poker Table (Press ESC to Leave)", True, WHITE)
        screen.blit(text, (350, 300))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

