# backend/app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, Union

# --- Payloads from Client ---
# ... (Position, PlayerMoveClientPayload, etc. unchanged) ...
class Position(BaseModel):
    x: int
    y: int

class PlayerMoveClientPayload(BaseModel):
    action: Literal["player_move"] = "player_move"
    new_pos: Position

class GenerateDungeonClientPayload(BaseModel):
    action: Literal["generate_dungeon"] = "generate_dungeon"
    seed: Optional[int] = None

class UseItemClientPayload(BaseModel):
    action: Literal["use_item"] = "use_item"
    item_id: str

class EquipItemClientPayload(BaseModel):
    action: Literal["equip_item"] = "equip_item"
    item_id: str

class UnequipItemClientPayload(BaseModel):
    action: Literal["unequip_item"] = "unequip_item"
    slot: str


# --- Responses to Client ---

class TileTypesResponse(BaseModel): # Unchanged
    EMPTY: int; FLOOR: int; WALL: int; ITEM_POTION: int; MONSTER_GOBLIN: int 
    MONSTER_ORC: int; MONSTER_SKELETON: int; DOOR_CLOSED: int; DOOR_OPEN: int   
    STAIRS_DOWN: int; FOG: int; ITEM_SCROLL_TELEPORT: int

class InventoryItemDetail(BaseModel): # Unchanged
    id: str; type_key: str; name: str; description: str; quantity: int = 1
    consumable: bool; equippable: bool; slot: Optional[str] = None
    attack_bonus: Optional[int] = None; defense_bonus: Optional[int] = None
    effect_value: Optional[Any] = None

class PlayerStatsResponse(BaseModel): # Unchanged
    hp: int; max_hp: int; attack: int; defense: int; level: int
    xp: int; xp_to_next_level: int; inventory: List[InventoryItemDetail]
    equipment: Dict[str, Optional[InventoryItemDetail]]

class MonsterInfoResponse(BaseModel): # Unchanged
    id: str; x: int; y: int; type: str; tile_id: int

class DungeonDataServerResponse(BaseModel): # Unchanged
    type: Literal["dungeon_data"] = "dungeon_data"; map: List[List[int]]
    player_start_pos: Position; tile_types: TileTypesResponse
    player_stats: PlayerStatsResponse; monsters: List[MonsterInfoResponse]
    seed_used: Optional[int] = None; current_dungeon_level: Optional[int] = None 

class PlayerMovedServerResponse(BaseModel): # Unchanged
    type: Literal["player_moved"] = "player_moved"; player_pos: Position

class InvalidMoveServerResponse(BaseModel): # Unchanged
    type: Literal["invalid_move"] = "invalid_move"; reason: str; player_pos: Position 

class TileChangeServerResponse(BaseModel): # Unchanged
    type: Literal["tile_change"] = "tile_change"; pos: Position; new_tile_type: int

class GameMessageServerResponse(BaseModel): # Unchanged
    type: Literal["game_message"] = "game_message"; text: str

class PlayerStatsUpdateServerResponse(BaseModel): # Unchanged
    type: Literal["player_stats_update"] = "player_stats_update"; stats: PlayerStatsResponse

class CombatEventServerResponse(BaseModel): # Unchanged
    type: Literal["combat_event"] = "combat_event"; attacker_faction: Optional[str] = None 
    attacker_id: Optional[str] = None; attacker_type: Optional[str] = None 
    defender_faction: Optional[str] = None; defender_id: Optional[str] = None 
    defender_type: Optional[str] = None; damage_done: int; defender_hp_current: int
    defender_hp_max: int; message: str

class EntityDiedServerResponse(BaseModel): # Unchanged
    type: Literal["entity_died"] = "entity_died"; entity_id: str; entity_type: str
    pos: Position; message: str

class PlayerDiedServerResponse(BaseModel): # Unchanged
    type: Literal["player_died"] = "player_died"; message: str

class MonsterMovedServerResponse(BaseModel): # Unchanged
    type: Literal["monster_moved"] = "monster_moved"; monster_id: str; new_pos: Position

class PlayerLeveledUpServerResponse(BaseModel): # Unchanged
    type: Literal["player_leveled_up"] = "player_leveled_up"; new_level: int; message: str

class ErrorServerResponse(BaseModel): # Unchanged
    type: Literal["error"] = "error"; message: str

# --- New Server Response ---
class MonsterAppearedServerResponse(BaseModel):
    type: Literal["monster_appeared"] = "monster_appeared"
    monster_info: MonsterInfoResponse

# Update the Union type for all possible server responses
ServerResponse = Union[
    DungeonDataServerResponse, PlayerMovedServerResponse, InvalidMoveServerResponse,
    TileChangeServerResponse, GameMessageServerResponse, PlayerStatsUpdateServerResponse,
    CombatEventServerResponse, EntityDiedServerResponse, PlayerDiedServerResponse,
    MonsterMovedServerResponse, ErrorServerResponse, PlayerLeveledUpServerResponse,
    MonsterAppearedServerResponse # Added new response type
]