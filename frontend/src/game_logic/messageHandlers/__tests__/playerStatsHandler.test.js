// frontend/src/game_logic/messageHandlers/__tests__/playerStatsHandler.test.js
import { handlePlayerStatsUpdate } from '../playerStatsHandler';
import { initialState, INITIAL_PLAYER_STATS } from '../../initialState'; // Assuming INITIAL_PLAYER_STATS is exported

describe('handlePlayerStatsUpdate', () => {
  let baseState;

  beforeEach(() => {
    baseState = { 
      ...initialState, // Use the full initial state as a base
      // Override playerStats for a defined starting point if needed, or use INITIAL_PLAYER_STATS
      playerStats: { 
        ...INITIAL_PLAYER_STATS, // Spread default initial stats
        hp: 10, max_hp: 20, attack: 5, defense: 2, level: 1, xp: 0, xp_to_next_level: 100,
        inventory: [{id: "old_potion", type_key: "potion_heal", name: "Old Potion", description: "", quantity: 1, consumable: true, equippable: false, slot: null}],
        equipment: { 
          weapon: {id: "old_dagger", type_key: "weapon_dagger", name: "Old Dagger", description: "", quantity: 1, consumable: false, equippable: true, slot: "weapon", attack_bonus: 1}, 
          armor: null 
        }
      },
      dungeonMap: [[0]], // Example other state parts
      monsters: [{id: "m1"}]
    };
  });

  test('should correctly update all player stats, inventory, and equipment', () => {
    const newStatsPayload = {
      hp: 18, max_hp: 25, attack: 6, defense: 3,
      level: 2, xp: 50, xp_to_next_level: 150,
      inventory: [
        { id: "item1", type_key: "potion_heal", name: "Health Potion", description: "Heals.", quantity: 2, consumable: true, equippable: false, slot: null, attack_bonus: null, defense_bonus: null, effect_value: 10 }
      ],
      equipment: {
        weapon: { id: "item2", type_key: "weapon_dagger", name: "Dagger", description: "Sharp.", quantity: 1, consumable: false, equippable: true, slot: "weapon", attack_bonus: 2, defense_bonus: null, effect_value: null },
        armor: null
      }
    };
    const message = {
      type: "player_stats_update",
      stats: newStatsPayload
    };

    const newState = handlePlayerStatsUpdate(baseState, message);

    expect(newState.playerStats).toEqual(newStatsPayload);
    // Ensure other parts of the state are not touched
    expect(newState.dungeonMap).toBe(baseState.dungeonMap);
    expect(newState.monsters).toBe(baseState.monsters);
    expect(newState.gameMessage).toBe(baseState.gameMessage); // Assuming gameMessage wasn't part of baseState for this test or is handled separately
  });

  test('should update player stats with empty inventory and equipment', () => {
    const newStatsPayload = {
      hp: 5, max_hp: 15, attack: 4, defense: 1,
      level: 1, xp: 10, xp_to_next_level: 100,
      inventory: [], // Empty inventory
      equipment: { weapon: null, armor: null } // Empty equipment
    };
    const message = {
      type: "player_stats_update",
      stats: newStatsPayload
    };
    
    const newState = handlePlayerStatsUpdate(baseState, message);
    expect(newState.playerStats).toEqual(newStatsPayload);
    expect(newState.playerStats.inventory).toEqual([]);
    expect(newState.playerStats.equipment).toEqual({ weapon: null, armor: null });
  });

  test('should correctly assign stats object even if some optional item fields are missing', () => {
    const newStatsPayload = {
      hp: 10, max_hp: 20, attack: 5, defense: 2,
      level: 1, xp: 0, xp_to_next_level: 100,
      inventory: [
        { id: "item_min", type_key: "potion_heal", name: "Basic Potion", consumable: true, equippable: false, quantity: 1, description: "", slot: null, attack_bonus: null, defense_bonus: null, effect_value: null }
      ],
      equipment: { weapon: null, armor: null }
    };
     const message = {
      type: "player_stats_update",
      stats: newStatsPayload
    };

    const newState = handlePlayerStatsUpdate(baseState, message);
    expect(newState.playerStats).toEqual(newStatsPayload);
  });
});