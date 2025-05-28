# backend/app/core/monsters/ai.py
from typing import Dict, Any, List, Optional, TYPE_CHECKING, cast
import random
import abc

from ..tiles import TILE_FLOOR, TILE_FOG, TILE_DOOR_CLOSED, TILE_DOOR_OPEN 
from ... import schemas 
from ..combat import apply_attack, resolve_monster_attack_on_player
from .. import config as game_config 

if TYPE_CHECKING:
    from ..game_state import GameState

def _handle_monster_move_on_map_and_responses(
    gs: 'GameState', monster: Dict[str, Any], old_x: int, old_y: int, new_x: int, new_y: int
) -> List['schemas.ServerResponse']:
    responses: List['schemas.ServerResponse'] = []
    
    if gs.map_manager.actual_dungeon_map:
        if 0 <= old_y < len(gs.map_manager.actual_dungeon_map) and 0 <= old_x < len(gs.map_manager.actual_dungeon_map[0]):
            pass # Actual map tile at old_x, old_y does not change when monster moves off
    
    monster["x"], monster["y"] = new_x, new_y 
    responses.append(schemas.MonsterMovedServerResponse(monster_id=monster["id"], new_pos=schemas.Position(x=new_x, y=new_y)))

    if gs.map_manager.dungeon_map_for_client and \
       0 <= old_y < len(gs.map_manager.dungeon_map_for_client) and \
       0 <= old_x < len(gs.map_manager.dungeon_map_for_client[0]) and \
       gs.map_manager.dungeon_map_for_client[old_y][old_x] != TILE_FOG: 
        
        underlying_tile_at_old_pos = TILE_FLOOR 
        if gs.map_manager.actual_dungeon_map: 
            underlying_tile_at_old_pos = gs.map_manager.actual_dungeon_map[old_y][old_x]
        
        gs.map_manager.dungeon_map_for_client[old_y][old_x] = underlying_tile_at_old_pos
        responses.append(schemas.TileChangeServerResponse(
            pos=schemas.Position(x=old_x, y=old_y), 
            new_tile_type=underlying_tile_at_old_pos 
        ))
    return responses

class MonsterAIBase(abc.ABC):
    @abc.abstractmethod
    def execute_turn(self, monster: Dict[str, Any], gs: 'GameState') -> List['schemas.ServerResponse']:
        pass

