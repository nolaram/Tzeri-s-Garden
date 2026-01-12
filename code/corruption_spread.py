import pygame
from settings import *
from random import randint, choice
from sprites import Generic

class CorruptionSpread:
    def __init__(self, all_sprites, collision_sprites):
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.display_surface = pygame.display.get_surface()
        
        # Corrupted tiles tracking
        self.corrupted_tiles = []  # List of (x, y) grid positions
        self.corrupted_sprites = pygame.sprite.Group()
        
        # Spread settings
        self.spread_interval = 60  # Spread every 1 minute
        self.spread_timer = 0
        self.tiles_per_spread = 2  # Spread to 2 tiles each time
        
        # Punishment for sleeping during day
        self.day_sleep_punishment = 10  # Extra tiles when sleeping during day
        
        # Damage settings
        self.damage_per_second = 1
        self.damage_timer = 0
        self.damage_interval = 1.0  # Damage every 1 second

        # Notification settings
        self.show_spread_notification = False
        self.notification_timer = 0
        self.notification_duration = 3.0  # Show for 3 seconds
        self.last_spread_count = 0
        
        # Create subtle corrupted tile that blends with ground
        self.corruption_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        # Dark purple/black base with transparency to show ground beneath
        self.corruption_surf.fill((40, 20, 50, 180))

        # Add organic corruption spots (like mold/decay)
        for i in range(20):
            x = randint(0, TILE_SIZE)
            y = randint(0, TILE_SIZE)
            size = randint(4, 12)
            # Dark purple spots
            pygame.draw.circle(self.corruption_surf, (60, 20, 80, 200), (x, y), size)

        # Add some darker patches
        for i in range(10):
            x = randint(0, TILE_SIZE)
            y = randint(0, TILE_SIZE)
            size = randint(8, 16)
            pygame.draw.circle(self.corruption_surf, (20, 10, 30, 150), (x, y), size)

        # Add subtle veins/cracks
        for i in range(5):
            x1, y1 = randint(0, TILE_SIZE), randint(0, TILE_SIZE)
            x2, y2 = randint(0, TILE_SIZE), randint(0, TILE_SIZE)
            pygame.draw.line(self.corruption_surf, (80, 30, 100, 180), (x1, y1), (x2, y2), 2)

        # Add slight purple glow around edges
        pygame.draw.rect(self.corruption_surf, (100, 40, 120, 100), self.corruption_surf.get_rect(), 3)
                    
        # Map bounds (get from ground image)
        try:
            ground = pygame.image.load('graphics/world/ground.png')
            self.map_width = ground.get_width() // TILE_SIZE
            self.map_height = ground.get_height() // TILE_SIZE
        except:
            self.map_width = 100
            self.map_height = 100
    
    def update_corruption_visuals(self):
        """Make corruption tiles pulse for visibility"""
        import math
        pulse = abs(math.sin(pygame.time.get_ticks() / 1000.0))
        
        for sprite in self.corrupted_sprites.sprites():
            # Make the sprite pulse by adjusting alpha
            sprite.image.set_alpha(int(180 + 75 * pulse))
    
    def tint_surface(self, surface, color):
        """Tint a surface with a color"""
        tinted = surface.copy()
        tinted.fill(color + (0,), special_flags=pygame.BLEND_RGBA_MULT)
        return tinted
    
    def is_valid_tile(self, grid_x, grid_y):
        """Check if tile position is valid"""
        if grid_x < 0 or grid_y < 0:
            return False
        if grid_x >= self.map_width or grid_y >= self.map_height:
            return False
        return True
    
    def add_corrupted_tile(self, grid_x, grid_y, ward_system=None):
        """Add a corrupted tile at grid position"""
        if not self.is_valid_tile(grid_x, grid_y):
            return
        
        # Check if tile is protected by ward
        if ward_system and ward_system.is_tile_protected(grid_x, grid_y):
            print(f"🛡️ Tile ({grid_x}, {grid_y}) protected by ward!")
            return
        
        # Don't add if already corrupted
        if (grid_x, grid_y) in self.corrupted_tiles:
            return
        
        # Add to tracking
        self.corrupted_tiles.append((grid_x, grid_y))
        
        # Create visual sprite
        pos = (grid_x * TILE_SIZE, grid_y * TILE_SIZE)
        
        try:
            corruption_sprite = Generic(
            pos=pos,
            surf=self.corruption_surf,
            groups=[self.all_sprites, self.corrupted_sprites],
            z=LAYERS['main'] + 0.7  # Draw ABOVE everything including player
        )
        except Exception as e:
            print(f"❌ Failed to create corruption sprite: {e}")
            self.corrupted_tiles.remove((grid_x, grid_y))
            return
        
        # Reduce console spam - only print every 10th tile
        if len(self.corrupted_tiles) % 10 == 0:
            print(f"🦠 Corruption count: {len(self.corrupted_tiles)} tiles")
    
    def spread_corruption(self, num_tiles=None, ward_system=None):
        """Spread corruption to random tiles"""
        
        if num_tiles is None:
            num_tiles = self.tiles_per_spread

        # If no corruption exists yet, start with random tiles
        if not self.corrupted_tiles:
            for _ in range(num_tiles):
                grid_x = randint(0, self.map_width - 1)
                grid_y = randint(0, self.map_height - 1)
                self.add_corrupted_tile(grid_x, grid_y, ward_system)
            return

        # Spread from existing corruption
        for _ in range(num_tiles):
            if not self.corrupted_tiles:
                break

            # Safety check - if map is nearly full, stop spreading
            if len(self.corrupted_tiles) >= (self.map_width * self.map_height * 0.8):
                print("⚠️ Map is 80% corrupted, stopping spread")
                return

            # Pick a random corrupted tile to spread from
            source_x, source_y = choice(self.corrupted_tiles)

            directions = [
                (0, 1), (0, -1), (1, 0), (-1, 0),
                (1, 1), (-1, -1), (1, -1), (-1, 1)
            ]

            attempts = 0
            max_attempts = 50
            found = False

            while attempts < max_attempts:
                dx, dy = choice(directions)
                new_x = source_x + dx
                new_y = source_y + dy

                if self.is_valid_tile(new_x, new_y) and (new_x, new_y) not in self.corrupted_tiles:
                    self.add_corrupted_tile(new_x, new_y, ward_system)
                    found = True
                    break

                attempts += 1

            # Fallback: random tile
            if not found:
                attempts = 0
                while attempts < max_attempts:
                    new_x = randint(0, self.map_width - 1)
                    new_y = randint(0, self.map_height - 1)

                    if (new_x, new_y) not in self.corrupted_tiles:
                        self.add_corrupted_tile(new_x, new_y, ward_system)
                        break

                    attempts += 1
   
    def remove_corrupted_tile(self, grid_x, grid_y):
        """Remove a corrupted tile"""
        if (grid_x, grid_y) in self.corrupted_tiles:
            self.corrupted_tiles.remove((grid_x, grid_y))
            
            # Remove sprite
            for sprite in self.corrupted_sprites.sprites():
                if hasattr(sprite, 'rect'):
                    sprite_grid_x = sprite.rect.x // TILE_SIZE
                    sprite_grid_y = sprite.rect.y // TILE_SIZE
                    if sprite_grid_x == grid_x and sprite_grid_y == grid_y:
                        sprite.kill()
                        break
    
    def check_and_destroy_crops(self, soil_layer):
        """Check if any crops are on corrupted tiles and destroy them"""
        if not soil_layer or not soil_layer.plant_sprites:
            return
        
        # Use a set for faster lookup
        corrupted_set = set(self.corrupted_tiles)
        
        destroyed_count = 0
        plants_to_destroy = []
        
        # First pass - identify plants to destroy
        for plant in soil_layer.plant_sprites.sprites():
            # Get plant grid position
            plant_grid_x = plant.rect.centerx // TILE_SIZE
            plant_grid_y = plant.rect.centery // TILE_SIZE
            
            # Check if plant is on corrupted tile
            if (plant_grid_x, plant_grid_y) in corrupted_set:
                plants_to_destroy.append(plant)
        
        # Second pass - destroy identified plants
        for plant in plants_to_destroy:
            plant_grid_x = plant.rect.centerx // TILE_SIZE
            plant_grid_y = plant.rect.centery // TILE_SIZE
            
            # Remove from soil grid
            if 0 <= plant_grid_y < len(soil_layer.grid) and 0 <= plant_grid_x < len(soil_layer.grid[0]):
                cell = soil_layer.grid[plant_grid_y][plant_grid_x]
                while 'P' in cell:
                    cell.remove('P')
            
            # Create particle effect
            try:
                from sprites import Particle
                Particle(
                    plant.rect.topleft,
                    plant.image,
                    [self.all_sprites],
                    LAYERS['main'],
                    duration=300
                )
            except:
                pass  # Skip particle if it fails
            
            # Destroy plant
            plant.kill()
            destroyed_count += 1
        
        if destroyed_count > 0:
            print(f"🦠 Corruption destroyed {destroyed_count} crops")
    
    def punish_day_sleep(self):
        """Spread extra corruption when player sleeps during day"""
        print(f"⚠️ Day sleep punishment: {self.day_sleep_punishment} extra corrupted tiles!")
        self.spread_corruption(self.day_sleep_punishment)
    
    def is_player_on_corruption(self, player_rect):
        """Check if player is standing on corrupted tile"""
        player_grid_x = player_rect.centerx // TILE_SIZE
        player_grid_y = player_rect.centery // TILE_SIZE
        return (player_grid_x, player_grid_y) in self.corrupted_tiles
    
    def damage_player(self, player_health_system):
        """Damage player if on corrupted tile"""
        self.damage_timer += self.damage_interval
        player_health_system.take_damage(self.damage_per_second)
        print(f"💔 Player damaged by corruption! Health: {player_health_system.current_health}")
    
    def update(self, dt, soil_layer=None, player=None, player_health=None, ward_system=None):
        """Update corruption spread"""
        # Update notification timer
        # Add this line at the start
        self.update_corruption_visuals()
        if self.show_spread_notification:
            self.notification_timer += dt
            if self.notification_timer >= self.notification_duration:
                self.show_spread_notification = False
        
        # Spread timer
        self.spread_timer += dt
        
        if self.spread_timer >= self.spread_interval:
            self.spread_timer = 0
            
            count_before = len(self.corrupted_tiles)
            
            self.spread_corruption(ward_system=ward_system)
            
            # Calculate how many tiles were added
            count_after = len(self.corrupted_tiles)
            self.last_spread_count = count_after - count_before
            
            # Show notification
            if self.last_spread_count > 0:
                self.show_spread_notification = True
                self.notification_timer = 0
            
            # Check and destroy crops when corruption spreads
            if soil_layer:
                self.check_and_destroy_crops(soil_layer)
        
        # Damage timer
        if player and player_health:
            if self.is_player_on_corruption(player.rect):
                self.damage_timer += dt
                if self.damage_timer >= self.damage_interval:
                    self.damage_timer = 0
                    self.damage_player(player_health)
            else:
                self.damage_timer = 0

    def draw_spread_notification(self):
        """Draw notification when corruption spreads"""
        if not self.show_spread_notification:
            return
        
        # Calculate fade based on timer
        fade_progress = self.notification_timer / self.notification_duration
        alpha = int(255 * (1 - fade_progress))  # Fade out over time
        
        # Position at top center
        x = SCREEN_WIDTH // 2
        y = 150
        
        # Text
        spread_text = f"🦠 Corruption Spread! +{self.last_spread_count} tiles"
        try:
            font = pygame.font.Font('font/LycheeSoda.ttf', 24)
        except:
            font = pygame.font.Font(None, 24)
        
        text_surf = font.render(spread_text, True, (255, 100, 100))
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect(center=(x, y))
        
        # Background box
        padding = 15
        bg_rect = text_rect.inflate(padding * 2, padding)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((20, 0, 0, min(180, alpha)))
        
        # Draw
        self.display_surface.blit(bg_surf, bg_rect)
        
        # Border
        import math
        pulse = abs(math.sin(pygame.time.get_ticks() / 200.0))
        border_color = (255, int(50 + 100 * pulse), 50, alpha)
        pygame.draw.rect(self.display_surface, border_color, bg_rect, 3, border_radius=8)
        
        self.display_surface.blit(text_surf, text_rect)
        
        # Progress bar showing corruption total
        bar_width = 200
        bar_height = 8
        bar_x = x - bar_width // 2
        bar_y = y + 25
        
        # Calculate corruption percentage
        max_tiles = self.map_width * self.map_height
        corruption_percent = len(self.corrupted_tiles) / max_tiles
        
        # Background bar
        bar_bg = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.display_surface, (40, 0, 0, alpha), bar_bg, border_radius=4)
        
        # Fill bar
        fill_width = int(bar_width * corruption_percent)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(self.display_surface, (200, 50, 50, alpha), fill_rect, border_radius=4)
        
        # Percentage text
        try:
            small_font = pygame.font.Font('font/LycheeSoda.ttf', 16)
        except:
            small_font = pygame.font.Font(None, 16)
        
        percent_text = f"{int(corruption_percent * 100)}% Corrupted"
        percent_surf = small_font.render(percent_text, True, (255, 150, 150))
        percent_surf.set_alpha(alpha)
        percent_rect = percent_surf.get_rect(center=(x, bar_y + bar_height + 12))
        self.display_surface.blit(percent_surf, percent_rect)
    
    def draw(self):
        """Draw corruption UI elements"""
        self.draw_spread_notification()

    def clear_all_corruption(self):
        """Clear all corrupted tiles (for testing or cleansing)"""
        self.corrupted_tiles.clear()
        for sprite in self.corrupted_sprites.sprites():
            sprite.kill()
        print("✨ All corruption cleared!")
    
    def get_corruption_count(self):
        """Get number of corrupted tiles"""
        return len(self.corrupted_tiles)
    
    def draw(self):
        """Draw corruption UI elements"""
        self.draw_spread_notification()


