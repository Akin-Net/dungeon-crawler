# backend/app/tests/test_ai.py
import pytest
from unittest.mock import MagicMock, patch
import random

# Removed _handle_monster_move_on_map_and_responses from direct import for patching in tests
from app.core.monsters.ai import ChaserAI, RangedAI 
from app.core.monsters.definitions import MONSTER_TEMPLATES, TILE_MONSTER_GOBLIN
from app.core.game_state import GameState 
from app.core.player import Player 
from app.core.map_manager import MapManager 
from app.core.tiles import TILE_FLOOR, TILE_FOG # Added TILE_FOG for map_manager.dungeon_map_for_client
from app.core import config as game_config
from app.schemas import ( 
    MonsterMovedServerResponse, CombatEventServerResponse, 
    PlayerStatsUpdateServerResponse, PlayerDiedServerResponse,
    PlayerStatsResponse, InventoryItemDetail, Position 
)

# --- Fixtures ---

@pytest.fixture
def mock_gs() -> MagicMock:
    """Mocks the GameState and its relevant attributes/methods for AI testing."""
    gs = MagicMock(spec=GameState)
    
    # Mock player
    gs.player = MagicMock(spec=Player)
    gs.player.pos = {"x": 0, "y": 0} # Default player position
    gs.player.hp = game_config.PLAYER_INITIAL_HP
    
    # Create a mock PlayerStatsResponse instance for the player's get_effective_stats
    mock_player_stats = PlayerStatsResponse(
        hp=game_config.PLAYER_INITIAL_HP,
        max_hp=game_config.PLAYER_INITIAL_MAX_HP,
        attack=game_config.PLAYER_INITIAL_ATTACK,
        defense=game_config.PLAYER_INITIAL_DEFENSE,
        level=1, xp=0, xp_to_next_level=100,
        inventory=[], # Empty inventory for simplicity
        equipment={"weapon": None, "armor": None} # No equipment for simplicity
    )
    gs.player.get_effective_stats = MagicMock(return_value=mock_player_stats.model_dump()) # Return dict form
    gs.player.take_damage = MagicMock(return_value=False) # Returns True if player died
    gs.player.create_player_stats_response = MagicMock(return_value=mock_player_stats)


    # Mock map_manager and its methods used by AI or its helpers
    gs.map_manager = MagicMock(spec=MapManager)
    # Default map: 10x10 all floor. Necessary for _handle_monster_move_on_map_and_responses to run.
    gs.map_manager.actual_dungeon_map = [[TILE_FLOOR for _ in range(10)] for _ in range(10)]
    # Client map with some FOG. Necessary for _handle_monster_move_on_map_and_responses.
    gs.map_manager.dungeon_map_for_client = [[TILE_FOG for _ in range(10)] for _ in range(10)]
    
    # REMOVED THE PROBLEMATIC LINE:
    # gs.map_manager.dungeon_map_for_client.__getitem__.side_effect = lambda y: gs.map_manager.dungeon_map_for_client[y]
    
    # Other map_manager mocks (not directly called by _handle_monster_move_on_map_and_responses, but common)
    gs.map_manager.update_fov = MagicMock(return_value=[]) 


    # Mock GameState methods directly used or relied upon by AI
    gs._has_line_of_sight = MagicMock(return_value=False) # Default: no LoS
    gs._find_path_bfs = MagicMock(return_value=None)      # Default: no path found
    gs._is_walkable_for_entity = MagicMock(return_value=True) # Default: all tiles walkable for monster

    # Combat resolution is patched in specific tests where needed.

    gs.game_over = False
    gs.logger = MagicMock()
    return gs

@pytest.fixture
def chaser_monster_data() -> dict:
    """Provides a sample monster dictionary for a chaser AI."""
    template = MONSTER_TEMPLATES[TILE_MONSTER_GOBLIN] 
    return {
        "id": "test_goblin_chaser", "x": 5, "y": 5, "type_name": "goblin",
        **template, # Includes hp, attack, defense, detection_radius, move_chance, ai_type
        "hp": template["hp"], # Ensure current HP is set from template's base HP
        "max_hp": template["max_hp"],
        "last_known_player_pos": None,
        "turns_since_player_seen": 0,
        "ai_state": "idle" # Initial state
    }

# --- ChaserAI Tests ---

