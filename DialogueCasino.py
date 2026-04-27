# DialogueCasino.py
# -------- BOSS DIALOGUE (cover‑safe) --------
BOSS_DIALOGUE = {
    "easy": {
        "name": "Old Guard",
        "think": ["Let's see here...", "Give an old man a second...", "What are you up to, rookie?", "Let me test my luck."],
        "fold": ["Too rich for my blood.", "You can have this one.", "I fold. My bones ache anyway.", "I'll let you take it."],
        "call": ["I'll match that.", "Call. Let's see 'em.", "Not scared of that bet.", "You think I am scared?"],
        "raise": ["Let's make it interesting.", "I raise. Don't test me.", "Back in my day, we bet bigger.", "RAISE the roof."],
        "check": ["Check.", "I'll hold.", "Your move.", "Checkmate"],
        "defeat": [
            "The Old Guard sighs heavily, pushing his empty chip tray away.",
            "'Well, you cleaned me out. Guess you got more street smarts than I thought, kid.'",
            "'Take this 4-card straight technique. You'll need it against the Slick Ruffian.'",
            "The Old Guard slowly stands up and leaves the table."
        ],
        "buff": "fourCardStraight",
        "door_lock": "The Old Guard barks: 'Earn your stripes here first, rookie!'"
    },
    "medium": {
        "name": "Slick Ruffian",
        "think": ["Hmmm, partner...", "Let me calculate the odds...", "Are you bluffing?", "Let's see how slick I am."],
        "fold": ["I know when to fold 'em.", "I won't fall for that.", "Take the pennies.", "Fold 'em, cowpoke."],
        "call": ["I'll call you on that.", "Matching.", "Let's see it, partner.", "I'll call it, friend."],
        "raise": ["Up the stakes.", "I'm raising. Can you handle it?", "Let's make this expensive.", "Why the long face, honey?"],
        "check": ["Check.", "Pass to you.", "Go ahead.", "Take it."],
        "defeat": [
            "The Slick Ruffian smirks, shaking her head. 'Cleaned me out.'",
            "'I haven't lost like this in years. You're dangerously good for new blood.'",
            "'Take the 4-card flush technique. The Enforcer won't go easy on you.'",
            "She gathers her coat and vanishes into the shadows."
        ],
        "buff": "fourCardFlush",
        "door_lock": "The Slick Ruffian's voice echoes: 'You're not ready for him yet, partner.'"
    },
    "hard": {
        "name": "Enforcer",
        "think": ["...", "Trying to be smart?", "I'm watching you closely.", "I can read your mind."],
        "fold": ["Fine.", "I'll wait for a better shot.", "Fold.", "Take the little bucks."],
        "call": ["Call.", "I'm not going anywhere.", "Matching.", "Ring ring, I'm calling."],
        "raise": ["Raise. Think you can match me?", "I'm pushing you out.", "More.", "Let's spice it up."],
        "check": ["Check.", "Move.", "Waiting."],
        "defeat": [
            "The Enforcer slams his fist on the table. 'Empty! Impossible!'",
            "'You've beaten us all. The boss wants to see the new recruit now.'",
            "'Take my peekBossCard. You'll need it for what comes next.'",
            "He steps aside, granting you access to the inner sanctum."
        ],
        "buff": "peekBossCard",
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
        "Three bosses control the ranks: The Old Guard, The Slick Ruffian,",
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
