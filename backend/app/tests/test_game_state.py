# backend/app/tests/test_game_state.py
import pytest
from unittest.mock import MagicMock, patch
import random
import uuid 

from app.core.game_state import GameState
from app.core.player import Player
from app.core.map_manager import MapManager
from app.core.entity_manager import EntityManager
from app.core.dungeon_generator import DungeonGenerator, Room
from app.core import config as game_config
from app.core.tiles import (
    TILE_FLOOR, TILE_WALL, TILE_DOOR_CLOSED, TILE_DOOR_OPEN, 
    TILE_ITEM_POTION, TILE_STAIRS_DOWN, TILE_FOG, TILE_ITEM_SCROLL_TELEPORT
)
from app.core.items.definitions import (
    ITEM_TYPE_POTION_HEAL, ITEM_TYPE_WEAPON_DAGGER, MAP_TILE_TO_ITEM_TYPE,
    ITEM_TYPE_SCROLL_TELEPORT, ITEM_TEMPLATES, ITEM_TYPE_ARMOR_LEATHER
)
from app.core.monsters.definitions import MONSTER_TEMPLATES, TILE_MONSTER_GOBLIN
from app.schemas import (
    DungeonDataServerResponse,
    PlayerMovedServerResponse,
    TileChangeServerResponse,
    GameMessageServerResponse,
    PlayerStatsUpdateServerResponse,
    CombatEventServerResponse,
    EntityDiedServerResponse,
    MonsterAppearedServerResponse,
    InvalidMoveServerResponse,
    PlayerDiedServerResponse,
    Position,
    MonsterMovedServerResponse 
)

# Helper function needs to be at module level or accessible to tests using it
def find_walkable_adjacent_tile_for_test(gs: GameState) -> tuple[int, int, int, int]:
    if not gs.player.pos or not gs.map_manager.actual_dungeon_map:
        raise ValueError("Player position or map not set for find_walkable_adjacent_tile_for_test")
    player_x, player_y = gs.player.pos["x"], gs.player.pos["y"]
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]: 
        target_x, target_y = player_x + dx, player_y + dy
        if 0 <= target_y < len(gs.map_manager.actual_dungeon_map) and \
           0 <= target_x < len(gs.map_manager.actual_dungeon_map[0]):
            tile_type = gs.map_manager.actual_dungeon_map[target_y][target_x]
            if tile_type == TILE_FLOOR and (gs.entity_manager.get_monster_at(target_x, target_y) is None):
                return player_x, player_y, target_x, target_y
    for y_scan in range(len(gs.map_manager.actual_dungeon_map)):
        for x_scan in range(len(gs.map_manager.actual_dungeon_map[0])):
            if gs.map_manager.actual_dungeon_map[y_scan][x_scan] == TILE_FLOOR and \
               gs.entity_manager.get_monster_at(x_scan, y_scan) is None and \
               not (gs.player.pos["x"] == x_scan and gs.player.pos["y"] == y_scan) :
                original_player_pos_temp = gs.player.pos.copy()
                gs.player.pos = {"x":x_scan, "y":y_scan}
                try:
                    px, py, tx, ty = find_walkable_adjacent_tile_for_test(gs) 
                    return px, py, tx, ty 
                except AssertionError:
                    gs.player.pos = original_player_pos_temp 
                    continue 
    raise AssertionError("Could not find a walkable adjacent empty floor tile for testing move in find_walkable_adjacent_tile_for_test.")


@pytest.fixture
def game_state_instance() -> GameState:
    gs = GameState(client_id="test_client_websocket")
    gs.logger = MagicMock()
    gs.map_manager.logger = MagicMock() 
    gs.entity_manager.logger_ref = MagicMock() 
    gs.player.logger = MagicMock() 
    gs.generate_new_dungeon(seed=1, is_new_level=False) 
    return gs

