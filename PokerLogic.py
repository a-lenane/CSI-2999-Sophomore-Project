from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations


SUIT = ["hearts", "diamonds", "spades", "clubs"]
RANK = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]
RANK_VALUE = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "jack": 11,
    "queen": 12,
    "king": 13,
    "ace": 14,
}
HAND_TYPE = {
    8: "straight flush",
    7: "four of a kind",
    6: "full house",
    5: "flush",
    4: "straight",
    3: "three of a kind",
    2: "two pair",
    1: "one pair",
    0: "high card",
}
GAMEPHASE = ["blinds", "preflop", "bet", "flop", "bet", "turn", "bet", "river", "bet", "handCheck"]


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"Card(rank={self.rank!r}, suit={self.suit!r})"


@dataclass
class Player:
    name: str
    chips: int = 1000
    currentContribution: int = 0
    hand: list[Card] = field(default_factory=list)
    folded: bool = False
    buffs: list[str] = field(default_factory=list)

    def receiveCard(self, card: Card):
        self.hand.append(card)

    def reset_for_hand(self):
        self.currentContribution = 0
        self.hand.clear()
        self.folded = False


@dataclass
class Boss(Player):
    personality: str = "serious"
    difficulty: str = "easy"


class Action:
    def __init__(self, type, amount=0):
        self.type = type
        self.amount = amount

    def processAction(self, player, game):
        if self.type == "fold":
            player.folded = True
            return

        if self.type == "check":
            return

        to_call = max(0, game.currentBet - player.currentContribution)
        if self.type == "call":
            total = min(player.chips, to_call)
            player.chips -= total
            game.table.pot += total
            player.currentContribution += total
            return

        if self.type == "raise":
            raise_size = max(0, self.amount)
            total = min(player.chips, to_call + raise_size)
            player.chips -= total
            game.table.pot += total
            player.currentContribution += total
            game.currentBet = max(game.currentBet, player.currentContribution)


class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for rank in RANK for suit in SUIT]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def drawCard(self) -> Card:
        return self.cards.pop()

    def deal(self, player, numCards):
        for _ in range(numCards):
            player.receiveCard(self.drawCard())


class Table:
    def __init__(self):
        self.pot = 0
        self.communityCards = []
        self.burnCards = []

    def addCard(self, card: Card):
        self.communityCards.append(card)

    def reset(self):
        self.pot = 0
        self.communityCards.clear()
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

    def newHand(self):
        self.deck = Deck()
        self.table.reset()
        self.currentPlayer.reset_for_hand()
        self.boss.reset_for_hand()
        self.phaseIndex = 0
        self.phase = GAMEPHASE[self.phaseIndex]
        self.currentBet = 0
        self.handWinner = None
        self.playerActed = False
        self.bossActed = False
        self.showdownDone = False
        self.deck.deal(self.currentPlayer, 2)
        self.deck.deal(self.boss, 2)

    def dealCommunityCards(self):
        if self.phase == "flop":
            for _ in range(3):
                self.table.addCard(self.deck.drawCard())
        elif self.phase in {"turn", "river"}:
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
        player_score, _ = bestHandOf7(self.currentPlayer.hand + self.table.communityCards)
        boss_score, _ = bestHandOf7(self.boss.hand + self.table.communityCards)
        comparison = compare_scores(player_score, boss_score)
        if comparison > 0:
            self.currentPlayer.chips += self.table.pot
            self.table.pot = 0
            return self.currentPlayer, player_score
        if comparison < 0:
            self.boss.chips += self.table.pot
            self.table.pot = 0
            return self.boss, boss_score
        split = self.table.pot // 2
        self.currentPlayer.chips += split
        self.boss.chips += self.table.pot - split
        self.table.pot = 0
        return None, player_score

    def awardPot(self, winner):
        winner.chips += self.table.pot
        self.table.pot = 0

    def getCallAmount(self, player):
        return max(0, self.currentBet - player.currentContribution)


def flush(cards):
    return len(set(card.suit for card in cards)) == 1


def flushKicker(cards):
    return sorted([RANK_VALUE[c.rank] for c in cards], reverse=True)


def straightValue(cards):
    ranks = sorted(set(RANK_VALUE[c.rank] for c in cards))
    if len(ranks) != 5:
        return None
    if ranks == [2, 3, 4, 5, 14]:
        return 5
    for idx in range(4):
        if ranks[idx] + 1 != ranks[idx + 1]:
            return None
    return ranks[-1]


def evaluatePairs(cards):
    ranks = [RANK_VALUE[c.rank] for c in cards]
    counts = Counter(ranks)
    groups = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)

    if groups[0][1] == 4:
        quad = groups[0][0]
        kicker = [r for r in ranks if r != quad][0]
        return 7, [quad, kicker]

    if groups[0][1] == 3 and groups[1][1] == 2:
        return 6, [groups[0][0], groups[1][0]]

    if groups[0][1] == 3:
        trips = groups[0][0]
        kickers = sorted([r for r in ranks if r != trips], reverse=True)
        return 3, [trips] + kickers

    if groups[0][1] == 2 and groups[1][1] == 2:
        high_pair = max(groups[0][0], groups[1][0])
        low_pair = min(groups[0][0], groups[1][0])
        kicker = [r for r in ranks if r not in (high_pair, low_pair)][0]
        return 2, [high_pair, low_pair, kicker]

    if groups[0][1] == 2:
        pair_rank = groups[0][0]
        kickers = sorted([r for r in ranks if r != pair_rank], reverse=True)
        return 1, [pair_rank] + kickers

    return 0, sorted(ranks, reverse=True)


def evaluateHand(cards):
    straight = straightValue(cards)
    is_flush = flush(cards)
    if straight is not None and is_flush:
        return 8, [straight]
    pair_type, kickers = evaluatePairs(cards)
    if pair_type >= 6:
        return pair_type, kickers
    if is_flush:
        return 5, flushKicker(cards)
    if straight is not None:
        return 4, [straight]
    return pair_type, kickers


def bestHandOf7(cards7):
    if len(cards7) < 5:
        raise ValueError("bestHandOf7 requires at least 5 cards")
    best_score = None
    best_five = None
    for hand5 in combinations(cards7, 5):
        score = evaluateHand(hand5)
        if best_score is None or score > best_score:
            best_score = score
            best_five = list(hand5)
    return best_score, best_five


def compare_scores(score1, score2):
    if score1 > score2:
        return 1
    if score1 < score2:
        return -1
    return 0


def score_to_value(score):
    hand_rank, kickers = score
    total = float(hand_rank)
    for idx, kicker in enumerate(kickers):
        total += kicker / (15 ** (idx + 1))
    return total


def score_label(score):
    return HAND_TYPE[score[0]]


def showCards(cards):
    return [f"({c.rank} of {c.suit})" for c in cards]
