import random

# EASY DIFFICULTY
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


# MEDIUM DIFFICULTY
def medium_ai(hand_strength, pot_odds):
    print("\nCard Shark: 'You made it this far? Not bad. Let’s see what you’ve got.'")

    if hand_strength > 0.75:
        print("Card Shark: 'Heh. I like my odds. I raise.'")
        return "raise"

    elif hand_strength > pot_odds:
        print("Card Shark: 'The numbers favor me... I call.'")
        return "call"

    else:
        print("Card Shark: 'Not worth the risk. I fold.'")
        return "fold"


# HARD DIFFICULTY (Boss Style)
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

    # Bluff chance
    if random.random() < 0.15:
        print("Casino Boss: 'Sometimes… confidence is all you need. I raise.'")
        return "raise"

    print("Casino Boss: 'Know when to walk away. I fold.'")
    return "fold"
