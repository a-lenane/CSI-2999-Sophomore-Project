from __future__ import annotations

import os

import pygame

from PokerLogic import RANK, SUIT
from game_constants import ASSET_DIR, CARD_UI_DIR, NPC_SPRITE_BOX, PLAYER_SPRITE_BOX


def load_image(path):
    if not os.path.exists(path):
        return None
    try:
        return pygame.image.load(path)
    except pygame.error:
        return None


def crop_surface(surface, rect):
    out = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    out.blit(surface, (0, 0), rect)
    return out


def scale_to_fit(surface, width, height):
    if surface is None:
        return None
    sw, sh = surface.get_size()
    if sw == 0 or sh == 0:
        return surface
    ratio = min(width / sw, height / sh)
    size = (max(1, int(sw * ratio)), max(1, int(sh * ratio)))
    return pygame.transform.smoothscale(surface, size)


def remove_bg_color(surface, tolerance=20):
    surface = surface.convert_alpha()
    bg = surface.get_at((0, 0))
    w, h = surface.get_size()
    for y in range(h):
        for x in range(w):
            c = surface.get_at((x, y))
            if abs(c.r - bg.r) <= tolerance and abs(c.g - bg.g) <= tolerance and abs(c.b - bg.b) <= tolerance:
                surface.set_at((x, y), (0, 0, 0, 0))
    return surface


def load_tiles_prop(path, rect, target_size=None):
    image = load_image(path)
    if image is None:
        return None
    image = image.convert()
    prop = crop_surface(image, rect)
    prop = remove_bg_color(prop)
    if target_size is not None:
        prop = scale_to_fit(prop, *target_size)
    return prop


class SpriteSheet:
    def __init__(self, path, target_size):
        self.target_size = target_size
        self.frames = {"down": [], "right": [], "up": []}
        self.ready = False
        self.load(path)

    def expand_rect(self, rect, max_width, max_height, padding=10):
        left = max(0, rect.x - padding)
        top = max(0, rect.y - padding)
        right = min(max_width, rect.right + padding)
        bottom = min(max_height, rect.bottom + padding)
        return pygame.Rect(left, top, right - left, bottom - top)

    def union_bounds(self, frames, padding=10):
        bounds = None
        for frame in frames:
            rect = frame.get_bounding_rect()
            if rect.width == 0 or rect.height == 0:
                continue
            bounds = rect if bounds is None else bounds.union(rect)
        if bounds is None:
            return pygame.Rect(0, 0, frames[0].get_width(), frames[0].get_height())
        return self.expand_rect(bounds, frames[0].get_width(), frames[0].get_height(), padding)

    def remove_bg(self, surface, tolerance=26):
        surface = surface.convert_alpha()
        bg = surface.get_at((0, 0))
        w, h = surface.get_size()
        for y in range(h):
            for x in range(w):
                c = surface.get_at((x, y))
                if abs(c.r - bg.r) <= tolerance and abs(c.g - bg.g) <= tolerance and abs(c.b - bg.b) <= tolerance:
                    surface.set_at((x, y), (0, 0, 0, 0))
        return surface

    def prepare(self, frame, clip_rect):
        frame = self.remove_bg(frame)
        if clip_rect.width == 0 or clip_rect.height == 0:
            return frame
        frame = crop_surface(frame, (clip_rect.x, clip_rect.y, clip_rect.width, clip_rect.height))
        return scale_to_fit(frame, *self.target_size)

    def load(self, path):
        image = load_image(path)
        if image is None:
            return
        image = image.convert()
        cols, rows = 4, 4
        fw = image.get_width() // cols
        fh = image.get_height() // rows
        rows_out = []
        for row in range(rows):
            raw_frames = []
            for col in range(cols):
                frame = crop_surface(image, (col * fw, row * fh, fw, fh))
                raw_frames.append(frame)
            clip_rect = self.union_bounds([self.remove_bg(frame.copy()) for frame in raw_frames])
            row_frames = [self.prepare(frame, clip_rect) for frame in raw_frames]
            rows_out.append(row_frames)
        self.frames["down"] = rows_out[0]
        self.frames["right"] = rows_out[1]
        self.frames["up"] = rows_out[2]
        self.ready = True

    def get_frame(self, direction, index):
        if not self.ready:
            return None
        if direction == "left":
            base = self.frames["right"][index % 4]
            return pygame.transform.flip(base, True, False)
        return self.frames.get(direction, self.frames["down"])[index % 4]


class Assets:
    def __init__(self):
        self.player_sheet = SpriteSheet(os.path.join(ASSET_DIR, "player.jpeg"), PLAYER_SPRITE_BOX)
        self.gambler_sheet = SpriteSheet(os.path.join(ASSET_DIR, "gambler.jpeg"), NPC_SPRITE_BOX)
        self.dealer_sheet = SpriteSheet(os.path.join(ASSET_DIR, "dealer.jpeg"), NPC_SPRITE_BOX)
        self.boss_sheet = SpriteSheet(os.path.join(ASSET_DIR, "Boss.jpeg"), NPC_SPRITE_BOX)
        self.table_sprite = load_tiles_prop(os.path.join(ASSET_DIR, "tiles.png"), (768, 256, 256, 512), (170, 118))
        self.card_faces = self.load_card_faces()

    def card_asset_name(self, rank, suit):
        return f"{rank}_of_{suit}.png"

    def load_card_faces(self):
        out = {}
        for suit in SUIT:
            for rank in RANK:
                path = os.path.join(CARD_UI_DIR, self.card_asset_name(rank, suit))
                image = load_image(path)
                if image is not None:
                    out[(rank, suit)] = image.convert_alpha()
        return out
