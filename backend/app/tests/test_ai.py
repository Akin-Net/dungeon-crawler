# backend/app/tests/test_ai.py
import pytest
from unittest.mock import MagicMock, patch, PropertyMock, call 
import random

# Removed _handle_monster_move_on_map_and_responses from direct import for patching in tests
from app.core.monsters.ai import ChaserAI, RangedAI 
from app.core.monsters.definitions import MONSTER_TEMPLATES, TILE_MONSTER_GOBLIN, TILE_MONSTER_SKELETON 
from app.core.game_state import GameState 
from app.core.player import Player 
from app.core.map_manager import MapManager 
from app.core.tiles import TILE_FLOOR, TILE_FOG 
from app.core import config as game_config
from app.schemas import ( 
    MonsterMovedServerResponse, CombatEventServerResponse, 
    PlayerStatsUpdateServerResponse, PlayerDiedServerResponse,
    PlayerStatsResponse, InventoryItemDetail, Position 
)

# --- Mock Client Map Storage ---
_mock_client_map_storage_for_ai_tests = [[TILE_FOG for _ in range(10)] for _ in range(10)]

def get_mock_row_for_ai_tests(y_index):
    if 0 <= y_index < len(_mock_client_map_storage_for_ai_tests):
        return _mock_client_map_storage_for_ai_tests[y_index]
    else:
        raise IndexError("list index out of range")

@pytest.fixture(autouse=True) 
def reset_mock_client_map():
    global _mock_client_map_storage_for_ai_tests
    _mock_client_map_storage_for_ai_tests = [[TILE_FOG for _ in range(10)] for _ in range(10)]


@pytest.fixture
def mock_gs() -> MagicMock:
    gs = MagicMock(spec=GameState)
    gs.player = MagicMock(spec=Player)
    gs.player.pos = {"x": 0, "y": 0} 
    gs.player.hp = game_config.PLAYER_INITIAL_HP
    mock_player_stats = PlayerStatsResponse(
        hp=game_config.PLAYER_INITIAL_HP, max_hp=game_config.PLAYER_INITIAL_MAX_HP,
        attack=game_config.PLAYER_INITIAL_ATTACK, defense=game_config.PLAYER_INITIAL_DEFENSE,
        level=1, xp=0, xp_to_next_level=100, inventory=[], equipment={"weapon": None, "armor": None} 
    )
    gs.player.get_effective_stats = MagicMock(return_value=mock_player_stats.model_dump()) 
    gs.player.take_damage = MagicMock(return_value=False) 
    gs.player.create_player_stats_response = MagicMock(return_value=mock_player_stats)
    gs.map_manager = MagicMock(spec=MapManager)
    gs.map_manager.actual_dungeon_map = [[TILE_FLOOR for _ in range(10)] for _ in range(10)]
    gs.map_manager.dungeon_map_for_client = MagicMock()
    gs.map_manager.dungeon_map_for_client.__getitem__.side_effect = get_mock_row_for_ai_tests
    gs.map_manager.dungeon_map_for_client.__len__.side_effect = lambda: len(_mock_client_map_storage_for_ai_tests)
    gs.map_manager.update_fov = MagicMock(return_value=[]) 
    gs._has_line_of_sight = MagicMock(return_value=False) 
    gs._find_path_bfs = MagicMock(return_value=None)      
    gs._is_walkable_for_entity = MagicMock(return_value=True) 
    gs.game_over = False
    gs.logger = MagicMock()
    return gs


@pytest.fixture
def chaser_monster_data() -> dict:
    template = MONSTER_TEMPLATES[TILE_MONSTER_GOBLIN] 
    return {
        "id": "test_goblin_chaser", "x": 5, "y": 5, "type_name": "goblin",
        **template, 
        "hp": template["hp"], "max_hp": template["max_hp"],
        "last_known_player_pos": None, "turns_since_player_seen": 0, "ai_state": "idle" 
    }

