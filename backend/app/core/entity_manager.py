# backend/app/core/entity_manager.py
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# No TILE_FLOOR needed here if GameState handles map modification after population
# from .tiles import TILE_FLOOR 

if TYPE_CHECKING:
    pass 

class EntityManager:
    def __init__(self, logger_parent_name: str = "EntityManager"):
        self.monsters_on_map: List[Dict[str, Any]] = []
        self.logger_ref = logger_parent_name 

    def initialize_entities(self):
        self.monsters_on_map = []

    def add_monster(self, monster_data: Dict[str, Any]):
        self.monsters_on_map.append(monster_data)

    def remove_monster(self, monster_instance: Dict[str, Any]) -> bool:
        try:
            self.monsters_on_map.remove(monster_instance)
            return True
        except ValueError:
            return False

    def get_monster_at(self, x: int, y: int) -> Optional[Dict[str, Any]]:
        for monster in self.monsters_on_map:
            if monster["x"] == x and monster["y"] == y:
                return monster
        return None

    def get_all_monsters(self) -> List[Dict[str, Any]]:
        return list(self.monsters_on_map)

    def get_monster_by_id(self, monster_id: str) -> Optional[Dict[str, Any]]:
        for monster in self.monsters_on_map:
            if monster["id"] == monster_id:
                return monster
        return None
    
    # populate_monsters_from_map_tiles is removed, GameState will handle this loop for now.