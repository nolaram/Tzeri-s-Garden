from title_screen import TitleScreen
from level import Level
from intro_cutscene import IntroCutscene  # Add this import
import pygame
from settings import *

class Game:
	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
		pygame.display.set_caption('Tzeri\'s Garden')
		self.clock = pygame.time.Clock()
		
		self.state = 'title'  # States: 'title', 'cutscene', 'playing'
		self.title_screen = TitleScreen()
		self.intro_cutscene = None
		self.level = None

	def run(self):
		while True:
			dt = self.clock.tick(60) / 1000
			events = pygame.event.get()
			
			# Check for quit
			for event in events:
				if event.type == pygame.QUIT:
					pygame.quit()
					exit()
			
			if self.state == 'title':
				result = self.title_screen.run(dt, events)
				if result == 'start':
					self.state = 'cutscene'
					self.intro_cutscene = IntroCutscene()
				elif result == 'quit':
					pygame.quit()
					exit()
			
			elif self.state == 'cutscene':
				if self.intro_cutscene.run(dt, events):
					# Cutscene finished, start game
					self.state = 'playing'
					self.level = Level()
			
			elif self.state == 'playing':
				if self.level:
					self.level.run(dt, events)
			
			pygame.display.update()

if __name__ == '__main__':
	game = Game()
	game.run()