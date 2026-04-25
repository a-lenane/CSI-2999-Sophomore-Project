from __future__ import annotations

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from level_generator import DOOR, GeneratedLevel, ROOM_TILE_BY_THEME, SPAWN, WALL, generate_casino_level
from sprite_loader import SpriteLoader


class SpriteSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.loader = SpriteLoader(tile_size=64)

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_required_tiles_load(self) -> None:
        for name in SpriteLoader.TILE_FILES:
            surface = self.loader.get_tile(name)
            self.assertEqual(surface.get_size(), (64, 64))

    def test_player_sheet_slicing(self) -> None:
        frames = self.loader.load_player_frames()
        for key in ("walk_down", "walk_left", "walk_right", "walk_up"):
            self.assertEqual(len(frames[key]), 4)
            for frame in frames[key]:
                self.assertEqual(frame.get_size(), (64, 64))
        self.assertEqual(len(frames["idle_down"]), 1)
        self.assertEqual(len(frames["idle_up"]), 1)

    def test_tilesheet_objects_are_present(self) -> None:
        objects = self.loader.load_tilesheet_objects()
        for name in ("brick_wall", "slot_machine", "green_rug", "poker_table", "crates", "bar"):
            self.assertIn(name, objects)
            self.assertGreater(objects[name].get_width(), 0)
            self.assertGreater(objects[name].get_height(), 0)

    def test_sprite_sheet_background_edges_are_cleaned(self) -> None:
        frames = self.loader.load_player_frames(tile_size=96)
        for animation in frames.values():
            for frame in animation:
                width, height = frame.get_size()
                edge_points = (
                    (0, 0),
                    (width - 1, 0),
                    (0, height - 1),
                    (width - 1, height - 1),
                )
                for point in edge_points:
                    self.assertEqual(frame.get_at(point).a, 0)

        objects = self.loader.load_tilesheet_objects()
        for name in ("slot_machine", "poker_table", "crates", "bar"):
            surface = objects[name]
            self.assertEqual(surface.get_at((0, 0)).a, 0)

    def test_generation_boundaries_and_spawn(self) -> None:
        level = generate_casino_level(seed=11)
        self.assertIsInstance(level, GeneratedLevel)
        width = len(level.grid[0])
        height = len(level.grid)
        self.assertEqual(level.grid[level.spawn_point[1]][level.spawn_point[0]], SPAWN)

        for x in range(width):
            self.assertEqual(level.grid[0][x], WALL)
            self.assertEqual(level.grid[height - 1][x], WALL)
        for y in range(height):
            self.assertEqual(level.grid[y][0], WALL)
            self.assertEqual(level.grid[y][width - 1], WALL)

    def test_rooms_have_themed_tiles_and_doors(self) -> None:
        level = generate_casino_level(seed=3)
        room_names = {room.name for room in level.rooms}
        self.assertTrue({"table", "bar", "office", "vault"}.issubset(room_names))
        for room in level.rooms:
            expected_tile = ROOM_TILE_BY_THEME[room.theme]
            self.assertEqual(level.grid[room.y][room.x], expected_tile)
            self.assertEqual(level.grid[room.door[1]][room.door[0]], DOOR)

    def test_seed_is_reproducible_and_changes_layout(self) -> None:
        first = generate_casino_level(seed=9)
        second = generate_casino_level(seed=9)
        third = generate_casino_level(seed=10)
        self.assertEqual(first.grid, second.grid)
        self.assertNotEqual(first.grid, third.grid)

    def test_props_do_not_overlap_or_cover_doors(self) -> None:
        level = generate_casino_level(seed=17)
        occupied: set[tuple[int, int]] = set()
        for prop in level.props:
            for y in range(prop.y, prop.y + prop.height):
                for x in range(prop.x, prop.x + prop.width):
                    tile = level.grid[y][x]
                    self.assertNotEqual(tile, WALL)
                    self.assertNotEqual(tile, DOOR)
                    if prop.blocks_movement:
                        self.assertNotIn((x, y), occupied)
                        occupied.add((x, y))

    def test_table_zones_exist(self) -> None:
        level = generate_casino_level(seed=13)
        self.assertGreaterEqual(len(level.table_zones), 1)
        for zone in level.table_zones:
            self.assertIn(zone.difficulty, {"medium", "hard"})


if __name__ == "__main__":
    unittest.main()