@pytest.fixture
def game_state_no_init() -> GameState:
    gs = GameState(client_id="test_client_no_init")
    gs.logger = MagicMock()
    gs.map_manager.logger = MagicMock()
    gs.entity_manager.logger_ref = MagicMock()
    gs.player.logger = MagicMock()
    # Ensure these are MagicMock instances on the fixture object
    gs._has_line_of_sight = MagicMock()
    gs._find_path_bfs = MagicMock()
    return gs


def add_item_to_player(player: Player, item_type_key: str) -> str:
    item_instance_data = player.add_item_to_inventory(item_type_key)
    assert item_instance_data is not None, f"Failed to add {item_type_key} to inventory for test setup"
    return item_instance_data["id"]


def find_specific_tile_adjacent(gs: GameState, tile_to_find: int) -> tuple[int, int, int, int]:
    if gs.player.pos is None or not gs.map_manager.actual_dungeon_map:
        raise ValueError("Player position or map not set for find_specific_tile_adjacent")
    player_x, player_y = gs.player.pos["x"], gs.player.pos["y"]
    for dx_offset, dy_offset in [(0, -1), (0, 1), (-1, 0), (1, 0)]: 
        target_x_candidate, target_y_candidate = player_x + dx_offset, player_y + dy_offset
        if 0 <= target_y_candidate < len(gs.map_manager.actual_dungeon_map) and \
           0 <= target_x_candidate < len(gs.map_manager.actual_dungeon_map[0]):
            if gs.map_manager.actual_dungeon_map[target_y_candidate][target_x_candidate] == tile_to_find:
                return player_x, player_y, target_x_candidate, target_y_candidate
    for y_scan in range(len(gs.map_manager.actual_dungeon_map)):
        for x_scan in range(len(gs.map_manager.actual_dungeon_map[0])):
            if gs.map_manager.actual_dungeon_map[y_scan][x_scan] == tile_to_find:
                for dx_adj, dy_adj in [(0,1), (0,-1), (1,0), (-1,0), (-1,-1), (1,-1), (-1,1), (1,1)]: 
                    adj_x, adj_y = x_scan + dx_adj, y_scan + dy_adj
                    if 0 <= adj_y < len(gs.map_manager.actual_dungeon_map) and \
                       0 <= adj_x < len(gs.map_manager.actual_dungeon_map[0]) and \
                       gs.map_manager.actual_dungeon_map[adj_y][adj_x] == TILE_FLOOR and \
                       gs.entity_manager.get_monster_at(adj_x, adj_y) is None:
                        gs.player.pos = {"x": adj_x, "y": adj_y} 
                        if gs.map_manager.dungeon_map_for_client: 
                           gs.map_manager.update_fov(gs.player.pos) 
                        return adj_x, adj_y, x_scan, y_scan 
    raise AssertionError(f"Could not find tile {tile_to_find} or a place to move player next to it.")


