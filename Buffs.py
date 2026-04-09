import random

class Player:
    def __init__(self, name):
        self.name = name
        self.chips = 500  # Starting chips
        self.buffs = []
        self.second_chance_used = False
        self.beaten_bosses = []  # Track which difficulties beaten

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

    def can_play_table(self, difficulty):
        """Check if player has enough chips and has beaten previous difficulties"""
        requirements = {"easy": 100, "medium": 300, "hard": 800}
        required_chips = requirements.get(difficulty, 100)
        
        if self.chips < required_chips:
            return False, f"Need {required_chips} chips to play at this table! (You have {self.chips})"
        
        # Must beat easy before medium, medium before hard
        if difficulty == "medium" and "easy" not in self.beaten_bosses:
            return False, "You must beat the Easy boss first!"
        if difficulty == "hard" and "medium" not in self.beaten_bosses:
            return False, "You must beat the Medium boss first!"
        
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