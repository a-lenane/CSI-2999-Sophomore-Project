import pygame
import sys
import random

"""
TODO:
- hide dealer cards (diff card backs for diff dealers?)
- menu to adjust bet amount (mayb  buttons like, bet 1x, bet 2x, bet 5x)
- player money tracking
- using ChipsAndCode to assess hands, can mayb show optimal hand to player during play
- determine a winner (+ payout)
- where get buffs (store?)
- hide player cards untill click "deal" button
- dynamic adjustments for each turn, such as "deal" being only option, then only "check" or "bet", then "check", "bet" or fold, with game finish handling
- buff menu / info 
"""

pygame.init()

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Texas Hold'em: High Stakes")

clock = pygame.time.Clock()

# COLORS
TABLE_GREEN = (6, 71, 42)
GOLD = (212, 175, 55)
WHITE = (255, 255, 255)
LIGHT_GOLD = (255, 215, 0)
FLOOR = (40, 40, 40)
WALL = (20, 20, 20)
PLAYER_COLOR = (200, 50, 50)
NPC_COLOR = (200, 200, 50)
GUARD_COLOR = (50, 120, 220)

# FONTS
title_font = pygame.font.SysFont("arialblack", 80)
font = pygame.font.SysFont(None, 32)

# --------------------------------------------------
# UI & OBJECT CLASSES
# --------------------------------------------------
class Button:
    def __init__(self, text, x_ratio, y_ratio, w_ratio=0.18, h_ratio=0.07):
        self.text = text
        self.x_ratio = x_ratio
        self.y_ratio = y_ratio
        self.w_ratio = w_ratio
        self.h_ratio = h_ratio
        self.rect = pygame.Rect(0, 0, 0, 0)

    def draw(self, surface):
        btn_w = WIDTH * self.w_ratio
        btn_h = HEIGHT * self.h_ratio
        self.rect.size = (btn_w, btn_h)
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)
        
        dynamic_font = pygame.font.SysFont("arial", int(btn_h * 0.5))
        color = GOLD if not self.rect.collidepoint(pygame.mouse.get_pos()) else LIGHT_GOLD

        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        text_surf = dynamic_font.render(self.text, True, TABLE_GREEN)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

class Player:
    def __init__(self):
        self.rect = pygame.Rect(100, 100, 40, 40)
        self.speed = 5
        self.x_ratio = 0.1
        self.y_ratio = 0.1

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def move(self, dx, dy, colliders):
        self.rect.x += dx
        if any(self.rect.colliderect(c) for c in colliders): self.rect.x -= dx
        self.rect.y += dy
        if any(self.rect.colliderect(c) for c in colliders): self.rect.y -= dy
        self.x_ratio = self.rect.centerx / WIDTH
        self.y_ratio = self.rect.centery / HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, PLAYER_COLOR, self.rect)

class NPC:
    def __init__(self, x_ratio, y_ratio):
        self.x_ratio, self.y_ratio = x_ratio, y_ratio
        self.rect = pygame.Rect(0, 0, 35, 35)
        self.reposition()
        self.timer = 0
        self.direction = (0, 0)

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def update(self, colliders):
        self.timer -= 1
        if self.timer <= 0:
            self.direction = random.choice([(1,0),(-1,0),(0,1),(0,-1),(0,0)])
            self.timer = random.randint(30, 120)
        
        dx, dy = self.direction[0] * 2, self.direction[1] * 2
        self.rect.x += dx
        if any(self.rect.colliderect(c) for c in colliders): self.rect.x -= dx
        self.rect.y += dy
        if any(self.rect.colliderect(c) for c in colliders): self.rect.y -= dy
        self.x_ratio = self.rect.centerx / WIDTH
        self.y_ratio = self.rect.centery / HEIGHT

    def draw(self, surface):
        pygame.draw.rect(surface, NPC_COLOR, self.rect)

class Guard:
    def __init__(self, x_ratio, y_ratio):
        self.x_ratio, self.y_ratio = x_ratio, y_ratio
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.reposition()

    def reposition(self):
        self.rect.center = (WIDTH * self.x_ratio, HEIGHT * self.y_ratio)

    def draw(self, surface):
        pygame.draw.rect(surface, GUARD_COLOR, self.rect)

