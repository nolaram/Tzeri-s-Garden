import pygame
from settings import *

class IntroCutscene:
	def __init__(self):
		self.display_surface = pygame.display.get_surface()
		self.font_large = pygame.font.Font('font/LycheeSoda.ttf', 36)
		self.font_small = pygame.font.Font('font/LycheeSoda.ttf', 20)
		
		# Cutscene script with timing
		self.script = [
			{"type": "text", "content": "This land was once alive…", "duration": 3000, "fade_in": 800, "fade_out": 800},
			{"type": "text", "content": "But when care was forgotten,\nthe earth began to rot.", "duration": 3500, "fade_in": 800, "fade_out": 800},
			{"type": "text", "content": "The corruption grew—\nnot from hatred…\nbut from neglect.", "duration": 4000, "fade_in": 800, "fade_out": 800},
			{"type": "text", "content": "Then, someone returned.", "duration": 2500, "fade_in": 800, "fade_out": 800},
			{"type": "text", "content": "Not to conquer.\nNot to destroy.\nBut to heal.", "duration": 4000, "fade_in": 800, "fade_out": 800},
			{"type": "text", "content": "The land does not ask\nfor perfection…\nOnly persistence.", "duration": 4000, "fade_in": 800, "fade_out": 800},
			{"type": "text", "content": "Cleanse the farm.\nOne harvest at a time.", "duration": 3500, "fade_in": 800, "fade_out": 1500},
		]
		
		self.current_scene = 0
		self.scene_timer = 0
		self.total_duration = 0
		self.finished = False
		self.skipped = False
		
		# Calculate total duration
		for scene in self.script:
			self.total_duration += scene["duration"] + scene["fade_in"] + scene["fade_out"]
	
	def draw_text_multiline(self, text, font, color, center_pos):
		"""Draw multi-line text centered"""
		lines = text.split('\n')
		total_height = len(lines) * font.get_linesize()
		y_offset = center_pos[1] - total_height // 2
		
		for line in lines:
			text_surf = font.render(line, True, color)
			text_rect = text_surf.get_rect(center=(center_pos[0], y_offset))
			self.display_surface.blit(text_surf, text_rect)
			y_offset += font.get_linesize()
	
	def draw_skip_button(self):
		"""Draw skip button in bottom right"""
		skip_text = "Press SPACE to skip"
		skip_surf = self.font_small.render(skip_text, True, (200, 200, 200))
		skip_rect = skip_surf.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
		self.display_surface.blit(skip_surf, skip_rect)
	
	def update(self, dt, events):
		"""Update cutscene state"""
		if self.finished:
			return
		
		# Check for skip
		for event in events:
			if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
				self.skipped = True
				self.finished = True
				return
		
		# Update timer
		self.scene_timer += dt * 1000  # Convert to milliseconds
		
		# Check if current scene is done
		if self.current_scene < len(self.script):
			current = self.script[self.current_scene]
			scene_total = current["fade_in"] + current["duration"] + current["fade_out"]
			
			if self.scene_timer >= scene_total:
				self.current_scene += 1
				self.scene_timer = 0
		else:
			self.finished = True
	
	def draw(self):
		"""Draw current scene"""
		if self.current_scene >= len(self.script):
			return
		
		# Fill black background
		self.display_surface.fill((0, 0, 0))
		
		current = self.script[self.current_scene]
		fade_in = current["fade_in"]
		duration = current["duration"]
		fade_out = current["fade_out"]
		
		# Calculate alpha based on timer
		alpha = 255
		if self.scene_timer < fade_in:
			# Fading in
			alpha = int((self.scene_timer / fade_in) * 255)
		elif self.scene_timer > fade_in + duration:
			# Fading out
			fade_progress = self.scene_timer - (fade_in + duration)
			alpha = int(255 - (fade_progress / fade_out) * 255)
		
		alpha = max(0, min(255, alpha))
		
		# Draw text with alpha
		color = (alpha, alpha, alpha)
		center_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
		self.draw_text_multiline(current["content"], self.font_large, color, center_pos)
		
		# Draw skip button
		self.draw_skip_button()
		
		pygame.display.update()
	
	def run(self, dt, events):
		"""Main run method"""
		self.update(dt, events)
		self.draw()
		return self.finished