import random

class Player:
    def __init__(self, name):
        self.name = name
        self.chips = 500  # Starting chips
        self.buffs = []
        self.second_chance_used = False
        self.beaten_bosses = []  # Track which difficulties beaten
        self.boss_chips = {
            "easy": 1000,
            "medium": 2000,
            "hard": 4000,
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

    def can_play_table(self, difficulty, cost=None):
        """Check if player has enough chips and progression for a table.

        The optional cost keeps old code working while the newer main game can
        pass dynamic buy-ins based on each boss's remaining chip stack.
        """
        requirements = {"easy": 100, "medium": 300, "hard": 800}
        required_chips = cost if cost is not None else requirements.get(difficulty, 100)

        if self.boss_chips.get(difficulty, 1) <= 0:
            return False, "This boss has already been cleaned out!"
        
        if self.chips < required_chips:
            return False, f"Need ${required_chips} to play at this table! (You have ${self.chips})"
        
        # Newer flow unlocks rooms by buffs; legacy code still records beaten bosses.
        if difficulty == "medium" and not (self.has_buff("Lucky Draw") or "easy" in self.beaten_bosses):
            return False, "Old Guard: 'Beat me first before you face the Lady.'"
        if difficulty == "hard" and not (self.has_buff("High Roller") or "medium" in self.beaten_bosses):
            return False, "Sharp Lady: 'You're not ready for him yet, darling.'"
        
        return True, "Ready to play!"

    def award_buff_for_boss(self, difficulty):
        """Give buff reward for beating a boss"""
        buff_rewards = {
            "easy": "Lucky Draw",
            "medium": "High Roller", 
            "hard": "All-In Fury"
        }
        if difficulty in buff_rewards and difficulty not in self.beaten_bosses:
            self.add_buff(buff_rewards[difficulty])
            self.beaten_bosses.append(difficulty)
            return buff_rewards[difficulty]
        return None
