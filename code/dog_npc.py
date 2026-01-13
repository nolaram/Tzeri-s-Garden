"""
DOG NPC - HASH MAP PATHFINDING IMPLEMENTATION
==============================================
This module demonstrates hash map (dictionary) usage for:
1. A* pathfinding algorithm (open/closed sets as hash maps)
2. Corruption avoidance using spatial hash lookups
3. Behavior state management
4. Efficient tile checking and path caching

Hash Maps provide O(1) lookup time vs O(n) for lists!
"""

import pygame
from settings import *
from support import import_folder
from random import randint, choice
import math

class DogNPC(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, corruption_system):
        super().__init__(groups)
        
        self.import_assets()
        self.status = 'down'
        self.frame_index = 0
        self.current_animation = 'down'

        # ==================== VISUAL SETUP ====================
        # Simple dog sprite (you can replace with actual asset)
        self.image = self.create_dog_sprite()
        self.rect = self.image.get_rect(center=pos)
        self.z = LAYERS['main']
        self.hitbox = self.rect.copy().inflate(-20, -10)
        
        # ==================== REFERENCES ====================
        self.collision_sprites = collision_sprites
        self.corruption_system = corruption_system
        self.display_surface = pygame.display.get_surface()
        
        # ==================== MOVEMENT ====================
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 100  # pixels per second
        self.direction = pygame.math.Vector2(0, 0)
        
        # ==================== HASH MAP 1: BEHAVIOR STATE MACHINE ====================
        # Using hash map to store different behavior states and their properties
        # O(1) lookup for current behavior
        self.behavior_states = {
            'wandering': {
                'speed_multiplier': 1.0,
                'path_update_interval': 8.0,  # Update path every 3 seconds
                'max_distance': 500  # Max distance from spawn
            },
            'following': {
                'speed_multiplier': 1.2,
                'path_update_interval': 0.5,  # Update more frequently when following
                'follow_distance': 100  # Stay within 100 pixels of player
            },
            'circling': {
                'speed_multiplier': 0.8,
                'circle_radius': 80,
                'circle_speed': 2.0  # radians per second
            },
            'idle': {
                'speed_multiplier': 0.0,
                'idle_duration': 2.0
            }
        }
        
        self.current_behavior = 'wandering'
        self.behavior_timer = 0
        
        # ==================== HASH MAP 2: PATHFINDING STRUCTURES ====================
        self.current_path = []  # List of (x, y) positions
        self.path_index = 0
        self.pathfinding_cooldown = 0
        
        # Hash maps for A* algorithm (explained in pathfinding method)
        self.open_set = {}      # Hash map: position -> f_score
        self.closed_set = {}    # Hash map: position -> True/False
        self.came_from = {}     # Hash map: position -> previous position
        self.g_score = {}       # Hash map: position -> cost from start
        self.f_score = {}       # Hash map: position -> estimated total cost
        
        # ==================== HASH MAP 3: VISITED TILES (MEMORY) ====================
        # Remember where we've been to avoid getting stuck
        # O(1) to check if tile has been visited
        self.visited_tiles = {}  # Hash map: (grid_x, grid_y) -> timestamp
        self.visit_memory_duration = 10.0  # Forget after 10 seconds
        
        # ==================== HASH MAP 4: TILE CACHE ====================
        # Cache tile safety checks to avoid repeated calculations
        # O(1) lookup vs recalculating each time
        self.tile_safety_cache = {}  # Hash map: (grid_x, grid_y) -> is_safe
        self.cache_expiry = {}  # Hash map: (grid_x, grid_y) -> expiry_time
        self.cache_duration = 5.0  # Cache valid for 5 seconds
        
        # ==================== FEEDING SYSTEM ====================
        self.feed_count = 0
        self.max_feeds_to_befriend = 3
        self.is_befriended = False
        self.feed_cooldown = 0
        self.feed_cooldown_duration = 1.0
        
        # Interaction
        self.interaction_range = 60
        
        # ==================== CIRCLING BEHAVIOR ====================
        self.circle_angle = 0
        self.circle_center = pygame.math.Vector2(pos)
        
        # ==================== SPAWN LOCATION ====================
        self.spawn_pos = pygame.math.Vector2(pos)
        
        # ==================== ANIMATION ====================
        self.animation_timer = 0
        self.animation_frame = 0
        
        # Sound (optional - will fail gracefully if not found)
        try:
            self.bark_sound = pygame.mixer.Sound('audio/dog_bark.wav')
            self.bark_sound.set_volume(0.3)
        except:
            self.bark_sound = None
        
        print(f"🐕 Dog NPC spawned at {pos}")
    def create_dog_sprite(self):
    # Return the first frame of the default direction (down)
        if 'down' in self.animations and len(self.animations['down']) > 0:
            return self.animations['down'][0]
        
        # Fallback: check other directions if 'down' doesn't exist
        for direction in ['up', 'left', 'right']:
            if direction in self.animations and len(self.animations[direction]) > 0:
                return self.animations[direction][0]
        
        # Final fallback: create a placeholder surface
        placeholder = pygame.Surface((64, 64))
        placeholder.fill((150, 100, 50))  # Brown color for dog
        return placeholder
    
    def import_assets(self):
        self.animations = {
            'up': [],
            'down': [],
            'left': [],
            'right': [],
            'idle_up': [],
            'idle_down': [],
            'idle_left': [],
            'idle_right': [],
        }
        
        try:
            # Load all animations from folders (both movement and idle)
            for animation in self.animations.keys():
                full_path = f'graphics/dog/{animation}'
                print(f"🔍 Trying to load: {full_path}")
                
                try:
                    frames = import_folder(full_path)
                    if frames:
                        self.animations[animation] = frames
                        print(f"✅ Loaded {len(frames)} frames for {animation}")
                    else:
                        print(f"⚠️ No frames found in {full_path}")
                        # If idle folder is empty, use first frame of movement
                        if 'idle_' in animation:
                            direction = animation.replace('idle_', '')
                            if self.animations.get(direction):
                                self.animations[animation] = [self.animations[direction][0]]
                                print(f"📝 Using fallback for {animation}")
                except Exception as e:
                    print(f"❌ Error loading {full_path}: {e}")
                    # Fallback for idle: use first frame of movement
                    if 'idle_' in animation:
                        direction = animation.replace('idle_', '')
                        if direction in self.animations and self.animations[direction]:
                            self.animations[animation] = [self.animations[direction][0]]
            
            print("✅ Dog animations loaded successfully!")
            print(f"📊 Animation summary: {[(k, len(v)) for k, v in self.animations.items()]}")
            
        except Exception as e:
            print(f"⚠️ Could not load dog animations: {e}")
            print("Using fallback sprites...")
            for direction in ['up', 'down', 'left', 'right']:
                frames = []
                for i in range(4):
                    frames.append(self.create_fallback_sprite(direction, i))
                self.animations[direction] = frames
                self.animations[f'idle_{direction}'] = [frames[0]]

    def create_fallback_sprite(self, direction, frame):
        sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
        base_color = 139 - (frame * 10)
        body_color = (base_color, 90, 43)
        pygame.draw.ellipse(sprite, body_color, (4, 8, 24, 16))   
        pygame.draw.circle(sprite, body_color, (16, 8), 8)

        if direction == 'up':
            pygame.draw.circle(sprite, (0, 0, 0), (13, 5), 2)
            pygame.draw.circle(sprite, (0, 0, 0), (19, 5), 2)
            pygame.draw.circle(sprite, (0, 0, 0), (16, 3), 2)
        elif direction == 'down':
            pygame.draw.circle(sprite, (0, 0, 0), (13, 9), 2)
            pygame.draw.circle(sprite, (0, 0, 0), (16, 12), 2)
        elif direction == 'left':
            pygame.draw.circle(sprite, (0, 0, 0), (11, 7), 2)
            pygame.draw.circle(sprite, (0, 0, 0), (17, 7), 2)
            pygame.draw.circle(sprite, (0, 0, 0), (8, 8), 2)
        elif direction == 'right':
            pygame.draw.circle(sprite, (0, 0, 0), (15, 7), 2)
            pygame.draw.circle(sprite, (0, 0, 0), (21, 7), 2)
            pygame.draw.circle(sprite, (0, 0, 0), (24, 8), 2)

        ear_color = (101, 67, 33)
        pygame.draw.ellipse(sprite, ear_color, (8, 2, 6, 10))
        pygame.draw.ellipse(sprite, ear_color, (18, 2, 6, 10))
        pygame.draw.arc(sprite, ear_color, (20, 10, 10, 10), 0, 3.14, 3)
        leg_offset = frame % 2
        pygame.draw.line(sprite, ear_color, (10, 24), (10 + leg_offset, 30), 3)
        pygame.draw.line(sprite, ear_color, (22, 24), (22 - leg_offset, 30), 3)

        return sprite
    
    def animate(self, dt):
    # Check if dog is moving
        is_moving = self.direction.magnitude() > 0.1
        
        if is_moving:
            # Moving: cycle through movement animation
            anim_key = self.status
            animation_speed = 6  # Fast running animation
        else:
            # Idle: cycle through idle animation (tail wagging)
            anim_key = f'idle_{self.status}'
            animation_speed = 3  # Slower tail wagging animation
            
            # Fallback if idle animation doesn't exist
            if anim_key not in self.animations or len(self.animations[anim_key]) == 0:
                anim_key = self.status
                animation_speed = 1  # Very slow if using movement frames
        
        # Reset frame index if switching animations or if out of bounds
        if not hasattr(self, 'current_animation') or self.current_animation != anim_key:
            self.frame_index = 0
            self.current_animation = anim_key
        
        # Update frame index
        self.frame_index += animation_speed * dt
        
        # Check if animation exists and has frames
        if anim_key in self.animations and len(self.animations[anim_key]) > 0:
            # Wrap frame index
            if self.frame_index >= len(self.animations[anim_key]):
                self.frame_index = 0
            
            self.image = self.animations[anim_key][int(self.frame_index)]

        
    def get_status(self):
        if self.direction.magnitude() == 0:
            return
        
        if abs(self.direction.x) > abs(self.direction.y):
            if self.direction.x > 0:
                self.status = 'right'

            else:
                self.status = 'left'
        else:
            if self.direction.y > 0:
                self.status = 'down'
            else:
                self.status = 'up'
    
    
    def can_feed(self, player):
        """Check if player is close enough to feed"""
        if self.feed_cooldown > 0:
            return False
        
        distance = self.pos.distance_to(pygame.math.Vector2(player.rect.center))
        return distance <= self.interaction_range
    
    def feed(self, crop_name):
        """Feed the dog with a crop"""
        if self.feed_cooldown > 0:
            return False
        
        self.feed_count += 1
        self.feed_cooldown = self.feed_cooldown_duration
        
        print(f"🐕 Dog fed! ({self.feed_count}/{self.max_feeds_to_befriend})")
        
        # Play sound if available
        if self.bark_sound:
            self.bark_sound.play()
        
        # Check if befriended
        if self.feed_count >= self.max_feeds_to_befriend and not self.is_befriended:
            self.is_befriended = True
            self.current_behavior = 'following'
            print("🐕 Dog is now your companion! 💚")
            return True
        
        return False
    
    # ==================== HASH MAP PATHFINDING: A* ALGORITHM ====================
    def find_path_astar(self, start_pos, goal_pos):
        """
        A* pathfinding algorithm using HASH MAPS for efficiency
        
        WHY HASH MAPS?
        - Open set: O(1) to check if node is in set (vs O(n) for list)
        - Closed set: O(1) to check if node was visited
        - Came from: O(1) to reconstruct path
        - G/F scores: O(1) to lookup/update scores
        
        Time Complexity: O(b^d) where b=branching factor, d=depth
        Space Complexity: O(b^d) - hash maps store visited nodes
        """
        
        # Convert positions to grid coordinates
        start_grid = (int(start_pos[0] // TILE_SIZE), int(start_pos[1] // TILE_SIZE))
        goal_grid = (int(goal_pos[0] // TILE_SIZE), int(goal_pos[1] // TILE_SIZE))
        
        # Clear previous pathfinding data (reset hash maps)
        self.open_set.clear()      # O(1) clear operation
        self.closed_set.clear()
        self.came_from.clear()
        self.g_score.clear()
        self.f_score.clear()
        
        # Initialize starting node
        # Hash map insertion: O(1)
        self.g_score[start_grid] = 0
        self.f_score[start_grid] = self.heuristic(start_grid, goal_grid)
        self.open_set[start_grid] = self.f_score[start_grid]
        
        max_iterations = 500  # Prevent infinite loops
        iterations = 0
        
        while self.open_set and iterations < max_iterations:
            iterations += 1
            
            # Find node with lowest f_score in open set
            # Hash map lookup: O(1) for each node
            current = min(self.open_set, key=self.open_set.get)
            
            # Goal reached!
            if current == goal_grid:
                return self.reconstruct_path(current)
            
            # Move current from open to closed set
            # Hash map operations: O(1)
            del self.open_set[current]
            self.closed_set[current] = True
            
            # Check all neighbors (8 directions)
            neighbors = self.get_neighbors(current)
            
            for neighbor in neighbors:
                # Skip if already evaluated (O(1) lookup in hash map)
                if neighbor in self.closed_set:
                    continue
                
                # Calculate tentative g_score
                tentative_g = self.g_score[current] + self.get_movement_cost(current, neighbor)
                
                # Check if this path is better (O(1) lookup in hash map)
                if neighbor not in self.g_score or tentative_g < self.g_score[neighbor]:
                    # This is the best path so far, record it!
                    # Hash map insertion/update: O(1)
                    self.came_from[neighbor] = current
                    self.g_score[neighbor] = tentative_g
                    self.f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal_grid)
                    
                    # Add to open set if not already there
                    if neighbor not in self.open_set:
                        self.open_set[neighbor] = self.f_score[neighbor]
        
        # No path found
        return []
    
    def reconstruct_path(self, current):
        """
        Reconstruct path from came_from hash map
        O(n) where n = path length (following parent pointers)
        """
        path = [current]
        
        # Follow the came_from hash map backwards
        # Each lookup is O(1)
        while current in self.came_from:
            current = self.came_from[current]
            path.append(current)
        
        path.reverse()
        
        # Convert grid positions to world positions
        world_path = []
        for grid_pos in path:
            world_x = grid_pos[0] * TILE_SIZE + TILE_SIZE // 2
            world_y = grid_pos[1] * TILE_SIZE + TILE_SIZE // 2
            world_path.append((world_x, world_y))
        
        return world_path
    
    def heuristic(self, pos1, pos2):
        """
        Heuristic function for A* (Manhattan distance)
        Estimates cost from pos1 to pos2
        """
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def get_neighbors(self, grid_pos):
        """
        Get valid neighbors for pathfinding
        Returns list of (x, y) grid positions
        """
        x, y = grid_pos
        neighbors = []
        
        # 8 directions (including diagonals)
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),  # Cardinal
            (1, 1), (-1, -1), (1, -1), (-1, 1)  # Diagonal
        ]
        
        for dx, dy in directions:
            neighbor = (x + dx, y + dy)
            
            # Check if tile is walkable using hash map cache
            if self.is_tile_walkable(neighbor[0], neighbor[1]):
                neighbors.append(neighbor)
        
        return neighbors
    
    def get_movement_cost(self, from_pos, to_pos):
        """
        Calculate movement cost between two positions
        Diagonal movement costs more than cardinal
        Corrupted tiles have higher cost
        """
        # Base cost
        dx = abs(to_pos[0] - from_pos[0])
        dy = abs(to_pos[1] - from_pos[1])
        
        # Diagonal movement costs sqrt(2) ≈ 1.4
        if dx and dy:
            cost = 1.4
        else:
            cost = 1.0
        
        # Check if tile is corrupted (using hash map lookup)
        if self.is_tile_corrupted(to_pos[0], to_pos[1]):
            cost += 100  # High penalty for corrupted tiles (we avoid them)
        
        return cost
    
    # ==================== HASH MAP: TILE SAFETY CHECKING WITH CACHE ====================
    def is_tile_walkable(self, grid_x, grid_y):
        """
        Check if tile is walkable using CACHED hash map lookups
        
        WHY CACHE?
        - Checking collision/corruption is expensive
        - Hash map cache gives O(1) lookup for previously checked tiles
        - Reduces repeated calculations
        """
        current_time = pygame.time.get_ticks() / 1000.0
        tile_key = (grid_x, grid_y)
        
        # Check cache first (O(1) hash map lookup)
        if tile_key in self.tile_safety_cache:
            # Check if cache is still valid
            if tile_key in self.cache_expiry and current_time < self.cache_expiry[tile_key]:
                return self.tile_safety_cache[tile_key]  # Return cached result
        
        # Cache miss or expired - calculate and cache result
        is_safe = True
        
        # Check if out of bounds
        if grid_x < 0 or grid_y < 0:
            is_safe = False
        
        # Check corruption (using corruption system's hash map)
        if is_safe and self.is_tile_corrupted(grid_x, grid_y):
            is_safe = False
        
        # Check collision sprites
        if is_safe:
            world_pos = pygame.Rect(
                grid_x * TILE_SIZE,
                grid_y * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE
            )
            
            for sprite in self.collision_sprites.sprites():
                if hasattr(sprite, 'hitbox') and sprite.hitbox.colliderect(world_pos):
                    is_safe = False
                    break
        
        # Store in cache (O(1) hash map insertion)
        self.tile_safety_cache[tile_key] = is_safe
        self.cache_expiry[tile_key] = current_time + self.cache_duration
        
        return is_safe
    
    def is_tile_corrupted(self, grid_x, grid_y):
        """
        Check if tile is corrupted using corruption system's hash map
        O(1) lookup!
        """
        if hasattr(self.corruption_system, 'corruption_map'):
            # If corruption system uses hash map (new implementation)
            return (grid_x, grid_y) in self.corruption_system.corruption_map
        elif hasattr(self.corruption_system, 'corrupted_tiles'):
            # Fallback to list (slower: O(n) lookup)
            return (grid_x, grid_y) in self.corruption_system.corrupted_tiles
        
        return False
    
    # ==================== HASH MAP: VISITED TILES MEMORY ====================
    def mark_tile_visited(self, grid_x, grid_y):
        """
        Mark tile as visited using hash map
        O(1) insertion
        """
        current_time = pygame.time.get_ticks() / 1000.0
        self.visited_tiles[(grid_x, grid_y)] = current_time
    
    def is_tile_recently_visited(self, grid_x, grid_y):
        """
        Check if tile was recently visited using hash map
        O(1) lookup
        """
        current_time = pygame.time.get_ticks() / 1000.0
        tile_key = (grid_x, grid_y)
        
        if tile_key in self.visited_tiles:
            visit_time = self.visited_tiles[tile_key]
            if current_time - visit_time < self.visit_memory_duration:
                return True
            else:
                # Remove old visit from memory (cleanup)
                del self.visited_tiles[tile_key]
        
        return False
    
    def clean_old_visits(self):
        """
        Clean up old visited tiles from hash map
        Prevents memory bloat
        """
        current_time = pygame.time.get_ticks() / 1000.0
        
        # Create list of tiles to remove (can't modify dict during iteration)
        to_remove = []
        for tile_key, visit_time in self.visited_tiles.items():
            if current_time - visit_time > self.visit_memory_duration:
                to_remove.append(tile_key)
        
        # Remove old visits (O(1) per removal)
        for tile_key in to_remove:
            del self.visited_tiles[tile_key]
    
    # ==================== BEHAVIOR SYSTEM ====================
    def update_behavior(self, player, dt):
        """
        Update dog behavior based on current state
        Uses hash map to lookup behavior properties
        """
        self.behavior_timer += dt
        
        # Get current behavior properties from hash map (O(1) lookup)
        behavior_props = self.behavior_states[self.current_behavior]
        
        if self.current_behavior == 'wandering':
            self.update_wandering(dt, behavior_props)
        
        elif self.current_behavior == 'following':
            self.update_following(player, dt, behavior_props)
        
        elif self.current_behavior == 'circling':
            self.update_circling(player, dt, behavior_props)
        
        elif self.current_behavior == 'idle':
            self.update_idle(dt, behavior_props)
    
    def update_wandering(self, dt, behavior_props):
        """Random exploration behavior"""
        # Update path periodically
        if self.behavior_timer >= behavior_props['path_update_interval']:
            self.behavior_timer = 0
            
            # Pick random goal near spawn
            max_dist = behavior_props['max_distance']
            goal_x = self.spawn_pos.x + randint(-max_dist, max_dist)
            goal_y = self.spawn_pos.y + randint(-max_dist, max_dist)
            
            # Find path to goal
            self.current_path = self.find_path_astar(self.pos, (goal_x, goal_y))
            self.path_index = 0
    
    def update_following(self, player, dt, behavior_props):
        """Follow player behavior"""
        player_pos = pygame.math.Vector2(player.rect.center)
        distance = self.pos.distance_to(player_pos)
        
        # If player is far, follow
        if distance > behavior_props['follow_distance']:
            # Update path periodically
            if self.behavior_timer >= behavior_props['path_update_interval']:
                self.behavior_timer = 0
                self.current_path = self.find_path_astar(self.pos, player_pos)
                self.path_index = 0
        
        # If player is close and idle, circle around
        elif distance < behavior_props['follow_distance'] and player.direction.magnitude() == 0:
            self.current_behavior = 'circling'
            self.circle_center = player_pos
            self.behavior_timer = 0
    
    def update_circling(self, player, dt, behavior_props):
        """Circle around player"""
        player_pos = pygame.math.Vector2(player.rect.center)
        
        # If player moved, stop circling
        if player.direction.magnitude() > 0:
            self.current_behavior = 'following'
            self.behavior_timer = 0
            return
        
        # Update circle angle
        self.circle_angle += behavior_props['circle_speed'] * dt
        
        # Calculate position on circle
        radius = behavior_props['circle_radius']
        offset_x = math.cos(self.circle_angle) * radius
        offset_y = math.sin(self.circle_angle) * radius
        
        target_pos = player_pos + pygame.math.Vector2(offset_x, offset_y)
        
        # Move towards target position
        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.direction = direction
    
    def update_idle(self, dt, behavior_props):
        """Stand still"""
        self.direction = pygame.math.Vector2(0, 0)
        self.current_path = []

        
        if self.behavior_timer >= behavior_props['idle_duration']:
            # Switch back to previous behavior
            if self.is_befriended:
                self.current_behavior = 'following'
            else:
                self.current_behavior = 'wandering'
            self.behavior_timer = 0
    
    def follow_path(self, dt):
        """Follow the current path"""
        if not self.current_path or self.path_index >= len(self.current_path):
            self.direction = pygame.math.Vector2(0, 0)
            return
        
        # Get next waypoint
        target = pygame.math.Vector2(self.current_path[self.path_index])
        
        # Calculate direction to waypoint
        direction = target - self.pos
        distance = direction.length()
        
        # Reached waypoint
        if distance < 10:
            self.path_index += 1
            
            # Mark tile as visited
            grid_x = int(target.x // TILE_SIZE)
            grid_y = int(target.y // TILE_SIZE)
            self.mark_tile_visited(grid_x, grid_y)
            
            if self.path_index >= len(self.current_path):
                self.direction = pygame.math.Vector2(0, 0)
                return
        
        # Move towards waypoint
        if distance > 0:
            self.direction = direction.normalize()
        else:
            self.direftion = pygame.math.Vector2(0, 0)
    def move(self, dt):
        """Move the dog"""
        if self.direction.magnitude() > 0:
            # Get speed multiplier from current behavior
            behavior_props = self.behavior_states[self.current_behavior]
            speed_mult = behavior_props.get('speed_multiplier', 1.0)
            
            normalized_direction = self.direction.normalize()
            self.pos += normalized_direction * self.speed * speed_mult * dt

            # Move
            self.rect.center = self.pos
            self.hitbox.center = self.rect.center
    
    def update(self, dt, player):
        """Main update method"""
        # Update cooldowns
        if self.feed_cooldown > 0:
            self.feed_cooldown -= dt
        
        # Update pathfinding cooldown
        if self.pathfinding_cooldown > 0:
            self.pathfinding_cooldown -= dt
        
        # Clean old visited tiles periodically
        if pygame.time.get_ticks() % 5000 < 50:  # Every 5 seconds
            self.clean_old_visits()
        
        # Update behavior
        self.update_behavior(player, dt)
        
        # Follow path if in wandering/following mode
        if self.current_behavior in ['wandering', 'following']:
            self.follow_path(dt)
        
        self.get_status()
        # Move
        self.move(dt)
        
        # Simple animation (bounce)
        self.animate(dt)
    
    def draw_interaction_prompt(self, camera_offset, player):
        """Draw 'Press F to Feed' prompt when player is near"""
        if not self.can_feed(player):
            return
        
        # Check if player has any crops
        has_crops = False
        for crop, amount in player.item_inventory.items():
            if crop in ['corn', 'tomato', 'moon_melon', 'pumpkin', 'cactus'] and amount > 0:
                has_crops = True
                break
        
        if not has_crops:
            return
        
        # Draw prompt above dog
        font = pygame.font.Font('font/LycheeSoda.ttf', 16)
        
        if not self.is_befriended:
            text = f"Press F to Feed ({self.feed_count}/{self.max_feeds_to_befriend})"
        else:
            text = "Press F to Feed"
        
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(
            center=(self.rect.centerx - camera_offset.x, self.rect.top - 20 - camera_offset.y)
        )
        
        # Background
        bg_rect = text_rect.inflate(10, 4)
        pygame.draw.rect(self.display_surface, (0, 0, 0), bg_rect, border_radius=4)
        pygame.draw.rect(self.display_surface, (255, 255, 255), bg_rect, 2, border_radius=4)
        
        self.display_surface.blit(text_surf, text_rect)
    
    def draw_path_debug(self, camera_offset):
        """Draw pathfinding debug visualization (optional)"""
        if not self.current_path:
            return
        
        # Draw path line
        if len(self.current_path) > 1:
            points = []
            for waypoint in self.current_path:
                screen_pos = (
                    waypoint[0] - camera_offset.x,
                    waypoint[1] - camera_offset.y
                )
                points.append(screen_pos)
            
            pygame.draw.lines(self.display_surface, (100, 200, 255), False, points, 2)
        
        # Draw waypoints
        for i, waypoint in enumerate(self.current_path):
            screen_pos = (
                int(waypoint[0] - camera_offset.x),
                int(waypoint[1] - camera_offset.y)
            )
            
            color = (0, 255, 0) if i == self.path_index else (100, 200, 255)
            pygame.draw.circle(self.display_surface, color, screen_pos, 4)