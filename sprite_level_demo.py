from __future__ import annotations

import argparse
from dataclasses import dataclass

import pygame

from level_generator import DOOR, LOBBY_FLOOR, OFFICE_FLOOR, SPAWN, SERVICE_FLOOR, VAULT_FLOOR, GeneratedLevel, generate_casino_level
from sprite_loader import SpriteLoader


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 768
TILE_SIZE = 64
PLAYER_SPEED = 220
BG_COLOR = (18, 12, 10)
ZONE_COLORS = {
    "medium": (76, 175, 80),
    "hard": (244, 67, 54),
}


@dataclass
class Player:
    x: float
    y: float
    width: int
    height: int
    frames: dict[str, list[pygame.Surface]]
    direction: str = "down"
    moving: bool = False
    frame_index: float = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, collisions: set[tuple[int, int]]) -> None:
        dx = 0.0
        dy = 0.0
        if keys[pygame.K_a]:
            dx -= PLAYER_SPEED * dt
        if keys[pygame.K_d]:
            dx += PLAYER_SPEED * dt
        if keys[pygame.K_w]:
            dy -= PLAYER_SPEED * dt
        if keys[pygame.K_s]:
            dy += PLAYER_SPEED * dt

        self.moving = dx != 0 or dy != 0
        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
        elif dy != 0:
            self.direction = "down" if dy > 0 else "up"

        self.x = _move_axis(self.rect, dx, axis="x", collisions=collisions)
        self.y = _move_axis(self.rect, dy, axis="y", collisions=collisions)

        if self.moving:
            self.frame_index = (self.frame_index + 8 * dt) % len(self.frames[f"walk_{self.direction}"])
        else:
            self.frame_index = 0.0

    def current_frame(self) -> pygame.Surface:
        key = f"walk_{self.direction}" if self.moving else f"idle_{self.direction}"
        frames = self.frames[key]
        return frames[int(self.frame_index) % len(frames)]


def _move_axis(
    rect: pygame.Rect,
    delta: float,
    axis: str,
    collisions: set[tuple[int, int]],
) -> float:
    if delta == 0:
        return getattr(rect, axis)

    trial = rect.copy()
    step = 1 if delta > 0 else -1
    for _ in range(abs(int(round(delta)))):
        if axis == "x":
            trial.x += step
        else:
            trial.y += step
        if _is_colliding(trial, collisions):
            if axis == "x":
                trial.x -= step
                return float(trial.x)
            trial.y -= step
            return float(trial.y)

    return float(trial.x if axis == "x" else trial.y)


def _is_colliding(rect: pygame.Rect, collisions: set[tuple[int, int]]) -> bool:
    left = rect.left // TILE_SIZE
    right = (rect.right - 1) // TILE_SIZE
    top = rect.top // TILE_SIZE
    bottom = (rect.bottom - 1) // TILE_SIZE
    for tile_y in range(top, bottom + 1):
        for tile_x in range(left, right + 1):
            if (tile_x, tile_y) in collisions:
                return True
    return False


def draw_level(
    screen: pygame.Surface,
    level: GeneratedLevel,
    loader: SpriteLoader,
    camera: pygame.Vector2,
    object_surfaces: dict[str, pygame.Surface],
) -> None:
    tile_map = {
        LOBBY_FLOOR: loader.get_tile("wood_floor_warm"),
        SERVICE_FLOOR: loader.get_tile("wood_floor_dark"),
        OFFICE_FLOOR: loader.get_tile("office_floor"),
        VAULT_FLOOR: loader.get_tile("vault_floor"),
        SPAWN: loader.get_tile("wood_floor_warm"),
        DOOR: loader.get_tile("door_service"),
    }
    wall_surface = pygame.transform.scale(object_surfaces["brick_wall"], (TILE_SIZE, TILE_SIZE))

    for y, row in enumerate(level.grid):
        for x, tile in enumerate(row):
            position = (x * TILE_SIZE - camera.x, y * TILE_SIZE - camera.y)
            if tile == "W":
                screen.blit(wall_surface, position)
            else:
                screen.blit(tile_map[tile], position)

    for prop in level.props:
        if prop.name in SpriteLoader.TILE_FILES:
            surf = loader.get_tile(prop.name)
            surf = pygame.transform.scale(surf, (prop.width * TILE_SIZE, prop.height * TILE_SIZE))
        else:
            surf = pygame.transform.scale(
                object_surfaces[prop.name],
                (prop.width * TILE_SIZE, prop.height * TILE_SIZE),
            )
        position = (prop.x * TILE_SIZE - camera.x, prop.y * TILE_SIZE - camera.y)
        screen.blit(surf, position)

    for zone in level.table_zones:
        rect = pygame.Rect(
            zone.x * TILE_SIZE - camera.x,
            zone.y * TILE_SIZE - camera.y,
            zone.width * TILE_SIZE,
            zone.height * TILE_SIZE,
        )
        color = ZONE_COLORS.get(zone.difficulty, (255, 255, 255))
        pygame.draw.rect(screen, color, rect, 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone sprite loader and casino level demo")
    parser.add_argument("--seed", type=int, default=7, help="Deterministic seed for the generated layout")
    args = parser.parse_args()

    pygame.init()
    pygame.display.set_caption("Casino Sprite Loader Demo")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)

    loader = SpriteLoader(tile_size=TILE_SIZE)
    object_surfaces = loader.load_tilesheet_objects()
    player_frames = loader.load_player_frames()
    level = generate_casino_level(seed=args.seed)

    spawn_x, spawn_y = level.spawn_point
    player = Player(
        x=spawn_x * TILE_SIZE + 8,
        y=spawn_y * TILE_SIZE + 6,
        width=TILE_SIZE - 16,
        height=TILE_SIZE - 12,
        frames=player_frames,
    )

    world_pixel_width = len(level.grid[0]) * TILE_SIZE
    world_pixel_height = len(level.grid) * TILE_SIZE
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.update(dt, keys, level.collision_tiles)
        camera = pygame.Vector2(
            max(0, min(player.x - SCREEN_WIDTH / 2, world_pixel_width - SCREEN_WIDTH)),
            max(0, min(player.y - SCREEN_HEIGHT / 2, world_pixel_height - SCREEN_HEIGHT)),
        )

        screen.fill(BG_COLOR)
        draw_level(screen, level, loader, camera, object_surfaces)
        screen.blit(player.current_frame(), (player.x - camera.x, player.y - camera.y))

        info = font.render("WASD to move | colored outlines mark generated table zones", True, (240, 230, 210))
        screen.blit(info, (18, 18))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
