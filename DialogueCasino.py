import random

# -------- GENERIC DIALOGUE SYSTEM --------
dialogue = {
    "cocky": [
        "You really thought you had me there? That’s cute.",
        "I don’t lose. I just let people think they had a chance.",
        "All that confidence… for that hand?",
        "You should’ve folded while you still had chips.",
        "I’ve seen better bluffs from beginners.",
        "This table? Yeah, it’s mine now.",
        "Keep raising… you’re just digging deeper.",
        "I don’t chase luck. Luck chases me.",
        "Hope you brought more chips."
    ],
    "serious": [
        "Focus.",
        "I’ve already read your play.",
        "Your pattern is obvious.",
        "This ends now.",
        "You hesitate. That’s your weakness.",
        "I don’t gamble. I calculate.",
        "Every move you make… I’ve seen before.",
        "You’re predictable.",
        "No mistakes."
    ],
    "funny": [
        "Bro what are you DOING",
        "Ain’t no way you just played that",
        "You bluffing or just confused?",
        "Did you mean to do that?",
        "I respect the confidence… not the play though.",
        "You got heart. No skill, but heart.",
        "This isn’t UNO bro",
        "You good? Need a tutorial?"
    ],
    "straightup": [
        "That was a bad move.",
        "You’re overplaying your hand.",
        "You should’ve folded.",
        "That raise made no sense.",
        "You’re chasing losses.",
        "Think before you act.",
        "That’s not how you win.",
        "Play smarter."
    ],
    "smart": [
        "Your odds didn’t justify that.",
        "You ignored the pot odds.",
        "That bluff had no setup.",
        "You misread the board.",
        "Your range is weak here.",
        "You’re telegraphing your moves.",
        "That play was mathematically unsound."
    ],
    "win": [
        "And that’s game.",
        "Too easy.",
        "Told you.",
        "You walked right into that.",
        "That’s how it’s done.",
        "Better luck next time.",
        "I didn’t even try."
    ],
    "lose": [
        "Lucky.",
        "That won’t happen again.",
        "You got one. Don’t get comfortable.",
        "Alright… now I’m locked in.",
        "Enjoy it while it lasts.",
        "Now it gets serious."
    ],
    "casino": [
        "The house always wins… let’s see if you can prove me wrong.",
        "You’re in my territory now.",
        "Every chip you lose belongs to me.",
        "High stakes… high consequences.",
        "Walk away while you still can."
    ]
}


def get_dialogue(category):
    if category in dialogue:
        return random.choice(dialogue[category])
    return "..."

# -------- BOSS DIALOGUE (cover‑safe) --------
BOSS_DIALOGUE = {
    "easy": {
        "name": "Old Guard",
        "think": ["Let's see here...", "Give an old man a second...", "What are you up to, rookie?"],
        "fold": ["Too rich for my blood.", "You can have this one.", "I fold. My bones ache anyway."],
        "call": ["I'll match that.", "Call. Let's see 'em.", "Not scared of that bet."],
        "raise": ["Let's make it interesting.", "I raise. Don't test me.", "Back in my day, we bet bigger."],
        "check": ["Check.", "I'll hold.", "Your move."],
        "defeat": [
            "The Old Guard sighs heavily, pushing his empty chip tray away.",
            "'Well, you cleaned me out. Guess you got more street smarts than I thought, kid.'",
            "'Take this Lucky Draw technique. You'll need it against the Lady.'",
            "The Old Guard slowly stands up and leaves the table."
        ],
        "buff": "Lucky Draw",
        "door_lock": "The Old Guard barks: 'Earn your stripes here first, rookie!'"
    },
    "medium": {
        "name": "Sharp Lady",
        "think": ["Hmmm, darling...", "Let me calculate the odds...", "Are you bluffing?"],
        "fold": ["I know when to fold 'em.", "I won't fall for that.", "Take the pennies."],
        "call": ["I'll call you on that.", "Matching.", "Let's see it, darling."],
        "raise": ["Up the stakes.", "I'm raising. Can you handle it?", "Let's make this expensive."],
        "check": ["Check.", "Pass to you.", "Go ahead."],
        "defeat": [
            "The Sharp Lady smirks, shaking her head. 'Cleaned me out.'",
            "'I haven't lost like this in years. You're dangerously good for new blood.'",
            "'Take the High Roller technique. The Enforcer won't go easy on you.'",
            "She gathers her coat and vanishes into the shadows."
        ],
        "buff": "High Roller",
        "door_lock": "The Sharp Lady's voice echoes: 'You're not ready for him yet, darling.'"
    },
    "hard": {
        "name": "Enforcer",
        "think": ["...", "Trying to be smart?", "I'm watching you closely."],
        "fold": ["Fine.", "I'll wait for a better shot.", "Fold."],
        "call": ["Call.", "I'm not going anywhere.", "Matching."],
        "raise": ["Raise. Think you can match me?", "I'm pushing you out.", "More."],
        "check": ["Check.", "Move.", "Waiting."],
        "defeat": [
            "The Enforcer slams his fist on the table. 'Empty! Impossible!'",
            "'You've beaten us all. The boss wants to see the new recruit now.'",
            "'Take my All-In Fury. You'll need it for what comes next.'",
            "He steps aside, granting you access to the inner sanctum."
        ],
        "buff": "All-In Fury",
        "door_lock": "The door is bolted shut with heavy steel."
    }
}

# -------- STORY SCENES (cover‑intact) --------
STORY_PAGES = [
    [
        "CENTRAL INTELLIGENCE AGENCY - EYES ONLY",
        "Your mission, should you choose to accept it:",
        "Infiltrate 'The Syndicate', an underground poker ring.",
        "Your cover: a gifted but unknown poker player."
    ],
    [
        "The Syndicate operates from a hidden basement den.",
        "Three bosses control the ranks: The Old Guard, The Sharp Lady,",
        "and The Enforcer. Defeating each boss earns you a buff",
        "and access to the next room."
    ],
    [
        "Your goal: uncover the identity of the mysterious leader.",
        "Win the final poker game to extract intel and escape.",
        "If you lose at any stage, your cover is blown.",
        "Good luck, agent. The Agency is counting on you."
    ],
    [
        "Press any key to begin your infiltration..."
    ]
]

# -------- ENDING / GAME OVER --------
GAME_OVER_TEXT = [
    "Your cover is blown. The Syndicate has vanished.",
    "The Agency disavows all knowledge of your mission.",
    "You're left with nothing but debts and regret.",
    "",
    "GAME OVER"
]

ENDING_TEXT = [
    "AGENCY CHAT LOG - SUCCESSFUL EXFILTRATION",
    "",
    "You: 'I've identified the leader. He's a former intelligence officer.'",
    "Handler: 'Outstanding work, agent. We'll take it from here.'",
    "",
    "The Syndicate is dismantled. You're promoted.",
    "Press ESC to return to the world."
]
