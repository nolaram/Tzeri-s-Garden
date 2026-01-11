import pygame
from settings import *

class EnergySystem:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 20)
        
        # Energy settings
        self.max_energy = 100
        self.current_energy = 100
        
        # Regeneration settings
        self.regen_rate = 2  # points per regen interval
        self.regen_interval = 10.0  # seconds
        self.regen_timer = 0
        
        # Energy costs for actions
        self.action_costs = {
            'hoe': 2,
            'axe': 4,
            'water': 2,
            'plant': 2,
            'harvest': 1
        }
        
        # Visual settings
        self.bar_width = 200
        self.bar_height = 24
        self.padding = 20
        
    def use_energy(self, action):
        """Use energy for an action. Returns True if had enough energy, False otherwise"""
        cost = self.action_costs.get(action, 0)
        
        if self.current_energy >= cost:
            self.current_energy -= cost
            return True
        else:
            # Not enough energy
            return False
    
    def add_energy(self, amount):
        """Add energy (from items, rest, etc.)"""
        self.current_energy = min(self.max_energy, self.current_energy + amount)
    
    def set_energy(self, amount):
        """Set energy to specific amount"""
        self.current_energy = max(0, min(self.max_energy, amount))
    
    def is_depleted(self):
        """Check if energy is too low to perform actions"""
        return self.current_energy <= 0
    
    def update(self, dt):
        """Update energy regeneration"""
        self.regen_timer += dt
        
        # Regenerate energy every interval
        if self.regen_timer >= self.regen_interval:
            self.regen_timer = 0
            self.add_energy(self.regen_rate)
    
    def get_energy_color(self):
        """Get color based on energy level"""
        energy_percent = self.current_energy / self.max_energy
        
        if energy_percent > 0.5:
            # Green to yellow
            return (100, 200, 100)
        elif energy_percent > 0.25:
            # Yellow to orange
            return (200, 200, 50)
        else:
            # Red (low energy)
            return (200, 50, 50)
    
    def draw(self):
        """Draw energy bar in bottom-right corner (Stardew Valley style)"""
        # Position in bottom-right
        x = SCREEN_WIDTH - self.bar_width - self.padding
        y = SCREEN_HEIGHT - self.bar_height - self.padding - 10
        
        # Background bar (darker)
        bg_rect = pygame.Rect(x - 4, y - 4, self.bar_width + 8, self.bar_height + 8)
        pygame.draw.rect(self.display_surface, (20, 20, 20), bg_rect, border_radius=6)
        pygame.draw.rect(self.display_surface, (100, 100, 100), bg_rect, 2, border_radius=6)
        
        # Energy bar background (empty portion)
        bar_bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(self.display_surface, (40, 40, 40), bar_bg_rect, border_radius=4)
        
        # Energy bar fill
        energy_percent = self.current_energy / self.max_energy
        fill_width = int(self.bar_width * energy_percent)
        
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y, fill_width, self.bar_height)
            energy_color = self.get_energy_color()
            pygame.draw.rect(self.display_surface, energy_color, fill_rect, border_radius=4)
            
            # Add a highlight effect on top
            highlight_rect = pygame.Rect(x, y, fill_width, self.bar_height // 3)
            highlight_color = tuple(min(255, c + 30) for c in energy_color)
            pygame.draw.rect(self.display_surface, highlight_color, highlight_rect, border_radius=4)
        
        # Energy text (centered in bar)
        energy_text = f"{int(self.current_energy)}/{self.max_energy}"
        text_surf = self.font.render(energy_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        
        # Text shadow for better readability
        shadow_surf = self.font.render(energy_text, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(text_rect.centerx + 1, text_rect.centery + 1))
        self.display_surface.blit(shadow_surf, shadow_rect)
        self.display_surface.blit(text_surf, text_rect)
        
        # Label above bar
        label_text = "Energy"
        label_surf = self.font.render(label_text, True, (200, 200, 200))
        label_rect = label_surf.get_rect(midtop=(x + self.bar_width // 2, y - 24))
        
        # Label shadow
        label_shadow = self.font.render(label_text, True, (0, 0, 0))
        label_shadow_rect = label_shadow.get_rect(midtop=(label_rect.centerx + 1, label_rect.top + 1))
        self.display_surface.blit(label_shadow, label_shadow_rect)
        self.display_surface.blit(label_surf, label_rect)
        
        # Warning indicator when energy is low
        if energy_percent < 0.2:
            self.draw_low_energy_warning()
    
    def draw_low_energy_warning(self):
        """Draw a pulsing warning when energy is low"""
        # Calculate pulse effect
        import math
        pulse = abs(math.sin(pygame.time.get_ticks() / 500.0))
        alpha = int(100 + 155 * pulse)
        
        # Warning text
        warning_text = "Low Energy!"
        warning_surf = self.font.render(warning_text, True, (255, 100, 100))
        warning_surf.set_alpha(alpha)
        
        x = SCREEN_WIDTH - self.bar_width - self.padding
        y = SCREEN_HEIGHT - self.bar_height - self.padding - 60
        
        warning_rect = warning_surf.get_rect(midtop=(x + self.bar_width // 2, y))
        self.display_surface.blit(warning_surf, warning_rect)
    
    def restore_full(self):
        """Restore energy to full (used when sleeping)"""
        self.current_energy = self.max_energy