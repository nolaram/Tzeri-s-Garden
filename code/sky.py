import pygame 
from settings import *
from support import import_folder
from sprites import Generic
from random import randint, choice

class Sky:
	def __init__(self):
		self.display_surface = pygame.display.get_surface()
		self.full_surf = pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
		self.start_color = [255,255,255]
		self.end_color = (38,101,189)
		self.initialized = False
		self.corruption_tint = pygame.Color(120, 40, 160)  # purple corruption
		self.flash_alpha = 0
		self.flash_timer = 0


	def display(self, time_system, corruption_surge=None):
		hour = time_system.hour
		minute = time_system.minute
		current_time = hour + minute / 60

		# --- base day/night factor ---
		if 6 <= current_time < 8:               # sunrise
			factor = 1 - (current_time - 6) / 2
		elif 18 <= current_time < 20:            # sunset
			factor = (current_time - 18) / 2
		elif current_time >= 20 or current_time < 6:  # night
			factor = 1
		else:
			factor = 0

		# --- base sky color ---
		day = pygame.Color(255, 255, 255)
		night = pygame.Color(38, 101, 189)

		r = day.r + (night.r - day.r) * factor
		g = day.g + (night.g - day.g) * factor
		b = day.b + (night.b - day.b) * factor

		sky_color = pygame.Color(int(r), int(g), int(b))

		# --- corruption surge effect ---
		if corruption_surge and corruption_surge.is_active():
			pulse = (pygame.time.get_ticks() % 2000) / 2000
			pulse_strength = 0.15 + 0.15 * abs(pulse - 0.5) * 2

			sky_color.r = min(255, int(sky_color.r + self.corruption_tint.r * pulse_strength))
			sky_color.g = min(255, int(sky_color.g + self.corruption_tint.g * pulse_strength))
			sky_color.b = min(255, int(sky_color.b + self.corruption_tint.b * pulse_strength))

			# --- lightning flash (rare) ---
			if randint(0, 300) == 1:
				self.flash_alpha = 180

		# --- draw base sky ---
		self.full_surf.fill(sky_color)
		self.display_surface.blit(
			self.full_surf, (0, 0),
			special_flags=pygame.BLEND_RGBA_MULT
		)

		# --- lightning flash overlay ---
		if self.flash_alpha > 0:
			flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
			flash.fill((255, 255, 255))
			flash.set_alpha(self.flash_alpha)
			self.display_surface.blit(flash, (0, 0))
			self.flash_alpha -= 15



class Drop(Generic):
	def __init__(self, surf, pos, moving, groups, z):
		
		# general setup
		super().__init__(pos, surf, groups, z)
		self.lifetime = randint(400,500)
		self.start_time = pygame.time.get_ticks()

		# moving 
		self.moving = moving
		if self.moving:
			self.pos = pygame.math.Vector2(self.rect.topleft)
			self.direction = pygame.math.Vector2(-2,4)
			self.speed = randint(200,250)

	def update(self,dt):
		# movement
		if self.moving:
			self.pos += self.direction * self.speed * dt
			self.rect.topleft = (round(self.pos.x), round(self.pos.y))

		# timer
		if pygame.time.get_ticks() - self.start_time >= self.lifetime:
			self.kill()

class Rain:
	def __init__(self, all_sprites):
		self.all_sprites = all_sprites
		self.rain_drops = import_folder('graphics/rain/drops/')
		self.rain_floor = import_folder('graphics/rain/floor/')
		self.floor_w, self.floor_h =  pygame.image.load('graphics/world/ground.png').get_size()

	def create_floor(self):
		Drop(
			surf = choice(self.rain_floor), 
			pos = (randint(0,self.floor_w),randint(0,self.floor_h)), 
			moving = False, 
			groups = self.all_sprites, 
			z = LAYERS['rain floor'])

	def create_drops(self):
		Drop(
			surf = choice(self.rain_drops), 
			pos = (randint(0,self.floor_w),randint(0,self.floor_h)), 
			moving = True, 
			groups = self.all_sprites, 
			z = LAYERS['rain drops'])

	def update(self):
		self.create_floor()
		self.create_drops()