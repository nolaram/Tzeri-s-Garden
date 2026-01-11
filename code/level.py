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
from quest_system import QuestManager
from inventory_ui import InventoryUI

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
		self.soil_layer = None
		self.setup()
		if self.current_map_path:
			print(f"\n=== Creating Soil Layer ===")
			print(f"Using map path: {self.current_map_path}")
			self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites, self.current_map_path)
			# Update player's soil layer reference
			if self.player:
				self.player.soil_layer = self.soil_layer
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

		# Inventory UI
		self.inventory_ui = InventoryUI(self.player)
		self.inventory_active = False

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
		
		import os
		print(f"\n{'='*50}")
		print(f"Loading map: {map_path}")
		print(f"Current stage: {self.cleanse_stage}")
		print(f"File exists: {os.path.exists(map_path)}")
		
		try:
			tmx_data = load_pygame(map_path)
			print(f"✓ Successfully loaded map for stage: {self.cleanse_stage}")
		except Exception as e:
			print(f"✗ Error loading {map_path}: {e}")
			print(f"Falling back to default map.tmx")
			map_path = 'data/map.tmx'
			self.current_map_path = map_path
			tmx_data = load_pygame(map_path)

		# Clear ALL existing sprites
		self.clear_all_sprites()
		
		# Process ALL layers in the correct order
		self.process_all_layers_in_order(tmx_data)
		
		# Setup player and interactions
		self.setup_player_and_interactions(tmx_data)
		
		# Check for missing important layers
		layer_names = [layer.name.lower() for layer in tmx_data.visible_layers]
		if 'farmable' not in layer_names:
			print(f"  ⚠ WARNING: No 'Farmable' layer found in this map!")
			print(f"  → Farming will not work until you add and make visible a Farmable layer")
		if 'collision' not in layer_names:
			print(f"  ⚠ WARNING: No 'Collision' layer found in this map!")
			print(f"  → Custom collision tiles will not work")
		
		print(f"{'='*50}\n")

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
		print(f"\nProcessing layers for {self.cleanse_stage}:")
		print("-" * 30)
		
		# Get all visible layers in their Tiled order
		all_layers = list(tmx_data.visible_layers)
		
		for i, layer in enumerate(all_layers):
			layer_name = layer.name
			layer_type = type(layer).__name__
			print(f"Layer {i+1}: {layer_name} (type: {layer_type})")
			
			# Handle tile layers - check for tiles() method
			if hasattr(layer, 'tiles') and callable(layer.tiles):
				self.process_tile_layer_by_name(layer_name, layer, tmx_data)
			
			# Handle object layers - check layer type
			elif 'TiledObjectGroup' in layer_type or 'ObjectLayer' in layer_type:
				self.process_object_layer_by_name(layer_name, layer, tmx_data)
			
			# Fallback: try to iterate as object layer
			elif hasattr(layer, '__iter__'):
				try:
					# Try to peek at first item
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
		
		print(f"  Processing tile layer '{layer_name}': {tile_count} tiles")
		
		# Define comprehensive layer processing rules
		layer_rules = {
			# Water layers (bottom-most)
			'water': {'z': LAYERS['water'], 'groups': [self.all_sprites], 'special': 'water'},
			'corrupted water': {'z': LAYERS['water'], 'groups': [self.all_sprites], 'special': 'water'},
			
			# Ground and terrain layers - these should be visible!
			'ground': {'z': LAYERS['ground'], 'groups': [self.all_sprites], 'collision': False},
			'grass': {'z': LAYERS['ground'] + 0.2, 'groups': [self.all_sprites], 'collision': False},
			'forest grass': {'z': LAYERS['ground'] + 0.3, 'groups': [self.all_sprites], 'collision': False},
			'path': {'z': LAYERS['ground'] + 0.4, 'groups': [self.all_sprites], 'collision': False},
			'hills': {'z': LAYERS['ground'] + 0.5, 'groups': [self.all_sprites], 'collision': False},
			
			# Details layer (above ground, below player)
			'details': {'z': LAYERS['ground'] + 0.6, 'groups': [self.all_sprites], 'collision': False},
			
			# Decorations - NO collision, just visual
			'decorations': {'z': LAYERS['main'] - 0.5, 'groups': [self.all_sprites], 'collision': False},
			'decoration': {'z': LAYERS['main'] - 0.5, 'groups': [self.all_sprites], 'collision': False},
			'outside decoration': {'z': LAYERS['main'] - 0.5, 'groups': [self.all_sprites], 'collision': False},
			
			# House layers
			'housefloor': {'z': LAYERS['house bottom'], 'groups': [self.all_sprites], 'collision': False},
			'housefurniturebottom': {'z': LAYERS['house bottom'], 'groups': [self.all_sprites], 'collision': False},
			'housewalls': {'z': LAYERS['main'], 'groups': [self.all_sprites, self.collision_sprites], 'collision': True},
			'housefurnituretop': {'z': LAYERS['main'], 'groups': [self.all_sprites], 'collision': False},  # Removed collision
			
			# Fences and obstacles - keep collision only for fences
			'fence': {'z': LAYERS['main'], 'groups': [self.all_sprites, self.collision_sprites], 'collision': True},
			
			# Farmable layer - should be visible!
			'farmable': {'z': LAYERS['ground'] + 0.05, 'groups': [self.all_sprites], 'collision': False, 'special': 'farmable'},
			
			# Collision layer - invisible collision tiles
			'collision': {'z': LAYERS['main'], 'groups': [self.collision_sprites], 'collision': True, 'invisible': True},
			
			# Corruption-specific layers - NO collision (use collision layer instead)
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
			# Determine default behavior based on layer name patterns
			if 'collision' in layer_name_lower:
				rule = {'z': LAYERS['main'], 'groups': [self.collision_sprites], 'collision': True, 'invisible': True}
				print(f"    Using COLLISION rule for layer: {layer_name}")
			elif 'house' in layer_name_lower:
				rule = {'z': LAYERS['main'], 'groups': [self.all_sprites], 'collision': False}
			elif 'tree' in layer_name_lower:
				rule = {'z': LAYERS['main'] + 1, 'groups': [self.all_sprites, self.collision_sprites], 'collision': True}
			else:
				rule = {'z': LAYERS['main'], 'groups': [self.all_sprites], 'collision': False}
			print(f"    Using default rule for layer: {layer_name}")
		else:
			print(f"    Matched rule: {matched_key}")
		
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
					# Register this tile position with the soil layer!
					# Add 'F' to the soil grid at this position
					if hasattr(self, 'soil_layer') and self.soil_layer:
						# Make sure grid is large enough
						if y < len(self.soil_layer.grid) and x < len(self.soil_layer.grid[0]):
							if 'F' not in self.soil_layer.grid[y][x]:
								self.soil_layer.grid[y][x].append('F')
								farmable_tiles_registered += 1
					
					# Only create visual sprite for corrupted stage, make it invisible for other stages
					if self.cleanse_stage == 'corrupted':
						# Visible farmable tiles in corrupted stage
						Generic(pos, surf, rule['groups'], rule['z'])
					else:
						# Invisible farmable tiles in cleaner stages (still functional)
						invisible_surf = surf.copy()
						invisible_surf.set_alpha(0)
						Generic(pos, invisible_surf, rule['groups'], rule['z'])
					
					tiles_created += 1
					continue
				
				elif rule['special'] == 'water':
					try:
						# Try to load appropriate water frames
						if 'corrupted' in layer_name_lower:
							try:
								water_frames = import_folder('graphics/corrupted_water')
							except:
								water_frames = import_folder('graphics/water')
						else:
							water_frames = import_folder('graphics/water')
						
						# Make sure we have frames before creating water
						if water_frames and len(water_frames) > 0:
							Water(pos, water_frames, rule['groups'])
							tiles_created += 1
						else:
							# Fallback to generic sprite if no water frames
							if surf:
								Generic(pos, surf, rule['groups'], rule['z'])
								tiles_created += 1
					except Exception as e:
						print(f"    Warning: Could not create water tile at {pos}: {e}")
					continue
					
				elif rule['special'] == 'corrupted_tree':
					# Create a corrupted tree as a simple obstacle (not an interactive Tree)
					# Corrupted trees don't produce apples and can't be chopped
					Generic(pos, surf, rule['groups'], rule['z'])
					tiles_created += 1
					continue
			
			# Handle invisible collision tiles
			if rule.get('invisible', False):
				# Create invisible collision sprite
				if surf:
					# Make the surface invisible
					invisible_surf = surf.copy()
					invisible_surf.set_alpha(0)
					Generic(pos, invisible_surf, rule['groups'], rule['z'])
					tiles_created += 1
				else:
					# No surface, create a blank invisible tile
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
				print(f"    Warning: Could not create tile at {pos}: {e}")
		
		print(f"    Created {tiles_created} sprites from this layer")
		
		if tiles_skipped_no_surf > 0:
			print(f"    ⚠ Skipped {tiles_skipped_no_surf} tiles with no surface/graphic")
		
		if tiles_created > 0 and tiles_created != tile_count:
			print(f"    ⚠ Warning: {tile_count - tiles_created - tiles_skipped_no_surf} tiles failed to create")

	def process_object_layer_by_name(self, layer_name, layer, tmx_data):
		"""Process a specific object layer based on its name"""
		layer_name_lower = layer_name.lower()
		
		objects_list = list(layer)
		print(f"  Processing object layer '{layer_name}': {len(objects_list)} objects")
		
		for obj in objects_list:
			pos = (obj.x, obj.y)
				
			obj_name = getattr(obj, 'name', None)
			print(f"    Processing object: '{obj_name}' at ({obj.x}, {obj.y})")
				
			# Debug: Check if object has image
			has_image = hasattr(obj, 'image') and obj.image is not None
			print(f"      Has image: {has_image}")
			if has_image:
				print(f"      Image size: {obj.image.get_size()}")
				
			# If object has no name but has an image, render it as a generic sprite
			if (not obj_name or obj_name == 'None') and has_image:
				Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
				print(f"      ✓ Created generic sprite from unnamed/None object")
				continue
				
			# NOW check for named objects
			if hasattr(obj, 'name') and obj_name:
				if obj_name == 'Trader':
					# Create visual sprite for trader if it has an image
					if hasattr(obj, 'image') and obj.image:
						Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
					
					# Create interaction zone
					Interaction(
						pos=pos,
						size=(obj.width, obj.height),
						groups=[self.interaction_sprites],  # Don't add to all_sprites (invisible hitbox)
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
				elif obj_name == 'CorruptedTree':
					if hasattr(obj, 'image') and obj.image:
						CorruptedTree(
							pos=pos,
							surf=obj.image,
							groups=[self.all_sprites],
							name=obj.name if hasattr(obj, 'name') else 'CorruptedTree',
							player_add=self.player_add
						)

			# Collision layer - invisible collision tiles
			if 'collision' in layer_name_lower:
				if hasattr(obj, 'width') and hasattr(obj, 'height'):
					# Create invisible collision surface
					collision_surf = pygame.Surface((obj.width, obj.height))
					collision_surf.set_alpha(0)  # Invisible
					Generic(pos, collision_surf, [self.collision_sprites], LAYERS['main'])
					print(f"    Created collision rect at ({obj.x}, {obj.y}) - {obj.width}x{obj.height}")
			
			# Player layer - handled separately in setup_player
			elif 'player' in layer_name_lower:
				pass  # Handled separately
			
			# Objects layer
			elif 'objects' in layer_name_lower:
				if hasattr(obj, 'image') and obj.image:
					Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
					obj_name = getattr(obj, 'name', None)
				print(f"    Processing object: '{obj_name}' at ({obj.x}, {obj.y})")
				
				# Debug: Check if object has image
				has_image = hasattr(obj, 'image') and obj.image is not None
				print(f"      Has image: {has_image}")
				if has_image:
					print(f"      Image size: {obj.image.get_size()}")
				
				# If object has no name but has an image, render it as a generic sprite
				if (not obj_name or obj_name == 'None') and has_image:
					Generic((obj.x, obj.y), obj.image, [self.all_sprites], LAYERS['main'])
					print(f"      ✓ Created generic sprite from unnamed/None object")
					continue
				
				# Skip if no name attribute
				if not hasattr(obj, 'name') or not obj_name:
					if has_image:
						# Still create it as a generic sprite
						Generic((obj.x, obj.y), obj.image, [self.all_sprites], LAYERS['main'])
						print(f"      ✓ Created generic sprite (no name)")
					continue
			
			# Trader layer
			elif 'trader' in layer_name_lower:
				if hasattr(obj, 'name') and obj.name == 'Trader':
					# Create visual sprite for trader if it has an image
					if hasattr(obj, 'image') and obj.image:
						Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
					
					# Create interaction zone
					Interaction(
						pos=pos,
						size=(obj.width, obj.height),
						groups=[self.interaction_sprites],  # Don't add to all_sprites (invisible hitbox)
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
			
			# Default object handling - if it has an image, render it
			else:
				if hasattr(obj, 'image') and obj.image:
					# Determine if it should have collision based on properties
					has_collision = False
					if hasattr(obj, 'properties') and obj.properties:
						has_collision = obj.properties.get('collision', False)
					
					groups = [self.all_sprites]
					if has_collision:
						groups.append(self.collision_sprites)
					
					Generic(pos, obj.image, groups, LAYERS['main'])
					print(f"    Created generic sprite from object at ({obj.x}, {obj.y})")

	def setup_player_and_interactions(self, tmx_data):
		"""Setup player, bed, and other interactions from object layers"""
		player_exists = hasattr(self, 'player') and self.player is not None
		
		print(f"\nSearching for player and interactions...")
		print(f"Total visible layers: {len(list(tmx_data.visible_layers))}")
		
		# Look for Player layer
		player_layer_found = False
		for layer in tmx_data.visible_layers:
			layer_name = getattr(layer, 'name', 'unnamed')
			layer_type = type(layer).__name__
			is_object_layer = 'TiledObjectGroup' in layer_type or 'ObjectLayer' in layer_type or (hasattr(layer, '__iter__') and not hasattr(layer, 'tiles'))
			
			print(f"  Checking layer '{layer_name}' (type: {layer_type}) - is object layer: {is_object_layer}")
			
			if is_object_layer and 'player' in layer_name.lower():
				player_layer_found = True
				print(f"  ✓ Found Player layer: '{layer_name}'")
				objects_in_layer = list(layer)
				print(f"    Objects in layer: {len(objects_in_layer)}")
				
				for obj in objects_in_layer:
					obj_name = getattr(obj, 'name', 'unnamed')
					print(f"    Processing object: '{obj_name}' at ({obj.x}, {obj.y})")
					
					# Debug: Check if object has image
					has_image = hasattr(obj, 'image') and obj.image is not None
					print(f"      Has image: {has_image}")
					if has_image:
						print(f"      Image size: {obj.image.get_size()}")
					if hasattr(obj, 'name'):
						# Player start position
						if obj.name == 'Start':
							# Tiled objects store position as top-left by default
							# But if the object is a point (no width/height), use center directly
							# Otherwise calculate center from the object's dimensions
							if hasattr(obj, 'width') and hasattr(obj, 'height') and obj.width > 0 and obj.height > 0:
								# Object has dimensions - calculate center
								start_pos = (obj.x + obj.width // 2, obj.y + obj.height // 2)
							else:
								# Point object - use position directly
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
							else:
								# Reposition existing player
								self.player.pos = pygame.math.Vector2(start_pos)
								self.player.rect.center = start_pos
								self.player.hitbox.center = self.player.rect.center
							
							print(f"  Player positioned at: {start_pos} (from obj at {obj.x}, {obj.y})")
						
						# Bed interaction
						elif obj.name == 'Bed':
							# Create visual sprite for bed if it has an image
							if hasattr(obj, 'image') and obj.image:
								Generic(pos, obj.image, [self.all_sprites], LAYERS['house bottom'])
							
							# Create interaction zone
							Interaction(
								pos=(obj.x, obj.y),
								size=(obj.width, obj.height),
								groups=[self.interaction_sprites],  # Don't add to all_sprites (invisible hitbox)
								name='Bed'
							)
							print(f"  Bed placed at: ({obj.x}, {obj.y})")
						
						# Trader interaction (if not already placed)
						elif obj.name == 'Trader':
							# Check if trader already exists
							trader_exists = False
							for sprite in self.interaction_sprites:
								if hasattr(sprite, 'name') and sprite.name == 'Trader':
									trader_exists = True
									break
							
							if not trader_exists:
								# Create visual sprite for trader if it has an image
								if hasattr(obj, 'image') and obj.image:
									Generic(pos, obj.image, [self.all_sprites], LAYERS['main'])
								
								# Create interaction zone
								Interaction(
									pos=(obj.x, obj.y),
									size=(obj.width, obj.height),
									groups=[self.interaction_sprites],  # Don't add to all_sprites (invisible hitbox)
									name='Trader'
								)
								print(f"  Trader placed at: ({obj.x}, {obj.y})")

		# Ensure player exists
		if not player_exists and self.player is None:
			print(f"  ⚠ Warning: No player start found, creating default player at (640, 360)")
			if not player_layer_found:
				print(f"  ⚠ Player layer was not found in the map!")
			self.player = Player(
				pos=(640, 360),
				group=self.all_sprites,
				collision_sprites=self.collision_sprites,
				tree_sprites=self.tree_sprites,
				interaction=self.interaction_sprites,
				soil_layer=self.soil_layer,
				toggle_shop=self.toggle_shop
			)
		elif self.player:
			print(f"  ✓ Player setup complete at position: {self.player.rect.center}")
		
		# Update player's soil layer reference if soil layer exists
		if self.soil_layer and self.player:
			self.player.soil_layer = self.soil_layer
		
		# Update overlay with player reference
		if hasattr(self, 'overlay'):
			self.overlay.player = self.player
		
		# Debug: Print sprite group statistics
		print(f"\n=== Sprite Statistics ===")
		print(f"Total sprites in all_sprites: {len(self.all_sprites.sprites())}")
		print(f"Collision sprites: {len(self.collision_sprites.sprites())}")
		
		# Count sprites by Z layer
		layer_counts = {}
		for sprite in self.all_sprites.sprites():
			z = getattr(sprite, 'z', 'unknown')
			layer_counts[z] = layer_counts.get(z, 0) + 1
		
		print(f"\nSprites per Z-layer:")
		for z in sorted([k for k in layer_counts.keys() if k != 'unknown']):
			layer_name = [name for name, val in LAYERS.items() if val == z]
			layer_name = layer_name[0] if layer_name else f"Z={z}"
			print(f"  {layer_name} (Z={z}): {layer_counts[z]} sprites")
		
		if 'unknown' in layer_counts:
			print(f"  Unknown Z-layer: {layer_counts['unknown']} sprites")
		print(f"========================\n")

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
			# Reset cleanse points to prevent re-triggering
			self.cleanse_points = 0
			
			# Play stage transition effect
			self.play_stage_transition()
			# Update quest for stage progress
			self.quest_manager.on_stage_progress()
			# Change stage BEFORE saving data
			self.cleanse_stage = stage_order[current_index + 1]
			print(f"\n{'='*50}")
			print(f"FARM PROGRESSED TO: {self.cleanse_stage.upper()}")
			print(f"{'='*50}")
			
			# Save the current soil state AND plant data
			saved_grid = [row[:] for row in self.soil_layer.grid]  # Deep copy
			saved_plants = []  # Store plant data

			# Save existing plant information
			for plant in self.soil_layer.plant_sprites.sprites():
				plant_data = {
					'plant_type': plant.plant_type,
					'age': plant.age,
					'pos': (plant.soil.rect.x // TILE_SIZE, plant.soil.rect.y // TILE_SIZE)
				}
				saved_plants.append(plant_data)

			# Clear old soil layer completely
			for sprite in list(self.soil_layer.soil_sprites.sprites()):
				sprite.kill()
			for sprite in list(self.soil_layer.water_sprites.sprites()):
				sprite.kill()
			for sprite in list(self.soil_layer.plant_sprites.sprites()):
				sprite.kill()

			# Reload the map with new stage (this creates collision sprites)
			self.setup()
			
			# NOW create new soil layer for the new map
			self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites, self.current_map_path)
			self.soil_layer.raining = self.raining
			
			# Update player's soil layer reference
			if self.player:
				self.player.soil_layer = self.soil_layer

			# Restore the saved soil state to the new grid
			for y in range(min(len(saved_grid), len(self.soil_layer.grid))):
				for x in range(min(len(saved_grid[0]), len(self.soil_layer.grid[0]))):
					# Keep 'F' from new map, but restore 'X', 'W' from old
					old_cell = saved_grid[y][x]
					new_cell = self.soil_layer.grid[y][x]
					
					# Restore tilled soil
					if 'X' in old_cell and 'X' not in new_cell:
						new_cell.append('X')
					# Restore water
					if 'W' in old_cell and 'W' not in new_cell:
						new_cell.append('W')

			# Recreate visual soil sprites
			self.soil_layer.create_soil_tiles()

			# Restore plants
			for plant_data in saved_plants:
				x, y = plant_data['pos']
				if y < len(self.soil_layer.grid) and x < len(self.soil_layer.grid[0]):
					# Find the corresponding soil sprite
					for soil_sprite in self.soil_layer.soil_sprites.sprites():
						if soil_sprite.rect.x == x * TILE_SIZE and soil_sprite.rect.y == y * TILE_SIZE:
							# Add 'P' marker back
							self.soil_layer.grid[y][x].append('P')
							
							# Recreate the plant
							from soil import Plant
							new_plant = Plant(
								plant_data['plant_type'],
								[self.all_sprites, self.soil_layer.plant_sprites, self.collision_sprites],
								soil_sprite,
								self.soil_layer.check_watered
							)
							# Restore the plant's age
							new_plant.age = plant_data['age']
							new_plant.image = new_plant.frames[int(new_plant.age)]
							new_plant.rect = new_plant.image.get_rect(
								midbottom=soil_sprite.rect.midbottom + pygame.math.Vector2(0, new_plant.y_offset)
							)
							if int(new_plant.age) >= new_plant.max_age:
								new_plant.harvestable = True
							break

			# Recreate water sprites if it was raining
			for sprite in list(self.soil_layer.water_sprites.sprites()):
				sprite.kill()
				
			if self.raining:
				self.soil_layer.water_all()
			
			# Show notification
			print(f"✓ Stage transition complete!")

	def play_stage_transition(self):
		"""Play a visual transition when stage changes"""
		# Create a simple fade effect
		fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
		fade_surface.fill((0, 0, 0))
		
		# Fade out
		for alpha in range(0, 255, 15):
			# Keep game running in background
			self.all_sprites.update(0.016)  # Simulate frame
			
			fade_surface.set_alpha(alpha)
			self.display_surface.blit(fade_surface, (0, 0))
			pygame.display.update()
			pygame.time.delay(30)
		
		# Hold black screen with "Cleansing the Farm" text
		start_time = pygame.time.get_ticks()
		duration = 2500  # 2.5 seconds
		
		while pygame.time.get_ticks() - start_time < duration:
			# Keep game running
			self.all_sprites.update(0.016)
			
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
			# Keep game running
			self.all_sprites.update(0.016)
			
			fade_surface.set_alpha(alpha)
			# Redraw game during fade in
			self.display_surface.fill('black')
			self.all_sprites.custom_draw(self.player)
			self.display_cleanse_progress()
			self.display_surface.blit(fade_surface, (0, 0))
			pygame.display.update()
			pygame.time.delay(30)

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
		# plants
		self.soil_layer.update_plants()

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
		"""
		Handles player harvesting plants safely.
		Also adds cleanse points when crops are harvested.
		"""
		if not self.soil_layer.plant_sprites:
			return

		for plant in self.soil_layer.plant_sprites.sprites():
			if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
				
				# 1️⃣ Give player the plant
				self.player_add(plant.plant_type)

				# Update quest progress
				self.quest_manager.on_harvest(plant.plant_type)

				# Add cleanse points based on crop type
				cleanse_values = {
					'corn': 5,
					'tomato': 8,
					'moon_melon': 12,
					'pumpkin': 10,
					'cactus': 10
				}
				points = cleanse_values.get(plant.plant_type, 5)
				self.add_cleanse_points(points)

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
			# Check for inventory toggle
			if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
				self.inventory_active = not self.inventory_active
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
			filtered_events.append(event)

		# drawing logic
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player)

		if self.player.timers['tool use'].active or self.player.timers['seed use'].active:
			self.draw_grid_selection()
		
		# Update player's knowledge about camera offset to make spatial mouse control possible
		if hasattr(self, 'player'):
			self.player.offset = self.all_sprites.offset
		
		# updates
		if self.pause_active:
			# let the pause menu handle its events and drawing (use filtered events)
			self.pause.update(filtered_events)
		elif self.shop_active:
			self.menu.update()
		elif self.inventory_active:
			# Inventory is open - pause game updates
			pass
		else:
			self.all_sprites.update(dt)
			self.plant_collision()
			self.quest_manager.update(dt)

		# weather
		if hasattr(self, 'player'):
			self.overlay.display(dt, filtered_events)
		if self.raining and not (self.shop_active or self.pause_active or self.inventory_active):
			self.rain.update()
		self.sky.display(dt)

		# Quest UI
		if not self.inventory_active:
			self.quest_manager.draw()

		# Display cleanse progress
		self.display_cleanse_progress()

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