def test_generate_new_dungeon_initial_game(game_state_no_init: GameState):
    gs = game_state_no_init
    # For generate_new_dungeon, we want it to use its real internal logic,
    # not necessarily the top-level mocks on gs if they were to interfere.
    # This ensures that if generate_new_dungeon calls MapManager methods that use LoS,
    # it's the real MapManager LoS being tested.
    gs._has_line_of_sight.side_effect = lambda s_pos, e_pos: GameState._has_line_of_sight(gs, s_pos, e_pos)
    gs._find_path_bfs.side_effect = lambda s_pos, e_pos, et, em, pp: GameState._find_path_bfs(gs, s_pos, e_pos, et, em, pp)

    test_seed = 12345
    response = gs.generate_new_dungeon(seed=test_seed,is_new_level=False)
    
    # Restore mocks to default behavior if other tests using this fixture expect them to be simple Mocks
    gs._has_line_of_sight.side_effect = None
    gs._find_path_bfs.side_effect = None


    assert isinstance(response, DungeonDataServerResponse)
    assert gs.current_dungeon_level == 1
    assert not gs.game_over
    assert gs.seed == test_seed
    assert gs.player.hp == game_config.PLAYER_INITIAL_HP
    inventory_type_keys = [item['type_key'] for item in gs.player.inventory]
    assert ITEM_TYPE_POTION_HEAL in inventory_type_keys
    assert gs.player.equipment["weapon"]["type_key"] == ITEM_TYPE_WEAPON_DAGGER
    assert gs.map_manager.actual_dungeon_map is not None
    if gs.map_manager.generated_rooms: 
        assert len(gs.map_manager.generated_rooms) > 0
    player_x, player_y = gs.player.pos["x"], gs.player.pos["y"]
    assert gs.map_manager.actual_dungeon_map[player_y][player_x] == TILE_FLOOR
    for monster in gs.entity_manager.get_all_monsters():
        assert gs.map_manager.actual_dungeon_map[monster["y"]][monster["x"]] == TILE_FLOOR
    if gs.map_manager.dungeon_map_for_client : 
      assert gs.map_manager.dungeon_map_for_client[player_y][player_x] != TILE_FOG
    assert response.player_start_pos.x == player_x
    client_monster_ids = {m.id for m in response.monsters}
    assert client_monster_ids == gs.revealed_monster_ids
    manually_revealed_monsters = {
        m_data["id"] for m_data in gs.entity_manager.get_all_monsters() 
        if gs.map_manager.dungeon_map_for_client and \
           0 <= m_data["y"] < len(gs.map_manager.dungeon_map_for_client) and \
           0 <= m_data["x"] < len(gs.map_manager.dungeon_map_for_client[0]) and \
           gs.map_manager.dungeon_map_for_client[m_data["y"]][m_data["x"]] != TILE_FOG
    }
    assert gs.revealed_monster_ids == manually_revealed_monsters


def test_generate_new_dungeon_new_level(game_state_no_init: GameState): 
    gs = game_state_no_init
    original_los_side_effect = gs._has_line_of_sight.side_effect
    original_bfs_side_effect = gs._find_path_bfs.side_effect
    gs._has_line_of_sight.side_effect = lambda s_pos, e_pos: GameState._has_line_of_sight(gs, s_pos, e_pos)
    gs._find_path_bfs.side_effect = lambda s_pos, e_pos, et, em, pp: GameState._find_path_bfs(gs, s_pos, e_pos, et, em, pp)

    initial_seed = 100
    gs.generate_new_dungeon(seed=initial_seed, is_new_level=False) 
    gs.player.xp = 50; gs.player.level = 2; gs.player.hp = gs.player.max_hp // 2 
    original_inventory_count = len(gs.player.inventory)
    original_weapon_id = gs.player.equipment["weapon"]["id"] if gs.player.equipment["weapon"] else None
    
    # Ensure real methods for the next call too
    gs._has_line_of_sight.side_effect = lambda s_pos, e_pos: GameState._has_line_of_sight(gs, s_pos, e_pos)
    gs._find_path_bfs.side_effect = lambda s_pos, e_pos, et, em, pp: GameState._find_path_bfs(gs, s_pos, e_pos, et, em, pp)

    next_level_seed = initial_seed + gs.current_dungeon_level 
    response = gs.generate_new_dungeon(seed=next_level_seed, is_new_level=True)

    gs._has_line_of_sight.side_effect = original_los_side_effect # Restore
    gs._find_path_bfs.side_effect = original_bfs_side_effect

    assert isinstance(response, DungeonDataServerResponse)
    assert gs.current_dungeon_level == 2
    assert gs.player.hp == gs.player.max_hp
    assert len(gs.player.inventory) == original_inventory_count
    if original_weapon_id:
        assert gs.player.equipment["weapon"]["id"] == original_weapon_id
    assert response.current_dungeon_level == 2
    assert response.player_stats.hp == response.player_stats.max_hp
    client_monster_ids = {m.id for m in response.monsters}
    assert client_monster_ids == gs.revealed_monster_ids


def test_handle_player_move_to_empty_floor(game_state_instance: GameState):
    gs = game_state_instance 
    assert gs.player.pos is not None
    _, _, target_x, target_y = find_walkable_adjacent_tile_for_test(gs)
    responses = gs.handle_player_move(target_x, target_y)
    assert gs.player.pos["x"] == target_x
    assert any(isinstance(r, PlayerMovedServerResponse) and r.player_pos.x == target_x for r in responses)
    assert any(isinstance(r, TileChangeServerResponse) for r in responses) 
    assert not any(isinstance(r, InvalidMoveServerResponse) or (hasattr(r, 'type') and r.type == 'error') for r in responses)
    assert not gs.game_over

