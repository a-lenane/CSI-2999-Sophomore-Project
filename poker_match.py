from __future__ import annotations

import random

import pygame

from DialogueCasino import get_boss_line
from PokerLogic import Deck, HAND_TYPE, RANK_VALUE, bestHandOf7, compare_scores, score_to_value
from asset_pipeline import scale_to_fit
from game_constants import HEIGHT, WIDTH


class PokerTableMatch:
    def __init__(self, screen, assets, player_profile, npc, fonts):
        self.screen = screen
        self.assets = assets
        self.player_profile = player_profile
        self.npc = npc
        self.font, self.small_font, self.big_font = fonts
        self.deck = Deck()
        self.player_hand = [self.deck.drawCard(), self.deck.drawCard()]
        self.boss_hand = [self.deck.drawCard(), self.deck.drawCard()]
        self.community = []
        self.stage = 0
        self.stage_names = ["Pre-Flop", "Flop", "Turn", "River", "Showdown"]
        self.pot = 40
        self.current_bet = 0
        self.player_contribution = 20
        self.boss_contribution = 20
        self.enemy_stack = max(200, 220 + (80 if npc.difficulty == "medium" else 180 if npc.difficulty == "hard" else 0))
        self.player_profile.chips -= 20
        self.enemy_stack -= 20
        self.game_over = False
        self.result_text = ""
        self.winner = None
        self.pending_response = False
        self.last_dialogue = f"{npc.name}: {npc.dialogue}"
        self.action_log = [self.last_dialogue]
        self.street_banner = self.stage_names[self.stage]
        self.street_timer = 90
        self.bluff_pressure = 0.0
        self.last_reward_text = ""
        self.reward_choices = []
        self.awaiting_reward_pick = False
        self.player_profile.reset_round_state()

    def log(self, message):
        self.last_dialogue = message
        self.action_log.append(message)
        self.action_log = self.action_log[-4:]

    def set_stage_banner(self, text):
        self.street_banner = text
        self.street_timer = 90

    def visible_count(self):
        return len(self.community)

    def get_call_amount(self):
        return max(0, self.current_bet - self.player_contribution)

    def current_raise_amount(self):
        return min(self.player_profile.chips, 40 + self.stage * 20 + self.player_profile.poker_bonus * 10)

    def get_strength(self, hand, visible):
        cards = hand + self.community[:visible]
        if len(cards) < 5:
            ranks = sorted((RANK_VALUE[c.rank] for c in hand), reverse=True)
            pair_bonus = 0.18 if len(ranks) == 2 and ranks[0] == ranks[1] else 0.0
            suited_bonus = 0.05 if hand[0].suit == hand[1].suit else 0.0
            connected_bonus = 0.04 if abs(ranks[0] - ranks[1]) == 1 else 0.0
            return min(1.0, ranks[0] / 14.0 + pair_bonus + suited_bonus + connected_bonus)
        score, _ = bestHandOf7(cards)
        return min(1.0, score_to_value(score) / 9.0)

    def award_victory_extras(self):
        gold_reward = {"easy": 4, "medium": 7, "hard": 12}.get(self.npc.difficulty, 4)
        self.player_profile.earn_gold(gold_reward)
        self.last_reward_text = f"+{gold_reward} gold"
        return gold_reward

    def ai_action(self, player_aggressive=False):
        visible = self.visible_count()
        strength = max(0.0, self.get_strength(self.boss_hand, visible) - self.bluff_pressure)
        to_call = max(0, self.current_bet - self.boss_contribution)
        pot_odds = to_call / max(1, self.pot + to_call)
        if self.npc.difficulty == "easy":
            if strength > 0.78:
                return "raise"
            if strength + 0.12 >= pot_odds:
                return "call"
            return random.choice(["call", "fold", "fold"])
        if self.npc.difficulty == "hard":
            if strength > 0.64:
                return "raise"
            if player_aggressive and strength > 0.48:
                return "call"
            if strength + 0.03 >= pot_odds:
                return "call"
            return "raise" if random.random() < 0.16 else "fold"
        if strength > 0.70:
            return "raise"
        if strength + 0.06 >= pot_odds:
            return "call"
        return "fold"

    def progress_street(self):
        self.current_bet = 0
        self.player_contribution = 0
        self.boss_contribution = 0
        self.pending_response = False
        self.bluff_pressure = 0.0
        if self.stage == 0:
            self.community.extend([self.deck.drawCard(), self.deck.drawCard(), self.deck.drawCard()])
            self.stage = 1
        elif self.stage == 1:
            self.community.append(self.deck.drawCard())
            self.stage = 2
        elif self.stage == 2:
            self.community.append(self.deck.drawCard())
            self.stage = 3
        else:
            self.stage = 4
            self.resolve_showdown()
            return
        self.set_stage_banner(self.stage_names[self.stage])
        self.log(f"{self.stage_names[self.stage]} dealt.")

    def bluff(self):
        if self.game_over:
            return
        choices = ["monster hand", "stone cold bluff", "you read them perfectly", "dead silence"]
        line = random.choice(choices)
        chance = 0.25 + (0.25 if "Bluff Master" in self.player_profile.buffs else 0.0)
        self.log(f"You lean in: '{line.title()}.'")
        if random.random() < chance:
            self.bluff_pressure = 0.10 + (0.04 if "Intimidation" in self.player_profile.buffs else 0.0)
            self.log("The room shifts toward you.")
        if random.random() < chance and random.random() < 0.22:
            self.winner = "Player"
            self.player_profile.chips += self.pot
            gold_reward = self.award_victory_extras()
            self.result_text = f"{self.npc.name} folds to the bluff. You win {self.pot} chips.\n+{gold_reward} gold"
            self.game_over = True

    def fold(self):
        loss = self.player_profile.reduce_loss(max(10, self.pot // 3))
        self.winner = "Boss"
        self.result_text = f"You fold. {self.npc.name} takes the pot, and you lose {loss} extra chips in pride."
        self.player_profile.chips = max(0, self.player_profile.chips - loss)
        self.game_over = True

    def call_or_check(self):
        if self.game_over:
            return
        if self.pending_response:
            to_call = self.get_call_amount()
            if to_call > self.player_profile.chips:
                self.result_text = "Not enough chips to call."
                self.game_over = True
                return
            self.player_profile.chips -= to_call
            self.pot += to_call
            self.player_contribution += to_call
            self.log(f"You call {to_call} chips.")
            self.progress_street()
            return

        if self.current_bet == 0:
            action = self.ai_action()
            if action == "raise" and self.enemy_stack > 0:
                bet = min(self.enemy_stack, 30 + self.stage * 20 + (15 if self.npc.difficulty == "hard" else 0))
                self.enemy_stack -= bet
                self.current_bet = bet
                self.boss_contribution = bet
                self.pot += bet
                self.pending_response = True
                self.log(f"{self.npc.name} opens for {bet} chips.")
            elif action == "fold":
                self.player_profile.chips += self.pot
                gold_reward = self.award_victory_extras()
                self.result_text = f"{self.npc.name} gives up. You win {self.pot} chips.\n+{gold_reward} gold"
                self.game_over = True
            else:
                self.log(f"{self.npc.name} checks it back.")
                self.progress_street()
        else:
            to_call = self.get_call_amount()
            if to_call > self.player_profile.chips:
                self.result_text = "Not enough chips to call."
                self.game_over = True
                return
            self.player_profile.chips -= to_call
            self.pot += to_call
            self.player_contribution += to_call
            self.log(f"You call {to_call} chips.")
            self.progress_street()

    def raise_bet(self):
        if self.game_over:
            return
        raise_amount = self.current_raise_amount()
        if raise_amount <= 0:
            self.result_text = "No chips left to raise."
            self.game_over = True
            return

        if self.pending_response:
            total = self.get_call_amount() + raise_amount
            if total > self.player_profile.chips:
                self.result_text = "Not enough chips to raise."
                self.game_over = True
                return
            self.player_profile.chips -= total
            self.pot += total
            self.current_bet += raise_amount
            self.player_contribution = self.current_bet
            self.log(f"You reraise {raise_amount} chips.")
        else:
            self.player_profile.chips -= raise_amount
            self.pot += raise_amount
            self.current_bet = raise_amount
            self.player_contribution = raise_amount
            self.log(f"You bet {raise_amount} chips.")

        action = self.ai_action(player_aggressive=True)
        if action == "fold":
            self.player_profile.chips += self.pot
            gold_reward = self.award_victory_extras()
            self.result_text = f"{self.npc.name} folds. You win the {self.pot}-chip pot.\n+{gold_reward} gold"
            self.game_over = True
            return

        call_amount = max(0, self.current_bet - self.boss_contribution)
        enemy_call = min(self.enemy_stack, call_amount)
        self.enemy_stack -= enemy_call
        self.boss_contribution += enemy_call
        self.pot += enemy_call

        if action == "raise" and self.enemy_stack > 0 and not self.pending_response:
            extra = min(self.enemy_stack, 30 + (20 if self.npc.difficulty == "hard" else 10))
            self.enemy_stack -= extra
            self.current_bet += extra
            self.boss_contribution += extra
            self.pot += extra
            self.pending_response = True
            self.log(f"{self.npc.name} comes back over the top for {extra} more.")
            return

        self.log(f"{self.npc.name} calls.")
        self.progress_street()

    def resolve_showdown(self):
        player_score, _ = bestHandOf7(self.player_hand + self.community)
        boss_score, _ = bestHandOf7(self.boss_hand + self.community)
        player_strength = score_to_value(player_score) / 9.0
        boss_strength = score_to_value(boss_score) / 9.0
        player_strength, boss_strength = self.player_profile.apply_buffs(player_strength, boss_strength)

        comparison = compare_scores(player_score, boss_score)
        if abs(player_strength - boss_strength) > 0.015:
            comparison = 1 if player_strength > boss_strength else -1

        if comparison > 0:
            self.winner = "Player"
            self.player_profile.chips += self.pot
            gold_reward = self.award_victory_extras()
            self.result_text = f"You win with {HAND_TYPE[player_score[0]].title()}. +{self.pot} chips\n+{gold_reward} gold"
            self.log(f"{self.npc.name}: {get_boss_line(self.npc.difficulty, outcome='win')}")
            if self.npc.role == "boss":
                self.player_profile.beaten_bosses.add(self.npc.npc_id)
                self.reward_choices = self.player_profile.boss_reward_choices(self.npc.difficulty)
                if self.reward_choices:
                    self.awaiting_reward_pick = True
                    self.result_text += "\nChoose your buff reward:"
                else:
                    self.result_text += "\nEvery buff is already yours."
            self.npc.active = False
        elif comparison < 0:
            self.winner = "Boss"
            loss = self.player_profile.reduce_loss(max(10, self.pot // 4))
            self.player_profile.chips = max(0, self.player_profile.chips - loss)
            self.result_text = f"{self.npc.name} wins with {HAND_TYPE[boss_score[0]].title()}. You drop {loss} extra chips."
            self.log(f"{self.npc.name}: {get_boss_line(self.npc.difficulty, outcome='lose')}")
        else:
            split = self.pot // 2
            self.player_profile.chips += split
            self.result_text = f"Tie with {HAND_TYPE[player_score[0]].title()}. You recover {split} chips."
            self.log(f"{self.npc.name}: We split it. For now.")

        self.game_over = True

    def handle_key(self, key):
        if self.game_over:
            if self.awaiting_reward_pick:
                options = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
                index = options.get(key)
                if index is None or index >= len(self.reward_choices):
                    return "CONTINUE"
                buff = self.reward_choices[index]
                if self.player_profile.claim_buff(buff):
                    self.result_text += f"\nBuff claimed: {buff}"
                    self.log(f"New edge secured: {buff}.")
                self.awaiting_reward_pick = False
                self.reward_choices = []
                return "CONTINUE"
            if key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_e):
                return "LEAVE"
            return "CONTINUE"
        if key == pygame.K_1:
            self.call_or_check()
        elif key == pygame.K_2:
            self.raise_bet()
        elif key == pygame.K_3:
            self.fold()
        elif key == pygame.K_4:
            self.bluff()
        return "CONTINUE"

    def draw_card(self, x, y, card=None, hidden=False):
        rect = pygame.Rect(x, y, 70, 100)
        if hidden:
            pygame.draw.rect(self.screen, (150, 30, 30), rect, border_radius=8)
            pygame.draw.rect(self.screen, (245, 245, 245), rect, 2, border_radius=8)
            return
        if card is None:
            pygame.draw.rect(self.screen, (40, 80, 40), rect, 2, border_radius=8)
            return
        face = self.assets.card_faces.get((card.rank, card.suit))
        if face:
            self.screen.blit(scale_to_fit(face, 70, 100), (x, y))
            return
        pygame.draw.rect(self.screen, (250, 250, 250), rect, border_radius=8)
        pygame.draw.rect(self.screen, (20, 20, 20), rect, 2, border_radius=8)
        text = self.small_font.render(f"{card.rank[:2]} {card.suit[0].upper()}", True, (20, 20, 20))
        self.screen.blit(text, (x + 8, y + 10))

    def draw(self):
        self.screen.fill((24, 110, 48))
        pygame.draw.ellipse(self.screen, (12, 74, 30), (120, 70, 720, 430))
        pygame.draw.ellipse(self.screen, (210, 170, 90), (118, 68, 724, 434), 6)

        title = self.big_font.render(f"Table: {self.npc.name}", True, (255, 228, 150))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 18))

        call_amount = self.get_call_amount()
        info = [
            f"Your Chips: {self.player_profile.chips}",
            f"Pot: {self.pot}",
            f"Stage: {self.stage_names[self.stage]}",
            f"Boss Chips: {self.enemy_stack}",
            f"To Call: {call_amount}",
            f"Raise: {self.current_raise_amount()}",
        ]
        hint_line = None
        if self.player_profile.tutorials_enabled:
            visible = self.visible_count()
            if visible + 2 >= 5:
                score, _ = bestHandOf7(self.player_hand + self.community)
                hint_line = f"Hint: {HAND_TYPE[score[0]].title()}"
            elif self.player_hand[0].rank == self.player_hand[1].rank:
                hint_line = f"Hint: Pocket {self.player_hand[0].rank.title()}s"
            elif self.player_hand[0].suit == self.player_hand[1].suit:
                hint_line = "Hint: Suited start"
            else:
                hint_line = f"Hint: strength {self.get_strength(self.player_hand, visible):.2f}"
        for idx, line in enumerate(info):
            surf = self.font.render(line, True, (245, 245, 245))
            x = 24 + (idx % 3) * 290
            y = 66 + (idx // 3) * 28
            self.screen.blit(surf, (x, y))

        if self.street_timer > 0:
            banner = self.big_font.render(self.street_banner, True, (255, 240, 180))
            banner_bg = pygame.Rect(0, 0, banner.get_width() + 30, banner.get_height() + 12)
            banner_bg.center = (WIDTH // 2, 108)
            pygame.draw.rect(self.screen, (12, 12, 18), banner_bg, border_radius=10)
            pygame.draw.rect(self.screen, (245, 220, 150), banner_bg, 2, border_radius=10)
            self.screen.blit(banner, banner.get_rect(center=banner_bg.center))
            self.street_timer -= 1

        for idx, card in enumerate(self.boss_hand):
            self.draw_card(350 + idx * 90, 140, card, hidden=not self.game_over)
        for idx in range(5):
            card = self.community[idx] if idx < len(self.community) else None
            self.draw_card(190 + idx * 90, 282, card, hidden=False)
        for idx, card in enumerate(self.player_hand):
            self.draw_card(350 + idx * 90, 430, card)

        log_panel = pygame.Rect(24, 500, 420, 118)
        pygame.draw.rect(self.screen, (18, 18, 24), log_panel, border_radius=12)
        pygame.draw.rect(self.screen, (235, 235, 235), log_panel, 2, border_radius=12)
        for idx, line in enumerate(self.action_log[-4:]):
            surf = self.small_font.render(line[:48], True, (240, 240, 240))
            self.screen.blit(surf, (log_panel.x + 14, log_panel.y + 12 + idx * 24))

        controls_panel = pygame.Rect(470, 500, WIDTH - 494, 118)
        pygame.draw.rect(self.screen, (18, 18, 24), controls_panel, border_radius=12)
        pygame.draw.rect(self.screen, (235, 235, 235), controls_panel, 2, border_radius=12)

        if self.game_over and self.awaiting_reward_pick:
            prompt = "Choose reward: 1 / 2 / 3"
        elif self.game_over:
            prompt = "Press Enter, E, or Esc to leave the table"
        elif self.pending_response:
            prompt = f"1 Call {call_amount}   3 Fold   4 Bluff"
        else:
            prompt = f"1 Check/Call   2 Raise {self.current_raise_amount()}   3 Fold   4 Bluff"

        lines = [prompt]
        if hint_line:
            lines.append(hint_line)
        if self.result_text:
            lines = self.result_text.split("\n")
            if self.awaiting_reward_pick and self.reward_choices:
                for idx, buff in enumerate(self.reward_choices, start=1):
                    lines.append(f"{idx} {buff}")
            lines.append(prompt)
        elif self.last_reward_text:
            lines.append(self.last_reward_text)

        for idx, line in enumerate(lines[:4]):
            surf = self.font.render(line, True, (240, 240, 240))
            self.screen.blit(surf, (controls_panel.x + 14, controls_panel.y + 14 + idx * 24))
