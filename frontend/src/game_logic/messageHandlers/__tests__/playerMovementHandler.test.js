// frontend/src/game_logic/messageHandlers/__tests__/playerMovementHandler.test.js
import { handlePlayerMoved, handleInvalidMove } from '../playerMovementHandler';
import { initialState } from '../../initialState';

describe('handlePlayerMoved', () => {
  test('should update playerPos to the new position from the message', () => {
    const currentState = { 
      ...initialState, 
      playerPos: { x: 1, y: 1 } 
    };
    const message = {
      type: "player_moved",
      "player_pos": { "x": 2, "y": 1 } // Corrected
    };
    const newState = handlePlayerMoved(currentState, message);
    expect(newState.playerPos).toEqual({ x: 2, y: 1 });
    expect(newState.dungeonMap).toBe(currentState.dungeonMap); 
  });
});

describe('handleInvalidMove', () => {
  let baseState;

  beforeEach(() => {
    baseState = {
      ...initialState,
      playerPos: { x: 1, y: 1 },
      gameMessage: { text: '', isError: false, duration: 0 }
    };
  });

  test('should update playerPos and set gameMessage with provided reason', () => {
    const message = {
      type: "invalid_move",
      "reason": "Path blocked by a wall.", // Corrected
      "player_pos": { "x": 1, "y": 1 }   // Corrected
    };
    const newState = handleInvalidMove(baseState, message);
    expect(newState.playerPos).toEqual({ x: 1, y: 1 });
    expect(newState.gameMessage).toEqual({
      text: "Invalid move: Path blocked by a wall.",
      isError: true,
      duration: 3000
    });
  });

  test('should update playerPos and set gameMessage with default reason if none provided', () => {
    const message = {
      type: "invalid_move",
      "player_pos": { "x": 1, "y": 1 } // Corrected
    };
    const newState = handleInvalidMove(baseState, message);
    expect(newState.playerPos).toEqual({ x: 1, y: 1 });
    expect(newState.gameMessage).toEqual({
      text: "Invalid move: Blocked.",
      isError: true,
      duration: 3000
    });
  });

  test('should update playerPos even if it differs from current client state (syncing)', () => {
    const message = {
      type: "invalid_move",
      "reason": "Out of bounds.",      // Corrected
      "player_pos": { "x": 0, "y": 0 } // Corrected
    };
    const clientOutOfSyncState = { ...baseState, playerPos: { x: 1, y: 1 } };
    const newState = handleInvalidMove(clientOutOfSyncState, message);
    expect(newState.playerPos).toEqual({ x: 0, y: 0 }); 
    expect(newState.gameMessage.text).toBe("Invalid move: Out of bounds.");
  });
});