@pytest.fixture
def ranged_monster_data() -> dict:
    template = MONSTER_TEMPLATES[TILE_MONSTER_SKELETON] 
    return {
        "id": "test_skeleton_ranged", "x": 5, "y": 5, "type_name": "skeleton",
        **template, "hp": template["hp"], "max_hp": template["max_hp"],
        "last_known_player_pos": None, "turns_since_player_seen": 0, "ai_state": "idle" 
    }

# --- ChaserAI Tests ---
def test_chaser_ai_attacks_if_player_adjacent_and_los(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 1, 0 
    mock_gs.player.pos = {"x": 0, "y": 0}

    mock_gs._has_line_of_sight.reset_mock()
    mock_gs._find_path_bfs.reset_mock()
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
                defender_hp_current=mock_gs.player.hp-2, defender_hp_max=mock_gs.player.hp, message="Test Attack"
            ), PlayerStatsUpdateServerResponse(stats=dummy_player_stats_response)
        ]
        responses = ai.execute_turn(monster, mock_gs)
    mock_gs._has_line_of_sight.assert_called_once_with({"x": 1, "y": 0}, {"x": 0, "y": 0})
    mock_apply_attack.assert_called_once()
    mock_resolve_attack.assert_called_once()
    assert monster["ai_state"] == "chasing" 
    assert monster["last_known_player_pos"] == {"x": 0, "y": 0}
    assert monster["x"] == 1 and monster["y"] == 0 
    assert any(isinstance(r, CombatEventServerResponse) for r in responses)
    assert not any(isinstance(r, MonsterMovedServerResponse) for r in responses)

def test_chaser_ai_moves_towards_player_if_los_and_path(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 2, 0 
    mock_gs.player.pos = {"x": 0, "y": 0}

    mock_gs._has_line_of_sight.reset_mock()
    mock_gs._find_path_bfs.reset_mock()
    mock_gs._is_walkable_for_entity.reset_mock()
    mock_gs._has_line_of_sight.return_value = True 
    mock_gs._find_path_bfs.return_value = [{"x": 2, "y": 0}, {"x": 1, "y": 0}, {"x": 0, "y": 0}]
    mock_gs._is_walkable_for_entity.return_value = True 

    global _mock_client_map_storage_for_ai_tests
    _mock_client_map_storage_for_ai_tests[0][2] = TILE_FLOOR 
    responses = ai.execute_turn(monster, mock_gs)
    mock_gs._find_path_bfs.assert_called_once_with({"x": 2, "y": 0}, {"x": 0, "y": 0}, "monster")
    mock_gs._is_walkable_for_entity.assert_any_call(1, 0, "monster") 
    assert monster["x"] == 1 and monster["y"] == 0 
    assert monster["ai_state"] == "chasing"
    assert monster["last_known_player_pos"] == {"x": 0, "y": 0}
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses)
    assert _mock_client_map_storage_for_ai_tests[0][2] == TILE_FLOOR 

def test_chaser_ai_moves_to_lkp_if_no_los(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 5, 5
    monster["last_known_player_pos"] = {"x": 1, "y": 1} 
    monster["turns_since_player_seen"] = 1 
    monster["ai_state"] = "searching_lkp" 
    mock_gs.player.pos = {"x": 0, "y": 0} 

    mock_gs._has_line_of_sight.reset_mock()
    mock_gs._find_path_bfs.reset_mock()
    mock_gs._has_line_of_sight.return_value = False 
    mock_gs._find_path_bfs.return_value = [{"x": 5, "y": 5}, {"x": 4, "y": 5}] 

    responses = ai.execute_turn(monster, mock_gs)
    mock_gs._find_path_bfs.assert_called_once_with({"x": 5, "y": 5}, {"x": 1, "y": 1}, "monster") 
    assert monster["x"] == 4 and monster["y"] == 5 
    assert monster["ai_state"] == "searching_lkp" 
    assert monster["turns_since_player_seen"] == 2 
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses)

