import random


dialogue = {
    "cocky": [
        "You really thought you had me there?",
        "Keep betting. I like free chips.",
        "That confidence is expensive.",
        "You walked into my room."
    ],
    "serious": [
        "Focus.",
        "Your timing just changed.",
        "I already have the line mapped out.",
        "No wasted moves."
    ],
    "funny": [
        "This is not UNO, friend.",
        "Bold move. Weird move. Bold though.",
        "You bluffing or freestyling?",
        "I respect the chaos."
    ],
    "straightup": [
        "That was a bad move.",
        "You are overplaying this hand.",
        "Fold next time.",
        "Think one street ahead."
    ],
    "smart": [
        "Your odds did not justify that.",
        "You ignored the board texture.",
        "That line is too transparent.",
        "Math is not on your side."
    ],
    "win": [
        "And that is game.",
        "House edge.",
        "Too clean.",
        "You fed the pot right to me."
    ],
    "lose": [
        "Fine. One hand.",
        "Enjoy it while it lasts.",
        "Good hit."
    ],
    "casino": [
        "The house always leans forward.",
        "High stakes. High pressure.",
        "Every table here remembers winners.",
    ],
}

PERSONALITY_TO_CATEGORY = {
    "easy": "funny",
    "medium": "smart",
    "hard": "cocky",
    "rookie": "funny",
    "card_shark": "smart",
    "boss": "serious",
}


def get_dialogue(category, fallback="serious"):
    chosen = dialogue.get(category) or dialogue.get(fallback) or ["..."]
    return random.choice(chosen)


def get_boss_line(difficulty, outcome=None):
    if outcome == "win":
        return get_dialogue("win")
    if outcome == "lose":
        return get_dialogue("lose")
    category = PERSONALITY_TO_CATEGORY.get(difficulty, "casino")
    return get_dialogue(category)
