// frontend/src/hooks/__tests__/useGameState.test.js
import { renderHook, act } from '@testing-library/react';
import { useGameState } from '../useGameState'; 
import { initialState, INITIAL_PLAYER_STATS } from '../../game_logic/initialState'; 
import { vi } from 'vitest'; 

describe('useGameState Hook - Action Creators', () => {
  let mockSendMessageToServer;

  beforeEach(() => {
    mockSendMessageToServer = vi.fn(); 
  });

  // Helper to get a clean hook instance, optionally with initial messages
  const getHook = (initialMessages = []) => {
    return renderHook((props) => useGameState(props.messageBatchFromServer, props.mockSendMessageToServer), {
      initialProps: { messageBatchFromServer: initialMessages, mockSendMessageToServer }
    });
  };

  test('requestNewDungeonGeneration should dispatch SET_LOADING (isNewLevel=false) and call sendMessageToServer', () => {
    const { result, rerender } = getHook(); // Start with empty messages
    
    // Ensure isLoading is false initially by simulating a prior load if needed
    if (result.current.isLoading) {
      const initialLoadMessage = [{ 
        type: 'dungeon_data', map: [], player_start_pos: {x:0,y:0}, 
        tile_types: {}, player_stats: INITIAL_PLAYER_STATS, monsters: [] 
      }];
      act(() => {
        rerender({messageBatchFromServer: initialLoadMessage, mockSendMessageToServer});
      });
    }
    expect(result.current.isLoading).toBe(false); // Should be false after initial load

    act(() => {
      result.current.requestNewDungeonGeneration(123, false); // isNewLevel = false
    });

    expect(result.current.isLoading).toBe(true); // Now should be true
    expect(result.current.gameMessage.text).toContain('Requesting dungeon (Seed: 123)');
    expect(mockSendMessageToServer).toHaveBeenCalledTimes(1);
    expect(mockSendMessageToServer).toHaveBeenCalledWith({ 
      action: 'generate_dungeon', 
      seed: 123 
    });
  });

  test('requestNewDungeonGeneration for new level (isNewLevel=true) should not set isLoading', () => {
    const { result, rerender } = getHook(); 
    
    if (result.current.isLoading) {
      const initialLoadMessage = [{ 
        type: 'dungeon_data', map: [], player_start_pos: {x:0,y:0}, 
        tile_types: {}, player_stats: INITIAL_PLAYER_STATS, monsters: [] 
      }];
      act(() => {
        rerender({messageBatchFromServer: initialLoadMessage, mockSendMessageToServer});
      });
    }
    expect(result.current.isLoading).toBe(false);
    
    act(() => {
      result.current.requestNewDungeonGeneration(456, true); // isNewLevel = true
    });

    expect(result.current.isLoading).toBe(false); 
    expect(result.current.gameMessage.text).toContain('Requesting dungeon (Seed: 456)');
    expect(mockSendMessageToServer).toHaveBeenCalledWith({ 
      action: 'generate_dungeon', 
      seed: 456 
    });
  });

  test('attemptPlayerMove should call sendMessageToServer if not game over', () => {
    const initialMessages = [{ 
        type: 'dungeon_data', 
        map: [], 
        "player_start_pos": {x:0,y:0}, 
        "tile_types": {},  
        "player_stats": INITIAL_PLAYER_STATS, 
        "monsters": []  
    }];
    const { result } = getHook(initialMessages); // isGameOver will be false

    act(() => {
      result.current.attemptPlayerMove(5, 10);
    });

    expect(mockSendMessageToServer).toHaveBeenCalledTimes(1);
    expect(mockSendMessageToServer).toHaveBeenCalledWith({
      action: 'player_move',
      "new_pos": { x: 5, y: 10 } 
    });
  });

  test('attemptPlayerMove should set game message and not call sendMessageToServer if game over', () => {
    const initialMessages = [{ type: 'player_died', "message": 'Game Over Test' }];
    const { result } = getHook(initialMessages);
        
    expect(result.current.isGameOver).toBe(true);

    act(() => {
      result.current.attemptPlayerMove(5, 10);
    });

    expect(mockSendMessageToServer).not.toHaveBeenCalled();
    expect(result.current.gameMessage.text).toContain('Game Over. Generate a new dungeon.');
    expect(result.current.gameMessage.isError).toBe(true);
  });

  describe('attemptUseItem', () => {
    test('should call sendMessageToServer with item_id and clear selection', () => {
        const mockInventoryItem = { "id": "item123", "name": "Potion", "consumable": true, "equippable": false, "type_key":"potion_heal", "description":"", "quantity":1, "slot": null, "attack_bonus": null, "defense_bonus": null, "effect_value": null };
        const initialMessages = [{ 
            type: 'player_stats_update', 
            "stats": { ...INITIAL_PLAYER_STATS, inventory: [mockInventoryItem] } 
        }];
        const { result, rerender } = getHook(initialMessages);
        
        act(() => { // Select the item after initial state is set
          result.current.selectInventoryItem(0); 
        });
        expect(result.current.selectedInventoryItemIndex).toBe(0);

        act(() => {
            result.current.attemptUseItem("item123"); 
        });

        expect(mockSendMessageToServer).toHaveBeenCalledWith({ action: 'use_item', "item_id": "item123" });
        expect(result.current.selectedInventoryItemIndex).toBeNull(); 
    });

    test('should set game message if no item_id provided', () => {
        const { result } = getHook(); // No initial messages needed
        act(() => {
            result.current.attemptUseItem(null); 
        });
        expect(mockSendMessageToServer).not.toHaveBeenCalled();
        expect(result.current.gameMessage.text).toBe("No item selected to use.");
    });
  });
  
  describe('attemptEquipItem', () => {
    test('should call sendMessageToServer with item_id and clear selection', () => {
        const mockEquippableItem = { "id": "dagger123", "name": "Dagger", "equippable": true, "consumable": false, "type_key":"weapon_dagger", "description":"", "quantity":1, "slot": "weapon", "attack_bonus": null, "defense_bonus": null, "effect_value": null };
        const initialMessages = [{ 
            type: 'player_stats_update', 
            "stats": { ...INITIAL_PLAYER_STATS, inventory: [mockEquippableItem] } 
        }];
        const { result } = getHook(initialMessages);
        
        act(() => { // Select item after initial state setup
            result.current.selectInventoryItem(0);
        });
        expect(result.current.selectedInventoryItemIndex).toBe(0);

        act(() => {
            result.current.attemptEquipItem("dagger123");
        });
        expect(mockSendMessageToServer).toHaveBeenCalledWith({ action: 'equip_item', "item_id": "dagger123" });
        expect(result.current.selectedInventoryItemIndex).toBeNull();
    });
  });
  
  describe('attemptUnequipItem', () => {
    test('should call sendMessageToServer with slot if item is equipped', () => {
        const equippedWeapon = { "id": "w1", "type_key": "weapon_sword", "name": "Sword", "description": "strong", "quantity": 1, "consumable": false, "equippable": true, "slot": "weapon", "attack_bonus": 5, "defense_bonus": null, "effect_value": null };
        const initialMessages = [{ 
            type: 'player_stats_update', 
            "stats": { ...INITIAL_PLAYER_STATS, equipment: { "weapon": equippedWeapon, "armor": null } } 
        }];
        const { result } = getHook(initialMessages);
        
        expect(result.current.equipment.weapon).toEqual(equippedWeapon);

        act(() => {
            result.current.attemptUnequipItem("weapon");
        });
        expect(mockSendMessageToServer).toHaveBeenCalledWith({ action: 'unequip_item', "slot": "weapon" });
    });

     test('should set game message if no item in slot', () => {
        const initialMessages = [{ 
            type: 'player_stats_update', 
            "stats": { ...INITIAL_PLAYER_STATS, equipment: { "weapon": null, "armor": null } } 
        }];
        const { result } = getHook(initialMessages);

        act(() => {
            result.current.attemptUnequipItem("weapon");
        });
        expect(mockSendMessageToServer).not.toHaveBeenCalled();
        expect(result.current.gameMessage.text).toBe("Nothing equipped in weapon slot.");
    });
  });

  describe('selectInventoryItem', () => {
    test('should update selectedInventoryItemIndex state', () => {
      const { result } = getHook();
      expect(result.current.selectedInventoryItemIndex).toBeNull();
      act(() => {
        result.current.selectInventoryItem(1);
      });
      expect(result.current.selectedInventoryItemIndex).toBe(1);
    });
  });
});