import pygame, sys, os
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
os.chdir(ROOT_DIR)
sys.path.append(str(ROOT_DIR / 'code'))
from settings import *
from level import Level
from title_screen import TitleScreen


class Game:
	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
		pygame.display.set_caption("Tzeri's Garden")
		self.clock = pygame.time.Clock()

		# start with title screen
		self.title_screen = TitleScreen()
		self.level = None
		self.state = 'title'  # 'title' or 'playing'

	def run(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
  
			dt = self.clock.tick() / 1000

			# Title state
			if self.state == 'title':
				self.title_screen.update(dt)
				self.title_screen.draw()
				if self.title_screen.done:
					# create the level and switch state
					self.level = Level()
					self.state = 'playing'

			# Playing state
			else:
				self.level.run(dt)

			pygame.display.update()

if __name__ == '__main__':
	game = Game()
	game.run()