import pygame

TILE_SIZE = 64

def load_tiles():

    sheet = pygame.image.load("assets/tiles.png").convert_alpha()

    tiles = {"floor": sheet.subsurface((0, 0, 64, 64)), "wall": sheet.subsurface((64, 0, 64, 64)),
             "table": sheet.subsurface((128, 0, 64, 64)), "slot": sheet.subsurface((192, 0, 64, 64)),
             "crate": sheet.subsurface((256, 0, 64, 64)), "bar": sheet.subsurface((320, 0, 64, 64))}

    return tiles