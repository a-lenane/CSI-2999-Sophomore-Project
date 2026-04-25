from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import random


WALL = "W"
LOBBY_FLOOR = "L"
SERVICE_FLOOR = "S"
OFFICE_FLOOR = "O"
VAULT_FLOOR = "V"
DOOR = "D"
SPAWN = "P"


ROOM_TILE_BY_THEME = {
    "table": LOBBY_FLOOR,
    "bar": SERVICE_FLOOR,
    "storage": SERVICE_FLOOR,
    "office": OFFICE_FLOOR,
    "vault": VAULT_FLOOR,
}


@dataclass(frozen=True)
class Room:
    name: str
    theme: str
    x: int
    y: int
    width: int
    height: int
    door: tuple[int, int]


@dataclass(frozen=True)
class PropPlacement:
    name: str
    x: int
    y: int
    width: int
    height: int
    blocks_movement: bool = True


@dataclass(frozen=True)
class TableZone:
    x: int
    y: int
    width: int
    height: int
    difficulty: str


@dataclass(frozen=True)
class GeneratedLevel:
    grid: list[list[str]]
    rooms: list[Room]
    props: list[PropPlacement]
    spawn_point: tuple[int, int]
    table_zones: list[TableZone]
    collision_tiles: set[tuple[int, int]]


