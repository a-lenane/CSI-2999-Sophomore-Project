import pygame
import random
import os
from PokerLogic import Deck, Card, bestHandOf7, HAND_TYPE, RANK_VALUE
from DifficultiesCodeAndChips import easy_ai, medium_ai, hard_ai, evaluate_hand_strength
from DialogueCasino import get_dialogue

class PokerGame:
    def __init__(self, screen, player_profile, difficulty="easy"):
        self.screen = screen
        self.player_profile = player_profile
        self.difficulty = difficulty
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.dialogue_font = pygame.font.SysFont("Arial", 20, italic=True)
        
        # Load card images
        self.card_images = {}
        self.load_card_images()
        
        # Game state
        self.deck = Deck()
        self.player_hand = [self.deck.drawCard(), self.deck.drawCard()]
        self.boss_hand = [self.deck.drawCard(), self.deck.drawCard()]
        self.community_cards = []
        self.stage = 0  # 0: Pre-flop, 1: Flop, 2: Turn, 3: River, 4: Showdown
        self.pot = 0
        self.current_bet = 50
        self.player_contribution = 0
        self.boss_contribution = 0
        self.game_over = False
        self.result_text = ""
        self.winner = None
        self.player_folded = False
        
        # Betting amounts
        self.bet_amounts = [50, 100, 200, 500]
        self.selected_bet_index = 0
        
        # Dialogue/bluff system
        self.bluff_options = [
            ("Bluff: 'I've got a monster hand!'", "bluff"),
            ("Intimidate: 'You're out of your league!'", "intimidate"),
            ("Confuse: 'What's a flush again?'", "confuse"),
            ("Stay quiet", "quiet")
        ]
        self.selected_bluff = 0
        self.showing_bluff_menu = False
        self.bluff_result = None
        self.bluff_timer = 0
        
        # Player aggression tracking for hard AI
        self.player_aggressive_count = 0
        
        # Ante - take chips to join
        ante = 50
        self.player_profile.chips -= ante
        self.pot += ante * 2
        
        # GUI Buttons
        self.btn_call = pygame.Rect(100, 500, 120, 40)
        self.btn_raise = pygame.Rect(240, 500, 120, 40)
        self.btn_fold = pygame.Rect(380, 500, 120, 40)
        self.btn_bluff = pygame.Rect(520, 500, 120, 40)
        self.btn_leave = pygame.Rect(660, 500, 120, 40)
        
        # Bluff menu buttons
        self.bluff_buttons = []
        for i, (text, _) in enumerate(self.bluff_options):
            self.bluff_buttons.append(pygame.Rect(200, 250 + i * 50, 500, 40))

    def load_card_images(self):
        """Load all card images from the ui folder."""
        card_size = (70, 100)
        suits = ["spades", "hearts", "diamonds", "clubs"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]
        
        # Try to load card back
        back_path = os.path.join("ui", "card_back.png")
        if os.path.exists(back_path):
            try:
                back_img = pygame.image.load(back_path)
                self.card_back = pygame.transform.scale(back_img, card_size)
            except:
                self.card_back = None
        else:
            self.card_back = None
        
        # Load each card
        for suit in suits:
            for rank in ranks:
                filename = f"{rank}_of_{suit}.png"
                filepath = os.path.join("ui", filename)
                if os.path.exists(filepath):
                    try:
                        img = pygame.image.load(filepath)
                        self.card_images[(suit, rank)] = pygame.transform.scale(img, card_size)
                    except:
                        self.card_images[(suit, rank)] = None
                else:
                    self.card_images[(suit, rank)] = None
        
        # Create fallback card back if not loaded
        if self.card_back is None:
            self.card_back = pygame.Surface(card_size)
            self.card_back.fill((180, 0, 0))
            pygame.draw.rect(self.card_back, (255, 255, 255), self.card_back.get_rect(), 3)

    def get_card_image(self, card):
        """Get the surface for a Card object, or None if not loaded."""
        if card is None:
            return None
        suit = card.suit.lower()
        rank = card.rank.lower()
        return self.card_images.get((suit, rank))

    def get_hand_strength(self, hand, visible_count):
        """Get hand strength using the evaluation function"""
        hand_tuples = [(c.suit.lower(), c.rank.lower()) for c in hand]
        pool_tuples = [(c.suit.lower(), c.rank.lower()) for c in self.community_cards]
        return evaluate_hand_strength(hand_tuples, pool_tuples, visible_count)

    def get_call_amount(self):
        return max(0, self.current_bet - self.player_contribution)

    def boss_turn(self):
        visible_count = 0 if self.stage == 0 else (3 if self.stage == 1 else (4 if self.stage == 2 else 5))
        hand_strength = self.get_hand_strength(self.boss_hand, visible_count)
        pot_odds = self.current_bet / max(1, self.pot + self.current_bet)
        
        if self.difficulty == "easy":
            action = easy_ai(hand_strength)
        elif self.difficulty == "medium":
            action = medium_ai(hand_strength, pot_odds)
        else:
            action = hard_ai(hand_strength, pot_odds, self.player_aggressive_count > 2)
        
        if action == "raise":
            raise_amount = self.current_bet
            self.current_bet += raise_amount
            self.boss_contribution = self.current_bet
            self.pot += raise_amount
        elif action == "call":
            to_call = self.current_bet - self.boss_contribution
            self.boss_contribution = self.current_bet
            self.pot += to_call
        elif action == "fold":
            self.winner = "Player"
            self.game_over = True
            self.result_text = f"Boss folded! You win {self.pot} chips!"
            self.player_profile.chips += self.pot
            return
        
        self.advance_stage()

    def advance_stage(self):
        if self.stage == 0:
            # Deal flop (3 cards)
            for _ in range(3):
                self.community_cards.append(self.deck.drawCard())
            self.stage = 1
            self.current_bet = 0
            self.player_contribution = 0
            self.boss_contribution = 0
        elif self.stage == 1:
            # Deal turn
            self.community_cards.append(self.deck.drawCard())
            self.stage = 2
            self.current_bet = 0
            self.player_contribution = 0
            self.boss_contribution = 0
        elif self.stage == 2:
            # Deal river
            self.community_cards.append(self.deck.drawCard())
            self.stage = 3
            self.current_bet = 0
            self.player_contribution = 0
            self.boss_contribution = 0
        elif self.stage == 3:
            self.resolve_showdown()
        else:
            self.resolve_showdown()

    def resolve_showdown(self):
        # Evaluate hands
        player_cards = self.player_hand + self.community_cards
        boss_cards = self.boss_hand + self.community_cards
        
        player_score, player_best = bestHandOf7(player_cards)
        boss_score, boss_best = bestHandOf7(boss_cards)
        
        # Apply player buffs
        player_strength = player_score / 8.0 if isinstance(player_score, (int, float)) else player_score[0] / 8.0
        boss_strength = boss_score / 8.0 if isinstance(boss_score, (int, float)) else boss_score[0] / 8.0
        player_strength, boss_strength = self.player_profile.apply_buffs(player_strength, boss_strength)
        
        if player_strength > boss_strength:
            self.winner = "Player"
            self.player_profile.chips += self.pot
            self.result_text = f"You win! (+{self.pot} chips)"
            
            # Award buff if boss beaten for first time
            buff_gained = self.player_profile.award_buff_for_boss(self.difficulty)
            if buff_gained:
                self.result_text += f"\nGained buff: {buff_gained}!"
        elif boss_strength > player_strength:
            self.winner = "Boss"
            loss = self.player_profile.reduce_loss(self.pot)
            self.result_text = f"Boss wins! You lost {loss} chips."
        else:
            # Tie - split pot
            split = self.pot // 2
            self.player_profile.chips += split
            self.result_text = f"Tie! Pot split. You get {split} chips."
        
        self.game_over = True

    def execute_bluff(self, bluff_type):
        """Execute bluff and affect opponent's decision"""
        visible_count = 0 if self.stage == 0 else (3 if self.stage == 1 else (4 if self.stage == 2 else 5))
        actual_strength = self.get_hand_strength(self.player_hand, visible_count)
        
        if bluff_type == "bluff":
            success_chance = 0.4
            if "Bluff Master" in self.player_profile.buffs:
                success_chance = 0.7
            if random.random() < success_chance:
                self.bluff_result = "success"
                # Opponent may fold
                if random.random() < 0.5:
                    self.winner = "Player"
                    self.game_over = True
                    self.result_text = "Bluff successful! Opponent folded!"
                    self.player_profile.chips += self.pot
                    return
            else:
                self.bluff_result = "fail"
                
        elif bluff_type == "intimidate":
            success_chance = 0.35
            if "Intimidation" in self.player_profile.buffs:
                success_chance = 0.6
            if random.random() < success_chance:
                self.bluff_result = "success"
                # Reduce opponent's next bet
                self.current_bet = max(20, self.current_bet // 2)
            else:
                self.bluff_result = "fail"
                
        elif bluff_type == "confuse":
            success_chance = 0.3
            if random.random() < success_chance:
                self.bluff_result = "success"
                # Opponent checks instead of raising
                pass
            else:
                self.bluff_result = "fail"
        
        self.bluff_timer = 60  # Show result for 1 second
        self.showing_bluff_menu = False

    def update(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                
                if self.btn_leave.collidepoint(mouse_pos):
                    return "LEAVE"
                
                if not self.game_over and not self.showing_bluff_menu:
                    if self.btn_call.collidepoint(mouse_pos):
                        to_call = self.get_call_amount()
                        if to_call <= self.player_profile.chips:
                            self.player_profile.chips -= to_call
                            self.player_contribution = self.current_bet
                            self.pot += to_call
                            self.boss_turn()
                        else:
                            self.result_text = "Not enough chips!"
                            self.game_over = True
                            
                    elif self.btn_raise.collidepoint(mouse_pos):
                        raise_amount = self.bet_amounts[self.selected_bet_index]
                        total = self.get_call_amount() + raise_amount
                        if total <= self.player_profile.chips:
                            self.player_profile.chips -= total
                            self.player_contribution = self.current_bet + raise_amount
                            self.current_bet += raise_amount
                            self.pot += total
                            self.player_aggressive_count += 1
                            self.boss_turn()
                        else:
                            self.result_text = "Not enough chips to raise!"
                            
                    elif self.btn_fold.collidepoint(mouse_pos):
                        self.player_folded = True
                        self.game_over = True
                        self.result_text = "You folded. Boss wins the pot."
                        
                    elif self.btn_bluff.collidepoint(mouse_pos):
                        self.showing_bluff_menu = True
                        
                elif self.showing_bluff_menu:
                    for i, btn in enumerate(self.bluff_buttons):
                        if btn.collidepoint(mouse_pos):
                            self.execute_bluff(self.bluff_options[i][1])
                            break
                            
            elif event.type == pygame.KEYDOWN and self.showing_bluff_menu:
                if event.key == pygame.K_UP:
                    self.selected_bluff = (self.selected_bluff - 1) % len(self.bluff_options)
                elif event.key == pygame.K_DOWN:
                    self.selected_bluff = (self.selected_bluff + 1) % len(self.bluff_options)
                elif event.key == pygame.K_RETURN:
                    self.execute_bluff(self.bluff_options[self.selected_bluff][1])
                elif event.key == pygame.K_ESCAPE:
                    self.showing_bluff_menu = False
        
        # Update bluff timer
        if self.bluff_timer > 0:
            self.bluff_timer -= 1
            if self.bluff_timer == 0:
                self.bluff_result = None
        
        return "CONTINUE"

    def draw_card(self, x, y, card=None, hidden=False):
        """Draw a card at (x,y). If hidden, draw card back. If card is None, draw nothing."""
        rect = pygame.Rect(x, y, 70, 100)
        
        if hidden:
            self.screen.blit(self.card_back, (x, y))
        elif card is not None:
            img = self.get_card_image(card)
            if img is not None:
                self.screen.blit(img, (x, y))
            else:
                # Fallback to rectangle drawing
                surface = pygame.Surface((70, 100), pygame.SRCALPHA)
                surface.fill((255, 255, 255, 255))
                pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 2)
                color = (255, 0, 0) if card.suit in ["Hearts", "Diamonds"] else (0, 0, 0)
                rank_text = card.rank[:2] if card.rank != "10" else "10"
                text = self.font.render(rank_text, True, color)
                surface.blit(text, (5, 5))
                suit_text = self.small_font.render(card.suit[0], True, color)
                surface.blit(suit_text, (5, 70))
                self.screen.blit(surface, (x, y))

    def draw(self):
        # Draw green felt table
        self.screen.fill((34, 139, 34))
        
        # Info panel
        info_y = 10
        chip_text = self.font.render(f"Chips: {self.player_profile.chips}", True, (255, 215, 0))
        pot_text = self.font.render(f"Pot: {self.pot}", True, (255, 215, 0))
        bet_text = self.font.render(f"Current Bet: {self.current_bet}", True, (255, 215, 0))
        self.screen.blit(chip_text, (10, info_y))
        self.screen.blit(pot_text, (400 - pot_text.get_width() // 2, info_y))
        self.screen.blit(bet_text, (750 - bet_text.get_width(), info_y))
        
        # Draw buffs
        buff_y = 40
        for i, buff in enumerate(self.player_profile.buffs):
            buff_surf = self.small_font.render(f"✓ {buff}", True, (100, 255, 100))
            self.screen.blit(buff_surf, (10, buff_y + i * 20))
        
        # Draw Boss Hand (hidden until showdown)
        self.draw_card(350, 60, self.boss_hand[0] if self.game_over else None, hidden=not self.game_over)
        self.draw_card(430, 60, self.boss_hand[1] if self.game_over else None, hidden=not self.game_over)
        
        # Draw Community Cards
        pool_x = 220
        for i, card in enumerate(self.community_cards):
            self.draw_card(pool_x + (i * 80), 220, card)
        # Draw empty slots for remaining cards
        for i in range(len(self.community_cards), 5):
            self.draw_card(pool_x + (i * 80), 220, hidden=True)
        
        # Draw Player Hand
        self.draw_card(350, 380, self.player_hand[0])
        self.draw_card(430, 380, self.player_hand[1])
        
        # Draw buttons
        buttons = [
            (self.btn_call, f"Call {self.get_call_amount()}", (50, 50, 200)),
            (self.btn_raise, f"Raise {self.bet_amounts[self.selected_bet_index]}", (200, 50, 50)),
            (self.btn_fold, "Fold", (100, 100, 100)),
            (self.btn_bluff, "Bluff/Dialogue", (200, 150, 50)),
            (self.btn_leave, "Leave Table", (200, 150, 50))
        ]
        
        for rect, text, color in buttons:
            if rect == self.btn_raise:
                # Draw raise amount selector
                pygame.draw.rect(self.screen, color, rect, border_radius=5)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=5)
                text_surf = self.font.render(text, True, (255, 255, 255))
                self.screen.blit(text_surf, (rect.x + (rect.width - text_surf.get_width()) // 2,
                                            rect.y + (rect.height - text_surf.get_height()) // 2))
                # Draw small arrows for bet selection
                up_arrow = pygame.Rect(rect.right - 25, rect.y + 5, 20, 15)
                down_arrow = pygame.Rect(rect.right - 25, rect.y + rect.height - 20, 20, 15)
                pygame.draw.polygon(self.screen, (255, 255, 255), [(up_arrow.centerx, up_arrow.y + 3), 
                                    (up_arrow.x + 3, up_arrow.bottom - 3), (up_arrow.right - 3, up_arrow.bottom - 3)])
                pygame.draw.polygon(self.screen, (255, 255, 255), [(down_arrow.centerx, down_arrow.bottom - 3),
                                    (down_arrow.x + 3, down_arrow.y + 3), (down_arrow.right - 3, down_arrow.y + 3)])
            else:
                pygame.draw.rect(self.screen, color, rect, border_radius=5)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=5)
                text_surf = self.font.render(text, True, (255, 255, 255))
                self.screen.blit(text_surf, (rect.x + (rect.width - text_surf.get_width()) // 2,
                                            rect.y + (rect.height - text_surf.get_height()) // 2))
        
        # Draw bluff result
        if self.bluff_result:
            result_color = (100, 255, 100) if self.bluff_result == "success" else (255, 100, 100)
            result_text = "Bluff Successful!" if self.bluff_result == "success" else "Bluff Failed!"
            result_surf = self.font.render(result_text, True, result_color)
            self.screen.blit(result_surf, (400 - result_surf.get_width() // 2, 450))
        
        # Draw bluff menu if active
        if self.showing_bluff_menu:
            overlay = pygame.Surface((900, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            title = self.font.render("Choose your dialogue/bluff:", True, (255, 255, 255))
            self.screen.blit(title, (450 - title.get_width() // 2, 200))
            
            for i, (btn, (text, _)) in enumerate(zip(self.bluff_buttons, self.bluff_options)):
                color = (100, 100, 200) if i == self.selected_bluff else (60, 60, 120)
                pygame.draw.rect(self.screen, color, btn, border_radius=5)
                pygame.draw.rect(self.screen, (255, 255, 255), btn, 2, border_radius=5)
                text_surf = self.font.render(text, True, (255, 255, 255))
                self.screen.blit(text_surf, (btn.x + 10, btn.y + 10))
        
        # Game Over Overlay
        if self.game_over:
            overlay = pygame.Surface((900, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            # Draw result text with word wrap
            words = self.result_text.split(' ')
            lines = []
            current_line = ""
            for word in words:
                if self.font.size(current_line + word)[0] < 700:
                    current_line += word + " "
                else:
                    lines.append(current_line)
                    current_line = word + " "
            lines.append(current_line)
            
            y_offset = 270
            for line in lines:
                result_surf = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(result_surf, (450 - result_surf.get_width() // 2, y_offset))
                y_offset += 30
            
            continue_text = self.small_font.render("Click 'Leave Table' to continue", True, (200, 200, 200))
            self.screen.blit(continue_text, (450 - continue_text.get_width() // 2, 400))