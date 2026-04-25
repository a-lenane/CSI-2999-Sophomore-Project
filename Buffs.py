import random

class Player:
    def __init__(self, name):
        self.name = name
        self.chips = 500  # Starting chips
        self.buffs = []
        self.second_chance_used = False
        self.beaten_bosses = []  # Track which difficulties beaten (legacy)
        
        # Persistent boss chip stacks
        self.boss_chips = {
            "easy": 1000,
            "medium": 2000,
            "hard": 4000
        }

    def add_buff(self, buff_name):
        if buff_name not in self.buffs:
            self.buffs.append(buff_name)
            print(f"{self.name} gained buff: {buff_name}")
            return True
        return False

    def has_buff(self, buff_name):
        return buff_name in self.buffs

    def apply_buffs(self, hand_strength, boss_strength=None):
        modified_strength = hand_strength

        for buff in self.buffs:
            if buff == "Lucky Draw":
                modified_strength += 0.1
            elif buff == "High Roller":
                modified_strength += 0.15
            elif buff == "Bluff Master":
                if random.random() < 0.25:
                    modified_strength += 0.2
            elif buff == "Second Chance":
                if modified_strength < 0.4 and not self.second_chance_used:
                    modified_strength = random.uniform(0.4, 0.7)
                    self.second_chance_used = True
            elif buff == "All-In Fury":
                if modified_strength > 0.7:
                    modified_strength += 0.2
            elif buff == "Intimidation" and boss_strength is not None:
                boss_strength -= 0.1

        modified_strength = min(modified_strength, 1.0)
        return modified_strength, boss_strength

    def reduce_loss(self, chip_loss):
        if "Chip Shield" in self.buffs:
            return int(chip_loss * 0.7)
        return chip_loss

    def can_play_table(self, difficulty, cost):
        """Check if player has enough chips and has the required buffs for progression"""
        if self.boss_chips[difficulty] <= 0:
            return False, "This boss has already been cleaned out!"

        if self.chips < cost:
            return False, f"Need ${cost} to play at this table! (You have ${self.chips})"
        
        # Progression relies on holding the previous boss's buff
        if difficulty == "medium" and not self.has_buff("Lucky Draw"):
            return False, "Old Guard: 'Beat me first before you face the Lady.'"
        if difficulty == "hard" and not self.has_buff("High Roller"):
            return False, "Sharp Lady: 'You're not ready for him yet, darling.'"
        
        return True, "Ready to play!"