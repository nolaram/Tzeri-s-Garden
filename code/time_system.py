import pygame
from settings import *

class TimeSystem:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 20)
        self.large_font = pygame.font.Font('font/LycheeSoda.ttf', 24)
        
        # Time settings
        self.day = 1
        self.hour = 6  # Start at 6 AM
        self.minute = 0
        
        # Time progression (in real seconds per in-game minute)
        self.seconds_per_minute = 1.0  # 1 real second = 1 game minute
        self.time_accumulator = 0
        
        # Day/night cycle
        self.is_night = False
        self.night_start_hour = 20  # 8 PM
        self.night_end_hour = 6     # 6 AM
        
    def update(self, dt, corruption_surge=None):
        """Update time progression"""
        self.time_accumulator += dt
        
        # Progress time when accumulator reaches threshold
        if self.time_accumulator >= self.seconds_per_minute:
            self.time_accumulator = 0
            self.minute += 1
            
            # Handle minute overflow
            if self.minute >= 60:
                self.minute = 0
                self.hour += 1
                
                # Try to trigger corruption surge each hour (passing current day)
                if corruption_surge:
                    corruption_surge.try_trigger_surge(self.hour, self.day)
                
                # Handle hour overflow (new day)
                if self.hour >= 24:
                    self.hour = 0
                    self.day += 1
            
            # Update day/night status
            self.update_day_night()
    
    def update_day_night(self):
        """Check if it's currently night time"""
        if self.hour >= self.night_start_hour or self.hour < self.night_end_hour:
            self.is_night = True
        else:
            self.is_night = False
    
    def get_time_string(self):
        """Get formatted time string (12-hour format)"""
        hour_12 = self.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        am_pm = "AM" if self.hour < 12 else "PM"
        return f"{hour_12}:{self.minute:02d} {am_pm}"
    
    def get_day_string(self):
        """Get formatted day string"""
        return f"Day {self.day}"
    
    def get_time_period(self):
        """Get the time period name"""
        if 6 <= self.hour < 12:
            return "Morning"
        elif 12 <= self.hour < 17:
            return "Afternoon"
        elif 17 <= self.hour < 20:
            return "Evening"
        else:
            return "Night"
    
    def draw(self):
        """Draw time and day display in top-left corner"""
        # Position settings
        padding = 10
        x_pos = padding
        y_pos = padding
        
        # Draw day
        day_text = self.get_day_string()
        day_surf = self.large_font.render(day_text, False, 'White')
        day_rect = day_surf.get_rect(topleft=(x_pos, y_pos))
        
        # Background for day
        day_bg_rect = day_rect.inflate(10, 6)
        pygame.draw.rect(self.display_surface, 'Black', day_bg_rect, 0, 4)
        pygame.draw.rect(self.display_surface, 'White', day_bg_rect, 2, 4)
        self.display_surface.blit(day_surf, day_rect)
        
        # Draw time
        time_text = self.get_time_string()
        time_surf = self.font.render(time_text, False, 'White')
        time_rect = time_surf.get_rect(topleft=(x_pos, day_bg_rect.bottom + 5))
        
        # Background for time
        time_bg_rect = time_rect.inflate(10, 6)
        pygame.draw.rect(self.display_surface, 'Black', time_bg_rect, 0, 4)
        pygame.draw.rect(self.display_surface, 'White', time_bg_rect, 2, 4)
        self.display_surface.blit(time_surf, time_rect)
        
        # Draw time period (Morning/Afternoon/Evening/Night)
        period_text = self.get_time_period()
        period_color = (255, 255, 150) if not self.is_night else (150, 150, 255)
        period_surf = self.font.render(period_text, False, period_color)
        period_rect = period_surf.get_rect(topleft=(x_pos, time_bg_rect.bottom + 5))
        
        # Background for period
        period_bg_rect = period_rect.inflate(10, 6)
        pygame.draw.rect(self.display_surface, 'Black', period_bg_rect, 0, 4)
        pygame.draw.rect(self.display_surface, period_color, period_bg_rect, 2, 4)
        self.display_surface.blit(period_surf, period_rect)
    
    def advance_to_next_day(self):
        """Advance time to the start of next day (used when sleeping)"""
        self.day += 1
        self.hour = 6
        self.minute = 0
        self.time_accumulator = 0
        self.update_day_night()
    
    def set_time(self, hour, minute=0):
        """Set specific time (useful for testing or events)"""
        self.hour = hour % 24
        self.minute = minute % 60
        self.time_accumulator = 0
        self.update_day_night()