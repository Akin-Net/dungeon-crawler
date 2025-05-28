// frontend/src/game_logic/messageHandlers/__tests__/tileChangeHandler.test.js
import { handleTileChange } from '../tileChangeHandler';
import { initialState } from '../../initialState';

describe('handleTileChange', () => {
  let baseState;

  beforeEach(() => {
    baseState = {
      ...initialState,
      dungeonMap: [
        [1, 1, 1],
        [1, 2, 1],
        [1, 1, 1]
      ],
      monsters: [{ id: 'm1', x: 0, y: 0, tile_id: 4 }],
      playerPos: { x: 0, y: 0}
    };
  });

  test('should update the specified tile within map boundaries', () => {
    const message = {
      type: "tile_change",
      pos: { "x": 1, "y": 1 },
      "new_tile_type": 0 
    };
    const newState = handleTileChange(baseState, message);
    expect(newState.dungeonMap[1][1]).toBe(0);
    expect(newState.dungeonMap).not.toBe(baseState.dungeonMap); 
    expect(newState.dungeonMap[1]).not.toBe(baseState.dungeonMap[1]); 
    expect(newState.dungeonMap[0]).toBe(baseState.dungeonMap[0]); 
    expect(newState.monsters).toBe(baseState.monsters);
    expect(newState.playerPos).toBe(baseState.playerPos);
  });

  test('should not change map content if x position is out of bounds', () => {
    const message = {
      type: "tile_change",
      pos: { "x": 10, "y": 1 }, 
      "new_tile_type": 0
    };
    const newState = handleTileChange(baseState, message);
    expect(newState.dungeonMap).toEqual(baseState.dungeonMap); 
    expect(newState.dungeonMap).not.toBe(baseState.dungeonMap); 
    if (baseState.dungeonMap && baseState.dungeonMap.length > 1 && newState.dungeonMap.length > 1) {
        expect(newState.dungeonMap[1]).not.toBe(baseState.dungeonMap[1]); 
        if (baseState.dungeonMap.length > 0 && newState.dungeonMap.length > 0) { 
            expect(newState.dungeonMap[0]).toBe(baseState.dungeonMap[0]);     
        }
    }
  });

  test('should not change map content if y position is out of bounds', () => {
    const message = {
      type: "tile_change",
      pos: { "x": 1, "y": 10 }, 
      "new_tile_type": 0
    };
    const newState = handleTileChange(baseState, message);
    expect(newState.dungeonMap).toEqual(baseState.dungeonMap); 
    expect(newState.dungeonMap).not.toBe(baseState.dungeonMap);
    if (newState.dungeonMap && baseState.dungeonMap) { 
        newState.dungeonMap.forEach((row, i) => {
            if (baseState.dungeonMap[i]) { 
                expect(row).toBe(baseState.dungeonMap[i]);
            }
        });
    }
  });

  test('should handle null dungeonMap in current state', () => {
    const nullMapState = { ...initialState, dungeonMap: null };
    const message = {
      type: "tile_change",
      pos: { "x": 1, "y": 1 },
      "new_tile_type": 0
    };
    const newState = handleTileChange(nullMapState, message);
    expect(newState.dungeonMap).toBeNull();
  });

  test('should handle empty dungeonMap in current state', () => {
    const emptyMapState = { ...initialState, dungeonMap: [] };
    const message = {
      type: "tile_change",
      pos: { "x": 1, "y": 1 },
      "new_tile_type": 0
    };
    const newState = handleTileChange(emptyMapState, message);
    expect(newState.dungeonMap).toEqual([]);
  });

  test('should not change map if message is missing pos', () => {
    const message = { type: "tile_change", "new_tile_type": 0 };
    const newState = handleTileChange(baseState, message);
    expect(newState.dungeonMap).toEqual(baseState.dungeonMap);
    // The current handler logic: newDungeonMap is initialized to currentState.dungeonMap.
    // If the 'if' condition (which checks for message.pos) is false,
    // newDungeonMap is never reassigned to the result of a .map().
    // So, the instance should be the same.
    expect(newState.dungeonMap).toBe(baseState.dungeonMap); 
  });

  test('should not change map content if message is missing new_tile_type', () => {
    const message = { type: "tile_change", pos: { "x": 1, "y": 1 } };
    const newState = handleTileChange(baseState, message);
    // Because message.hasOwnProperty('new_tile_type') is false, the map modification block is skipped.
    // newDungeonMap remains the same instance as currentState.dungeonMap.
    expect(newState.dungeonMap).toEqual(baseState.dungeonMap);
    expect(newState.dungeonMap).toBe(baseState.dungeonMap); // Expect instance to be the same
  });
});