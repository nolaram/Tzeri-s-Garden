import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *
from random import choice

class SoilTile(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups):
		super().__init__(groups)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = LAYERS['soil']

class WaterTile(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups):
		super().__init__(groups)
		self.image = surf
		self.rect = self.image.get_rect(topleft = pos)
		self.z = LAYERS['soil water']

class Plant(pygame.sprite.Sprite):
	def __init__(self, plant_type, groups, soil, check_watered):
		super().__init__(groups)
		
		# setup
		self.plant_type = plant_type
		self.frames = import_folder(f'graphics/fruit/{plant_type}')
		self.soil = soil
		self.check_watered = check_watered

		# Time-based growing (in seconds)
		self.growth_times = {
			'corn': 60,        # 1 minute
			'tomato': 90,      # 1.5 minutes
			'moon_melon': 120, # 2 minutes
			'pumpkin': 120,    # 2 minutes
			'cactus': 180      # 3 minutes
		}
		
		self.total_grow_time = self.growth_times.get(plant_type, 60)
		self.current_grow_time = 0
		self.max_age = len(self.frames) - 1
		self.harvestable = False
		
		# Quality/Rating system
		self.quality = 'standard'  # standard, silver, gold, mythical
		self.quality_colors = {
			'standard': (255, 255, 255),
			'silver': (192, 192, 192),
			'gold': (255, 215, 0),
			'mythical': (138, 43, 226)
		}
		
		# sprite setup
		self.age = 0
		self.image = self.frames[0]  # Start at phase 0
		self.y_offset = -16 if plant_type == 'corn' else -8
		self.rect = self.image.get_rect(midbottom = soil.rect.midbottom + pygame.math.Vector2(0,self.y_offset))
		self.z = LAYERS['ground plant']
		self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)  # ADD THIS LINE

	def grow(self, dt):
		"""Grow plant based on delta time"""
		if self.check_watered(self.rect.center):
			# Add time
			self.current_grow_time += dt
			
			# Calculate growth stage (0, 1, 2, 3)
			# Phase 0: 0-25% of time
			# Phase 1: 25-50% of time
			# Phase 2: 50-75% of time
			# Phase 3: 75-100% of time (harvestable)
			growth_percent = min(self.current_grow_time / self.total_grow_time, 1.0)
			new_age = int(growth_percent * (self.max_age + 1))
			
			# Ensure we don't exceed max age
			new_age = min(new_age, self.max_age)
			
			# Update visual if age changed
			if new_age != self.age:
				self.age = new_age
				self.image = self.frames[self.age]
				self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0,self.y_offset))
				
			# Change Z layer when growing
			if self.age > 0:
				self.z = LAYERS['main']
				if not hasattr(self, 'hitbox') or self.hitbox is None:
					self.hitbox = self.rect.copy().inflate(-26,-self.rect.height * 0.4)
		
		# Check if fully grown
		if self.age >= self.max_age:
			self.harvestable = True
			
			# Determine quality when fully grown (only once)
			if self.quality == 'standard':
				self.determine_quality()
	
	def determine_quality(self):
		"""Randomly determine crop quality when harvested"""
		import random
		roll = random.random()
		
		if roll < 0.60:  # 60% chance
			self.quality = 'standard'
		elif roll < 0.85:  # 25% chance
			self.quality = 'silver'
		elif roll < 0.97:  # 12% chance
			self.quality = 'gold'
		else:  # 3% chance
			self.quality = 'mythical'
	
	def draw_quality_indicator(self, surface, camera_offset):
		"""Draw quality indicator above plant"""
		if not self.harvestable or self.quality == 'standard':
			return
		
		# Draw sparkle effect for rare+ quality
		color = self.quality_colors[self.quality]
		
		# Position above plant
		indicator_pos = (
			self.rect.centerx - camera_offset.x,
			self.rect.top - 10 - camera_offset.y
		)
		
		# Draw small circle indicator
		pygame.draw.circle(surface, color, (int(indicator_pos[0]), int(indicator_pos[1])), 4)
		pygame.draw.circle(surface, (255, 255, 255), (int(indicator_pos[0]), int(indicator_pos[1])), 2)

