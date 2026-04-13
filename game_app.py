from __future__ import annotations

import sys

import pygame

from asset_pipeline import Assets
from game_constants import (
    HEIGHT,
    PLAYER_SIZE,
    SCENE_GAME_OVER,
    SCENE_INTRO,
    SCENE_MENU,
    SCENE_POKER,
    SCENE_WORLD,
    TILE_SIZE,
    WIDTH,
    WORLD_COLS,
    WORLD_ROWS,
)
from game_profile import PlayerProfile
from poker_match import PokerTableMatch
from world_models import Area, DialogueWindow, NPC, Warp


class Player:
    def __init__(self, sprite_sheet):
        self.sprite_sheet = sprite_sheet
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.direction = "down"
        self.anim = 0

    def place(self, x, y):
        self.rect.topleft = (x, y)

    def move(self, keys, blockers):
        dx = dy = 0
        speed = 4
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= speed
            self.direction = "left"
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += speed
            self.direction = "right"
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= speed
            self.direction = "up"
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += speed
            self.direction = "down"
        moved = dx or dy
        if moved:
            self.anim = (self.anim + 1) % 32
        next_rect = self.rect.move(dx, 0)
        if not any(next_rect.colliderect(b) for b in blockers):
            self.rect = next_rect
        next_rect = self.rect.move(0, dy)
        if not any(next_rect.colliderect(b) for b in blockers):
            self.rect = next_rect

        world_rect = pygame.Rect(0, 0, WORLD_COLS * TILE_SIZE, WORLD_ROWS * TILE_SIZE)
        self.rect.clamp_ip(world_rect)

    def draw(self, screen, cam_x, cam_y):
        pygame.draw.ellipse(screen, (0, 0, 0, 80), (self.rect.x - cam_x - 4, self.rect.y - cam_y + 18, 42, 16))
        frame = self.sprite_sheet.get_frame(self.direction, (self.anim // 8) % 4)
        if frame is not None:
            bob = 2 if (self.anim // 8) % 2 else 0
            x = self.rect.x - cam_x + PLAYER_SIZE // 2 - frame.get_width() // 2
            y = self.rect.y - cam_y + PLAYER_SIZE - frame.get_height() - bob
            screen.blit(frame, (x, y))
        pygame.draw.rect(screen, (95, 180, 255), (self.rect.x - cam_x, self.rect.y - cam_y, PLAYER_SIZE, PLAYER_SIZE), 2, 6)


class Menu:
    def __init__(self, game):
        self.game = game
        self.options = ["Start Game", "Quit"]
        self.selected = 0
        self.font = pygame.font.SysFont(None, 54)

    def handle_input(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % len(self.options)
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % len(self.options)
        elif event.key == pygame.K_RETURN:
            if self.selected == 0:
                self.game.start_new_game()
            else:
                self.game.player_profile.save()
                pygame.quit()
                sys.exit()

    def draw(self, screen):
        screen.fill((10, 12, 16))
        title = self.font.render("Casino District Poker", True, (255, 228, 150))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        subtitle = pygame.font.SysFont(None, 26).render("Enter start | H hints in world | R reset save", True, (180, 180, 180))
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 225))
        for idx, option in enumerate(self.options):
            color = (255, 220, 100) if idx == self.selected else (220, 220, 220)
            surf = self.font.render(option, True, color)
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 320 + idx * 80))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Casino District Poker")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.font = pygame.font.SysFont(None, 26)
        self.small_font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 34)
        self.title_font = pygame.font.SysFont(None, 42)

        self.menu = Menu(self)
        self.scene = SCENE_MENU
        self.player_profile = PlayerProfile.load()
        self.player = Player(self.assets.player_sheet)
        self.current_area = None
        self.areas = {}
        self.dialogue = None
        self.game_over_reason = ""
        self.match = None
        self.intro_pages = [
            ["The district doesn't fight fair."],
            ["Every locked room is a table.", "Every table wants your chips."],
            ["Beat the bosses at poker.", "Take the whole block."],
        ]
        self.intro_index = 0

    def start_new_game(self):
        self.player_profile = PlayerProfile()
        self.player_profile.save()
        self.areas = self.build_areas()
        self.current_area = "lounge"
        self.player.place(*self.areas[self.current_area].spawn)
        self.dialogue = None
        self.match = None
        self.scene = SCENE_INTRO
        self.intro_index = 0

    def build_areas(self):
        lounge = Area("lounge", "Velvet Lounge", (76, 56, 42), (TILE_SIZE * 2, TILE_SIZE * 8))
        lounge.npcs = [
            NPC("lounge_boss", "Mara", "dealer", TILE_SIZE * 8, TILE_SIZE * 3, "boss", "You want the alley? Beat me first.", "easy"),
            NPC("bartender", "Silas", "dealer", TILE_SIZE * 11, TILE_SIZE * 7, "talk", "Beat bosses and choose the edge you want. That is how this district remembers winners."),
        ]
        lounge.warps = [Warp(TILE_SIZE * 13, TILE_SIZE * 5, "alley", (TILE_SIZE * 1, TILE_SIZE * 5), "To Alley")]

        alley = Area("alley", "Back Alley", (54, 60, 72), (TILE_SIZE * 1, TILE_SIZE * 5))
        alley.npcs = [
            NPC("alley_boss", "Rook", "gambler", TILE_SIZE * 8, TILE_SIZE * 4, "boss", "You don't get into the vault on borrowed luck.", "medium"),
        ]
        alley.warps = [
            Warp(TILE_SIZE * 1, TILE_SIZE * 5, "lounge", (TILE_SIZE * 12, TILE_SIZE * 5), "Back To Lounge"),
            Warp(TILE_SIZE * 13, TILE_SIZE * 4, "vault", (TILE_SIZE * 1, TILE_SIZE * 4), "To Vault"),
        ]

        vault = Area("vault", "Cash Room", (52, 72, 60), (TILE_SIZE * 1, TILE_SIZE * 4))
        vault.npcs = [
            NPC("vault_boss", "Ivy", "dealer", TILE_SIZE * 8, TILE_SIZE * 4, "boss", "The office opens when I say it opens.", "medium"),
        ]
        vault.warps = [
            Warp(TILE_SIZE * 1, TILE_SIZE * 4, "alley", (TILE_SIZE * 12, TILE_SIZE * 4), "Back To Alley"),
            Warp(TILE_SIZE * 13, TILE_SIZE * 3, "office", (TILE_SIZE * 2, TILE_SIZE * 8), "To Office"),
        ]

        office = Area("office", "High Roller Office", (80, 46, 46), (TILE_SIZE * 2, TILE_SIZE * 8))
        office.npcs = [
            NPC("office_boss", "Mr. Vale", "boss", TILE_SIZE * 8, TILE_SIZE * 3, "boss", "You made it up here. Now earn it.", "hard"),
        ]
        office.warps = [Warp(TILE_SIZE * 2, TILE_SIZE * 9, "vault", (TILE_SIZE * 12, TILE_SIZE * 3), "Back To Vault")]
        return {"lounge": lounge, "alley": alley, "vault": vault, "office": office}

    def active_area(self):
        return self.areas[self.current_area]

    def area_boss_beaten(self, area_id):
        boss_ids = {"lounge": "lounge_boss", "alley": "alley_boss", "vault": "vault_boss"}
        needed = boss_ids.get(area_id)
        return needed is None or needed in self.player_profile.beaten_bosses

    def warp_is_locked(self, warp):
        if warp.target_area == "alley":
            return not self.area_boss_beaten("lounge")
        if warp.target_area == "vault":
            return not self.area_boss_beaten("alley")
        if warp.target_area == "office":
            return not self.area_boss_beaten("vault")
        return False

    def use_warp(self, warp):
        if self.warp_is_locked(warp):
            self.dialogue = DialogueWindow("Locked", "Beat the room boss at poker first.")
            return
        self.current_area = warp.target_area
        self.player.place(*warp.target_pos)
        self.dialogue = None

    def blocker_rects(self):
        return [npc.rect for npc in self.active_area().npcs if npc.active]

    def nearest_interaction(self):
        zone = self.player.rect.inflate(40, 40)
        for npc in self.active_area().npcs:
            if npc.active and zone.colliderect(npc.rect):
                return ("npc", npc)
        for warp in self.active_area().warps:
            if zone.colliderect(warp.rect):
                return ("warp", warp)
        return None

    def interact(self):
        found = self.nearest_interaction()
        if not found:
            self.dialogue = DialogueWindow("Quiet", "Nobody answers. Move closer to a table or door.")
            return
        kind, obj = found
        if kind == "warp":
            self.use_warp(obj)
            return
        if obj.role != "boss":
            lines = [obj.dialogue]
            if obj.npc_id == "bartender":
                lines.append("Boss wins let you choose one new buff.")
                if self.player_profile.beaten_bosses:
                    lines.append(f"Bosses beaten: {len(self.player_profile.beaten_bosses)}")
                if self.player_profile.buffs:
                    lines.append(f"Current buffs: {', '.join(self.player_profile.buffs[:4])}")
            self.dialogue = DialogueWindow(obj.name, "\n".join(lines))
            return
        if self.player_profile.chips < 20:
            self.dialogue = DialogueWindow(obj.name, "You need at least 20 chips to sit down.")
            return
        self.match = PokerTableMatch(self.screen, self.assets, self.player_profile, obj, (self.font, self.small_font, self.big_font))
        self.scene = SCENE_POKER

    def handle_world_key(self, event):
        if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            self.interact()
        elif event.key == pygame.K_ESCAPE:
            self.dialogue = None
        elif event.key == pygame.K_h:
            self.player_profile.tutorials_enabled = not self.player_profile.tutorials_enabled
            state = "enabled" if self.player_profile.tutorials_enabled else "disabled"
            self.dialogue = DialogueWindow("Hints", f"Table hints {state}.")
            self.player_profile.save()
        elif event.key == pygame.K_r:
            self.player_profile = PlayerProfile()
            self.player_profile.save()
            self.areas = self.build_areas()
            self.current_area = "lounge"
            self.player.place(*self.areas[self.current_area].spawn)
            self.dialogue = DialogueWindow("Reset", "Save reset. Back to the lounge.")

    def draw_intro(self):
        self.screen.fill((0, 0, 0))
        lines = self.intro_pages[self.intro_index]
        for idx, line in enumerate(lines):
            surf = self.title_font.render(line, True, (245, 245, 245))
            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 260 + idx * 56))
        prompt = self.small_font.render("Press Enter, Space, or click", True, (190, 190, 190))
        self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 90))

    def draw_character(self, sprite_key, x, y, direction):
        sheet = {
            "dealer": self.assets.dealer_sheet,
            "gambler": self.assets.gambler_sheet,
            "boss": self.assets.boss_sheet,
            "player": self.assets.player_sheet,
        }.get(sprite_key)
        frame = sheet.get_frame(direction, 0) if sheet else None
        if frame is not None:
            draw_x = x + PLAYER_SIZE // 2 - frame.get_width() // 2
            draw_y = y + PLAYER_SIZE - frame.get_height()
            self.screen.blit(frame, (draw_x, draw_y))
        else:
            pygame.draw.rect(self.screen, (230, 230, 230), (x, y, PLAYER_SIZE, PLAYER_SIZE))

    def draw_boss_table(self, npc, cam_x, cam_y, front=False):
        table = self.assets.table_sprite
        if table is None:
            return

        draw_x = npc.x - cam_x - 68
        draw_y = npc.y - cam_y - 6
        shadow_rect = pygame.Rect(draw_x + 20, draw_y + table.get_height() - 22, table.get_width() - 40, 22)

        if not front:
            pygame.draw.ellipse(self.screen, (0, 0, 0, 90), shadow_rect)
            clip = self.screen.get_clip()
            self.screen.set_clip(pygame.Rect(draw_x, draw_y, table.get_width(), table.get_height() // 2 + 12))
            self.screen.blit(table, (draw_x, draw_y))
            self.screen.set_clip(clip)
            return

        clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(draw_x, draw_y + table.get_height() // 2 - 8, table.get_width(), table.get_height()))
        self.screen.blit(table, (draw_x, draw_y))
        self.screen.set_clip(clip)

    def draw_world(self):
        area = self.active_area()
        self.screen.fill(area.palette)
        cam_x = max(0, min(self.player.rect.centerx - WIDTH // 2, WORLD_COLS * TILE_SIZE - WIDTH))
        cam_y = max(0, min(self.player.rect.centery - HEIGHT // 2, WORLD_ROWS * TILE_SIZE - HEIGHT))

        for y in range(WORLD_ROWS):
            for x in range(WORLD_COLS):
                rect = pygame.Rect(x * TILE_SIZE - cam_x, y * TILE_SIZE - cam_y, TILE_SIZE, TILE_SIZE)
                color = tuple(min(255, c + ((x + y) % 2) * 8) for c in area.palette)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (24, 24, 24), rect, 1)

        for warp in area.warps:
            rect = pygame.Rect(warp.x - cam_x, warp.y - cam_y, TILE_SIZE, TILE_SIZE)
            color = (150, 70, 70) if self.warp_is_locked(warp) else (85, 155, 220)
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, (230, 230, 230), rect, 2, border_radius=10)

        for npc in area.npcs:
            if npc.active and npc.role == "boss":
                self.draw_boss_table(npc, cam_x, cam_y, front=False)

        for npc in area.npcs:
            if npc.active:
                self.draw_character(npc.sprite_key, npc.x - cam_x, npc.y - cam_y, "down")

        for npc in area.npcs:
            if npc.active and npc.role == "boss":
                self.draw_boss_table(npc, cam_x, cam_y, front=True)

        self.player.draw(self.screen, cam_x, cam_y)

        hud = pygame.Rect(16, 16, 392, 214)
        pygame.draw.rect(self.screen, (22, 22, 28), hud, border_radius=12)
        pygame.draw.rect(self.screen, (225, 225, 225), hud, 2, border_radius=12)
        buffs = ", ".join(self.player_profile.buffs[:4]) if self.player_profile.buffs else "None"
        cleared = len(self.player_profile.beaten_bosses)
        lines = [
            f"Area: {area.name}",
            f"Chips: {self.player_profile.chips}",
            f"Gold: {self.player_profile.gold}",
            f"Poker Bonus: +{self.player_profile.poker_bonus}",
            f"Buffs: {buffs}",
            f"Bosses Beat: {cleared}",
            "E interact   H hints   R reset",
            "Boss wins now let you choose a new buff.",
        ]
        for idx, line in enumerate(lines):
            surf = self.small_font.render(line, True, (240, 240, 240))
            self.screen.blit(surf, (hud.x + 12, hud.y + 12 + idx * 24))

        if self.dialogue:
            self.dialogue.draw(self.screen, self.big_font, self.font)

    def run(self):
        while True:
            keys = pygame.key.get_pressed()
            if self.scene == SCENE_WORLD and not self.dialogue:
                self.player.move(keys, self.blocker_rects())

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.player_profile.save()
                    pygame.quit()
                    sys.exit()

                if self.scene == SCENE_MENU:
                    self.menu.handle_input(event)
                elif self.scene == SCENE_INTRO:
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                        self.intro_index += 1
                        if self.intro_index >= len(self.intro_pages):
                            self.scene = SCENE_WORLD
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.intro_index += 1
                        if self.intro_index >= len(self.intro_pages):
                            self.scene = SCENE_WORLD
                elif self.scene == SCENE_WORLD and event.type == pygame.KEYDOWN:
                    self.handle_world_key(event)
                elif self.scene == SCENE_POKER and event.type == pygame.KEYDOWN:
                    result = self.match.handle_key(event.key)
                    if result == "LEAVE":
                        self.player_profile.save()
                        if self.player_profile.chips <= 0:
                            self.scene = SCENE_GAME_OVER
                            self.game_over_reason = "You ran out of chips and the district shut its doors on you."
                        elif "office_boss" in self.player_profile.beaten_bosses:
                            self.scene = SCENE_GAME_OVER
                            self.game_over_reason = "Mr. Vale is beaten. The district is yours."
                        else:
                            self.scene = SCENE_WORLD
                            self.match = None
                elif self.scene == SCENE_GAME_OVER and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.player_profile.save()
                        self.scene = SCENE_MENU

            if self.scene == SCENE_MENU:
                self.menu.draw(self.screen)
            elif self.scene == SCENE_INTRO:
                self.draw_intro()
            elif self.scene == SCENE_WORLD:
                self.draw_world()
            elif self.scene == SCENE_POKER:
                self.match.draw()
            elif self.scene == SCENE_GAME_OVER:
                self.screen.fill((10, 10, 14))
                title = self.title_font.render("Game Over", True, (255, 226, 150))
                self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 220))
                for idx, line in enumerate(self.game_over_reason.split("\n")):
                    surf = self.font.render(line, True, (240, 240, 240))
                    self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 310 + idx * 30))
                prompt = self.small_font.render("Press Enter for menu", True, (200, 200, 200))
                self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 430))

            pygame.display.flip()
            self.clock.tick(60)
