import pygame 
import random
from collections import Counter
from itertools import combinations

##constant lists for the card suit/rank, and phase of the current game.
SUIT = ["hearts", "diamonds", "spades", "clubs"]

RANK = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]

#card values for evalutating winning hand
RANK_VALUE = { "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "jack": 11, "queen": 12, "king": 13,
              "ace": 14}

HAND_TYPE = {8: "straight flush", 7: "four of a kind", 6: "full house", 5: "flush", 4: "straight", 3: "three of a kind",
             2: "two pair", 1: "one pair", 0: "high card"}

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

    def receiveCard(self, card: Card):

        self.hand.append(card)   

#class for boss attributes/actions, inherits from Player class
class Boss(Player):

    #constructor
    def __init__(self, name, personality, difficulty):

        super().__init__(name)
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
    def processAction(self, player, game):
        
        if self.type == "fold":

            player.folded = True

        elif self.type == "call":

            player.chips -= self.amount

            game.table.pot += self.amount
        
        elif self.type == "raise":

            player.chips -= self.amount

            game.table.pot += self.amount

        elif self.type == "check":

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
        self.phase = GAMEPHASE[self.phaseIndex]
        self.deck = Deck()
        self.table = Table()
        self.phaseIndex = 0

    #function for starting/dealing a new hand
    def newHand(self):

        #reset/refresh necessary fields for a new hand
        self.deck = Deck()
        self.table.reset()
        self.currentPlayer.hand.clear()
        self.boss.hand.clear()
        self.phaseIndex = 0
        self.phase = GAMEPHASE[self.phaseIndex]


        #deal the new hand
        self.deck.deal(self.currentPlayer, 2)
        self.deck.deal(self.boss, 2)

    #method for dealing community cards depending on phase
    def dealCommunityCards(self):

        if self.phase == "flop":

            for c in range(3):
                
                self.table.addCard(self.deck.drawCard())
            
        elif self.phase == "turn":

            self.table.addCard(self.deck.drawCard())

        elif self.phase == "river":

            self.table.addCard(self.deck.drawCard())



    #method for progressing the game phase
    def changePhase(self):

        #might need to be edited with an else statement for when it reaches last phase
        if (self.phaseIndex + 1) < len(GAMEPHASE):

            self.phaseIndex += 1

            self.phase = GAMEPHASE[self.phaseIndex]

    def showDown(self):

        #combine hand with community cards for both participants
        playerCards = self.currentPlayer.hand + self.table.communityCards
        bossCards = self.boss.hand + self.table.communityCards

        #define variables to hold the returned values of bestHandOf7 function
        playerHandRank, playerBestHand = bestHandOf7(playerCards)
        bossHandRank, bossBestHand = bestHandOf7(bossCards)

        ## player wins
        if playerHandRank > bossHandRank:

            self.currentPlayer.chips += self.table.pot

            print(f"{self.currentPlayer.name} wins with {HAND_TYPE[playerHandRank]}")

            self.table.pot = 0

            return self.currentPlayer, playerHandRank

        #boss wins
        elif bossHandRank > playerHandRank:

            self.boss.chips += self.table.pot

            print(f"{self.boss.name} wins with {HAND_TYPE[bossHandRank]}")

            self.table.pot = 0
            
            return self.boss, bossHandRank
        
        ##if its a tie
        else:
            #split the pot between player and boss
            splitPot = self.table.pot // 2
            self.currentPlayer.chips += splitPot
            self.boss.chips += splitPot

            print(f"tie with {HAND_TYPE[playerHandRank]}")

            self.table.pot = 0

            return None, playerHandRank

            



##_____________functions for evaluating the winning hand____________________"

def flush(cards):
    ##create a list for each suit in the hand
    suits = [c.suit for c in cards]

    ##takes the list of suits and creates a set to remove duplicates, returns boolean
    return len(set(suits)) == 1

##helper function for determining the high card of the flush when comparing two flushes
def flushKicker(cards):

    ranks = [RANK_VALUE[c.rank] for c in cards]

    flushRanks = sorted(ranks, reverse = True)

    return flushRanks

##returns the straight high card value if it is a straight, and None of not a straight
def straightValue(cards):

    ##create a list to hold the cards by value for comparison, then sort from low -> high removing duplicates
    ranks = [RANK_VALUE[c.rank] for c in cards]
    
    ranks = sorted(set(ranks))

    if len(ranks) != 5:
        return None

    if ranks == [2,3,4,5,14]:
        return 5
    
    for i in range(4):

        if ranks[i] + 1 != ranks[i+1]:
            return None
        
    return ranks[-1] 

#all-in-one function for determining if a pair is a full house, four of a kind, three of a kind, two of a kind, two pair,
# or single pair
def evaluatePairs(cards):

    #Create a list of the ranks that the hand contains, then count the occurances of each rank. 
    # then, Create a key:value pair of ranks:counts
    ranks = [RANK_VALUE[c.rank] for c in cards]
    counts = Counter(ranks)

    ##create a sorted list of (ranks, counts) based on the highest count #, reverse the list so its high -> low
    kickerGroups = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse = True)

    ##four of a kind
    if kickerGroups[0][1] == 4:

        quadRank = kickerGroups[0][0]
        kicker = [r for r in ranks if r != quadRank][0]

        return 7, [quadRank, kicker]
    
    ##full house
    if kickerGroups[0][1] == 3 and kickerGroups[1][1] == 2:

        tripRank = kickerGroups[0][0]
        pairRank = kickerGroups[1][0]

        return 6, [tripRank, pairRank]
    
    ## three of a kind
    if kickerGroups[0][1] == 3:

        tripsRank = kickerGroups[0][0]
        kickers = sorted([r for r in ranks if r != tripsRank], reverse = True)

        return 3, [tripsRank] + kickers
    
    ##two pairs
    if kickerGroups[0][1] == 2 and kickerGroups[1][1] == 2:

        pair1 = kickerGroups[0][0]
        pair2 = kickerGroups[1][0]
        highPair = max(pair1, pair2)
        lowPair = min(pair1, pair2)
        kicker = [r for r in ranks if r != highPair and r != lowPair][0]

        return 2, [highPair, lowPair, kicker]
    
    ##single pair
    if kickerGroups[0][1] == 2:

        pairRank = kickerGroups[0][0]

        kickers = sorted([r for r in ranks if r != pairRank], reverse = True)

        return 1, [pairRank] + kickers
    
    ##high card
    return 0, sorted(ranks, reverse = True)

def bestHandOf7(cards7):

    best5 = None
    bestHandScore = None

    for hand5 in combinations(cards7, 5):

        handScore = evaluateHand(hand5)

        if bestHandScore == None or handScore > bestHandScore:

            bestHandScore = handScore
            best5 = list(hand5)

    return bestHandScore, best5

#fucntion used by bestHandOf7 to evaluate each players hand
def evaluateHand(cards):

    straight = straightValue(cards)
    isFlush = flush(cards)

    if straight is not None and isFlush:
        return 8
    
    #variable to check if four of a kind or fullhouse
    pairType, PairKickers = evaluatePairs(cards)

    #if four of a kind or fullHouse exists
    if pairType >= 6:

        return pairType, PairKickers
    
    if isFlush:

        return 5, flushKicker(cards)
    
    if straight is not None:

        return 4, [straight]
    
    #return the lower pair rank or high card if none of the above
    return pairType, PairKickers
      

