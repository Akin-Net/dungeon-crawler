# backend/app/core/game_state.py
from typing import Any, Dict, List, Optional, Union, cast, Tuple, Set
import uuid
import random
import logging
import math
from collections import deque

from .tiles import (
    TILE_FLOOR, TILE_WALL, TILE_ITEM_POTION, TILE_EMPTY,
    TILE_MONSTER_GOBLIN, TILE_MONSTER_ORC, TILE_MONSTER_SKELETON, 
    TILE_DOOR_CLOSED, TILE_DOOR_OPEN, TILE_STAIRS_DOWN, TILE_FOG,
    TILE_ITEM_SCROLL_TELEPORT
)
from .monsters.definitions import MONSTER_TEMPLATES
from .monsters.ai import MONSTER_AI_STRATEGIES
from .items.definitions import ITEM_TEMPLATES, MAP_TILE_TO_ITEM_TYPE
from .items.effects import ITEM_EFFECT_HANDLERS
from .combat import apply_attack, resolve_player_attack_on_monster, resolve_monster_attack_on_player
from . import config as game_config # CORRECTED IMPORT

from .. import schemas
from .dungeon_generator import DungeonGenerator, Room 
from .map_manager import MapManager
from .entity_manager import EntityManager
from .player import Player


logger = logging.getLogger(__name__)

