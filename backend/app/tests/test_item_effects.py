# backend/app/tests/test_item_effects.py
import pytest
from unittest.mock import MagicMock, PropertyMock, patch
import random

from app.core.items import effects as item_effects
from app.core.items.definitions import ITEM_TEMPLATES, ITEM_TYPE_POTION_HEAL, ITEM_TYPE_SCROLL_TELEPORT
from app.core.player import Player
from app.core.game_state import GameState
from app.core.map_manager import MapManager
from app.core.entity_manager import EntityManager
from app.core import config as game_config
from app.core.tiles import TILE_FLOOR, TILE_WALL, TILE_FOG
from app.schemas import GameMessageServerResponse, PlayerMovedServerResponse, TileChangeServerResponse, Position

# --- Fixtures ---

@pytest.fixture
def mock_player() -> MagicMock:
    player = MagicMock(spec=Player)
    player.pos = {"x": 5, "y": 5}
    player.hp = 10
    player.max_hp = game_config.PLAYER_INITIAL_MAX_HP  
    player.inventory = [] 
    player.logger = MagicMock()
    return player

@pytest.fixture
def mock_map_manager() -> MagicMock:
    manager = MagicMock(spec=MapManager)
    default_map_data = [[TILE_FLOOR for _ in range(10)] for _ in range(10)]
    manager.actual_dungeon_map = default_map_data
    # Make client map initially all FOG to better test FoV updates
    manager.dungeon_map_for_client = [[TILE_FOG for _ in range(10)] for _ in range(10)] 
    manager.generated_rooms = [] 
    manager.visited_room_indices = set()
    # ever_revealed_tiles should be empty initially for FoV tests
    manager.ever_revealed_tiles = set()

    manager.get_room_at_pos = MagicMock(return_value=None)
    manager.reveal_room_and_connected_corridors = MagicMock(return_value=[])
    # Default update_fov returns an empty list. Tests can override this.
    manager.update_fov = MagicMock(return_value=[]) 
    return manager

@pytest.fixture
def mock_entity_manager() -> MagicMock:
    manager = MagicMock(spec=EntityManager)
    manager.get_monster_at = MagicMock(return_value=None) 
    manager.get_all_monsters = MagicMock(return_value=[])
    return manager

@pytest.fixture
def mock_game_state(mock_player: MagicMock, mock_map_manager: MagicMock, mock_entity_manager: MagicMock) -> MagicMock:
    gs = MagicMock(spec=GameState)
    gs.player = mock_player
    gs.map_manager = mock_map_manager
    gs.entity_manager = mock_entity_manager
    gs.logger = MagicMock()
    
    def fake_is_walkable(x, y, entity_type):
        # Ensure map_manager and actual_dungeon_map are valid before accessing
        if not gs.map_manager or not gs.map_manager.actual_dungeon_map:
            return False # Or raise an error, depending on expected robustness
        if not (0 <= y < len(gs.map_manager.actual_dungeon_map) and \
                0 <= x < len(gs.map_manager.actual_dungeon_map[0])):
            return False
        if gs.map_manager.actual_dungeon_map[y][x] == TILE_WALL:
            return False
        if entity_type == "player_teleport":
            # Ensure entity_manager is valid before calling get_monster_at
            if gs.entity_manager and gs.entity_manager.get_monster_at(x,y): return False
            return gs.map_manager.actual_dungeon_map[y][x] == TILE_FLOOR
        return True 
    gs._is_walkable_for_entity = MagicMock(side_effect=fake_is_walkable)
    return gs

# --- Tests for apply_heal_effect ---

def test_apply_heal_effect_heals_player(mock_game_state: MagicMock):
    player = mock_game_state.player
    player.hp = 5
    player.max_hp = 20
    heal_amount = 10
    item_data = {"type_name": "Health Potion", "effect_value": heal_amount}
    
    responses = item_effects.apply_heal_effect(mock_game_state, item_data)
    
    assert player.hp == 15
    assert any(isinstance(r, GameMessageServerResponse) and f"heal for {heal_amount} HP" in r.text for r in responses)

def test_apply_heal_effect_caps_at_max_hp(mock_game_state: MagicMock):
    player = mock_game_state.player
    player.hp = 18
    player.max_hp = 20
    item_data = {"type_name": "Health Potion", "effect_value": 10} 
    
    responses = item_effects.apply_heal_effect(mock_game_state, item_data)
    
    assert player.hp == 20 
    assert any(isinstance(r, GameMessageServerResponse) and "heal for 2 HP" in r.text for r in responses)

def test_apply_heal_effect_at_max_hp(mock_game_state: MagicMock):
    player = mock_game_state.player
    player.hp = 20
    player.max_hp = 20
    item_data = {"type_name": "Health Potion", "effect_value": 10}
    
    responses = item_effects.apply_heal_effect(mock_game_state, item_data)
    
    assert player.hp == 20 
    assert any(isinstance(r, GameMessageServerResponse) and "health is already full" in r.text for r in responses)

# --- Tests for apply_teleport_random_effect ---

