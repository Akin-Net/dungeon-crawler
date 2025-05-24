# backend/app/tests/test_dungeon_generator.py
import pytest
import random
from collections import deque
from typing import List, Set, Tuple

from app.core.dungeon_generator import DungeonGenerator, Room
from app.core.tiles import (
    TILE_FLOOR, TILE_WALL, TILE_EMPTY, TILE_DOOR_CLOSED, TILE_DOOR_OPEN,
    TILE_ITEM_POTION, TILE_ITEM_SCROLL_TELEPORT,
    TILE_MONSTER_GOBLIN, TILE_MONSTER_ORC, TILE_MONSTER_SKELETON,
    TILE_STAIRS_DOWN 
)
from app.core import config as game_config

# --- Fixtures ---

@pytest.fixture
def dungeon_generator_instance() -> DungeonGenerator:
    return DungeonGenerator(
        map_width=game_config.DEFAULT_MAP_WIDTH,
        map_height=game_config.DEFAULT_MAP_HEIGHT,
        seed=12345 
    )

# --- Helper Functions ---

def bfs_find_reachable_rooms(
    map_data: List[List[int]], 
    all_rooms: List[Room], 
    start_room_idx: int
) -> Set[int]:
    """
    Performs a BFS starting from a tile in start_room_idx.
    Returns a set of room indices that are reachable.
    Considers closed doors as traversable for pathfinding between rooms.
    """
    if not all_rooms or start_room_idx >= len(all_rooms):
        return set()

    height = len(map_data)
    width = len(map_data[0])
    
    start_room = all_rooms[start_room_idx]
    # Find a valid starting floor tile within the start_room
    start_tile = None
    for r_y in range(start_room.y1, start_room.y2 + 1):
        for r_x in range(start_room.x1, start_room.x2 + 1):
            if 0 <= r_y < height and 0 <= r_x < width and \
               map_data[r_y][r_x] not in [TILE_WALL, TILE_EMPTY]:
                start_tile = (r_x, r_y)
                break
        if start_tile:
            break
    
    if not start_tile: # Should not happen if room is valid
        return {start_room_idx} if all_rooms else set()


    q: deque[Tuple[int, int]] = deque([start_tile])
    visited_tiles: Set[Tuple[int, int]] = {start_tile}
    reached_room_indices: Set[int] = {start_room_idx} # Start room is reached

    head = 0
    while q:
        cx, cy = q.popleft()

        # Check if current tile is inside any other room
        for r_idx, room_obj in enumerate(all_rooms):
            if room_obj.is_inside(cx, cy):
                reached_room_indices.add(r_idx)

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= ny < height and 0 <= nx < width and \
               (nx, ny) not in visited_tiles and \
               map_data[ny][nx] not in [TILE_WALL, TILE_EMPTY]: # Traversable (floor, any door, item etc.)
                visited_tiles.add((nx, ny))
                q.append((nx, ny))
                
    return reached_room_indices


# --- Test Cases ---

def test_dungeon_generator_map_dimensions(dungeon_generator_instance: DungeonGenerator):
    gen = dungeon_generator_instance
    map_data, _ = gen.generate_dungeon()
    
    assert map_data is not None, "Generated map data should not be None"
    assert len(map_data) == gen.map_height, "Map height mismatch"
    assert len(map_data[0]) == gen.map_width, "Map width mismatch"

def test_dungeon_generator_player_start_position(dungeon_generator_instance: DungeonGenerator):
    gen = dungeon_generator_instance
    map_data, player_start = gen.generate_dungeon()

    assert player_start is not None, "Player start position should be generated"
    start_x, start_y = player_start
    
    assert 0 <= start_y < gen.map_height, "Player start Y out of bounds"
    assert 0 <= start_x < gen.map_width, "Player start X out of bounds"
    assert map_data[start_y][start_x] not in [TILE_WALL, TILE_EMPTY, TILE_DOOR_CLOSED], \
        f"Player start position ({start_x},{start_y}) is not on a traversable tile (it's {map_data[start_y][start_x]})"


def test_dungeon_generator_room_generation(dungeon_generator_instance: DungeonGenerator):
    gen = dungeon_generator_instance
    seeds_to_test = [None, 123, 9876, 555]
    min_rooms_expected = 2 

    for seed in seeds_to_test:
        gen_seeded = DungeonGenerator(gen.map_width, gen.map_height, seed=seed)
        map_data, _ = gen_seeded.generate_dungeon(max_rooms=game_config.DEFAULT_MAX_ROOMS)
        assert len(gen_seeded.rooms) > 0, f"Expected at least one room to be generated (seed: {seed})"
        if game_config.DEFAULT_MAX_ROOMS > 1: 
             assert len(gen_seeded.rooms) >= min_rooms_expected, \
                f"Expected at least {min_rooms_expected} rooms with default settings (seed: {seed}), got {len(gen_seeded.rooms)}"
        
        for room in gen_seeded.rooms:
            for y in range(room.y1, room.y2 + 1):
                for x in range(room.x1, room.x2 + 1):
                    if 0 <= y < gen.map_height and 0 <= x < gen.map_width:
                         assert map_data[y][x] not in [TILE_WALL, TILE_EMPTY], \
                            f"Room {room.id} area at ({x},{y}) should be traversable (not Wall/Empty), but was {map_data[y][x]} (seed: {seed})"


