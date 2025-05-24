# backend/app/core/tiles.py

# Tile types
TILE_EMPTY = 0 # This could represent unseen/fog if not otherwise used
TILE_FLOOR = 1
TILE_WALL = 2
TILE_ITEM_POTION = 3
TILE_MONSTER_GOBLIN = 4
TILE_MONSTER_ORC = 5
TILE_MONSTER_SKELETON = 6
TILE_DOOR_CLOSED = 7
TILE_DOOR_OPEN = 8
# TILE_DOOR_LOCKED = 9 
TILE_STAIRS_DOWN = 10 
TILE_FOG = 11 # New tile type for Fog of War
TILE_ITEM_SCROLL_TELEPORT = 12 # New item tile