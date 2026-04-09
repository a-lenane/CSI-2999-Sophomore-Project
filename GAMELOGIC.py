import random
from PokerLogic import Card, Deck, bestHandOf7, RANK_VALUE

SUITS = ["spades", "hearts", "diamonds", "clubs"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]

def deck_randomizer():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append((suit, rank))  # Fixed: append tuple
    random.shuffle(deck)
    return deck

def deck_cardpick(deck):
    card = deck.pop()
    return card, deck

def opponent_cards(difficulty, deck):
    opponent_hand = []
    for i in range(2):
        card, deck = deck_cardpick(deck)
        opponent_hand.append(card)
    return opponent_hand, deck

def pool_cards(deck):
    pool_cards = []
    for i in range(5):
        card, deck = deck_cardpick(deck)
        pool_cards.append(card)
    return pool_cards, deck

def player_hand(deck):
    player_hand = []
    for i in range(2):
        card, deck = deck_cardpick(deck)
        player_hand.append(card)
    return player_hand, deck

def score_method(player_hand, opponent_hand, pool_cards):
    # Convert tuple cards to Card objects for evaluation
    def to_card(card_tuple):
        suit, rank = card_tuple
        return Card(rank, suit)
    
    player_cards = [to_card(c) for c in player_hand] + [to_card(c) for c in pool_cards]
    opponent_cards = [to_card(c) for c in opponent_hand] + [to_card(c) for c in pool_cards]
    
    player_score, _ = bestHandOf7(player_cards)
    opponent_score, _ = bestHandOf7(opponent_cards)
    
    return player_score, opponent_score