def generate_casino_level(width: int = 28, height: int = 18, seed: int | None = None) -> GeneratedLevel:
    if width < 24 or height < 16:
        raise ValueError("Level dimensions must be at least 24x16 for the structured layout")

    rng = random.Random(seed)
    grid = [[WALL for _ in range(width)] for _ in range(height)]
    corridor_center = height // 2
    corridor_top = corridor_center - 1
    corridor_bottom = corridor_center + 1

    for y in range(corridor_top, corridor_bottom + 1):
        for x in range(1, width - 1):
            grid[y][x] = LOBBY_FLOOR

    room_names = ["table", "bar", "office", "vault"]
    add_storage = width >= 30 and height >= 18
    if add_storage:
        room_names.append("storage")
    rng.shuffle(room_names)

    top_band_height = corridor_top - 1
    bottom_band_y = corridor_bottom + 2
    bottom_band_height = height - bottom_band_y - 1

    top_x_ranges = _split_columns(width, 2)
    bottom_x_ranges = _split_columns(width, 2 if not add_storage else 3)

    assignments = [
        (room_names[0], "top", top_x_ranges[0]),
        (room_names[1], "top", top_x_ranges[1]),
        (room_names[2], "bottom", bottom_x_ranges[0]),
        (room_names[3], "bottom", bottom_x_ranges[1]),
    ]
    if add_storage:
        assignments.append((room_names[4], "bottom", bottom_x_ranges[2]))

    rooms: list[Room] = []
    for name, side, (section_start, section_end) in assignments:
        if side == "top":
            room = _build_room(
                name=name,
                rng=rng,
                section_start=section_start,
                section_end=section_end,
                top_limit=1,
                bottom_limit=top_band_height,
                corridor_y=corridor_top,
                place_above=True,
            )
        else:
            room = _build_room(
                name=name,
                rng=rng,
                section_start=section_start,
                section_end=section_end,
                top_limit=bottom_band_y,
                bottom_limit=bottom_band_y + bottom_band_height - 1,
                corridor_y=corridor_bottom + 1,
                place_above=False,
            )
        rooms.append(room)
        _carve_room(grid, room)

    spawn_point = (width // 2, corridor_center)
    grid[spawn_point[1]][spawn_point[0]] = SPAWN

    props, table_zones = _place_props(rooms, rng)
    collision_tiles = _build_collision_tiles(grid, props)

    _validate_connectivity(grid, spawn_point, collision_tiles)
    return GeneratedLevel(
        grid=grid,
        rooms=rooms,
        props=props,
        spawn_point=spawn_point,
        table_zones=table_zones,
        collision_tiles=collision_tiles,
    )


def _split_columns(width: int, sections: int) -> list[tuple[int, int]]:
    usable_start = 2
    usable_end = width - 3
    usable_width = usable_end - usable_start + 1
    base = usable_width // sections
    remainder = usable_width % sections
    ranges: list[tuple[int, int]] = []
    cursor = usable_start
    for index in range(sections):
        part = base + (1 if index < remainder else 0)
        ranges.append((cursor, cursor + part - 1))
        cursor += part
    return ranges


def _build_room(
    name: str,
    rng: random.Random,
    section_start: int,
    section_end: int,
    top_limit: int,
    bottom_limit: int,
    corridor_y: int,
    place_above: bool,
) -> Room:
    max_width = min(8, section_end - section_start - 1)
    min_width = min(5, max_width)
    width = rng.randint(min_width, max_width)
    room_x = rng.randint(section_start, max(section_start, section_end - width + 1))

    band_height = bottom_limit - top_limit + 1
    max_height = min(5, band_height - 1)
    min_height = min(4, max_height)
    height = rng.randint(min_height, max_height)

    if place_above:
        room_y = max(top_limit, bottom_limit - height + 1)
        door_y = corridor_y
    else:
        room_y = min(bottom_limit - height + 1, top_limit)
        door_y = corridor_y

    door_x = rng.randint(room_x + 1, room_x + width - 2)
    theme = name if name in ROOM_TILE_BY_THEME else "service"
    return Room(name=name, theme=theme, x=room_x, y=room_y, width=width, height=height, door=(door_x, door_y))


def _carve_room(grid: list[list[str]], room: Room) -> None:
    floor_code = ROOM_TILE_BY_THEME[room.theme]
    for y in range(room.y, room.y + room.height):
        for x in range(room.x, room.x + room.width):
            grid[y][x] = floor_code
    door_x, door_y = room.door
    grid[door_y][door_x] = DOOR


def _place_props(rooms: list[Room], rng: random.Random) -> tuple[list[PropPlacement], list[TableZone]]:
    props: list[PropPlacement] = []
    table_zones: list[TableZone] = []
    occupied: set[tuple[int, int]] = set()

    def mark(prop: PropPlacement) -> None:
        props.append(prop)
        if prop.blocks_movement:
            for py in range(prop.y, prop.y + prop.height):
                for px in range(prop.x, prop.x + prop.width):
                    occupied.add((px, py))

    for room in rooms:
        if room.name == "table":
            rug = PropPlacement("green_rug", room.x + 1, room.y + 1, min(4, room.width - 2), min(3, room.height - 2), False)
            mark(rug)
            table_width = 3
            table_height = 2
            table_x = room.x + max(1, (room.width - table_width) // 2)
            table_y = room.y + max(1, (room.height - table_height) // 2)
            table = PropPlacement("poker_table", table_x, table_y, table_width, table_height, True)
            mark(table)
            table_zones.append(TableZone(table_x, table_y, table_width, table_height, "medium"))
            if room.width >= 7:
                alt_x = room.x + room.width - table_width - 1
                alt_y = room.y + 1
                if _prop_fits(room, alt_x, alt_y, table_width, table_height, occupied):
                    side_table = PropPlacement("poker_table", alt_x, alt_y, table_width, table_height, True)
                    mark(side_table)
                    table_zones.append(TableZone(alt_x, alt_y, table_width, table_height, "hard"))
        elif room.name == "bar":
            bar = PropPlacement("bar", room.x + max(1, room.width - 5), room.y + 1, 4, 2, True)
            if _prop_fits(room, bar.x, bar.y, bar.width, bar.height, occupied):
                mark(bar)
            slot = PropPlacement("slot_machine", room.x + 1, room.y + max(1, room.height - 3), 1, 2, True)
            if _prop_fits(room, slot.x, slot.y, slot.width, slot.height, occupied):
                mark(slot)
        elif room.name == "office":
            desk = PropPlacement("bar", room.x + 1, room.y + 1, 4, 2, True)
            if _prop_fits(room, desk.x, desk.y, desk.width, desk.height, occupied):
                mark(desk)
        elif room.name == "vault":
            stairs = PropPlacement("stairs_gold", room.x + 1, room.y + 1, 1, 1, False)
            mark(stairs)
            crates = PropPlacement("crates", room.x + max(1, room.width - 3), room.y + max(1, room.height - 3), 2, 2, True)
            if _prop_fits(room, crates.x, crates.y, crates.width, crates.height, occupied):
                mark(crates)
        elif room.name == "storage":
            crates = PropPlacement("crates", room.x + 1, room.y + 1, 2, 2, True)
            if _prop_fits(room, crates.x, crates.y, crates.width, crates.height, occupied):
                mark(crates)
            extra_slot = PropPlacement("slot_machine", room.x + room.width - 2, room.y + 1, 1, 2, True)
            if _prop_fits(room, extra_slot.x, extra_slot.y, extra_slot.width, extra_slot.height, occupied):
                mark(extra_slot)

    return props, table_zones


def _prop_fits(
    room: Room,
    x: int,
    y: int,
    width: int,
    height: int,
    occupied: set[tuple[int, int]],
) -> bool:
    if x < room.x + 1 or y < room.y + 1:
        return False
    if x + width > room.x + room.width - 1:
        return False
    if y + height > room.y + room.height - 1:
        return False
    for py in range(y, y + height):
        for px in range(x, x + width):
            if (px, py) in occupied:
                return False
    return True


def _build_collision_tiles(
    grid: list[list[str]],
    props: list[PropPlacement],
) -> set[tuple[int, int]]:
    collisions = set()
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile == WALL:
                collisions.add((x, y))
    for prop in props:
        if not prop.blocks_movement:
            continue
        for py in range(prop.y, prop.y + prop.height):
            for px in range(prop.x, prop.x + prop.width):
                collisions.add((px, py))
    return collisions


def _validate_connectivity(
    grid: list[list[str]],
    spawn_point: tuple[int, int],
    collision_tiles: set[tuple[int, int]],
) -> None:
    width = len(grid[0])
    height = len(grid)
    queue = deque([spawn_point])
    seen = {spawn_point}

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in seen or (nx, ny) in collision_tiles:
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))

    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile != WALL and (x, y) not in collision_tiles and (x, y) not in seen:
                raise ValueError(f"Generated unreachable walkable tile at {(x, y)}")