def test_handle_player_move_into_wall(game_state_instance: GameState):
    gs = game_state_instance
    assert gs.player.pos is not None
    original_player_x, original_player_y, target_x, target_y = find_specific_tile_adjacent(gs, TILE_WALL)
    responses = gs.handle_player_move(target_x, target_y)
    assert gs.player.pos["x"] == original_player_x
    assert gs.player.pos["y"] == original_player_y
    assert any(isinstance(r, InvalidMoveServerResponse) for r in responses)
    player_moved_response = next((r for r in responses if isinstance(r, PlayerMovedServerResponse)), None)
    assert player_moved_response is not None, "PlayerMovedServerResponse must still be sent to sync client"
    assert player_moved_response.player_pos.x == original_player_x
    assert player_moved_response.player_pos.y == original_player_y
    assert not any(isinstance(r, (CombatEventServerResponse, MonsterMovedServerResponse, EntityDiedServerResponse)) for r in responses)

def test_handle_player_move_open_door(game_state_instance: GameState):
    gs = game_state_instance
    assert gs.player.pos is not None
    original_player_x, original_player_y, door_x, door_y = find_specific_tile_adjacent(gs, TILE_DOOR_CLOSED)
    responses = gs.handle_player_move(door_x, door_y)
    assert gs.player.pos["x"] == original_player_x 
    assert gs.player.pos["y"] == original_player_y
    assert gs.map_manager.actual_dungeon_map[door_y][door_x] == TILE_DOOR_OPEN
    tile_change_door_open = any(isinstance(r, TileChangeServerResponse) and r.pos == Position(x=door_x, y=door_y) and r.new_tile_type == TILE_DOOR_OPEN for r in responses)
    assert tile_change_door_open
    assert any(isinstance(r, GameMessageServerResponse) and "open the door" in r.text.lower() for r in responses)
    player_moved_response = next((r for r in responses if isinstance(r, PlayerMovedServerResponse)), None)
    assert player_moved_response is not None and player_moved_response.player_pos == Position(x=original_player_x, y=original_player_y)
    fov_tile_changes = [
        r for r in responses 
        if isinstance(r, TileChangeServerResponse) and \
        not (r.pos == Position(x=door_x, y=door_y) and r.new_tile_type == TILE_DOOR_OPEN)
    ]
    assert len(fov_tile_changes) > 0, "FoV updates expected after opening door"


def test_handle_player_move_pick_up_item(game_state_instance: GameState):
    gs = game_state_instance
    assert gs.player.pos is not None
    try:
        _, _, item_x, item_y = find_specific_tile_adjacent(gs, TILE_ITEM_POTION)
    except AssertionError: 
        player_start_x, player_start_y = gs.player.pos["x"], gs.player.pos["y"]
        placed = False
        for dx_place, dy_place in [(0,1), (1,0), (0,-1), (-1,0)]:
            test_x, test_y = player_start_x + dx_place, player_start_y + dy_place
            if 0 <= test_y < len(gs.map_manager.actual_dungeon_map) and \
               0 <= test_x < len(gs.map_manager.actual_dungeon_map[0]) and \
               gs.map_manager.actual_dungeon_map[test_y][test_x] == TILE_FLOOR:
                gs.map_manager.actual_dungeon_map[test_y][test_x] = TILE_ITEM_POTION
                if gs.map_manager.dungeon_map_for_client: 
                    gs.map_manager.dungeon_map_for_client[test_y][test_x] = TILE_ITEM_POTION
                _, _, item_x, item_y = player_start_x, player_start_y, test_x, test_y
                placed = True; break
        if not placed: raise AssertionError("Test setup failed: Could not place or find item.")
    item_type_key_on_ground = MAP_TILE_TO_ITEM_TYPE.get(TILE_ITEM_POTION)
    initial_item_quantity = next((inv_item["quantity"] for inv_item in gs.player.inventory if inv_item["type_key"] == item_type_key_on_ground), 0)
    responses = gs.handle_player_move(item_x, item_y)
    assert gs.player.pos == {"x": item_x, "y": item_y}
    assert gs.map_manager.actual_dungeon_map[item_y][item_x] == TILE_FLOOR
    picked_item_instance = next((inv_item for inv_item in gs.player.inventory if inv_item["type_key"] == item_type_key_on_ground), None)
    assert picked_item_instance is not None and picked_item_instance["quantity"] == initial_item_quantity + 1
    assert any(isinstance(r, PlayerMovedServerResponse) and r.player_pos == Position(x=item_x, y=item_y) for r in responses)
    assert any(isinstance(r, TileChangeServerResponse) and r.pos == Position(x=item_x, y=item_y) and r.new_tile_type == TILE_FLOOR for r in responses)
    assert any(isinstance(r, GameMessageServerResponse) and "picked up" in r.text.lower() for r in responses)
    assert any(isinstance(r, PlayerStatsUpdateServerResponse) for r in responses), "PlayerStatsUpdate expected after item pickup"

