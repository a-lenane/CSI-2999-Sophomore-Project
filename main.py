import pygame
from assets.tiles import load_tiles
from map import Map
from player import Player
import npc
from camera import Camera
import GAMELOGIC # TODO setup for 'entering' a game with this document

pygame.init()

screen = pygame.display.set_mode((900,600))
clock = pygame.time.Clock()

tiles = load_tiles()

player_sprite = pygame.image.load("assets/player.png").convert_alpha()
npc_sprite = pygame.image.load("assets/npc.png").convert_alpha()

game_map = Map(tiles)

player = Player(200,200,player_sprite)

npcs = [
    npc.NPC(500, 300, npc_sprite),
    npc.NPC(700, 400, npc_sprite)
]

camera = Camera()

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    player.move(keys)

    for npc in npcs:
        npc.update()

    camera.update(player)

    screen.fill((0,0,0))

    game_map.draw(screen,camera)

    for npc in npcs:
        npc.draw(screen,camera)

    player.draw(screen,camera)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()