import json
import os
from datetime import datetime

class SaveLoadSystem:
    def __init__(self):
        self.save_folder = "saves"
        self.ensure_save_folder()
    
    def ensure_save_folder(self):
        """Create saves folder if it doesn't exist"""
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
    
    def get_save_files(self):
        """Get list of all save files"""
        if not os.path.exists(self.save_folder):
            return []
        
        saves = []
        for filename in os.listdir(self.save_folder):
            if filename.endswith('.json'):
                saves.append(filename[:-5])  # Remove .json extension
        return sorted(saves)
    
    def save_game(self, level, slot_name="autosave"):
        """Save the entire game state"""
        try:
            save_data = {
                # Metadata
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'version': '1.0',
                
                # Player data
                'player': self._save_player(level.player),
                
                # Time system
                'time': self._save_time_system(level.time_system),
                
                # Energy and Health
                'energy': {
                    'current': level.energy_system.current_energy,
                    'max': level.energy_system.max_energy
                },
                'health': {
                    'current': level.health_system.current_health,
                    'max': level.health_system.max_health
                },
                
                # Quest system
                'quests': self._save_quest_system(level.quest_manager),
                
                # Farm cleansing progress
                'cleansing': {
                    'stage': level.cleanse_stage,
                    'points': level.cleanse_points
                },
                
                # Soil and plants
                'soil': self._save_soil_layer(level.soil_layer),
                
                # Corruption system
                'corruption': self._save_corruption(level.corruption_spread),
                
                # Ward system
                'wards': self._save_wards(level.ward_system),
                
                # Trader stock
                'trader': {
                    'stock': level.trader_menu.stock,
                    'stock_timer': level.trader_menu.stock_timer
                },
                
                # Weather
                'weather': {
                    'raining': level.raining
                }
            }
            
            # Save to file
            filepath = os.path.join(self.save_folder, f"{slot_name}.json")
            with open(filepath, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"✅ Game saved to '{slot_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save game: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_game(self, level, slot_name="autosave"):
        """Load game state and apply to level"""
        try:
            filepath = os.path.join(self.save_folder, f"{slot_name}.json")
            
            if not os.path.exists(filepath):
                print(f"❌ Save file '{slot_name}' not found")
                return False
            
            with open(filepath, 'r') as f:
                save_data = json.load(f)
            
            print(f"📂 Loading save from {save_data.get('timestamp', 'unknown time')}...")
            
            # Load player data
            self._load_player(level.player, save_data['player'])
            
            # Load time system
            self._load_time_system(level.time_system, save_data['time'])
            
            # Load energy and health
            level.energy_system.current_energy = save_data['energy']['current']
            level.energy_system.max_energy = save_data['energy']['max']
            level.health_system.current_health = save_data['health']['current']
            level.health_system.max_health = save_data['health']['max']
            
            # Load quest system
            self._load_quest_system(level.quest_manager, save_data['quests'])
            
            # Load cleansing progress
            level.cleanse_stage = save_data['cleansing']['stage']
            level.cleanse_points = save_data['cleansing']['points']
            
            # Reload map for current stage
            level.setup()
            
            # Load soil and plants
            self._load_soil_layer(level.soil_layer, save_data['soil'])
            
            # Load corruption
            self._load_corruption(level.corruption_spread, save_data['corruption'])
            
            # Load wards
            self._load_wards(level.ward_system, save_data['wards'], level.all_sprites)
            
            # Load trader stock
            level.trader_menu.stock = save_data['trader']['stock']
            level.trader_menu.stock_timer = save_data['trader']['stock_timer']
            
            # Load weather
            level.raining = save_data['weather']['raining']
            level.soil_layer.raining = level.raining
            
            print(f"✅ Game loaded from '{slot_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load game: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_save(self, slot_name):
        """Delete a save file"""
        try:
            filepath = os.path.join(self.save_folder, f"{slot_name}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ Deleted save '{slot_name}'")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to delete save: {e}")
            return False
    
    # === PRIVATE SAVE METHODS ===
    
    def _save_player(self, player):
        """Save player state"""
        return {
            'position': {
                'x': player.rect.centerx,
                'y': player.rect.centery
            },
            'money': player.money,
            'ward_count': player.ward_count,
            'item_inventory': player.item_inventory,
            'seed_inventory': player.seed_inventory,
            'crop_inventory': player.crop_inventory,
            'selected_tool_index': player.tool_index,
            'selected_seed_index': player.seed_index
        }
    
    def _save_time_system(self, time_system):
        """Save time system state"""
        return {
            'day': time_system.day,
            'hour': time_system.hour,
            'minute': time_system.minute
        }
    
    def _save_quest_system(self, quest_manager):
        """Save quest progress"""
        return {
            'active_quest_id': quest_manager.active_quest.id if quest_manager.active_quest else None,
            'completed_quest_ids': [q.id for q in quest_manager.completed_quests],
            'quest_progress': {
                q.id: {
                    'progress': q.progress,
                    'completed': q.completed,
                    'claimed': q.claimed
                } for q in quest_manager.all_quests
            },
            'quest_ui_visible': quest_manager.quest_ui_visible
        }
    
    def _save_soil_layer(self, soil_layer):
        """Save soil and plant state"""
        # Save grid state (F, X, W, P markers)
        grid_state = []
        for y, row in enumerate(soil_layer.grid):
            grid_row = []
            for x, cell in enumerate(row):
                grid_row.append(list(cell))  # Convert to list for JSON
            grid_state.append(grid_row)
        
        # Save plants
        plants = []
        for plant in soil_layer.plant_sprites.sprites():
            plant_data = {
                'plant_type': plant.plant_type,
                'age': plant.age,
                'current_grow_time': plant.current_grow_time,
                'harvestable': plant.harvestable,
                'quality': plant.quality,
                'grid_x': plant.rect.x // 64,  # TILE_SIZE
                'grid_y': plant.rect.y // 64
            }
            plants.append(plant_data)
        
        return {
            'grid': grid_state,
            'plants': plants
        }
    
    def _save_corruption(self, corruption_spread):
        """Save corruption state"""
        if not corruption_spread:
            return {'tiles': []}
        
        return {
            'tiles': list(corruption_spread.corrupted_tiles),
            'spread_timer': corruption_spread.spread_timer
        }
    
    def _save_wards(self, ward_system):
        """Save ward positions"""
        wards = []
        for ward in ward_system.ward_sprites.sprites():
            wards.append({
                'grid_x': ward.grid_x,
                'grid_y': ward.grid_y,
                'protection_radius': ward.protection_radius
            })
        return {'wards': wards}
    
    # === PRIVATE LOAD METHODS ===
    
    def _load_player(self, player, data):
        """Load player state"""
        player.rect.centerx = data['position']['x']
        player.rect.centery = data['position']['y']
        player.pos = pygame.math.Vector2(player.rect.center)
        player.hitbox.center = player.rect.center
        
        player.money = data['money']
        player.ward_count = data['ward_count']
        player.item_inventory = data['item_inventory']
        player.seed_inventory = data['seed_inventory']
        player.crop_inventory = data['crop_inventory']
        player.tool_index = data['selected_tool_index']
        player.seed_index = data['selected_seed_index']
        player.selected_tool = player.tools[player.tool_index]
        player.selected_seed = player.seeds[player.seed_index]
    
    def _load_time_system(self, time_system, data):
        """Load time system state"""
        time_system.day = data['day']
        time_system.hour = data['hour']
        time_system.minute = data['minute']
        time_system.update_day_night()
    
    def _load_quest_system(self, quest_manager, data):
        """Load quest progress"""
        # Restore quest progress
        for quest in quest_manager.all_quests:
            if quest.id in data['quest_progress']:
                quest_data = data['quest_progress'][quest.id]
                quest.progress = quest_data['progress']
                quest.completed = quest_data['completed']
                quest.claimed = quest_data['claimed']
        
        # Set active quest
        if data['active_quest_id'] is not None:
            quest_manager.active_quest = quest_manager.all_quests[data['active_quest_id']]
        else:
            quest_manager.active_quest = None
        
        # Restore completed quests
        quest_manager.completed_quests = [
            q for q in quest_manager.all_quests if q.id in data['completed_quest_ids']
        ]
        
        quest_manager.quest_ui_visible = data['quest_ui_visible']
    
    def _load_soil_layer(self, soil_layer, data):
        """Load soil and plant state"""
        # Clear existing
        for sprite in soil_layer.soil_sprites.sprites():
            sprite.kill()
        for sprite in soil_layer.water_sprites.sprites():
            sprite.kill()
        for sprite in soil_layer.plant_sprites.sprites():
            sprite.kill()
        
        # Restore grid state
        for y in range(len(soil_layer.grid)):
            for x in range(len(soil_layer.grid[0])):
                if y < len(data['grid']) and x < len(data['grid'][0]):
                    soil_layer.grid[y][x] = data['grid'][y][x]
        
        # Recreate soil tiles
        soil_layer.create_soil_tiles()
        
        # Recreate water tiles
        from random import choice
        for y, row in enumerate(soil_layer.grid):
            for x, cell in enumerate(row):
                if 'W' in cell:
                    pos = (x * 64, y * 64)
                    from soil import WaterTile
                    WaterTile(pos, choice(soil_layer.water_surfs), 
                             [soil_layer.all_sprites, soil_layer.water_sprites])
        
        # Recreate plants
        from soil import Plant
        for plant_data in data['plants']:
            grid_x = plant_data['grid_x']
            grid_y = plant_data['grid_y']
            
            # Find soil sprite
            soil_sprite = None
            for sprite in soil_layer.soil_sprites.sprites():
                if sprite.rect.x // 64 == grid_x and sprite.rect.y // 64 == grid_y:
                    soil_sprite = sprite
                    break
            
            if soil_sprite:
                plant = Plant(
                    plant_data['plant_type'],
                    [soil_layer.all_sprites, soil_layer.plant_sprites, soil_layer.collision_sprites],
                    soil_sprite,
                    soil_layer.check_watered
                )
                
                plant.age = plant_data['age']
                plant.current_grow_time = plant_data['current_grow_time']
                plant.harvestable = plant_data['harvestable']
                plant.quality = plant_data['quality']
                
                # Update visual
                plant.image = plant.frames[plant.age]
                plant.rect = plant.image.get_rect(
                    midbottom=soil_sprite.rect.midbottom + pygame.math.Vector2(0, plant.y_offset)
                )
                
                if plant.age > 0:
                    from settings import LAYERS
                    plant.z = LAYERS['main']
    
    def _load_corruption(self, corruption_spread, data):
        """Load corruption state"""
        if not corruption_spread:
            return
        
        # Clear existing
        corruption_spread.clear_all_corruption()
        
        # Restore corrupted tiles
        for tile_x, tile_y in data['tiles']:
            corruption_spread.add_corrupted_tile(tile_x, tile_y)
        
        corruption_spread.spread_timer = data['spread_timer']
    
    def _load_wards(self, ward_system, data, all_sprites):
        """Load ward positions"""
        # Clear existing wards
        for ward in ward_system.ward_sprites.sprites():
            ward.kill()
        
        # Recreate wards
        from ward_system import Ward
        for ward_data in data['wards']:
            pos = (ward_data['grid_x'] * 64, ward_data['grid_y'] * 64)
            ward = Ward(pos, [all_sprites, ward_system.ward_sprites])
            ward.grid_x = ward_data['grid_x']
            ward.grid_y = ward_data['grid_y']
            ward.protection_radius = ward_data['protection_radius']


import pygame