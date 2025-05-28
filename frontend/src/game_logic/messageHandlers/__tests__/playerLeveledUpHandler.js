// frontend/src/game_logic/messageHandlers/__tests__/playerLeveledUpHandler.test.js
import { handlePlayerLeveledUp } from '../playerLeveledUpHandler';
import { initialState, INITIAL_PLAYER_STATS } from '../../initialState';

describe('handlePlayerLeveledUp', () => {
  test('should update gameMessage with the level up message and set longer duration', () => {
    const currentState = {
      ...initialState,
      playerStats: { // Provide some initial player stats
        ...INITIAL_PLAYER_STATS,
        level: 1,
      },
      gameMessage: { text: 'Previous message', isError: false, duration: 1000 }
    };
    const message = {
      type: "player_leveled_up",
      "new_level": 2, // Key corrected
      "message": "LEVEL UP! You reached level 2!" // Key corrected
    };

    const newState = handlePlayerLeveledUp(currentState, message);

    expect(newState.gameMessage).toEqual({
      text: "LEVEL UP! You reached level 2!",
      isError: false,
      duration: 5000 
    });

    // Verify that playerStats.level is NOT changed by this handler directly
    // as per the comment in the handler itself.
    expect(newState.playerStats.level).toBe(currentState.playerStats.level); 
    
    // Ensure other parts of the state are not touched (except gameMessage)
    const { gameMessage, ...restOfOldState } = currentState;
    const { gameMessage: newMessage, ...restOfNewState } = newState;
    expect(restOfNewState).toEqual(restOfOldState);
  });

  test('should correctly set gameMessage even if previous message was an error', () => {
    const currentState = {
      ...initialState,
      playerStats: { 
        ...INITIAL_PLAYER_STATS,
        level: 3,
      },
      gameMessage: { text: 'An error occurred!', isError: true, duration: 0 }
    };
    const message = {
      type: "player_leveled_up",
      "new_level": 4, // Key corrected
      "message": "Awesome! Level 4 achieved!" // Key corrected
    };

    const newState = handlePlayerLeveledUp(currentState, message);

    expect(newState.gameMessage).toEqual({
      text: "Awesome! Level 4 achieved!",
      isError: false, // Should be reset to false
      duration: 5000
    });
    expect(newState.playerStats.level).toBe(3); // Level not changed by this handler
  });
});