class ChaserAI(MonsterAIBase):
    def execute_turn(self, monster: Dict[str, Any], gs: 'GameState') -> List['schemas.ServerResponse']:
        responses: List['schemas.ServerResponse'] = []
        if not gs.player.pos or not gs.map_manager.actual_dungeon_map: return responses
        monster_pos = {"x": monster["x"], "y": monster["y"]}; player_current_pos = gs.player.pos 
        distance_to_player = abs(monster_pos["x"]-player_current_pos["x"]) + abs(monster_pos["y"]-player_current_pos["y"])
        next_x, next_y = monster_pos["x"], monster_pos["y"]; did_attack_this_turn = False
        has_los_to_player = gs._has_line_of_sight(monster_pos, player_current_pos)

        # State determination
        if has_los_to_player:
            monster["last_known_player_pos"] = player_current_pos.copy()
            monster["turns_since_player_seen"] = 0
            monster["ai_state"] = "chasing"
        elif monster.get("last_known_player_pos"): # LKP exists, LoS is false
            # Explicitly fetch, increment, then store.
            current_turns_since_seen = monster.get("turns_since_player_seen", 0)
            updated_turns_since_seen = current_turns_since_seen + 1
            monster["turns_since_player_seen"] = updated_turns_since_seen
            
            if updated_turns_since_seen >= game_config.MONSTER_LKP_TIMEOUT_TURNS:
                monster["last_known_player_pos"] = None
                monster["ai_state"] = "idle"
            else:
                monster["ai_state"] = "searching_lkp"
        else: # No LoS, no LKP
            monster["ai_state"] = "idle"

        target_pos_for_pathing=None
        if monster["ai_state"]=="chasing": target_pos_for_pathing=player_current_pos
        elif monster["ai_state"]=="searching_lkp" and monster.get("last_known_player_pos"): 
            target_pos_for_pathing=monster["last_known_player_pos"]
        
        player_effective_stats = gs.player.get_effective_stats()

        if monster["ai_state"] == "searching_lkp" and \
           target_pos_for_pathing is not None and \
           monster_pos["x"] == target_pos_for_pathing["x"] and \
           monster_pos["y"] == target_pos_for_pathing["y"]:
            monster["last_known_player_pos"] = None 
            monster["ai_state"] = "idle"
            target_pos_for_pathing = None 

        if target_pos_for_pathing and (monster["ai_state"]=="chasing" or monster["ai_state"]=="searching_lkp"):
            path = gs._find_path_bfs(monster_pos, target_pos_for_pathing, "monster")
            if path and len(path) > 1:
                potential_next_step = path[1]
                if monster["ai_state"]=="chasing" and \
                   potential_next_step["x"]==player_current_pos["x"] and \
                   potential_next_step["y"]==player_current_pos["y"] and \
                   has_los_to_player: 
                    damage_to_player,_,_,msg_segment = apply_attack(monster["type_name"], monster.get("attack",1), "you", gs.player.hp, player_effective_stats["defense"])
                    responses.extend(resolve_monster_attack_on_player(gs,monster,damage_to_player,msg_segment))
                    did_attack_this_turn=True
                else: 
                    next_x,next_y = potential_next_step["x"],potential_next_step["y"]
                
                if not did_attack_this_turn and \
                   monster["ai_state"]=="searching_lkp" and monster.get("last_known_player_pos") and \
                   next_x==monster["last_known_player_pos"]["x"] and next_y==monster["last_known_player_pos"]["y"]:
                    monster["last_known_player_pos"]=None; monster["ai_state"]="idle"
            
            elif monster["ai_state"]!="idle": 
                if random.random() < game_config.AI_RANDOM_MOVE_CHANCE_NO_PATH: 
                    possible_moves=[(monster["x"]+dx,monster["y"]+dy) for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)] if gs._is_walkable_for_entity(monster["x"]+dx,monster["y"]+dy,"monster")]
                    if possible_moves: next_x,next_y=random.choice(possible_moves)
        
        if monster["ai_state"]=="idle" and not did_attack_this_turn:
            if random.random() < monster.get("move_chance", game_config.AI_DEFAULT_IDLE_MOVE_CHANCE):
                possible_moves=[(monster["x"]+dx,monster["y"]+dy) for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)] if gs._is_walkable_for_entity(monster["x"]+dx,monster["y"]+dy,"monster")]
                if possible_moves: next_x,next_y=random.choice(possible_moves)

        if not did_attack_this_turn and (next_x!=monster["x"] or next_y!=monster["y"]):
            if gs._is_walkable_for_entity(next_x,next_y,"monster"):
                responses.extend(_handle_monster_move_on_map_and_responses(gs,monster,monster["x"],monster["y"],next_x,next_y))
        return responses

