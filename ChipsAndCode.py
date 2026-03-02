import pygame 
import random

##constant lists for the card suit/rank, and phase of the current game.
SUIT = ["hearts", "diamonds", "spades", "clubs"]

RANK = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]

GAMEPHASE = ["blinds", "preflop", "bet", "flop", "bet", "turn", "bet", "river", "bet", "handCheck"]


##code for the png files | need to optimize later with key/item dictionary to make it only load once
#cardFile = f"assets/cards{RANK}_of_{SUIT}.png"



#class for individual cards
class Card:
    

    def __init__(self, rank, suit):

        self.rank = rank
        self.suit = suit
        self.image = pygame.image.load(f"assets/cards/{rank}_of_{suit}.png")

#class for the users player attributes
class Player:

    #
    def __init__(self, name):

        self.chips = 1000

        self.name = name

        self.hand = []

        self.folded = False

        self.buffs = []

    def recieveCard(self, card: Card):

        self.hand.append(card)   

#class for boss attributes/actions
class Boss:

    #constructor
    def __init__(self, name, personality, difficulty):

        super().__init__(name)

        self.name = name
        self.personality = personality
        self.difficulty = difficulty
    
    def chooseAction(self, game, table, call=0):

        phase = game.phase

#class for an action in game. EX: "fold" "check" "call" "raise"
class Action:

    #constructor
    def __init__(self, type, amount=0):

        self.type = type
        self.amount = amount

    #function that applies an action and updates relevant data
    def processAction(self, player, action, game):
        
        if action.type == "fold":

            player.folded = True

        elif action.type == "call":

            player.chips -= self.amount

            game.table.pot += self.amount
        
        elif action.type == "raise":

            player.chips -= self.amount

            game.table.pot += self.amount

        elif action.type == "check":

            pass
        
#class for a deck of cards                
class Deck:

    #constructor
    def __init__(self):

        self.cards = [Card(r,s) for r in RANK for s in SUIT]
        self.shuffle()

    #method for shuffling the deck after it is created
    def shuffle(self):

        random.shuffle(self.cards)

    #method for drawing a card from the deck
    def drawCard(self) -> Card:

        return self.cards.pop()
    
    #method for dealing cards to players
    def deal(self, player, numCards):

        for c in range(numCards):

            player.recieveCard(self.drawCard())


#class for the table, included to track community cards
class Table:

    #constructor
    def __init__(self):

        self.pot = 0
        self.communityCards = []
        self.burnCards = []

    #method for adding card to table (dealing a community card)
    def addCard(self, card: Card):

        self.communityCards.append(card)


    #reset the current table to default
    def reset(self):

        self.communityCards.clear()
        self.pot = 0
        self.burnCards.clear()


#class for an active game, includes info for the game such as the current phase, current pot, etc..
class ActiveGame:

    def __init__(self, player, boss: Boss):
        
        self.currentPlayer = player
        self.boss = boss
        self.phase = GAMEPHASE[0]
        self.deck = Deck()
        self.table = Table()

    #function for starting/dealing a new hand
    def newHand(self):

        #reset/refresh necessary fields for a new hand
        self.deck = Deck()
        self.table.reset()
        self.currentPlayer.hand.clear()
        self.boss.hand.clear()
        self.phase = GAMEPHASE[0]


        #deal the new hand
        self.deck.deal(self.currentPlayer, 2)
        self.deck.deal(self.boss, 2)

    #method for dealing community cards depending on phase
    def dealCommunityCards(self):

        if self.phase == "flop":

            for c in range(3):
                
                self.table.addCard(self.deck.drawCard())
            
        elif self.phase == "turn":

            self.table.addCard(self.deck.drawCard)

        elif self.phase == "river":

            self.table.addCard(self.deck.drawCard)



    #method for progressing the game phase
    def changePhase(self):

        currentPhase = self.phase

        i = GAMEPHASE.index(self.phase)

        #might need to be edited with an else statement for when it reaches last phase
        if (i + 1) < len(GAMEPHASE):

            self.phase = GAMEPHASE[i + 1]
      