class GameState:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.logger = logging.getLogger(f"GameState.{self.client_id}")
        self.map_manager = MapManager(logger_parent_name=self.logger.name)
        self.entity_manager = EntityManager(logger_parent_name=self.logger.name)
        self.player = Player(initial_pos={"x":0, "y":0}, logger_ref=self.logger)
        self.base_tile_types = {
            "EMPTY": TILE_EMPTY, "FLOOR": TILE_FLOOR, "WALL": TILE_WALL,
            "ITEM_POTION": TILE_ITEM_POTION, "MONSTER_GOBLIN": TILE_MONSTER_GOBLIN,
            "MONSTER_ORC": TILE_MONSTER_ORC, "MONSTER_SKELETON": TILE_MONSTER_SKELETON,
            "DOOR_CLOSED": TILE_DOOR_CLOSED, "DOOR_OPEN": TILE_DOOR_OPEN,
            "STAIRS_DOWN": TILE_STAIRS_DOWN, "FOG": TILE_FOG,
            "ITEM_SCROLL_TELEPORT": TILE_ITEM_SCROLL_TELEPORT,
        }
        self.game_over: bool = False
        self.current_dungeon_level: int = 1
        self.seed: Optional[int] = None
        self.revealed_monster_ids: Set[str] = set() 
        self.logger.info(f"GameState Initialized.") 

    def _get_effective_player_stats(self) -> Dict[str, Any]:
        return self.player.get_effective_stats()

    def _get_monster_at(self, x: int, y: int) -> Optional[Dict[str, Any]]:
        return self.entity_manager.get_monster_at(x,y)

    def _has_line_of_sight(self, start_pos: Dict[str, int], end_pos: Dict[str, int]) -> bool:
        return self.map_manager.has_line_of_sight(start_pos, end_pos)

    def _find_path_bfs(self, start_pos: Dict[str,int], end_pos: Dict[str,int], entity_type: str = "monster") -> Optional[List[Dict[str,int]]]:
        return self.map_manager.find_path_bfs(start_pos, end_pos, entity_type, self.entity_manager, self.player.pos)

    def _is_walkable_for_entity(self, x: int, y: int, entity_type: str) -> bool:
        return self.map_manager.is_walkable_for_entity(x, y, entity_type, self.entity_manager, self.player.pos)

    def _check_and_reveal_newly_visible_monsters(self) -> List[schemas.MonsterAppearedServerResponse]:
        newly_visible_monster_responses: List[schemas.MonsterAppearedServerResponse] = []
        if not self.map_manager.dungeon_map_for_client: return newly_visible_monster_responses
        for monster_data in self.entity_manager.get_all_monsters():
            monster_id = monster_data["id"]; mx, my = monster_data["x"], monster_data["y"]
            is_on_client_map_and_not_fog = (
                0 <= my < len(self.map_manager.dungeon_map_for_client) and
                0 <= mx < len(self.map_manager.dungeon_map_for_client[0]) and
                self.map_manager.dungeon_map_for_client[my][mx] != TILE_FOG )
            if is_on_client_map_and_not_fog and monster_id not in self.revealed_monster_ids:
                self.revealed_monster_ids.add(monster_id)
                monster_info = schemas.MonsterInfoResponse(id=monster_id, x=mx, y=my, type=monster_data["type_name"], tile_id=monster_data["tile_id"])
                newly_visible_monster_responses.append(schemas.MonsterAppearedServerResponse(monster_info=monster_info))
        return newly_visible_monster_responses

    def generate_new_dungeon(self, seed: Optional[int], 
                             width: int = game_config.DEFAULT_MAP_WIDTH, 
                             height: int = game_config.DEFAULT_MAP_HEIGHT, 
                             max_rooms: int = game_config.DEFAULT_MAX_ROOMS, 
                             room_min: int = game_config.DEFAULT_ROOM_MIN_SIZE, 
                             room_max: int = game_config.DEFAULT_ROOM_MAX_SIZE, 
                             is_new_level: bool = False):
        self.seed = seed
        
        current_inventory = list(self.player.inventory) if is_new_level else []
        current_equipment = dict(self.player.equipment) if is_new_level else {"weapon": None, "armor": None}
        self.revealed_monster_ids.clear() 

        if is_new_level:
            self.current_dungeon_level +=1
            self.logger.info(f"Generating dungeon for level {self.current_dungeon_level} (seed: {self.seed})")
            self.player.inventory = current_inventory 
            self.player.equipment = current_equipment 
            self.player.full_heal() 
        else: 
            self.current_dungeon_level = 1
            self.logger.info(f"Generating new game (level {self.current_dungeon_level}, seed: {self.seed})")
            self.game_over = False

        self.entity_manager.initialize_entities()
        try:
            generator = DungeonGenerator(width, height, seed=self.seed)
            actual_map_data_from_gen, start_pos_tuple = generator.generate_dungeon(max_rooms, room_min, room_max)
            
            if actual_map_data_from_gen is None or start_pos_tuple is None:
                self.logger.error("Dungeon generator returned None for map or start position.")
                return schemas.ErrorServerResponse(message="Dungeon generation failed critically.")

            self.map_manager.initialize_maps(actual_map_data_from_gen, width, height)
            self.map_manager.set_generated_rooms(generator.rooms) 
            
            player_start_pos_dict = {"x": start_pos_tuple[0], "y": start_pos_tuple[1]}

            if not is_new_level: 
                self.player.reset_for_new_game(player_start_pos_dict) 
            else: 
                self.player.pos = player_start_pos_dict 
            
            if self.map_manager.actual_dungeon_map and \
               self.map_manager.actual_dungeon_map[self.player.pos["y"]][self.player.pos["x"]] != TILE_FLOOR:
                self.map_manager.actual_dungeon_map[self.player.pos["y"]][self.player.pos["x"]] = TILE_FLOOR
            
            if self.map_manager.actual_dungeon_map:
                for r_idx, row in enumerate(list(self.map_manager.actual_dungeon_map)):
                    for c_idx, tile_val in enumerate(list(row)):
                        if tile_val in MONSTER_TEMPLATES: 
                            if c_idx == self.player.pos["x"] and r_idx == self.player.pos["y"]:
                                if self.map_manager.actual_dungeon_map[r_idx][c_idx] != TILE_FLOOR:
                                     self.map_manager.actual_dungeon_map[r_idx][c_idx] = TILE_FLOOR 
                                continue
                            template = MONSTER_TEMPLATES[tile_val]
                            monster_id = str(uuid.uuid4())
                            monster_instance_data = {**template, "id": monster_id, "x": c_idx, "y": r_idx, 
                                                     "hp": template["max_hp"], "last_known_player_pos": None}
                            self.entity_manager.add_monster(monster_instance_data)
                            self.map_manager.actual_dungeon_map[r_idx][c_idx] = TILE_FLOOR
            
            if self.map_manager.actual_dungeon_map and self.map_manager.generated_rooms and self.player.pos:
                last_room_idx = -1
                player_s_room_info = self.map_manager.get_room_at_pos(self.player.pos["x"], self.player.pos["y"])
                player_s_room_idx = player_s_room_info[0] if player_s_room_info else None
                if len(self.map_manager.generated_rooms) > 1 and player_s_room_idx is not None:
                    poss_indices = [i for i, _ in enumerate(self.map_manager.generated_rooms) if i != player_s_room_idx]
                    if poss_indices: last_room_idx = random.choice(poss_indices)
                elif self.map_manager.generated_rooms: last_room_idx = len(self.map_manager.generated_rooms) - 1
                if last_room_idx != -1 and last_room_idx < len(self.map_manager.generated_rooms):
                    last_room = self.map_manager.generated_rooms[last_room_idx]
                    potential_stairs = []
                    for r_y_s in range(last_room.y1, last_room.y2 + 1):
                        for r_x_s in range(last_room.x1, last_room.x2 + 1):
                            if self.map_manager.actual_dungeon_map[r_y_s][r_x_s] == TILE_FLOOR and \
                            not (r_x_s == self.player.pos["x"] and r_y_s == self.player.pos["y"]):
                                potential_stairs.append((r_x_s, r_y_s))
                    if potential_stairs:
                        sx, sy = random.choice(potential_stairs)
                        self.map_manager.actual_dungeon_map[sy][sx] = TILE_STAIRS_DOWN
                    elif self.map_manager.actual_dungeon_map[last_room.center()[1]][last_room.center()[0]] == TILE_FLOOR and \
                         not (last_room.center()[0] == self.player.pos["x"] and last_room.center()[1] == self.player.pos["y"]):
                        self.map_manager.actual_dungeon_map[last_room.center()[1]][last_room.center()[0]] = TILE_STAIRS_DOWN
            
            initial_monsters_for_client = []
            if self.player.pos:
                initial_room_info = self.map_manager.get_room_at_pos(self.player.pos["x"], self.player.pos["y"])
                if initial_room_info: self.map_manager.reveal_room_and_connected_corridors(initial_room_info[0], self)
                self.map_manager.update_fov(self.player.pos) 
                for m_data in self.entity_manager.get_all_monsters():
                    mx,my=m_data["x"],m_data["y"]
                    if self.map_manager.dungeon_map_for_client and 0<=my<len(self.map_manager.dungeon_map_for_client) and \
                       0<=mx<len(self.map_manager.dungeon_map_for_client[0]) and self.map_manager.dungeon_map_for_client[my][mx]!=TILE_FOG:
                        self.revealed_monster_ids.add(m_data["id"])
                        initial_monsters_for_client.append(schemas.MonsterInfoResponse(id=m_data["id"],x=mx,y=my,type=m_data["type_name"],tile_id=m_data["tile_id"]))
            else: self.logger.error("Player position None before initial FoV setup!")

        except Exception as e:
            self.logger.error(f"Dungeon gen outer exception: {e}", exc_info=True)
            if self.map_manager: self.map_manager.initialize_maps([[]],0,0) 
            return schemas.ErrorServerResponse(message=f"Dungeon generation failed: {str(e)[:100]}")

        if not self.map_manager.dungeon_map_for_client or not self.player.pos:
             return schemas.ErrorServerResponse(message="Internal error preparing map for client.")
        
        return schemas.DungeonDataServerResponse(
            map=self.map_manager.dungeon_map_for_client, player_start_pos=schemas.Position(**self.player.pos),
            tile_types=schemas.TileTypesResponse(**self.base_tile_types), player_stats=self.player.create_player_stats_response(),
            monsters=initial_monsters_for_client, seed_used=self.seed, current_dungeon_level=self.current_dungeon_level)

    def process_monster_turns(self) -> List[schemas.ServerResponse]:
        all_responses: List[schemas.ServerResponse] = []
        if self.game_over or not self.player.pos or \
           not self.map_manager.actual_dungeon_map or \
           not self.map_manager.dungeon_map_for_client:
            return all_responses
            
        for monster_data in list(self.entity_manager.get_all_monsters()): 
            monster = cast(Dict[str, Any], monster_data)
            if monster.get("_has_acted_this_player_turn"):
                del monster["_has_acted_this_player_turn"]; continue
            if monster["hp"] <= 0: continue 
            if self.game_over: break 

            monster_is_visible_on_client_map_now = False
            if self.map_manager.dungeon_map_for_client and \
               0 <= monster["y"] < len(self.map_manager.dungeon_map_for_client) and \
               0 <= monster["x"] < len(self.map_manager.dungeon_map_for_client[0]) and \
               self.map_manager.dungeon_map_for_client[monster["y"]][monster["x"]] != TILE_FOG:
                monster_is_visible_on_client_map_now = True

            if monster_is_visible_on_client_map_now or monster.get("ai_state") != "idle":
                ai_key = monster.get("ai_type", "chaser")
                strategy = MONSTER_AI_STRATEGIES.get(ai_key)
                if strategy: 
                    turn_responses = strategy.execute_turn(monster, self) 
                    all_responses.extend(turn_responses)
            if self.game_over: break 
        return all_responses

    def _handle_player_attack_interaction(self, monster_at_target: Dict[str, Any]) -> List[schemas.ServerResponse]:
        player_effective_stats = self.player.get_effective_stats()
        monster_stats_mut = cast(Dict[str, Any], monster_at_target)
        damage_to_monster, hp_after_attack, died, p_attack_msg = apply_attack(
            attacker_name="You", attacker_effective_attack=player_effective_stats["attack"],
            defender_name=monster_stats_mut["type_name"], defender_current_hp=monster_stats_mut["hp"],
            defender_effective_defense=monster_stats_mut.get("defense", 0))
        responses = resolve_player_attack_on_monster(self, monster_stats_mut, damage_to_monster, hp_after_attack, died, p_attack_msg)
        if not died and not self.game_over:
            retaliation_damage, _, _, m_attack_msg_segment = apply_attack(
                attacker_name=monster_stats_mut["type_name"], attacker_effective_attack=monster_stats_mut.get("attack", 1),
                defender_name="you", defender_current_hp=self.player.hp,
                defender_effective_defense=player_effective_stats["defense"])
            full_retaliation_message = f"{monster_stats_mut['type_name'].capitalize()} retaliates! {m_attack_msg_segment.split(' hits ', 1)[1]}" if ' hits ' in m_attack_msg_segment else f"{monster_stats_mut['type_name'].capitalize()} retaliates and {m_attack_msg_segment.split(' attacks ', 1)[1] if ' attacks ' in m_attack_msg_segment else m_attack_msg_segment}"
            if "deals no damage" in m_attack_msg_segment : full_retaliation_message = f"{monster_stats_mut['type_name'].capitalize()} retaliates! {m_attack_msg_segment}"
            responses.extend(resolve_monster_attack_on_player(self, monster_stats_mut, retaliation_damage, full_retaliation_message))
            monster_stats_mut["_has_acted_this_player_turn"] = True
        if self.player.pos: 
            responses.append(schemas.PlayerMovedServerResponse(player_pos=schemas.Position(**self.player.pos)))
        return responses

    def _handle_open_door_interaction(self, new_x: int, new_y: int, prev_player_pos: Dict[str, Any]) -> List[schemas.ServerResponse]:
        responses: List[schemas.ServerResponse] = []
        if self.map_manager.actual_dungeon_map: self.map_manager.actual_dungeon_map[new_y][new_x] = TILE_DOOR_OPEN
        if self.map_manager.dungeon_map_for_client: self.map_manager.dungeon_map_for_client[new_y][new_x] = TILE_DOOR_OPEN
        responses.append(schemas.TileChangeServerResponse(pos=schemas.Position(x=new_x,y=new_y),new_tile_type=TILE_DOOR_OPEN))
        responses.append(schemas.GameMessageServerResponse(text="You open the door."))
        room_check_x,room_check_y = new_x,new_y 
        if new_x==prev_player_pos["x"]: room_check_y=new_y+(new_y-prev_player_pos["y"]) 
        elif new_y==prev_player_pos["y"]: room_check_x=new_x+(new_x-prev_player_pos["x"])
        room_info=self.map_manager.get_room_at_pos(room_check_x,room_check_y)
        if room_info and room_info[0] not in self.map_manager.visited_room_indices:
            responses.extend(self.map_manager.reveal_room_and_connected_corridors(room_info[0], self))
        if self.player.pos: 
            responses.extend(self.map_manager.update_fov(prev_player_pos)) 
            responses.append(schemas.PlayerMovedServerResponse(player_pos=schemas.Position(**prev_player_pos))) 
        return responses

    def _handle_descend_stairs_interaction(self, new_x: int, new_y: int) -> Tuple[List[schemas.ServerResponse], bool]:
        responses: List[schemas.ServerResponse] = []
        self.player.pos={"x":new_x,"y":new_y} 
        responses.append(schemas.PlayerMovedServerResponse(player_pos=schemas.Position(**self.player.pos)))
        seed_val=(self.seed+self.current_dungeon_level) if self.seed is not None else random.randint(0,1_000_000)
        responses.append(schemas.GameMessageServerResponse(text=f"You descend to dungeon level {self.current_dungeon_level + 1}..."))
        dungeon_resp=self.generate_new_dungeon(seed=seed_val,width=game_config.DEFAULT_MAP_WIDTH,height=game_config.DEFAULT_MAP_HEIGHT,max_rooms=game_config.DEFAULT_MAX_ROOMS,room_min=game_config.DEFAULT_ROOM_MIN_SIZE,room_max=game_config.DEFAULT_ROOM_MAX_SIZE,is_new_level=True) 
        if isinstance(dungeon_resp,schemas.DungeonDataServerResponse): responses.append(dungeon_resp); return responses,True 
        else: responses.append(dungeon_resp);self.game_over=True;return responses,False

    def _handle_walk_on_tile_interaction(self, new_x: int, new_y: int, target_tile_actual: int) -> Tuple[List[schemas.ServerResponse], bool]:
        responses: List[schemas.ServerResponse] = []; player_moved_successfully=False
        if self._is_walkable_for_entity(new_x,new_y,"player"):
            self.player.pos={"x":new_x,"y":new_y}; player_moved_successfully=True
            item_key=MAP_TILE_TO_ITEM_TYPE.get(target_tile_actual)
            if item_key: 
                picked_item=self.player.add_item_to_inventory(item_key)
                if picked_item and self.map_manager.actual_dungeon_map:
                    self.map_manager.actual_dungeon_map[new_y][new_x]=TILE_FLOOR 
                    if self.map_manager.dungeon_map_for_client: self.map_manager.dungeon_map_for_client[new_y][new_x]=TILE_FLOOR
                    responses.append(schemas.TileChangeServerResponse(pos=schemas.Position(x=new_x,y=new_y),new_tile_type=TILE_FLOOR))
                    responses.append(schemas.GameMessageServerResponse(text=f"Picked up {picked_item['type_name']}."))
                    responses.append(schemas.PlayerStatsUpdateServerResponse(stats=self.player.create_player_stats_response()))
            responses.append(schemas.PlayerMovedServerResponse(player_pos=schemas.Position(**self.player.pos)))
        else: 
            if self.player.pos: responses.append(schemas.InvalidMoveServerResponse(reason="Path blocked (walk_on_tile).",player_pos=schemas.Position(**self.player.pos)))
        return responses,player_moved_successfully

    def handle_player_move(self, new_x: int, new_y: int) -> List[schemas.ServerResponse]:
        responses: List[schemas.ServerResponse] = []; action_taken_this_turn=False; descended_stairs_successfully=False
        
        if self.game_over:
            responses.append(schemas.GameMessageServerResponse(text="Game Over."))
            if self.player.pos: responses.append(schemas.PlayerMovedServerResponse(player_pos=schemas.Position(**self.player.pos)))
            return responses
        if not self.map_manager.actual_dungeon_map or not self.player.pos or not self.map_manager.dungeon_map_for_client:
            responses.append(schemas.ErrorServerResponse(message="Game not initialized for move."))
            return responses
        
        prev_player_pos=self.player.pos.copy() 

        if not (0 <= new_y < len(self.map_manager.actual_dungeon_map) and \
                0 <= new_x < len(self.map_manager.actual_dungeon_map[0])):
            responses.append(schemas.InvalidMoveServerResponse(reason="Target out of map bounds.", player_pos=schemas.Position(**prev_player_pos)))
            responses.append(schemas.PlayerMovedServerResponse(player_pos=schemas.Position(**prev_player_pos)))
            return responses

        target_tile_actual=self.map_manager.actual_dungeon_map[new_y][new_x]
        monster_at_target=self.entity_manager.get_monster_at(new_x,new_y)

        if monster_at_target: 
            responses.extend(self._handle_player_attack_interaction(monster_at_target))
            action_taken_this_turn=True 
        elif target_tile_actual==TILE_DOOR_CLOSED: 
            responses.extend(self._handle_open_door_interaction(new_x,new_y,prev_player_pos))
            action_taken_this_turn=True
        elif target_tile_actual==TILE_STAIRS_DOWN: 
            stair_responses,descended_stairs_successfully=self._handle_descend_stairs_interaction(new_x,new_y)
            responses.extend(stair_responses); action_taken_this_turn=True 
        elif self._is_walkable_for_entity(new_x,new_y,"player"):
            walk_responses,player_moved=self._handle_walk_on_tile_interaction(new_x,new_y,target_tile_actual)
            responses.extend(walk_responses)
            if player_moved:action_taken_this_turn=True
        else: 
            responses.append(schemas.InvalidMoveServerResponse(reason="Path blocked.",player_pos=schemas.Position(**prev_player_pos)))
            responses.append(schemas.PlayerMovedServerResponse(player_pos=schemas.Position(**prev_player_pos)))
        
        if action_taken_this_turn and not self.game_over: 
            current_fov_center = self.player.pos 
            if target_tile_actual == TILE_DOOR_CLOSED or monster_at_target: 
                current_fov_center = prev_player_pos
            
            if not descended_stairs_successfully: 
                fov_update_responses=self.map_manager.update_fov(current_fov_center) 
                responses.extend(fov_update_responses)
                responses.extend(self._check_and_reveal_newly_visible_monsters())
                responses.extend(self.process_monster_turns())
        return responses

    def handle_use_item(self, item_id: str) -> List[schemas.ServerResponse]:
        responses: List[schemas.ServerResponse] = []
        if self.game_over: responses.append(schemas.GameMessageServerResponse(text="Game Over.")); return responses
        item_instance = self.player.find_item_in_inventory(item_id)
        if not item_instance: 
            responses.append(schemas.GameMessageServerResponse(text="Item not found."))
            # Even if item not found, send stats to ensure client UI (e.g. selection) is consistent
            responses.append(schemas.PlayerStatsUpdateServerResponse(stats=self.player.create_player_stats_response()))
            return responses

        action_taken = False; item_name = item_instance.get("type_name", "item")
        
        if item_instance.get("equippable", False): 
            responses.append(schemas.GameMessageServerResponse(text=f"To equip {item_name}, use equip action."))
        elif item_instance.get("consumable", False):
            effect_id = item_instance.get("effect_id"); handler = ITEM_EFFECT_HANDLERS.get(effect_id) if effect_id else None
            if handler:
                effect_responses = handler(self, item_instance); responses.extend(effect_responses)
                if self.player.remove_item_from_inventory(item_id): action_taken = True
            else: responses.append(schemas.GameMessageServerResponse(text=f"{item_name} has no effect."))
        else: responses.append(schemas.GameMessageServerResponse(text=f"Cannot use {item_name} this way."))
        
        responses.append(schemas.PlayerStatsUpdateServerResponse(stats=self.player.create_player_stats_response()))
        
        if action_taken and not self.game_over and self.player.pos:
            if item_instance.get("effect_id") != "teleport_random": 
                 responses.extend(self.map_manager.update_fov(self.player.pos))
                 responses.extend(self._check_and_reveal_newly_visible_monsters())
            responses.extend(self.process_monster_turns())
        return responses

    def handle_equip_item(self, item_id: str) -> List[schemas.ServerResponse]:
        responses: List[schemas.ServerResponse] = []
        if self.game_over: responses.append(schemas.GameMessageServerResponse(text="Game Over.")); return responses
        
        equip_msg_responses, success = self.player.equip_item(item_id)
        responses.extend(equip_msg_responses)
        
        # Always send stats update regardless of success, as Player.equip_item might send messages
        # and client needs to reflect the current state (e.g. inventory if unequipped other item)
        responses.append(schemas.PlayerStatsUpdateServerResponse(stats=self.player.create_player_stats_response())) 

        if success and not self.game_over and self.player.pos:
            responses.extend(self.map_manager.update_fov(self.player.pos))
            responses.extend(self._check_and_reveal_newly_visible_monsters())
            responses.extend(self.process_monster_turns())
        return responses

    def handle_unequip_item(self, slot: str) -> List[schemas.ServerResponse]:
        responses: List[schemas.ServerResponse] = []
        if self.game_over: responses.append(schemas.GameMessageServerResponse(text="Game Over.")); return responses
        
        if slot not in self.player.equipment: 
            responses.append(schemas.GameMessageServerResponse(text=f"Invalid slot: {slot}"))
            responses.append(schemas.PlayerStatsUpdateServerResponse(stats=self.player.create_player_stats_response()))
            return responses
            
        unequip_msg_responses, success = self.player.unequip_item(slot)
        responses.extend(unequip_msg_responses)
        
        responses.append(schemas.PlayerStatsUpdateServerResponse(stats=self.player.create_player_stats_response()))

        if success and not self.game_over and self.player.pos:
            responses.extend(self.map_manager.update_fov(self.player.pos))
            responses.extend(self._check_and_reveal_newly_visible_monsters())
            responses.extend(self.process_monster_turns())
        return responses