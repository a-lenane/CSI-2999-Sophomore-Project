from __future__ import annotations

from pathlib import Path

import pygame
from PIL import Image


class SpriteLoader:
    def __init__(self, asset_root: str = ".", tile_size: int = 64):
        self.asset_root = Path(asset_root)
        self.tile_size = tile_size
        self._raw_cache: dict[str, pygame.Surface] = {}
        self._scaled_cache: dict[tuple[str, int], pygame.Surface] = {}
        self._player_cache: dict[int, dict[str, list[pygame.Surface]]] = {}

    def get_tile(self, name: str) -> pygame.Surface:
        # Not used for player, but kept for compatibility
        raise NotImplementedError("Use load_player_frames or load_table_sprite")

    def load_player_frames(self, tile_size: int | None = None) -> dict[str, list[pygame.Surface]]:
        target_size = tile_size or self.tile_size
        if target_size in self._player_cache:
            return self._player_cache[target_size]

        sheet = self._load_image("player_sheet", self.asset_root / "player.png")
        cols = 4
        rows = 4

        rows_data: list[list[pygame.Surface]] = []
        for row in range(rows):
            current_row: list[pygame.Surface] = []
            for col in range(cols):
                rect = self._grid_frame_rect(sheet, cols, rows, col, row)
                frame = self._prepare_player_frame(
                    sheet.subsurface(rect).copy(),
                    frame_width=rect.width,
                    frame_height=rect.height,
                )
                current_row.append(
                    pygame.transform.scale(frame, (target_size, target_size))
                )
            rows_data.append(current_row)

        walk_down = rows_data[0]
        walk_left = rows_data[1]
        walk_up = rows_data[2]
        walk_up_alt = rows_data[3]
        walk_right = [pygame.transform.flip(frame, True, False) for frame in walk_left]

        frames = {
            "idle_down": [walk_down[0]],
            "walk_down": walk_down,
            "idle_left": [walk_left[0]],
            "walk_left": walk_left,
            "idle_right": [walk_right[0]],
            "walk_right": walk_right,
            "idle_up": [walk_up[0]],
            "walk_up": walk_up,
            "walk_up_alt": walk_up_alt,
        }
        self._player_cache[target_size] = frames
        return frames

    def load_table_sprite(self, width: int, height: int) -> pygame.Surface:
        """Load and scale the poker table image."""
        img = self._load_image("poker_table", self.asset_root / "poker_table.png")
        return pygame.transform.scale(img, (width, height))

    def load_dealer_sprite(self, name: str, width: int, height: int) -> pygame.Surface:
        """Load a dealer sprite (dealer.png or boss.png) and scale it."""
        img = self._load_image(name, self.asset_root / name)
        return pygame.transform.scale(img, (width, height))

    def _load_image(self, name: str, path: Path) -> pygame.Surface:
        if name not in self._raw_cache:
            if not path.exists():
                raise FileNotFoundError(f"Missing asset: {path}")
            try:
                surface = pygame.image.load(str(path))
            except pygame.error:
                # Fallback to Pillow for PNG/JPEG
                with Image.open(path) as image:
                    converted = image.convert("RGBA")
                    surface = pygame.image.fromstring(
                        converted.tobytes(),
                        converted.size,
                        converted.mode,
                    )
            surface = self._convert_surface(surface)
            self._raw_cache[name] = surface
        return self._raw_cache[name]

    @staticmethod
    def _convert_surface(surface: pygame.Surface) -> pygame.Surface:
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            return surface.convert_alpha()
        return surface

    @staticmethod
    def _trim_surface(surface: pygame.Surface) -> pygame.Surface:
        mask = pygame.mask.from_surface(surface)
        bounding = mask.get_bounding_rects()
        if not bounding:
            return surface
        rect = bounding[0].copy()
        for extra in bounding[1:]:
            rect.union_ip(extra)
        return surface.subsurface(rect).copy()

    @staticmethod
    def _pad_surface(surface: pygame.Surface, padding: int = 1) -> pygame.Surface:
        padded = pygame.Surface(
            (surface.get_width() + padding * 2, surface.get_height() + padding * 2),
            pygame.SRCALPHA,
        )
        padded.blit(surface, (padding, padding))
        return padded

    @staticmethod
    def _grid_frame_rect(
        sheet: pygame.Surface,
        cols: int,
        rows: int,
        col: int,
        row: int,
    ) -> pygame.Rect:
        x0 = round(col * sheet.get_width() / cols)
        x1 = round((col + 1) * sheet.get_width() / cols)
        y0 = round(row * sheet.get_height() / rows)
        y1 = round((row + 1) * sheet.get_height() / rows)
        return pygame.Rect(x0, y0, x1 - x0, y1 - y0)

    @staticmethod
    def _matches_background(color: pygame.Color, background_colors: list[tuple[int, int, int]], tolerance: int = 38) -> bool:
        return any(
            abs(color.r - bg[0]) <= tolerance
            and abs(color.g - bg[1]) <= tolerance
            and abs(color.b - bg[2]) <= tolerance
            for bg in background_colors
        )

    @staticmethod
    def _looks_like_checkerboard_background(color: pygame.Color) -> bool:
        brightness = (color.r + color.g + color.b) / 3
        saturation = max(color.r, color.g, color.b) - min(color.r, color.g, color.b)
        return brightness >= 160 and saturation <= 34

    @classmethod
    def _strip_border_background(cls, surface: pygame.Surface) -> pygame.Surface:
        cleaned = surface.copy()
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            cleaned = cleaned.convert_alpha()
        width, height = cleaned.get_size()
        sample_points = {
            (0, 0),
            (1, 0),
            (0, 1),
            (width - 1, 0),
            (width - 2, 0),
            (width - 1, 1),
            (0, height - 1),
            (1, height - 1),
            (0, height - 2),
            (width - 1, height - 1),
            (width - 2, height - 1),
            (width - 1, height - 2),
        }
        background_colors = [cleaned.get_at(point)[:3] for point in sample_points]
        stack = []
        visited: set[tuple[int, int]] = set()

        for x in range(width):
            stack.append((x, 0))
            stack.append((x, height - 1))
        for y in range(height):
            stack.append((0, y))
            stack.append((width - 1, y))

        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            visited.add((x, y))
            color = cleaned.get_at((x, y))
            is_background = cls._matches_background(
                color,
                background_colors,
            ) or cls._looks_like_checkerboard_background(color)
            if color.a == 0 or not is_background:
                continue
            cleaned.set_at((x, y), (color.r, color.g, color.b, 0))
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    stack.append((nx, ny))

        return cleaned

    @classmethod
    def _prepare_sprite_surface(cls, surface: pygame.Surface) -> pygame.Surface:
        return cls._pad_surface(cls._trim_surface(cls._strip_border_background(surface)))

    @classmethod
    def _prepare_player_frame(
        cls,
        surface: pygame.Surface,
        *,
        frame_width: int,
        frame_height: int,
    ) -> pygame.Surface:
        cleaned = cls._prepare_sprite_surface(surface)
        canvas = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
        draw_rect = cleaned.get_rect(midbottom=(frame_width // 2, frame_height - 2))
        canvas.blit(cleaned, draw_rect)
        return canvas