def test_handle_player_move_descend_stairs(game_state_instance: GameState):
    gs = game_state_instance
    assert gs.player.pos is not None
    initial_level = gs.current_dungeon_level
    original_player_effective_stats = gs.player.get_effective_stats() 
    _, _, stairs_x, stairs_y = find_specific_tile_adjacent(gs, TILE_STAIRS_DOWN)
    responses = gs.handle_player_move(stairs_x, stairs_y)
    assert gs.current_dungeon_level == initial_level + 1
    dungeon_data_resp = next(r for r in responses if isinstance(r, DungeonDataServerResponse))
    assert dungeon_data_resp.current_dungeon_level == initial_level + 1
    assert gs.player.level == original_player_effective_stats["level"] 
    assert gs.player.xp == original_player_effective_stats["xp"] 
    current_effective_stats = gs.player.get_effective_stats() 
    assert current_effective_stats["attack"] == original_player_effective_stats["attack"]
    assert current_effective_stats["defense"] == original_player_effective_stats["defense"]
    assert gs.player.hp == gs.player.max_hp 
    assert dungeon_data_resp.player_stats.level == gs.player.level
    assert dungeon_data_resp.player_stats.hp == dungeon_data_resp.player_stats.max_hp
    assert gs.player.pos["x"] != stairs_x or gs.player.pos["y"] != stairs_y
    assert len(gs.entity_manager.get_all_monsters()) > 0

def test_handle_player_move_attack_monster(game_state_instance: GameState):
    gs = game_state_instance
    assert gs.player.pos is not None
    player_x, player_y = gs.player.pos["x"], gs.player.pos["y"]
    monster_x, monster_y = -1,-1
    for dx,dy in [(0,1),(1,0),(0,-1),(-1,0)]:
        cx,cy = player_x+dx, player_y+dy
        if gs.map_manager.is_walkable_for_entity(cx,cy,"player",gs.entity_manager,gs.player.pos) and not gs.entity_manager.get_monster_at(cx,cy):
            monster_x,monster_y=cx,cy; break
    if monster_x == -1 : pytest.skip("Could not find spot for test monster")
    
    monster_id = "m_atk"; monster_data = {**MONSTER_TEMPLATES[TILE_MONSTER_GOBLIN], "id":monster_id, "x":monster_x, "y":monster_y, "hp":100}
    gs.entity_manager.add_monster(monster_data)
    responses = gs.handle_player_move(monster_x, monster_y)
    assert any(isinstance(r, CombatEventServerResponse) for r in responses)


def test_handle_use_item_health_potion(game_state_instance: GameState):
    gs = game_state_instance; gs.player.hp = 5
    potion_id = add_item_to_player(gs.player, ITEM_TYPE_POTION_HEAL)
    responses = gs.handle_use_item(potion_id)
    assert gs.player.hp > 5

