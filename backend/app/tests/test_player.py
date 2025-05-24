# backend/app/tests/test_player.py
import pytest
from unittest.mock import MagicMock
import uuid # Ensure uuid is imported if Player.reset_for_new_game uses it.

from app.core.player import Player
from app.core import config as game_config
from app.core.items.definitions import ITEM_TEMPLATES, ITEM_TYPE_POTION_HEAL, ITEM_TYPE_WEAPON_DAGGER, ITEM_TYPE_ARMOR_LEATHER
from app.schemas import PlayerStatsResponse, InventoryItemDetail 

@pytest.fixture
def new_player() -> Player:
    mock_logger = MagicMock() 
    player = Player(initial_pos={"x": 1, "y": 1}, logger_ref=mock_logger)
    player.reset_for_new_game({"x":1, "y":1}) 
    return player

# --- Tests for Initialization and Reset ---
def test_player_initial_stats(new_player: Player):
    assert new_player.hp == game_config.PLAYER_INITIAL_HP
    assert new_player.max_hp == game_config.PLAYER_INITIAL_MAX_HP
    assert new_player.attack == game_config.PLAYER_INITIAL_ATTACK
    assert new_player.defense == game_config.PLAYER_INITIAL_DEFENSE
    assert new_player.level == game_config.PLAYER_INITIAL_LEVEL
    assert new_player.xp == game_config.PLAYER_INITIAL_XP
    # CORRECTED ASSERTION: Inventory now only contains the potion initially.
    assert len(new_player.inventory) == 1 
    assert new_player.inventory[0]["type_key"] == ITEM_TYPE_POTION_HEAL
    assert new_player.equipment.get("weapon") is not None 
    assert new_player.equipment.get("weapon")["type_key"] == ITEM_TYPE_WEAPON_DAGGER
    assert new_player.equipment.get("armor") is None

def test_player_reset_for_new_game(new_player: Player):
    new_player.level = 5
    new_player.xp = 500
    new_player.hp = 5
    new_player.add_item_to_inventory(ITEM_TYPE_ARMOR_LEATHER) 
    
    new_player.reset_for_new_game({"x":2, "y":2})
    
    assert new_player.pos == {"x":2, "y":2}
    assert new_player.hp == game_config.PLAYER_INITIAL_HP
    assert new_player.xp == game_config.PLAYER_INITIAL_XP
    assert new_player.level == game_config.PLAYER_INITIAL_LEVEL
    # CORRECTED ASSERTION: Inventory now only contains the potion after reset.
    assert len(new_player.inventory) == 1 
    assert new_player.inventory[0]["type_key"] == ITEM_TYPE_POTION_HEAL
    assert new_player.equipment.get("weapon")["type_key"] == ITEM_TYPE_WEAPON_DAGGER

# --- Tests for XP and Leveling ---
def test_calculate_xp_for_next_level(new_player: Player):
    assert new_player._calculate_xp_for_next_level(1) == game_config.BASE_XP_TO_LEVEL
    assert new_player._calculate_xp_for_next_level(2) == game_config.BASE_XP_TO_LEVEL + game_config.XP_SCALAR_PER_LEVEL
    assert new_player._calculate_xp_for_next_level(3) == game_config.BASE_XP_TO_LEVEL + (2 * game_config.XP_SCALAR_PER_LEVEL)

def test_grant_xp_no_level_up(new_player: Player):
    initial_xp = new_player.xp
    xp_to_grant = 50
    responses, leveled_up = new_player.grant_xp(xp_to_grant)
    
    assert not leveled_up
    assert new_player.xp == initial_xp + xp_to_grant
    assert len(responses) == 0 

def test_grant_xp_level_up_once(new_player: Player):
    # Reset player to base level 1 stats for this specific test if needed,
    # though fixture already provides a fresh player.
    new_player.reset_for_new_game(new_player.pos) # Ensure clean state
    new_player.xp = 0 
    new_player.xp_to_next_level = new_player._calculate_xp_for_next_level(1)

    xp_to_grant = game_config.BASE_XP_TO_LEVEL + 10 
    
    responses, leveled_up = new_player.grant_xp(xp_to_grant)
    
    assert leveled_up
    assert new_player.level == 2
    assert new_player.xp == 10 
    assert new_player.max_hp == game_config.PLAYER_INITIAL_MAX_HP + game_config.HP_GAIN_PER_LEVEL
    assert new_player.hp == new_player.max_hp 
    assert new_player.attack == game_config.PLAYER_INITIAL_ATTACK + game_config.ATK_GAIN_PER_LEVEL
    assert new_player.defense == game_config.PLAYER_INITIAL_DEFENSE + game_config.DEF_GAIN_PER_LEVEL
    assert new_player.xp_to_next_level == new_player._calculate_xp_for_next_level(2)
    assert len(responses) == 2 
    assert responses[0].type == "player_leveled_up"
    assert responses[1].type == "game_message"

