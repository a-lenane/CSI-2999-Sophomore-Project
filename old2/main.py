import pygame
import sys
from map import Map
from player import Player as OverworldPlayer
from camera import Camera
import npc
from poker_gui import PokerGame
from Buffs import Player as BuffPlayer

# Initialize Pygame
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Casino Hold'em RPG")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 36)
small_font = pygame.font.SysFont("Arial", 20)

# Fallback asset loader
def load_fallback_image(color, width=48, height=48):
    surf = pygame.Surface((width, height))
    surf.fill(color)
    return surf

# Initialize Overworld Elements
tiles = {
    "wall": load_fallback_image((100, 100, 100)),
    "floor": load_fallback_image((50, 0, 0)),
    "table": load_fallback_image((0, 150, 0)),
}

game_map = Map()
player_sprite = load_fallback_image((0, 0, 255))
npc_sprite = load_fallback_image((255, 0, 0))

overworld_player = OverworldPlayer(200, 200, player_sprite)
camera = Camera()
npcs = [npc.NPC(500, 300, npc_sprite), npc.NPC(700, 400, npc_sprite)]

# Initialize Player RPG Profile
rpg_player = BuffPlayer("Gambler")

# Game States
state = "MENU"
current_poker_game = None
table_difficulty_map = {"E": "easy", "M": "medium", "H": "hard"}
current_table_difficulty = None
error_message = ""
error_timer = 0

running = True
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False
        
        if state == "MENU":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                state = "OVERWORLD"
                
        elif state == "OVERWORLD":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                table_type = game_map.is_near_table(overworld_player.x, overworld_player.y)
                if table_type:
                    difficulty = table_difficulty_map.get(table_type)
                    if difficulty:
                        can_play, message = rpg_player.can_play_table(difficulty)
                        if can_play:
                            current_table_difficulty = difficulty
                            current_poker_game = PokerGame(screen, rpg_player, difficulty=difficulty)
                            state = "POKER"
                        else:
                            error_message = message
                            error_timer = 120  # Show for 2 seconds

    # --- STATE: START MENU ---
    if state == "MENU":
        screen.fill((20, 20, 20))
        title = font.render("CASINO HOLD'EM RPG", True, (255, 215, 0))
        prompt = font.render("Press ENTER to Start", True, (255, 255, 255))
        controls = small_font.render("WASD to move | E to interact with tables", True, (200, 200, 200))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 250))
        screen.blit(controls, (SCREEN_WIDTH//2 - controls.get_width()//2, 350))

    # --- STATE: OVERWORLD ---
    elif state == "OVERWORLD":
        keys = pygame.key.get_pressed()
        overworld_player.move(keys)
        
        for n in npcs:
            n.update()
            
        camera.update(overworld_player)
        screen.fill((0, 0, 0))
        game_map.draw(screen, camera)
        
        for n in npcs:
            n.draw(screen, camera)
            
        overworld_player.draw(screen, camera)

        # Draw player chips
        chips_text = small_font.render(f"Chips: {rpg_player.chips}", True, (255, 215, 0))
        screen.blit(chips_text, (10, 10))
        
        # Draw buffs
        buff_y = 35
        for i, buff in enumerate(rpg_player.buffs):
            buff_text = small_font.render(f"✓ {buff}", True, (100, 255, 100))
            screen.blit(buff_text, (10, buff_y + i * 18))
        
        # Interaction Prompt
        table_type = game_map.is_near_table(overworld_player.x, overworld_player.y)
        if table_type:
            difficulty = table_difficulty_map.get(table_type, "unknown")
            requirements = {"E": "100 chips", "M": "300 chips + beat Easy", "H": "800 chips + beat Medium"}
            prompt_text = f"Press 'E' to play {difficulty.upper()} table (Requires: {requirements.get(table_type, '???')})"
            prompt = small_font.render(prompt_text, True, (255, 255, 255))
            screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT - 50))
        
        # Draw error message
        if error_timer > 0:
            error_timer -= 1
            error_surf = small_font.render(error_message, True, (255, 100, 100))
            screen.blit(error_surf, (SCREEN_WIDTH//2 - error_surf.get_width()//2, SCREEN_HEIGHT - 100))

    # --- STATE: POKER GUI ---
    elif state == "POKER":
        action = current_poker_game.update(events)
        current_poker_game.draw()
        
        if action == "LEAVE":
            state = "OVERWORLD"
            current_poker_game = None
            current_table_difficulty = None

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()