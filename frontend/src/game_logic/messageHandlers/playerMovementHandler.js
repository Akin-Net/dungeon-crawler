// frontend/src/game_logic/messageHandlers/playerMovementHandler.js

export function handlePlayerMoved(currentState, message) {
  return { ...currentState, playerPos: message.player_pos };
}

export function handleInvalidMove(currentState, message) {
  return { 
    ...currentState, 
    playerPos: message.player_pos, // Sync position
    gameMessage: { text: `Invalid move: ${message.reason || 'Blocked.'}`, isError: true, duration: 3000 }
  };
}