// frontend/src/game_logic/messageHandlers/playerLeveledUpHandler.js

export function handlePlayerLeveledUp(currentState, message) {
  // The actual stat changes (HP, ATK, DEF, new XP threshold) will come via a
  // subsequent 'player_stats_update' message which is triggered by _check_for_level_up.
  // This handler is primarily for the notification message.
  // If PlayerLeveledUpServerResponse included new_stats, we could update them here too.
  // For now, we primarily focus on the game message.
  
  console.log("[playerLeveledUpHandler] Player leveled up:", message);
  return {
    ...currentState,
    // Player stats will be updated by a separate PlayerStatsUpdateServerResponse
    // that _check_for_level_up should be sending.
    // If we want to be absolutely sure level is updated here:
    // playerStats: {
    //   ...currentState.playerStats,
    //   level: message.new_level, 
    // },
    gameMessage: { text: message.message, isError: false, duration: 5000 } // Longer duration for level up
  };
}