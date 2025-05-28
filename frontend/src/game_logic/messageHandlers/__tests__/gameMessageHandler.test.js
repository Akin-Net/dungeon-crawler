// frontend/src/game_logic/messageHandlers/__tests__/gameMessageHandler.test.js
import { handleGameMessage } from '../gameMessageHandler';
import { initialState } from '../../initialState';

describe('handleGameMessage', () => {
  test('should update gameMessage with text from message and set isError to false and default duration', () => {
    const currentState = {
      ...initialState,
      gameMessage: { text: 'An old error message', isError: true, duration: 0 }
    };
    const message = {
      type: "game_message",
      "text": "A new informative message." // Corrected quote
    };
    const newState = handleGameMessage(currentState, message);
    expect(newState.gameMessage).toEqual({
      text: "A new informative message.",
      isError: false,
      duration: 3000
    });
    // Ensure other parts of state (except gameMessage) are untouched
    const { gameMessage, ...restOfOldState } = currentState;
    const { gameMessage: newMessage, ...restOfNewState } = newState;
    expect(restOfNewState).toEqual(restOfOldState);
  });

  test('should overwrite an existing game message', () => {
    const currentState = {
      ...initialState,
      gameMessage: { text: 'Welcome!', isError: false, duration: 5000 }
    };
    const message = {
      type: "game_message",
      "text": "Player leveled up!" // Corrected quote
    };
    const newState = handleGameMessage(currentState, message);
    expect(newState.gameMessage).toEqual({
      text: "Player leveled up!",
      isError: false,
      duration: 3000
    });
  });
});