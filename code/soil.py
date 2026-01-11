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

		# plant growing 
		self.age = 0
		self.max_age = len(self.frames) - 1
		self.grow_speed = GROW_SPEED.get(plant_type, 0.5)
		self.harvestable = False
		
		# sprite setup
		self.image = self.frames[self.age]
		self.y_offset = -16 if plant_type == 'corn' else -8
		self.rect = self.image.get_rect(midbottom = soil.rect.midbottom + pygame.math.Vector2(0,self.y_offset))
		self.z = LAYERS['ground plant']

	def grow(self):
		if self.check_watered(self.rect.center):
			self.age += self.grow_speed

			if int(self.age) > 0:
				self.z = LAYERS['main']
				self.hitbox = self.rect.copy().inflate(-26,-self.rect.height * 0.4)

			if self.age >= self.max_age:
				self.age = self.max_age
				self.harvestable = True

			self.image = self.frames[int(self.age)]
			self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0,self.y_offset))

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
		# Use the provided map path or fallback to default
		if map_path is None:
			map_path = 'data/map.tmx'
		
		print(f"  Loading Farmable layer from: {map_path}")
		
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
					print(f"    Checking layer: '{layer.name}'")
					if layer.name.lower() == 'farmable':
						farmable_layer = layer
						print(f"    ✓ Found Farmable layer!")
						break
			
			if farmable_layer is None:
				print(f"  ⚠ Warning: No 'Farmable' layer found in {map_path}")
				print(f"  Available layers: {[l.name for l in tmx_data.visible_layers]}")
				return
			
			# Mark farmable tiles
			farmable_count = 0
			if hasattr(farmable_layer, 'tiles'):
				# Tile layer
				for x, y, surf in farmable_layer.tiles():
					if surf and 0 <= y < v_tiles and 0 <= x < h_tiles:
						self.grid[y][x].append('F')
						farmable_count += 1
			else:
				# Object layer
				for obj in farmable_layer:
					x = int(obj.x // TILE_SIZE)
					y = int(obj.y // TILE_SIZE)
					if 0 <= y < v_tiles and 0 <= x < h_tiles:
						self.grid[y][x].append('F')
						farmable_count += 1
			
			print(f"  ✓ Loaded {farmable_count} farmable tiles from '{farmable_layer.name}' layer")
			
		except Exception as e:
			print(f"  ✗ Error loading farmable layer: {e}")
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

				# Check if already planted
				if 'P' not in self.grid[y][x]:
					self.plant_sound.play()
					self.grid[y][x].append('P')
					Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.check_watered)
					return True  # Planting successful
				else:
					# Already planted, planting failed
					return False
		
		return False  # No soil found at target position

	def update_plants(self):
		for plant in self.plant_sprites.sprites():
			plant.grow()

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