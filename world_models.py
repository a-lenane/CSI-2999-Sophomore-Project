from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from game_constants import HEIGHT, PLAYER_SIZE, TILE_SIZE, WIDTH


@dataclass
class DialogueWindow:
    title: str
    text: str

    def draw(self, screen, title_font, font):
        rect = pygame.Rect(WIDTH // 2 - 290, HEIGHT - 220, 580, 180)
        pygame.draw.rect(screen, (20, 20, 26), rect, border_radius=12)
        pygame.draw.rect(screen, (230, 230, 230), rect, 2, border_radius=12)
        title = title_font.render(self.title, True, (255, 222, 145))
        screen.blit(title, (rect.x + 16, rect.y + 14))
        y = rect.y + 56
        for line in self.text.split("\n"):
            surf = font.render(line, True, (240, 240, 240))
            screen.blit(surf, (rect.x + 16, y))
            y += 26


@dataclass
class Warp:
    x: int
    y: int
    target_area: str
    target_pos: tuple[int, int]
    label: str

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, TILE_SIZE, TILE_SIZE)


@dataclass
class NPC:
    npc_id: str
    name: str
    sprite_key: str
    x: int
    y: int
    role: str
    dialogue: str
    difficulty: str = "easy"
    active: bool = True

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)


@dataclass
class Area:
    area_id: str
    name: str
    palette: tuple[int, int, int]
    spawn: tuple[int, int]
    warps: list[Warp] = field(default_factory=list)
    npcs: list[NPC] = field(default_factory=list)
    props: list[tuple[str, int, int]] = field(default_factory=list)
