import pygame
from settings import *
from support import *
from timer import Timer

class Player(pygame.sprite.Sprite):
	def __init__(self, pos, group, collision_sprites, tree_sprites, interaction, soil_layer, toggle_shop):
		super().__init__(group)

		self.import_assets()
		self.status = 'down_idle'
		self.frame_index = 0

		# general setup
		self.image = self.animations[self.status][self.frame_index]
		self.rect = self.image.get_rect(center = pos)
		self.z = LAYERS['main']

		# movement attributes
		self.direction = pygame.math.Vector2()
		self.pos = pygame.math.Vector2(self.rect.center)
		self.target_pos = pygame.math.Vector2(self.rect.center)
		self.speed = 200

		# collision
		self.hitbox = self.rect.copy().inflate((-126,-70))
		self.collision_sprites = collision_sprites

		# timers 
		self.timers = {
			'tool use': Timer(350,self.use_tool),
			'tool switch': Timer(200),
			'seed use': Timer(350,self.use_seed),
			'seed switch': Timer(200),
		}

		# tools 
		self.tools = ['hoe','axe','water','ward']
		self.tool_index = 0
		self.selected_tool = self.tools[self.tool_index]

		# seeds 
		self.seeds = ['corn', 'tomato', 'moon_melon', 'pumpkin', 'cactus']
		self.seed_index = 0
		self.selected_seed = self.seeds[self.seed_index]

		# inventory
		self.item_inventory = {
			'wood':   0,
			'apple':  0,
			'corn':   0,
			'tomato': 0,
			'moon_melon': 0,
			'pumpkin': 0,
			'cactus': 0,
		}
		self.seed_inventory = {
		'corn': 50,
		'tomato': 50,
		'moon_melon': 50,	
		'pumpkin': 50,
		'cactus': 50
		}
		self.money = 200

		# Ward inventory
		self.ward_count = 1  # Start with 1 ward

		# Crop inventory (with quality)
		self.crop_inventory = {}

		# interaction
		self.tree_sprites = tree_sprites
		self.interaction = interaction
		self.sleep = False
		self.soil_layer = soil_layer
		self.toggle_shop = toggle_shop

		# sound
		self.watering = pygame.mixer.Sound('audio/water.mp3')
		self.watering.set_volume(0.2)

	def use_tool(self):
		# Check if player has enough energy
		if hasattr(self, 'energy_system'):
			if self.selected_tool == 'hoe':
				if self.energy_system.use_energy('hoe'):
					self.soil_layer.get_hit(self.target_pos)
			
			elif self.selected_tool == 'axe':
				if self.energy_system.use_energy('axe'):
					for tree in self.tree_sprites.sprites():
						if tree.rect.collidepoint(self.target_pos):
							tree.damage()
			
			elif self.selected_tool == 'water':
				if self.energy_system.use_energy('water'):
					self.soil_layer.water(self.target_pos)
					self.watering.play()

			elif self.selected_tool == 'ward':
				if self.ward_count > 0:
					grid_x = int(self.target_pos.x // TILE_SIZE)
					grid_y = int(self.target_pos.y // TILE_SIZE)
					if hasattr(self, 'ward_system') and self.ward_system:
						if self.ward_system.place_ward(grid_x, grid_y):
							self.ward_count -= 1
							print(f"🛡️ Ward placed! Remaining: {self.ward_count}")
		else:
			# Fallback if energy system not available
			if self.selected_tool == 'hoe':
				self.soil_layer.get_hit(self.target_pos)
			
			if self.selected_tool == 'axe':
				for tree in self.tree_sprites.sprites():
					if tree.rect.collidepoint(self.target_pos):
						tree.damage()
			
			if self.selected_tool == 'water':
				self.soil_layer.water(self.target_pos)
				self.watering.play()

	def get_target_pos(self):
		# added logic for target to follow mouse when using mouse. If gamit space, target is infront of character
		if pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:
			player_pos = pygame.math.Vector2(self.rect.center)
			corrected_mouse = pygame.mouse.get_pos() - pygame.math.Vector2(5,5)
			mouse_world_pos = corrected_mouse + self.offset
			
			distance = player_pos.distance_to(mouse_world_pos)

			if distance <= PLAYER_REACH_LIMIT:
					self.target_pos = mouse_world_pos
			else:
				direction_vec = (mouse_world_pos - player_pos).normalize()
				self.target_pos = player_pos + (direction_vec * PLAYER_REACH_LIMIT)
		else:
			if self.direction.magnitude() > 0:
				self.target_pos = self.rect.center + (self.direction.normalize() * 40)
			else:
				self.target_pos = pygame.math.Vector2(self.rect.center) + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]

	def use_seed(self):
		if self.seed_inventory[self.selected_seed] > 0:
			# Check if player has enough energy
			if hasattr(self, 'energy_system'):
				if self.energy_system.use_energy('plant'):
					# Only consume seed if planting was successful
					if self.soil_layer.plant_seed(self.target_pos, self.selected_seed):
						self.seed_inventory[self.selected_seed] -= 1
			else:
				# Fallback if energy system not available
				if self.soil_layer.plant_seed(self.target_pos, self.selected_seed):
					self.seed_inventory[self.selected_seed] -= 1

	def import_assets(self):
		self.animations = {'up': [],'down': [],'left': [],'right': [],
						'right_idle':[],'left_idle':[],'up_idle':[],'down_idle':[],
						'right_hoe':[],'left_hoe':[],'up_hoe':[],'down_hoe':[],
						'right_axe':[],'left_axe':[],'up_axe':[],'down_axe':[],
						'right_water':[],'left_water':[],'up_water':[],'down_water':[],
						'right_ward':[], 'left_ward':[], 'up_ward':[], 'down_ward':[]}

		for animation in self.animations.keys():
			full_path = 'graphics/character/' + animation
			self.animations[animation] = import_folder(full_path)
		
		# Reuse water animations for ward (since you probably don't have ward sprites yet)
		self.animations['right_ward'] = self.animations['right_ward']
		self.animations['left_ward'] = self.animations['left_ward']
		self.animations['up_ward'] = self.animations['up_ward']
		self.animations['down_ward'] = self.animations['down_ward']

	def animate(self,dt):
		self.frame_index += 4 * dt
		if self.frame_index >= len(self.animations[self.status]):
			self.frame_index = 0

		self.image = self.animations[self.status][int(self.frame_index)]

	def input(self):
		keys = pygame.key.get_pressed()
		# mouse support
		buttons = pygame.mouse.get_pressed() 

		if not self.timers['tool use'].active and not self.timers['seed use'].active and not self.sleep:

			# directions
			# up and down movement
			if keys[pygame.K_UP] or keys[pygame.K_w]:
				self.direction.y = -1
				self.status = 'up'
			elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
				self.direction.y = 1
				self.status = 'down'
			else:
				self.direction.y = 0
			# right and left movement
			if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
				self.direction.x = 1
				self.status = 'right'
			elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
				self.direction.x = -1
				self.status = 'left'
			else:
				self.direction.x = 0

			# tool use

			if buttons[0] or keys[pygame.K_SPACE] or keys[pygame.K_CAPSLOCK]:
				use_tool = False  # ADD THIS LINE
				
				# CAPS LOCK forces ward tool
				if keys[pygame.K_CAPSLOCK]:
					if self.ward_count > 0:
						# Temporarily switch to ward
						self.selected_tool = 'ward'
						use_tool = True
						self.timers['tool use'].activate()
						self.direction = pygame.math.Vector2()
						self.frame_index = 0
						self.get_target_pos()

				elif buttons[0]:
					# Calculate world mouse position
					mouse_world_pos = pygame.mouse.get_pos() + self.offset
					# Check distance betweem player and mouse
					distance = pygame.math.Vector2(self.rect.center).distance_to(mouse_world_pos)

					# cancel logic to only activate when within PLAYER_REACH_LIMIT
					if distance <= PLAYER_REACH_LIMIT:
						use_tool= True

						player_to_mouse = mouse_world_pos - pygame.math.Vector2(self.rect.center)
						if abs(player_to_mouse.x) > abs(player_to_mouse.y):
							self.status = 'right' if player_to_mouse.x > 0 else 'left'
						else:
							self.status = 'down' if player_to_mouse.y > 0 else 'up'


				elif keys[pygame.K_SPACE]:
						use_tool = True

				if use_tool and not keys[pygame.K_CAPSLOCK]:
					self.timers['tool use'].activate()
					self.direction = pygame.math.Vector2()
					self.frame_index = 0
					self.get_target_pos()

			# change tool
			if keys[pygame.K_q] and not self.timers['tool switch'].active:
				self.timers['tool switch'].activate()
				self.tool_index = (self.tool_index + 1) % len(self.tools)
				self.selected_tool = self.tools[self.tool_index]

			# seed use
			elif buttons[2] or keys[pygame.K_LCTRL]:
				use_seed = False
				if buttons[2]:
					mouse_world_pos = pygame.mouse.get_pos() + self.offset
					distance = pygame.math.Vector2(self.rect.center).distance_to(mouse_world_pos)

					if distance <= PLAYER_REACH_LIMIT:
						use_seed = True
						player_to_mouse = mouse_world_pos - pygame.math.Vector2(self.rect.center)
						if abs(player_to_mouse.x) > abs(player_to_mouse.y):
							self.status = 'right' if player_to_mouse.x > 0 else 'left'
						else:
							self.status = 'down' if player_to_mouse.y > 0 else 'up'

				elif keys[pygame.K_LCTRL]:
					use_seed = True

				if use_seed and not self.timers['seed use'].active:
					self.get_target_pos()
					self.timers['seed use'].activate()
					self.direction = pygame.math.Vector2()
					self.frame_index = 0

			# change seed 
			if keys[pygame.K_e] and not self.timers['seed switch'].active:
				self.timers['seed switch'].activate()
				self.seed_index += 1
				self.seed_index = self.seed_index if self.seed_index < len(self.seeds) else 0
				self.selected_seed = self.seeds[self.seed_index]
			# interact
			if keys[pygame.K_f] or keys[pygame.K_RETURN]:
				collided_interaction_sprite = pygame.sprite.spritecollide(self,self.interaction,False)
				if collided_interaction_sprite:
					if collided_interaction_sprite[0].name == 'Trader':
						self.toggle_shop()
					else:
						self.status = 'left_idle'
						self.sleep = True

	def get_status(self):
		
		# idle
		if self.direction.magnitude() == 0:
			self.status = self.status.split('_')[0] + '_idle'

		# tool use
		if self.timers['tool use'].active:
			self.status = self.status.split('_')[0] + '_' + self.selected_tool

	def update_timers(self):
		for timer in self.timers.values():
			timer.update()

	def collision(self, direction):
		for sprite in self.collision_sprites.sprites():
			if hasattr(sprite, 'hitbox'):
				if sprite.hitbox.colliderect(self.hitbox):
					if direction == 'horizontal':
						if self.direction.x > 0: # moving right
							self.hitbox.right = sprite.hitbox.left
						if self.direction.x < 0: # moving left
							self.hitbox.left = sprite.hitbox.right
						self.rect.centerx = self.hitbox.centerx
						self.pos.x = self.hitbox.centerx

					if direction == 'vertical':
						if self.direction.y > 0: # moving down
							self.hitbox.bottom = sprite.hitbox.top
						if self.direction.y < 0: # moving up
							self.hitbox.top = sprite.hitbox.bottom
						self.rect.centery = self.hitbox.centery
						self.pos.y = self.hitbox.centery

	def move(self,dt):

		# normalizing a vector 
		if self.direction.magnitude() > 0:
			self.direction = self.direction.normalize()

		# horizontal movement
		self.pos.x += self.direction.x * self.speed * dt
		self.hitbox.centerx = round(self.pos.x)
		self.rect.centerx = self.hitbox.centerx
		self.collision('horizontal')

		# vertical movement
		self.pos.y += self.direction.y * self.speed * dt
		self.hitbox.centery = round(self.pos.y)
		self.rect.centery = self.hitbox.centery
		self.collision('vertical')

	def update(self, dt):
		self.input()
		self.get_status()
		self.update_timers()
		if not self.timers['tool use'].active and not self.timers['seed use'].active:
			self.get_target_pos()

		self.move(dt)
		self.animate(dt)
