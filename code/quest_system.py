import pygame
from settings import *

class Quest:
    def __init__(self, quest_id, title, description, objectives, rewards, next_quest=None):
        """
        quest_id: unique identifier
        title: quest name
        description: what the player needs to do
        objectives: dict like {'corn': 5, 'tomato': 3}
        rewards: dict like {'money': 50, 'seeds': {'corn': 10}}
        next_quest: ID of the next quest to unlock
        """
        self.id = quest_id
        self.title = title
        self.description = description
        self.objectives = objectives  # What needs to be done
        self.progress = {key: 0 for key in objectives.keys()}  # Current progress
        self.rewards = rewards
        self.next_quest = next_quest
        self.completed = False
        self.claimed = False

    def update_progress(self, item, amount=1):
        """Update progress for a specific objective"""
        if item in self.progress and not self.completed:
            self.progress[item] += amount
            # Check if quest is complete
            if self.is_complete():
                self.completed = True
                return True
        return False

    def is_complete(self):
        """Check if all objectives are met"""
        for item, needed in self.objectives.items():
            if self.progress.get(item, 0) < needed:
                return False
        return True

    def get_progress_text(self):
        """Get formatted progress text"""
        lines = []
        for item, needed in self.objectives.items():
            current = self.progress.get(item, 0)
            lines.append(f"  • {item.replace('_', ' ').title()}: {current}/{needed}")
        return "\n".join(lines)


