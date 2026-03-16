import random

def apply_player_buffs(hand_strength, boss_strength, player_buffs, boss_type):

    boss_resistance = {
        "easy": {
            "Lucky Draw": 1.0,
            "High Roller": 1.0,
            "Bluff Master": 1.0,
            "Second Chance": 1.0,
            "Intimidation": 1.0,
            "All-In Fury": 1.0
        },

        "medium": {
            "Lucky Draw": 0.75,
            "High Roller": 0.75,
            "Bluff Master": 0.5,
            "Second Chance": 0.8,
            "Intimidation": 0.6,
            "All-In Fury": 0.8
        },

        "hard": {
            "Lucky Draw": 0.5,
            "High Roller": 0.5,
            "Bluff Master": 0.2,
            "Second Chance": 0.6,
            "Intimidation": 0.3,
            "All-In Fury": 0.7
        }
    }

    resistance = boss_resistance[boss_type]

    print("\nBoss difficulty:", boss_type)

    for buff in player_buffs:

        if buff == "Lucky Draw":
            boost = 0.1 * resistance["Lucky Draw"]
            hand_strength += boost
            print(f"Lucky Draw boost: {boost:.2f}")

        elif buff == "High Roller":
            boost = 0.15 * resistance["High Roller"]
            hand_strength += boost
            print(f"High Roller boost: {boost:.2f}")

        elif buff == "Bluff Master":
            chance = 0.25 * resistance["Bluff Master"]
            if random.random() < chance:
                hand_strength += 0.2
                print("Bluff worked!")
            else:
                print("Boss saw through the bluff!")

        elif buff == "Second Chance":
            if hand_strength < 0.4:
                hand_strength = random.uniform(0.4,0.7)
                print("Second Chance activated!")

        elif buff == "Intimidation":
            reduction = 0.1 * resistance["Intimidation"]
            boss_strength -= reduction
            print(f"Boss confidence lowered by {reduction:.2f}")

        elif buff == "All-In Fury":
            if hand_strength > 0.7:
                boost = 0.2 * resistance["All-In Fury"]
                hand_strength += boost
                print("All-In Fury boosted your hand!")

        elif buff == "Chip Shield":
            print("Chip Shield ready (reduces chip loss).")

    return hand_strength, boss_strength


# -------- TEST RUN --------

player_buffs = [
    "Lucky Draw",
    "High Roller",
    "Bluff Master",
    "Second Chance",
    "Intimidation",
    "Chip Shield",
    "All-In Fury"
]

player_hand = 0.35
boss_hand = 0.65


print("Starting test run...")

for boss in ["easy", "medium", "hard"]:
    
    new_player, new_boss = apply_player_buffs(
        player_hand,
        boss_hand,
        player_buffs,
        boss
    )

    print("Final Player Strength:", round(new_player,2))
    print("Final Boss Strength:", round(new_boss,2))