# --------------------------------------------------
# POKER LOGIC
# --------------------------------------------------
suits = ["spades", "hearts", "diamonds", "clubs"]
ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]

class Card:
    def __init__(self, rank, suit): self.rank, self.suit = rank, suit

class Deck:
    def __init__(self):
        self.cards = [Card(r, s) for s in suits for r in ranks]
        random.shuffle(self.cards)
    def deal(self): return self.cards.pop()

class PokerPlayer:
    def __init__(self, name, bankroll, is_human=False):
        self.name, self.bankroll, self.is_human = name, bankroll, is_human
        self.hand, self.folded = [], False

class PokerGame:
    def __init__(self):
        self.players = [PokerPlayer("You", 1000, True), PokerPlayer("Vinny", 1000), 
                        PokerPlayer("Rico", 1000), PokerPlayer("Lola", 1000)]
        self.dealer = PokerPlayer("Dealer", 0) # House hand
        self.deck = Deck()
        self.community, self.pot, self.phase = [], 0, "deal"
        self.dealer_revealed = True # Toggle this later to false to hide cards
        self.deal()

    def deal(self):
        for p in self.players: p.hand = [self.deck.deal(), self.deck.deal()]
        self.dealer.hand = [self.deck.deal(), self.deck.deal()]

    def next_phase(self):
        if self.phase == "deal": 
            self.community = [self.deck.deal(), self.deck.deal(), self.deck.deal()]
            self.phase = "flop"
        elif self.phase == "flop": self.community.append(self.deck.deal()); self.phase = "turn"
        elif self.phase == "turn": self.community.append(self.deck.deal()); self.phase = "river"
        elif self.phase == "river": self.phase = "showdown"

    def ai_turns(self):
        for p in self.players:
            if not p.is_human and not p.folded:
                if random.random() < 0.25: p.folded = True
                else: self.pot += 50

# --------------------------------------------------
# INITIALIZATION & RESIZING
# --------------------------------------------------
player = Player()
walls, tables = [], []
guards = [Guard(0.8, 0.3), Guard(0.84, 0.3)]
npcs = [NPC(0.2, 0.3), NPC(0.4, 0.5), NPC(0.7, 0.2)]

# Main Buttons
start_story = Button("Start Story", 0.5, 0.4, 0.3, 0.08)
free_play = Button("Free Play", 0.5, 0.55, 0.3, 0.08)
quit_button = Button("Quit", 0.5, 0.7, 0.3, 0.08)

# Poker Buttons
call_btn = Button("Call ($50)", 0.3, 0.9, 0.15, 0.06)
fold_btn = Button("Fold", 0.5, 0.9, 0.15, 0.06)
leave_btn = Button("Leave", 0.7, 0.9, 0.15, 0.06)

def recalculate_elements():
    global walls, tables
    t = 40
    walls = [pygame.Rect(0,0,WIDTH,t), pygame.Rect(0,0,t,HEIGHT),
             pygame.Rect(0,HEIGHT-t,WIDTH,t), pygame.Rect(WIDTH-t,0,t,HEIGHT)]
    tables = [pygame.Rect(WIDTH*0.3, HEIGHT*0.3, 120, 80), 
              pygame.Rect(WIDTH*0.6, HEIGHT*0.5, 120, 80)]
    player.reposition()
    for n in npcs: n.reposition()
    for g in guards: g.reposition()

recalculate_elements()
game_state, poker_game = "menu", None