class SoilLayer:
	def __init__(self, all_sprites, collision_sprites, map_path=None):
		# sprite groups
		self.all_sprites = all_sprites
		self.collision_sprites = collision_sprites
		self.soil_sprites = pygame.sprite.Group()
		self.water_sprites = pygame.sprite.Group()
		self.plant_sprites = pygame.sprite.Group()
		
		self.raining = False

		# graphics
		self.soil_surfs = import_folder_dict('graphics/soil/')
		self.water_surfs = import_folder('graphics/soil_water')

		# Create soil grid from the specific map
		self.create_soil_grid(map_path)
		self.create_hit_rects()

		# sounds
		self.hoe_sound = pygame.mixer.Sound('audio/hoe.wav')
		self.hoe_sound.set_volume(0.1)

		self.plant_sound = pygame.mixer.Sound('audio/plant.wav') 
		self.plant_sound.set_volume(0.2)

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

	def create_hit_rects(self):
		self.hit_rects = []
		for index_row, row in enumerate(self.grid):
			for index_col, cell in enumerate(row):
				if 'F' in cell:
					x = index_col * TILE_SIZE
					y = index_row * TILE_SIZE
					rect = pygame.Rect(x,y,TILE_SIZE, TILE_SIZE)
					self.hit_rects.append(rect)

	def get_hit(self, point):
		for rect in self.hit_rects:
			if rect.collidepoint(point):
				self.hoe_sound.play()

				x = rect.x // TILE_SIZE
				y = rect.y // TILE_SIZE

				if 'F' in self.grid[y][x]:
					self.grid[y][x].append('X')
					self.create_soil_tiles()
					if self.raining:
						self.water_all()

	def water(self, target_pos):
		for soil_sprite in self.soil_sprites.sprites():
			if soil_sprite.rect.collidepoint(target_pos):

				x = soil_sprite.rect.x // TILE_SIZE
				y = soil_sprite.rect.y // TILE_SIZE
				self.grid[y][x].append('W')

				pos = soil_sprite.rect.topleft
				surf = choice(self.water_surfs)
				WaterTile(pos, surf, [self.all_sprites, self.water_sprites])

	def water_all(self):
		for index_row, row in enumerate(self.grid):
			for index_col, cell in enumerate(row):
				if 'X' in cell and 'W' not in cell:
					cell.append('W')
					x = index_col * TILE_SIZE
					y = index_row * TILE_SIZE
					WaterTile((x,y), choice(self.water_surfs), [self.all_sprites, self.water_sprites])

	def remove_water(self):

		# destroy all water sprites
		for sprite in self.water_sprites.sprites():
			sprite.kill()

		# clean up the grid
		for row in self.grid:
			for cell in row:
				if 'W' in cell:
					cell.remove('W')

	def check_watered(self, pos):
		x = pos[0] // TILE_SIZE
		y = pos[1] // TILE_SIZE
		cell = self.grid[y][x]
		is_watered = 'W' in cell
		return is_watered

	def plant_seed(self, target_pos, seed):
		for soil_sprite in self.soil_sprites.sprites():
			if soil_sprite.rect.collidepoint(target_pos):
				x = soil_sprite.rect.x // TILE_SIZE
				y = soil_sprite.rect.y // TILE_SIZE

				# Check if soil is tilled AND not already planted
				if 'X' in self.grid[y][x] and 'P' not in self.grid[y][x]:
					self.plant_sound.play()
					self.grid[y][x].append('P')
					Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.check_watered)
					return True  # Planting successful
				else:
					# Already planted, planting failed
					return False
		
		return False  # No soil found at target position
		
		print(f"✗ No soil sprite found at target position")
		return False  # No soil found at target position

	def update_plants(self, dt):
		for plant in self.plant_sprites.sprites():
			# Safety check - only grow actual Plant objects
			if hasattr(plant, 'grow'):
				plant.grow(dt)

	def create_soil_tiles(self):
		self.soil_sprites.empty()
		for index_row, row in enumerate(self.grid):
			for index_col, cell in enumerate(row):
				if 'X' in cell:
					
					# tile options 
					t = 'X' in self.grid[index_row - 1][index_col]
					b = 'X' in self.grid[index_row + 1][index_col]
					r = 'X' in row[index_col + 1]
					l = 'X' in row[index_col - 1]

					tile_type = 'o'

					# all sides
					if all((t,r,b,l)): tile_type = 'x'

					# horizontal tiles only
					if l and not any((t,r,b)): tile_type = 'r'
					if r and not any((t,l,b)): tile_type = 'l'
					if r and l and not any((t,b)): tile_type = 'lr'

					# vertical only 
					if t and not any((r,l,b)): tile_type = 'b'
					if b and not any((r,l,t)): tile_type = 't'
					if b and t and not any((r,l)): tile_type = 'tb'

					# corners 
					if l and b and not any((t,r)): tile_type = 'tr'
					if r and b and not any((t,l)): tile_type = 'tl'
					if l and t and not any((b,r)): tile_type = 'br'
					if r and t and not any((b,l)): tile_type = 'bl'

					# T shapes
					if all((t,b,r)) and not l: tile_type = 'tbr'
					if all((t,b,l)) and not r: tile_type = 'tbl'
					if all((l,r,t)) and not b: tile_type = 'lrb'
					if all((l,r,b)) and not t: tile_type = 'lrt'

					SoilTile(
						pos = (index_col * TILE_SIZE,index_row * TILE_SIZE), 
						surf = self.soil_surfs[tile_type], 
						groups = [self.all_sprites, self.soil_sprites])
					
	def restore_plants(self, saved_plants, saved_grid):
		"""Restore plants after stage transition"""
		print(f"🌱 Restoring {len(saved_plants)} plants...")
		
		# Restore grid state
		for y in range(len(self.grid)):
			for x in range(len(self.grid[0])):
				if y < len(saved_grid) and x < len(saved_grid[0]):
					# Restore 'X' (tilled) and 'W' (watered) states
					if 'X' in saved_grid[y][x] and 'X' not in self.grid[y][x]:
						self.grid[y][x].append('X')
					if 'W' in saved_grid[y][x] and 'W' not in self.grid[y][x]:
						self.grid[y][x].append('W')
		
		# Recreate soil tiles
		self.create_soil_tiles()
		
		# Recreate water tiles
		for y in range(len(self.grid)):
			for x in range(len(self.grid[0])):
				if 'W' in self.grid[y][x]:
					from random import choice
					pos = (x * TILE_SIZE, y * TILE_SIZE)
					WaterTile(pos, choice(self.water_surfs), [self.all_sprites, self.water_sprites])
		
		# Restore plants
		restored_count = 0
		for plant_data in saved_plants:
			grid_x, grid_y = plant_data['pos']
			
			# Verify position is valid
			if not (0 <= grid_y < len(self.grid) and 0 <= grid_x < len(self.grid[0])):
				continue
			
			# Find soil sprite at this position
			soil_sprite = None
			for sprite in self.soil_sprites.sprites():
				if sprite.rect.x // TILE_SIZE == grid_x and sprite.rect.y // TILE_SIZE == grid_y:
					soil_sprite = sprite
					break
			
			if soil_sprite:
				# Mark as planted
				if 'P' not in self.grid[grid_y][grid_x]:
					self.grid[grid_y][grid_x].append('P')
				
				# Create plant
				plant = Plant(
					plant_data['plant_type'],
					[self.all_sprites, self.plant_sprites, self.collision_sprites],
					soil_sprite,
					self.check_watered
				)
				
				# Restore plant state
				plant.age = plant_data['age']
				plant.current_grow_time = plant_data.get('current_grow_time', 0)
				plant.harvestable = plant_data.get('harvestable', False)
				plant.quality = plant_data.get('quality', 'standard')
				
				# Update visual
				plant.image = plant.frames[plant.age]
				plant.rect = plant.image.get_rect(
					midbottom=soil_sprite.rect.midbottom + pygame.math.Vector2(0, plant.y_offset)
				)
				
				if plant.age > 0:
					plant.z = LAYERS['main']
				
				restored_count += 1
		
		print(f"✅ Restored {restored_count} plants successfully!")