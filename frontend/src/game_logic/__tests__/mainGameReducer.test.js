// frontend/src/game_logic/__tests__/mainGameStateReducer.test.js 
// (Or wherever you place reducer tests)

import { gameStateReducer } from '../mainGameStateReducer';
import { initialState } from '../initialState';

describe('gameStateReducer - Direct Actions', () => {
  describe('SET_LOADING', () => {
    test('should set isLoading to true', () => {
      const action = { type: 'SET_LOADING', payload: true };
      const currentState = { ...initialState, isLoading: false };
      const newState = gameStateReducer(currentState, action);
      expect(newState.isLoading).toBe(true);
      // Ensure other parts of state are preserved
      const { isLoading, ...restOfState } = newState;
      const { isLoading: oldLoading, ...restOfOldState } = currentState;
      expect(restOfState).toEqual(restOfOldState);
    });

    test('should set isLoading to false', () => {
      const action = { type: 'SET_LOADING', payload: false };
      const currentState = { ...initialState, isLoading: true };
      const newState = gameStateReducer(currentState, action);
      expect(newState.isLoading).toBe(false);
    });
  });

  describe('SET_GAME_MESSAGE', () => {
    test('should set new game message with default isError and duration', () => {
      const action = { type: 'SET_GAME_MESSAGE', payload: { "text": "New Message" } };
      const currentState = { ...initialState, gameMessage: { "text": "Old", "isError": true, "duration": 0 } };
      const newState = gameStateReducer(currentState, action);
      expect(newState.gameMessage).toEqual({ "text": "New Message", "isError": false, "duration": 3000 });
    });

    test('should set new game message with isError: true', () => {
      const action = { type: 'SET_GAME_MESSAGE', payload: { "text": "Error Occurred", "isError": true } };
      const currentState = { ...initialState, gameMessage: { "text": "", "isError": false, "duration": 3000 } };
      const newState = gameStateReducer(currentState, action);
      expect(newState.gameMessage).toEqual({ "text": "Error Occurred", "isError": true, "duration": 3000 });
    });

    test('should set new game message with specific duration', () => {
      const action = { type: 'SET_GAME_MESSAGE', payload: { "text": "Timed Message", "duration": 5000 } };
      const currentState = { ...initialState, gameMessage: { "text": "", "isError": false, "duration": 3000 } };
      const newState = gameStateReducer(currentState, action);
      expect(newState.gameMessage).toEqual({ "text": "Timed Message", "isError": false, "duration": 5000 });
    });

    test('should set new game message with duration: 0', () => {
      const action = { type: 'SET_GAME_MESSAGE', payload: { "text": "Persistent Message", "duration": 0 } };
      const currentState = { ...initialState, gameMessage: { "text": "", "isError": false, "duration": 3000 } };
      const newState = gameStateReducer(currentState, action);
      expect(newState.gameMessage).toEqual({ "text": "Persistent Message", "isError": false, "duration": 0 });
    });
  });

  describe('SELECT_INVENTORY_ITEM', () => {
    test('should set selectedInventoryItemIndex', () => {
      const action = { type: 'SELECT_INVENTORY_ITEM', payload: 2 };
      const currentState = { ...initialState, selectedInventoryItemIndex: null };
      const newState = gameStateReducer(currentState, action);
      expect(newState.selectedInventoryItemIndex).toBe(2);
    });

    test('should change selectedInventoryItemIndex', () => {
      const action = { type: 'SELECT_INVENTORY_ITEM', payload: 1 };
      const currentState = { ...initialState, selectedInventoryItemIndex: 0 };
      const newState = gameStateReducer(currentState, action);
      expect(newState.selectedInventoryItemIndex).toBe(1);
    });
  });

  describe('CLEAR_SELECTED_INVENTORY_ITEM', () => {
    test('should set selectedInventoryItemIndex to null when an item was selected', () => {
      const action = { type: 'CLEAR_SELECTED_INVENTORY_ITEM' };
      const currentState = { ...initialState, selectedInventoryItemIndex: 2 };
      const newState = gameStateReducer(currentState, action);
      expect(newState.selectedInventoryItemIndex).toBeNull();
    });

    test('should keep selectedInventoryItemIndex as null if no item was selected', () => {
      const action = { type: 'CLEAR_SELECTED_INVENTORY_ITEM' };
      const currentState = { ...initialState, selectedInventoryItemIndex: null };
      const newState = gameStateReducer(currentState, action);
      expect(newState.selectedInventoryItemIndex).toBeNull();
    });
  });

  // We could also add a test for an unhandled action type to ensure it returns the state unchanged.
  test('should return current state for an unhandled action type', () => {
    const action = { type: 'UNKNOWN_ACTION', payload: 'anything' };
    const currentState = { ...initialState, isLoading: true };
    const newState = gameStateReducer(currentState, action);
    expect(newState).toEqual(currentState); // Should be the same state object or deeply equal
    expect(newState).toBe(currentState); // More strictly, it might return the exact same object instance
  });
});