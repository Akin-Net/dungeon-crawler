# backend/app/tests/test_map_manager.py
import pytest
from unittest.mock import MagicMock, patch

from app.core.map_manager import MapManager
from app.core.entity_manager import EntityManager 
from app.core.player import Player 
from app.core.dungeon_generator import Room 
from app.core.tiles import TILE_FLOOR, TILE_WALL, TILE_DOOR_CLOSED, TILE_DOOR_OPEN, TILE_EMPTY, TILE_FOG, TILE_ITEM_POTION
from app.core import config as game_config
from app.schemas import TileChangeServerResponse, Position


@pytest.fixture
def map_manager_instance() -> MapManager:
    manager = MapManager(logger_parent_name="TestMapManager")
    return manager

@pytest.fixture
def entity_manager_instance() -> EntityManager:
    manager = EntityManager(logger_parent_name="TestEntityManager")
    return manager

@pytest.fixture
def player_instance(map_manager_instance: MapManager) -> Player: 
    mock_logger = MagicMock()
    start_pos = {"x": 1, "y": 1} 
    player = Player(initial_pos=start_pos, logger_ref=mock_logger)
    return player

@pytest.fixture
def mock_game_state(map_manager_instance, entity_manager_instance, player_instance) -> MagicMock:
    gs = MagicMock()
    gs.map_manager = map_manager_instance
    gs.entity_manager = entity_manager_instance
    gs.player = player_instance
    gs.logger = MagicMock() 
    return gs

