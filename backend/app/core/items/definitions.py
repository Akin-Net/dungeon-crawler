# backend/app/core/items/definitions.py
from typing import Dict, Any
from ..tiles import TILE_ITEM_POTION, TILE_ITEM_SCROLL_TELEPORT
from .. import config as game_config # Import the new config

# Item type identifiers (keys for ITEM_TEMPLATES)
ITEM_TYPE_POTION_HEAL = "potion_heal"
ITEM_TYPE_SCROLL_TELEPORT = "scroll_teleport"
ITEM_TYPE_WEAPON_DAGGER = "weapon_dagger"
ITEM_TYPE_ARMOR_LEATHER = "armor_leather"

ITEM_TEMPLATES: Dict[str, Dict[str, Any]] = {
    ITEM_TYPE_POTION_HEAL: {
        "type_name": "Health Potion",
        "tile_id": TILE_ITEM_POTION, 
        "effect_id": "heal", 
        "effect_value": game_config.ITEM_EFFECT_VALUES["potion_heal_amount"], # Use config
        "consumable": True,
        "equippable": False,
        "stackable": True, 
        "description": "A Potion that restores some health."
    },
    ITEM_TYPE_SCROLL_TELEPORT: {
        "type_name": "Scroll of Teleportation",
        "tile_id": TILE_ITEM_SCROLL_TELEPORT,
        "effect_id": "teleport_random",
        "consumable": True,
        "equippable": False,
        "stackable": True, 
        "description": "Teleports you to a random, safe location on this level."
    },
    ITEM_TYPE_WEAPON_DAGGER: {
        "type_name": "Dagger",
        "equippable": True,
        "consumable": False,
        "slot": "weapon",
        "attack_bonus": game_config.ITEM_BONUSES["dagger_attack_bonus"], # Use config
        "description": f"A simple, sharp dagger. Adds +{game_config.ITEM_BONUSES['dagger_attack_bonus']} to Attack."
    },
    ITEM_TYPE_ARMOR_LEATHER: {
        "type_name": "Leather Armor",
        "equippable": True,
        "consumable": False,
        "slot": "armor",
        "defense_bonus": game_config.ITEM_BONUSES["leather_armor_defense_bonus"], # Use config
        "description": f"Basic leather armor. Adds +{game_config.ITEM_BONUSES['leather_armor_defense_bonus']} to Defense."
    }
}

MAP_TILE_TO_ITEM_TYPE: Dict[int, str] = {
    TILE_ITEM_POTION: ITEM_TYPE_POTION_HEAL,
    TILE_ITEM_SCROLL_TELEPORT: ITEM_TYPE_SCROLL_TELEPORT,
}