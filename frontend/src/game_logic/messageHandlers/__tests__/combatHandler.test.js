// frontend/src/game_logic/messageHandlers/__tests__/combatHandler.test.js 

import { handleCombatEvent, handleEntityDied, handlePlayerDied } from '../combatHandler';
import { initialState } from '../../initialState';

describe('handleCombatEvent', () => {
  let baseState;

  beforeEach(() => {
    baseState = { 
      ...initialState, 
      gameMessage: { text: '', isError: false, duration: 0 } 
    };
  });

  test('should set error game message when player is defender and takes damage', () => {
    const message = {
      type: "combat_event",
      attacker_type: "goblin",
      defender_faction: "player",
      damage_done: 5,
      defender_hp_current: 15,
      defender_hp_max: 20,
      message: "Goblin hits you for 5 damage."
    };
    const newState = handleCombatEvent(baseState, message);
    expect(newState.gameMessage).toEqual({
      text: "Goblin hits you for 5 damage.",
      isError: true,
      duration: 3000
    });
    const { gameMessage, ...restOfOldState } = baseState;
    const { gameMessage: newMessage, ...restOfNewState } = newState;
    expect(restOfNewState).toEqual(restOfOldState); 
  });

  test('should set non-error game message when monster is defender', () => {
    const message = {
      type: "combat_event",
      attacker_faction: "player",
      defender_id: "monster1", // Corrected quote
      defender_type: "orc",
      damage_done: 7,
      defender_hp_current: 10, // Corrected quote
      defender_hp_max: 18,
      message: "You hit Orc for 7 damage."
    };
    const newState = handleCombatEvent(baseState, message);
    expect(newState.gameMessage).toEqual({
      text: "You hit Orc for 7 damage.",
      isError: false,
      duration: 3000
    });
  });

  test('should set non-error game message for no damage events', () => {
    const message = {
      type: "combat_event",
      attacker_faction: "player",
      defender_id: "monster1", // Corrected quote
      defender_type: "skeleton",
      damage_done: 0,
      defender_hp_current: 12, // Corrected quote
      defender_hp_max: 12,
      message: "You attack Skeleton but deal no damage."
    };
    const newState = handleCombatEvent(baseState, message);
    expect(newState.gameMessage).toEqual({
      text: "You attack Skeleton but deal no damage.",
      isError: false,
      duration: 3000
    });
  });
});

describe('handleEntityDied', () => {
  let baseState;

  beforeEach(() => {
    baseState = { 
      ...initialState, 
      monsters: [
        { id: "m1", type: "goblin", x: 1, y: 1, tile_id: 4 },
        { id: "m2", type: "orc", x: 5, y: 5, tile_id: 5 },
        { id: "m3", type: "skeleton", x: 3, y: 3, tile_id: 6 }
      ],
      gameMessage: { text: '', isError: false, duration: 0 } 
    };
  });

  test('should remove a monster from the list when it dies', () => {
    const message = {
      type: "entity_died",
      entity_id: "m2", // Corrected quote
      entity_type: "orc",
      pos: {"x": 5, "y": 5},
      message: "Orc dies! You gain 25 XP."
    };
    const newState = handleEntityDied(baseState, message);
    expect(newState.monsters).toEqual([
      { id: "m1", type: "goblin", x: 1, y: 1, tile_id: 4 },
      { id: "m3", type: "skeleton", x: 3, y: 3, tile_id: 6 }
    ]);
    expect(newState.monsters.find(m => m.id === "m2")).toBeUndefined();
    expect(newState.gameMessage).toEqual({
      text: "Orc dies! You gain 25 XP.",
      isError: false,
      duration: 4000
    });
  });

  test('should not change monsters list if entity_id does not match', () => {
    const message = {
      type: "entity_died",
      entity_id: "m99",  // Corrected quote
      entity_type: "goblin",
      pos: {"x": 0, "y": 0},
      message: "A mysterious entity vanishes."
    };
    const newState = handleEntityDied(baseState, message);
    expect(newState.monsters).toEqual(baseState.monsters);
    expect(newState.gameMessage.text).toBe("A mysterious entity vanishes.");
  });

  test('should not remove from monsters list if entity_type is player', () => {
    const message = {
      type: "entity_died",
      entity_id: "player_id_example", // Corrected quote
      entity_type: "player",
      pos: {"x": 0, "y": 0},
      message: "You have died."
    };
    const newState = handleEntityDied(baseState, message);
    expect(newState.monsters).toEqual(baseState.monsters);
    expect(newState.gameMessage.text).toBe("You have died.");
  });
});

describe('handlePlayerDied', () => {
  let baseState;

  beforeEach(() => {
    baseState = { 
      ...initialState, 
      isGameOver: false,
      gameMessage: { text: '', isError: false, duration: 3000 } 
    };
  });

  test('should set isGameOver to true and update game message', () => {
    const message = {
      type: "player_died",
      message: "You have been slain by a fearsome Orc!"
    };
    const newState = handlePlayerDied(baseState, message);
    expect(newState.isGameOver).toBe(true);
    expect(newState.gameMessage).toEqual({
      text: "You have been slain by a fearsome Orc!",
      isError: true,
      duration: 0 
    });
    const { isGameOver, gameMessage, ...restOfOldState } = baseState;
    const { isGameOver: newGameOver, gameMessage: newGameMessage, ...restOfNewState } = newState;
    expect(restOfNewState).toEqual(restOfOldState);
  });
});