def near_table():
    for table in tables:
        if player.rect.colliderect(table.inflate(40, 40)): return True
    return False

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.size
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            recalculate_elements()

        if game_state == "menu":
            if start_story.clicked(event): game_state = "story"
            if free_play.clicked(event): game_state = "world"
            if quit_button.clicked(event): running = False
        elif game_state == "poker":
            if call_btn.clicked(event):
                poker_game.pot += 50; poker_game.ai_turns(); poker_game.next_phase()
            if fold_btn.clicked(event):
                poker_game.players[0].folded = True; poker_game.ai_turns(); poker_game.next_phase()
            if leave_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                game_state = "world"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and game_state != "poker": game_state = "menu"
            if event.key == pygame.K_e and game_state == "world" and near_table():
                poker_game = PokerGame(); game_state = "poker"

    # UPDATE
    world_colliders = walls + tables + [g.rect for g in guards]
    if game_state == "world":
        keys = pygame.key.get_pressed()
        dx, dy = (keys[pygame.K_d] - keys[pygame.K_a]) * player.speed, (keys[pygame.K_s] - keys[pygame.K_w]) * player.speed
        player.move(dx, dy, world_colliders)
        for npc in npcs: npc.update(world_colliders)

    # DRAW
    screen.fill(FLOOR)
    if game_state == "menu":
        screen.fill(TABLE_GREEN); title = title_font.render("TEXAS HOLD'EM", True, GOLD)
        screen.blit(title, title.get_rect(center=(WIDTH/2, HEIGHT*0.2)))
        for btn in [start_story, free_play, quit_button]: btn.draw(screen)
    elif game_state == "story":
        screen.fill((0, 0, 0))
        lines = ["Rain hits the pavement.", "Someone tipped you about a poker game.", "Not a casino.", "A basement poker den.", "", "Press ESC to return."]
        for i, line in enumerate(lines):
            text = font.render(line, True, WHITE); screen.blit(text, text.get_rect(center=(WIDTH/2, HEIGHT*0.2 + i*(HEIGHT/10))))
    elif game_state == "world":
        for wall in walls: pygame.draw.rect(screen, WALL, wall)
        for table in tables: pygame.draw.rect(screen, TABLE_GREEN, table, border_radius=15)
        for npc in npcs: npc.draw(screen)
        for guard in guards: guard.draw(screen)
        player.draw(screen)
        if near_table():
            prompt = font.render("Press E to Play Poker", True, WHITE); screen.blit(prompt, prompt.get_rect(center=(WIDTH/2, HEIGHT*0.9)))
    elif game_state == "poker":
        screen.fill(TABLE_GREEN)
        pot_txt = font.render(f"Pot: ${poker_game.pot}", True, WHITE); screen.blit(pot_txt, pot_txt.get_rect(center=(WIDTH/2, HEIGHT/10)))

        scalar = min(HEIGHT, WIDTH) / 20
        card_w, card_h = int(scalar * 2.5), int(scalar * 3.5) 
        
        # --- DEALER HAND ---
        dealer_x = 60 # Padding from left wall
        dealer_y = HEIGHT * 0.12
        dealer_label = font.render("Dealer:", True, GOLD)
        screen.blit(dealer_label, (dealer_x, dealer_y - 30))
        
        for i, card in enumerate(poker_game.dealer.hand):
            if poker_game.dealer_revealed:
                try:
                    img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                    screen.blit(img, (dealer_x + i*(card_w + 5), dealer_y))
                except: pygame.draw.rect(screen, WHITE, (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), border_radius=5)
            else:
                # card backs
                pygame.draw.rect(screen, (150, 0, 0), (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), border_radius=5)
                pygame.draw.rect(screen, GOLD, (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), 2, border_radius=5)

        # Community & Player Hands
        x_comm = WIDTH/2 - (len(poker_game.community) * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.community):
            try:
                img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                screen.blit(img, (x_comm + i*(card_w + 10), HEIGHT/2 - card_h/2))
            except: pygame.draw.rect(screen, WHITE, (x_comm + i*(card_w+10), HEIGHT/2 - card_h/2, card_w, card_h))

        x_hand = WIDTH/2 - (2 * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.players[0].hand):
            try:
                img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                screen.blit(img, (x_hand + i*(card_w + 10), HEIGHT*0.65))
            except: pygame.draw.rect(screen, WHITE, (x_hand + i*(card_w+10), HEIGHT*0.65, card_w, card_h))

        for btn in [call_btn, fold_btn, leave_btn]: btn.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()