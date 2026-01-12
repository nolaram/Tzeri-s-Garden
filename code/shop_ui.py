import pygame
from settings import *

class ShopUI:
    def __init__(self, player, toggle_shop):
        self.player = player
        self.toggle_shop = toggle_shop
        self.display_surface = pygame.display.get_surface()
        
        # Fonts
        self.title_font = pygame.font.Font('font/LycheeSoda.ttf', 48)
        self.price_font = pygame.font.Font('font/LycheeSoda.ttf', 20)
        self.button_font = pygame.font.Font('font/LycheeSoda.ttf', 18)
        self.money_font = pygame.font.Font('font/LycheeSoda.ttf', 28)
        self.tooltip_font = pygame.font.Font('font/LycheeSoda.ttf', 16)
        
        # Shop dimensions
        self.shop_width = 700
        self.shop_height = 500
        self.shop_x = (SCREEN_WIDTH - self.shop_width) // 2
        self.shop_y = (SCREEN_HEIGHT - self.shop_height) // 2
        
        # Colors
        self.bg_color = (101, 67, 33)  # Brown
        self.frame_color = (139, 90, 43)  # Light brown
        self.slot_bg = (255, 200, 100)  # Yellow-orange
        self.button_buy = (100, 200, 100)  # Green
        self.button_sell = (200, 100, 100)  # Red
        self.button_hover = (220, 220, 100)  # Yellow
        
        # Item slots setup
        self.slot_size = 90
        self.slots_per_row = 4
        self.slot_padding = 20
        self.items_start_y = self.shop_y + 120
        
        # Scrolling
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        
        # Content area (where items are drawn)
        self.content_x = self.shop_x + 30
        self.content_y = self.items_start_y
        self.content_width = self.shop_width - 100  # Leave room for scrollbar
        self.content_height = self.shop_height - 200  # Title + money display
        
        # Create a surface for scrollable content
        self.content_surface = None
        
        # Scrollbar
        self.scrollbar_x = self.shop_x + self.shop_width - 50
        self.scrollbar_width = 20
        self.scrollbar_height = self.content_height
        self.scrollbar_y = self.content_y
        
        # Load item icons
        self.item_icons = {}
        self.load_icons()
        
        # Shop items - ALL items now!
        self.shop_items = [
            # Seeds to buy
            {'name': 'corn', 'type': 'seed', 'buy_price': PURCHASE_PRICES['corn'], 'sell_price': None},
            {'name': 'tomato', 'type': 'seed', 'buy_price': PURCHASE_PRICES['tomato'], 'sell_price': None},
            {'name': 'moon_melon', 'type': 'seed', 'buy_price': PURCHASE_PRICES['moon_melon'], 'sell_price': None},
            {'name': 'pumpkin', 'type': 'seed', 'buy_price': PURCHASE_PRICES['pumpkin'], 'sell_price': None},
            {'name': 'cactus', 'type': 'seed', 'buy_price': PURCHASE_PRICES['cactus'], 'sell_price': None},
            
            # Crops to sell
            {'name': 'corn', 'type': 'crop', 'buy_price': None, 'sell_price': SALE_PRICES['corn']},
            {'name': 'tomato', 'type': 'crop', 'buy_price': None, 'sell_price': SALE_PRICES['tomato']},
            {'name': 'moon_melon', 'type': 'crop', 'buy_price': None, 'sell_price': SALE_PRICES['moon_melon']},
            {'name': 'pumpkin', 'type': 'crop', 'buy_price': None, 'sell_price': SALE_PRICES['pumpkin']},
            {'name': 'cactus', 'type': 'crop', 'buy_price': None, 'sell_price': SALE_PRICES['cactus']},
            
            # Resources to sell
            {'name': 'wood', 'type': 'resource', 'buy_price': None, 'sell_price': SALE_PRICES['wood']},
            {'name': 'apple', 'type': 'resource', 'buy_price': None, 'sell_price': SALE_PRICES['apple']},
        ]
        
        # Create slot rectangles and button rectangles
        self.setup_slots()
        
        # Hover state
        self.hovered_slot = None
        
        # Close button
        self.close_button_rect = pygame.Rect(
            self.shop_x + self.shop_width - 50,
            self.shop_y + 10,
            40, 40
        )
        
        # Dragging scrollbar
        self.dragging_scrollbar = False
    
    def load_icons(self):
        """Load item icons"""
        items_to_load = ['corn', 'tomato', 'moon_melon', 'pumpkin', 'cactus']
        
        for item in items_to_load:
            try:
                # Seed icon (stage 0)
                seed_path = f'graphics/fruit/{item}/0.png'
                seed_icon = pygame.image.load(seed_path).convert_alpha()
                seed_icon = pygame.transform.scale(seed_icon, (60, 60))
                self.item_icons[f'{item}_seed'] = seed_icon
                
                # Crop icon (stage 3)
                crop_path = f'graphics/fruit/{item}/3.png'
                crop_icon = pygame.image.load(crop_path).convert_alpha()
                crop_icon = pygame.transform.scale(crop_icon, (60, 60))
                self.item_icons[f'{item}_crop'] = crop_icon
            except:
                # Fallback placeholder
                placeholder = pygame.Surface((60, 60))
                placeholder.fill((150, 150, 150))
                self.item_icons[f'{item}_seed'] = placeholder
                self.item_icons[f'{item}_crop'] = placeholder
        
        # Load resource icons
        try:
            wood_icon = pygame.image.load('graphics/stumps/small.png').convert_alpha()
            wood_icon = pygame.transform.scale(wood_icon, (60, 60))
            self.item_icons['wood_resource'] = wood_icon
        except:
            placeholder = pygame.Surface((60, 60))
            placeholder.fill((139, 69, 19))
            self.item_icons['wood_resource'] = placeholder
        
        try:
            apple_icon = pygame.image.load('graphics/fruit/apple.png').convert_alpha()
            apple_icon = pygame.transform.scale(apple_icon, (60, 60))
            self.item_icons['apple_resource'] = apple_icon
        except:
            placeholder = pygame.Surface((60, 60))
            placeholder.fill((255, 0, 0))
            self.item_icons['apple_resource'] = placeholder
    
    def setup_slots(self):
        """Setup slot positions and button rectangles"""
        self.slots = []
        
        # Calculate total content height
        total_rows = (len(self.shop_items) + self.slots_per_row - 1) // self.slots_per_row
        slot_height_with_button = self.slot_size + 60  # slot + button + padding
        total_content_height = total_rows * (slot_height_with_button + self.slot_padding)
        
        # Create content surface large enough for all items
        self.content_surface = pygame.Surface((self.content_width, total_content_height), pygame.SRCALPHA)
        
        # Calculate max scroll
        self.max_scroll = max(0, total_content_height - self.content_height)
        
        for i, item in enumerate(self.shop_items):
            row = i // self.slots_per_row
            col = i % self.slots_per_row
            
            # Position relative to content surface (not screen)
            x = 20 + col * (self.slot_size + self.slot_padding)
            y = 20 + row * (slot_height_with_button + self.slot_padding)
            
            slot_rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
            
            # Button below slot
            button_y = y + self.slot_size + 5
            button_width = self.slot_size
            button_height = 30
            
            if item['type'] == 'seed':
                button_rect = pygame.Rect(x, button_y, button_width, button_height)
                button_type = 'buy'
            else:
                button_rect = pygame.Rect(x, button_y, button_width, button_height)
                button_type = 'sell'
            
            self.slots.append({
                'item': item,
                'slot_rect': slot_rect,
                'button_rect': button_rect,
                'button_type': button_type
            })
    
    def handle_scroll(self, events):
        """Handle mouse wheel scrolling"""
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * self.scroll_speed
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check if clicking on scrollbar
                    scrollbar_rect = pygame.Rect(
                        self.scrollbar_x, self.scrollbar_y,
                        self.scrollbar_width, self.scrollbar_height
                    )
                    if scrollbar_rect.collidepoint(event.pos):
                        self.dragging_scrollbar = True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging_scrollbar = False
        
        # Handle scrollbar dragging
        if self.dragging_scrollbar:
            mouse_y = pygame.mouse.get_pos()[1]
            # Calculate scroll position based on mouse y
            relative_y = mouse_y - self.scrollbar_y
            scroll_percentage = relative_y / self.scrollbar_height
            self.scroll_offset = scroll_percentage * self.max_scroll
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
    
    def handle_input(self, events):
        """Handle mouse input"""
        mouse_pos = pygame.mouse.get_pos()
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check close button
                if self.close_button_rect.collidepoint(mouse_pos):
                    self.toggle_shop()
                    return
                
                # Check item buttons (adjusted for scroll)
                content_mouse_x = mouse_pos[0] - self.content_x
                content_mouse_y = mouse_pos[1] - self.content_y + self.scroll_offset
                
                # Check if click is within content area
                content_rect = pygame.Rect(self.content_x, self.content_y, self.content_width, self.content_height)
                if content_rect.collidepoint(mouse_pos):
                    for slot in self.slots:
                        if slot['button_rect'].collidepoint(content_mouse_x, content_mouse_y):
                            self.handle_transaction(slot)
    
    def handle_transaction(self, slot):
        """Handle buy/sell transaction"""
        item = slot['item']
        
        if slot['button_type'] == 'buy':
            # Buying seeds
            price = item['buy_price']
            if self.player.money >= price:
                self.player.money -= price
                self.player.seed_inventory[item['name']] += 1
        
        elif slot['button_type'] == 'sell':
            # Selling crops or resources
            if item['type'] == 'crop' or item['type'] == 'resource':
                if self.player.item_inventory[item['name']] > 0:
                    self.player.item_inventory[item['name']] -= 1
                    self.player.money += item['sell_price']
    
    def get_item_count(self, item):
        """Get how many of this item the player has"""
        if item['type'] == 'seed':
            return self.player.seed_inventory.get(item['name'], 0)
        else:
            return self.player.item_inventory.get(item['name'], 0)
    
    def can_afford(self, item):
        """Check if player can afford to buy"""
        if item['buy_price'] is None:
            return True
        return self.player.money >= item['buy_price']
    
    def draw(self, events):
        """Draw the shop UI"""
        # Handle scrolling first
        self.handle_scroll(events)
        
        # Handle input
        self.handle_input(events)
        
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.display_surface.blit(overlay, (0, 0))
        
        # Main shop background
        shop_rect = pygame.Rect(self.shop_x, self.shop_y, self.shop_width, self.shop_height)
        pygame.draw.rect(self.display_surface, self.bg_color, shop_rect, border_radius=20)
        pygame.draw.rect(self.display_surface, self.frame_color, shop_rect, 5, border_radius=20)
        
        # Shop title
        title_surf = self.title_font.render('SHOP', True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + 50))
        
        # Title background
        title_bg = pygame.Rect(
            title_rect.x - 20, title_rect.y - 10,
            title_rect.width + 40, title_rect.height + 20
        )
        pygame.draw.rect(self.display_surface, (139, 90, 43), title_bg, border_radius=15)
        pygame.draw.rect(self.display_surface, (255, 215, 0), title_bg, 3, border_radius=15)
        self.display_surface.blit(title_surf, title_rect)
        
        # Clear content surface
        self.content_surface.fill((0, 0, 0, 0))
        
        # Draw item slots on content surface
        mouse_pos = pygame.mouse.get_pos()
        # Adjust mouse position for scrolling
        content_mouse_x = mouse_pos[0] - self.content_x
        content_mouse_y = mouse_pos[1] - self.content_y + self.scroll_offset
        content_mouse_pos = (content_mouse_x, content_mouse_y)
        
        self.hovered_slot = None
        
        for slot in self.slots:
            self.draw_slot_on_surface(slot, content_mouse_pos)
        
        # Draw the scrollable content (clipped to content area)
        content_rect = pygame.Rect(self.content_x, self.content_y, self.content_width, self.content_height)
        
        # Create a subsurface to blit (scrolled portion)
        scroll_rect = pygame.Rect(0, int(self.scroll_offset), self.content_width, self.content_height)
        
        # Blit the scrolled content
        self.display_surface.blit(
            self.content_surface,
            content_rect.topleft,
            scroll_rect
        )
        
        # Draw scrollbar if needed
        if self.max_scroll > 0:
            self.draw_scrollbar()
        
        # Draw money display
        money_text = f"${self.player.money}"
        money_surf = self.money_font.render(money_text, True, (255, 215, 0))
        money_rect = money_surf.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + self.shop_height - 30))
        
        money_bg = money_rect.inflate(20, 10)
        pygame.draw.rect(self.display_surface, (50, 50, 50), money_bg, border_radius=8)
        pygame.draw.rect(self.display_surface, (255, 215, 0), money_bg, 2, border_radius=8)
        self.display_surface.blit(money_surf, money_rect)
        
        # Close button
        pygame.draw.rect(self.display_surface, (200, 50, 50), self.close_button_rect, border_radius=8)
        pygame.draw.rect(self.display_surface, (255, 100, 100), self.close_button_rect, 3, border_radius=8)
        
        close_text = self.button_font.render('X', True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=self.close_button_rect.center)
        self.display_surface.blit(close_text, close_text_rect)
        
        # Draw tooltip if hovering
        if self.hovered_slot:
            self.draw_tooltip(self.hovered_slot, mouse_pos)
    
    def draw_slot_on_surface(self, slot, mouse_pos):
        """Draw a single item slot on the content surface"""
        item = slot['item']
        slot_rect = slot['slot_rect']
        button_rect = slot['button_rect']
        
        # Slot background
        pygame.draw.rect(self.content_surface, self.slot_bg, slot_rect, border_radius=10)
        pygame.draw.rect(self.content_surface, (255, 255, 255), slot_rect, 3, border_radius=10)
        
        # Item icon
        icon_key = f"{item['name']}_{item['type']}"
        if icon_key in self.item_icons:
            icon = self.item_icons[icon_key]
            icon_rect = icon.get_rect(center=slot_rect.center)
            self.content_surface.blit(icon, icon_rect)
        
        # Price tag
        if item['buy_price']:
            price_text = f"${item['buy_price']}"
        else:
            price_text = f"${item['sell_price']}"
        
        price_surf = self.price_font.render(price_text, True, (0, 0, 0))
        price_rect = price_surf.get_rect(center=(slot_rect.centerx, slot_rect.top + 15))
        
        price_bg = price_rect.inflate(10, 6)
        pygame.draw.rect(self.content_surface, (255, 255, 200), price_bg, border_radius=5)
        self.content_surface.blit(price_surf, price_rect)
        
        # Player's item count
        count = self.get_item_count(item)
        count_surf = self.price_font.render(f"Own: {count}", True, (255, 255, 255))
        count_rect = count_surf.get_rect(center=(slot_rect.centerx, slot_rect.bottom - 15))
        
        count_bg = count_rect.inflate(10, 6)
        pygame.draw.rect(self.content_surface, (0, 0, 0), count_bg, border_radius=5)
        self.content_surface.blit(count_surf, count_rect)
        
        # Button
        is_hovering = button_rect.collidepoint(mouse_pos)
        
        if slot['button_type'] == 'buy':
            can_buy = self.can_afford(item)
            button_color = self.button_buy if can_buy else (100, 100, 100)
            button_text = 'BUY'
        else:
            can_sell = count > 0
            button_color = self.button_sell if can_sell else (100, 100, 100)
            button_text = 'SELL'
        
        if is_hovering and ((slot['button_type'] == 'buy' and self.can_afford(item)) or 
                           (slot['button_type'] == 'sell' and count > 0)):
            button_color = self.button_hover
        
        pygame.draw.rect(self.content_surface, button_color, button_rect, border_radius=8)
        pygame.draw.rect(self.content_surface, (255, 255, 255), button_rect, 2, border_radius=8)
        
        text_surf = self.button_font.render(button_text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.content_surface.blit(text_surf, text_rect)
        
        # Check if hovering over slot for tooltip
        if slot_rect.collidepoint(mouse_pos):
            self.hovered_slot = slot
    
    def draw_scrollbar(self):
        """Draw the scrollbar"""
        # Scrollbar track
        track_rect = pygame.Rect(
            self.scrollbar_x, self.scrollbar_y,
            self.scrollbar_width, self.scrollbar_height
        )
        pygame.draw.rect(self.display_surface, (80, 60, 40), track_rect, border_radius=10)
        
        # Scrollbar handle
        if self.max_scroll > 0:
            handle_height = max(30, int(self.scrollbar_height * (self.content_height / self.content_surface.get_height())))
            scroll_percentage = self.scroll_offset / self.max_scroll
            handle_y = self.scrollbar_y + int((self.scrollbar_height - handle_height) * scroll_percentage)
            
            handle_rect = pygame.Rect(
                self.scrollbar_x, handle_y,
                self.scrollbar_width, handle_height
            )
            
            # Highlight if dragging
            handle_color = (255, 215, 0) if self.dragging_scrollbar else (200, 180, 120)
            pygame.draw.rect(self.display_surface, handle_color, handle_rect, border_radius=10)
            pygame.draw.rect(self.display_surface, (255, 255, 255), handle_rect, 2, border_radius=10)
    
    def draw_tooltip(self, slot, mouse_pos):
        """Draw tooltip for hovered item"""
        item = slot['item']
        
        # Create tooltip text
        name = item['name'].replace('_', ' ').title()
        if item['type'] == 'seed':
            desc = f"{name} Seed"
            extra = f"Plant to grow {name.lower()}"
        elif item['type'] == 'crop':
            desc = f"{name}"
            extra = f"Sell for ${item['sell_price']}"
        else:
            desc = f"{name}"
            extra = f"Sell for ${item['sell_price']}"
        
        # Render tooltip
        lines = [desc, extra]
        padding = 10
        line_height = self.tooltip_font.get_linesize()
        
        # Calculate tooltip size
        max_width = max(self.tooltip_font.size(line)[0] for line in lines)
        tooltip_width = max_width + padding * 2
        tooltip_height = len(lines) * line_height + padding * 2
        
        # Position tooltip near mouse
        tooltip_x = mouse_pos[0] + 20
        tooltip_y = mouse_pos[1] + 20
        
        # Keep tooltip on screen
        if tooltip_x + tooltip_width > SCREEN_WIDTH:
            tooltip_x = mouse_pos[0] - tooltip_width - 10
        if tooltip_y + tooltip_height > SCREEN_HEIGHT:
            tooltip_y = mouse_pos[1] - tooltip_height - 10
        
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        # Draw tooltip background
        pygame.draw.rect(self.display_surface, (50, 40, 30), tooltip_rect, border_radius=8)
        pygame.draw.rect(self.display_surface, (255, 215, 0), tooltip_rect, 2, border_radius=8)
        
        # Draw text lines
        y = tooltip_y + padding
        for line in lines:
            text_surf = self.tooltip_font.render(line, True, (255, 255, 255))
            self.display_surface.blit(text_surf, (tooltip_x + padding, y))
            y += line_height