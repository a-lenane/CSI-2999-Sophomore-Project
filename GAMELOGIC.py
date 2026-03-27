import random
import ChipsAndCode # TODO implementation using this file 
import Buffs # TODO implementation using this file 
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

def opponent_cards(difficulty, deck):
    opponent_hand = []
    
    if difficulty == "easy":
        i = 0
        while i < 2:
            card, deck = deck_cardpick(deck) 
            opponent_hand.append(card)
            i += 1
            
    elif difficulty == "medium":
        #TODO 
        # only implementation here is to make the 'dealer' give the opponent better cards using some kind of algorithm from DifficultiesCodeAndChips.py
        # can pass pool cards to the 'dealer' to help him pick better cards or smth from main() if difficulty is selected prior to here <--- TODO add difficulty selection and pass it from main.py to here
        pass 
    elif difficulty == "hard":
        #TODO 
        pass

    return opponent_hand, deck
  
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

# def ability_track(): TODO! buffs.py needs to be directly implemented in this code! not just a isolated function, but can use if statements directly in other functions to check for buff purposes!)
# I might make this the shop or 'control' for what buffs are active, using data from map.py or main.py to determine what buffs the player has active. then, can use if statements for if buff do xyz directly in functions
# ex: i will implement forsight, where if buff is active player will be allowed to see the top 5 cards of the pool draw pile after the first 3 are drawn

def score_method(player_hand, opponent_hand, pool_cards):

    final_player_hand = player_hand + pool_cards
    final_opponent_hand = opponent_hand + pool_cards

    from ChipsAndCode import bestHandOf7

    #todo
    pass





def fold_method():
    #gui (does nothing anyways ig)
    pass

def bet_method():
    #gui TODO
    pass

def main():
    #initialize
    pot = 0
    deck = deck_randomizer()

    # setup pool cards early (for possible forsight ability, also easier)
    pool_cards, deck = pool_cards(deck)

    while True:
        
        
        False

    """game loop: TODO
    - phase 1: draw pool cards (keeping hidden untill needed!)
    - phase 2: draw opponent + player cards 
    - phase 3: call/raise/fold (player + opponent (AI LOGIC))
    - next: reveal first 3 pool cards
    - next: call/raise/fold (player + opponent (AI LOGIC))
    - next: reveal next pool card
    - next: check/raise (player + opponent (AI LOGIC))
    - next: reveal last pool card
    - next: call/raise/fold (player + opponent (AI LOGIC))
    - last: check hands and determine winner. pot goes to winner. 

    - additionally: deal with pot, deal with abilities, deal with dialouge.
    """

