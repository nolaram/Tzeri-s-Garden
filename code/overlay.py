import pygame
from settings import *

class Overlay:
	def __init__(self,player,show_objective: bool = False):

		# general setup
		self.display_surface = pygame.display.get_surface()
		self.player = player

		# imports 
		overlay_path = 'graphics/overlay/'
		self.tools_surf = {tool: pygame.image.load(f'{overlay_path}{tool}.png').convert_alpha() for tool in player.tools}
		self.seeds_surf = {seed: pygame.image.load(f'{overlay_path}{seed}.png').convert_alpha() for seed in player.seeds}

		# objective box
		try:
			self.objective_surf = pygame.image.load(f'{overlay_path}objective_textbox.png').convert_alpha()
		except Exception:
			self.objective_surf = None

		self.objective_font = pygame.font.Font('font/LycheeSoda.ttf', 20)
		self.objective_text = "Plant various seeds, grow, and sell them to the Trader"
		self.show_objective = show_objective
		self.objective_timer = 10.0
		self.button_rect = None

	def _wrap_text(self, text, font, max_width):
		words = text.split(' ')
		lines = []
		cur = ''
		for w in words:
			test = cur + (' ' if cur else '') + w
			if font.size(test)[0] <= max_width:
				cur = test
			else:
				if cur:
					lines.append(cur)
				cur = w
		if cur:
			lines.append(cur)
		return lines

	def display(self, dt: float = 0, events = None):

		# tool
		tool_surf = self.tools_surf[self.player.selected_tool]
		tool_rect = tool_surf.get_rect(midbottom = OVERLAY_POSITIONS['tool'])
		self.display_surface.blit(tool_surf,tool_rect)

		# seeds
		seed_surf = self.seeds_surf[self.player.selected_seed]
		seed_rect = seed_surf.get_rect(midbottom = OVERLAY_POSITIONS['seed'])
		self.display_surface.blit(seed_surf,seed_rect)

		# objective box (show once at level start)
		if self.show_objective and self.objective_surf:
			self.objective_timer -= dt

			# scale the objective box down to a reasonable size (50% of screen width)
			orig_w, orig_h = self.objective_surf.get_size()
			target_w = int(SCREEN_WIDTH * 0.5)
			scale = target_w / orig_w if orig_w else 1
			target_h = int(orig_h * scale)
			box_surf = pygame.transform.smoothscale(self.objective_surf, (target_w, target_h))
			box_rect = box_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
			self.display_surface.blit(box_surf, box_rect)

			# render text inside the box
			padding = 16
			max_text_width = box_rect.width - padding * 2
			lines = self._wrap_text(self.objective_text, self.objective_font, max_text_width)

			# compute starting y so text is vertically centered above the button
			button_h = 32
			text_block_height = sum(self.objective_font.size(line)[1] + 4 for line in lines) - 4
			available_height = box_rect.height - padding * 2 - button_h - 8
			start_y = box_rect.top + padding
			if text_block_height < available_height:
				start_y = box_rect.top + padding + (available_height - text_block_height) // 2

			y = start_y
			for line in lines:
				surf = self.objective_font.render(line, True, (0, 0, 0))
				rect = surf.get_rect()
				rect.centerx = box_rect.centerx
				rect.top = y
				self.display_surface.blit(surf, rect)
				y += surf.get_height() + 4

			# Dismiss button (placed inside box bottom)
			button_w, button_h = 120, 40
			button_rect = pygame.Rect(0, 0, button_w, button_h)
			button_rect.centerx = box_rect.centerx
			button_rect.bottom = box_rect.bottom - padding + 5
			self.button_rect = button_rect

			mx, my = pygame.mouse.get_pos()
			hover = button_rect.collidepoint((mx, my))
			button_color = (200, 200, 200) if not hover else (170, 170, 170)
			pygame.draw.rect(self.display_surface, button_color, button_rect, border_radius=6)
			pygame.draw.rect(self.display_surface, (0, 0, 0), button_rect, 2, border_radius=6)
			btn_surf = self.objective_font.render('Dismiss', True, (0, 0, 0))
			btn_rect = btn_surf.get_rect(center=button_rect.center)
			self.display_surface.blit(btn_surf, btn_rect)

			# click handling (dismiss on left click)
			if events is not None:
				for event in events:
					if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
						if button_rect.collidepoint(event.pos):
							self.show_objective = False
							break

			if self.objective_timer <= 0:
				self.show_objective = False