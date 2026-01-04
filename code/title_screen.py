import pygame
from settings import *
from pathlib import Path

ASSET_PATH = Path('graphics/overlay/title_screen.png')

class TitleScreen:
    def __init__(self):
        pygame.font.init()
        self.display_surface = pygame.display.get_surface()
        self.screen_rect = self.display_surface.get_rect()
        self.title_font = pygame.font.Font('font/LycheeSoda.ttf', 72)
        self.subtitle_font = pygame.font.Font('font/LycheeSoda.ttf', 28)

        # load the title image inserted by the user (required)
        if not ASSET_PATH.exists():
            raise FileNotFoundError(f"Title image not found: {ASSET_PATH}")

        self.image = pygame.image.load(str(ASSET_PATH)).convert_alpha()
        # scale to fit screen
        self.image = pygame.transform.smoothscale(self.image, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # fade control
        self.fading = False
        self.done = False
        self.fade_alpha = 0
        self.fade_speed = 400  # alpha per second

        # title music (use user-provided file at audio/title_music.mp3)
        self.music_path = Path('audio/title_music.mp3')
        if not self.music_path.exists():
            print(f"Title music not found: {self.music_path}")
            self.music = None
        else:
            try:
                self.music = pygame.mixer.Sound(str(self.music_path))
                self.music.set_volume(0.2)
                self.music.play(loops = -1)
            except Exception as e:
                # fail gracefully if audio can't be played
                print(f"Title music error: {e}")
                self.music = None



    def input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not self.fading:
            self.fading = True

    def update(self, dt):
        self.input()

        if self.fading:
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.done = True
                # stop the title music when transition finishes
                if self.music:
                    try:
                        self.music.stop()
                    except Exception:
                        pass


    def draw(self):
        self.display_surface.blit(self.image, (0, 0))

        # draw hint if not fading
        if not self.fading:
            sub_s = self.subtitle_font.render('Press SPACE to start', True, (240, 240, 240))
            sub_rect = sub_s.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
            self.display_surface.blit(sub_s, sub_rect)

        # draw fade surface
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surf.set_alpha(int(self.fade_alpha))
            fade_surf.fill((0, 0, 0))
            self.display_surface.blit(fade_surf, (0, 0))