class HealthSystem:
    def __init__(self, on_death=None):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 20)
        
        # Health settings
        self.max_health = 100
        self.current_health = 100
        
        # Death callback
        self.on_death = on_death
        
        # Visual settings
        self.bar_width = 200
        self.bar_height = 24
        self.padding = 20
        
        # Invulnerability for damage cooldown
        self.invulnerable = False
        self.invuln_duration = 0.5
        self.invuln_timer = 0
    
    def take_damage(self, amount):
        """Take damage"""
        if self.invulnerable:
            return
        
        self.current_health = max(0, self.current_health - amount)
        self.invulnerable = True
        self.invuln_timer = 0
        
        if self.current_health <= 0:
            print("💀 Player died!")
            if self.on_death:
                self.on_death()
    
    def heal(self, amount):
        """Heal player"""
        self.current_health = min(self.max_health, self.current_health + amount)
    
    def restore_full(self):
        """Restore health to full (used when sleeping)"""
        self.current_health = self.max_health
    
    def is_dead(self):
        """Check if player is dead"""
        return self.current_health <= 0
    
    def update(self, dt):
        """Update invulnerability timer"""
        if self.invulnerable:
            self.invuln_timer += dt
            if self.invuln_timer >= self.invuln_duration:
                self.invulnerable = False
    
    def get_health_color(self):
        """Get color based on health level"""
        health_percent = self.current_health / self.max_health
        
        if health_percent > 0.5:
            # Green
            return (100, 200, 100)
        elif health_percent > 0.25:
            # Yellow to orange
            return (200, 200, 50)
        else:
            # Red (low health)
            return (200, 50, 50)
    
    def draw(self):
        """Draw health bar in bottom-right corner (above energy bar)"""
        # Position in bottom-right, above energy bar
        x = SCREEN_WIDTH - self.bar_width - self.padding
        y = SCREEN_HEIGHT - (self.bar_height * 2) - self.padding - 60
        
        # Background bar (darker)
        bg_rect = pygame.Rect(x - 4, y - 4, self.bar_width + 8, self.bar_height + 8)
        pygame.draw.rect(self.display_surface, (20, 20, 20), bg_rect, border_radius=6)
        pygame.draw.rect(self.display_surface, (100, 100, 100), bg_rect, 2, border_radius=6)
        
        # Health bar background (empty portion)
        bar_bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(self.display_surface, (40, 40, 40), bar_bg_rect, border_radius=4)
        
        # Health bar fill
        health_percent = self.current_health / self.max_health
        fill_width = int(self.bar_width * health_percent)
        
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y, fill_width, self.bar_height)
            health_color = self.get_health_color()
            pygame.draw.rect(self.display_surface, health_color, fill_rect, border_radius=4)
            
            # Add a highlight effect on top
            highlight_rect = pygame.Rect(x, y, fill_width, self.bar_height // 3)
            highlight_color = tuple(min(255, c + 30) for c in health_color)
            pygame.draw.rect(self.display_surface, highlight_color, highlight_rect, border_radius=4)
        
        # Health text (centered in bar)
        health_text = f"{int(self.current_health)}/{self.max_health}"
        text_surf = self.font.render(health_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(x + self.bar_width // 2, y + self.bar_height // 2))
        
        # Text shadow for better readability
        shadow_surf = self.font.render(health_text, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(text_rect.centerx + 1, text_rect.centery + 1))
        self.display_surface.blit(shadow_surf, shadow_rect)
        self.display_surface.blit(text_surf, text_rect)
        
        # Label above bar
        label_text = "Health"
        label_surf = self.font.render(label_text, True, (200, 200, 200))
        label_rect = label_surf.get_rect(midtop=(x + self.bar_width // 2, y - 24))
        
        # Label shadow
        label_shadow = self.font.render(label_text, True, (0, 0, 0))
        label_shadow_rect = label_shadow.get_rect(midtop=(label_rect.centerx + 1, label_rect.top + 1))
        self.display_surface.blit(label_shadow, label_shadow_rect)
        self.display_surface.blit(label_surf, label_rect)
        
        # Warning indicator when health is low
        if health_percent < 0.2:
            self.draw_low_health_warning()
    
    def draw_low_health_warning(self):
        """Draw a pulsing warning when health is low"""
        # Calculate pulse effect
        import math
        pulse = abs(math.sin(pygame.time.get_ticks() / 500.0))
        alpha = int(100 + 155 * pulse)
        
        # Warning text
        warning_text = "Low Health!"
        warning_surf = self.font.render(warning_text, True, (255, 100, 100))
        warning_surf.set_alpha(alpha)
        
        x = SCREEN_WIDTH - self.bar_width - self.padding
        y = SCREEN_HEIGHT - (self.bar_height * 2) - self.padding - 110
        
        warning_rect = warning_surf.get_rect(midtop=(x + self.bar_width // 2, y))
        self.display_surface.blit(warning_surf, warning_rect)