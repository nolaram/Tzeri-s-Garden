import pygame
from settings import *

class StageCutscene:
	def __init__(self, stage):
		self.display_surface = pygame.display.get_surface()
		self.font_large = pygame.font.Font('font/LycheeSoda.ttf', 36)
		self.font_small = pygame.font.Font('font/LycheeSoda.ttf', 20)
		
		# Define scripts for each stage
		self.scripts = {
			'corrupted': [
				{"type": "text", "content": "Corruption - The Wounded Land", "duration": 4000, "fade_in": 2000, "fade_out": 800},
				{"type": "text", "content": "The land is sick... but not dead.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "Something terrible happened here.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "The earth remembers pain.", "duration": 3000, "fade_in": 800, "fade_out": 1000},
			],
			'stage1': [
				{"type": "text", "content": "Stage 1 - First Breath ", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "The land notices your effort.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "The earth stirs.", "duration": 2500, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "It has not been cared for\nin a long time.", "duration": 3500, "fade_in": 800, "fade_out": 1000},
			],
			'stage2': [
				{"type": "text", "content": "Stage 2 - Remembered Life", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "The land remembers\nwhat it once was.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "This place once fed many.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "It remembers gentle hands.", "duration": 3000, "fade_in": 800, "fade_out": 1000},
			],
			'stage3': [
				{"type": "text", "content": "Stage 3 - Healing Bonds", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "The corruption weakens.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "Life returns to the soil.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "Hope blooms again.", "duration": 3000, "fade_in": 800, "fade_out": 1000},
			],
			'cleansed': [
				{"type": "text", "content": "Cleansed - A New Dawn", "duration": 4000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "The land forgives.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "The land breathes freely.", "duration": 3000, "fade_in": 800, "fade_out": 800},
				{"type": "text", "content": "And this time,\nit is not alone.", "duration": 3500, "fade_in": 800, "fade_out": 1500},
			]
		}
		
		# Get script for this stage
		self.script = self.scripts.get(stage, [])
		
		self.current_scene = 0
		self.scene_timer = 0
		self.total_duration = 0
		self.finished = False
		self.skipped = False
		
		# Calculate total duration
		for scene in self.script:
			self.total_duration += scene["duration"] + scene["fade_in"] + scene["fade_out"]
		
		# Load stage-specific music
		self.music = None
		music_paths = {
			'corrupted': 'audio/corrupted_cutscene.mp3',
			'stage1': 'audio/stage1_cutscene.mp3',
			'stage2': 'audio/stage2_cutscene.mp3',
			'stage3': 'audio/stage3_cutscene.mp3',
			'cleansed': 'audio/cleansed_cutscene.mp3'
		}
		
		music_path = music_paths.get(stage)
		if music_path:
			try:
				self.music = pygame.mixer.Sound(music_path)
				self.music.set_volume(0.3)
				self.music.play(loops=-1)
			except Exception as e:
				print(f"Could not load cutscene music: {music_path} - {e}")
				self.music = None
	
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
				if self.music:
					self.music.stop()
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
			if self.music:
				self.music.stop()
	
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
	
	def run(self, dt, events):
		"""Main run method"""
		self.update(dt, events)
		self.draw()
		return self.finished
	
	def cleanup(self):
		"""Stop music when done"""
		if self.music:
			self.music.stop()