class QuestManager:
    def __init__(self, player):
        self.player = player
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 20)
        self.title_font = pygame.font.Font('font/LycheeSoda.ttf', 28)
        
        # Define all quests
        self.all_quests = self.create_quests()
        self.active_quest = self.all_quests[0]  # Start with first quest
        self.completed_quests = []
        
        # UI state
        self.show_completion = False
        self.completion_timer = 0
        self.completion_duration = 3.0  # Show for 3 seconds

    def create_quests(self):
        """Define all quests in the game"""
        quests = [
            Quest(
                quest_id=0,
                title="First Harvest",
                description="Learn the basics by growing corn",
                objectives={'harvest_corn': 5},
                rewards={'money': 30, 'seeds': {'tomato': 5}},
                next_quest=1
            ),
            Quest(
                quest_id=1,
                title="Diversify Your Farm",
                description="Grow different crops",
                objectives={'harvest_corn': 3, 'harvest_tomato': 3},
                rewards={'money': 50, 'seeds': {'moon_melon': 3}},
                next_quest=2
            ),
            Quest(
                quest_id=2,
                title="Experienced Farmer",
                description="Harvest a variety of crops",
                objectives={'harvest_corn': 5, 'harvest_tomato': 5, 'harvest_moon_melon': 3},
                rewards={'money': 100, 'seeds': {'pumpkin': 5, 'cactus': 5}},
                next_quest=3
            ),
            Quest(
                quest_id=3,
                title="Master Gardener",
                description="Become a farming expert",
                objectives={
                    'harvest_corn': 10,
                    'harvest_tomato': 10,
                    'harvest_moon_melon': 5,
                    'harvest_pumpkin': 5
                },
                rewards={'money': 200},
                next_quest=4
            ),
            Quest(
                quest_id=4,
                title="Cleanse the Farm",
                description="Complete the farm cleansing",
                objectives={'cleanse_stage': 1},  # Reach stage 1
                rewards={'money': 500},
                next_quest=None  # Final quest
            )
        ]
        return quests

    def on_harvest(self, crop_type):
        """Called when player harvests a crop"""
        if self.active_quest and not self.active_quest.completed:
            objective_key = f'harvest_{crop_type}'
            if self.active_quest.update_progress(objective_key):
                self.show_completion = True
                self.completion_timer = self.completion_duration

    def on_stage_progress(self):
        """Called when farm progresses to next stage"""
        if self.active_quest and not self.active_quest.completed:
            if self.active_quest.update_progress('cleanse_stage'):
                self.show_completion = True
                self.completion_timer = self.completion_duration

    def claim_rewards(self):
        """Give rewards to player and move to next quest"""
        if not self.active_quest or not self.active_quest.completed or self.active_quest.claimed:
            return False
        
        quest = self.active_quest
        
        # Give money reward
        if 'money' in quest.rewards:
            self.player.money += quest.rewards['money']
        
        # Give seed rewards
        if 'seeds' in quest.rewards:
            for seed, amount in quest.rewards['seeds'].items():
                self.player.seed_inventory[seed] += amount
        
        # Mark as claimed
        quest.claimed = True
        self.completed_quests.append(quest)
        
        # Move to next quest
        if quest.next_quest is not None:
            self.active_quest = self.all_quests[quest.next_quest]
        else:
            self.active_quest = None  # No more quests
        
        return True

    def update(self, dt):
        """Update quest manager"""
        if self.show_completion:
            self.completion_timer -= dt
            if self.completion_timer <= 0:
                self.show_completion = False

    def draw_quest_ui(self):
        """Draw quest progress in top-left corner"""
        if not self.active_quest:
            return
        
        # Position
        x, y = 10, 100
        padding = 10
        
        # Quest title
        title_text = f"Quest: {self.active_quest.title}"
        title_surf = self.title_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surf.get_rect(topleft=(x, y))
        
        # Progress text
        progress_text = self.active_quest.get_progress_text()
        progress_lines = progress_text.split('\n')
        
        # Calculate total height
        total_height = title_rect.height + padding
        for line in progress_lines:
            total_height += self.font.get_linesize()
        total_height += padding * 2
        
        # Calculate total width
        max_width = title_rect.width
        for line in progress_lines:
            line_width = self.font.size(line)[0]
            max_width = max(max_width, line_width)
        max_width += padding * 2
        
        # Draw background
        bg_rect = pygame.Rect(x - padding, y - padding, max_width + padding * 2, total_height)
        pygame.draw.rect(self.display_surface, (0, 0, 0, 180), bg_rect, border_radius=8)
        pygame.draw.rect(self.display_surface, (255, 255, 255), bg_rect, 2, border_radius=8)
        
        # Draw title
        self.display_surface.blit(title_surf, title_rect)
        
        # Draw progress
        current_y = y + title_rect.height + padding
        for line in progress_lines:
            line_surf = self.font.render(line, True, (200, 200, 200))
            self.display_surface.blit(line_surf, (x, current_y))
            current_y += self.font.get_linesize()

    def draw_completion_popup(self):
        """Draw quest completion popup"""
        if not self.show_completion or not self.active_quest:
            return
        
        # Center popup
        popup_width = 400
        popup_height = 200
        popup_x = SCREEN_WIDTH // 2 - popup_width // 2
        popup_y = SCREEN_HEIGHT // 2 - popup_height // 2
        
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        
        # Draw popup background
        pygame.draw.rect(self.display_surface, (50, 50, 50), popup_rect, border_radius=12)
        pygame.draw.rect(self.display_surface, (255, 215, 0), popup_rect, 3, border_radius=12)
        
        # Title
        title = "Quest Complete!"
        title_surf = self.title_font.render(title, True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(popup_x + popup_width // 2, popup_y + 40))
        self.display_surface.blit(title_surf, title_rect)
        
        # Quest name
        quest_surf = self.font.render(self.active_quest.title, True, (255, 255, 255))
        quest_rect = quest_surf.get_rect(center=(popup_x + popup_width // 2, popup_y + 80))
        self.display_surface.blit(quest_surf, quest_rect)
        
        # Rewards text
        reward_text = "Press ENTER to claim rewards"
        reward_surf = self.font.render(reward_text, True, (200, 200, 200))
        reward_rect = reward_surf.get_rect(center=(popup_x + popup_width // 2, popup_y + 120))
        self.display_surface.blit(reward_surf, reward_rect)

    def draw(self):
        """Draw all quest UI elements"""
        self.draw_quest_ui()
        self.draw_completion_popup()