import pygame
import sys

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