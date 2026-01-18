import os
import sys

# This forces the "Working Directory" to be the folder containing Tzeris_Garden.exe
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    # If running normally, it sets the directory to the project root
    # Adjust the '..' depending on if main.py is in a subfolder or root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if os.path.basename(os.getcwd()) == 'code':
        os.chdir('..')


from title_screen import TitleScreen
from level import Level
from intro_cutscene import IntroCutscene
import pygame
from settings import *

class Game:
	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
		pygame.display.set_caption('Tzeri\'s Garden')
		self.clock = pygame.time.Clock()
		
		self.state = 'intro'  # States: 'intro', 'title', 'playing'
		self.intro_cutscene = IntroCutscene('intro')
		self.title_screen = None
		self.level = None

	def run(self):
		while True:
			dt = self.clock.tick(60) / 1000
			events = pygame.event.get()
			
			# Check for quit
			for event in events:
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
			
			if self.state == 'intro':
				if self.intro_cutscene.run(dt, events):
					# Intro finished, show title
					self.state = 'title'
					self.title_screen = TitleScreen()
			
			elif self.state == 'title':
				result = self.title_screen.run(dt, events)
				if result == 'start':
					# Title finished, start game
					self.state = 'playing'
					self.level = Level()
				elif result == 'quit':
					pygame.quit()
					exit()
			
			elif self.state == 'playing':
				if self.level:
					self.level.run(dt, events)
			
			pygame.display.update()

if __name__ == '__main__':
	game = Game()
	game.run()