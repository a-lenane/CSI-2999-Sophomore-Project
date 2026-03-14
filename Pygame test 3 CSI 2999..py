import pygame
import sys
import random
import ChipsAndCode

pygame.init()

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Texas Hold'em: High Stakes")

clock = pygame.time.Clock()

# COLORS
TABLE_GREEN = (6,71,42)
GOLD = (212,175,55)
WHITE = (255,255,255)
LIGHT_GOLD = (255,215,0)
FLOOR = (40,40,40)
WALL = (20,20,20)
PLAYER_COLOR = (200,50,50)
NPC_COLOR = (200,200,50)
GUARD_COLOR = (50,120,220)

# FONTS
title_font = pygame.font.SysFont("arialblack",80)
button_font = pygame.font.SysFont("arial",40)
font = pygame.font.SysFont(None,32)

# --------------------------------------------------
# UI
# --------------------------------------------------

class Button:

    def __init__(self,text,y):
        self.text=text
        self.rect=pygame.Rect(WIDTH//2-150,y,300,60)

    def draw(self,surface):

        color = GOLD
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            color = LIGHT_GOLD

        pygame.draw.rect(surface,color,self.rect,border_radius=10)

        text = button_font.render(self.text,True,TABLE_GREEN)
        surface.blit(text,text.get_rect(center=self.rect.center))

    def clicked(self,event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


# --------------------------------------------------
# WORLD CHARACTERS
# --------------------------------------------------

class Player:

    def __init__(self):
        self.rect = pygame.Rect(100,100,40,40)
        self.speed = 5

    def move(self,dx,dy,colliders):

        self.rect.x += dx
        for c in colliders:
            if self.rect.colliderect(c):
                self.rect.x -= dx

        self.rect.y += dy
        for c in colliders:
            if self.rect.colliderect(c):
                self.rect.y -= dy

    def draw(self,surface):
        pygame.draw.rect(surface,PLAYER_COLOR,self.rect)


class NPC:

    def __init__(self,x,y):
        self.rect = pygame.Rect(x,y,35,35)
        self.timer = 0
        self.direction = random.choice([(1,0),(-1,0),(0,1),(0,-1)])

    def update(self):

        self.timer -= 1

        if self.timer <= 0:
            self.direction = random.choice([(1,0),(-1,0),(0,1),(0,-1),(0,0)])
            self.timer = random.randint(30,120)

        self.rect.x += self.direction[0]*2
        self.rect.y += self.direction[1]*2

    def draw(self,surface):
        pygame.draw.rect(surface,NPC_COLOR,self.rect)


class Guard:

    def __init__(self,x,y):
        self.rect = pygame.Rect(x,y,40,40)

    def draw(self,surface):
        pygame.draw.rect(surface,GUARD_COLOR,self.rect)


# --------------------------------------------------
# POKER SYSTEM
# --------------------------------------------------

suits = ["spades","hearts","diamonds","clubs"]
ranks = ["2","3","4","5","6","7","8","9","10","jack","queen","king","ace"]

class Card:

    def __init__(self,rank,suit):
        self.rank = rank
        self.suit = suit

    def text(self):
        return f"{self.rank}{self.suit}"


class Deck:

    def __init__(self):
        self.cards = [Card(r,s) for s in suits for r in ranks]
        random.shuffle(self.cards)

    def deal(self):
        return self.cards.pop()


class PokerPlayer:

    def __init__(self,name,bankroll,is_human=False):
        self.name = name
        self.bankroll = bankroll
        self.hand = []
        self.folded = False
        self.is_human = is_human

    def bet(self,amount):
        amount = min(amount,self.bankroll)
        self.bankroll -= amount
        return amount


class PokerGame:

    def __init__(self):

        self.players = [
            PokerPlayer("You",1000,True),
            PokerPlayer("Vinny",1000),
            PokerPlayer("Rico",1000),
            PokerPlayer("Lola",1000)
        ]

        self.deck = Deck()
        self.community = []
        self.pot = 0
        self.phase = "deal"

        self.deal()

    def deal(self):
        for p in self.players:
            p.hand = [self.deck.deal(),self.deck.deal()]

    def next_phase(self):

        if self.phase == "deal":

            self.community = [self.deck.deal(),
                              self.deck.deal(),
                              self.deck.deal()]
            self.phase = "flop"

        elif self.phase == "flop":

            self.community.append(self.deck.deal())
            self.phase = "turn"

        elif self.phase == "turn":

            self.community.append(self.deck.deal())
            self.phase = "river"

        elif self.phase == "river":

            self.phase = "showdown"

    def ai_turns(self):

        for p in self.players:

            if not p.is_human and not p.folded:

                if random.random() < 0.25:
                    p.folded = True
                else:
                    self.pot += p.bet(50)

# --------------------------------------------------
# GAME SETUP
# --------------------------------------------------

player = Player()

walls = [
pygame.Rect(0,0,WIDTH,40),
pygame.Rect(0,0,40,HEIGHT),
pygame.Rect(0,HEIGHT-40,WIDTH,40),
pygame.Rect(WIDTH-40,0,40,HEIGHT)
]

tables = [
pygame.Rect(300,200,120,80),
pygame.Rect(600,400,120,80)
]

guards = [
Guard(800,300),
Guard(840,300)
]

npcs = [
NPC(200,300),
NPC(400,500),
NPC(700,200)
]

start_story = Button("Start Story",250)
free_play = Button("Free Play",330)
quit_button = Button("Quit",410)

game_state = "menu"
poker_game = None

# --------------------------------------------------
# HELPER
# --------------------------------------------------

def near_table():

    for table in tables:
        if player.rect.colliderect(table.inflate(40,40)):
            return True
    return False

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running=False

        if game_state=="menu":

            if start_story.clicked(event):
                game_state="story"

            if free_play.clicked(event):
                game_state="world"

            if quit_button.clicked(event):
                running=False

        if event.type==pygame.KEYDOWN:

            if event.key==pygame.K_ESCAPE:

                if game_state=="poker":
                    game_state="world"
                else:
                    game_state="menu"

            if event.key==pygame.K_e and game_state=="world":
                if near_table():
                    poker_game = PokerGame()
                    game_state="poker"

            if game_state=="poker":

                if event.key==pygame.K_c:
                    poker_game.pot += poker_game.players[0].bet(50)
                    poker_game.ai_turns()
                    poker_game.next_phase()

                if event.key==pygame.K_f:
                    poker_game.players[0].folded=True
                    poker_game.ai_turns()
                    poker_game.next_phase()

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    keys = pygame.key.get_pressed()

    if game_state=="world":

        dx=dy=0

        if keys[pygame.K_w]: dy=-player.speed
        if keys[pygame.K_s]: dy=player.speed
        if keys[pygame.K_a]: dx=-player.speed
        if keys[pygame.K_d]: dx=player.speed

        colliders = walls + tables + [g.rect for g in guards]

        player.move(dx,dy,colliders)

        for npc in npcs:
            npc.update()

    # --------------------------------------------------
    # DRAW
    # --------------------------------------------------

    if game_state=="menu":

        screen.fill(TABLE_GREEN)

        title = title_font.render("TEXAS HOLD'EM",True,GOLD)
        screen.blit(title,title.get_rect(center=(WIDTH//2,150)))

        start_story.draw(screen)
        free_play.draw(screen)
        quit_button.draw(screen)

    elif game_state=="story":

        screen.fill((0,0,0))

        lines = [
        "Rain hits the pavement.",
        "Someone tipped you about a poker game.",
        "Not a casino.",
        "A basement poker den.",
        "",
        "Press ESC to return."
        ]

        y=200
        for line in lines:

            text=font.render(line,True,WHITE)
            screen.blit(text,(WIDTH//2-text.get_width()//2,y))
            y+=40

    elif game_state=="world":

        screen.fill(FLOOR)

        for wall in walls:
            pygame.draw.rect(screen,WALL,wall)

        for table in tables:
            pygame.draw.rect(screen,TABLE_GREEN,table,border_radius=20)

        for npc in npcs:
            npc.draw(screen)

        for guard in guards:
            guard.draw(screen)

        player.draw(screen)

        if near_table():
            text=font.render("Press E to Play Poker",True,WHITE)
            screen.blit(text,(WIDTH//2-120,HEIGHT-80))

    elif game_state=="poker":

        screen.fill(TABLE_GREEN)

        pot_text = font.render(f"Pot: ${poker_game.pot}",True,WHITE)
        pot_rect = pygame.Surface.get_rect(pot_text)
        pot_rect.center = (WIDTH/2,HEIGHT/10)
        screen.blit(pot_text,pot_rect)

        card_height = HEIGHT/7
        card_width = WIDTH/14

        spacing_community = WIDTH/10 - WIDTH/140
        total_width_community = 4 * spacing_community + card_width
        x=WIDTH/2 - total_width_community/2
        for card in poker_game.community:            
            filename = f"ui/{card.rank}_of_{card.suit}.png"
            card_sprite = pygame.image.load(filename)
            card_sprite = pygame.transform.smoothscale(card_sprite, (card_width, card_height))
            screen.blit(card_sprite, (x, HEIGHT/3))

            x+=spacing_community

        
        spacing_player = WIDTH/8 - WIDTH/140
        total_width_player = spacing_player + card_width
        x=WIDTH/2 - total_width_player/2
        for card in poker_game.players[0].hand:
            filename = f"ui/{card.rank}_of_{card.suit}.png"
            card_sprite = pygame.image.load(filename)
            card_sprite = pygame.transform.smoothscale(card_sprite, (card_width, card_height))
            screen.blit(card_sprite, (x, HEIGHT*2/3))
            x+=spacing_player

        controls_text = font.render("C=Call   F=Fold   ESC=Leave",True,WHITE)
        controls_rect = pygame.Surface.get_rect(controls_text)
        controls_rect.center = (WIDTH/2,HEIGHT*9/10)
        screen.blit(controls_text,controls_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()