import random

class Player:
    def __init__(self, name):
        self.name = name
        self.points = 0
        self.buffs = []
        self.second_chance_used = False

    def add_buff(self, buff_name):
        self.buffs.append(buff_name)
        print(f"{self.name} gained buff: {buff_name}")

    def apply_buffs(self, hand_strength, boss_strength=None):
        modified_strength = hand_strength

        print(f"\nBase hand strength: {hand_strength}")

        for buff in self.buffs:

            if buff == "Lucky Draw":
                modified_strength += 0.1
                print("✨ Lucky Draw increases hand strength!")

            elif buff == "High Roller":
                modified_strength += 0.15
                print("High Roller boosts confidence!")

            elif buff == "Bluff Master":
                if random.random() < 0.25:
                    modified_strength += 0.2
                    print("Bluff Master activated!")

            elif buff == "Second Chance":
                if modified_strength < 0.4 and not self.second_chance_used:
                    modified_strength = random.uniform(0.4, 0.7)
                    self.second_chance_used = True
                    print("Second Chance activated! Hand rerolled!")

            elif buff == "All-In Fury":
                if modified_strength > 0.7:
                    modified_strength += 0.2
                    print("All-In Fury activated! Big power boost!")

            elif buff == "Intimidation" and boss_strength is not None:
                boss_strength -= 0.1
                print("Intimidation lowers boss confidence!")

        modified_strength = min(modified_strength, 1.0)

        return modified_strength, boss_strength

    def reduce_loss(self, chip_loss):
        if "Chip Shield" in self.buffs:
            print("Chip Shield reduced chip loss!")
            return int(chip_loss * 0.7)
        return chip_loss


# -------- TEST AREA --------
if __name__ == "__main__":
    player = Player("Anthony")

    # Add ALL buffs
    player.add_buff("Lucky Draw")
    player.add_buff("High Roller")
    player.add_buff("Bluff Master")
    player.add_buff("Second Chance")
    player.add_buff("Intimidation")
    player.add_buff("Chip Shield")
    player.add_buff("All-In Fury")

    base_hand = 0.35
    boss_hand = 0.65

    print(f"\nBoss base strength: {boss_hand}")

    new_hand, new_boss = player.apply_buffs(base_hand, boss_hand)

    print("\nFinal player strength:", new_hand)
    print("Final boss strength:", new_boss)

    chip_loss = 100
    final_loss = player.reduce_loss(chip_loss)
    print("\nOriginal chip loss:", chip_loss)
    print("Final chip loss after shield:", final_loss)
