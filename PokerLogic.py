import random
from collections import Counter
from itertools import combinations

SUIT = ["hearts", "diamonds", "spades", "clubs"]
RANK = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]
RANK_VALUE = { "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
               "jack": 11, "queen": 12, "king": 13, "ace": 14 }
HAND_TYPE = {8: "straight flush", 7: "four of a kind", 6: "full house", 5: "flush",
             4: "straight", 3: "three of a kind", 2: "two pair", 1: "one pair", 0: "high card"}
GAMEPHASE = ["blinds", "preflop", "bet", "flop", "bet", "turn", "bet", "river", "bet", "handCheck"]

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

class Player:
    def __init__(self, name):
        self.chips = 1000
        self.currentContribution = 0
        self.name = name
        self.hand = []
        self.folded = False
        # Poker buffs (in‑game hand modifiers)
        self.buffs = {
            "fourCardStraight": False,
            "fourCardFlush": False,
            
        }

    def reset_hand_state(self):
        self.currentContribution = 0
        self.hand = []
        self.folded = False

    def receiveCard(self, card: Card):
        self.hand.append(card)

class Boss(Player):
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
                return Action("raise", max(50, game.table.pot // 2))
            if strength == "strong" and random.random() < 0.4:
                return Action("raise", max(50, game.table.pot // 2))
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

class Action:
    def __init__(self, type, amount=0):
        self.type = type
        self.amount = amount

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

class Deck:
    def __init__(self):
        self.cards = [Card(r,s) for r in RANK for s in SUIT]
        self.shuffle()
    def shuffle(self):
        random.shuffle(self.cards)
    def drawCard(self) -> Card:
        return self.cards.pop()
    def deal(self, player, numCards):
        for c in range(numCards):
            player.receiveCard(self.drawCard())

class Table:
    def __init__(self):
        self.pot = 0
        self.communityCards = []
        self.burnCards = []
    def addCard(self, card: Card):
        self.communityCards.append(card)
    def reset(self):
        self.communityCards.clear()
        self.pot = 0
        self.burnCards.clear()

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

    def newHand(self):
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

        self.deck.deal(self.currentPlayer, 2)
        self.deck.deal(self.boss, 2)

        sb = min(self.smallBlind, self.human.chips)
        bb = min(self.bigBlind, self.boss.chips)

        self.human.chips -= sb
        self.human.currentContribution = sb

        self.boss.chips -= bb
        self.boss.currentContribution = bb

        self.table.pot = sb + bb
        self.currentBet = bb

    def dealCommunityCards(self):
        if self.phase == "flop":
            for c in range(3):
                self.table.addCard(self.deck.drawCard())
        elif self.phase == "turn":
            self.table.addCard(self.deck.drawCard())
        elif self.phase == "river":
            self.table.addCard(self.deck.drawCard())

    def changePhase(self):
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
        playerCards = self.currentPlayer.hand + self.table.communityCards
        bossCards = self.boss.hand + self.table.communityCards
        playerHandRank, playerBestHand = bestHandOf7(playerCards, self.currentPlayer)
        bossHandRank, bossBestHand = bestHandOf7(bossCards, self.boss)

        if playerHandRank > bossHandRank:
            self.currentPlayer.chips += self.table.pot
            self.table.pot = 0
            return self.currentPlayer, playerHandRank
        elif bossHandRank > playerHandRank:
            self.boss.chips += self.table.pot
            self.table.pot = 0
            return self.boss, bossHandRank
        else:
            splitPot = self.table.pot // 2
            self.currentPlayer.chips += splitPot
            self.boss.chips += splitPot
            self.table.pot = 0
            return None, playerHandRank
        
    def awardPot(self, winner):
        winner.chips += self.table.pot
        self.table.pot = 0

    def getCallAmount(self, player):
        return max(0, self.currentBet - player.currentContribution)

# ------------------- Hand evaluation -------------------
def flush(cards, needed=5):
    suitsCounts = Counter(c.suit for c in cards)
    return any(count >= needed for count in suitsCounts.values())

def flushKicker(cards, needed=5):
    suit_groups = {}
    for c in cards:
        suit_groups.setdefault(c.suit, []).append(RANK_VALUE[c.rank])
    best_flush_ranks = None
    for suit, ranks in suit_groups.items():
        if len(ranks) >= needed:
            current = sorted(ranks, reverse=True)[:needed]
            if best_flush_ranks is None or current > best_flush_ranks:
                best_flush_ranks = current
    return best_flush_ranks

def straightValue(cards, needed=5):
    ranks = sorted(set(RANK_VALUE[c.rank] for c in cards))
    if 14 in ranks:
        ranks = [1] + ranks
    streak = 1
    best_high = None
    for i in range(1, len(ranks)):
        if ranks[i] == ranks[i-1] + 1:
            streak += 1
            if streak >= needed:
                best_high = ranks[i]
        else:
            streak = 1
    return best_high

def evaluatePairs(cards):
    ranks = [RANK_VALUE[c.rank] for c in cards]
    counts = Counter(ranks)
    kickerGroups = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    if kickerGroups[0][1] == 4:
        quadRank = kickerGroups[0][0]
        kicker = [r for r in ranks if r != quadRank][0]
        return 7, [quadRank, kicker]
    if kickerGroups[0][1] == 3 and kickerGroups[1][1] == 2:
        tripRank = kickerGroups[0][0]
        pairRank = kickerGroups[1][0]
        return 6, [tripRank, pairRank]
    if kickerGroups[0][1] == 3:
        tripsRank = kickerGroups[0][0]
        kickers = sorted([r for r in ranks if r != tripsRank], reverse=True)
        return 3, [tripsRank] + kickers
    if kickerGroups[0][1] == 2 and kickerGroups[1][1] == 2:
        pair1 = kickerGroups[0][0]
        pair2 = kickerGroups[1][0]
        highPair = max(pair1, pair2)
        lowPair = min(pair1, pair2)
        kicker = [r for r in ranks if r != highPair and r != lowPair][0]
        return 2, [highPair, lowPair, kicker]
    if kickerGroups[0][1] == 2:
        pairRank = kickerGroups[0][0]
        kickers = sorted([r for r in ranks if r != pairRank], reverse=True)
        return 1, [pairRank] + kickers
    return 0, sorted(ranks, reverse=True)

def bestHandOf7(cards7, player=None):
    best5 = None
    bestHandScore = None
    for hand5 in combinations(cards7, 5):
        handScore = evaluateHand(hand5, player)
        if bestHandScore is None or handScore > bestHandScore:
            bestHandScore = handScore
            best5 = list(hand5)
    return bestHandScore, best5

def evaluateHand(cards, player=None):
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
        return 8
    pairType, pairKickers = evaluatePairs(cards)
    if pairType >= 6:
        return pairType, pairKickers
    if isFlush:
        return 5, flushKicker(cards, flushNeeded)
    if straight is not None:
        return 4, [straight]
    return pairType, pairKickers

def evaluateStartingHand(card1, card2):
    c1 = RANK_VALUE[card1.rank]
    c2 = RANK_VALUE[card2.rank]
    suited = card1.suit == card2.suit
    high = max(c1, c2)
    low = min(c1, c2)
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