def test_grant_xp_level_up_multiple(new_player: Player):
    new_player.reset_for_new_game(new_player.pos) # Ensure clean state
    new_player.xp = 0
    new_player.level = 1
    # Explicitly reset these to base, as reset_for_new_game does it.
    new_player.max_hp = game_config.PLAYER_INITIAL_MAX_HP 
    new_player.attack = game_config.PLAYER_INITIAL_ATTACK
    new_player.defense = game_config.PLAYER_INITIAL_DEFENSE
    new_player.xp_to_next_level = new_player._calculate_xp_for_next_level(1)

    xp_for_level_1_to_2 = new_player._calculate_xp_for_next_level(1)
    xp_for_level_2_to_3 = new_player._calculate_xp_for_next_level(2)
    xp_to_grant = xp_for_level_1_to_2 + xp_for_level_2_to_3 + 20

    responses, leveled_up = new_player.grant_xp(xp_to_grant)

    assert leveled_up
    assert new_player.level == 3
    assert new_player.xp == 20 
    assert new_player.max_hp == game_config.PLAYER_INITIAL_MAX_HP + (2 * game_config.HP_GAIN_PER_LEVEL)
    assert new_player.hp == new_player.max_hp
    assert len(responses) == 4 

# --- Tests for Damage and Healing ---
def test_take_damage_no_death(new_player: Player):
    initial_hp = new_player.hp
    damage = 5
    died = new_player.take_damage(damage)
    assert not died
    assert new_player.hp == initial_hp - damage

def test_take_damage_exact_death(new_player: Player):
    damage = new_player.hp
    died = new_player.take_damage(damage)
    assert died
    assert new_player.hp == 0

def test_take_damage_overkill(new_player: Player):
    damage = new_player.hp + 10
    died = new_player.take_damage(damage)
    assert died
    assert new_player.hp == 0

def test_full_heal(new_player: Player):
    new_player.hp = 1
    new_player.full_heal()
    assert new_player.hp == new_player.max_hp 

# --- Tests for Inventory ---
def test_add_item_to_inventory_non_stackable(new_player: Player):
    new_player.inventory = [] 
    item_data = new_player.add_item_to_inventory(ITEM_TYPE_WEAPON_DAGGER)
    assert item_data is not None
    assert len(new_player.inventory) == 1
    assert new_player.inventory[0]["type_key"] == ITEM_TYPE_WEAPON_DAGGER
    assert new_player.inventory[0]["quantity"] == 1

    item_data2 = new_player.add_item_to_inventory(ITEM_TYPE_WEAPON_DAGGER) 
    assert item_data2 is not None
    assert len(new_player.inventory) == 2 

def test_add_item_to_inventory_stackable(new_player: Player):
    new_player.inventory = [] 
    item_data1 = new_player.add_item_to_inventory(ITEM_TYPE_POTION_HEAL)
    assert item_data1 is not None
    assert len(new_player.inventory) == 1
    assert new_player.inventory[0]["quantity"] == 1

    item_data2 = new_player.add_item_to_inventory(ITEM_TYPE_POTION_HEAL) 
    assert item_data2 is not None
    assert len(new_player.inventory) == 1 
    assert new_player.inventory[0]["quantity"] == 2
    assert item_data1["id"] == item_data2["id"] 

def test_find_item_in_inventory(new_player: Player):
    new_player.inventory = []
    item1 = new_player.add_item_to_inventory(ITEM_TYPE_POTION_HEAL)
    assert item1 is not None
    found_item = new_player.find_item_in_inventory(item1["id"])
    assert found_item is not None
    assert found_item["id"] == item1["id"]
    assert new_player.find_item_in_inventory("nonexistent_id") is None

def test_remove_item_from_inventory_single(new_player: Player):
    new_player.inventory = []
    item1 = new_player.add_item_to_inventory(ITEM_TYPE_WEAPON_DAGGER)
    assert item1 is not None
    removed = new_player.remove_item_from_inventory(item1["id"])
    assert removed
    assert len(new_player.inventory) == 0
    assert not new_player.remove_item_from_inventory("nonexistent_id")

