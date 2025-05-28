// frontend/src/game_logic/messageHandlers/__tests__/monsterHandler.test.js
// (You'd create this file)

import { handleMonsterMoved, handleMonsterAppeared } from '../monsterHandler';
import { initialState } from '../../initialState';

describe('handleMonsterMoved', () => {
  let baseState;

  beforeEach(() => {
    baseState = {
      ...initialState,
      monsters: [
        { id: "m1", type: "goblin", x: 1, y: 1, tile_id: 4 },
        { id: "m2", type: "orc", x: 5, y: 5, tile_id: 5 }
      ]
    };
  });

  test('should update the position of the specified monster', () => {
    const message = {
      type: "monster_moved",
      monster_id: "m1",
      new_pos: { "x": 2, "y": 1 }
    };
    const newState = handleMonsterMoved(baseState, message);
    const movedMonster = newState.monsters.find(m => m.id === "m1");
    const otherMonster = newState.monsters.find(m => m.id === "m2");

    expect(movedMonster).toBeDefined();
    expect(movedMonster.x).toBe(2);
    expect(movedMonster.y).toBe(1);
    expect(otherMonster.x).toBe(5); // Unchanged
    expect(otherMonster.y).toBe(5); // Unchanged
  });

  test('should not change monster list if monster_id does not match', () => {
    const message = {
      type: "monster_moved",
      monster_id: "m99",
      new_pos: { "x": 10, "y": 10 }
    };
    const newState = handleMonsterMoved(baseState, message);
    expect(newState.monsters).toEqual(baseState.monsters);
  });

  test('should handle an empty monsters list gracefully', () => {
    const emptyState = { ...initialState, monsters: [] };
    const message = {
      type: "monster_moved",
      monster_id: "m1",
      new_pos: { "x": 2, "y": 1 }
    };
    const newState = handleMonsterMoved(emptyState, message);
    expect(newState.monsters).toEqual([]);
  });

  test('should handle null/undefined monsters list by returning empty array', () => {
    const nullState = { ...initialState, monsters: null };
    const message = {
      type: "monster_moved",
      monster_id: "m1",
      new_pos: { "x": 2, "y": 1 }
    };
    let newState = handleMonsterMoved(nullState, message);
    expect(newState.monsters).toEqual([]);

    const undefinedState = { ...initialState, monsters: undefined };
    newState = handleMonsterMoved(undefinedState, message);
    expect(newState.monsters).toEqual([]);
  });
});

describe('handleMonsterAppeared', () => {
  let baseState;

  beforeEach(() => {
    baseState = {
      ...initialState,
      monsters: [
        { id: "m1", type: "goblin", x: 1, y: 1, tile_id: 4 }
      ]
    };
  });

  test('should add a new monster to the list', () => {
    const message = {
      type: "monster_appeared",
      monster_info: { "id": "m2", "type": "orc", "x": 5, "y": 5, "tile_id": 5 }
    };
    const newState = handleMonsterAppeared(baseState, message);
    expect(newState.monsters).toHaveLength(2);
    expect(newState.monsters).toEqual(expect.arrayContaining([
      { id: "m1", type: "goblin", x: 1, y: 1, tile_id: 4 },
      { id: "m2", type: "orc", x: 5, y: 5, tile_id: 5 }
    ]));
  });

  test('should update an existing monster if ID matches', () => {
    const message = {
      type: "monster_appeared",
      monster_info: { "id": "m1", "type": "goblin_chief", "x": 2, "y": 2, "tile_id": 4 }
    };
    const newState = handleMonsterAppeared(baseState, message);
    expect(newState.monsters).toHaveLength(1);
    const updatedMonster = newState.monsters.find(m => m.id === "m1");
    expect(updatedMonster).toEqual({ "id": "m1", "type": "goblin_chief", "x": 2, "y": 2, "tile_id": 4 });
  });

  test('should add a monster if monsters list is initially empty', () => {
    const emptyState = { ...initialState, monsters: [] };
    const message = {
      type: "monster_appeared",
      monster_info: { "id": "m3", "type": "skeleton", "x": 3, "y": 3, "tile_id": 6 }
    };
    const newState = handleMonsterAppeared(emptyState, message);
    expect(newState.monsters).toHaveLength(1);
    expect(newState.monsters[0]).toEqual({ "id": "m3", "type": "skeleton", "x": 3, "y": 3, "tile_id": 6 });
  });
});