def test_handle_use_item_teleport_scroll(game_state_instance: GameState):
    gs = game_state_instance
    scroll_id = add_item_to_player(gs.player, ITEM_TYPE_SCROLL_TELEPORT)
    initial_player_pos = gs.player.pos.copy()
    
    valid_teleport_spot_found = False
    forced_teleport_target_x, forced_teleport_target_y = -1, -1
    if gs.map_manager.actual_dungeon_map:
        for r in range(len(gs.map_manager.actual_dungeon_map)):
            for c in range(len(gs.map_manager.actual_dungeon_map[0])):
                if gs.map_manager.actual_dungeon_map[r][c] == TILE_FLOOR and \
                   not (c == initial_player_pos["x"] and r == initial_player_pos["y"]) and \
                   gs.entity_manager.get_monster_at(c,r) is None:
                    forced_teleport_target_x, forced_teleport_target_y = c,r
                    valid_teleport_spot_found = True; break
            if valid_teleport_spot_found: break
        if not valid_teleport_spot_found and gs.map_manager.actual_dungeon_map: 
            map_w = len(gs.map_manager.actual_dungeon_map[0])
            map_h = len(gs.map_manager.actual_dungeon_map)
            if map_w > 0 and map_h > 0:
                forced_teleport_target_x = (initial_player_pos["x"] + 1) % map_w
                forced_teleport_target_y = initial_player_pos["y"]
                if forced_teleport_target_x == initial_player_pos["x"] and forced_teleport_target_y == initial_player_pos["y"] and map_w > 1:
                     forced_teleport_target_x = (initial_player_pos["x"] + 2) % map_w
                elif forced_teleport_target_x == initial_player_pos["x"] and forced_teleport_target_y == initial_player_pos["y"] and map_h > 1: 
                     forced_teleport_target_y = (initial_player_pos["y"] + 1) % map_h

                if 0 <= forced_teleport_target_y < map_h and 0 <= forced_teleport_target_x < map_w:
                    gs.map_manager.actual_dungeon_map[forced_teleport_target_y][forced_teleport_target_x] = TILE_FLOOR
                    valid_teleport_spot_found = True 
    
    if not valid_teleport_spot_found: 
        forced_teleport_target_x, forced_teleport_target_y = 0,0 
        if initial_player_pos == {"x":0, "y":0} and gs.map_manager.actual_dungeon_map and len(gs.map_manager.actual_dungeon_map[0]) > 1: 
            forced_teleport_target_x = 1 
        if gs.map_manager.actual_dungeon_map:
             gs.map_manager.actual_dungeon_map[forced_teleport_target_y][forced_teleport_target_x] = TILE_FLOOR


    with patch('app.core.items.effects.random.choice', return_value=(forced_teleport_target_x, forced_teleport_target_y)) as mock_random_choice:
        responses = gs.handle_use_item(scroll_id) 
    
    if not any("fizzles" in r.text.lower() for r in responses if isinstance(r, GameMessageServerResponse)):
        assert gs.player.pos != initial_player_pos, "Player should have teleported"
        if valid_teleport_spot_found and forced_teleport_target_x != -1 : 
             mock_random_choice.assert_called()
    
    assert gs.player.find_item_in_inventory(scroll_id) is None, "Scroll should be consumed"


def test_handle_use_item_not_in_inventory(game_state_instance: GameState):
    gs = game_state_instance
    responses = gs.handle_use_item("non_existent_id")
    assert any("item not found" in r.text.lower() for r in responses if isinstance(r, GameMessageServerResponse))

def test_handle_use_item_equippable_item(game_state_instance: GameState):
    gs = game_state_instance
    if gs.player.equipment["weapon"] and gs.player.equipment["weapon"]["type_key"] == ITEM_TYPE_WEAPON_DAGGER:
        gs.player.unequip_item("weapon")
    dagger_id = add_item_to_player(gs.player, ITEM_TYPE_WEAPON_DAGGER)
    responses = gs.handle_use_item(dagger_id)
    assert any("to equip" in r.text.lower() for r in responses if isinstance(r, GameMessageServerResponse)), \
        f"Unexpected/missing message. Responses: {[r.model_dump() for r in responses if isinstance(r, GameMessageServerResponse)]}"


