# backend/app/tests/test_entity_manager.py
from typing import Any, Dict
import pytest
from unittest.mock import MagicMock

from app.core.entity_manager import EntityManager

@pytest.fixture
def entity_manager() -> EntityManager:
    """Provides a clean EntityManager instance for each test."""
    # logger_mock = MagicMock() # If EntityManager had its own logger instance it used
    # For now, logger_ref is just a name.
    return EntityManager(logger_parent_name="TestEntityManager")

# Sample monster data for testing
def create_monster_data(id_val: str, x: int, y: int, type_name: str = "goblin") -> Dict[str, Any]:
    return {
        "id": id_val, "x": x, "y": y, 
        "type_name": type_name, "tile_id": 4, # Example tile_id
        "hp": 10, "max_hp": 10, "attack": 3, "defense": 1
    }

def test_initialize_entities(entity_manager: EntityManager):
    monster1_data = create_monster_data("m1", 5, 5)
    entity_manager.add_monster(monster1_data)
    assert len(entity_manager.get_all_monsters()) == 1
    
    entity_manager.initialize_entities()
    assert len(entity_manager.get_all_monsters()) == 0

def test_add_monster(entity_manager: EntityManager):
    assert len(entity_manager.get_all_monsters()) == 0
    monster1_data = create_monster_data("m1", 5, 5)
    entity_manager.add_monster(monster1_data)
    
    monsters = entity_manager.get_all_monsters()
    assert len(monsters) == 1
    assert monsters[0]["id"] == "m1"
    assert monsters[0]["x"] == 5
    assert monsters[0]["y"] == 5

    monster2_data = create_monster_data("m2", 6, 6)
    entity_manager.add_monster(monster2_data)
    assert len(entity_manager.get_all_monsters()) == 2

def test_remove_monster_existing(entity_manager: EntityManager):
    monster1_data = create_monster_data("m1", 5, 5)
    monster2_data = create_monster_data("m2", 6, 6)
    entity_manager.add_monster(monster1_data)
    entity_manager.add_monster(monster2_data)
    
    assert len(entity_manager.get_all_monsters()) == 2
    removed = entity_manager.remove_monster(monster1_data) # Remove by object reference
    assert removed
    assert len(entity_manager.get_all_monsters()) == 1
    assert entity_manager.get_all_monsters()[0]["id"] == "m2"

def test_remove_monster_non_existing(entity_manager: EntityManager):
    monster1_data = create_monster_data("m1", 5, 5)
    entity_manager.add_monster(monster1_data)
    
    non_existing_monster_data = create_monster_data("m3", 7, 7) # Different object
    removed = entity_manager.remove_monster(non_existing_monster_data)
    assert not removed
    assert len(entity_manager.get_all_monsters()) == 1

def test_get_monster_at_found(entity_manager: EntityManager):
    monster1_data = create_monster_data("m1", 5, 5)
    monster2_data = create_monster_data("m2", 6, 6, "orc")
    entity_manager.add_monster(monster1_data)
    entity_manager.add_monster(monster2_data)

    found_monster = entity_manager.get_monster_at(6, 6)
    assert found_monster is not None
    assert found_monster["id"] == "m2"
    assert found_monster["type_name"] == "orc"

def test_get_monster_at_not_found(entity_manager: EntityManager):
    monster1_data = create_monster_data("m1", 5, 5)
    entity_manager.add_monster(monster1_data)
    
    assert entity_manager.get_monster_at(1, 1) is None # Empty spot
    assert entity_manager.get_monster_at(5, 6) is None # Wrong y

def test_get_monster_at_empty_list(entity_manager: EntityManager):
    assert entity_manager.get_monster_at(5, 5) is None

def test_get_all_monsters_empty(entity_manager: EntityManager):
    assert len(entity_manager.get_all_monsters()) == 0

def test_get_all_monsters_returns_copy(entity_manager: EntityManager):
    monster1_data = create_monster_data("m1", 5, 5)
    entity_manager.add_monster(monster1_data)
    
    list1 = entity_manager.get_all_monsters()
    assert len(list1) == 1
    list1.append(create_monster_data("m_temp",0,0)) # Modify the returned list
    
    # Original list in EntityManager should be unaffected
    assert len(entity_manager.get_all_monsters()) == 1 

def test_get_monster_by_id_found(entity_manager: EntityManager):
    monster1_data = create_monster_data("m1", 5, 5)
    monster2_data = create_monster_data("m2", 6, 6)
    entity_manager.add_monster(monster1_data)
    entity_manager.add_monster(monster2_data)

    found_monster = entity_manager.get_monster_by_id("m1")
    assert found_monster is not None
    assert found_monster["x"] == 5

    found_monster_2 = entity_manager.get_monster_by_id("m2")
    assert found_monster_2 is not None
    assert found_monster_2["x"] == 6

def test_get_monster_by_id_not_found(entity_manager: EntityManager):
    monster1_data = create_monster_data("m1", 5, 5)
    entity_manager.add_monster(monster1_data)
    assert entity_manager.get_monster_by_id("nonexistent_id") is None