def test_chaser_ai_lkp_times_out(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 5, 5
    monster["last_known_player_pos"] = {"x": 1, "y": 1}
    monster["turns_since_player_seen"] = game_config.MONSTER_LKP_TIMEOUT_TURNS -1 
    monster["ai_state"] = "searching_lkp"
    mock_gs.player.pos = {"x": 0, "y": 0}

    mock_gs._has_line_of_sight.reset_mock()
    mock_gs._find_path_bfs.reset_mock()
    mock_gs._has_line_of_sight.return_value = False
    mock_gs._find_path_bfs.return_value = None 

    with patch('random.random', return_value=1.0): # Ensure no random move if LKP times out
        responses = ai.execute_turn(monster, mock_gs)
    assert monster["ai_state"] == "idle" 
    assert monster["last_known_player_pos"] is None 
    assert monster["turns_since_player_seen"] == game_config.MONSTER_LKP_TIMEOUT_TURNS
    assert not any(isinstance(r, MonsterMovedServerResponse) for r in responses)

def test_chaser_ai_idle_random_move(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 5, 5
    monster["ai_state"] = "idle" 
    monster["move_chance"] = 0.5 
    mock_gs.player.pos = {"x": 0, "y": 0} 

    mock_gs._has_line_of_sight.reset_mock()
    mock_gs._find_path_bfs.reset_mock()
    mock_gs._is_walkable_for_entity.reset_mock()
    mock_gs._has_line_of_sight.return_value = False
    mock_gs._find_path_bfs.return_value = None 
    def custom_is_walkable(x, y, entity_type): return (x == 5 and y == 6)
    mock_gs._is_walkable_for_entity.side_effect = custom_is_walkable

    with patch('random.random', return_value=0.4), \
         patch('random.choice', return_value=(5,6)) as mock_random_choice: 
        responses = ai.execute_turn(monster, mock_gs)
    mock_random_choice.assert_called_once_with([(5,6)])
    assert monster["x"] == 5 and monster["y"] == 6 
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses)

def test_chaser_ai_idle_no_random_move(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 5, 5
    monster["ai_state"] = "idle"; monster["move_chance"] = 0.5 
    mock_gs.player.pos = {"x": 0, "y": 0} 
    mock_gs._has_line_of_sight.reset_mock()
    mock_gs._find_path_bfs.reset_mock()
    mock_gs._has_line_of_sight.return_value = False
    mock_gs._find_path_bfs.return_value = None 
    with patch('random.random', return_value=0.6): 
        responses = ai.execute_turn(monster, mock_gs)
    assert monster["x"] == 5 and monster["y"] == 5 
    assert not any(isinstance(r, MonsterMovedServerResponse) for r in responses)

def test_chaser_ai_no_path_attempts_random_move(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    monster["x"], monster["y"] = 2, 0 
    mock_gs.player.pos = {"x": 0, "y": 0}

    mock_gs._has_line_of_sight.reset_mock()
    mock_gs._find_path_bfs.reset_mock()
    mock_gs._is_walkable_for_entity.reset_mock()
    mock_gs._has_line_of_sight.return_value = True 
    mock_gs._find_path_bfs.return_value = None 

    with patch('random.random', return_value=0.5): 
        def specific_random_walkable(x,y,entity_type): return (x,y) in [(3,0),(1,0),(2,1),(2,-1)] and entity_type=="monster"
        mock_gs._is_walkable_for_entity.side_effect = specific_random_walkable
        with patch('random.choice', return_value=(3,0)) as mock_random_choice:
            global _mock_client_map_storage_for_ai_tests
            _mock_client_map_storage_for_ai_tests[0][2] = TILE_FLOOR 
            responses = ai.execute_turn(monster, mock_gs)
    mock_gs._find_path_bfs.assert_called_once_with({"x": 2, "y": 0}, {"x": 0, "y": 0}, "monster")
    mock_gs._is_walkable_for_entity.assert_any_call(3,0,"monster"); mock_gs._is_walkable_for_entity.assert_any_call(1,0,"monster")
    mock_gs._is_walkable_for_entity.assert_any_call(2,1,"monster"); mock_gs._is_walkable_for_entity.assert_any_call(2,-1,"monster")
    mock_random_choice.assert_called_once_with([(2,1), (2,-1), (3,0), (1,0)]) 
    assert monster["x"] == 3 and monster["y"] == 0 
    assert monster["ai_state"] == "chasing" 
    assert monster["last_known_player_pos"] == {"x": 0, "y": 0}
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses)
    assert _mock_client_map_storage_for_ai_tests[0][2] == TILE_FLOOR 

def test_chaser_ai_reaches_lkp_becomes_idle(mock_gs: MagicMock, chaser_monster_data: dict):
    ai = ChaserAI()
    monster = chaser_monster_data
    
    monster["x"], monster["y"] = 1, 0
    monster["last_known_player_pos"] = {"x": 0, "y": 0} 
    monster["turns_since_player_seen"] = 1
    monster["ai_state"] = "searching_lkp"
    
    mock_gs.player.pos = {"x": 5, "y": 5} 
    
    mock_gs._has_line_of_sight.reset_mock()
    mock_gs._find_path_bfs.reset_mock()
    mock_gs._is_walkable_for_entity.reset_mock()

    mock_gs._has_line_of_sight.return_value = False
    mock_gs._find_path_bfs.return_value = [{"x": 1, "y": 0}, {"x": 0, "y": 0}]
    mock_gs._is_walkable_for_entity.return_value = True 

    global _mock_client_map_storage_for_ai_tests 
    _mock_client_map_storage_for_ai_tests[0][1] = TILE_FLOOR 

    # Patch random.random to ensure "no path random move" and "idle random move" don't trigger if logic is flawed
    with patch('random.random', return_value=1.0):
        responses = ai.execute_turn(monster, mock_gs)

    assert monster["x"] == 0 and monster["y"] == 0 
    assert monster["ai_state"] == "idle"
    assert monster["last_known_player_pos"] is None
    assert monster["turns_since_player_seen"] == 2 
    
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses)
    moved_response = next(r for r in responses if isinstance(r, MonsterMovedServerResponse))
    assert moved_response.new_pos == Position(x=0, y=0)
    assert _mock_client_map_storage_for_ai_tests[0][1] == TILE_FLOOR


# --- RangedAI Tests ---
def test_ranged_ai_attacks_if_player_in_los_and_range(mock_gs: MagicMock, ranged_monster_data: dict):
    ai = RangedAI(); monster = ranged_monster_data
    monster["x"], monster["y"] = 3,0; monster["attack_range"]=5; mock_gs.player.pos = {"x":0,"y":0}
    mock_gs._has_line_of_sight.reset_mock(); mock_gs._has_line_of_sight.return_value = True
    with patch('app.core.monsters.ai.apply_attack') as mock_apply_attack, \
         patch('app.core.monsters.ai.resolve_monster_attack_on_player') as mock_resolve_attack:
        mock_apply_attack.return_value = (1, mock_gs.player.hp-1, False, "Skel shoots")
        dummy_stats = PlayerStatsResponse(hp=mock_gs.player.hp-1,max_hp=mock_gs.player.hp,attack=1,defense=1,level=1,xp=0,xp_to_next_level=100,inventory=[],equipment={})
        mock_resolve_attack.return_value = [CombatEventServerResponse(attacker_id="id",damage_done=1,defender_hp_current=1,defender_hp_max=1,message=""), PlayerStatsUpdateServerResponse(stats=dummy_stats)]
        responses = ai.execute_turn(monster,mock_gs)
    mock_gs._has_line_of_sight.assert_called_once_with({"x":3,"y":0},{"x":0,"y":0})
    mock_apply_attack.assert_called_once(); mock_resolve_attack.assert_called_once()
    assert monster["ai_state"]=="engaging"; assert monster["last_known_player_pos"]=={"x":0,"y":0}
    assert monster["x"]==3 and monster["y"]==0; assert any(isinstance(r,CombatEventServerResponse) for r in responses)
    assert not any(isinstance(r,MonsterMovedServerResponse) for r in responses)

def test_ranged_ai_moves_closer_if_player_in_los_but_out_of_range(mock_gs: MagicMock, ranged_monster_data: dict):
    ai = RangedAI(); monster = ranged_monster_data
    monster["x"],monster["y"]=7,0; monster["attack_range"]=5; mock_gs.player.pos={"x":0,"y":0}
    mock_gs._has_line_of_sight.reset_mock(); mock_gs._has_line_of_sight.return_value = True
    mock_gs._find_path_bfs.reset_mock(); mock_gs._find_path_bfs.return_value = [{"x":7,"y":0},{"x":6,"y":0}]
    mock_gs._is_walkable_for_entity.reset_mock(); mock_gs._is_walkable_for_entity.return_value=True
    global _mock_client_map_storage_for_ai_tests; _mock_client_map_storage_for_ai_tests[0][7] = TILE_FLOOR
    responses = ai.execute_turn(monster,mock_gs)
    mock_gs._find_path_bfs.assert_called_with({"x":7,"y":0},{"x":0,"y":0},"monster")
    assert monster["x"]==6 and monster["y"]==0; assert monster["ai_state"]=="engaging"
    assert any(isinstance(r,MonsterMovedServerResponse) for r in responses)
    assert _mock_client_map_storage_for_ai_tests[0][7] == TILE_FLOOR

def test_ranged_ai_kites_if_player_adjacent_and_los(mock_gs: MagicMock, ranged_monster_data: dict):
    ai = RangedAI(); monster = ranged_monster_data
    monster["x"],monster["y"]=1,0; monster["attack_range"]=5; mock_gs.player.pos={"x":0,"y":0}
    mock_gs._has_line_of_sight.reset_mock(); mock_gs._has_line_of_sight.return_value = True
    mock_gs._is_walkable_for_entity.reset_mock()
    def custom_is_walkable(x,y,entity_type): return (x==2 and y==0)
    mock_gs._is_walkable_for_entity.side_effect=custom_is_walkable
    global _mock_client_map_storage_for_ai_tests; _mock_client_map_storage_for_ai_tests[0][1]=TILE_FLOOR
    responses = ai.execute_turn(monster,mock_gs)
    mock_gs._find_path_bfs.assert_not_called()
    assert monster["x"]==2 and monster["y"]==0; assert monster["ai_state"]=="engaging"
    assert any(isinstance(r,MonsterMovedServerResponse) for r in responses)
    assert _mock_client_map_storage_for_ai_tests[0][1]==TILE_FLOOR

def test_ranged_ai_moves_to_lkp_if_no_los(mock_gs: MagicMock, ranged_monster_data: dict):
    ai=RangedAI(); monster=ranged_monster_data
    monster["x"],monster["y"]=5,5; monster["last_known_player_pos"]={"x":1,"y":1}
    monster["turns_since_player_seen"]=1; monster["ai_state"]="searching_lkp"
    mock_gs.player.pos={"x":0,"y":0}
    mock_gs._has_line_of_sight.reset_mock(); mock_gs._has_line_of_sight.return_value=False
    mock_gs._find_path_bfs.reset_mock(); mock_gs._find_path_bfs.return_value = [{"x":5,"y":5},{"x":4,"y":5}]
    responses=ai.execute_turn(monster,mock_gs)
    mock_gs._find_path_bfs.assert_called_with({"x":5,"y":5},{"x":1,"y":1},"monster")
    assert monster["x"]==4 and monster["y"]==5; assert monster["ai_state"]=="searching_lkp"
    assert monster["turns_since_player_seen"]==2; assert any(isinstance(r,MonsterMovedServerResponse) for r in responses)

def test_ranged_ai_lkp_times_out_becomes_idle(mock_gs: MagicMock, ranged_monster_data: dict):
    ai=RangedAI(); monster=ranged_monster_data
    monster["x"],monster["y"]=5,5; monster["last_known_player_pos"]={"x":1,"y":1}
    monster["turns_since_player_seen"]=game_config.MONSTER_LKP_TIMEOUT_TURNS-1
    monster["ai_state"]="searching_lkp"
    mock_gs.player.pos={"x":0,"y":0}
    mock_gs._has_line_of_sight.reset_mock(); mock_gs._has_line_of_sight.return_value=False
    mock_gs._find_path_bfs.reset_mock(); mock_gs._find_path_bfs.return_value=None
    with patch('random.random',return_value=1.0): responses=ai.execute_turn(monster,mock_gs)
    assert monster["ai_state"]=="idle"; assert monster["last_known_player_pos"] is None
    assert monster["turns_since_player_seen"]==game_config.MONSTER_LKP_TIMEOUT_TURNS
    assert not any(isinstance(r,MonsterMovedServerResponse) for r in responses)

def test_ranged_ai_idle_random_move(mock_gs: MagicMock, ranged_monster_data: dict):
    ai=RangedAI(); monster=ranged_monster_data
    monster["x"],monster["y"]=5,5; monster["ai_state"]="idle"; monster["move_chance"]=0.7
    mock_gs.player.pos={"x":0,"y":0}
    mock_gs._has_line_of_sight.reset_mock(); mock_gs._has_line_of_sight.return_value=False
    mock_gs._find_path_bfs.reset_mock(); mock_gs._find_path_bfs.return_value=None
    mock_gs._is_walkable_for_entity.reset_mock()
    def custom_is_walkable(x,y,entity_type): return(x==5 and y==4)
    mock_gs._is_walkable_for_entity.side_effect=custom_is_walkable
    with patch('random.random',return_value=0.4), patch('random.choice',return_value=(5,4)) as mrc:
        responses=ai.execute_turn(monster,mock_gs)
    mrc.assert_called_once_with([(5,4)]); assert monster["x"]==5 and monster["y"]==4
    assert any(isinstance(r,MonsterMovedServerResponse) for r in responses)

def test_ranged_ai_no_path_to_target_attempts_random_move(mock_gs: MagicMock, ranged_monster_data: dict):
    ai=RangedAI(); monster=ranged_monster_data
    monster["x"],monster["y"]=7,0; monster["attack_range"]=5; monster["ai_state"]="engaging"
    mock_gs.player.pos={"x":0,"y":0}
    mock_gs._has_line_of_sight.reset_mock(); mock_gs._has_line_of_sight.return_value=True
    mock_gs._find_path_bfs.reset_mock(); mock_gs._find_path_bfs.return_value=None
    mock_gs._is_walkable_for_entity.reset_mock()
    with patch('random.random',return_value=0.5):
        def srw(x,y,et): return (x,y)==(7,1) and et=="monster"
        mock_gs._is_walkable_for_entity.side_effect=srw
        with patch('random.choice',return_value=(7,1)) as mrc:
            global _mock_client_map_storage_for_ai_tests
            _mock_client_map_storage_for_ai_tests[0][7]=TILE_FLOOR
            responses=ai.execute_turn(monster,mock_gs)
    mock_gs._find_path_bfs.assert_called_with({"x":7,"y":0},{"x":0,"y":0},"monster")
    mrc.assert_called_once_with([(7,1)]); assert monster["x"]==7 and monster["y"]==1
    assert any(isinstance(r,MonsterMovedServerResponse) for r in responses)
    assert _mock_client_map_storage_for_ai_tests[0][7]==TILE_FLOOR

def test_ranged_ai_reaches_lkp_becomes_idle(mock_gs: MagicMock, ranged_monster_data: dict):
    ai = RangedAI() 
    monster = ranged_monster_data
    monster["x"], monster["y"] = 1, 0
    monster["last_known_player_pos"] = {"x": 0, "y": 0} 
    monster["turns_since_player_seen"] = 2 
    monster["ai_state"] = "searching_lkp"
    mock_gs.player.pos = {"x": 5, "y": 5} 
    mock_gs._has_line_of_sight.reset_mock(); mock_gs._has_line_of_sight.return_value = False 
    mock_gs._find_path_bfs.reset_mock(); mock_gs._find_path_bfs.return_value = [{"x": 1, "y": 0}, {"x": 0, "y": 0}]
    mock_gs._is_walkable_for_entity.reset_mock(); mock_gs._is_walkable_for_entity.return_value = True
    
    with patch('random.random', return_value=1.0): # Prevent random moves
        responses = ai.execute_turn(monster, mock_gs)

    assert monster["x"] == 0 and monster["y"] == 0 
    assert monster["ai_state"] == "idle"
    assert monster["last_known_player_pos"] is None
    assert monster["turns_since_player_seen"] == 3 
    assert any(isinstance(r, MonsterMovedServerResponse) for r in responses)