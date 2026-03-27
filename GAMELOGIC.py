import random
import ChipsAndCode # TODO implementation using this file 
import buffs # TODO implementation using this file 
import BossReactions # TODO implementation using this file 
import DifficultiesCodeAndChips # TODO implementation using this file 

SUITS = ["spades", "hearts", "diamonds", "clubs"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]

def deck_randomizer():
    deck = []

    for suit in SUITS:
        for rank in RANKS:
            deck.append(suit, rank)

    random.shuffle(deck)
    return deck

def deck_cardpick(deck):
    card = deck.pop()
    return card, deck

def dealer_cards(difficulty, deck):
    dealer_hand = []
    
    if difficulty == "easy":
        i = 0
        while i < 2:
            card, deck = deck_cardpick(deck) 
            dealer_hand.append(card)
            i += 1
            
    elif difficulty == "medium":
        #todo
        pass 
    elif difficulty == "hard":
        #todo
        pass

    return dealer_hand, deck
  
def pool_cards(deck):
    pool_cards = []
    i = 0
    while i < 5:
        card, deck = deck_cardpick(deck) 
        pool_cards.append(card)
        i += 1
    return pool_cards, deck

def player_hand():
    # add abilities as a input (todo)
    player_hand = []
    i = 0
    # if ability then xyz, else:
    while i < 5:
        card, deck = deck_cardpick(deck) 
        player_hand.append(card)
        i += 1
    return player_hand, deck

# def ability_track(): (using buffs.py?)

def score_method(player_hand, dealer_hand, pool_cards):

    final_player_hand = player_hand + pool_cards
    final_dealer_hand = dealer_hand + pool_cards

    from ChipsAndCode import bestHandOf7

    #todo
    pass





def fold_method():
    #gui
    pass

def bet_method():
    #gui
    pass

def main():
    #initialize
    pot = 0
    deck = deck_randomizer()

    # setup pool cards early (for possible forsight ability, also easier)
    pool_cards, deck = pool_cards(deck)

    while True:
        
        
        False

    """game loop:
    - phase 1: draw pool cards (keeping hidden untill needed!)
    - phase 2: draw dealer + player cards 
    - phase 3: call/raise/fold 
    - next: reveal first 3 pool cards
    - next: call/raise/fold 
    - next: reveal next pool card
    - next: check/raise
    - next: reveal last pool card
    - next: call/raise/fold
    - last: check hands and determine winner. pot goes to winner. 

    - additionally: deal with pot, deal with abilities, deal with dialouge.
    """

