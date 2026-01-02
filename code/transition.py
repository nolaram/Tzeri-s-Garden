import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class TransitionStack:
    def __init__(self, reset, player):
        # Setup
        self.display_surface = pygame.display.get_surface()
        self.reset = reset
        self.player = player

        # Stack of transitions
        # Each element: {'color': int, 'speed': int}
        self.stack = []

    def add_transition(self, color=255, speed=-2):
        """Add a new transition on top of the stack."""
        self.stack.append({'color': color, 'speed': speed})

    def play(self):
        if not self.stack:
            return

        # Get the top transition
        transition = self.stack[-1]

        # Update color
        transition['color'] += transition['speed']

        # Trigger reset when fully black
        if transition['color'] <= 0:
            transition['speed'] *= -1  # reverse
            transition['color'] = 0
            self.reset()

        # Finish transition when fully white
        if transition['color'] > 255:
            transition['color'] = 255
            self.player.sleep = False
            transition['speed'] = -2
            self.stack.pop()  # remove finished transition

        # Draw overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((transition['color'], transition['color'], transition['color']))
        self.display_surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
