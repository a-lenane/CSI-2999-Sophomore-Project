import pygame
import sys
import random
from PokerLogic import *  

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
- dealer sprites when open table
- change back to full dynamic card positions vs using fixed pixel offset
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

class WorldPlayer:
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
# INITIALIZATION & RESIZING
# --------------------------------------------------
player = WorldPlayer()
walls, tables = [], []
guards = [Guard(0.8, 0.3), Guard(0.84, 0.3)]
npcs = [NPC(0.2, 0.3), NPC(0.4, 0.5), NPC(0.7, 0.2)]

# Main Buttons
start_story = Button("Start Story", 0.5, 0.4, 0.3, 0.08)
free_play = Button("Free Play", 0.5, 0.55, 0.3, 0.08)
quit_button = Button("Quit", 0.5, 0.7, 0.3, 0.08)

# Poker Buttons
checkCall_btn = Button("Check/Call", 0.2, 0.9, 0.15, 0.06)
raise_btn = Button(f"raise (currentRaiseAmount)", 0.4, 0.9, 0.15, .06)
fold_btn = Button("Fold", 0.6, 0.9, 0.15, 0.06)
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

            if checkCall_btn.clicked(event):
                #finds the amount that the player needs to call
                callAmount = poker_game.getCallAmount(poker_game.currentPlayer)

                if callAmount <= 0:
                    action = Action("check")
                else:
                    action = Action("call")

                action.processAction(poker_game.currentPlayer, poker_game)
                poker_game.playerActed = True

                #temporary boss check/call logic
                bossCallAmount = poker_game.getCallAmount(poker_game.boss)

                if bossCallAmount <= 0:

                    bossAction = Action("check")
                else:
                    bossAction = Action("call")

                bossAction.processAction(poker_game.boss, poker_game)

                poker_game.bossActed = True

            if raise_btn.clicked(event):

                action = Action("raise", 50)
                action.processAction(poker_game.currentPlayer, poker_game)
                poker_game.playerActed = True

                #temporary boss logic
                bossAction = Action("call")
                bossAction.processAction(poker_game.boss, poker_game)
                poker_game.bossActed = True

            if fold_btn.clicked(event):

                action = Action("fold")
                action.processAction(poker_game.currentPlayer, poker_game)                

                poker_game.handWinner = poker_game.boss
                poker_game.phase = "handCheck"
                poker_game.phaseIndex = GAMEPHASE.index("handCheck")
                poker_game.playerActed = False
                poker_game.bossActed = False
                
            if leave_btn.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):

                game_state = "world"

        if event.type == pygame.KEYDOWN:

            #starts a new hand after handCheck
            if game_state == "poker" and poker_game is not None and poker_game.phase == "handCheck":
                poker_game.newHand()

            if event.key == pygame.K_ESCAPE and game_state != "poker": 
                game_state = "menu"

            if event.key == pygame.K_e and game_state == "world" and near_table():

                human_player = Player("You")
                boss_player = Boss("Boss", "easy", 2)
                poker_game = ActiveGame(human_player, boss_player)

                poker_game.newHand()

                game_state = "poker"

    # UPDATE
    world_colliders = walls + tables + [g.rect for g in guards]
    if game_state == "world":
        keys = pygame.key.get_pressed()
        dx, dy = (keys[pygame.K_d] - keys[pygame.K_a]) * player.speed, (keys[pygame.K_s] - keys[pygame.K_w]) * player.speed
        player.move(dx, dy, world_colliders)
        for npc in npcs: npc.update(world_colliders)

    if game_state == "poker" and poker_game is not None:

        #betting round completeness check
        if poker_game.phase != "handCheck" and poker_game.playerActed and poker_game.bossActed:
            poker_game.changePhase()
            poker_game.playerActed = False
            poker_game.bossActed = False

        if poker_game.phase == "flop":
            poker_game.dealCommunityCards()
            poker_game.changePhase()

        elif poker_game.phase == "turn":
            poker_game.dealCommunityCards()
            poker_game.changePhase()
        
        elif poker_game.phase == "river":
            poker_game.dealCommunityCards()
            poker_game.changePhase()

        elif poker_game.phase == "handCheck" and not poker_game.showdownDone:
            #if player folded
            if poker_game.handWinner is not None:
                poker_game.awardPot(poker_game.handWinner)
                winner = poker_game.handWinner
                rank = None
            #if player did not fold
            else:
                 winner, rank = poker_game.showDown()

            poker_game.showdownDone = True


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
        pot_txt = font.render(f"Pot: ${poker_game.table.pot}", True, WHITE); screen.blit(pot_txt, pot_txt.get_rect(center=(WIDTH/2, HEIGHT/10)))

        scalar = min(HEIGHT, WIDTH) / 20
        card_w, card_h = int(scalar * 2.5), int(scalar * 3.5) 
        
        # --- DEALER HAND ---
        dealer_x = 60 # Padding from left wall
        dealer_y = HEIGHT * 0.12
        dealer_label = font.render("Dealer:", True, GOLD)
        screen.blit(dealer_label, (dealer_x, dealer_y - 30))

        #--- Update Button Text ----
        callAmount = poker_game.getCallAmount(poker_game.currentPlayer)

        if callAmount <= 0:
            checkCall_btn.text = "Check"
        else:
            checkCall_btn.text = f"Call (${callAmount})"

        raise_btn.text = "Raise (50$)"
        
        for i, card in enumerate(poker_game.boss.hand):
            if poker_game.phase == "handCheck":
                try:
                    img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                    screen.blit(img, (dealer_x + i*(card_w + 5), dealer_y))
                except: pygame.draw.rect(screen, WHITE, (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), border_radius=5)
            else:
                # card backs
                pygame.draw.rect(screen, (150, 0, 0), (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), border_radius=5)
                pygame.draw.rect(screen, GOLD, (dealer_x + i*(card_w + 5), dealer_y, card_w, card_h), 2, border_radius=5)

        # Community & WorldPlayer Hands
        x_comm = WIDTH/2 - (len(poker_game.table.communityCards) * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.table.communityCards):
            try:
                img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                screen.blit(img, (x_comm + i*(card_w + 10), HEIGHT/2 - card_h/2))
            except: pygame.draw.rect(screen, WHITE, (x_comm + i*(card_w+10), HEIGHT/2 - card_h/2, card_w, card_h))

        x_hand = WIDTH/2 - (2 * (card_w + 10)) / 2
        for i, card in enumerate(poker_game.human.hand):
            try:
                img = pygame.transform.smoothscale(pygame.image.load(f"ui/{card.rank}_of_{card.suit}.png"), (card_w, card_h))
                screen.blit(img, (x_hand + i*(card_w + 10), HEIGHT*0.65))
            except: pygame.draw.rect(screen, WHITE, (x_hand + i*(card_w+10), HEIGHT*0.65, card_w, card_h))

        #only draw the poker buttons in the phases that are relevant
        if poker_game.phase != "handCheck":
            for btn in [checkCall_btn, raise_btn, fold_btn, leave_btn]:

                btn.draw(screen)

        #display the message telling player to press any button to continue at the end of a hand
        if poker_game.phase == "handCheck":

            displayTxt = font.render("Press any key for next hand", True, WHITE)
            screen.blit(displayTxt, displayTxt.get_rect(center = (WIDTH/2, HEIGHT * 0.85)))
                
                 

                

    pygame.display.flip()
    clock.tick(60)

pygame.quit()