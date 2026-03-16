from assets import tiles

CASINO_MAP = [

"############################",
"#............S......S......#",
"#..........................#",
"#.....TTTT.....TTTT........#",
"#.....TTTT.....TTTT........#",
"#..........................#",
"#..C..C...............N....#",
"#..........................#",
"#....B.....................#",
"#...............M..........#",
"#..........D...............#",
"#......................G...#",
"#.....P.............V......#",
"############################"

]


class Map:

    def __init__(self,tiles):

        self.tiles = CASINO_MAP
        self.tile_images = tiles

    def draw(self,screen,camera):

        for y,row in enumerate(self.tiles):

            for x,tile in enumerate(row):

                world_x = x * tiles.TILE_SIZE
                world_y = y * tiles.TILE_SIZE

                draw_x = world_x - camera.x
                draw_y = world_y - camera.y

                if tile == "#":
                    img = self.tile_images["wall"]

                elif tile == "T":
                    img = self.tile_images["table"]

                elif tile == "S":
                    img = self.tile_images["slot"]

                elif tile == "C":
                    img = self.tile_images["crate"]

                elif tile == "B":
                    img = self.tile_images["bar"]

                else:
                    img = self.tile_images["floor"]

                screen.blit(img,(draw_x,draw_y))