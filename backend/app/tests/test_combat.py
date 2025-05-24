# backend/app/tests/test_combat.py
import pytest
from app.core import combat # Adjust import path if necessary based on your project structure

# --- Tests for calculate_damage ---

def test_calculate_damage_positive_damage():
    assert combat.calculate_damage(attacker_attack=10, defender_defense=5) == 5

def test_calculate_damage_zero_damage_equal_stats():
    assert combat.calculate_damage(attacker_attack=5, defender_defense=5) == 0

def test_calculate_damage_negative_result_becomes_zero():
    assert combat.calculate_damage(attacker_attack=3, defender_defense=10) == 0

def test_calculate_damage_zero_attack():
    assert combat.calculate_damage(attacker_attack=0, defender_defense=5) == 0

def test_calculate_damage_zero_defense():
    assert combat.calculate_damage(attacker_attack=7, defender_defense=0) == 7

def test_calculate_damage_both_zero():
    assert combat.calculate_damage(attacker_attack=0, defender_defense=0) == 0

# --- Tests for apply_attack ---

def test_apply_attack_deals_damage_no_kill():
    damage, hp_after, died, msg = combat.apply_attack(
        attacker_name="Player", attacker_effective_attack=10,
        defender_name="Goblin", defender_current_hp=15, defender_effective_defense=3
    )
    assert damage == 7
    assert hp_after == 8
    assert not died
    assert "Player hits Goblin for 7 damage." in msg

def test_apply_attack_deals_exact_kill():
    damage, hp_after, died, msg = combat.apply_attack(
        attacker_name="Orc", attacker_effective_attack=8,
        defender_name="Player", defender_current_hp=8, defender_effective_defense=0
    )
    assert damage == 8
    assert hp_after == 0
    assert died
    assert "Orc hits Player for 8 damage." in msg # "you" is usually for GameState context

def test_apply_attack_overkill():
    damage, hp_after, died, msg = combat.apply_attack(
        attacker_name="Skeleton", attacker_effective_attack=20,
        defender_name="Goblin", defender_current_hp=5, defender_effective_defense=1
    )
    assert damage == 19
    assert hp_after == 0 # HP should not go below 0
    assert died
    assert "Skeleton hits Goblin for 19 damage." in msg

def test_apply_attack_no_damage():
    damage, hp_after, died, msg = combat.apply_attack(
        attacker_name="Player", attacker_effective_attack=5,
        defender_name="Orc", defender_current_hp=20, defender_effective_defense=5
    )
    assert damage == 0
    assert hp_after == 20
    assert not died
    assert "Player attacks Orc but deals no damage." in msg

def test_apply_attack_defender_already_low_hp_survives():
    damage, hp_after, died, msg = combat.apply_attack(
        attacker_name="Goblin", attacker_effective_attack=3,
        defender_name="Player", defender_current_hp=2, defender_effective_defense=1
    )
    assert damage == 2
    assert hp_after == 0 # Should be 0, as it's a kill
    assert died # This was a bug in my manual test thought, fixed.
    assert "Goblin hits Player for 2 damage." in msg


# --- Placeholder for more complex tests for resolver functions ---
# These would require mocking GameState and its components, or setting up test fixtures.

# @pytest.mark.skip(reason="Requires mocking GameState and its components")
# def test_resolve_player_attack_on_monster_kill():
#     # TODO: Setup mock GameState, mock Player, mock EntityManager, mock MapManager
#     # Call resolve_player_attack_on_monster and assert responses and state changes
#     pass

# @pytest.mark.skip(reason="Requires mocking GameState and its components")
# def test_resolve_monster_attack_on_player_damages():
#     # TODO: Setup mock GameState, mock Player
#     # Call resolve_monster_attack_on_player and assert responses and state changes
#     pass

if __name__ == "__main__":
    # This allows running the tests directly with `python -m app.tests.test_combat`
    # (though `pytest` is preferred for better output and discovery)
    pytest.main()