class RangedAI(MonsterAIBase): 
    def execute_turn(self, monster: Dict[str, Any], gs: 'GameState') -> List['schemas.ServerResponse']:
        responses: List['schemas.ServerResponse'] = []
        if not gs.player.pos or not gs.map_manager.actual_dungeon_map: return responses
        
        monster_pos={"x":monster["x"],"y":monster["y"]}
        player_current_pos=gs.player.pos
        distance_to_player=abs(monster_pos["x"]-player_current_pos["x"])+abs(monster_pos["y"]-player_current_pos["y"])
        
        next_x,next_y=monster_pos["x"],monster_pos["y"] 
        did_attack_this_turn=False
        
        attack_range=monster.get("attack_range",5)
        has_los_to_player=gs._has_line_of_sight(monster_pos,player_current_pos)
        player_effective_stats=gs.player.get_effective_stats()

        # State determination
        if has_los_to_player: 
            monster["last_known_player_pos"]=player_current_pos.copy()
            monster["turns_since_player_seen"]=0
            monster["ai_state"]="engaging"
        elif monster.get("last_known_player_pos"):
            current_turns_since_seen = monster.get("turns_since_player_seen", 0)
            updated_turns_since_seen = current_turns_since_seen + 1
            monster["turns_since_player_seen"] = updated_turns_since_seen
            
            if updated_turns_since_seen >= game_config.MONSTER_LKP_TIMEOUT_TURNS:
                monster["last_known_player_pos"]=None
                monster["ai_state"]="idle"
            else: 
                monster["ai_state"]="searching_lkp"
        else: 
            monster["ai_state"]="idle"
        
        target_pos_for_pathing=None 
        action_taken_instead_of_pathing = False 

        if monster["ai_state"]=="engaging":
            if has_los_to_player and distance_to_player == 1: 
                best_kite_move=None
                max_kite_dist = distance_to_player 
                for dx_k,dy_k in [(0,1),(0,-1),(1,0),(-1,0)]:
                    kx,ky=monster_pos["x"]+dx_k,monster_pos["y"]+dy_k
                    if gs._is_walkable_for_entity(kx,ky,"monster"):
                        k_dist_to_player=abs(kx-player_current_pos["x"])+abs(ky-player_current_pos["y"])
                        if k_dist_to_player > max_kite_dist: 
                            max_kite_dist = k_dist_to_player
                            best_kite_move=(kx,ky)
                        elif best_kite_move is None and k_dist_to_player > 0: 
                            best_kite_move=(kx,ky)
                if best_kite_move:
                    next_x,next_y = best_kite_move
                    action_taken_instead_of_pathing = True 
            elif has_los_to_player and distance_to_player <= attack_range and distance_to_player > 0:
                damage_to_player,_,_,msg_segment=apply_attack(monster["type_name"],monster.get("attack",1),"you",gs.player.hp,player_effective_stats["defense"])
                responses.extend(resolve_monster_attack_on_player(gs,monster,damage_to_player,msg_segment))
                did_attack_this_turn=True
                action_taken_instead_of_pathing = True 
            else: 
                target_pos_for_pathing = player_current_pos
        
        elif monster["ai_state"]=="searching_lkp" and monster.get("last_known_player_pos"):
            target_pos_for_pathing = monster["last_known_player_pos"]
            if monster_pos["x"] == target_pos_for_pathing["x"] and \
               monster_pos["y"] == target_pos_for_pathing["y"]:
                monster["last_known_player_pos"] = None 
                monster["ai_state"] = "idle"
                target_pos_for_pathing = None 
                action_taken_instead_of_pathing = True 
        
        if not action_taken_instead_of_pathing and target_pos_for_pathing:
            path = gs._find_path_bfs(monster_pos, target_pos_for_pathing, "monster")
            if path and len(path) > 1:
                potential_next_step = path[1]
                is_target_player_and_engaging = (
                    monster["ai_state"] == "engaging" and
                    potential_next_step["x"] == player_current_pos["x"] and
                    potential_next_step["y"] == player_current_pos["y"]
                )
                if not is_target_player_and_engaging:
                    if gs._is_walkable_for_entity(potential_next_step["x"], potential_next_step["y"], "monster"):
                        next_x, next_y = potential_next_step["x"], potential_next_step["y"]

                if monster["ai_state"] == "searching_lkp" and monster.get("last_known_player_pos") and \
                   next_x == monster["last_known_player_pos"]["x"] and next_y == monster["last_known_player_pos"]["y"]:
                    monster["last_known_player_pos"] = None 
                    monster["ai_state"] = "idle"
            elif monster["ai_state"] != "idle": 
                if random.random() < game_config.AI_RANDOM_MOVE_CHANCE_NO_PATH: 
                    possible_moves=[(monster["x"]+dx,monster["y"]+dy) for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)] if gs._is_walkable_for_entity(monster["x"]+dx,monster["y"]+dy,"monster")]
                    if possible_moves:
                        next_x,next_y=random.choice(possible_moves)

        if monster["ai_state"]=="idle" and not did_attack_this_turn and not action_taken_instead_of_pathing and (next_x == monster_pos["x"] and next_y == monster_pos["y"]):
            if random.random() < monster.get("move_chance", game_config.AI_DEFAULT_IDLE_MOVE_CHANCE):
                possible_moves=[(monster["x"]+dx,monster["y"]+dy) for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)] if gs._is_walkable_for_entity(monster["x"]+dx,monster["y"]+dy,"monster")]
                if possible_moves:
                    next_x,next_y=random.choice(possible_moves)
        
        if not did_attack_this_turn and (next_x != monster_pos["x"] or next_y != monster_pos["y"]):
            if gs._is_walkable_for_entity(next_x, next_y, "monster"): 
                responses.extend(_handle_monster_move_on_map_and_responses(gs, monster, monster_pos["x"], monster_pos["y"], next_x, next_y))
        
        return responses

MONSTER_AI_STRATEGIES: Dict[str, MonsterAIBase] = {
    "chaser": ChaserAI(),
    "ranged_attacker": RangedAI()
}