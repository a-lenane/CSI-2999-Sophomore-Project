import random
from PokerLogic import RANK_VALUE, Card, bestHandOf7

def evaluate_hand_strength(hand, pool_cards, visible_pool_count):
    """Calculate hand strength as float 0-1 based on actual poker hand ranking"""
    def to_card(card_tuple):
        suit, rank = card_tuple
        return Card(rank, suit)
    
    visible_cards = [to_card(c) for c in hand]
    for i in range(min(visible_pool_count, len(pool_cards))):
        visible_cards.append(to_card(pool_cards[i]))
    
    if len(visible_cards) < 5:
        # Not enough cards yet, estimate based on high card
        values = [RANK_VALUE[Card(r, s).rank] for (s, r) in hand]
        return max(values) / 14.0
    
    result = bestHandOf7(visible_cards)
    # bestHandOf7 returns (score, best_hand)
    # score can be an int or a tuple (from evaluateHand)
    if isinstance(result, tuple) and len(result) == 2:
        score = result[0]
        # If score is a tuple, extract the hand rank (first element)
        if isinstance(score, tuple):
            score = score[0]
    else:
        score = result
    return score / 8.0

# --- AI functions remain unchanged ---
def easy_ai(hand_strength):
    print("\nRookie Gambler: 'Ohhh you wanna battle? You won't get past me that easily!'")
    if hand_strength > 0.7:
        print("Rookie Gambler: 'Wait... I actually have something good?! I'm going ALL IN!!'")
        return "raise"
    elif hand_strength > 0.4:
        move = random.choice(["call", "fold"])
        print("Rookie Gambler: 'Uh... I think I'll just play it safe...'")
        return move
    else:
        print("Rookie Gambler: 'This hand is terrible... I fold!'")
        return "fold"

def medium_ai(hand_strength, pot_odds):
    print("\nCard Shark: 'You made it this far? Not bad. Let's see what you've got.'")
    if hand_strength > 0.75:
        print("Card Shark: 'Heh. I like my odds. I raise.'")
        return "raise"
    elif hand_strength > pot_odds:
        print("Card Shark: 'The numbers favor me... I call.'")
        return "call"
    else:
        print("Card Shark: 'Not worth the risk. I fold.'")
        return "fold"

def hard_ai(hand_strength, pot_odds, player_aggressive):
    print("\nCasino Boss: 'So you're the one trying to climb my tables?'")
    print("Casino Boss: 'You think you can take my chips? After beating my underlings?'")
    if hand_strength > 0.8:
        print("Casino Boss: 'Pathetic. This round is mine. I raise.'")
        return "raise"
    if player_aggressive and hand_strength > 0.6:
        print("Casino Boss: 'I see through your aggression. I raise you.'")
        return "raise"
    if hand_strength > pot_odds:
        print("Casino Boss: 'I'll allow this. I call.'")
        return "call"
    if random.random() < 0.15:
        print("Casino Boss: 'Sometimes… confidence is all you need. I raise.'")
        return "raise"
    print("Casino Boss: 'Know when to walk away. I fold.'")
    return "fold"