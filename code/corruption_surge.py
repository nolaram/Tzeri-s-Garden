import pygame
from settings import *
from random import randint, choice

class CorruptionSurge:
    def __init__(self, soil_layer):
        self.display_surface = pygame.display.get_surface()
        self.soil_layer = soil_layer
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 24)
        self.title_font = pygame.font.Font('font/LycheeSoda.ttf', 48)
        # Report UI
        self.destroyed_crops = {}
        self.report_active = False
        self.close_button_rect = None

        # Surge settings
        self.surge_chance = 0.20  # 100% for testing (change to 0.2 for 20%)
        self.surge_triggered = False
        self.surge_happened_today = False
        
        # Warning phase
        self.warning_active = False
        self.warning_duration = 10.0  # 10 seconds warning
        self.warning_timer = 0
        
        # Surge execution
        self.surge_active = False
        self.surge_duration = 5.0  # 5 seconds of surge effect
        self.surge_timer = 0
        
        # Visual effects
        self.shake_intensity = 0
        self.shake_offset = pygame.math.Vector2(0, 0)
        self.flash_alpha = 0
        
        # Crop destruction settings
        self.destruction_percentage = 0.3  # Destroy 30% of crops
        
        # Sound (optional - will work if file exists)
        try:
            self.warning_sound = pygame.mixer.Sound('audio/warning.wav')
            self.warning_sound.set_volume(0.3)
        except:
            self.warning_sound = None
        
        try:
            self.surge_sound = pygame.mixer.Sound('audio/surge.wav')
            self.surge_sound.set_volume(0.4)
        except:
            self.surge_sound = None
    
    def reset_daily(self):
        """Reset surge status for new day"""
        self.surge_happened_today = False
        self.surge_triggered = False
    
    def try_trigger_surge(self, current_hour, current_day):
        """Try to trigger surge at specific hour (called by time system)"""
        # Can trigger from day 1 onwards
        
        # Only trigger during daytime (8 AM to 6 PM)
        if not (8 <= current_hour <= 18):
            return False
        
        # Check random chance
        if randint(1, 100) <= (self.surge_chance * 100):
            self.start_warning()
            self.surge_triggered = True
            return True
        
        return False
    
    def start_warning(self):
        """Start the warning phase"""
        self.warning_active = True
        self.warning_timer = 0
        if self.warning_sound:
            self.warning_sound.play()
        
    def start_surge(self):
        """Start the actual surge"""
        self.warning_active = False
        self.surge_active = True
        self.surge_timer = 0
        if self.surge_sound:
            self.surge_sound.play()
        self.destroyed_crops = {}
        self.destroy_crops()
    
    def destroy_crops(self):
        """Destroy a percentage of player's crops"""
        if not self.soil_layer or not self.soil_layer.plant_sprites:
            return
        
        all_plants = list(self.soil_layer.plant_sprites.sprites())
        
        if not all_plants:
            return
        
        num_to_destroy = max(1, int(len(all_plants) * self.destruction_percentage))
        
        plants_to_destroy = []
        while len(plants_to_destroy) < num_to_destroy and all_plants:
            plant = choice(all_plants)
            plants_to_destroy.append(plant)
            all_plants.remove(plant)
        
        destroyed_count = 0
        for plant in plants_to_destroy:
            cell_y = plant.rect.centery // TILE_SIZE
            cell_x = plant.rect.centerx // TILE_SIZE
            
            if 0 <= cell_y < len(self.soil_layer.grid) and 0 <= cell_x < len(self.soil_layer.grid[0]):
                cell = self.soil_layer.grid[cell_y][cell_x]
                while 'P' in cell:
                    cell.remove('P')
            
            from sprites import Particle
            Particle(
                plant.rect.topleft,
                plant.image,
                [sprite for group in plant.groups() for sprite in [group]],
                LAYERS['main'],
                duration=300
            )
            
            plant.kill()
            plant_type = getattr(plant, "plant_type", "unknown")

            if plant_type not in self.destroyed_crops:
                self.destroyed_crops[plant_type] = 0
            self.destroyed_crops[plant_type] += 1

            destroyed_count += 1
        
        self.surge_happened_today = True
    
    def update(self, dt):
        """Update surge state"""
        # Warning phase
        if self.warning_active:
            self.warning_timer += dt
            
            # Pulsing effect during warning
            import math
            self.flash_alpha = int(50 + 50 * abs(math.sin(pygame.time.get_ticks() / 200.0)))
            
            if self.warning_timer >= self.warning_duration:
                self.start_surge()
        
        # Surge phase
        elif self.surge_active:
            self.surge_timer += dt
            
            # Screen shake effect
            import math
            shake_amount = 8
            self.shake_offset.x = randint(-shake_amount, shake_amount)
            self.shake_offset.y = randint(-shake_amount, shake_amount)
            
            # Flash effect
            self.flash_alpha = int(100 + 100 * abs(math.sin(pygame.time.get_ticks() / 100.0)))
            
            if self.surge_timer >= self.surge_duration:
                self.end_surge()
    
    def end_surge(self):
        """End the surge"""
        self.surge_active = False
        self.surge_timer = 0
        self.shake_offset = pygame.math.Vector2(0, 0)
        self.flash_alpha = 0
        self.report_active = True
    
    def draw_warning(self):
        """Draw warning UI"""
        if not self.warning_active:
            return
        
        # Semi-transparent red overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((150, 0, 0, self.flash_alpha))
        self.display_surface.blit(overlay, (0, 0))
        
        # Warning box
        box_width = 600
        box_height = 200
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT // 2 - box_height // 2
        
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        
        # Pulsing border
        import math
        pulse = abs(math.sin(pygame.time.get_ticks() / 300.0))
        border_color = (255, int(100 + 155 * pulse), 0)
        
        pygame.draw.rect(self.display_surface, (20, 0, 0), box_rect, border_radius=12)
        pygame.draw.rect(self.display_surface, border_color, box_rect, 4, border_radius=12)
        
        # Warning title
        title_text = "⚠ CORRUPTION SURGE ⚠"
        title_surf = self.title_font.render(title_text, True, (255, 200, 0))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 50))
        self.display_surface.blit(title_surf, title_rect)
        
        # Warning message
        message_text = "Incoming in..."
        message_surf = self.font.render(message_text, True, (255, 255, 255))
        message_rect = message_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 100))
        self.display_surface.blit(message_surf, message_rect)
        
        # Countdown
        time_left = max(0, self.warning_duration - self.warning_timer)
        countdown_text = f"{time_left:.1f}s"
        countdown_surf = self.title_font.render(countdown_text, True, (255, 50, 50))
        countdown_rect = countdown_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 145))
        self.display_surface.blit(countdown_surf, countdown_rect)
    
    def draw_surge(self):
        """Draw surge effects"""
        if not self.surge_active:
            return
        
        # Dark red overlay with high opacity
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((100, 0, 0, self.flash_alpha))
        self.display_surface.blit(overlay, (0, 0))
        
        # Surge text
        surge_text = "CORRUPTION SURGE!"
        surge_surf = self.title_font.render(surge_text, True, (255, 0, 0))
        surge_rect = surge_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        
        # Shadow for text
        shadow_surf = self.title_font.render(surge_text, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(surge_rect.centerx + 3, surge_rect.centery + 3))
        self.display_surface.blit(shadow_surf, shadow_rect)
        self.display_surface.blit(surge_surf, surge_rect)
    
    def draw(self):
        """Draw all surge UI elements"""
        self.draw_warning()
        self.draw_surge()
    
    def get_shake_offset(self):
        """Get current screen shake offset"""
        if self.surge_active:
            return self.shake_offset
        return pygame.math.Vector2(0, 0)
    
    def is_active(self):
        """Check if warning or surge is currently active"""
        return self.warning_active or self.surge_active
    
    def draw_report(self):
        if not self.report_active:
            return

        # Dark background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.display_surface.blit(overlay, (0, 0))

        # Window box  ✅ MUST COME BEFORE button
        box = pygame.Rect(0, 0, 520, 360)
        box.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        pygame.draw.rect(self.display_surface, (20, 0, 0), box, border_radius=12)
        pygame.draw.rect(self.display_surface, (200, 50, 50), box, 4, border_radius=12)

        # Close button ✅ NOW box exists
        btn_size = 36
        self.close_button_rect = pygame.Rect(
            box.right - btn_size - 12,
            box.top + 12,
            btn_size,
            btn_size
        )

        pygame.draw.rect(self.display_surface, (120, 0, 0), self.close_button_rect, border_radius=6)
        pygame.draw.rect(self.display_surface, (255, 80, 80), self.close_button_rect, 2, border_radius=6)

        x_text = self.font.render("X", True, (255, 200, 200))
        x_rect = x_text.get_rect(center=self.close_button_rect.center)
        self.display_surface.blit(x_text, x_rect)

        # Title
        title = self.title_font.render("Corruption Surge Report", True, (255, 80, 80))
        title_rect = title.get_rect(center=(box.centerx, box.top + 40))
        self.display_surface.blit(title, title_rect)

        # Crop list
        y = box.top + 90

        if not self.destroyed_crops:
            text = self.font.render("No crops were destroyed.", True, (220, 220, 220))
            self.display_surface.blit(text, (box.left + 40, y))
        else:
            for crop, amount in self.destroyed_crops.items():
                line = f"- {crop.capitalize()}: {amount}"
                text = self.font.render(line, True, (255, 220, 220))
                self.display_surface.blit(text, (box.left + 40, y))
                y += 35

        hint = self.font.render("Click X to close", True, (180, 180, 180))
        hint_rect = hint.get_rect(center=(box.centerx, box.bottom - 30))
        self.display_surface.blit(hint, hint_rect)


    def handle_report_input(self, events):
        if not self.report_active or not self.close_button_rect:
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.close_button_rect.collidepoint(event.pos):
                    self.report_active = False
                    self.close_button_rect = None



