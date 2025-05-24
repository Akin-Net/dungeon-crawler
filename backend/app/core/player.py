# backend/app/core/player.py
import uuid
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from .. import schemas 
from .items.definitions import ITEM_TEMPLATES, ITEM_TYPE_POTION_HEAL, ITEM_TYPE_WEAPON_DAGGER
from . import config as game_config

if TYPE_CHECKING:
    pass 

class Player:
    def __init__(self, initial_pos: Dict[str, int], logger_ref: Any): 
        self.pos: Dict[str, int] = initial_pos
        self.hp: int = game_config.PLAYER_INITIAL_HP
        self.max_hp: int = game_config.PLAYER_INITIAL_MAX_HP
        self.attack: int = game_config.PLAYER_INITIAL_ATTACK 
        self.defense: int = game_config.PLAYER_INITIAL_DEFENSE 
        self.level: int = game_config.PLAYER_INITIAL_LEVEL
        self.xp: int = game_config.PLAYER_INITIAL_XP
        self.xp_to_next_level: int = self._calculate_xp_for_next_level(game_config.PLAYER_INITIAL_LEVEL)
        
        self.inventory: List[Dict[str, Any]] = [] 
        self.equipment: Dict[str, Optional[Dict[str, Any]]] = {
            "weapon": None,
            "armor": None,
        }
        self.logger = logger_ref 

    def reset_for_new_game(self, start_pos: Dict[str, int]):
        self.pos = start_pos
        self.hp = game_config.PLAYER_INITIAL_HP
        self.max_hp = game_config.PLAYER_INITIAL_MAX_HP
        self.attack = game_config.PLAYER_INITIAL_ATTACK
        self.defense = game_config.PLAYER_INITIAL_DEFENSE
        self.level = game_config.PLAYER_INITIAL_LEVEL
        self.xp = game_config.PLAYER_INITIAL_XP
        self.xp_to_next_level = self._calculate_xp_for_next_level(game_config.PLAYER_INITIAL_LEVEL)
        
        self.inventory = [] # Clear inventory
        self.equipment = {"weapon": None, "armor": None} # Clear equipment
        
        # Add starting potion to inventory
        self.add_item_to_inventory(ITEM_TYPE_POTION_HEAL) 
        
        # Create and directly equip starting dagger; it does not go into general inventory first
        start_dagger_template = ITEM_TEMPLATES.get(ITEM_TYPE_WEAPON_DAGGER)
        if start_dagger_template:
            dagger_for_equipment = {
                **start_dagger_template, 
                "id": str(uuid.uuid4()), 
                "type_key": ITEM_TYPE_WEAPON_DAGGER, 
                "quantity": 1
            }
            self.equipment["weapon"] = dagger_for_equipment
            # Note: This dagger is NOT in the self.inventory list at this point.
            # If unequipped later, it will be added to self.inventory.

    def full_heal(self):
        self.hp = self.get_effective_max_hp()

    def _calculate_xp_for_next_level(self, level: int) -> int:
        return game_config.BASE_XP_TO_LEVEL + ((level - 1) * game_config.XP_SCALAR_PER_LEVEL)

    def get_base_stats_dict(self) -> Dict[str, Any]: 
        return {
            "hp": self.hp, "max_hp": self.max_hp, "attack": self.attack, "defense": self.defense,
            "level": self.level, "xp": self.xp, "xp_to_next_level": self.xp_to_next_level,
        }

    def get_effective_stats(self) -> Dict[str, Any]:
        effective_attack = self.attack
        effective_defense = self.defense
        effective_max_hp = self.max_hp 

        if self.equipment["weapon"]:
            effective_attack += self.equipment["weapon"].get("attack_bonus", 0)
        if self.equipment["armor"]:
            effective_defense += self.equipment["armor"].get("defense_bonus", 0)
        
        return {
            "hp": self.hp, "max_hp": effective_max_hp, "attack": effective_attack,
            "defense": effective_defense, "level": self.level, "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
        }
    
    def get_effective_max_hp(self) -> int:
        return self.max_hp

    def _convert_item_to_detail(self, item_instance: Dict[str, Any]) -> schemas.InventoryItemDetail:
        return schemas.InventoryItemDetail(
            id=item_instance["id"], type_key=item_instance["type_key"], name=item_instance["type_name"],
            description=item_instance.get("description", ""), quantity=item_instance.get("quantity", 1),
            consumable=item_instance.get("consumable", False), equippable=item_instance.get("equippable", False),
            slot=item_instance.get("slot"), attack_bonus=item_instance.get("attack_bonus"),
            defense_bonus=item_instance.get("defense_bonus"), effect_value=item_instance.get("effect_value") )

    def create_player_stats_response(self) -> schemas.PlayerStatsResponse:
        effective_stats = self.get_effective_stats()
        inventory_details = [self._convert_item_to_detail(item) for item in self.inventory]
        equipment_details = {
            slot: self._convert_item_to_detail(item) if item else None
            for slot, item in self.equipment.items()
        }
        return schemas.PlayerStatsResponse(
            hp=effective_stats["hp"], max_hp=effective_stats["max_hp"], attack=effective_stats["attack"],
            defense=effective_stats["defense"], level=effective_stats["level"], xp=effective_stats["xp"],
            xp_to_next_level=effective_stats["xp_to_next_level"], inventory=inventory_details,
            equipment=equipment_details )

    def grant_xp(self, amount: int) -> Tuple[List[schemas.ServerResponse], bool]:
        responses: List[schemas.ServerResponse] = []
        if amount <= 0: return responses, False
        self.xp += amount
        leveled_up_in_this_call = False
        level_up_check_responses, leveled_up_flag = self._check_for_level_up()
        responses.extend(level_up_check_responses)
        if leveled_up_flag: leveled_up_in_this_call = True
        return responses, leveled_up_in_this_call

    def _check_for_level_up(self) -> Tuple[List[schemas.ServerResponse], bool]:
        responses: List[schemas.ServerResponse] = []
        leveled_up_this_check = False
        while self.xp >= self.xp_to_next_level:
            leveled_up_this_check = True
            self.xp -= self.xp_to_next_level; self.level += 1
            self.max_hp += game_config.HP_GAIN_PER_LEVEL
            self.attack += game_config.ATK_GAIN_PER_LEVEL
            self.defense += game_config.DEF_GAIN_PER_LEVEL
            self.hp = self.max_hp 
            self.xp_to_next_level = self._calculate_xp_for_next_level(self.level)
            level_up_message = (
                f"LEVEL UP! You reached level {self.level}! Max HP +{game_config.HP_GAIN_PER_LEVEL}, "
                f"Attack +{game_config.ATK_GAIN_PER_LEVEL}, Defense +{game_config.DEF_GAIN_PER_LEVEL}. You are fully healed." )
            responses.append(schemas.PlayerLeveledUpServerResponse(new_level=self.level, message=level_up_message))
            responses.append(schemas.GameMessageServerResponse(text=level_up_message))
        return responses, leveled_up_this_check

    def add_item_to_inventory(self, item_type_key: str) -> Optional[Dict[str, Any]]:
        item_template = ITEM_TEMPLATES.get(item_type_key)
        if not item_template:
            self.logger.warning(f"Player: Attempted to add unknown item type key: {item_type_key}")
            return None
        item_instance_data = {**item_template, "id":str(uuid.uuid4()), "type_key":item_type_key, "quantity":1}
        if item_template.get("stackable", False):
            for existing_item in self.inventory:
                if existing_item["type_key"] == item_type_key:
                    existing_item["quantity"] += 1; return existing_item
            self.inventory.append(item_instance_data)
        else: self.inventory.append(item_instance_data)
        return item_instance_data

    def find_item_in_inventory(self, item_id: str) -> Optional[Dict[str, Any]]:
        for item in self.inventory:
            if item["id"] == item_id: return item
        return None

    def remove_item_from_inventory(self, item_id: str, quantity_to_remove: int = 1) -> bool:
        item_idx_to_remove = -1
        for i, item_instance in enumerate(self.inventory):
            if item_instance["id"] == item_id:
                if item_instance.get("stackable",False) and item_instance["quantity"] > quantity_to_remove:
                    item_instance["quantity"] -= quantity_to_remove; return True
                else: item_idx_to_remove = i; break
        if item_idx_to_remove != -1: self.inventory.pop(item_idx_to_remove); return True
        return False

    def _equip_item_internal(self, item_to_equip: Dict[str, Any]) -> bool:
        """Internal equip logic for initial setup, no server responses. Assumes item is NOT in general inventory."""
        slot = item_to_equip.get("slot")
        if not slot:
            self.logger.warning(f"Player: Item {item_to_equip.get('type_name')} has no slot for _equip_item_internal.")
            return False
        # This method does not handle unequipping existing items or inventory management.
        # It's for direct placement, e.g., during player character initialization.
        self.equipment[slot] = item_to_equip
        return True

    def equip_item(self, item_id: str) -> Tuple[List[schemas.ServerResponse], bool]: 
        responses: List[schemas.ServerResponse] = []
        item_to_equip = self.find_item_in_inventory(item_id)
        if not item_to_equip:
            responses.append(schemas.GameMessageServerResponse(text="Cannot equip: Item not found in inventory."))
            return responses, False
        if not item_to_equip.get("equippable", False):
            responses.append(schemas.GameMessageServerResponse(text=f"You cannot equip the {item_to_equip['type_name']}."))
            return responses, False
        slot = item_to_equip.get("slot")
        if not slot:
            responses.append(schemas.GameMessageServerResponse(text=f"Cannot equip {item_to_equip['type_name']}: No designated slot."))
            return responses, False
        
        currently_equipped_item_in_slot = self.equipment.get(slot)
        if currently_equipped_item_in_slot: 
            self.equipment[slot] = None # Unequip current
            self.inventory.append(currently_equipped_item_in_slot) # Add old item back to inventory
            responses.append(schemas.GameMessageServerResponse(text=f"You unequip {currently_equipped_item_in_slot['type_name']}."))

        # Now, remove the item_to_equip from inventory before placing in equipment
        if not self.remove_item_from_inventory(item_id): 
            self.logger.error(f"Player: Item {item_id} found but failed to remove for equipping. This should not happen.")
            responses.append(schemas.GameMessageServerResponse(text=f"Error equipping {item_to_equip['type_name']}: Inventory inconsistency."))
            # Revert the unequip of the old item if we failed to remove the new one
            if currently_equipped_item_in_slot:
                 self.inventory.remove(currently_equipped_item_in_slot) # It was optimistically added
                 self.equipment[slot] = currently_equipped_item_in_slot
            return responses, False
            
        self.equipment[slot] = item_to_equip
        responses.append(schemas.GameMessageServerResponse(text=f"You equip the {item_to_equip['type_name']}."))
        return responses, True

    def unequip_item(self, slot: str) -> Tuple[List[schemas.ServerResponse], bool]: 
        responses: List[schemas.ServerResponse] = []
        item_to_unequip = self.equipment.get(slot)
        if not item_to_unequip:
            responses.append(schemas.GameMessageServerResponse(text=f"Nothing to unequip from {slot} slot."))
            return responses, False
        
        self.equipment[slot] = None
        self.inventory.append(item_to_unequip) # Add the unequipped item to inventory
        responses.append(schemas.GameMessageServerResponse(text=f"You unequip the {item_to_unequip['type_name']}."))
        return responses, True

    def take_damage(self, amount: int) -> bool: 
        self.hp -= amount
        if self.hp <= 0: self.hp = 0; return True 
        return False