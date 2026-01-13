import pygame
from settings import *
from save_load import SaveLoadSystem

class SaveLoadMenu:
    def __init__(self, level, toggle_menu):
        self.level = level
        self.toggle_menu = toggle_menu
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 24)
        self.title_font = pygame.font.Font('font/LycheeSoda.ttf', 40)
        self.small_font = pygame.font.Font('font/LycheeSoda.ttf', 18)
        
        # Save/Load system
        self.save_system = SaveLoadSystem()
        
        # Menu state
        self.mode = 'main'  # 'main', 'save', 'load'
        self.selected_slot = 0
        self.max_slots = 5
        
        # New save name input
        self.typing_new_name = False
        self.new_save_name = ""
        
        self.renaming_slot = None  # Track which slot is being renamed
        self.rename_text = ""  
        # Scroll
        self.scroll_offset = 0
        
        # UI dimensions
        self.width = 700
        self.height = 550
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT // 2 - self.height // 2
        
        # Hover tracking
        self.hovered_button = None
        self.hovered_slot = None
    
    def handle_input(self, events):
        """Handle menu input"""
        mouse_pos = pygame.mouse.get_pos()
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                # ESC to go back or close
                if event.key == pygame.K_ESCAPE:
                    if self.typing_new_name:
                        self.typing_new_name = False
                        self.new_save_name = ""
                    elif self.mode == 'main':
                        self.toggle_menu()
                    else:
                        self.mode = 'main'
                        self.scroll_offset = 0
                
                # Text input for new save name
                elif self.typing_new_name:
                    if event.key == pygame.K_RETURN:
                        if self.new_save_name.strip():
                            self.save_game(self.new_save_name.strip())
                        self.typing_new_name = False
                        self.new_save_name = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.new_save_name = self.new_save_name[:-1]
                    else:
                        # Add character (limit to 20 chars)
                        if len(self.new_save_name) < 20 and event.unicode.isprintable():
                            self.new_save_name += event.unicode
                elif self.renaming_slot is not None:
                    if event.key == pygame.K_RETURN:
                        if self.rename_text.strip():
                            saves = self.save_system.get_save_files()
                            old_name = saves[self.renaming_slot]
                            new_name = self.rename_text.strip()
                            
                            # Rename the file
                            import os
                            old_path = f'saves/{old_name}.json'
                            new_path = f'saves/{new_name}.json'
                            if os.path.exists(old_path):
                                os.rename(old_path, new_path)
                                print(f"âœ… Renamed '{old_name}' to '{new_name}'")
                        
                        self.renaming_slot = None
                        self.rename_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.rename_text = self.rename_text[:-1]
                    else:
                        if len(self.rename_text) < 20 and event.unicode.isprintable():
                            self.rename_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Main menu buttons
                if self.mode == 'main':
                    if self.hovered_button == 'save':
                        self.mode = 'save'
                    elif self.hovered_button == 'load':
                        self.mode = 'load'
                    elif self.hovered_button == 'back':
                        self.toggle_menu()
                
                # Save menu
                elif self.mode == 'save':
                    if self.hovered_button == 'new_save':
                        self.typing_new_name = True
                        self.new_save_name = ""
                    elif self.hovered_button == 'back':
                        self.mode = 'main'
                    elif self.hovered_slot is not None:
                        # Quick save to existing slot
                        saves = self.save_system.get_save_files()
                        if 0 <= self.hovered_slot < len(saves):
                            self.renaming_slot = self.hovered_slot
                            self.rename_text = saves[self.hovered_slot]
                
                # Load menu
                elif self.mode == 'load':
                    if self.hovered_button == 'back':
                        self.mode = 'main'
                    elif self.hovered_slot is not None:
                        # Load selected slot
                        saves = self.save_system.get_save_files()
                        if 0 <= self.hovered_slot < len(saves):
                            slot_name = saves[self.hovered_slot]
                            if self.save_system.load_game(self.level, slot_name):
                                self.toggle_menu()  # Close menu on successful load
    
    def save_game(self, slot_name):
        """Save game to slot"""
        if self.save_system.save_game(self.level, slot_name):
            print(f"✅ Saved to '{slot_name}'")
            self.mode = 'main'
    
    def draw(self):
        """Draw save/load menu"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.display_surface.blit(overlay, (0, 0))
        
        # Menu background
        menu_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(self.display_surface, (30, 30, 30), menu_rect, border_radius=12)
        pygame.draw.rect(self.display_surface, (200, 200, 200), menu_rect, 3, border_radius=12)
        
        if self.mode == 'main':
            self.draw_main_menu()
        elif self.mode == 'save':
            self.draw_save_menu()
        elif self.mode == 'load':
            self.draw_load_menu()
    
    def draw_main_menu(self):
        """Draw main save/load menu"""
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_button = None
        
        # Title
        title = "Save / Load Game"
        title_surf = self.title_font.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 60))
        self.display_surface.blit(title_surf, title_rect)
        
        # Buttons
        buttons = [
            {'text': 'Save Game', 'id': 'save'},
            {'text': 'Load Game', 'id': 'load'},
            {'text': 'Back', 'id': 'back'}
        ]
        
        start_y = self.y + 150
        button_width = 350
        button_height = 70
        
        for i, button in enumerate(buttons):
            button_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - button_width // 2,
                start_y + i * 90,
                button_width,
                button_height
            )
            
            is_hovering = button_rect.collidepoint(mouse_pos)
            if is_hovering:
                self.hovered_button = button['id']
            
            # Button background
            button_color = (80, 80, 80) if is_hovering else (50, 50, 50)
            pygame.draw.rect(self.display_surface, button_color, button_rect, border_radius=10)
            pygame.draw.rect(self.display_surface, (150, 150, 150), button_rect, 3, border_radius=10)
            
            # Button text
            text_color = (255, 215, 0) if is_hovering else (255, 255, 255)
            text_surf = self.font.render(button['text'], True, text_color)
            text_rect = text_surf.get_rect(center=button_rect.center)
            self.display_surface.blit(text_surf, text_rect)
    
    def draw_save_menu(self):
        """Draw save slot selection menu"""
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_button = None
        self.hovered_slot = None
        
        # Title
        title = "Save Game"
        title_surf = self.title_font.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 40))
        self.display_surface.blit(title_surf, title_rect)
        
        # New save button
        new_save_rect = pygame.Rect(self.x + 50, self.y + 90, 200, 50)
        is_new_hover = new_save_rect.collidepoint(mouse_pos)
        if is_new_hover:
            self.hovered_button = 'new_save'
        
        new_color = (80, 120, 80) if is_new_hover else (50, 80, 50)
        pygame.draw.rect(self.display_surface, new_color, new_save_rect, border_radius=8)
        pygame.draw.rect(self.display_surface, (100, 200, 100), new_save_rect, 2, border_radius=8)
        
        new_text = self.font.render('+ New Save', True, (255, 255, 255))
        new_text_rect = new_text.get_rect(center=new_save_rect.center)
        self.display_surface.blit(new_text, new_text_rect)

        if self.renaming_slot is not None:
            input_rect = pygame.Rect(self.x + 270, self.y + 90, 350, 50)
            pygame.draw.rect(self.display_surface, (70, 70, 70), input_rect, border_radius=8)
            pygame.draw.rect(self.display_surface, (255, 200, 0), input_rect, 2, border_radius=8)
            
            # Show current rename text
            input_text = self.rename_text + "|"  # Cursor
            input_surf = self.font.render(input_text, True, (255, 255, 255))
            input_surf_rect = input_surf.get_rect(midleft=(input_rect.left + 10, input_rect.centery))
            self.display_surface.blit(input_surf, input_surf_rect)
            
            # Hint
            hint = "Renaming - Press ENTER to save, ESC to cancel"
            hint_surf = self.small_font.render(hint, True, (200, 200, 200))
            hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 155))
            self.display_surface.blit(hint_surf, hint_rect)
                
        # Text input field if typing
        if self.typing_new_name:
            input_rect = pygame.Rect(self.x + 270, self.y + 90, 350, 50)
            pygame.draw.rect(self.display_surface, (70, 70, 70), input_rect, border_radius=8)
            pygame.draw.rect(self.display_surface, (255, 215, 0), input_rect, 2, border_radius=8)
            
            # Show current text
            input_text = self.new_save_name + "|"  # Cursor
            input_surf = self.font.render(input_text, True, (255, 255, 255))
            input_surf_rect = input_surf.get_rect(midleft=(input_rect.left + 10, input_rect.centery))
            self.display_surface.blit(input_surf, input_surf_rect)
            
            # Hint
            hint = "Press ENTER to save, ESC to cancel"
            hint_surf = self.small_font.render(hint, True, (200, 200, 200))
            hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 155))
            self.display_surface.blit(hint_surf, hint_rect)
        
        # Existing saves
        saves = self.save_system.get_save_files()
        
        saves_y = self.y + 180
        save_height = 60
        
        if not saves:
            no_saves = "No saved games"
            no_saves_surf = self.font.render(no_saves, True, (150, 150, 150))
            no_saves_rect = no_saves_surf.get_rect(center=(SCREEN_WIDTH // 2, saves_y + 50))
            self.display_surface.blit(no_saves_surf, no_saves_rect)
        else:
            for i, save_name in enumerate(saves):
                slot_rect = pygame.Rect(
                    self.x + 50,
                    saves_y + i * (save_height + 10),
                    self.width - 100,
                    save_height
                )
                
                is_hovering = slot_rect.collidepoint(mouse_pos)
                if is_hovering:
                    self.hovered_slot = i
                
                slot_color = (70, 70, 70) if is_hovering else (50, 50, 50)
                pygame.draw.rect(self.display_surface, slot_color, slot_rect, border_radius=8)
                pygame.draw.rect(self.display_surface, (150, 150, 150), slot_rect, 2, border_radius=8)
                
                # Save name
                name_surf = self.font.render(save_name, True, (255, 255, 255))
                name_rect = name_surf.get_rect(midleft=(slot_rect.left + 15, slot_rect.centery - 10))
                self.display_surface.blit(name_surf, name_rect)
                
            

                hint_text = "Click to rename" if self.renaming_slot != i else "Renaming..."
                hint_surf = self.small_font.render(hint_text, True, (180, 180, 180))
                hint_rect = hint_surf.get_rect(midleft=(slot_rect.left + 15, slot_rect.centery + 12))
                self.display_surface.blit(hint_surf, hint_rect)
        
        # Back button
        back_rect = pygame.Rect(self.x + 20, self.y + self.height - 60, 120, 45)
        is_back_hover = back_rect.collidepoint(mouse_pos)
        if is_back_hover:
            self.hovered_button = 'back'
        
        back_color = (80, 80, 80) if is_back_hover else (50, 50, 50)
        pygame.draw.rect(self.display_surface, back_color, back_rect, border_radius=8)
        pygame.draw.rect(self.display_surface, (150, 150, 150), back_rect, 2, border_radius=8)
        
        back_text = self.font.render('Back', True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.display_surface.blit(back_text, back_text_rect)
    
    def draw_load_menu(self):
        """Draw load slot selection menu"""
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_button = None
        self.hovered_slot = None
        
        # Title
        title = "Load Game"
        title_surf = self.title_font.render(title, True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, self.y + 40))
        self.display_surface.blit(title_surf, title_rect)
        
        # Get saves
        saves = self.save_system.get_save_files()
        
        saves_y = self.y + 100
        save_height = 70
        
        if not saves:
            no_saves = "No saved games found"
            no_saves_surf = self.font.render(no_saves, True, (150, 150, 150))
            no_saves_rect = no_saves_surf.get_rect(center=(SCREEN_WIDTH // 2, saves_y + 100))
            self.display_surface.blit(no_saves_surf, no_saves_rect)
        else:
            for i, save_name in enumerate(saves):
                slot_rect = pygame.Rect(
                    self.x + 50,
                    saves_y + i * (save_height + 10),
                    self.width - 100,
                    save_height
                )
                
                is_hovering = slot_rect.collidepoint(mouse_pos)
                if is_hovering:
                    self.hovered_slot = i
                
                slot_color = (70, 70, 100) if is_hovering else (50, 50, 70)
                pygame.draw.rect(self.display_surface, slot_color, slot_rect, border_radius=8)
                pygame.draw.rect(self.display_surface, (100, 150, 200), slot_rect, 2, border_radius=8)
                
                # Save name
                name_surf = self.font.render(save_name, True, (255, 255, 255))
                name_rect = name_surf.get_rect(midleft=(slot_rect.left + 15, slot_rect.centery - 12))
                self.display_surface.blit(name_surf, name_rect)
                
                # Try to get timestamp
                try:
                    import json
                    filepath = f"saves/{save_name}.json"
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        timestamp = data.get('timestamp', 'Unknown time')
                        
                        time_surf = self.small_font.render(f"Saved: {timestamp}", True, (180, 180, 180))
                        time_rect = time_surf.get_rect(midleft=(slot_rect.left + 15, slot_rect.centery + 10))
                        self.display_surface.blit(time_surf, time_rect)
                except:
                    pass
        
        # Back button
        back_rect = pygame.Rect(self.x + 20, self.y + self.height - 60, 120, 45)
        is_back_hover = back_rect.collidepoint(mouse_pos)
        if is_back_hover:
            self.hovered_button = 'back'
        
        back_color = (80, 80, 80) if is_back_hover else (50, 50, 50)
        pygame.draw.rect(self.display_surface, back_color, back_rect, border_radius=8)
        pygame.draw.rect(self.display_surface, (150, 150, 150), back_rect, 2, border_radius=8)
        
        back_text = self.font.render('Back', True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.display_surface.blit(back_text, back_text_rect)