def test_apply_teleport_random_effect_successful(mock_game_state: MagicMock):
    player = mock_game_state.player
    initial_pos = player.pos.copy()
    
    mock_game_state.map_manager.actual_dungeon_map[0][0] = TILE_FLOOR 
    if initial_pos["x"] == 0 and initial_pos["y"] == 0: 
        mock_game_state.map_manager.actual_dungeon_map[0][1] = TILE_FLOOR

    # CRITICAL FIX: Configure the mock update_fov to return a TileChangeServerResponse for this test
    dummy_tile_change = TileChangeServerResponse(pos=Position(x=0,y=0), new_tile_type=TILE_FLOOR)
    mock_game_state.map_manager.update_fov.return_value = [dummy_tile_change]
    # Also, mock reveal_room_and_connected_corridors if it might be called and needs to return something
    mock_game_state.map_manager.reveal_room_and_connected_corridors.return_value = []


    item_data = {"type_name": "Teleport Scroll"}
    responses = item_effects.apply_teleport_random_effect(mock_game_state, item_data)
    
    assert player.pos != initial_pos, "Player position should change"
    assert any(isinstance(r, GameMessageServerResponse) and ("teleports you" in r.text.lower() or "reappearing elsewhere" in r.text.lower()) for r in responses)
    assert any(isinstance(r, PlayerMovedServerResponse) for r in responses)
    assert any(isinstance(r, TileChangeServerResponse) for r in responses), "TileChangeServerResponse for FoV not found"
    mock_game_state.map_manager.update_fov.assert_called_once_with(player.pos) # Verify it was called


def test_apply_teleport_random_effect_no_valid_locations(mock_game_state: MagicMock):
    player = mock_game_state.player
    initial_pos = player.pos.copy()
    
    rows = len(mock_game_state.map_manager.actual_dungeon_map)
    cols = len(mock_game_state.map_manager.actual_dungeon_map[0])
    for r_idx in range(rows):
        for c_idx in range(cols):
            if r_idx == player.pos["y"] and c_idx == player.pos["x"]:
                mock_game_state.map_manager.actual_dungeon_map[r_idx][c_idx] = TILE_FLOOR
            else:
                mock_game_state.map_manager.actual_dungeon_map[r_idx][c_idx] = TILE_WALL
                
    item_data = {"type_name": "Teleport Scroll"}
    responses = item_effects.apply_teleport_random_effect(mock_game_state, item_data)
    
    assert player.pos == initial_pos, "Player position should not change if teleport fizzles"
    assert any(isinstance(r, GameMessageServerResponse) and "fizzles" in r.text.lower() for r in responses)
    assert not any(isinstance(r, PlayerMovedServerResponse) for r in responses), "PlayerMoved should not occur if teleport fizzles"
    mock_game_state.map_manager.update_fov.assert_not_called() # FoV update should not happen if teleport fails this way


def test_apply_teleport_random_effect_avoids_monsters(mock_game_state: MagicMock):
    player = mock_game_state.player
    
    # Simplified map setup: 3x3
    # (0,0) = Valid Floor, (0,1) = Monster on Floor, (0,2) = Wall
    # (1,0) = Wall,      (1,1) = Wall,             (1,2) = Wall
    # (2,0) = Wall,      (2,1) = Wall,             (2,2) = Player Start Floor
    new_map = [
        [TILE_FLOOR, TILE_FLOOR, TILE_WALL],
        [TILE_WALL,  TILE_WALL,  TILE_WALL],
        [TILE_WALL,  TILE_WALL,  TILE_FLOOR]
    ]
    mock_game_state.map_manager.actual_dungeon_map = new_map
    # Make client map initially all FOG to allow FoV updates to be meaningful
    mock_game_state.map_manager.dungeon_map_for_client = [[TILE_FOG for _ in range(3)] for _ in range(3)]
    mock_game_state.map_manager.ever_revealed_tiles = set()


    player.pos = {"x": 2, "y": 2} 
    
    # Configure get_monster_at to return a monster only at (0,1)
    mock_game_state.entity_manager.get_monster_at = lambda x, y: {"id": "m1"} if x == 0 and y == 1 else None
    
    # Configure update_fov to return a dummy response when called
    dummy_tile_change = TileChangeServerResponse(pos=Position(x=0,y=0), new_tile_type=TILE_FLOOR)
    mock_game_state.map_manager.update_fov.return_value = [dummy_tile_change]


    item_data = {"type_name": "Teleport Scroll"}
    
    teleported_successfully_to_valid_spot = False
    for _ in range(30): # Increased attempts for small number of valid spots
        player.pos = {"x": 2, "y": 2} # Reset player pos
        mock_game_state.map_manager.update_fov.reset_mock() # Reset call count for each attempt

        responses = item_effects.apply_teleport_random_effect(mock_game_state, item_data)
        
        if player.pos["x"] == 0 and player.pos["y"] == 0: # The only valid non-monster spot
            teleported_successfully_to_valid_spot = True
            assert any(isinstance(r, PlayerMovedServerResponse) for r in responses)
            mock_game_state.map_manager.update_fov.assert_called_once_with(player.pos)
            break
        
        assert not (player.pos["x"] == 0 and player.pos["y"] == 1), "Player should not teleport onto a monster"
        # If it fizzled (player pos didn't change from (2,2))
        if player.pos["x"] == 2 and player.pos["y"] == 2:
            assert any(isinstance(r, GameMessageServerResponse) and "fizzles" in r.text.lower() for r in responses)
            mock_game_state.map_manager.update_fov.assert_not_called()


    assert teleported_successfully_to_valid_spot, "Player did not teleport to the only valid non-monster spot (0,0) after multiple tries"