def test_chaser_ai_attacks_if_player_adjacent_and_los(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 1, 0 # Monster next to player at (0,0)
    mock_gs.player.pos = {"x": 0, "y": 0}

    mock_gs._has_line_of_sight.return_value = True 
    mock_gs._find_path_bfs.return_value = [{"x": 1, "y": 0}, {"x": 0, "y": 0}] 

    with patch('app.core.monsters.ai.apply_attack') as mock_apply_attack, \
         patch('app.core.monsters.ai.resolve_monster_attack_on_player') as mock_resolve_attack:
        
        mock_apply_attack.return_value = (2, mock_gs.player.hp - 2, False, "Goblin hits you for 2 damage.")
        
        dummy_player_stats_response = PlayerStatsResponse(
            hp=mock_gs.player.hp-2, max_hp=mock_gs.player.hp, attack=5, defense=2, level=1, xp=0, xp_to_next_level=100,
            inventory=[], equipment={"weapon":None, "armor":None}
        )
        mock_resolve_attack.return_value = [
            CombatEventServerResponse(
                attacker_id=monster["id"], defender_faction="player", damage_done=2, 
                defender_hp_current=mock_gs.player.hp-2, defender_hp_max=mock_gs.player.hp, 
                message="Test Attack"
            ),
            PlayerStatsUpdateServerResponse(stats=dummy_player_stats_response)
        ]

        responses = ai.execute_turn(monster, mock_gs)

    mock_gs._has_line_of_sight.assert_called_once_with({"x": 1, "y": 0}, {"x": 0, "y": 0})
    mock_apply_attack.assert_called_once()
    mock_resolve_attack.assert_called_once()
    
    assert monster["ai_state"] == "chasing" 
    assert monster["last_known_player_pos"] == {"x": 0, "y": 0}
    assert monster["x"] == 1 and monster["y"] == 0 

    assert any(isinstance(r, CombatEventServerResponse) for r in responses), "Expected CombatEvent response"
    assert not any(isinstance(r, MonsterMovedServerResponse) for r in responses), "Monster should not move if it attacked"


def test_chaser_ai_moves_towards_player_if_los_and_path(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 2, 0 
    mock_gs.player.pos = {"x": 0, "y": 0}

    mock_gs._has_line_of_sight.return_value = True 
    mock_gs._find_path_bfs.return_value = [
        {"x": 2, "y": 0}, {"x": 1, "y": 0}, {"x": 0, "y": 0}
    ]
    mock_gs._is_walkable_for_entity.return_value = True 

    # Make monster's starting tile visible on client map for _handle_monster_move_on_map_and_responses
    mock_gs.map_manager.dungeon_map_for_client[0][2] = TILE_FLOOR 

    responses = ai.execute_turn(monster, mock_gs)

    mock_gs._find_path_bfs.assert_called_once_with({"x": 2, "y": 0}, {"x": 0, "y": 0}, "monster")
    mock_gs._is_walkable_for_entity.assert_any_call(1, 0, "monster") 
    
    assert monster["x"] == 1 and monster["y"] == 0 
    assert monster["ai_state"] == "chasing"
    assert monster["last_known_player_pos"] == {"x": 0, "y": 0}
    
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses), "Expected MonsterMoved response"
    # Verify the old monster position on client map is now TILE_FLOOR (done by helper)
    assert mock_gs.map_manager.dungeon_map_for_client[0][2] == TILE_FLOOR 


def test_chaser_ai_moves_to_lkp_if_no_los(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 5, 5
    monster["last_known_player_pos"] = {"x": 1, "y": 1} 
    monster["turns_since_player_seen"] = 1 
    monster["ai_state"] = "searching_lkp" 
    
    mock_gs.player.pos = {"x": 0, "y": 0} 
    mock_gs._has_line_of_sight.return_value = False 
    mock_gs._find_path_bfs.return_value = [{"x": 5, "y": 5}, {"x": 4, "y": 5}] 

    responses = ai.execute_turn(monster, mock_gs)

    mock_gs._find_path_bfs.assert_called_once_with({"x": 5, "y": 5}, {"x": 1, "y": 1}, "monster") 
    assert monster["x"] == 4 and monster["y"] == 5 
    assert monster["ai_state"] == "searching_lkp" 
    assert monster["turns_since_player_seen"] == 2 
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses), "Expected MonsterMoved response"


def test_chaser_ai_lkp_times_out(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 5, 5
    monster["last_known_player_pos"] = {"x": 1, "y": 1}
    monster["turns_since_player_seen"] = game_config.MONSTER_LKP_TIMEOUT_TURNS -1 
    monster["ai_state"] = "searching_lkp"

    mock_gs.player.pos = {"x": 0, "y": 0}
    mock_gs._has_line_of_sight.return_value = False
    mock_gs._find_path_bfs.return_value = None 

    with patch('random.random', return_value=1.0): 
        responses = ai.execute_turn(monster, mock_gs)

    assert monster["ai_state"] == "idle" 
    assert monster["last_known_player_pos"] is None 
    assert monster["turns_since_player_seen"] == game_config.MONSTER_LKP_TIMEOUT_TURNS
    # No move expected here, so no MonsterMovedServerResponse should be in responses list
    assert not any(isinstance(r, MonsterMovedServerResponse) for r in responses)


def test_chaser_ai_idle_random_move(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 5, 5
    monster["ai_state"] = "idle" 
    monster["move_chance"] = 0.5 

    mock_gs.player.pos = {"x": 0, "y": 0} 
    mock_gs._has_line_of_sight.return_value = False
    mock_gs._find_path_bfs.return_value = None 

    def custom_is_walkable(x, y, entity_type):
        return (x == 5 and y == 6)
    mock_gs._is_walkable_for_entity.side_effect = custom_is_walkable
    
    with patch('random.random', return_value=0.4), \
         patch('random.choice', return_value=(5,6)) as mock_random_choice: 
        
        responses = ai.execute_turn(monster, mock_gs)

    mock_random_choice.assert_called_once_with([(5,6)])
    
    assert monster["x"] == 5 and monster["y"] == 6 
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses), "Expected MonsterMoved response"


def test_chaser_ai_idle_no_random_move(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 5, 5
    monster["ai_state"] = "idle"
    monster["move_chance"] = 0.5 

    mock_gs.player.pos = {"x": 0, "y": 0} 
    mock_gs._has_line_of_sight.return_value = False
    mock_gs._find_path_bfs.return_value = None 

    with patch('random.random', return_value=0.6): 
        responses = ai.execute_turn(monster, mock_gs)

    assert monster["x"] == 5 and monster["y"] == 5 # Monster should not have moved
    assert not any(isinstance(r, MonsterMovedServerResponse) for r in responses)