def test_dungeon_generator_entity_placement(dungeon_generator_instance: DungeonGenerator):
    gen = dungeon_generator_instance
    map_data, _ = gen.generate_dungeon(
        max_rooms=5, 
        room_min_size=game_config.DEFAULT_ROOM_MIN_SIZE,
        room_max_size=game_config.DEFAULT_ROOM_MAX_SIZE
    )
    item_tiles = [TILE_ITEM_POTION, TILE_ITEM_SCROLL_TELEPORT]
    monster_tiles = [TILE_MONSTER_GOBLIN, TILE_MONSTER_ORC, TILE_MONSTER_SKELETON]
    item_found = any(tile_val in item_tiles for r in map_data for tile_val in r)
    monster_found = any(tile_val in monster_tiles for r in map_data for tile_val in r)
    assert item_found, "Expected at least one item tile to be placed"
    assert monster_found, "Expected at least one monster tile to be placed"

def test_dungeon_generator_room_connectivity(dungeon_generator_instance: DungeonGenerator):
    gen = dungeon_generator_instance
    seeds = [1, 20, 300, 4000, 55555, None, 42, 88, 777] # Test more seeds
    for seed in seeds:
        gen_seeded = DungeonGenerator(gen.map_width, gen.map_height, seed=seed)
        map_data, player_start = gen_seeded.generate_dungeon(
            max_rooms=game_config.DEFAULT_MAX_ROOMS, # Default number of rooms
            room_min_size=game_config.DEFAULT_ROOM_MIN_SIZE, 
            room_max_size=game_config.DEFAULT_ROOM_MAX_SIZE
        )

        if not gen_seeded.rooms:
            print(f"Warning (seed {seed}): No rooms generated, skipping connectivity check.")
            continue
        
        if player_start is None:
             # This case implies a major failure in generation if rooms were expected/made.
             # If no rooms, player_start might legitimately be None or a default.
            if gen_seeded.rooms:
                 pytest.fail(f"Player start is None but rooms were generated (seed: {seed}). Rooms: {len(gen_seeded.rooms)}")
            else: # No rooms, no player_start.
                print(f"Warning (seed {seed}): No rooms and no player start for connectivity check.")
                continue


        # Find the room the player starts in, or default to room 0
        start_room_idx = 0
        player_in_a_room = False
        for idx, r_obj in enumerate(gen_seeded.rooms):
            if r_obj.is_inside(player_start[0], player_start[1]):
                start_room_idx = idx
                player_in_a_room = True
                break
        
        if not player_in_a_room and gen_seeded.rooms:
            # If player is not in any defined room (e.g. starts in a corridor),
            # pick the first room as the BFS start for room connectivity.
            # This situation suggests player_start_pos logic in generator might need review
            # if it's meant to always be in a room.
            print(f"Warning (seed {seed}): Player not in any listed room. Defaulting BFS start to room 0 for room connectivity.")
            start_room_idx = 0 
            # Additionally, check if player_start itself is on a traversable tile for overall map connectivity later
            if map_data[player_start[1]][player_start[0]] in [TILE_WALL, TILE_EMPTY]:
                pytest.fail(f"Player start ({player_start}) is on a non-traversable tile ({map_data[player_start[1]][player_start[0]]}) (seed: {seed})")


        reachable_room_indices = bfs_find_reachable_rooms(map_data, gen_seeded.rooms, start_room_idx)
        
        assert len(reachable_room_indices) == len(gen_seeded.rooms), \
            f"Not all rooms are connected (seed {seed}). Reached: {len(reachable_room_indices)}/{len(gen_seeded.rooms)}. Indices: {reachable_room_indices}"


def test_dungeon_generator_wall_integrity_simple(dungeon_generator_instance: DungeonGenerator):
    gen = dungeon_generator_instance
    map_data, _ = gen.generate_dungeon(max_rooms=3, room_min_size=3, room_max_size=5) 

    height = len(map_data)
    width = len(map_data[0])

    for y in range(height):
        for x in range(width):
            tile = map_data[y][x]
            if tile not in [TILE_WALL, TILE_EMPTY]: 
                adj_tiles_passable = 0
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= ny < height and 0 <= nx < width:
                        if map_data[ny][nx] not in [TILE_EMPTY, TILE_WALL]: 
                            adj_tiles_passable +=1
                # For a traversable tile, it should have at least one traversable neighbor
                # unless it's a 1x1 room that somehow got created AND has no doors.
                is_tiny_isolated_room = False
                if gen.rooms and len(gen.rooms) == 1 and gen.rooms[0].width == 1 and gen.rooms[0].height == 1:
                    room = gen.rooms[0]
                    if room.is_inside(x,y) and room.doors_made == 0 : # Check if it's this specific 1x1 room with no doors
                        is_tiny_isolated_room = True
                
                if not is_tiny_isolated_room:
                     assert adj_tiles_passable > 0, f"Traversable tile at ({x},{y}) value {tile} has no passable non-diagonal neighbors."