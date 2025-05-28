// frontend/src/game_logic/messageHandlers/__tests__/dungeonDataHandler.test.js
import { handleDungeonData } from '../dungeonDataHandler';
import { initialState, INITIAL_PLAYER_STATS, LOCAL_TILE_TYPES } from '../../initialState';

describe('handleDungeonData', () => {
  let baseCurrentState;
  let fullMessage;

  beforeEach(() => {
    baseCurrentState = {
      ...initialState, 
      isLoading: true,
      isGameOver: true,
      currentDungeonLevel: 5, 
      monsters: [{ "id": "old_monster", "type": "zombie", "x": 0, "y": 0, "tile_id": 99 }],
      gameMessage: {"text": "Old message", "isError": true, "duration": 1000}
    };

    fullMessage = {
      "type": "dungeon_data",
      "map": [[10, 12], [12, 10]],
      "player_start_pos": { "x": 1, "y": 1 },
      "tile_types": { 
        "EMPTY": 0, "FLOOR": 1, "WALL": 2, "ITEM_POTION": 3, 
        "MONSTER_GOBLIN": 4, "MONSTER_ORC": 5, "MONSTER_SKELETON": 6, 
        "DOOR_CLOSED": 7, "DOOR_OPEN": 8, "STAIRS_DOWN": 10, 
        "FOG": 11, "ITEM_SCROLL_TELEPORT": 12 
      },
      "player_stats": {
        "hp": 30, "max_hp": 30, "attack": 7, "defense": 4, "level": 3, "xp": 10, "xp_to_next_level": 200,
        "inventory": [{ "id": "p2", "type_key": "potion_super", "name": "Super Potion", "description": "super", "quantity": 1, "consumable": true, "equippable": false, "slot": null, "attack_bonus": null, "defense_bonus": null, "effect_value": null }],
        "equipment": { "weapon": { "id": "w1", "type_key": "weapon_sword", "name": "Sword", "description": "strong", "quantity": 1, "consumable": false, "equippable": true, "slot": "weapon", "attack_bonus": 5, "defense_bonus": null, "effect_value": null }, "armor": null }
      },
      "monsters": [
        { "id": "new_g1", "x": 0, "y": 1, "type": "goblin_new", "tile_id": 4 }
      ],
      "seed_used": 54321,
      "current_dungeon_level": 2
    };
  });

  test('should correctly update state with full dungeon data', () => {
    const newState = handleDungeonData(baseCurrentState, fullMessage);

    expect(newState.isLoading).toBe(false);
    expect(newState.dungeonMap).toEqual(fullMessage.map);
    expect(newState.playerPos).toEqual(fullMessage.player_start_pos);
    expect(newState.tileDefinitions).toEqual({ ...LOCAL_TILE_TYPES, ...fullMessage.tile_types });
    expect(newState.playerStats).toEqual(fullMessage.player_stats);
    expect(newState.monsters).toEqual(fullMessage.monsters);
    expect(newState.isGameOver).toBe(false);
    expect(newState.currentDungeonLevel).toBe(fullMessage.current_dungeon_level);
    expect(newState.selectedInventoryItemIndex).toBeNull();
    expect(newState.gameMessage).toEqual({
      text: `Entered Dungeon Level ${fullMessage.current_dungeon_level} (Seed: ${fullMessage.seed_used}).`,
      isError: false,
      duration: 5000
    });
  });

  test('should use INITIAL_PLAYER_STATS if message.player_stats is missing', () => {
    const messageWithoutPlayerStats = { ...fullMessage, "player_stats": undefined }; 
    const newState = handleDungeonData(baseCurrentState, messageWithoutPlayerStats);
    expect(newState.playerStats).toEqual(INITIAL_PLAYER_STATS);
  });

  test('should use empty array for monsters if message.monsters is missing', () => {
    const messageWithoutMonsters = { ...fullMessage, "monsters": undefined };
    const newState = handleDungeonData(baseCurrentState, messageWithoutMonsters);
    expect(newState.monsters).toEqual([]);
  });

  test('should use currentState.currentDungeonLevel if message.current_dungeon_level is missing', () => {
    const messageWithoutLevel = { ...fullMessage, "current_dungeon_level": undefined, "seed_used": 777 };
    const newState = handleDungeonData(baseCurrentState, messageWithoutLevel);
    expect(newState.currentDungeonLevel).toBe(5); 
    expect(newState.gameMessage.text).toBe(`Entered Dungeon Level 5 (Seed: 777).`);
  });
  
  test('should use default 1 for currentDungeonLevel if both message and currentState lack it', () => {
    const stateWithoutLevel = { ...baseCurrentState, currentDungeonLevel: undefined };
    const messageWithoutLevelAndSeed = { ...fullMessage, "current_dungeon_level": undefined, "seed_used": undefined };
    const newState = handleDungeonData(stateWithoutLevel, messageWithoutLevelAndSeed);
    expect(newState.currentDungeonLevel).toBe(1);
    expect(newState.gameMessage.text).toBe(`Entered Dungeon Level 1 (Seed: N/A).`);
  });

  test('should display N/A for seed if message.seed_used is missing', () => {
    const messageWithoutSeed = { ...fullMessage, "seed_used": undefined };
    const newState = handleDungeonData(baseCurrentState, messageWithoutSeed);
    expect(newState.gameMessage.text).toBe(`Entered Dungeon Level ${fullMessage.current_dungeon_level} (Seed: N/A).`);
  });
});