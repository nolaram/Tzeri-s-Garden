import pygame
from settings import *

class InventoryUI:
    def __init__(self, player):
        self.player = player
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 24)
        self.font_small = pygame.font.Font('font/LycheeSoda.ttf', 18)
        
        # UI settings
        self.bg_color = (20, 20, 20)
        self.border_color = (255, 255, 255)
        self.highlight_color = (100, 100, 100)
        
        # Inventory panel dimensions (slightly smaller)
        self.width = 520
        self.height = 420
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = (SCREEN_HEIGHT - self.height) // 2
        
        # Item slot settings (more compact)
        self.slot_size = 64
        self.slots_per_row = 6
        self.slot_padding = 6
        
        # Load item icons
        self.item_icons = {}
        self.load_item_icons()
    
    def load_item_icons(self):
        items_to_load = [
            'corn', 'tomato', 'moon_melon', 'pumpkin', 'cactus',
            'corn seed', 'tomato seed', 'wood', 'apple'
        ]
        
        for item in items_to_load:
            try:
                if 'seed' in item:
                    crop_name = item.replace(' seed', '')
                    path = f'graphics/fruit/{crop_name}/0.png'   # seeds = stage 0
                elif item == 'wood':
                    path = 'graphics/stumps/small.png'
                elif item == 'apple':
                    path = 'graphics/fruit/apple.png'
                else:
                    path = f'graphics/fruit/{item}/3.png'        # fruits = stage 3
                
                icon = pygame.image.load(path).convert_alpha()
                icon = pygame.transform.scale(
                    icon, (self.slot_size - 16, self.slot_size - 16)
                )
                self.item_icons[item] = icon
            except:
                placeholder = pygame.Surface(
                    (self.slot_size - 16, self.slot_size - 16)
                )
                placeholder.fill((100, 100, 100))
                self.item_icons[item] = placeholder
    
    def draw(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.display_surface.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        
        panel_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        panel_surf.fill((20, 20, 20, 200))  
        self.display_surface.blit(panel_surf, (self.x, self.y))
        pygame.draw.rect(self.display_surface, self.border_color, panel_rect, 3)


        
        title_surf = self.font.render("Inventory", True, self.border_color)
        self.display_surface.blit(
            title_surf,
            title_surf.get_rect(centerx=self.x + self.width // 2, y=self.y + 15)
        )
        
        close_surf = self.font_small.render(
            "Press 'Tab' or 'ESC' to close", True, (200, 200, 200)
        )
        self.display_surface.blit(
            close_surf,
            close_surf.get_rect(centerx=self.x + self.width // 2, y=self.y + 45)
        )
        
        current_y = self.y + 80
        
        # CROPS
        self.display_surface.blit(
            self.font.render("CROPS", True, (255, 200, 100)),
            (self.x + 20, current_y)
        )
        current_y += 30
        
        crop_items = ['corn', 'tomato', 'moon_melon', 'pumpkin', 'cactus']
        items_drawn = self.draw_category_items(
            crop_items, self.player.item_inventory, current_y
        )
        current_y += max(1, (items_drawn - 1) // self.slots_per_row + 1) * (
            self.slot_size + self.slot_padding
        ) + 20
        
        # SEEDS
        self.display_surface.blit(
            self.font.render("SEEDS", True, (255, 200, 100)),
            (self.x + 20, current_y)
        )
        current_y += 30
        
        seed_items = ['corn', 'tomato', 'moon_melon', 'pumpkin', 'cactus']
        items_drawn = self.draw_category_items(
            seed_items, self.player.seed_inventory, current_y, is_seed=True
        )
        current_y += max(1, (items_drawn - 1) // self.slots_per_row + 1) * (
            self.slot_size + self.slot_padding
        ) + 20
        
        # RESOURCES
        self.display_surface.blit(
            self.font.render("RESOURCES", True, (255, 200, 100)),
            (self.x + 20, current_y)
        )
        current_y += 30
        
        resource_items = ['wood', 'apple']
        self.draw_category_items(
            resource_items, self.player.item_inventory, current_y
        )

        # Draw ward count separately
        current_y += 80
        ward_text = f"Wards: {self.player.ward_count}"
        ward_surf = self.font.render(ward_text, True, (150, 220, 255))
        self.display_surface.blit(ward_surf, (self.x + 20, current_y))
        
        if hasattr(self.player, 'money'):
            money_surf = self.font.render(
                f"Money: ${self.player.money}", True, (255, 215, 0)
            )
            self.display_surface.blit(
                money_surf,
                money_surf.get_rect(
                    bottomright=(self.x + self.width - 15,
                                 self.y + self.height - 15)
                )
            )
    
    def draw_category_items(self, items, inventory_dict, start_y, is_seed=False):
        items_drawn = 0
        mouse_pos = pygame.mouse.get_pos()
        
        for item in items:
            if item in inventory_dict and inventory_dict[item] > 0:
                col = items_drawn % self.slots_per_row
                row = items_drawn // self.slots_per_row
                
                slot_x = self.x + 20 + col * (self.slot_size + self.slot_padding)
                slot_y = start_y + row * (self.slot_size + self.slot_padding)
                
                slot_rect = pygame.Rect(
                    slot_x, slot_y, self.slot_size, self.slot_size
                )
                
                pygame.draw.rect(self.display_surface, (40, 40, 40), slot_rect)
                pygame.draw.rect(self.display_surface, (120, 120, 120), slot_rect, 2)
                
                icon_key = item if not is_seed else f"{item} seed"
                icon = self.item_icons.get(icon_key, self.item_icons.get(item))
                if icon:
                    self.display_surface.blit(
                        icon, icon.get_rect(center=slot_rect.center)
                    )
                
                qty_surf = self.font_small.render(
                    str(inventory_dict[item]), True, (255, 255, 255)
                )
                qty_rect = qty_surf.get_rect(
                    bottomright=(slot_rect.right - 4, slot_rect.bottom - 4)
                )
                pygame.draw.rect(
                    self.display_surface, (0, 0, 0),
                    qty_rect.inflate(6, 4)
                )
                self.display_surface.blit(qty_surf, qty_rect)
                
                # 🔹 HOVER TOOLTIP ONLY
                if slot_rect.collidepoint(mouse_pos):
                    name = item.replace('_', ' ').title()
                    if is_seed:
                        name += " Seed"
                    
                    tip_surf = self.font_small.render(name, True, (255, 255, 255))
                    tip_rect = tip_surf.get_rect(
                        midbottom=(mouse_pos[0], mouse_pos[1] - 10)
                    )
                    
                    pygame.draw.rect(
                        self.display_surface, (0, 0, 0),
                        tip_rect.inflate(10, 6)
                    )
                    pygame.draw.rect(
                        self.display_surface, (255, 255, 255),
                        tip_rect.inflate(10, 6), 1
                    )
                    self.display_surface.blit(tip_surf, tip_rect)
                
                items_drawn += 1
        
        return items_drawn
