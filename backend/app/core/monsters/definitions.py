# backend/app/core/monsters/definitions.py
from typing import Dict, Any
from ..tiles import ( 
    TILE_MONSTER_GOBLIN,
    TILE_MONSTER_ORC,
    TILE_MONSTER_SKELETON
)
from .. import config as game_config # Import the new config

# Centralized Monster Definitions
# Monster stats are now primarily loaded from game_config.MONSTER_DATA
# MONSTER_TEMPLATES will combine these with tile_id and type_name.

MONSTER_TEMPLATES: Dict[int, Dict[str, Any]] = {
    TILE_MONSTER_GOBLIN: {
        "type_name": "goblin", 
        "tile_id": TILE_MONSTER_GOBLIN,
        **game_config.MONSTER_DATA["goblin"], # Spread values from config
        "max_hp": game_config.MONSTER_DATA["goblin"]["hp"], # Explicitly set max_hp from configured hp
    },
    TILE_MONSTER_ORC: {
        "type_name": "orc", 
        "tile_id": TILE_MONSTER_ORC,
        **game_config.MONSTER_DATA["orc"],
        "max_hp": game_config.MONSTER_DATA["orc"]["hp"],
    },
    TILE_MONSTER_SKELETON: {
        "type_name": "skeleton", 
        "tile_id": TILE_MONSTER_SKELETON,
        **game_config.MONSTER_DATA["skeleton"],
        "max_hp": game_config.MONSTER_DATA["skeleton"]["hp"],
    }
}