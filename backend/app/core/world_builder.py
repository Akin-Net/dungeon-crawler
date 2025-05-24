# backend/app/core/world_builder.py
import uuid
from typing import Any, Dict, List, TYPE_CHECKING

from .tiles import TILE_FLOOR # For map updates
from .monsters.definitions import MONSTER_TEMPLATES # Import directly for convenience

if TYPE_CHECKING:
    from .map_manager import MapManager
    from .entity_manager import EntityManager
    from .player import Player

def populate_monsters_from_map_tiles(
    map_manager: 'MapManager', 
    entity_manager: 'EntityManager', 
    player: 'Player'
) -> None:
    """
    Scans the map_data for monster tiles, creates monster entities,
    adds them to the EntityManager, and changes the tile on map_data to TILE_FLOOR.
    Assumes map_manager.actual_dungeon_map and player.pos are valid.
    """
    if not map_manager.actual_dungeon_map or not player.pos:
        # Logger might be useful here if passed or made global
        print("Warning: Cannot populate monsters, map or player position not available.")
        return

    # Iterate over a copy of the map dimensions if modification happens during iteration,
    # or ensure modification doesn't affect iteration bounds.
    # Here, we modify map_data in place, which is fine for this loop structure.
    for r_idx, row in enumerate(map_manager.actual_dungeon_map):
        for c_idx, tile_val in enumerate(row):
            if tile_val in MONSTER_TEMPLATES: 
                if c_idx == player.pos["x"] and r_idx == player.pos["y"]:
                    map_manager.actual_dungeon_map[r_idx][c_idx] = TILE_FLOOR 
                    continue
                
                template = MONSTER_TEMPLATES[tile_val]
                monster_instance_data = template.copy()
                monster_instance_data.update({
                    "id": str(uuid.uuid4()), 
                    "x": c_idx, 
                    "y": r_idx, 
                    "hp": template["max_hp"], 
                    "last_known_player_pos": None
                })
                entity_manager.add_monster(monster_instance_data)
                map_manager.actual_dungeon_map[r_idx][c_idx] = TILE_FLOOR