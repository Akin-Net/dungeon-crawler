// frontend/src/game_logic/messageHandlers/gameMessageHandler.js
export function handleGameMessage(currentState, message) {
  return { 
    ...currentState, 
    gameMessage: { text: message.text, isError: false, duration: 3000 }
  };
}