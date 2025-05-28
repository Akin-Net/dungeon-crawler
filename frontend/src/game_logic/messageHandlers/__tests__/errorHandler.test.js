// frontend/src/game_logic/messageHandlers/__tests__/errorHandler.test.js
import { handleError } from '../errorHandler';
import { initialState } from '../../initialState';

describe('handleError', () => {
  let baseState;

  beforeEach(() => {
    baseState = {
      ...initialState,
      isLoading: true, // Default to true for typical error scenario during loading
      gameMessage: { text: 'Initial message', isError: false, duration: 3000 }
    };
  });

  test('should set isLoading to false and update gameMessage with provided error message', () => {
    const message = {
      type: "error", // or "parse_error"
      "message": "Specific error from server." // Corrected quote
    };
    const newState = handleError(baseState, message);

    expect(newState.isLoading).toBe(false);
    expect(newState.gameMessage).toEqual({
      text: "Error: Specific error from server.",
      isError: true,
      duration: 0
    });
    // Ensure other parts of state (except isLoading, gameMessage) are untouched
    const { isLoading, gameMessage, ...restOfOldState } = baseState;
    const { isLoading: newLoading, gameMessage: newMessage, ...restOfNewState } = newState;
    expect(restOfNewState).toEqual(restOfOldState);
  });

  test('should use default error text if message.message is missing', () => {
    const message = {
      type: "error"
      // message.message is undefined
    };
    const newState = handleError(baseState, message);

    expect(newState.isLoading).toBe(false);
    expect(newState.gameMessage).toEqual({
      text: "Error: Data issue.",
      isError: true,
      duration: 0
    });
  });

  test('should use default error text if message.message is null', () => {
    const message = {
      type: "error",
      "message": null // Corrected quote
    };
    const newState = handleError(baseState, message);
    expect(newState.isLoading).toBe(false);
    expect(newState.gameMessage.text).toBe("Error: Data issue.");
  });

  test('should use default error text if message.message is an empty string', () => {
    const message = {
      type: "error",
      "message": "" // Corrected quote
    };
    const newState = handleError(baseState, message);
    expect(newState.isLoading).toBe(false);
    expect(newState.gameMessage.text).toBe("Error: Data issue.");
  });

  test('should keep isLoading as false if it was already false', () => {
    const alreadyNotLoadingState = {
      ...baseState,
      isLoading: false
    };
    const message = {
      type: "error",
      "message": "Another error." // Corrected quote
    };
    const newState = handleError(alreadyNotLoadingState, message);

    expect(newState.isLoading).toBe(false);
    expect(newState.gameMessage.text).toBe("Error: Another error.");
  });
});