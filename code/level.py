from operator import pos
import pygame, math
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
from trader_menu import TraderMenu
from pause_menu import PauseMenu
from quest_system import QuestManager
from inventory_ui import InventoryUI
from time_system import TimeSystem
from energy_system import EnergySystem
from corruption_surge import CorruptionSurge
from corruption_spread import CorruptionSpread, HealthSystem
from ward_system import WardSystem
from stage_cutscene import StageCutscene
from save_load_menu import SaveLoadMenu
from dog_npc import DogNPC

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
		
		# Track which stage we're in for special handling
		self.current_map_path = None

		# Farm cleansing system
		self.cleanse_stage = 'corrupted'  # corrupted, stage1, stage2, stage3, cleansed
		self.cleanse_points = 0
		self.points_needed = {
			'corrupted': 100,  # points to reach stage1
			'stage1': 200,     # points to reach stage2
			'stage2': 300,     # points to reach stage3
			'stage3': 400      # points to reach cleansed
		}

		# Initialize player as None first
		self.player = None
		# Stage cutscene system
		self.stage_cutscene = None
		self.pending_cutscene_stage = None
		self.has_shown_intro = False
		self.soil_layer = None

		# Energy system
		self.energy_system = EnergySystem()	

		# Health system (with death callback)
		self.health_system = HealthSystem(on_death=self.on_player_death)

		# Corruption spread system (initialize AFTER sprite groups)
		try:
			self.corruption_spread = CorruptionSpread(self.all_sprites, self.collision_sprites)
			print("✓ Corruption spread system initialized")
		except Exception as e:
			print(f"✗ Failed to initialize corruption spread: {e}")
			import traceback
			traceback.print_exc()
			self.corruption_spread = None

		# Ward system
		self.ward_system = WardSystem(self.all_sprites)
		self.ward_system.corruption_spread_ref = self.corruption_spread  # ADD THIS LINE

		# save load
		self.save_load_menu = SaveLoadMenu(self, self.toggle_save_load_menu)
		self.save_load_active = False

		self.dog = None
		self.dog_spawned = False

		self.setup()

		# Create soil layer AFTER setup
		if self.current_map_path:
			print(f"\n=== Creating Soil Layer ===")
			print(f"Using map path: {self.current_map_path}")
			self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites, self.current_map_path)
			if self.player:
				self.player.soil_layer = self.soil_layer
		else:
			# Fallback
			self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites, 'data/map.tmx')
			if self.player:
				self.player.soil_layer = self.soil_layer

		# Corruption surge system
		self.corruption_surge = CorruptionSurge(self.soil_layer)

		self.overlay = Overlay(self.player, show_objective=True)
		self.transition = TransitionStack(self.reset, self.player)
		# Quest system
		self.quest_manager = QuestManager(self.player)
		
		

		# sky
		self.rain = Rain(self.all_sprites)
		self.raining = randint(0,10) > 0
		self.soil_layer.raining = self.raining
		self.sky = Sky()

		# shop
		self.trader_menu = TraderMenu(self.player, self.toggle_shop)
		self.shop_active = False

		# pause
		self.pause = PauseMenu(self.toggle_pause, self.toggle_save_load_menu)
		self.pause_active = False

		# music
		self.success = pygame.mixer.Sound('audio/success.wav')
		self.success.set_volume(0.3)

		# Inventory UI
		self.inventory_ui = InventoryUI(self.player)
		self.inventory_active = False

		# Time system
		self.time_system = TimeSystem()

	def quick_save(self):
		from save_load import SaveLoadSystem
		save_system = SaveLoadSystem()
		save_system.save_game(self, "autosave")
		print ("💾 Quick saved!")
	
	def quick_load(self):
		from save_load import SaveLoadSystem
		save_system = SaveLoadSystem()
		if save_system.load_game(self, "autosave"):
			print ("📂 Quick loaded!")

	def toggle_save_load_menu(self):
		self.save_load_active = not self.save_load_active
		pygame.mouse.set_visible(self.save_load_active)


	def on_player_death(self):
		"""Called when player dies"""
		self.show_death_screen()
		self.restart_same_day()

	def show_death_screen(self):
		"""Display 'You Died' screen"""
		fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
		fade_surface.fill((0, 0, 0))
		
		# Fade to black
		for alpha in range(0, 255, 15):
			pygame.event.clear()
			fade_surface.set_alpha(alpha)
			self.display_surface.blit(fade_surface, (0, 0))
			pygame.display.update()
			pygame.time.delay(30)
		
		# Show "You Died" text
		start_time = pygame.time.get_ticks()
		duration = 3000  # 3 seconds
		
		while pygame.time.get_ticks() - start_time < duration:
			pygame.event.clear()
			self.display_surface.fill((0, 0, 0))
			
			try:
				font = pygame.font.Font('font/LycheeSoda.ttf', 72)
			except:
				font = pygame.font.Font(None, 72)
			
			text = "You Died"
			text_surf = font.render(text, True, (255, 50, 50))
			text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
			
			self.display_surface.blit(text_surf, text_rect)
			pygame.display.update()
			pygame.time.delay(30)
		
		# Fade back in
		for alpha in range(255, 0, -15):
			pygame.event.clear()
			fade_surface.set_alpha(alpha)
			self.display_surface.fill('black')
			self.all_sprites.custom_draw(self.player)
			self.display_surface.blit(fade_surface, (0, 0))
			pygame.display.update()
			pygame.time.delay(30)
		
		pygame.event.clear()

	def restart_same_day(self):
		"""Restart current day without advancing time"""
		# Reset plants
		self.soil_layer.update_plants()
		
		# Restore energy
		self.energy_system.restore_full()
		
		# Restore health
		self.health_system.restore_full()
		
		# Reset corruption surge
		self.corruption_surge.reset_daily()
		
		# Remove water
		self.soil_layer.remove_water()
		
		# Respawn apples
		for tree in self.tree_sprites.sprites():
			if hasattr(tree, 'create_fruit'):
				if hasattr(tree, 'apple_sprite'):
					for apple in tree.apple_sprites.sprites():
						apple.kill()
				tree.create_fruit()
		
		# Reset sky
		self.sky.start_color = [255, 255, 255]
		
		# DON'T advance day - keep same day

	def setup(self):
		"""Load ALL layers from the current stage map"""
		# Map file paths for each stage
		map_files = {
			'corrupted': 'data/corrupted farm.tmx',
			'stage1': 'data/stage 1.tmx',
			'stage2': 'data/stage 2.tmx',
			'stage3': 'data/stage 3.tmx',
			'cleansed': 'data/map.tmx'
		}

		# Try to load the stage-specific map
		map_path = map_files.get(self.cleanse_stage, 'data/map.tmx')
		self.current_map_path = map_path
		
		try:
			tmx_data = load_pygame(map_path)
		except Exception as e:
			map_path = 'data/map.tmx'
			self.current_map_path = map_path
			tmx_data = load_pygame(map_path)

		# Clear ALL existing sprites
		self.clear_all_sprites()
		
		# Process ALL layers in the correct order
		self.process_all_layers_in_order(tmx_data)
		
		# Setup player and interactions
		self.setup_player_and_interactions(tmx_data)

	def clear_all_sprites(self):
		"""Clear all sprite groups"""
		# Store player reference if it exists
		player_temp = getattr(self, 'player', None)
		
		# Clear all sprite groups except player
		for sprite in list(self.all_sprites.sprites()):
			if sprite != player_temp:
				sprite.kill()
		
		for sprite in list(self.collision_sprites.sprites()):
			if sprite != player_temp:
				sprite.kill()
		
		for sprite in list(self.tree_sprites.sprites()):
			sprite.kill()
		
		for sprite in list(self.interaction_sprites.sprites()):
			sprite.kill()

	def process_all_layers_in_order(self, tmx_data):
		"""Process ALL layers in the order they appear in Tiled"""
		all_layers = list(tmx_data.visible_layers)
		
		for i, layer in enumerate(all_layers):
			layer_name = layer.name
			layer_type = type(layer).__name__
			
			# Handle tile layers - check for tiles() method
			if hasattr(layer, 'tiles') and callable(layer.tiles):
				self.process_tile_layer_by_name(layer_name, layer, tmx_data)
			
			# Handle object layers - check layer type
			elif 'TiledObjectGroup' in layer_type or 'ObjectLayer' in layer_type:
				self.process_object_layer_by_name(layer_name, layer, tmx_data)
			
			# Fallback: try to iterate as object layer
			elif hasattr(layer, '__iter__'):
				try:
					items = list(layer)
					if items:
						self.process_object_layer_by_name(layer_name, layer, tmx_data)
				except:
					pass

	def process_tile_layer_by_name(self, layer_name, layer, tmx_data):
		"""Process a specific tile layer based on its name"""
		layer_name_lower = layer_name.lower()
		
		# Count tiles in layer
		tile_count = 0
		for x, y, surf in layer.tiles():
			if surf:
				tile_count += 1
		
		# Define comprehensive layer processing rules
		layer_rules = {
			# Water layers (bottom-most)
			'water': {'z': LAYERS['water'], 'groups': [self.all_sprites], 'special': 'water'},
			'corrupted water': {'z': LAYERS['water'], 'groups': [self.all_sprites], 'special': 'water'},
			
			# Ground and terrain layers
			'ground': {'z': LAYERS['ground'], 'groups': [self.all_sprites], 'collision': False},
			'grass': {'z': LAYERS['ground'] + 0.2, 'groups': [self.all_sprites], 'collision': False},
			'forest grass': {'z': LAYERS['ground'] + 0.3, 'groups': [self.all_sprites], 'collision': False},
			'path': {'z': LAYERS['ground'] + 0.4, 'groups': [self.all_sprites], 'collision': False},
			'hills': {'z': LAYERS['ground'] + 0.5, 'groups': [self.all_sprites], 'collision': False},
			
			# Details layer
			'details': {'z': LAYERS['ground'] + 0.6, 'groups': [self.all_sprites], 'collision': False},
			
			# Decorations
			'decorations': {'z': LAYERS['main'] - 0.5, 'groups': [self.all_sprites], 'collision': False},
			'decoration': {'z': LAYERS['main'] - 0.5, 'groups': [self.all_sprites], 'collision': False},
			'outside decoration': {'z': LAYERS['main'] - 0.5, 'groups': [self.all_sprites], 'collision': False},
			
			# House layers
			'housefloor': {'z': LAYERS['house bottom'], 'groups': [self.all_sprites], 'collision': False},
			'housefurniturebottom': {'z': LAYERS['house bottom'], 'groups': [self.all_sprites], 'collision': False},
			'housewalls': {'z': LAYERS['main'], 'groups': [self.all_sprites, self.collision_sprites], 'collision': True},
			'housefurnituretop': {'z': LAYERS['main'], 'groups': [self.all_sprites], 'collision': False},
			
			# Fences and obstacles
			'fence': {'z': LAYERS['main'], 'groups': [self.all_sprites, self.collision_sprites], 'collision': True},
			
			# Farmable layer
			'farmable': {'z': LAYERS['ground'] + 0.05, 'groups': [self.all_sprites], 'collision': False, 'special': 'farmable'},
			
			# Collision layer
			'collision': {'z': LAYERS['main'], 'groups': [self.collision_sprites], 'collision': True, 'invisible': True},
			
			# Corruption-specific layers
			'corrupted objects': {'z': LAYERS['main'], 'groups': [self.all_sprites], 'collision': False},
			'corrupted rock': {'z': LAYERS['main'], 'groups': [self.all_sprites], 'collision': False},
			'corrupted tree1': {'z': LAYERS['main'] + 1, 'groups': [self.all_sprites], 'special': 'corrupted_tree'},
			'corrupted tree2': {'z': LAYERS['main'] + 1, 'groups': [self.all_sprites], 'special': 'corrupted_tree'},
			'corrupted tree3': {'z': LAYERS['main'] + 1, 'groups': [self.all_sprites], 'special': 'corrupted_tree'},
		}
		
		# Find matching rule (check for partial matches)
		rule = None
		matched_key = None
		for rule_name, rule_data in layer_rules.items():
			if rule_name in layer_name_lower:
				rule = rule_data
				matched_key = rule_name
				break
		
		# Default rule if no match
		if not rule:
			if 'collision' in layer_name_lower:
				rule = {'z': LAYERS['main'], 'groups': [self.collision_sprites], 'collision': True, 'invisible': True}
			elif 'house' in layer_name_lower:
				rule = {'z': LAYERS['main'], 'groups': [self.all_sprites], 'collision': False}
			elif 'tree' in layer_name_lower:
				rule = {'z': LAYERS['main'] + 1, 'groups': [self.all_sprites, self.collision_sprites], 'collision': True}
			else:
				rule = {'z': LAYERS['main'], 'groups': [self.all_sprites], 'collision': False}
		
		# Process tiles in this layer
		tiles_created = 0
		tiles_skipped_no_surf = 0
		farmable_tiles_registered = 0
		
		for x, y, surf in layer.tiles():
			if not surf:
				tiles_skipped_no_surf += 1
				continue
				
			pos = (x * TILE_SIZE, y * TILE_SIZE)
			
			# Handle special cases
			if 'special' in rule:
				if rule['special'] == 'farmable':
					# Register with soil layer
					if hasattr(self, 'soil_layer') and self.soil_layer:
						if y < len(self.soil_layer.grid) and x < len(self.soil_layer.grid[0]):
							if 'F' not in self.soil_layer.grid[y][x]:
								self.soil_layer.grid[y][x].append('F')
								farmable_tiles_registered += 1
					
					# Create visual sprite
					if self.cleanse_stage == 'corrupted':
						Generic(pos, surf, rule['groups'], rule['z'])
					else:
						invisible_surf = surf.copy()
						invisible_surf.set_alpha(0)
						Generic(pos, invisible_surf, rule['groups'], rule['z'])
					
					tiles_created += 1
					continue
				
				elif rule['special'] == 'water':
					try:
						if 'corrupted' in layer_name_lower:
							try:
								water_frames = import_folder('graphics/corrupted_water')
							except:
								water_frames = import_folder('graphics/water')
						else:
							water_frames = import_folder('graphics/water')
						
						if water_frames and len(water_frames) > 0:
							Water(pos, water_frames, rule['groups'])
							tiles_created += 1
						else:
							if surf:
								Generic(pos, surf, rule['groups'], rule['z'])
								tiles_created += 1
					except Exception as e:
						pass
					continue
					
				elif rule['special'] == 'corrupted_tree':
					Generic(pos, surf, rule['groups'], rule['z'])
					tiles_created += 1
					continue
			
			# Handle invisible collision tiles
			if rule.get('invisible', False):
				if surf:
					invisible_surf = surf.copy()
					invisible_surf.set_alpha(0)
					Generic(pos, invisible_surf, rule['groups'], rule['z'])
					tiles_created += 1
				else:
					collision_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
					collision_surf.set_alpha(0)
					Generic(pos, collision_surf, rule['groups'], rule['z'])
					tiles_created += 1
				continue
			
			# Create the generic sprite
			try:
				Generic(pos, surf, rule['groups'], rule['z'])
				tiles_created += 1
			except Exception as e:
				pass

	def process_object_layer_by_name(self, layer_name, layer, tmx_data):
		"""Process a specific object layer based on its name"""
		layer_name_lower = layer_name.lower()
		
		objects_list = list(layer)
		
		for obj in objects_list:
			pos = (obj.x, obj.y)
			obj_name = getattr(obj, 'name', None)
			has_image = hasattr(obj, 'image') and obj.image is not None
			
			# If object has no name but has an image, render it as a generic sprite
			if (not obj_name or obj_name == 'None') and has_image:
				Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
				continue
			
			# NOW check for named objects
			if hasattr(obj, 'name') and obj_name:
				if obj_name == 'Trader':
					if hasattr(obj, 'image') and obj.image:
						Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
					
					Interaction(
						pos=pos,
						size=(obj.width, obj.height),
						groups=[self.interaction_sprites],
						name='Trader'
					)
				elif obj_name == 'Tree':
					if hasattr(obj, 'image') and obj.image:
						Tree(
							pos=pos,
							surf=obj.image,
							groups=[self.all_sprites, self.collision_sprites, self.tree_sprites],
							name=obj.name if hasattr(obj, 'name') else 'Tree',
							player_add=self.player_add
						)
				elif obj_name == 'WildFlower':
					if hasattr(obj, 'image') and obj.image:
						WildFlower(pos, obj.image, [self.all_sprites, self.collision_sprites])

			# Collision layer
			if 'collision' in layer_name_lower:
				if hasattr(obj, 'width') and hasattr(obj, 'height'):
					collision_surf = pygame.Surface((obj.width, obj.height))
					collision_surf.set_alpha(0)
					Generic(pos, collision_surf, [self.collision_sprites], LAYERS['main'])
			
			# Player layer - handled separately in setup_player
			elif 'player' in layer_name_lower:
				pass
			
			# Objects layer
			elif 'objects' in layer_name_lower:
				if hasattr(obj, 'image') and obj.image:
					Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
			
			# Trader layer
			elif 'trader' in layer_name_lower:
				if hasattr(obj, 'name') and obj.name == 'Trader':
					if hasattr(obj, 'image') and obj.image:
						Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
					
					Interaction(
						pos=pos,
						size=(obj.width, obj.height),
						groups=[self.interaction_sprites],
						name='Trader'
					)
			
			# Tree layers (non-corrupted)
			elif 'tree' in layer_name_lower and 'corrupted' not in layer_name_lower:
				if hasattr(obj, 'image') and obj.image:
					Tree(
						pos=pos,
						surf=obj.image,
						groups=[self.all_sprites, self.collision_sprites, self.tree_sprites],
						name=obj.name if hasattr(obj, 'name') else 'Tree',
						player_add=self.player_add
					)
			
			# Decoration/Flower layers
			elif any(keyword in layer_name_lower for keyword in ['decoration', 'flower', 'rock', 'bush']):
				if hasattr(obj, 'image') and obj.image:
					WildFlower(pos, obj.image, [self.all_sprites, self.collision_sprites])
			
			# Default object handling
			else:
				if hasattr(obj, 'image') and obj.image:
					has_collision = False
					if hasattr(obj, 'properties') and obj.properties:
						has_collision = obj.properties.get('collision', False)
					
					groups = [self.all_sprites]
					if has_collision:
						groups.append(self.collision_sprites)
					
					Generic(pos, obj.image, groups, LAYERS['main'])

	def setup_player_and_interactions(self, tmx_data):
		"""Setup player, bed, and other interactions from object layers"""
		player_exists = hasattr(self, 'player') and self.player is not None
		
		# Look for Player layer
		player_layer_found = False
		for layer in tmx_data.visible_layers:
			layer_name = getattr(layer, 'name', 'unnamed')
			layer_type = type(layer).__name__
			is_object_layer = 'TiledObjectGroup' in layer_type or 'ObjectLayer' in layer_type or (hasattr(layer, '__iter__') and not hasattr(layer, 'tiles'))
			
			if is_object_layer and 'player' in layer_name.lower():
				player_layer_found = True
				objects_in_layer = list(layer)
				
				for obj in objects_in_layer:
					obj_name = getattr(obj, 'name', 'unnamed')
					
					if hasattr(obj, 'name'):
						# Player start position
						if obj.name == 'Start':
							if hasattr(obj, 'width') and hasattr(obj, 'height') and obj.width > 0 and obj.height > 0:
								start_pos = (obj.x + obj.width // 2, obj.y + obj.height // 2)
							else:
								start_pos = (obj.x, obj.y)
							
							if not player_exists:
								self.player = Player(
									pos=start_pos,
									group=self.all_sprites,
									collision_sprites=self.collision_sprites,
									tree_sprites=self.tree_sprites,
									interaction=self.interaction_sprites,
									soil_layer=self.soil_layer,
									toggle_shop=self.toggle_shop
								)
								self.player.energy_system = self.energy_system	
								# Set health system reference
								self.player.health_system = self.health_system
								self.player.ward_system = self.ward_system
							else:
								self.player.pos = pygame.math.Vector2(start_pos)
								self.player.rect.center = start_pos
								self.player.hitbox.center = self.player.rect.center
						
						# Bed interaction
						elif obj.name == 'Bed':
							if hasattr(obj, 'image') and obj.image:
								Generic(pos, obj.image, [self.all_sprites], LAYERS['house bottom'])
							
							Interaction(
								pos=(obj.x, obj.y),
								size=(obj.width, obj.height),
								groups=[self.interaction_sprites],
								name='Bed'
							)
						
						# Trader interaction
						elif obj.name == 'Trader':
							trader_exists = False
							for sprite in self.interaction_sprites:
								if hasattr(sprite, 'name') and sprite.name == 'Trader':
									trader_exists = True
									break
							
							if not trader_exists:
								if hasattr(obj, 'image') and obj.image:
									Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
								
								Interaction(
									pos=(obj.x, obj.y),
									size=(obj.width, obj.height),
									groups=[self.interaction_sprites],
									name='Trader'
								)

		# Ensure player exists
		if not player_exists and self.player is None:
			self.player = Player(
				pos=(640, 360),
				group=self.all_sprites,
				collision_sprites=self.collision_sprites,
				tree_sprites=self.tree_sprites,
				interaction=self.interaction_sprites,
				soil_layer=self.soil_layer,
				toggle_shop=self.toggle_shop
			)
		
		# Update player's soil layer reference
		if self.soil_layer and self.player:
			self.player.soil_layer = self.soil_layer
		
		# Update overlay with player reference
		if hasattr(self, 'overlay'):
			self.overlay.player = self.player

	def add_cleanse_points(self, points):
		"""Add cleanse points and check for stage progression"""
		self.cleanse_points += points
		
		# Check if we should progress to next stage
		current_threshold = self.points_needed.get(self.cleanse_stage, float('inf'))
		
		if self.cleanse_points >= current_threshold:
			self.progress_stage()

	def progress_stage(self):
		"""Progress to the next cleansing stage with transition"""
		stage_order = ['corrupted', 'stage1', 'stage2', 'stage3', 'cleansed']
		current_index = stage_order.index(self.cleanse_stage)
		
		if current_index < len(stage_order) - 1:
			# Freeze player during transition
			player_was_sleeping = self.player.sleep
			self.player.sleep = True
			
			# Reset cleanse points
			self.cleanse_points = 0
			
			# Save player position
			saved_player_pos = self.player.rect.center
			
			# Change stage
			self.cleanse_stage = stage_order[current_index + 1]
			
			# Save soil state and plant data BEFORE transition
			saved_grid = [row[:] for row in self.soil_layer.grid]
			saved_plants = []

			for plant in self.soil_layer.plant_sprites.sprites():
				plant_data = {
					'plant_type': plant.plant_type,
					'age': plant.age,
					'pos': (plant.rect.x // TILE_SIZE, plant.rect.y // TILE_SIZE),
					'current_grow_time': plant.current_grow_time,
					'harvestable': plant.harvestable,
					'quality': getattr(plant, 'quality', 'standard')
				}
				saved_plants.append(plant_data)

			# RELOAD THE MAP for the new stage (sprites load in background)
			self.setup()

			# Create new soil layer for new stage
			if self.current_map_path:
				self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites, self.current_map_path)
				if self.player:
					self.player.soil_layer = self.soil_layer

			# RESTORE plants after setup
			if self.soil_layer and saved_plants:
				self.soil_layer.restore_plants(saved_plants, saved_grid)

			# Apply cleansed stage effects if reached
			self.apply_cleansed_stage_effects()

			# Unfreeze player
			self.player.sleep = player_was_sleeping
			
			# Set pending cutscene for this stage
			self.pending_cutscene_stage = self.cleanse_stage

	def set_stage_dialogue(self, stage):
		"""Set dialogue for stage transition"""
		dialogues = {
			'stage1': [
				"The land notices your effort.",
				"The earth stirs.",
				"It has not been cared for in a long time."
			],
			'stage2': [
				"The land remembers what it once was.",
				"This place once fed many.",
				"It remembers gentle hands."
			],
			'stage3': [
				"The corruption weakens.",
				"Life returns to the soil.",
				"Hope blooms again."
			],
			'cleansed': [
				"The land forgives.",
				"The land breathes freely.",
				"And this time, it is not alone."
			]
		}
		
		if stage in dialogues:
			self.pending_dialogue = dialogues[stage]

	def apply_cleansed_stage_effects(self):
		"""Apply special effects when reaching cleansed stage"""
		if self.cleanse_stage == 'cleansed':
			# Place permanent ward in center of map
			center_x = self.corruption_spread.map_width // 2
			center_y = self.corruption_spread.map_height // 2
			
			# Create mega ward with map-wide radius
			map_radius = max(self.corruption_spread.map_width, self.corruption_spread.map_height)
			self.ward_system.place_mega_ward(center_x, center_y, map_radius)
			
			# Disable corruption spread notifications
			self.corruption_spread.notifications_enabled = False

	def create_soil_grid(self, map_path=None):
		"""Create soil grid from the Farmable layer in the specified map"""
		if map_path is None:
			map_path = 'data/map.tmx'
		
		try:
			tmx_data = load_pygame(map_path)
			
			# Get map dimensions
			ground = pygame.image.load('graphics/world/ground.png')
			h_tiles = ground.get_width() // TILE_SIZE
			v_tiles = ground.get_height() // TILE_SIZE
			
			# Initialize empty grid
			self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
			
			# Look for Farmable layer
			farmable_layer = None
			for layer in tmx_data.visible_layers:
				if hasattr(layer, 'name'):
					if layer.name.lower() == 'farmable':
						farmable_layer = layer
						break
			
			if farmable_layer is None:
				return
			
			# Mark farmable tiles
			farmable_count = 0
			if hasattr(farmable_layer, 'tiles'):
				for x, y, surf in farmable_layer.tiles():
					if surf and 0 <= y < v_tiles and 0 <= x < h_tiles:
						self.grid[y][x].append('F')
						farmable_count += 1
			else:
				for obj in farmable_layer:
					x = int(obj.x // TILE_SIZE)
					y = int(obj.y // TILE_SIZE)
					if 0 <= y < v_tiles and 0 <= x < h_tiles:
						self.grid[y][x].append('F')
						farmable_count += 1
			
		except Exception as e:
			# Create empty grid as fallback
			ground = pygame.image.load('graphics/world/ground.png')
			h_tiles = ground.get_width() // TILE_SIZE
			v_tiles = ground.get_height() // TILE_SIZE
			self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]

	def play_stage_transition(self):
		"""Play a visual transition when stage changes"""
		# Create a simple fade effect
		fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
		fade_surface.fill((0, 0, 0))
		
		# Fade out
		for alpha in range(0, 255, 15):
			# Clear any pending events to prevent player input
			pygame.event.clear()
			
			fade_surface.set_alpha(alpha)
			self.display_surface.blit(fade_surface, (0, 0))
			pygame.display.update()
			pygame.time.delay(30)
		
		# Hold black screen with "Cleansing the Farm" text
		start_time = pygame.time.get_ticks()
		duration = 2500  # 2.5 seconds
		
		while pygame.time.get_ticks() - start_time < duration:
			# Clear any pending events
			pygame.event.clear()
			
			# Draw black screen with text
			self.display_surface.fill((0, 0, 0))
			
			try:
				font = pygame.font.Font('font/LycheeSoda.ttf', 48)
			except:
				font = pygame.font.Font(None, 48)
			
			text = "Cleansing the Farm..."
			text_surf = font.render(text, True, (255, 255, 255))
			text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
			
			self.display_surface.blit(text_surf, text_rect)
			pygame.display.update()
			pygame.time.delay(30)
		
		# Fade in
		for alpha in range(255, 0, -15):
			# Clear any pending events
			pygame.event.clear()
			
			fade_surface.set_alpha(alpha)
			# Redraw game during fade in
			self.display_surface.fill('black')
			self.all_sprites.custom_draw(self.player)
			self.display_cleanse_progress()
			self.display_surface.blit(fade_surface, (0, 0))
			pygame.display.update()
			pygame.time.delay(30)

		# One final clear of events before returning control
		pygame.event.clear()

	def player_add(self,item):
		if hasattr(self, 'player'):
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
		# Advance to next day
		self.time_system.advance_to_next_day()
		
		# plants (grows on real time now)
		#self.soil_layer.update_plants(0)

		# Restore energy
		self.energy_system.restore_full()

		# Reset corruption surge for new day
		self.corruption_surge.reset_daily()

		# Restore health
		self.health_system.restore_full()
		
		# Punish day sleep ONLY if sleeping during day (between 6 AM and 11 PM)
		# Player should sleep at night (after 11 PM or before 6 AM) to avoid penalty
		if 6 <= self.time_system.hour < 23:
			self.corruption_spread.punish_day_sleep()

		# soil
		self.soil_layer.remove_water()
		self.raining = randint(0,10) > 0
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
		"""Handles player harvesting plants with quality"""
		if not self.soil_layer.plant_sprites:
			return

		for plant in self.soil_layer.plant_sprites.sprites():
			# Check both rect and hitbox for collision
			collision = plant.rect.colliderect(self.player.hitbox)
			if hasattr(plant, 'hitbox'):
				collision = collision or plant.hitbox.colliderect(self.player.hitbox)
			
			if plant.harvestable and collision:
				
				# Store crop with quality
				crop_key = f"{plant.plant_type}_{plant.quality}"
				
				# Add to inventory (we'll need a new inventory structure)
				if not hasattr(self.player, 'crop_inventory'):
					self.player.crop_inventory = {}
				
				if crop_key not in self.player.crop_inventory:
					self.player.crop_inventory[crop_key] = 0
				
				self.player.crop_inventory[crop_key] += 1
				
				# Also add to regular inventory for backwards compatibility
				self.player_add(plant.plant_type)

				# Show quality notification
				quality_text = {
					'standard': '',
					'silver': '✨ Silver!',
					'gold': '⭐ Gold!',
					'mythical': '💎 MYTHICAL!'
				}

				# Update quest progress
				self.quest_manager.on_harvest(plant.plant_type)

				# Add cleanse points
				cleanse_values = {
					'corn': 100,
					'tomato': 100,
					'moon_melon': 100,
					'pumpkin': 100,
					'cactus': 100
				}
				points = cleanse_values.get(plant.plant_type, 5)
				self.add_cleanse_points(points)

				# Remove the plant
				plant.kill()

				# Remove 'P' from grid (use soil position, not plant position)
				cell_x = plant.soil.rect.x // TILE_SIZE
				cell_y = plant.soil.rect.y // TILE_SIZE

				if 0 <= cell_y < len(self.soil_layer.grid) and 0 <= cell_x < len(self.soil_layer.grid[0]):
					cell = self.soil_layer.grid[cell_y][cell_x]
					while 'P' in cell:
						cell.remove('P')

				# Spawn particle effect
				Particle(plant.rect.topleft, plant.image, self.all_sprites, z=LAYERS['main'])

	def run(self, dt, events):
    # Spawn dog once on day 1
		if not self.dog_spawned and self.time_system.day >= 1:
			spawn_pos = (self.player.rect.centerx + 100, self.player.rect.centery)    
			self.dog = DogNPC(
				pos=spawn_pos,
				groups=[],
				collision_sprites=self.collision_sprites,        
				corruption_system=self.corruption_spread
			)
			
			# Connect dog to corruption system
			self.corruption_spread.dog_npc = self.dog
			
			# Set flag to prevent re-spawning
			self.dog_spawned = True
			
			print("🐕 Dog has appeared!")
    

		

		# handle events and consume ESC that opens the pause menu so it doesn't immediately close
		filtered_events = []
		for event in events:

			self.corruption_surge.handle_report_input(filtered_events)

			# Check for inventory toggle
			if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
				self.inventory_active = not self.inventory_active
				continue

			# Check for quest toggle
			if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
				self.quest_manager.toggle_quest_ui()
				continue
			
			# if ESC pressed
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				if self.inventory_active:
					# Close inventory if it's open
					self.inventory_active = False
					continue
				elif not self.pause_active:
					# Open pause menu
					self.toggle_pause()
					continue
			
			# Handle quest reward claiming
			if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
				if self.quest_manager.active_quest and self.quest_manager.active_quest.completed:
					self.quest_manager.claim_rewards()
					continue

			if event.type == pygame.KEYDOWN and event.key == pygame.K_F5: 
				if not self.save_load_active and not self.pause_active:
					self.toggle_save_load_menu()
					continue

			if event.type == pygame.KEYDOWN and event.key == pygame.K_F6:
				self.quick_save()
				continue

			if event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
				self.quick_load()
				continue

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_RETURN:
					if hasattr(self, 'dog') and self.dog:
						distance = self.player.rect.center
						dog_pos = self.dog.rect.center
						dist = math.sqrt((distance[0]-dog_pos[0])**2 + (distance[1]-dog_pos[1])**2)

						if dist < 60:
							self.dog.toggle_sit()
			
			
			if event.type == pygame.KEYDOWN and event.key == pygame.K_f and self.dog:    
					if self.dog.can_feed(self.player):       
						for crop in ['corn', 'tomato', 'moon_melon', 'pumpkin', 'cactus']:
							if self.player.item_inventory.get(crop, 0) > 0:                
								self.player.item_inventory[crop] -= 1                 
								self.dog.feed(crop)
								break

				


								






	



			filtered_events.append(event)

		# drawing logic
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player)


		if self.dog:    
			camera_offset = self.all_sprites.offset    
			dog_screen_pos = self.dog.rect.move(-camera_offset.x, -camera_offset.y)     
			self.display_surface.blit(self.dog.image, dog_screen_pos)


		if hasattr(self, 'dog') and self.dog:
			self.dog.draw_ward_effect(self.all_sprites.offset)



		if self.player.timers['tool use'].active or self.player.timers['seed use'].active:
			self.draw_grid_selection()

		# Draw ward radius overlay when hovering over placed wards
		self.draw_ward_radius_on_hover()
		
		# Update player's knowledge about camera offset to make spatial mouse control possible
		if hasattr(self, 'player'):
			self.player.offset = self.all_sprites.offset
		
		# updates
		if self.save_load_active:
			self.save_load_menu.handle_input(filtered_events)
			self.save_load_menu.draw()
		
		elif self.pause_active:
			# let the pause menu handle its events and drawing (use filtered events)
			self.pause.update(filtered_events)
		elif self.stage_cutscene:
			# Stage cutscene is playing
			if self.stage_cutscene.run(dt, filtered_events):
				# Cutscene finished
				self.stage_cutscene.cleanup()
				self.stage_cutscene = None
		elif self.shop_active:
			self.trader_menu.update(dt)
			self.trader_menu.handle_input(filtered_events)
			self.trader_menu.draw()
		elif self.inventory_active:
			# Inventory is open - pause game updates
			pass
		else:
			if self.dog:
				self.dog.update(dt,	self.player)
			self.all_sprites.update(dt)
			self.soil_layer.update_plants(dt)
			self.plant_collision()
			self.quest_manager.update(dt)
			self.time_system.update(dt, self.corruption_surge)
			self.energy_system.update(dt)
			self.health_system.update(dt)
			self.corruption_surge.update(dt)
			if self.corruption_spread:
				self.corruption_spread.update(dt, self.soil_layer, self.player, self.health_system, self.ward_system)

		# Check for pending cutscene
		if self.pending_cutscene_stage and not self.stage_cutscene:
			self.stage_cutscene = StageCutscene(self.pending_cutscene_stage)
			self.pending_cutscene_stage = None

		# Show intro cutscene on first frame
		if not self.has_shown_intro and not self.stage_cutscene:
			self.has_shown_intro = True
			self.stage_cutscene = StageCutscene('corrupted')

		# weather
		if hasattr(self, 'player'):
			self.overlay.display(dt, filtered_events)
		if self.raining and not (self.shop_active or self.pause_active or self.inventory_active):
			self.rain.update()
		self.sky.display(self.time_system, self.corruption_surge)

		# Quest UI
		if not self.inventory_active:
			self.quest_manager.draw()

		# Display cleanse progress
		self.display_cleanse_progress()

		# Display time and day
		self.time_system.draw()

		# Display health bar
		self.health_system.draw()

		# Display energy bar
		self.energy_system.draw()

		# Display energy bar
		self.energy_system.draw()

		self.corruption_surge.draw()
		self.corruption_surge.draw_report()
		self.corruption_surge.handle_report_input(events)

		# Display corruption spread notifications
		if self.corruption_spread:
			self.corruption_spread.draw()

		# transition overlay
		if hasattr(self, 'player') and self.player.sleep:
			if not self.transition.stack:
				self.transition.add_transition()
			self.transition.play()

		# Draw inventory UI (on top of everything)
		if self.inventory_active:
			self.inventory_ui.draw()

		# draw either custom cursor or let system cursor show while paused
		self.draw_cursor()
		

		# draw pause menu on top
		if self.pause_active:
			self.pause.draw()


		if self.dog:
			camera_offset = self.all_sprites.offset  # Your camera offset    
			self.dog.draw_interaction_prompt(camera_offset, self.player)


	def display_cleanse_progress(self):
		"""Display the current cleanse stage and progress"""
		font = pygame.font.Font('font/LycheeSoda.ttf', 20)
		
		# Stage name
		stage_text = f"Stage: {self.cleanse_stage.upper()}"
		stage_surf = font.render(stage_text, False, 'White')
		stage_rect = stage_surf.get_rect(topright=(SCREEN_WIDTH - 10, 10))
		
		# Background for stage
		bg_rect = stage_rect.inflate(10, 6)
		pygame.draw.rect(self.display_surface, 'Black', bg_rect, 0, 4)
		pygame.draw.rect(self.display_surface, 'White', bg_rect, 2, 4)
		self.display_surface.blit(stage_surf, stage_rect)
		
		# Progress bar (if not at final stage)
		if self.cleanse_stage != 'cleansed':
			points_needed = self.points_needed.get(self.cleanse_stage, 100)
			progress = min(self.cleanse_points / points_needed, 1.0)
			
			# Progress text
			progress_text = f"Cleanse: {self.cleanse_points}/{points_needed}"
			progress_surf = font.render(progress_text, False, 'White')
			progress_rect = progress_surf.get_rect(topright=(SCREEN_WIDTH - 10, 40))
			
			# Background
			bg_rect2 = progress_rect.inflate(10, 6)
			pygame.draw.rect(self.display_surface, 'Black', bg_rect2, 0, 4)
			pygame.draw.rect(self.display_surface, 'White', bg_rect2, 2, 4)
			self.display_surface.blit(progress_surf, progress_rect)
			
			# Progress bar
			bar_width = 150
			bar_height = 15
			bar_x = SCREEN_WIDTH - 10 - bar_width
			bar_y = 70
			
			# Background bar
			pygame.draw.rect(self.display_surface, 'Black', 
							(bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 0, 4)
			pygame.draw.rect(self.display_surface, 'Gray', 
							(bar_x, bar_y, bar_width, bar_height), 0, 3)
			
			# Progress fill
			fill_width = int(bar_width * progress)
			if fill_width > 0:
				pygame.draw.rect(self.display_surface, 'Green', 
								(bar_x, bar_y, fill_width, bar_height), 0, 3)

	def draw_cursor(self):
		# Attempt to make mouse feel smooth
		mouse_pos = pygame.mouse.get_pos()
	
		offset_x = 5
		offset_y = 5
		render_pos = (mouse_pos[0] - offset_x, mouse_pos[1] - offset_y)
		self.display_surface.blit(self.cursor_surf, render_pos)
		# only draw custom cursor when OS cursor is hidden (e.g., not paused)

	def draw_grid_selection(self):
		target_pos = self.player.target_pos
		col = int(target_pos.x // TILE_SIZE)
		row = int(target_pos.y // TILE_SIZE)

		current_tile_rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
		offset = self.all_sprites.offset
		pygame.draw.rect(self.display_surface, 'white', current_tile_rect.move(-offset), 3)

	def draw_ward_preview(self):
		"""Draw ward placement preview at mouse/target position"""
		# Get target position
		target_pos = self.player.target_pos
		grid_x = int(target_pos.x // TILE_SIZE)
		grid_y = int(target_pos.y // TILE_SIZE)
		
		# Draw protection radius preview (6 tiles in each direction)
		protection_radius = 6
		offset = self.all_sprites.offset
		
		for dx in range(-protection_radius, protection_radius + 1):
			for dy in range(-protection_radius, protection_radius + 1):
				# Calculate distance for circular effect
				distance = (dx * dx + dy * dy) ** 0.5
				if distance <= protection_radius:
					tile_x = (grid_x + dx) * TILE_SIZE
					tile_y = (grid_y + dy) * TILE_SIZE
					
					# Semi-transparent blue overlay
					preview_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
					alpha = int(80 * (1 - distance / protection_radius))  # Fade towards edges
					preview_surf.fill((100, 200, 255, alpha))
					
					preview_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
					self.display_surface.blit(preview_surf, preview_rect.move(-offset))
		
		# Draw center ward indicator (brighter)
		center_x = grid_x * TILE_SIZE
		center_y = grid_y * TILE_SIZE
		center_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
		
		# Draw glowing circle in center
		pygame.draw.circle(center_surf, (150, 220, 255, 150), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 3)
		pygame.draw.circle(center_surf, (200, 240, 255, 200), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 4)
		
		center_rect = pygame.Rect(center_x, center_y, TILE_SIZE, TILE_SIZE)
		self.display_surface.blit(center_surf, center_rect.move(-offset))

	def draw_ward_radius_on_hover(self):
		"""Draw ward radius when hovering cursor over placed wards"""
		mouse_pos = pygame.mouse.get_pos()
		mouse_world_pos = pygame.math.Vector2(mouse_pos) + self.all_sprites.offset
		
		# Check if mouse is hovering over any ward
		for ward in self.ward_system.ward_sprites.sprites():
			ward_rect = ward.rect
			if ward_rect.collidepoint(mouse_world_pos):
				# Draw protection radius for this ward
				protection_radius = ward.protection_radius
				offset = self.all_sprites.offset
				
				for dx in range(-protection_radius, protection_radius + 1):
					for dy in range(-protection_radius, protection_radius + 1):
						# Calculate distance for circular effect
						distance = (dx * dx + dy * dy) ** 0.5
						if distance <= protection_radius:
							tile_x = (ward.grid_x + dx) * TILE_SIZE
							tile_y = (ward.grid_y + dy) * TILE_SIZE
							
							# Semi-transparent blue overlay
							preview_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
							alpha = int(100 * (1 - distance / (protection_radius + 1)))
							preview_surf.fill((100, 200, 255, alpha))
							
							preview_rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
							self.display_surface.blit(preview_surf, preview_rect.move(-offset))
				
				# Highlight the ward itself
				highlight_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
				pygame.draw.circle(highlight_surf, (255, 255, 255, 100), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 2)
				highlight_rect = ward_rect.move(-offset)
				self.display_surface.blit(highlight_surf, highlight_rect)
				
				break  # Only show one ward radius at a time

class CameraGroup(pygame.sprite.Group):
	def __init__(self):
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.offset = pygame.math.Vector2()

	def custom_draw(self, player):
		self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
		self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

		# Get all unique Z values from sprites (not just from LAYERS dict)
		all_z_values = set()
		for sprite in self.sprites():
			all_z_values.add(sprite.z)
		
		# Draw sprites layer by layer, sorting by Y within each layer
		for z_value in sorted(all_z_values):
			# Get all sprites in this Z layer
			layer_sprites = [sprite for sprite in self.sprites() if sprite.z == z_value]
			
			# Sort by Y position within the layer for depth effect
			for sprite in sorted(layer_sprites, key=lambda s: s.rect.centery):
				offset_rect = sprite.rect.copy()
				offset_rect.center -= self.offset
				self.display_surface.blit(sprite.image, offset_rect)