def test_handle_equip_item_weapon_from_inventory(game_state_instance: GameState):
    gs = game_state_instance
    if gs.player.equipment["weapon"]: gs.player.unequip_item("weapon")
    dagger_id = add_item_to_player(gs.player, ITEM_TYPE_WEAPON_DAGGER)
    responses = gs.handle_equip_item(dagger_id)
    assert gs.player.equipment["weapon"] is not None

def test_handle_equip_item_armor_from_inventory(game_state_instance: GameState):
    gs = game_state_instance
    armor_id = add_item_to_player(gs.player, ITEM_TYPE_ARMOR_LEATHER)
    responses = gs.handle_equip_item(armor_id)
    assert gs.player.equipment["armor"] is not None

def test_handle_equip_item_replace_existing_weapon(game_state_instance: GameState):
    gs = game_state_instance 
    original_weapon_id = gs.player.equipment["weapon"]["id"] if gs.player.equipment["weapon"] else None
    new_weapon_id = add_item_to_player(gs.player, ITEM_TYPE_WEAPON_DAGGER) 
    responses = gs.handle_equip_item(new_weapon_id)
    assert gs.player.equipment["weapon"]["id"] == new_weapon_id
    if original_weapon_id:
      assert gs.player.find_item_in_inventory(original_weapon_id) is not None

def test_handle_equip_item_non_equippable(game_state_instance: GameState):
    gs = game_state_instance
    potion_id = add_item_to_player(gs.player, ITEM_TYPE_POTION_HEAL)
    responses = gs.handle_equip_item(potion_id)
    assert any("cannot equip" in r.text.lower() for r in responses if isinstance(r, GameMessageServerResponse))

def test_handle_equip_item_not_in_inventory(game_state_instance: GameState):
    gs = game_state_instance
    responses = gs.handle_equip_item("non_existent_id")
    assert any("not found" in r.text.lower() for r in responses if isinstance(r, GameMessageServerResponse))

def test_handle_unequip_item_weapon(game_state_instance: GameState):
    gs = game_state_instance 
    if not gs.player.equipment["weapon"]: 
        dagger_id = add_item_to_player(gs.player, ITEM_TYPE_WEAPON_DAGGER)
        gs.handle_equip_item(dagger_id)
    assert gs.player.equipment["weapon"] is not None
    item_id = gs.player.equipment["weapon"]["id"]
    responses = gs.handle_unequip_item("weapon")
    assert gs.player.equipment["weapon"] is None
    assert gs.player.find_item_in_inventory(item_id) is not None

def test_handle_unequip_item_armor(game_state_instance: GameState):
    gs = game_state_instance
    armor_id = add_item_to_player(gs.player, ITEM_TYPE_ARMOR_LEATHER)
    gs.handle_equip_item(armor_id)
    assert gs.player.equipment["armor"] is not None
    responses = gs.handle_unequip_item("armor")
    assert gs.player.equipment["armor"] is None
    assert gs.player.find_item_in_inventory(armor_id) is not None

def test_handle_unequip_item_empty_slot(game_state_instance: GameState):
    gs = game_state_instance
    gs.player.equipment["armor"] = None 
    responses = gs.handle_unequip_item("armor")
    assert any("nothing to unequip" in r.text.lower() for r in responses if isinstance(r, GameMessageServerResponse)), \
        f"Unexpected/missing message. Responses: {[r.model_dump() for r in responses if isinstance(r, GameMessageServerResponse)]}"


def test_handle_unequip_item_invalid_slot(game_state_instance: GameState):
    gs = game_state_instance
    responses = gs.handle_unequip_item("invalid_slot_name")
    assert any("invalid slot" in r.text.lower() for r in responses if isinstance(r, GameMessageServerResponse)), \
        f"Unexpected/missing message. Responses: {[r.model_dump() for r in responses if isinstance(r, GameMessageServerResponse)]}"