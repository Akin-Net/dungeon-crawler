// frontend/src/game_logic/messageHandlers/combatHandler.js
export function handleCombatEvent(currentState, message) {
  return { 
    ...currentState, 
    gameMessage: { text: message.message, isError: message.defender_faction === 'player', duration: 3000 }
  };
}
export function handleEntityDied(currentState, message) {
  let newMonsters = currentState.monsters;
  if (message.entity_type !== "player") {
    newMonsters = currentState.monsters.filter(m => m.id !== message.entity_id);
  }
  return { 
    ...currentState, 
    monsters: newMonsters,
    gameMessage: { text: message.message, isError: false, duration: 4000 }
  };
}
export function handlePlayerDied(currentState, message) {
  return { 
    ...currentState, 
    isGameOver: true,
    gameMessage: { text: message.message, isError: true, duration: 0 }
  };
}