import pygame 
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particle
from pytmx.util_pygame import load_pygame
from support import *
from transition import TransitionStack
from soil import SoilLayer
from sky import Rain, Sky
from random import randint
from menu import Menu
from pause_menu import PauseMenu

class Level:
	def __init__(self):
		pygame.mouse.set_visible(False)
		self.cursor_surf = pygame.image.load('graphics/cursor.png').convert_alpha()
		# get the display surface
		self.display_surface = pygame.display.get_surface()

		# sprite groups
		self.all_sprites = CameraGroup()
		self.collision_sprites = pygame.sprite.Group()
		self.tree_sprites = pygame.sprite.Group()
		self.interaction_sprites = pygame.sprite.Group()

		self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
		self.setup()
		self.overlay = Overlay(self.player, show_objective=True)
		self.transition = TransitionStack(self.reset, self.player)

		# sky
		self.rain = Rain(self.all_sprites)
		self.raining = randint(0,10) > 7
		self.soil_layer.raining = self.raining
		self.sky = Sky()

		# shop
		self.menu = Menu(self.player, self.toggle_shop)
		self.shop_active = False

		# pause
		self.pause = PauseMenu(self.toggle_pause)
		self.pause_active = False

		# music
		self.success = pygame.mixer.Sound('audio/success.wav')
		self.success.set_volume(0.3)
		self.music = pygame.mixer.Sound('audio/music.mp3')
		self.music.play(loops = -1)

	def setup(self):
		tmx_data = load_pygame('data/map.tmx')

		# house 
		for layer in ['HouseFloor', 'HouseFurnitureBottom']:
			for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
				Generic((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, LAYERS['house bottom'])

		for layer in ['HouseWalls', 'HouseFurnitureTop']:
			for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
				Generic((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites)

		# Fence
		for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
			Generic((x * TILE_SIZE,y * TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])

		# water 
		water_frames = import_folder('graphics/water')
		for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
			Water((x * TILE_SIZE,y * TILE_SIZE), water_frames, self.all_sprites)

		# trees 
		for obj in tmx_data.get_layer_by_name('Trees'):
			Tree(
				pos = (obj.x, obj.y), 
				surf = obj.image, 
				groups = [self.all_sprites, self.collision_sprites, self.tree_sprites], 
				name = obj.name,
				player_add = self.player_add)

		# wildflowers 
		for obj in tmx_data.get_layer_by_name('Decoration'):
			WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

		# collion tiles
		for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
			Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)

		# Player 
		for obj in tmx_data.get_layer_by_name('Player'):
			if obj.name == 'Start':
				self.player = Player(
					pos = (obj.x,obj.y), 
					group = self.all_sprites, 
					collision_sprites = self.collision_sprites,
					tree_sprites = self.tree_sprites,
					interaction = self.interaction_sprites,
					soil_layer = self.soil_layer,
					toggle_shop = self.toggle_shop)
			
			if obj.name == 'Bed':
				Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)

			if obj.name == 'Trader':
				Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)


		Generic(
			pos = (0,0),
			surf = pygame.image.load('graphics/world/ground.png').convert_alpha(),
			groups = self.all_sprites,
			z = LAYERS['ground'])

	def player_add(self,item):

		self.player.item_inventory[item] += 1
		self.success.play()

	def toggle_shop(self):

		self.shop_active = not self.shop_active

	def toggle_pause(self):
		# ensure shop is closed while pausing
		if not self.pause_active:
			self.shop_active = False
		self.pause_active = not self.pause_active
		pygame.mouse.set_visible(self.pause_active)

	def reset(self):
		# plants
		self.soil_layer.update_plants()

		# soil
		self.soil_layer.remove_water()
		self.raining = randint(0,10) > 7
		self.soil_layer.raining = self.raining
		if self.raining:
			self.soil_layer.water_all()

		# apples on the trees
		for tree in self.tree_sprites.sprites():
			if hasattr(tree, 'create_fruit'):
				if hasattr(tree, 'apple_sprite'):
					for apple in tree.apple_sprites.sprites():
						apple.kill()
				tree.create_fruit()

		# sky
		self.sky.start_color = [255,255,255]

	def plant_collision(self):
		"""
		Handles player harvesting plants safely.

		- Adds the harvested plant to the player's inventory
		- Removes the plant sprite
		- Cleans the soil grid safely
		- Creates a particle effect
		"""

		if not self.soil_layer.plant_sprites:
			return

		for plant in self.soil_layer.plant_sprites.sprites():
			if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
				
				# 1️⃣ Give player the plant
				self.player_add(plant.plant_type)

				# 2️⃣ Remove the plant sprite
				plant.kill()

				# 3️⃣ Remove 'P' from the soil grid safely
				cell_y = plant.rect.centery // TILE_SIZE
				cell_x = plant.rect.centerx // TILE_SIZE

				# Ensure coordinates are in bounds
				if 0 <= cell_y < len(self.soil_layer.grid) and 0 <= cell_x < len(self.soil_layer.grid[0]):
					cell = self.soil_layer.grid[cell_y][cell_x]

					# Remove all 'P' in case multiple entries exist
					while 'P' in cell:
						cell.remove('P')

				# 4️⃣ Spawn particle effect
				Particle(plant.rect.topleft, plant.image, self.all_sprites, z=LAYERS['main'])


	def run(self, dt, events):
		# handle events and consume ESC that opens the pause menu so it doesn't immediately close
		filtered_events = []
		for event in events:
			# if ESC pressed and pause isn't active yet, open pause and don't forward this event
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.pause_active:
				self.toggle_pause()
				continue
			filtered_events.append(event)

		# drawing logic
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player)
		
		# Update player's knowledge about camera offset to make spatial mouse control possible
		self.player.offset = self.all_sprites.offset
		
		# updates
		if self.pause_active:
			# let the pause menu handle its events and drawing (use filtered events)
			self.pause.update(filtered_events)
		elif self.shop_active:
			self.menu.update()
		else:
			self.all_sprites.update(dt)
			self.plant_collision()

		# weather
		self.overlay.display(dt)
		if self.raining and not (self.shop_active or self.pause_active):
			self.rain.update()
		self.sky.display(dt)

		# transition overlay
		if self.player.sleep:
			if not self.transition.stack:
				self.transition.add_transition()
			self.transition.play()

		# draw either custom cursor or let system cursor show while paused
		self.draw_cursor()

		# draw pause menu on top
		if self.pause_active:
			self.pause.draw()
	def draw_selection_box(self):
		mouse_pos = pygame.mouse.get_pos() + self.all_sprites.offset
		# adding snap logic
		x = (mouse_pos.x // 64)	* 64
		y = (mouse_pos.y // 64) * 64

		# distance check for color
		player_center = pygame.math.Vector2(self.player.rect.center)
		tile_center = pygame.math.Vector2(x + 32, y +32)

		# PLAYER_REACH_LIMIT 
		if player_center.distance_to(tile_center) < PLAYER_REACH_LIMIT:
			rect_color = 'white'
		else:
			rect_color = 'red'
		rect = pygame.Rect(x - self.all_sprites.offset.x, y - self.all_sprites.offset.y, 64, 64)
		pygame.draw.rect(self.display_surface, rect_color, rect, 3, 2)

	def draw_cursor(self):
		# only draw custom cursor when OS cursor is hidden (e.g., not paused)
		if not pygame.mouse.get_visible():
			mouse_pos = pygame.mouse.get_pos()
			cursor_rect = self.cursor_surf.get_rect(center = mouse_pos)
			self.display_surface.blit(self.cursor_surf, cursor_rect)
class CameraGroup(pygame.sprite.Group):
	def __init__(self):
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.offset = pygame.math.Vector2()

	def custom_draw(self, player):
		self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
		self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

		for layer in LAYERS.values():
			for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
				if sprite.z == layer:
					offset_rect = sprite.rect.copy()
					offset_rect.center -= self.offset
					self.display_surface.blit(sprite.image, offset_rect)

					# # anaytics
					# if sprite == player:
					# 	pygame.draw.rect(self.display_surface,'red',offset_rect,5)
					# 	hitbox_rect = player.hitbox.copy()
					# 	hitbox_rect.center = offset_rect.center
					# 	pygame.draw.rect(self.display_surface,'green',hitbox_rect,5)
					# 	target_pos = offset_rect.center + PLAYER_TOOL_OFFSET[player.status.split('_')[0]]
					# 	pygame.draw.circle(self.display_surface,'blue',target_pos,5)

			

