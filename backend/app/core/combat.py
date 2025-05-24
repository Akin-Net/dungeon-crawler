# backend/app/core/combat.py
from typing import Dict, Any, Tuple, List, TYPE_CHECKING
from .. import schemas # For ServerResponse types
from .tiles import TILE_FLOOR # For map updates

if TYPE_CHECKING:
    from .game_state import GameState # For type hinting gs parameter

def calculate_damage(attacker_attack: int, defender_defense: int) -> int:
    """Calculates damage dealt in an attack."""
    damage = attacker_attack - defender_defense
    return max(0, damage)

def apply_attack(
    attacker_name: str,
    attacker_effective_attack: int,
    defender_name: str,
    defender_current_hp: int,
    defender_effective_defense: int,
    # is_defender_player: bool # No longer strictly needed here if messages are more generic
) -> Tuple[int, int, bool, str]: 
    # Returns: (damage_done, defender_hp_after_attack, defender_died, message_segment)
    
    damage_done = calculate_damage(attacker_effective_attack, defender_effective_defense)
    defender_hp_after_attack = defender_current_hp - damage_done
    defender_died = defender_hp_after_attack <= 0
    
    if defender_died:
        defender_hp_after_attack = 0

    message_segment = f"{attacker_name.capitalize()} hits {defender_name} for {damage_done} damage."
    if damage_done == 0:
        message_segment = f"{attacker_name.capitalize()} attacks {defender_name} but deals no damage."
        
    return damage_done, defender_hp_after_attack, defender_died, message_segment

def resolve_player_attack_on_monster(
    gs: 'GameState', 
    target_monster: Dict[str, Any], 
    damage_dealt: int, 
    monster_hp_after_attack: int,
    monster_died: bool, 
    base_combat_message: str
) -> List[schemas.ServerResponse]:
    responses: List[schemas.ServerResponse] = []
    
    target_monster["hp"] = monster_hp_after_attack 

    responses.append(schemas.CombatEventServerResponse(
        attacker_faction="player", defender_id=target_monster["id"], defender_type=target_monster["type_name"],
        damage_done=damage_dealt, defender_hp_current=target_monster["hp"], 
        defender_hp_max=target_monster["max_hp"], message=base_combat_message
    ))

    if monster_died:
        xp_gain = target_monster.get("xp_value", 0)
        death_message = f"{target_monster['type_name'].capitalize()} dies!"
        if xp_gain > 0:
            death_message += f" You gain {xp_gain} XP."
        
        responses.append(schemas.EntityDiedServerResponse(
            entity_id=target_monster["id"], entity_type=target_monster["type_name"], 
            pos=schemas.Position(x=target_monster["x"],y=target_monster["y"]), 
            message=death_message
        ))
        
        if gs.map_manager.actual_dungeon_map:
            gs.map_manager.actual_dungeon_map[target_monster["y"]][target_monster["x"]] = TILE_FLOOR
        if gs.map_manager.dungeon_map_for_client: 
            gs.map_manager.dungeon_map_for_client[target_monster["y"]][target_monster["x"]] = TILE_FLOOR
        
        gs.entity_manager.remove_monster(target_monster)
        
        responses.append(schemas.TileChangeServerResponse(
            pos=schemas.Position(x=target_monster["x"],y=target_monster["y"]), 
            new_tile_type=TILE_FLOOR
        ))
        
        if xp_gain > 0: 
            xp_responses, leveled_up = gs.player.grant_xp(xp_gain)
            responses.extend(xp_responses)
            # Ensure PlayerStatsUpdate is sent if XP changed but no level up (grant_xp handles level up case)
            if not leveled_up and not any(isinstance(r, schemas.PlayerStatsUpdateServerResponse) for r in xp_responses):
                 responses.append(schemas.PlayerStatsUpdateServerResponse(stats=gs.player.create_player_stats_response()))
    return responses

def resolve_monster_attack_on_player(
    gs: 'GameState', 
    attacking_monster_stats: Dict[str, Any], 
    damage_dealt: int,
    base_combat_message: str # This should be the direct output from apply_attack
) -> List[schemas.ServerResponse]:
    responses: List[schemas.ServerResponse] = []
    player_effective_stats_before_hit = gs.player.get_effective_stats()

    player_died_from_attack = gs.player.take_damage(damage_dealt)
    
    # Construct the full message for CombatEventServerResponse
    # base_combat_message might be "Monster hits you for X damage."
    # If retaliation, GameState's handle_player_move can prepend "Monster retaliates! "
    
    responses.append(schemas.CombatEventServerResponse(
        attacker_id=attacking_monster_stats["id"], attacker_type=attacking_monster_stats["type_name"], 
        defender_faction="player", damage_done=damage_dealt, 
        defender_hp_current=gs.player.hp, defender_hp_max=player_effective_stats_before_hit["max_hp"], 
        message=base_combat_message # Use the message from apply_attack
    ))

    if player_died_from_attack:
        gs.game_over = True
        responses.append(schemas.PlayerDiedServerResponse(message=f"You have been slain by {attacking_monster_stats['type_name']}!"))
    
    responses.append(schemas.PlayerStatsUpdateServerResponse(stats=gs.player.create_player_stats_response()))
    return responses