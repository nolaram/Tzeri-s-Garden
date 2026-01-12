import pygame
from settings import *
from sprites import Generic

class Ward(Generic):
    def __init__(self, pos, groups):
        # Create ward visual
        ward_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # Draw a glowing protective circle
        # Outer glow
        pygame.draw.circle(ward_surf, (100, 200, 255, 100), (TILE_SIZE // 2, TILE_SIZE // 2), 28)
        # Middle ring
        pygame.draw.circle(ward_surf, (150, 220, 255, 200), (TILE_SIZE // 2, TILE_SIZE // 2), 20)
        # Inner core
        pygame.draw.circle(ward_surf, (200, 240, 255), (TILE_SIZE // 2, TILE_SIZE // 2), 12)
        # Bright center
        pygame.draw.circle(ward_surf, (255, 255, 255), (TILE_SIZE // 2, TILE_SIZE // 2), 6)
        
        super().__init__(pos, ward_surf, groups, LAYERS['main'])
        
        # Ward properties
        self.protection_radius = 6  # Protects 8 tiles in each direction
        self.grid_x = pos[0] // TILE_SIZE
        self.grid_y = pos[1] // TILE_SIZE
        self.pulse_timer = 0
        
    def get_protected_tiles(self):
        """Get list of tiles protected by this ward"""
        protected = []
        for dx in range(-self.protection_radius, self.protection_radius + 1):
            for dy in range(-self.protection_radius, self.protection_radius + 1):
                protected.append((self.grid_x + dx, self.grid_y + dy))
        return protected
    
    def update(self, dt):
        """Update ward animation"""
        self.pulse_timer += dt
        # Pulsing glow effect could be added here


class WardSystem:
    def __init__(self, all_sprites):
        self.all_sprites = all_sprites
        self.ward_sprites = pygame.sprite.Group()
        self.display_surface = pygame.display.get_surface()
        
    def place_ward(self, grid_x, grid_y):
        """Place a ward at grid position"""
        # Check if ward already exists here
        for ward in self.ward_sprites.sprites():
            if ward.grid_x == grid_x and ward.grid_y == grid_y:
                print("⚠️ Ward already placed here!")
                return False
        
        # Create ward
        pos = (grid_x * TILE_SIZE, grid_y * TILE_SIZE)
        ward = Ward(pos, [self.all_sprites, self.ward_sprites])
        print(f"🛡️ Ward placed at ({grid_x}, {grid_y})")
        
        # CLEAR CORRUPTION in ward radius
        if hasattr(self, 'corruption_spread_ref') and self.corruption_spread_ref:
            protected_tiles = ward.get_protected_tiles()
            cleared_count = 0
            for tile_x, tile_y in protected_tiles:
                if (tile_x, tile_y) in self.corruption_spread_ref.corrupted_tiles:
                    self.corruption_spread_ref.remove_corrupted_tile(tile_x, tile_y)
                    cleared_count += 1
            print(f"✨ Ward cleared {cleared_count} corruption tiles!")
        
        return True
        
    def get_all_protected_tiles(self):
        """Get all tiles protected by wards"""
        protected = set()
        for ward in self.ward_sprites.sprites():
            protected.update(ward.get_protected_tiles())
        return protected
    
    def is_tile_protected(self, grid_x, grid_y):
        """Check if a tile is protected by any ward"""
        return (grid_x, grid_y) in self.get_all_protected_tiles()
    
    def draw_protection_radius(self, player_target_pos):
        """Draw ward placement preview"""
        grid_x = int(player_target_pos.x // TILE_SIZE)
        grid_y = int(player_target_pos.y // TILE_SIZE)
        
        # Draw preview of protection area
        for dx in range(-6, 7):
            for dy in range(-6, 7):
                tile_x = (grid_x + dx) * TILE_SIZE
                tile_y = (grid_y + dy) * TILE_SIZE
                
                # Draw semi-transparent blue overlay
                preview_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                preview_surf.fill((100, 200, 255, 50))
                
                # Get camera offset
                from level import CameraGroup
                if hasattr(self, 'camera_offset'):
                    offset = self.camera_offset
                else:
                    offset = pygame.math.Vector2(0, 0)
                
                preview_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
                self.display_surface.blit(preview_surf, preview_rect.move(-offset))