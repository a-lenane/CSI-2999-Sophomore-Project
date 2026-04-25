#import pygame 
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
        #self.image = pygame.image.load(f"assets/cards/{rank}_of_{suit}.png")

#class for the users player attributes
class Player:

    #
    def __init__(self, name):

        self.chips = 1000

        self.currentContribution = 0

        self.name = name

        self.hand = []

        self.folded = False

        self.buffs = {"fourCardStraight": False,
                      "fourCardFlush": False,
                      "DiscountCall": False,
                      "ReadOneBossCard": False,
                      "BlindSheild": False
                      }


    def receiveCard(self, card: Card):

        self.hand.append(card)   

#class for boss attributes/actions, inherits from Player class
class Boss(Player):

    #constructor
    def __init__(self, name, personality, difficulty):

        super().__init__(name)
        self.personality = personality
        self.difficulty = difficulty

    def easyDecision(self, strength, call, callRatio, stackRatio, game):
        
        if call == 0:
            if strength in ["strongest"] and random.random() < 0.4:
                return Action("raise", 50)
            return Action("check")
        
        if strength in ["strongest", "strong"]:
            return Action("call")
        
        if strength == "medium" and callRatio < 0.5:
            return Action("call")
        
        return Action("fold")
    
    def mediumDecision(self, strength, call, callRatio, stackRatio, game):

        if call == 0:
            if strength == "strongest":
                return Action("raise", max(50, game.table.pot // 2))
            
            #bluff logic
            if strength == "medium" and random.random() < 0.1:
                return Action("raise", max(50, game.table.pot // 3))
            
            return Action("check")
            
        if strength == "strongest":
            return Action("raise", max(50, game.table.pot // 2))
        
        
        if strength == "strong" and callRatio < .6:
            return Action("call")
        
        if strength == "medium" and callRatio < .25:
            return Action("call")
        
        if strength == "playable" and call < 50:
            return Action("call")
        
        return Action("fold")
    
    def hardDecision(self, strength, call, callRatio, stackRatio, game):
        
        if call == 0:
            if strength == "strongest":
                #switch up between calling and raising when hand is strong
                return Action("raise", max(50, game.table.pot // 2))
            
            if strength == "strong" and random.random() < 0.4:
                return Action("raise", max(50, game.table.pot // 2))
            
            #bluff logic
            if len(game.table.communityCards) > 0 and strength in ["weak", "medium"] and random.random() < 0.2:
                return Action("raise", max(50, game.table.pot // 3))   
            
            return Action("check")
        
        if strength == "strongest":
            if callRatio < 1.0:
                return Action("raise", max(50, game.table.pot // 2))
            return Action("call")
        
        if strength == "strong" and callRatio < 0.5 and stackRatio < 0.2:
            return Action("call")
        
        if strength == "medium" and callRatio < 0.15 and stackRatio < .08:
            return Action("call")
            
        
        return Action("fold")
    
    def chooseAction(self, game, table, call=0):
        
        if len(self.hand) < 2:
            return Action("check")
        
        pot = max(1, game.table.pot)
        callRatio = call / pot
        stackRatio = call / max(1, self.chips)

        #logic to use the correct hand strength function 
        if len(game.table.communityCards) == 0:
            strength = evaluateStartingHand(self.hand[0], self.hand[1])
        
        else:
            strength = evaluatePostFlopStrength(self.hand + game.table.communityCards)


        if self.difficulty == 1:
            return self.easyDecision(strength, call, callRatio, stackRatio, game)
        
        elif self.difficulty == 2:
            return self.mediumDecision(strength, call, callRatio, stackRatio, game)
        
        elif self.difficulty == 3:
            return self.hardDecision(strength, call, callRatio, stackRatio, game)
        
        return Action("check")

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

            toCall = game.currentBet - player.currentContribution

            player.chips -= toCall

            game.table.pot += toCall

            player.currentContribution += toCall
        
        elif self.type == "raise":

            toCall = game.currentBet - player.currentContribution

            total = toCall + self.amount

            game.currentBet += self.amount

            player.chips -= total

            game.table.pot += total

            player.currentContribution += total

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

            player.receiveCard(self.drawCard())


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
        self.human = player
        self.boss = boss
        self.phaseIndex = 0
        self.phase = GAMEPHASE[self.phaseIndex]
        self.deck = Deck()
        self.table = Table()
        self.currentBet = 0
        self.handWinner = None
        self.playerActed = False
        self.bossActed = False
        self.showdownDone = False

        self.smallBlind = 25
        self.bigBlind = 50


    #function for starting/dealing a new hand
    def newHand(self):

        #reset/refresh necessary fields for a new hand
        self.deck = Deck()
        self.table.reset()
        self.currentPlayer.hand.clear()
        self.boss.hand.clear()
        self.phaseIndex = 1
        self.phase = GAMEPHASE[self.phaseIndex]
        self.currentBet = 0
        self.currentPlayer.currentContribution = 0
        self.boss.currentContribution = 0
        self.playerActed = False
        self.bossActed = False
        self.showdownDone = False
        self.handWinner = None


        #deal the new hand
        self.deck.deal(self.currentPlayer, 2)
        self.deck.deal(self.boss, 2)

        #take blinds
        sb = min(self.smallBlind, self.human.chips)
        bb = min(self.bigBlind, self.boss.chips)

        self.human.chips -= sb
        self.human.currentContribution = sb

        self.boss.chips -= bb
        self.boss.currentContribution = bb

        self.table.pot = sb + bb
        self.currentBet = bb

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

            if self.phase in ["flop", "turn", "river"]:

                self.currentBet = 0
                self.currentPlayer.currentContribution = 0
                self.boss.currentContribution = 0
                self.playerActed = False
                self.bossActed = False
 

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

            print(f"{self.currentPlayer.name} wins with {HAND_TYPE[playerHandRank[0]]}")

            self.table.pot = 0

            return self.currentPlayer, playerHandRank

        #boss wins
        elif bossHandRank > playerHandRank:

            self.boss.chips += self.table.pot

            print(f"{self.boss.name} wins with {HAND_TYPE[bossHandRank[0]]}")

            self.table.pot = 0
            
            return self.boss, bossHandRank
        
        ##if its a tie
        else:
            #split the pot between player and boss
            splitPot = self.table.pot // 2
            self.currentPlayer.chips += splitPot
            self.boss.chips += splitPot

            # FIX: playerHandRank is a tuple, take first element for HAND_TYPE key
            print(f"tie with {HAND_TYPE[playerHandRank[0]]}")

            self.table.pot = 0

            return None, playerHandRank
        
    #function for proper payout when player folds. purpose is to not cause bugs with showDown function.    
    def awardPot(self, winner):

        winner.chips += self.table.pot
        self.table.pot = 0

        
    def getCallAmount(self, player):

        return max(0,self.currentBet - player.currentContribution)

            



##_____________functions for evaluating the winning hand____________________"

def flush(cards, needed = 5):
    ##create a list for each suit in the hand
    suitsCounts = Counter(c.suit for c in cards)

    ##checks that the number of suits is 5 or more
    return any(count >= needed for count in suitsCounts.values())

##helper function for determining the high card of the flush when comparing two flushes
def flushKicker(cards, needed = 5):
    #create a dictionary for each suit, and appened each cards rank to the correct suit group
    suitGroups = {}
    for c in cards:
        suitGroups.setdefault(c.suit, []).append(RANK_VALUE[c.rank])

    #create a list of the best flush group with the needed amount depending on if buff is active or not  
    bestFlushRanks = None
    for suit, ranks in suitGroups.item():
        if len(ranks) >= needed:
            current = sorted(ranks, reverse=True)[:needed]
            if bestFlushRanks is None or current > bestFlushRanks:
                bestFlushRanks = current
    

    

    return bestFlushRanks

##returns the straight high card value if it is a straight, and None of not a straight
def straightValue(cards, needed = 5):

    ##create a list to hold the cards by value for comparison, then sort from low -> high removing duplicate
    ranks = sorted(set(RANK_VALUE[c.rank] for c in cards))

    #handles the wheel house straight
    if 14 in ranks:
        ranks = [1] + ranks

    streak = 1 
    bestHigh = None

    for i in range(1, len(ranks)):
        if ranks[i] == ranks[i - 1] + 1:
            streak += 1
            if streak >= needed:
                bestHigh = ranks[i]

            else:
                streak = 1

    return bestHigh


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

def bestHandOf7(cards7, player = None):

    best5 = None
    bestHandScore = None

    for hand5 in combinations(cards7, 5):

        handScore = evaluateHand(hand5, player)

        if bestHandScore == None or handScore > bestHandScore:

            bestHandScore = handScore
            best5 = list(hand5)

    return bestHandScore, best5

#fucntion used by bestHandOf7 to evaluate each players hand
def evaluateHand(cards, player = None):

    straightNeeded = 5
    flushNeeded = 5

    if player is not None:
        if player.buffs.get("fourCardStraight", False):
            straightNeeded = 4
        if player.buffs.get("fourCardFlush", False):
            flushNeeded = 4

    straight = straightValue(cards, straightNeeded)
    isFlush = flush(cards, flushNeeded)

    if straight is not None and isFlush:
        return 8 #, [straight]
    
    #variable to check if four of a kind or fullhouse
    pairType, PairKickers = evaluatePairs(cards)

    #if four of a kind or fullHouse exists
    if pairType >= 6:

        return pairType, PairKickers
    
    if isFlush:

        return 5, flushKicker(cards, flushNeeded)
    
    if straight is not None:

        return 4, [straight]
    
    #return the lower pair rank or high card if none of the above
    return pairType, PairKickers

def evaluateStartingHand(card1, card2):

    c1 = RANK_VALUE[card1.rank]
    c2 = RANK_VALUE[card2.rank]
    suited = card1.suit == card2.suit

    high = max(c1, c2)
    low = min(c1, c2)

    # if pair
    if c1 == c2:
        
        if c1 >= 11:
            return "strongest"
        
        elif c1 >= 7:
            return "strong"
        
        else:
            return "medium"
        
    if high == 14 and low >= 10:
        return "strong"
    
    if high >= 13 and low >= 10:
        return "medium"
    
    #suited connectors
    if suited and abs(c1 - c2) == 1 and high >= 9:
        return "medium"
    
    if suited and high >= 11:
        return "playable" 
        
    return "weak"

def evaluatePostFlopStrength(cards):

    handScore, best5 = bestHandOf7(cards)

    rank = handScore[0] if isinstance(handScore, tuple) else handScore

    if rank >= 5:
        return "strongest"
    
    elif rank >= 3:
        return "strong"
    
    elif rank >= 1:
        return "medium"
    
    else:
        return "weak"


def printHand(cards):
    return [(c.rank, c.suit) for c in cards]

def showCards(cards):
    return [f"({c.rank} of {c.suit})" for c in cards]

#_____________________TEST LOGIC________________________________________
if __name__ == "__main__":

    # Test 1: straight
    cards1 = [
        Card("ace", "spades"),
        Card("king", "hearts"),
        Card("queen", "clubs"),
        Card("jack", "diamonds"),
        Card("10", "spades"),
        Card("3", "hearts"),
        Card("2", "clubs")
    ]

    score1, best1 = bestHandOf7(cards1)
    print("TEST 1")
    print("All cards:", showCards(cards1))
    print("Best score:", score1)
    print("Best hand:", showCards(best1))
    print()

    # Test 2: flush
    cards2 = [
        Card("ace", "hearts"),
        Card("queen", "hearts"),
        Card("9", "hearts"),
        Card("7", "hearts"),
        Card("3", "hearts"),
        Card("king", "clubs"),
        Card("2", "spades")
    ]

    score2, best2 = bestHandOf7(cards2)
    print("TEST 2")
    print("All cards:", showCards(cards2))
    print("Best score:", score2)
    print("Best hand:", showCards(best2))
    print()

    # Test 3: full house
    cards3 = [
        Card("ace", "spades"),
        Card("ace", "hearts"),
        Card("ace", "clubs"),
        Card("king", "diamonds"),
        Card("king", "spades"),
        Card("4", "hearts"),
        Card("2", "clubs")
    ]

    score3, best3 = bestHandOf7(cards3)
    print("TEST 3")
    print("All cards:", showCards(cards3))
    print("Best score:", score3)
    print("Best hand:", showCards(best3))
    print()

print("TEST 4")

hand1 = [
    Card("ace","spades"),
    Card("ace","hearts"),
    Card("9","clubs"),
    Card("7","diamonds"),
    Card("3","spades"),
    Card("2","hearts"),
    Card("4","clubs")
]

hand2 = [
    Card("ace","diamonds"),
    Card("ace","clubs"),
    Card("9","hearts"),
    Card("7","clubs"),
    Card("2","spades"),
    Card("3","hearts"),
    Card("5","diamonds")
]

score1, best1 = bestHandOf7(hand1)
score2, best2 = bestHandOf7(hand2)

print("Hand1:", showCards(hand1), score1)
print("Hand2:", showCards(hand2), score2)

if score1 > score2:
    print("Hand1 wins")
elif score2 > score1:
    print("Hand2 wins")
else:
    print("Tie")

print()


print("TEST 6")

hand1 = [
    Card("ace","spades"),
    Card("ace","hearts"),
    Card("king","clubs"),
    Card("king","diamonds"),
    Card("5","spades"),
    Card("2","hearts"),
    Card("4","clubs")
]

hand2 = [
    Card("ace","diamonds"),
    Card("ace","clubs"),
    Card("king","hearts"),
    Card("king","spades"),
    Card("3","diamonds"),
    Card("2","clubs"),
    Card("4","hearts")
]

score1, best1 = bestHandOf7(hand1)
score2, best2 = bestHandOf7(hand2)

print("Hand1:", showCards(hand1), score1, HAND_TYPE[score1[0]])
print("Best1:", showCards(best1))
print("Hand2:", showCards(hand2), score2, HAND_TYPE[score2[0]])
print("Best2:", showCards(best2))

if score1 > score2:
    print("Hand1 wins")
elif score2 > score1:
    print("Hand2 wins")
else:
    print("Tie")

print()
      

