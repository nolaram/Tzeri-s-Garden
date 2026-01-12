from pygame.math import Vector2
# screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 64

# maximum reach distance (pixels) for interacting with tiles
PLAYER_REACH_LIMIT = 150

# overlay positions 
OVERLAY_POSITIONS = {
	'tool' : (40, SCREEN_HEIGHT - 15), 
	'seed': (70, SCREEN_HEIGHT - 5)}

PLAYER_TOOL_OFFSET = {
	'left': Vector2(-50,40),
	'right': Vector2(50,40),
	'up': Vector2(0,-10),
	'down': Vector2(0,50)
}

LAYERS = {
	'water': 0,
	'ground': 1,
	'soil': 2,
	'soil water': 3,
	'rain floor': 4,
	'house bottom': 5,
	'ground plant': 6,
	'main': 7,
	'house top': 8,
	'fruit': 9,
	'rain drops': 10
}

APPLE_POS = {
	'Small': [(18,17), (30,37), (12,50), (30,45), (20,30), (30,10)],
	'Large': [(30,24), (60,65), (50,50), (16,40),(45,50), (42,70)]
}

GROW_SPEED = {
	'corn': 1,
	'tomato': 1,
    'moon_melon': 0.5,
    'pumpkin': 0.7,
    'cactus': 0.6
}

SALE_PRICES = {
	'wood': 10,
	'apple': 2,
	'corn': 10,
	'tomato': 20,
    'moon_melon': 25,
    'pumpkin': 20,
	'cactus': 20
    
}
PURCHASE_PRICES = {
	'corn': 30,
	'tomato': 40,
    'moon_melon': 200,
    'pumpkin': 150,
    'cactus': 170
}