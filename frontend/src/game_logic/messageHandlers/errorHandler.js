// frontend/src/game_logic/messageHandlers/errorHandler.js (Example)
export function handleError(currentState, message) {
  console.log("[errorHandler] Handling error/parse_error. Setting isLoading to false.");
  return { 
    ...currentState, 
    isLoading: false, // Make sure this happens
    gameMessage: { text: `Error: ${message.message || 'Data issue.'}`, isError: true, duration: 0 }
  };
}