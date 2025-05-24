# backend/app/core/items/effects.py
from typing import Dict, Any, List, TYPE_CHECKING, Tuple
import random

if TYPE_CHECKING:
    from ..game_state import GameState # GameState still passed for broader context
    from ...schemas import ServerResponse # Schemas used directly
    from ..player import Player # For type hinting player modifications

from ..tiles import TILE_FLOOR, TILE_FOG # TILE_DOOR_OPEN also walkable for player
from ... import schemas # For response types like GameMessageServerResponse


def apply_heal_effect(
    gs: 'GameState', # GameState provides access to gs.player
    item_data: Dict[str, Any] 
) -> List['ServerResponse']:
    responses: List['ServerResponse'] = []
    player_instance = gs.player # Get player instance from GameState

    heal_amount = item_data.get("effect_value", 10)
    
    old_hp = player_instance.hp
    # Healing applies to player's base HP, effective HP will be recalculated by its own methods
    player_instance.hp = min(player_instance.max_hp, player_instance.hp + heal_amount)
    healed_for = player_instance.hp - old_hp

    if healed_for > 0:
        responses.append(schemas.GameMessageServerResponse(text=f"You use the {item_data.get('type_name', 'item')} and heal for {healed_for} HP."))
    else:
        responses.append(schemas.GameMessageServerResponse(text=f"You use the {item_data.get('type_name', 'item')}, but your health is already full."))
        
    return responses

def apply_teleport_random_effect(
    gs: 'GameState', # GameState provides access to gs.player, gs.map_manager, gs.entity_manager
    item_data: Dict[str, Any] 
) -> List['ServerResponse']:
    responses: List['ServerResponse'] = []
    player_instance = gs.player

    if not gs.map_manager.actual_dungeon_map or not player_instance.pos:
        responses.append(schemas.GameMessageServerResponse(text="Cannot teleport: map or player position invalid."))
        return responses

    possible_locations: List[Tuple[int, int]] = []
    map_h = len(gs.map_manager.actual_dungeon_map)
    map_w = len(gs.map_manager.actual_dungeon_map[0])

    for y in range(map_h):
        for x in range(map_w):
            # gs._is_walkable_for_entity uses map_manager and needs entity_manager, player_pos
            if gs._is_walkable_for_entity(x, y, "player_teleport"): 
                if player_instance.pos["x"] == x and player_instance.pos["y"] == y:
                    continue
                if gs.entity_manager.get_monster_at(x,y): # Use entity_manager
                    continue
                possible_locations.append((x,y))
    
    if not possible_locations:
        responses.append(schemas.GameMessageServerResponse(text="The scroll fizzles. No safe place to teleport!"))
        return responses

    new_x, new_y = random.choice(possible_locations)
    player_instance.pos = {"x": new_x, "y": new_y} # Update player's position directly

    responses.append(schemas.GameMessageServerResponse(text=f"You read the {item_data.get('type_name', 'scroll')} and vanish, reappearing elsewhere!"))
    responses.append(schemas.PlayerMovedServerResponse(player_pos=schemas.Position(**player_instance.pos)))

    room_info = gs.map_manager.get_room_at_pos(player_instance.pos["x"], player_instance.pos["y"])
    if room_info and room_info[0] not in gs.map_manager.visited_room_indices:
        responses.extend(gs.map_manager.reveal_room_and_connected_corridors(room_info[0], gs))
    
    if gs.map_manager.dungeon_map_for_client: 
        fov_updates = gs.map_manager.update_fov(player_instance.pos)
        responses.extend(fov_updates)

    return responses


# --- Registry of Effect Handlers ---
ITEM_EFFECT_HANDLERS: Dict[str, callable] = {
    "heal": apply_heal_effect,
    "teleport_random": apply_teleport_random_effect,
}