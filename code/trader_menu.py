import pygame
from settings import *
from random import randint

class TraderMenu:
	def __init__(self, player, toggle_menu):
		self.player = player
		self.toggle_menu = toggle_menu
		self.display_surface = pygame.display.get_surface()
		self.font = pygame.font.Font('font/LycheeSoda.ttf', 24)
		self.title_font = pygame.font.Font('font/LycheeSoda.ttf', 36)
		self.small_font = pygame.font.Font('font/LycheeSoda.ttf', 18)
		self.item_icons = {}
		self.load_icons()
		self.hovered_button = None
		self.hovered_item = None
		
		# Menu state
		self.mode = 'main'  # main, buy, sell, appraise
		
		# Trader stock system
		self.stock = {
			'corn': randint(5, 15),
			'tomato': randint(5, 15),
			'moon_melon': randint(3, 10),
			'pumpkin': randint(3, 10),
			'cactus': randint(10, 20)
		}
		
		# Stock refresh timer (5 minutes = 300 seconds)
		self.stock_refresh_interval = 300
		self.stock_timer = 0
		
		# Selection
		self.selected_index = 0

		# Scroll offset for buy/sell menus
		self.scroll_offset = 0
		self.max_visible_rows = 2 # Show 2 rows at a time
		
		# UI dimensions
		self.width = 600
		self.height = 500
		self.x = SCREEN_WIDTH // 2 - self.width // 2
		self.y = SCREEN_HEIGHT // 2 - self.height // 2
	
	def refresh_stock(self):
		"""Refresh trader stock"""
		for seed in self.stock:
			self.stock[seed] = randint(5, 15)
		print("🔄 Trader stock refreshed!")
		
	def load_icons(self):
		"""Load item icons"""
		items_to_load = ['corn', 'tomato', 'moon_melon', 'pumpkin', 'cactus']
		
		for item in items_to_load:
			try:
				# Seed icon (stage 0)
				seed_path = f'graphics/fruit/{item}/0.png'
				seed_icon = pygame.image.load(seed_path).convert_alpha()
				seed_icon = pygame.transform.scale(seed_icon, (50, 50))
				self.item_icons[f'{item}_seed'] = seed_icon
				
				# Crop icon (stage 3)
				crop_path = f'graphics/fruit/{item}/3.png'
				crop_icon = pygame.image.load(crop_path).convert_alpha()
				crop_icon = pygame.transform.scale(crop_icon, (50, 50))
				self.item_icons[f'{item}_crop'] = crop_icon
			except:
				# Fallback placeholder
				placeholder = pygame.Surface((50, 50))
				placeholder.fill((150, 150, 150))
				self.item_icons[f'{item}_seed'] = placeholder
				self.item_icons[f'{item}_crop'] = placeholder

	
	def update(self, dt):
		"""Update stock timer"""
		self.stock_timer += dt
		if self.stock_timer >= self.stock_refresh_interval:
			self.stock_timer = 0
			self.refresh_stock()
	
	def handle_input(self, events):
		"""Handle menu input with mouse and scroll"""
		mouse_pos = pygame.mouse.get_pos()
		
		for event in events:
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					if self.mode == 'main':
						self.toggle_menu()
					else:
						self.mode = 'main'
						self.scroll_offset = 0
			
			# Mouse wheel scrolling
			elif event.type == pygame.MOUSEWHEEL:
				if self.mode in ['buy', 'sell']:
					self.scroll_offset -= event.y
					# Clamp scroll offset
					if self.mode == 'buy':
						max_scroll = max(0, (len(self.stock) - 1) // 5)
					elif self.mode == 'sell':
						sellable = self.get_sellable_crops()
						max_scroll = max(0, (len(sellable) - 1) // 4)
					self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
			
			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				# Check main menu buttons
				if self.mode == 'main':
					if self.hovered_button == 'buy':
						self.mode = 'buy'
						self.scroll_offset = 0
					elif self.hovered_button == 'sell':
						self.mode = 'sell'
						self.scroll_offset = 0
					elif self.hovered_button == 'exit':
						self.toggle_menu()
				
				# Check buy menu items
				elif self.mode == 'buy' and self.hovered_item is not None:
					self.buy_seed(self.hovered_item)
				
				# Check sell menu items
				elif self.mode == 'sell' and self.hovered_item is not None:
					self.sell_crop(self.hovered_item)
				
				# Check back button
				if self.hovered_button == 'back' and self.mode != 'main':
					self.mode = 'main'
					self.scroll_offset = 0

	def buy_seed(self, seed):
		"""Buy a seed"""
		price = PURCHASE_PRICES.get(seed, 10)
		
		if self.stock[seed] > 0 and self.player.money >= price:
			self.player.seed_inventory[seed] += 1
			self.player.money -= price
			self.stock[seed] -= 1
			print(f"✅ Bought {seed} seed for ${price}")
		elif self.stock[seed] <= 0:
			print("❌ Out of stock!")
		else:
			print("❌ Not enough money!")

	def sell_crop(self, crop_key):
		"""Sell a crop and update both inventories"""
		parts = crop_key.split('_')
		crop_type = '_'.join(parts[:-1])
		quality = parts[-1]
		
		if isinstance(SALE_PRICES[crop_type], dict):
			price = SALE_PRICES[crop_type][quality]
		else:
			price = SALE_PRICES[crop_type]
		
		# Update crop_inventory (with quality)
		self.player.crop_inventory[crop_key] -= 1
		if self.player.crop_inventory[crop_key] <= 0:
			del self.player.crop_inventory[crop_key]
		
		# Also update regular item_inventory for backward compatibility
		if crop_type in self.player.item_inventory:
			self.player.item_inventory[crop_type] -= 1
			if self.player.item_inventory[crop_type] < 0:
				self.player.item_inventory[crop_type] = 0
		
		self.player.money += price
		print(f"✅ Sold {crop_type} ({quality}) for ${price}")
	
	def get_sellable_crops(self):
		"""Get list of crops that can be sold"""
		if not hasattr(self.player, 'crop_inventory'):
			return []
		return [key for key, qty in self.player.crop_inventory.items() if qty > 0]
	
	def draw(self):
		"""Draw trader menu"""
		# Semi-transparent overlay
		overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 180))
		self.display_surface.blit(overlay, (0, 0))
		
		# Menu background
		menu_rect = pygame.Rect(self.x, self.y, self.width, self.height)
		pygame.draw.rect(self.display_surface, (40, 30, 20), menu_rect, border_radius=12)
		pygame.draw.rect(self.display_surface, (200, 180, 150), menu_rect, 3, border_radius=12)
		
		if self.mode == 'main':
			self.draw_main_menu()
		elif self.mode == 'buy':
			self.draw_buy_menu()
		elif self.mode == 'sell':
			self.draw_sell_menu()
	
	def draw_main_menu(self):
		"""Draw main trader menu with mouse support"""
		mouse_pos = pygame.mouse.get_pos()
		self.hovered_button = None
		
		# Title
		title = "Trader's Shop"
		title_surf = self.title_font.render(title, True, (255, 230, 200))
		title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 50))
		self.display_surface.blit(title_surf, title_rect)
		
		# Buttons
		buttons = [
			{'text': 'Buy Seeds', 'id': 'buy'},
			{'text': 'Sell Crops', 'id': 'sell'},
			{'text': 'Exit', 'id': 'exit'}
		]
		
		start_y = self.y + 140
		button_width = 300
		button_height = 60
		
		for i, button in enumerate(buttons):
			button_rect = pygame.Rect(
				SCREEN_WIDTH // 2 - button_width // 2,
				start_y + i * 80,
				button_width,
				button_height
			)
			
			is_hovering = button_rect.collidepoint(mouse_pos)
			if is_hovering:
				self.hovered_button = button['id']
			
			# Button background
			button_color = (100, 80, 60) if is_hovering else (60, 45, 30)
			pygame.draw.rect(self.display_surface, button_color, button_rect, border_radius=10)
			pygame.draw.rect(self.display_surface, (200, 180, 150), button_rect, 3, border_radius=10)
			
			# Button text
			text_color = (255, 215, 0) if is_hovering else (255, 255, 255)
			text_surf = self.font.render(button['text'], True, text_color)
			text_rect = text_surf.get_rect(center=button_rect.center)
			self.display_surface.blit(text_surf, text_rect)
		
		# Money display
		money_surf = self.font.render(f"Money: ${self.player.money}", True, (255, 215, 0))
		money_rect = money_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + self.height - 50))
		self.display_surface.blit(money_surf, money_rect)
	
	def draw_buy_menu(self):
		"""Draw seed buying menu with icons"""
		mouse_pos = pygame.mouse.get_pos()	
		self.hovered_item = None
		self.hovered_button = None
		
		# Title
		title = "Buy Seeds"
		title_surf = self.title_font.render(title, True, (255, 230, 200))
		title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 40))
		self.display_surface.blit(title_surf, title_rect)
		
		# Stock timer
		time_left = self.stock_refresh_interval - self.stock_timer
		minutes = int(time_left // 60)
		seconds = int(time_left % 60)
		timer_text = f"Stock refreshes in: {minutes}:{seconds:02d}"
		timer_surf = self.small_font.render(timer_text, True, (180, 180, 180))
		timer_rect = timer_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 75))
		self.display_surface.blit(timer_surf, timer_rect)
		
		# Draw seed items in grid
		seeds = list(self.stock.keys())
		start_x = self.x + 30
		start_y = self.y + 120
		slot_width = 100
		slot_height = 140
		slots_per_row = 5
		
		for i, seed in enumerate(seeds):
			row = i // slots_per_row
			col = i % slots_per_row
			
			x = start_x + col * (slot_width + 10)
			y = start_y + row * (slot_height + 10)
			
			# Slot rect
			slot_rect = pygame.Rect(x, y, slot_width, slot_height)
			is_hovering = slot_rect.collidepoint(mouse_pos)
			
			if is_hovering:
				self.hovered_item = seed
			
			# Slot background
			slot_color = (80, 60, 40) if is_hovering else (60, 45, 30)
			pygame.draw.rect(self.display_surface, slot_color, slot_rect, border_radius=8)
			pygame.draw.rect(self.display_surface, (200, 180, 150), slot_rect, 2, border_radius=8)
			
			# Icon
			icon_key = f'{seed}_seed'
			if icon_key in self.item_icons:
				icon = self.item_icons[icon_key]
				icon_rect = icon.get_rect(center=(x + slot_width // 2, y + 35))
				self.display_surface.blit(icon, icon_rect)
			
			# Seed name
			name = seed.replace('_', ' ').title()
			name_surf = self.small_font.render(name, True, (255, 255, 255))
			name_rect = name_surf.get_rect(center=(x + slot_width // 2, y + 75))
			self.display_surface.blit(name_surf, name_rect)
			
			# Stock
			stock = self.stock[seed]
			stock_color = (100, 200, 100) if stock > 0 else (200, 100, 100)
			stock_surf = self.small_font.render(f"Stock: {stock}", True, stock_color)
			stock_rect = stock_surf.get_rect(center=(x + slot_width // 2, y + 95))
			self.display_surface.blit(stock_surf, stock_rect)
			
			# Price
			price = PURCHASE_PRICES.get(seed, 10)
			price_surf = self.small_font.render(f"${price}", True, (255, 215, 0))
			price_rect = price_surf.get_rect(center=(x + slot_width // 2, y + 115))
			self.display_surface.blit(price_surf, price_rect)
		
		# Back button
		back_rect = pygame.Rect(self.x + 20, self.y + self.height - 60, 100, 40)
		is_back_hover = back_rect.collidepoint(mouse_pos)
		if is_back_hover:
			self.hovered_button = 'back'
		
		back_color = (100, 80, 60) if is_back_hover else (60, 45, 30)
		pygame.draw.rect(self.display_surface, back_color, back_rect, border_radius=8)
		pygame.draw.rect(self.display_surface, (200, 180, 150), back_rect, 2, border_radius=8)
		
		back_text = self.font.render('Back', True, (255, 255, 255))
		back_text_rect = back_text.get_rect(center=back_rect.center)
		self.display_surface.blit(back_text, back_text_rect)
		
		# Money display
		money_surf = self.font.render(f"Money: ${self.player.money}", True, (255, 215, 0))
		money_rect = money_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + self.height - 30))
		self.display_surface.blit(money_surf, money_rect)
	
	def draw_sell_menu(self):
		"""Draw crop selling menu with quality display"""
		mouse_pos = pygame.mouse.get_pos()
		self.hovered_item = None
		self.hovered_button = None
		
		# Title
		title = "Sell Crops"
		title_surf = self.title_font.render(title, True, (255, 230, 200))
		title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 40))
		self.display_surface.blit(title_surf, title_rect)
		
		# Get sellable crops
		sellable = self.get_sellable_crops()
		
		if not sellable:
			no_crops = "No crops to sell!"
			no_crops_surf = self.font.render(no_crops, True, (200, 200, 200))
			no_crops_rect = no_crops_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
			self.display_surface.blit(no_crops_surf, no_crops_rect)
		else:
			# Draw items in grid
			start_x = self.x + 50
			start_y = self.y + 100
			slot_width = 110
			slot_height = 150
			slots_per_row = 4
			
			for i, crop_key in enumerate(sellable):
				row = i // slots_per_row
				col = i % slots_per_row
				
				x = start_x + col * (slot_width + 10)
				y = start_y + row * (slot_height + 10)
				
				# Parse crop
				parts = crop_key.split('_')
				crop_type = '_'.join(parts[:-1])
				quality = parts[-1]
				qty = self.player.crop_inventory[crop_key]
				
				# Get price
				if isinstance(SALE_PRICES[crop_type], dict):
					price = SALE_PRICES[crop_type][quality]
				else:
					price = SALE_PRICES[crop_type]
				
				# Slot rect
				slot_rect = pygame.Rect(x, y, slot_width, slot_height)
				is_hovering = slot_rect.collidepoint(mouse_pos)
				
				if is_hovering:
					self.hovered_item = crop_key
				
				# Slot background
				slot_color = (80, 60, 40) if is_hovering else (60, 45, 30)
				pygame.draw.rect(self.display_surface, slot_color, slot_rect, border_radius=8)
				pygame.draw.rect(self.display_surface, (200, 180, 150), slot_rect, 2, border_radius=8)
				
				# Icon
				icon_key = f'{crop_type}_crop'
				if icon_key in self.item_icons:
					icon = self.item_icons[icon_key]
					icon_rect = icon.get_rect(center=(x + slot_width // 2, y + 35))
					self.display_surface.blit(icon, icon_rect)
				
				# Crop name
				name = crop_type.replace('_', ' ').title()
				name_surf = self.small_font.render(name, True, (255, 255, 255))
				name_rect = name_surf.get_rect(center=(x + slot_width // 2, y + 75))
				self.display_surface.blit(name_surf, name_rect)
				
				# Quality
				quality_colors = {
					'standard': (255, 255, 255),
					'silver': (192, 192, 192),
					'gold': (255, 215, 0),
					'mythical': (138, 43, 226)
				}
				quality_surf = self.small_font.render(quality.upper(), True, quality_colors[quality])
				quality_rect = quality_surf.get_rect(center=(x + slot_width // 2, y + 95))
				self.display_surface.blit(quality_surf, quality_rect)
				
				# Quantity
				qty_surf = self.small_font.render(f"x{qty}", True, (200, 200, 200))
				qty_rect = qty_surf.get_rect(center=(x + slot_width // 2, y + 115))
				self.display_surface.blit(qty_surf, qty_rect)
				
				# Price
				price_surf = self.small_font.render(f"${price}", True, (100, 200, 100))
				price_rect = price_surf.get_rect(center=(x + slot_width // 2, y + 135))
				self.display_surface.blit(price_surf, price_rect)
		
		# Back button
		back_rect = pygame.Rect(self.x + 20, self.y + self.height - 60, 100, 40)
		is_back_hover = back_rect.collidepoint(mouse_pos)
		if is_back_hover:
			self.hovered_button = 'back'
		
		back_color = (100, 80, 60) if is_back_hover else (60, 45, 30)
		pygame.draw.rect(self.display_surface, back_color, back_rect, border_radius=8)
		pygame.draw.rect(self.display_surface, (200, 180, 150), back_rect, 2, border_radius=8)
		
		back_text = self.font.render('Back', True, (255, 255, 255))
		back_text_rect = back_text.get_rect(center=back_rect.center)
		self.display_surface.blit(back_text, back_text_rect)
		
		# Money display
		money_surf = self.font.render(f"Money: ${self.player.money}", True, (255, 215, 0))
		money_rect = money_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + self.height - 30))
		self.display_surface.blit(money_surf, money_rect)