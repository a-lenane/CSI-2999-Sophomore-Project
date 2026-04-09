import pygame

CASINO_MAP = [
"############################",
"#............E......M......#",
"#..........................#",
"#..........................#",
"#..........................#",
"#..........................#",
"#..........................#",
"#..........................#",
"#..........................#",
"#..........................#",
"#..........................#",
"#..........................#",
"#............H.............#",
"############################"
]

class Map:
    def __init__(self, tile_size=48):
        self.tiles = CASINO_MAP
        self.TILE_SIZE = tile_size

    def get_tile_at(self, x, y):
        grid_x, grid_y = int(x // self.TILE_SIZE), int(y // self.TILE_SIZE)
        if 0 <= grid_y < len(self.tiles) and 0 <= grid_x < len(self.tiles[0]):
            return self.tiles[grid_y][grid_x]
        return "#"

    def is_near_table(self, px, py):
        grid_x, grid_y = int(px // self.TILE_SIZE), int(py // self.TILE_SIZE)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                tile = self.get_tile_at((grid_x + dx) * self.TILE_SIZE, (grid_y + dy) * self.TILE_SIZE)
                if tile in ['E', 'M', 'H']:
                    return tile
        return None

    def draw(self, screen, camera):
        colors = {"#": (60, 60, 60), "E": (0, 150, 0), "M": (0, 100, 200), "H": (200, 50, 50), ".": (30, 30, 30)}
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                rect = (x * self.TILE_SIZE - camera.x, y * self.TILE_SIZE - camera.y, self.TILE_SIZE, self.TILE_SIZE)
                pygame.draw.rect(screen, colors.get(tile, (20, 20, 20)), rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)