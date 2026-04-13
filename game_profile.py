from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field

from game_constants import SAVE_PATH

BUFF_POOL = [
    "Lucky Draw",
    "Bluff Master",
    "Intimidation",
    "Chip Shield",
    "High Roller",
    "Second Chance",
    "All-In Fury",
]



@dataclass
class PlayerProfile:
    chips: int = 300
    gold: int = 18
    poker_bonus: int = 0
    buffs: list[str] = field(default_factory=lambda: ["Lucky Draw"])
    beaten_bosses: set[str] = field(default_factory=set)
    tutorials_enabled: bool = True
    second_chance_used: bool = False

    def reset_round_state(self):
        self.second_chance_used = False

    def apply_buffs(self, player_strength, boss_strength):
        if "Lucky Draw" in self.buffs:
            player_strength += 0.06
        if "High Roller" in self.buffs:
            player_strength += 0.08
        if "Bluff Master" in self.buffs and random.random() < 0.35:
            player_strength += 0.10
        if "All-In Fury" in self.buffs and player_strength > 0.72:
            player_strength += 0.12
        if "Intimidation" in self.buffs:
            boss_strength -= 0.07
        if "Second Chance" in self.buffs and player_strength < 0.45 and not self.second_chance_used:
            player_strength = max(player_strength, random.uniform(0.45, 0.72))
            self.second_chance_used = True
        return min(1.0, player_strength), max(0.0, boss_strength)

    def reduce_loss(self, amount):
        if "Chip Shield" in self.buffs:
            return max(1, int(amount * 0.7))
        return amount

    def boss_reward_choices(self, difficulty, count=3):
        preferred = {
            "easy": ["Lucky Draw", "Bluff Master", "Intimidation"],
            "medium": ["Chip Shield", "High Roller", "Second Chance"],
            "hard": ["All-In Fury", "High Roller", "Second Chance"],
        }.get(difficulty, [])

        available = [buff for buff in BUFF_POOL if buff not in self.buffs]
        if not available:
            return []

        choices = []
        for buff in preferred:
            if buff in available and buff not in choices:
                choices.append(buff)
            if len(choices) >= count:
                return choices

        remaining = [buff for buff in available if buff not in choices]
        random.shuffle(remaining)
        choices.extend(remaining[: max(0, count - len(choices))])
        return choices

    def claim_buff(self, buff_name):
        if buff_name not in BUFF_POOL or buff_name in self.buffs:
            return False
        self.buffs.append(buff_name)
        return True

    def earn_gold(self, amount):
        self.gold += max(0, amount)

    def to_dict(self):
        return {
            "chips": self.chips,
            "gold": self.gold,
            "poker_bonus": self.poker_bonus,
            "buffs": self.buffs,
            "beaten_bosses": sorted(self.beaten_bosses),
            "tutorials_enabled": self.tutorials_enabled,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            chips=data.get("chips", 300),
            gold=data.get("gold", 18),
            poker_bonus=data.get("poker_bonus", 0),
            buffs=list(data.get("buffs", ["Lucky Draw"])),
            beaten_bosses=set(data.get("beaten_bosses", [])),
            tutorials_enabled=data.get("tutorials_enabled", True),
        )

    def save(self, path=SAVE_PATH):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def load(cls, path=SAVE_PATH):
        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