def test_remove_item_from_inventory_stackable_partial(new_player: Player):
    new_player.inventory = []
    item1 = new_player.add_item_to_inventory(ITEM_TYPE_POTION_HEAL) 
    new_player.add_item_to_inventory(ITEM_TYPE_POTION_HEAL) 
    new_player.add_item_to_inventory(ITEM_TYPE_POTION_HEAL) 
    assert item1 is not None and new_player.inventory[0]["quantity"] == 3
    
    removed = new_player.remove_item_from_inventory(item1["id"]) 
    assert removed
    assert len(new_player.inventory) == 1
    assert new_player.inventory[0]["quantity"] == 2

    removed = new_player.remove_item_from_inventory(item1["id"], quantity_to_remove=2) 
    assert removed
    assert len(new_player.inventory) == 0

# --- Tests for Equipment ---
def test_equip_item_weapon(new_player: Player):
    # new_player fixture calls reset_for_new_game, which equips a dagger.
    # First, unequip the starting dagger to test equipping from inventory.
    starting_dagger = new_player.equipment["weapon"]
    assert starting_dagger is not None
    responses_unequip, success_unequip = new_player.unequip_item("weapon")
    assert success_unequip
    assert new_player.equipment["weapon"] is None
    assert new_player.find_item_in_inventory(starting_dagger["id"]) is not None # It's now in inventory
    
    # Now, equip it back from inventory
    responses, success = new_player.equip_item(starting_dagger["id"])
    assert success
    assert len(responses) > 0
    # The equip message might be different if it first unequips nothing then equips.
    # Check that the specific item is equipped.
    assert new_player.equipment["weapon"] is not None
    assert new_player.equipment["weapon"]["id"] == starting_dagger["id"]
    assert new_player.find_item_in_inventory(starting_dagger["id"]) is None # Should be removed from inventory

def test_equip_item_replaces_existing(new_player: Player):
    # new_player starts with a dagger equipped
    initial_dagger_id = new_player.equipment["weapon"]["id"]

    # Add a new weapon to inventory
    better_sword_data = new_player.add_item_to_inventory(ITEM_TYPE_WEAPON_DAGGER) # Using dagger type for simplicity
    assert better_sword_data is not None
    better_sword_id = better_sword_data["id"]
    
    responses, success = new_player.equip_item(better_sword_id)
    assert success
    assert new_player.equipment["weapon"] is not None
    assert new_player.equipment["weapon"]["id"] == better_sword_id
    
    found_initial_dagger = new_player.find_item_in_inventory(initial_dagger_id)
    assert found_initial_dagger is not None, "Initial dagger should be back in inventory"

def test_unequip_item(new_player: Player):
    # new_player starts with a dagger equipped
    dagger_in_equipment = new_player.equipment["weapon"]
    assert dagger_in_equipment is not None
    dagger_id = dagger_in_equipment["id"]

    responses, success = new_player.unequip_item("weapon")
    assert success
    assert len(responses) > 0
    assert responses[0].text.startswith("You unequip the Dagger") # Or whatever its name is
    assert new_player.equipment["weapon"] is None
    assert new_player.find_item_in_inventory(dagger_id) is not None

# --- Test Effective Stats ---
def test_effective_stats_no_equipment(new_player: Player):
    new_player.equipment["weapon"] = None # Ensure no weapon for this test
    new_player.equipment["armor"] = None
    eff_stats = new_player.get_effective_stats()
    assert eff_stats["attack"] == new_player.attack
    assert eff_stats["defense"] == new_player.defense
    assert eff_stats["max_hp"] == new_player.max_hp

def test_effective_stats_with_weapon(new_player: Player):
    # new_player starts with dagger equipped by fixture.
    # We can directly check its effect.
    base_attack = new_player.attack
    dagger_bonus = new_player.equipment["weapon"].get("attack_bonus", 0)
    
    eff_stats = new_player.get_effective_stats()
    assert eff_stats["attack"] == base_attack + dagger_bonus

def test_effective_stats_with_armor(new_player: Player):
    new_player.equipment["armor"] = None # Ensure no armor first
    armor_data = new_player.add_item_to_inventory(ITEM_TYPE_ARMOR_LEATHER)
    assert armor_data is not None
    new_player.equip_item(armor_data["id"]) # Equip the armor
    
    base_defense = new_player.defense
    armor_bonus = new_player.equipment["armor"].get("defense_bonus", 0)
    
    eff_stats = new_player.get_effective_stats()
    assert eff_stats["defense"] == base_defense + armor_bonus