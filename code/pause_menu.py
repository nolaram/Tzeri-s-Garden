import pygame
from settings import *

class PauseMenu:
	def __init__(self, toggle_pause):
		self.display_surface = pygame.display.get_surface()
		self.toggle_pause = toggle_pause
		self.font = pygame.font.Font('font/LycheeSoda.ttf', 28)
		self.title_font = pygame.font.Font('font/LycheeSoda.ttf', 48)

		# layout
		self.width = 640
		self.height = 420
		self.rect = pygame.Rect(SCREEN_WIDTH // 2 - self.width // 2,
							SCREEN_HEIGHT // 2 - self.height // 2,
							self.width, self.height)

		# buttons (label, rendered surf, rect, hitbox)
		labels = ['How to Play', 'Credits', 'Exit']
		self.buttons = []
		for i, label in enumerate(labels):
			surf = self.font.render(label, True, 'Black')
			rect = surf.get_rect(center=(SCREEN_WIDTH // 2, self.rect.top + 120 + i * 80))
			hit = rect.inflate(40, 18)
			self.buttons.append({'label': label, 'surf': surf, 'rect': rect, 'hit': hit})

		# subscreens
		self.active = None  # None, 'how', 'credits'

		# back button for subscreen
		self.back_surf = self.font.render('Back', True, 'Black')
		self.back_rect = self.back_surf.get_rect(midbottom=(self.rect.centerx, self.rect.bottom - 20))

		# content
		self.how_lines = [
			"Controls:",
			"Move: Arrow keys or WASD",
			"Use tool: SPACE",
			"Use seed: Left Ctrl",
			"Change tool: Q / Change seed: E",
			"Interact / Enter bed / Talk: RETURN",
			"Pause: ESC (this menu)",
			"Use the mouse to click buttons in menus."
		]

		self.credits_lines = [
			"Developed By:",
			"Altheo Mananquil",
			"Marlon Copino",
			"Lance Enagan",
			"Dustin Ong",
			"Marilou Nacional",
			"",
			"Game based from:",
			"Pydew Valley by Clearcode"
		]

	def handle_events(self, events):
		for event in events:
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					# if in subscreen go back, else close pause
					if self.active:
						self.active = None
					else:
						self.toggle_pause()

			if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				# prefer the event position; fall back to current mouse position
				pos = getattr(event, 'pos', pygame.mouse.get_pos())
				if self.active:
					# back button
					if self.back_rect.collidepoint(pos):
						self.active = None
				else:
					# main menu buttons
					for b in self.buttons:
						if b['hit'].collidepoint(pos):
							if b['label'] == 'Exit':
								self.toggle_pause()
							elif b['label'] == 'How to Play':
								self.active = 'how'
							elif b['label'] == 'Credits':
								self.active = 'credits'

	def update(self, events):
		# just process events here for clicks and keys
		self.handle_events(events)

	def draw(self):
		# dim background
		overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 160))
		self.display_surface.blit(overlay, (0, 0))

		# panel
		pygame.draw.rect(self.display_surface, 'White', self.rect, 0, 8)
		pygame.draw.rect(self.display_surface, 'Black', self.rect, 4, 8)

		# title
		title_s = self.title_font.render('Paused', True, 'Black')
		title_r = title_s.get_rect(center=(self.rect.centerx, self.rect.top + 50))
		self.display_surface.blit(title_s, title_r)

		# if subscreen active show content and back button
		if self.active == 'how':
			for i, line in enumerate(self.how_lines):
				s = self.font.render(line, True, 'Black')
				r = s.get_rect(midleft=(self.rect.left + 30, self.rect.top + 110 + i * 30))
				self.display_surface.blit(s, r)

			# back button
			pygame.draw.rect(self.display_surface, 'White', self.back_rect.inflate(20, 10), 0, 6)
			pygame.draw.rect(self.display_surface, 'Black', self.back_rect.inflate(20, 10), 2, 6)
			self.display_surface.blit(self.back_surf, self.back_rect)

		elif self.active == 'credits':
			for i, line in enumerate(self.credits_lines):
				s = self.font.render(line, True, 'Black')
				r = s.get_rect(midleft=(self.rect.left + 30, self.rect.top + 110 + i * 30))
				self.display_surface.blit(s, r)

			# back button
			pygame.draw.rect(self.display_surface, 'White', self.back_rect.inflate(20, 10), 0, 6)
			pygame.draw.rect(self.display_surface, 'Black', self.back_rect.inflate(20, 10), 2, 6)
			self.display_surface.blit(self.back_surf, self.back_rect)

		else:
			# draw buttons
			for b in self.buttons:
				# hover effect
				if b['hit'].collidepoint(pygame.mouse.get_pos()):
					pygame.draw.rect(self.display_surface, (220,220,220), b['hit'], 0, 6)
				else:
					pygame.draw.rect(self.display_surface, 'White', b['hit'], 0, 6)

				pygame.draw.rect(self.display_surface, 'Black', b['hit'], 2, 6)
				self.display_surface.blit(b['surf'], b['rect'])

			# hint
			hint = self.font.render('Use mouse to click. Press ESC to close.', True, 'Black')
			hint_r = hint.get_rect(center=(self.rect.centerx, self.rect.bottom - 40))
			self.display_surface.blit(hint, hint_r)