los_map_data = [
    [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_WALL, TILE_FLOOR, TILE_WALL], 
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL],
]
los_map_data_with_door = [
    [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_DOOR_CLOSED, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL],
]
los_map_data_with_open_door = [
    [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_DOOR_OPEN, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL],
]
los_map_clear_diag = [ 
    [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL], 
    [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
    [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL],
]

def test_is_tile_passable_basic(map_manager_instance: MapManager):
    map_manager_instance.actual_dungeon_map = [
        [TILE_WALL, TILE_WALL, TILE_WALL], [TILE_WALL, TILE_FLOOR, TILE_WALL],
        [TILE_WALL, TILE_DOOR_CLOSED, TILE_WALL], [TILE_WALL, TILE_DOOR_OPEN, TILE_WALL]]
    assert not map_manager_instance.is_tile_passable(1,0,"player")
    assert map_manager_instance.is_tile_passable(1,1,"player")    
    assert map_manager_instance.is_tile_passable(1,2,"player")    
    assert not map_manager_instance.is_tile_passable(1,2,"monster")
    assert map_manager_instance.is_tile_passable(1,3,"player")    
    assert map_manager_instance.is_tile_passable(1,3,"monster")   

def test_is_walkable_basic(map_manager_instance:MapManager,entity_manager_instance:EntityManager,player_instance:Player):
    map_data = [[TILE_FLOOR]*3 for _ in range(3)]; map_manager_instance.actual_dungeon_map = map_data
    player_instance.pos = {"x":0,"y":0}
    assert map_manager_instance.is_walkable_for_entity(1,1,"player",entity_manager_instance,player_instance.pos)
    assert not map_manager_instance.is_walkable_for_entity(0,0,"player",entity_manager_instance,player_instance.pos)

def test_is_walkable_blocked_by_monster(map_manager_instance:MapManager,entity_manager_instance:EntityManager,player_instance:Player):
    map_data = [[TILE_FLOOR,TILE_FLOOR]]; map_manager_instance.actual_dungeon_map=map_data
    player_instance.pos={"x":0,"y":0}
    entity_manager_instance.add_monster({"id":"m1","x":1,"y":0,"type_name":"g","tile_id":4})
    assert not map_manager_instance.is_walkable_for_entity(1,0,"monster",entity_manager_instance,player_instance.pos)
    assert not map_manager_instance.is_walkable_for_entity(1,0,"player",entity_manager_instance,player_instance.pos) 

def test_is_walkable_player_teleport(map_manager_instance:MapManager,entity_manager_instance:EntityManager,player_instance:Player):
    map_data=[[TILE_FLOOR,TILE_WALL,TILE_DOOR_OPEN],[TILE_FLOOR,TILE_FLOOR,TILE_FLOOR]]
    map_manager_instance.actual_dungeon_map=map_data; player_instance.pos={"x":0,"y":0}
    entity_manager_instance.add_monster({"id":"m1","x":0,"y":1,"type_name":"g","tile_id":4})
    assert map_manager_instance.is_walkable_for_entity(0,0,"player_teleport",entity_manager_instance,player_instance.pos) 
    assert not map_manager_instance.is_walkable_for_entity(1,0,"player_teleport",entity_manager_instance,player_instance.pos) 
    assert map_manager_instance.is_walkable_for_entity(2,0,"player_teleport",entity_manager_instance,player_instance.pos) 
    assert not map_manager_instance.is_walkable_for_entity(0,1,"player_teleport",entity_manager_instance,player_instance.pos)

def test_has_line_of_sight_clear_path(map_manager_instance:MapManager):
    map_manager_instance.actual_dungeon_map=los_map_data;start_pos={"x":1,"y":1};end_pos_clear={"x":3,"y":1}
    assert map_manager_instance.has_line_of_sight(start_pos,end_pos_clear)
def test_has_line_of_sight_blocked_by_wall(map_manager_instance:MapManager):
    map_manager_instance.actual_dungeon_map=los_map_data;start_pos={"x":1,"y":2};end_pos_blocked={"x":3,"y":2}
    assert not map_manager_instance.has_line_of_sight(start_pos,end_pos_blocked)
def test_has_line_of_sight_diagonal_blocked(map_manager_instance:MapManager): 
    map_manager_instance.actual_dungeon_map=los_map_data;start_pos={"x":1,"y":1};end_pos_diag_blocked={"x":3,"y":3}
    assert not map_manager_instance.has_line_of_sight(start_pos,end_pos_diag_blocked)
def test_has_line_of_sight_true_diagonal_clear(map_manager_instance:MapManager): 
    map_manager_instance.actual_dungeon_map=los_map_clear_diag;start_pos={"x":1,"y":1};end_pos_diag_clear={"x":3,"y":3}
    assert map_manager_instance.has_line_of_sight(start_pos,end_pos_diag_clear)
def test_has_line_of_sight_blocked_by_closed_door(map_manager_instance:MapManager):
    map_manager_instance.actual_dungeon_map=los_map_data_with_door;start_pos={"x":1,"y":2};end_pos_behind_door={"x":3,"y":2}
    assert not map_manager_instance.has_line_of_sight(start_pos,end_pos_behind_door)
def test_has_line_of_sight_through_open_door(map_manager_instance:MapManager):
    map_manager_instance.actual_dungeon_map=los_map_data_with_open_door;start_pos={"x":1,"y":2};end_pos_behind_door={"x":3,"y":2}
    assert map_manager_instance.has_line_of_sight(start_pos,end_pos_behind_door)
def test_has_line_of_sight_to_self(map_manager_instance:MapManager):
    map_manager_instance.actual_dungeon_map=los_map_data;pos={"x":1,"y":1}
    assert map_manager_instance.has_line_of_sight(pos,pos)
def test_has_line_of_sight_adjacent(map_manager_instance:MapManager):
    map_manager_instance.actual_dungeon_map=los_map_data;start_pos={"x":1,"y":1};adj_pos={"x":1,"y":2}
    assert map_manager_instance.has_line_of_sight(start_pos,adj_pos)

# --- Tests for update_fov ---
def test_update_fov_reveals_los_tiles(map_manager_instance: MapManager):
    actual_map_larger = [[TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_FLOOR, TILE_WALL]]
    map_manager_instance.initialize_maps(actual_map_larger, 8, 1)
    player_pos = {"x": 3, "y": 0} 
    responses = map_manager_instance.update_fov(player_pos)
    assert map_manager_instance.dungeon_map_for_client is not None
    assert map_manager_instance.dungeon_map_for_client[0][0] == TILE_WALL
    assert map_manager_instance.dungeon_map_for_client[0][1] == TILE_FLOOR
    assert map_manager_instance.dungeon_map_for_client[0][6] == TILE_FLOOR
    assert map_manager_instance.dungeon_map_for_client[0][7] == TILE_WALL
    assert len(responses) == 8 
    for i in range(8): 
        assert (i,0) in map_manager_instance.ever_revealed_tiles

def test_update_fov_uses_memory(map_manager_instance: MapManager):
    actual_map = [
        [TILE_WALL, TILE_FLOOR, TILE_WALL, TILE_WALL], 
        [TILE_WALL, TILE_FLOOR, TILE_WALL, TILE_WALL], 
        [TILE_WALL, TILE_FLOOR, TILE_FLOOR, TILE_WALL],
        [TILE_WALL, TILE_WALL, TILE_WALL, TILE_WALL], 
    ]
    map_manager_instance.initialize_maps(actual_map, 4, 4)
    map_manager_instance.ever_revealed_tiles.add((1,0)) 
    player_pos = {"x": 1, "y": 2} 
    responses = map_manager_instance.update_fov(player_pos) 
    assert map_manager_instance.dungeon_map_for_client is not None
    assert map_manager_instance.dungeon_map_for_client[0][1] == TILE_FLOOR 
    assert map_manager_instance.dungeon_map_for_client[2][1] == TILE_FLOOR 
    assert map_manager_instance.dungeon_map_for_client[2][2] == TILE_FLOOR
    # Tile (3,3) is TILE_WALL in actual_map. Player at (1,2). LoS to (3,3) is True.
    # So it should be revealed as TILE_WALL, not TILE_FOG.
    assert map_manager_instance.dungeon_map_for_client[3][3] == TILE_WALL 

# --- Tests for reveal_room_and_connected_corridors ---
def test_reveal_room_updates_ever_revealed(map_manager_instance: MapManager, mock_game_state: MagicMock):
    room1 = Room(x=0, y=0, width=3, height=3)
    map_manager_instance.generated_rooms = [room1]
    actual_map = [[TILE_FLOOR]*3 for _ in range(3)]
    map_manager_instance.initialize_maps(actual_map, 3, 3)
    map_manager_instance.reveal_room_and_connected_corridors(0, mock_game_state)
    assert 0 in map_manager_instance.visited_room_indices
    for y_test in range(3):
        for x_test in range(3):
            assert (x_test,y_test) in map_manager_instance.ever_revealed_tiles
    player_pos_in_room = {"x":1, "y":1} 
    fov_responses = map_manager_instance.update_fov(player_pos_in_room) 
    assert len(fov_responses) == 9 
    for y_test in range(3):
        for x_test in range(3):
            assert map_manager_instance.dungeon_map_for_client[y_test][x_test] == TILE_FLOOR